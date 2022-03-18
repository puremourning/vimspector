# vimspector - A multi-language debugging system for Vim
# Copyright 2018 Ben Jackson
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import glob
import json
import logging
import os
import shlex
import subprocess
import functools
import vim
import importlib

from vimspector import ( breakpoints,
                         code,
                         core_utils,
                         debug_adapter_connection,
                         install,
                         output,
                         stack_trace,
                         utils,
                         variables,
                         settings,
                         terminal,
                         installer )
from vimspector.vendor.json_minify import minify

# We cache this once, and don't allow it to change (FIXME?)
VIMSPECTOR_HOME = utils.GetVimspectorBase()

# cache of what the user entered for any option we ask them
USER_CHOICES = {}


class DebugSession( object ):
  def __init__( self, api_prefix ):
    self._logger = logging.getLogger( __name__ )
    utils.SetUpLogging( self._logger )

    self._api_prefix = api_prefix

    self._render_emitter = utils.EventEmitter()

    self._logger.info( "**** INITIALISING NEW VIMSPECTOR SESSION ****" )
    self._logger.info( "API is: {}".format( api_prefix ) )
    self._logger.info( 'VIMSPECTOR_HOME = %s', VIMSPECTOR_HOME )
    self._logger.info( 'gadgetDir = %s',
                       install.GetGadgetDir( VIMSPECTOR_HOME ) )

    self._uiTab = None
    self._logView = None
    self._stackTraceView = None
    self._variablesView = None
    self._saved_variables_data = None
    self._outputView = None
    self._codeView = None
    self._breakpoints = breakpoints.ProjectBreakpoints(
      self._render_emitter, self._IsPCPresentAt )
    self._splash_screen = None
    self._remote_term = None
    self._adapter_term = None

    self._run_on_server_exit = None

    self._configuration = None
    self._adapter = None
    self._launch_config = None

    self._ResetServerState()

  def _ResetServerState( self ):
    self._connection = None
    self._init_complete = False
    self._launch_complete = False
    self._on_init_complete_handlers = []
    self._server_capabilities = {}
    vim.vars[ 'vimspector_session_windows' ] = {}
    self.ClearTemporaryBreakpoints()

  def GetConfigurations( self, adapters ):
    current_file = utils.GetBufferFilepath( vim.current.buffer )
    filetypes = utils.GetBufferFiletypes( vim.current.buffer )
    configurations = {}

    for launch_config_file in PathsToAllConfigFiles( VIMSPECTOR_HOME,
                                                     current_file,
                                                     filetypes ):
      self._logger.debug( f'Reading configurations from: {launch_config_file}' )
      if not launch_config_file or not os.path.exists( launch_config_file ):
        continue

      with open( launch_config_file, 'r' ) as f:
        database = json.loads( minify( f.read() ) )
        configurations.update( database.get( 'configurations' ) or {} )
        adapters.update( database.get( 'adapters' ) or {} )

    filetype_configurations = configurations
    if filetypes:
      # filter out any configurations that have a 'filetypes' list set and it
      # doesn't contain one of the current filetypes
      filetype_configurations = {
        k: c for k, c in configurations.items() if 'filetypes' not in c or any(
          ft in c[ 'filetypes' ] for ft in filetypes
        )
      }

    return launch_config_file, filetype_configurations, configurations

  def Start( self,
             force_choose=False,
             launch_variables = None,
             adhoc_configurations = None ):
    # We mutate launch_variables, so don't mutate the default argument.
    # https://docs.python-guide.org/writing/gotchas/#mutable-default-arguments
    if launch_variables is None:
      launch_variables = {}

    self._logger.info( "User requested start debug session with %s",
                       launch_variables )

    current_file = utils.GetBufferFilepath( vim.current.buffer )
    adapters = {}

    launch_config_file = None
    configurations = None
    if adhoc_configurations:
      configurations = adhoc_configurations
    else:
      ( launch_config_file,
        configurations,
        all_configurations ) = self.GetConfigurations( adapters )

    if not configurations:
      utils.UserMessage( 'Unable to find any debug configurations. '
                         'You need to tell vimspector how to launch your '
                         'application.' )
      return

    glob.glob( install.GetGadgetDir( VIMSPECTOR_HOME ) )
    for gadget_config_file in PathsToAllGadgetConfigs( VIMSPECTOR_HOME,
                                                       current_file ):
      self._logger.debug( f'Reading gadget config: {gadget_config_file}' )
      if not gadget_config_file or not os.path.exists( gadget_config_file ):
        continue

      with open( gadget_config_file, 'r' ) as f:
        a =  json.loads( minify( f.read() ) ).get( 'adapters' ) or {}
        adapters.update( a )

    if 'configuration' in launch_variables:
      configuration_name = launch_variables.pop( 'configuration' )
    elif force_choose:
      # Always display the menu
      configuration_name = utils.SelectFromList(
        'Which launch configuration?',
        sorted( configurations.keys() ) )
    elif ( len( configurations ) == 1 and
           next( iter( configurations.values() ) ).get( "autoselect", True ) ):
      configuration_name = next( iter( configurations.keys() ) )
    else:
      # Find a single configuration with 'default' True and autoselect not False
      defaults = { n: c for n, c in configurations.items()
                   if c.get( 'default', False ) is True
                   and c.get( 'autoselect', True ) is not False }

      if len( defaults ) == 1:
        configuration_name = next( iter( defaults.keys() ) )
      else:
        configuration_name = utils.SelectFromList(
          'Which launch configuration?',
          sorted( configurations.keys() ) )

    if not configuration_name or configuration_name not in configurations:
      return

    if launch_config_file:
      self._workspace_root = os.path.dirname( launch_config_file )
    else:
      self._workspace_root = os.path.dirname( current_file )

    try:
      configuration = configurations[ configuration_name ]
    except KeyError:
      # Maybe the specified one by name that's not for this filetype? Let's try
      # that one...
      configuration = all_configurations[ configuration_name ]

    current_configuration_name = configuration_name
    while 'extends' in configuration:
      base_configuration_name = configuration.pop( 'extends' )
      base_configuration = all_configurations.get( base_configuration_name )
      if base_configuration is None:
        raise RuntimeError( f"The adapter { current_configuration_name } "
                            f"extends configuration { base_configuration_name }"
                            ", but this does not exist" )

      core_utils.override( base_configuration, configuration )
      current_configuration_name = base_configuration_name
      configuration = base_configuration


    adapter = configuration.get( 'adapter' )
    if isinstance( adapter, str ):
      adapter_dict = adapters.get( adapter )

      if adapter_dict is None:
        suggested_gadgets = installer.FindGadgetForAdapter( adapter )
        if suggested_gadgets:
          response = utils.AskForInput(
            f"The specified adapter '{adapter}' is not "
            "installed. Would you like to install the following gadgets? ",
            ' '.join( suggested_gadgets ) )
          if response:
            new_launch_variables = dict( launch_variables )
            new_launch_variables[ 'configuration' ] = configuration_name

            installer.RunInstaller(
              self._api_prefix,
              False, # Don't leave open
              *shlex.split( response ),
              then = lambda: self.Start( new_launch_variables ) )
            return
          elif response is None:
            return

        utils.UserMessage( f"The specified adapter '{adapter}' is not "
                           "available. Did you forget to run "
                           "'VimspectorInstall'?",
                           persist = True,
                           error = True )
        return

      adapter = adapter_dict

    if not adapter:
      utils.UserMessage( 'No adapter configured for {}'.format(
        configuration_name ),
        persist=True )
      return

    # Pull in anything from the base(s)
    # FIXME: this is copypasta from above, but sharing the code is a little icky
    # due to the way it returns from this method (maybe use an exception?)
    while 'extends' in adapter:
      base_adapter_name = adapter.pop( 'extends' )
      base_adapter = adapters.get( base_adapter_name )

      if base_adapter is None:
        suggested_gadgets = installer.FindGadgetForAdapter( base_adapter_name )
        if suggested_gadgets:
          response = utils.AskForInput(
            f"The specified base adapter '{base_adapter_name}' is not "
            "installed. Would you like to install the following gadgets? ",
            ' '.join( suggested_gadgets ) )
          if response:
            new_launch_variables = dict( launch_variables )
            new_launch_variables[ 'configuration' ] = configuration_name

            installer.RunInstaller(
              self._api_prefix,
              False, # Don't leave open
              *shlex.split( response ),
              then = lambda: self.Start( new_launch_variables ) )
            return
          elif response is None:
            return

        utils.UserMessage( f"The specified base adapter '{base_adapter_name}' "
                           "is not available. Did you forget to run "
                           "'VimspectorInstall'?",
                           persist = True,
                           error = True )
        return

      core_utils.override( base_adapter, adapter )
      adapter = base_adapter

    # Additional vars as defined by VSCode:
    #
    # ${workspaceFolder} - the path of the folder opened in VS Code
    # ${workspaceFolderBasename} - the name of the folder opened in VS Code
    #                              without any slashes (/)
    # ${file} - the current opened file
    # ${relativeFile} - the current opened file relative to workspaceFolder
    # ${fileBasename} - the current opened file's basename
    # ${fileBasenameNoExtension} - the current opened file's basename with no
    #                              file extension
    # ${fileDirname} - the current opened file's dirname
    # ${fileExtname} - the current opened file's extension
    # ${cwd} - the task runner's current working directory on startup
    # ${lineNumber} - the current selected line number in the active file
    # ${selectedText} - the current selected text in the active file
    # ${execPath} - the path to the running VS Code executable

    def relpath( p, relative_to ):
      if not p:
        return ''
      return os.path.relpath( p, relative_to )

    def splitext( p ):
      if not p:
        return [ '', '' ]
      return os.path.splitext( p )

    variables = {
      'dollar': '$', # HACK. Hote '$$' also works.
      'workspaceRoot': self._workspace_root,
      'workspaceFolder': self._workspace_root,
      'gadgetDir': install.GetGadgetDir( VIMSPECTOR_HOME ),
      'file': current_file,
    }

    calculus = {
      'relativeFile': lambda: relpath( current_file,
                                       self._workspace_root ),
      'fileBasename': lambda: os.path.basename( current_file ),
      'fileBasenameNoExtension':
        lambda: splitext( os.path.basename( current_file ) )[ 0 ],
      'fileDirname': lambda: os.path.dirname( current_file ),
      'fileExtname': lambda: splitext( os.path.basename( current_file ) )[ 1 ],
      # NOTE: this is the window-local cwd for the current window, *not* Vim's
      # working directory.
      'cwd': os.getcwd,
      'unusedLocalPort': utils.GetUnusedLocalPort,
    }

    # Pretend that vars passed to the launch command were typed in by the user
    # (they may have been in theory)
    USER_CHOICES.update( launch_variables )
    variables.update( launch_variables )

    try:
      variables.update(
        utils.ParseVariables( adapter.get( 'variables', {} ),
                              variables,
                              calculus,
                              USER_CHOICES ) )
      variables.update(
        utils.ParseVariables( configuration.get( 'variables', {} ),
                              variables,
                              calculus,
                              USER_CHOICES ) )


      utils.ExpandReferencesInDict( configuration,
                                    variables,
                                    calculus,
                                    USER_CHOICES )
      utils.ExpandReferencesInDict( adapter,
                                    variables,
                                    calculus,
                                    USER_CHOICES )
    except KeyboardInterrupt:
      self._Reset()
      return

    self._StartWithConfiguration( configuration, adapter )

  def _StartWithConfiguration( self, configuration, adapter ):
    def start():
      self._configuration = configuration
      self._adapter = adapter
      self._launch_config = None

      self._logger.info( 'Configuration: %s',
                         json.dumps( self._configuration ) )
      self._logger.info( 'Adapter: %s',
                         json.dumps( self._adapter ) )

      if not self._uiTab:
        self._SetUpUI()
      else:
        vim.current.tabpage = self._uiTab

      self._Prepare()
      if not self._StartDebugAdapter():
        self._logger.info( "Failed to launch or attach to the debug adapter" )
        return

      self._Initialise()

      self._stackTraceView.ConnectionUp( self._connection )
      self._variablesView.ConnectionUp( self._connection )

      if self._saved_variables_data:
        self._variablesView.Load( self._saved_variables_data )
        # TODO: clear it ?
        # TODO: store this stuff in module scope in variables.py ?
        # TODO: hmmm...

      self._outputView.ConnectionUp( self._connection )
      self._breakpoints.ConnectionUp( self._connection )

    if self._connection:
      self._logger.debug( "_StopDebugAdapter with callback: start" )
      self._StopDebugAdapter( interactive = False, callback = start )
      return

    start()

  def Restart( self ):
    if self._configuration is None or self._adapter is None:
      return self.Start()

    self._StartWithConfiguration( self._configuration, self._adapter )

  def IfConnected( otherwise=None ):
    def decorator( fct ):
      """Decorator, call fct if self._connected else echo warning"""
      @functools.wraps( fct )
      def wrapper( self, *args, **kwargs ):
        if not self._connection:
          utils.UserMessage(
            'Vimspector not connected, start a debug session first',
            persist=False,
            error=True )
          return otherwise
        return fct( self, *args, **kwargs )
      return wrapper
    return decorator

  def HasUI( self ):
    return self._uiTab and self._uiTab.valid

  def IsUITab( self, tab_nubmer ):
    return self.HasUI() and self._uiTab.number == tab_nubmer

  def RequiresUI( otherwise=None ):
    """Decorator, call fct if self._connected else echo warning"""
    def decorator( fct ):
      @functools.wraps( fct )
      def wrapper( self, *args, **kwargs ):
        if not self.HasUI():
          utils.UserMessage(
            'Vimspector is not active',
            persist=False,
            error=True )
          return otherwise
        return fct( self, *args, **kwargs )
      return wrapper
    return decorator

  def OnChannelData( self, data ):
    if self._connection is None:
      # Should _not_ happen, but maybe possible due to races or vim bufs?
      return

    self._connection.OnData( data )


  def OnServerStderr( self, data ):
    if self._outputView:
      self._outputView.Print( 'server', data )


  def OnRequestTimeout( self, timer_id ):
    self._connection.OnRequestTimeout( timer_id )

  def OnChannelClosed( self ):
    # TODO: Not calld
    self._connection = None

  @IfConnected()
  def Stop( self, interactive = False ):
    self._logger.debug( "Stop debug adapter with no callback" )
    self._StopDebugAdapter( interactive = interactive )

  def Reset( self, interactive = False ):
    if self._connection:
      self._logger.debug( "Stop debug adapter with callback : self._Reset()" )
      self._StopDebugAdapter( interactive = interactive,
                              callback = lambda: self._Reset() )
    else:
      self._Reset()

  def _IsPCPresentAt( self, file_path, line ):
    return self._codeView and self._codeView.IsPCPresentAt( file_path, line )

  def _Reset( self ):
    vim.vars[ 'vimspector_resetting' ] = 1
    self._logger.info( "Debugging complete." )

    def ResetUI():
      if self._stackTraceView:
        self._stackTraceView.Reset()
      if self._variablesView:
        self._variablesView.Reset()
      if self._outputView:
        self._outputView.Reset()
      if self._codeView:
        self._codeView.Reset()

      self._stackTraceView = None
      self._variablesView = None
      self._outputView = None
      self._codeView = None
      self._remote_term = None
      self._uiTab = None

    if self.HasUI():
      self._logger.debug( "Clearing down UI" )
      vim.current.tabpage = self._uiTab
      self._splash_screen = utils.HideSplash( self._api_prefix,
                                              self._splash_screen )
      ResetUI()
      vim.command( 'tabclose!' )
    else:
      ResetUI()

    vim.vars[ 'vimspector_session_windows' ] = {
      'breakpoints': vim.vars[ 'vimspector_session_windows' ].get(
        'breakpoints' )
    }

    vim.command( 'doautocmd <nomodeline> User VimspectorDebugEnded' )
    vim.vars[ 'vimspector_resetting' ] = 0

    # make sure that we're displaying signs in any still-open buffers
    self._breakpoints.UpdateUI()

  def ReadSessionFile( self, session_file: str = None ):
    if session_file is None:
      session_file = self._DetectSessionFile( invent_one_if_not_found = False )

    if session_file is None:
      utils.UserMessage( f"No { settings.Get( 'session_file_name' ) } file "
                         "found. Specify a file with :VimspectorLoadSession "
                         "<filename>",
                         persist = True,
                         error = True )
      return False

    try:
      with open( session_file, 'r' ) as f:
        session_data = json.load( f )

      USER_CHOICES.update(
        session_data.get( 'session', {} ).get( 'user_choices', {} ) )

      self._breakpoints.Load( session_data.get( 'breakpoints' ) )

      # We might not _have_ a self._variablesView yet so we need a
      # mechanism where we save this for later and reload when it's ready
      variables_data = session_data.get( 'variables', {} )
      if self._variablesView:
        self._variablesView.Load( variables_data )
      else:
        self._saved_variables_data = variables_data

      utils.UserMessage( f"Loaded { session_file }" )
      return True
    except OSError:
      self._logger.exception( f"Invalid session file { session_file }" )
      utils.UserMessage( f"Session file { session_file } not found",
                         persist=True,
                         error=True )
      return False
    except json.JSONDecodeError:
      self._logger.exception( f"Invalid session file { session_file }" )
      utils.UserMessage( "The session file could not be read",
                         persist = True,
                         error = True )
      return False


  def WriteSessionFile( self, session_file: str = None ):
    if session_file is None:
      session_file = self._DetectSessionFile( invent_one_if_not_found = True )

    try:
      with open( session_file, 'w' ) as f:
        f.write( json.dumps( {
          'breakpoints': self._breakpoints.Save(),
          'session': {
            'user_choices': USER_CHOICES,
          },
          'variables': self._variablesView.Save() if self._variablesView else {}
        } ) )

      utils.UserMessage( f"Wrote { session_file }" )
      return True
    except OSError:
      self._logger.exception( f"Unable to write session file { session_file }" )
      utils.UserMessage( "The session file could not be read",
                         persist = True,
                         error = True )
      return False


  def _DetectSessionFile( self, invent_one_if_not_found: bool ):
    session_file_name = settings.Get( 'session_file_name' )
    current_file = utils.GetBufferFilepath( vim.current.buffer )

    # Search from the path of the file we're editing. But note that if we invent
    # a file, we always use CWD as that's more like what would be expected.
    file_path = utils.PathToConfigFile( session_file_name,
                                        os.path.dirname( current_file ) )

    if file_path:
      return file_path

    if invent_one_if_not_found:
      return os.path.join( os.getcwd(), session_file_name )

    return None


  @IfConnected()
  def StepOver( self ):
    if self._stackTraceView.GetCurrentThreadId() is None:
      return

    self._connection.DoRequest( None, {
      'command': 'next',
      'arguments': {
        'threadId': self._stackTraceView.GetCurrentThreadId()
      },
    } )

    self._stackTraceView.OnContinued()
    self._codeView.SetCurrentFrame( None )

  @IfConnected()
  def StepInto( self ):
    threadId = self._stackTraceView.GetCurrentThreadId()
    if threadId is None:
      return

    def handler( *_ ):
      self._stackTraceView.OnContinued( { 'threadId': threadId } )
      self._codeView.SetCurrentFrame( None )

    self._connection.DoRequest( handler, {
      'command': 'stepIn',
      'arguments': {
        'threadId': threadId
      },
    } )

  @IfConnected()
  def StepOut( self ):
    threadId = self._stackTraceView.GetCurrentThreadId()
    if threadId is None:
      return

    def handler( *_ ):
      self._stackTraceView.OnContinued( { 'threadId': threadId } )
      self._codeView.SetCurrentFrame( None )

    self._connection.DoRequest( handler, {
      'command': 'stepOut',
      'arguments': {
        'threadId': threadId
      },
    } )


  def Continue( self ):
    if not self._connection:
      self.Start()
      return

    threadId = self._stackTraceView.GetCurrentThreadId()
    if threadId is None:
      utils.UserMessage( 'No current thread', persist = True )
      return

    def handler( msg ):
      self._stackTraceView.OnContinued( {
          'threadId': threadId,
          'allThreadsContinued': ( msg.get( 'body' ) or {} ).get(
            'allThreadsContinued',
            True )
        } )
      self._codeView.SetCurrentFrame( None )

    self._connection.DoRequest( handler, {
      'command': 'continue',
      'arguments': {
        'threadId': threadId,
      },
    } )

  @IfConnected()
  def Pause( self ):
    if self._stackTraceView.GetCurrentThreadId() is None:
      utils.UserMessage( 'No current thread', persist = True )
      return

    self._connection.DoRequest( None, {
      'command': 'pause',
      'arguments': {
        'threadId': self._stackTraceView.GetCurrentThreadId(),
      },
    } )

  @IfConnected()
  def PauseContinueThread( self ):
    self._stackTraceView.PauseContinueThread()

  @IfConnected()
  def SetCurrentThread( self ):
    self._stackTraceView.SetCurrentThread()

  @IfConnected()
  def ExpandVariable( self, buf = None, line_num = None ):
    self._variablesView.ExpandVariable( buf, line_num )

  @IfConnected()
  def SetVariableValue( self, new_value = None, buf = None, line_num = None ):
    self._variablesView.SetVariableValue( new_value, buf, line_num )

  @IfConnected()
  def ReadMemory( self, length = None, offset = None ):
    if not self._server_capabilities.get( 'supportsReadMemoryRequest' ):
      utils.UserMessage( "Server does not support memory request",
                         error = True )
      return

    memoryReference = self._variablesView.GetMemoryReference()
    if memoryReference is None:
      utils.UserMessage( "Cannot find memory reference for that",
                         error = True )
      return

    if length is None:
      length = utils.AskForInput( 'How much data to display? ',
                                  default_value = '1024' )

    try:
      length = int( length )
    except ValueError:
      return

    if offset is None:
      offset = utils.AskForInput( 'Location offset? ',
                                  default_value = '0' )

    try:
      offset = int( offset )
    except ValueError:
      return


    def handler( msg ):
      self._codeView.ShowMemory( memoryReference, length, offset, msg )

    self._connection.DoRequest( handler, {
      'command': 'readMemory',
      'arguments': {
        'memoryReference': memoryReference,
        'count': int( length ),
        'offset': int( offset )
      }
    } )


  @IfConnected()
  def AddWatch( self, expression ):
    self._variablesView.AddWatch( self._stackTraceView.GetCurrentFrame(),
                                  expression )

  @IfConnected()
  def EvaluateConsole( self, expression, verbose ):
    self._outputView.Evaluate( self._stackTraceView.GetCurrentFrame(),
                               expression,
                               verbose )

  @IfConnected()
  def DeleteWatch( self ):
    self._variablesView.DeleteWatch()


  @IfConnected()
  def HoverEvalTooltip( self, winnr, bufnr, lnum, expression, is_hover ):
    frame = self._stackTraceView.GetCurrentFrame()
    # Check if RIP is in a frame
    if frame is None:
      self._logger.debug( 'Tooltip: Not in a stack frame' )
      return ''

    # Check if cursor in code window
    if winnr == int( self._codeView._window.number ):
      return self._variablesView.HoverEvalTooltip( frame, expression, is_hover )

    return self._variablesView.HoverVarWinTooltip( bufnr,
                                                   lnum,
                                                   is_hover )
    # Return variable aware function


  def CleanUpTooltip( self ):
    return self._variablesView.CleanUpTooltip()

  @IfConnected()
  def ExpandFrameOrThread( self ):
    self._stackTraceView.ExpandFrameOrThread()

  @IfConnected()
  def UpFrame( self ):
    self._stackTraceView.UpFrame()

  @IfConnected()
  def DownFrame( self ):
    self._stackTraceView.DownFrame()

  def ToggleLog( self ):
    if self.HasUI():
      return self.ShowOutput( 'Vimspector' )

    if self._logView and self._logView.WindowIsValid():
      self._logView.Reset()
      self._logView = None
      return

    if self._logView:
      self._logView.Reset()

    # TODO: The UI code is too scattered. Re-organise into a UI class that
    # just deals with these thigns like window layout and custmisattion.
    vim.command( f'botright { settings.Int( "bottombar_height" ) }new' )
    win = vim.current.window
    self._logView = output.OutputView( win, self._api_prefix )
    self._logView.AddLogFileView()
    self._logView.ShowOutput( 'Vimspector' )

  @RequiresUI()
  def ShowOutput( self, category ):
    if not self._outputView.WindowIsValid():
      # TODO: The UI code is too scattered. Re-organise into a UI class that
      # just deals with these thigns like window layout and custmisattion.
      # currently, this class and the CodeView share some responsiblity for this
      # and poking into each View class to check its window is valid also feels
      # wrong.
      with utils.LetCurrentTabpage( self._uiTab ):
        vim.command( f'botright { settings.Int( "bottombar_height" ) }new' )
        self._outputView.UseWindow( vim.current.window )
        vim.vars[ 'vimspector_session_windows' ][ 'output' ] = utils.WindowID(
          vim.current.window,
          self._uiTab )

    self._outputView.ShowOutput( category )

  @RequiresUI( otherwise=[] )
  def GetOutputBuffers( self ):
    return self._outputView.GetCategories()

  @IfConnected( otherwise=[] )
  def GetCompletionsSync( self, text_line, column_in_bytes ):
    if not self._server_capabilities.get( 'supportsCompletionsRequest' ):
      return []

    response = self._connection.DoRequestSync( {
      'command': 'completions',
      'arguments': {
        'frameId': self._stackTraceView.GetCurrentFrame()[ 'id' ],
        # TODO: encoding ? bytes/codepoints
        'text': text_line,
        'column': column_in_bytes
      }
    } )
    # TODO:
    #  - start / length
    #  - sortText
    return response[ 'body' ][ 'targets' ]


  @IfConnected( otherwise=[] )
  def GetCommandLineCompletions( self, ArgLead, prev_non_keyword_char ):
    items = []
    for candidate in self.GetCompletionsSync( ArgLead, prev_non_keyword_char ):
      label = candidate.get( 'text', candidate[ 'label' ] )
      start = prev_non_keyword_char - 1
      if 'start' in candidate and 'length' in candidate:
        start = candidate[ 'start' ]
      items.append( ArgLead[ 0 : start ] + label )

    return items

  def RefreshSigns( self ):
    if self._connection:
      self._codeView.Refresh()
    self._breakpoints.Refresh()


  def _SetUpUI( self ):
    vim.command( 'tab split' )
    self._uiTab = vim.current.tabpage

    mode = settings.Get( 'ui_mode' )

    if mode == 'auto':
      # Go vertical if there isn't enough horizontal space for at least:
      #  the left bar width
      #  + the code min width
      #  + the terminal min width
      #  + enough space for a sign column and number column?
      min_width = ( settings.Int( 'sidebar_width' )
                    + 1 + 2 + 3
                    + settings.Int( 'code_minwidth' )
                    + 1 + settings.Int( 'terminal_minwidth' ) )

      min_height = ( settings.Int( 'code_minheight' ) + 1 +
                     settings.Int( 'topbar_height' ) + 1 +
                     settings.Int( 'bottombar_height' ) + 1 +
                     2 )

      mode = ( 'vertical'
               if vim.options[ 'columns' ] < min_width
               else 'horizontal' )

      if vim.options[ 'lines' ] < min_height:
        mode = 'horizontal'

      self._logger.debug( 'min_width/height: %s/%s, actual: %s/%s - result: %s',
                          min_width,
                          min_height,
                          vim.options[ 'columns' ],
                          vim.options[ 'lines' ],
                          mode )

    if mode == 'vertical':
      self._SetUpUIVertical()
    else:
      self._SetUpUIHorizontal()


  def _SetUpUIHorizontal( self ):
    # Code window
    code_window = vim.current.window
    self._codeView = code.CodeView( code_window,
      self._api_prefix,
      self._render_emitter,
      self._breakpoints.IsBreakpointPresentAt )

    # Call stack
    vim.command(
      f'topleft vertical { settings.Int( "sidebar_width" ) }new' )
    stack_trace_window = vim.current.window
    one_third = int( vim.eval( 'winheight( 0 )' ) ) / 3
    self._stackTraceView = stack_trace.StackTraceView( self,
                                                       stack_trace_window )

    # Watches
    vim.command( 'leftabove new' )
    watch_window = vim.current.window

    # Variables
    vim.command( 'leftabove new' )
    vars_window = vim.current.window

    with utils.LetCurrentWindow( vars_window ):
      vim.command( f'{ one_third }wincmd _' )
    with utils.LetCurrentWindow( watch_window ):
      vim.command( f'{ one_third }wincmd _' )
    with utils.LetCurrentWindow( stack_trace_window ):
      vim.command( f'{ one_third }wincmd _' )

    self._variablesView = variables.VariablesView( vars_window, watch_window )

    # Output/logging
    vim.current.window = code_window
    vim.command( f'rightbelow { settings.Int( "bottombar_height" ) }new' )
    output_window = vim.current.window
    self._outputView = output.DAPOutputView( output_window,
                                             self._api_prefix )

    # TODO: If/when we support multiple sessions, we'll need some way to
    # indicate which tab was created and store all the tabs
    vim.vars[ 'vimspector_session_windows' ] = {
      'mode': 'horizontal',
      'tabpage': self._uiTab.number,
      'code': utils.WindowID( code_window, self._uiTab ),
      'stack_trace': utils.WindowID( stack_trace_window, self._uiTab ),
      'variables': utils.WindowID( vars_window, self._uiTab ),
      'watches': utils.WindowID( watch_window, self._uiTab ),
      'output': utils.WindowID( output_window, self._uiTab ),
      'eval': None, # updated every time eval popup is opened
      'breakpoints': vim.vars[ 'vimspector_session_windows' ].get(
        'breakpoints' ) # same as above, but for breakpoints
    }
    with utils.RestoreCursorPosition():
      with utils.RestoreCurrentWindow():
        with utils.RestoreCurrentBuffer( vim.current.window ):
          vim.command( 'doautocmd User VimspectorUICreated' )


  def _SetUpUIVertical( self ):
    # Code window
    code_window = vim.current.window
    self._codeView = code.CodeView( code_window,
                                    self._api_prefix,
                                    self._render_emitter,
                                    self._breakpoints.IsBreakpointPresentAt )

    # Call stack
    vim.command(
      f'topleft { settings.Int( "topbar_height" ) }new' )
    stack_trace_window = vim.current.window
    one_third = int( vim.eval( 'winwidth( 0 )' ) ) / 3
    self._stackTraceView = stack_trace.StackTraceView( self,
                                                       stack_trace_window )


    # Watches
    vim.command( 'leftabove vertical new' )
    watch_window = vim.current.window

    # Variables
    vim.command( 'leftabove vertical new' )
    vars_window = vim.current.window


    with utils.LetCurrentWindow( vars_window ):
      vim.command( f'{ one_third }wincmd |' )
    with utils.LetCurrentWindow( watch_window ):
      vim.command( f'{ one_third }wincmd |' )
    with utils.LetCurrentWindow( stack_trace_window ):
      vim.command( f'{ one_third }wincmd |' )

    self._variablesView = variables.VariablesView( vars_window, watch_window )


    # Output/logging
    vim.current.window = code_window
    vim.command( f'rightbelow { settings.Int( "bottombar_height" ) }new' )
    output_window = vim.current.window
    self._outputView = output.DAPOutputView( output_window,
                                             self._api_prefix )

    # TODO: If/when we support multiple sessions, we'll need some way to
    # indicate which tab was created and store all the tabs
    vim.vars[ 'vimspector_session_windows' ] = {
      'mode': 'vertical',
      'tabpage': self._uiTab.number,
      'code': utils.WindowID( code_window, self._uiTab ),
      'stack_trace': utils.WindowID( stack_trace_window, self._uiTab ),
      'variables': utils.WindowID( vars_window, self._uiTab ),
      'watches': utils.WindowID( watch_window, self._uiTab ),
      'output': utils.WindowID( output_window, self._uiTab ),
      'eval': None, # updated every time eval popup is opened
      'breakpoints': vim.vars[ 'vimspector_session_windows' ].get(
        'breakpoints' ) # same as above, but for breakpoints
    }
    with utils.RestoreCursorPosition():
      with utils.RestoreCurrentWindow():
        with utils.RestoreCurrentBuffer( vim.current.window ):
          vim.command( 'doautocmd User VimspectorUICreated' )


  @RequiresUI()
  def ClearCurrentFrame( self ):
    self.SetCurrentFrame( None )

  @RequiresUI()
  def SetCurrentFrame( self, frame, reason = '' ):
    if not frame:
      self._stackTraceView.Clear()
      self._variablesView.Clear()

    if not self._codeView.SetCurrentFrame( frame ):
      return False

    # the codeView.SetCurrentFrame already checked the frame was valid and
    # countained a valid source
    assert frame
    if self._codeView.current_syntax not in ( 'ON', 'OFF' ):
      self._variablesView.SetSyntax( self._codeView.current_syntax )
      self._stackTraceView.SetSyntax( self._codeView.current_syntax )
    else:
      self._variablesView.SetSyntax( None )
      self._stackTraceView.SetSyntax( None )

    self._variablesView.LoadScopes( frame )
    self._variablesView.EvaluateWatches( frame )

    if reason == 'stopped':
      self._breakpoints.ClearTemporaryBreakpoint( frame[ 'source' ][ 'path' ],
                                                  frame[ 'line' ] )

    return True

  def _StartDebugAdapter( self ):
    self._splash_screen = utils.DisplaySplash(
      self._api_prefix,
      self._splash_screen,
      "Starting debug adapter..." )

    if self._connection:
      utils.UserMessage( 'The connection is already created. Please try again',
                         persist = True )
      return False

    self._logger.info( 'Starting debug adapter with: %s',
                       json.dumps( self._adapter ) )

    self._init_complete = False
    self._launch_complete = False
    self._run_on_server_exit = None

    self._connection_type = 'job'
    if 'port' in self._adapter:
      self._connection_type = 'channel'

      if self._adapter[ 'port' ] == 'ask':
        port = utils.AskForInput( 'Enter port to connect to: ' )
        if port is None:
          self._Reset()
          return False
        self._adapter[ 'port' ] = port

    self._connection_type = self._api_prefix + self._connection_type
    self._logger.debug( f"Connection Type: { self._connection_type }" )

    self._adapter[ 'env' ] = self._adapter.get( 'env', {} )

    if 'cwd' not in self._adapter:
      self._adapter[ 'cwd' ] = os.getcwd()

    vim.vars[ '_vimspector_adapter_spec' ] = self._adapter

    # if the debug adapter is lame and requires a terminal or has any
    # input/output on stdio, then launch it that way
    if self._adapter.get( 'tty', False ):
      if 'port' not in self._adapter:
        utils.UserMessage( "Invalid adapter configuration. When using a tty, "
                           "communication must use socket. Add the 'port' to "
                           "the adapter config." )
        return False

      if 'command' not in self._adapter:
        utils.UserMessage( "Invalid adapter configuration. When using a tty, "
                           "a command must be supplied. Add the 'commmand' to "
                           "the adapter config." )
        return False

      command = self._adapter[ 'command' ]
      if isinstance( command, str ):
        command = shlex.split( command )

      self._adapter_term = terminal.LaunchTerminal(
          self._api_prefix,
          {
            'args': command,
            'cwd': self._adapter[ 'cwd' ],
            'env': self._adapter[ 'env' ],
          },
          self._codeView._window,
          self._adapter_term )

    if not vim.eval( "vimspector#internal#{}#StartDebugSession( "
                     "  g:_vimspector_adapter_spec "
                     ")".format( self._connection_type ) ):
      self._logger.error( "Unable to start debug server" )
      self._splash_screen = utils.DisplaySplash(
        self._api_prefix,
        self._splash_screen,
        [
          "Unable to start or connect to debug adapter",
          "",
          "Check :messages and :VimspectorToggleLog for more information.",
          "",
          ":VimspectorReset to close down vimspector",
        ] )
      return False
    else:
      handlers = [ self ]
      if 'custom_handler' in self._adapter:
        spec = self._adapter[ 'custom_handler' ]
        if isinstance( spec, dict ):
          module = spec[ 'module' ]
          cls = spec[ 'class' ]
        else:
          module, cls = spec.rsplit( '.', 1 )

        try:
          CustomHandler = getattr( importlib.import_module( module ), cls )
          handlers = [ CustomHandler( self ), self ]
        except ImportError:
          self._logger.exception( "Unable to load custom adapter %s",
                                  spec )

      self._connection = debug_adapter_connection.DebugAdapterConnection(
        handlers,
        lambda msg: utils.Call(
          "vimspector#internal#{}#Send".format( self._connection_type ),
          msg ),
        self._adapter.get( 'sync_timeout' ),
        self._adapter.get( 'async_timeout' ) )

    self._logger.info( 'Debug Adapter Started' )
    return True

  def _StopDebugAdapter( self, interactive = False, callback = None ):
    arguments = {}

    def disconnect():
      self._splash_screen = utils.DisplaySplash(
        self._api_prefix,
        self._splash_screen,
        "Shutting down debug adapter..." )

      def handler( *args ):
        self._splash_screen = utils.HideSplash( self._api_prefix,
                                                self._splash_screen )

        if callback:
          self._logger.debug( "Setting server exit handler before disconnect" )
          assert not self._run_on_server_exit
          self._run_on_server_exit = callback

        vim.eval( 'vimspector#internal#{}#StopDebugSession()'.format(
          self._connection_type ) )

      self._connection.DoRequest(
        handler,
        {
          'command': 'disconnect',
          'arguments': arguments,
        },
        failure_handler = handler,
        timeout = self._connection.sync_timeout )

    if not interactive:
      disconnect()
    elif not self._server_capabilities.get( 'supportTerminateDebuggee' ):
      disconnect()
    elif not self._stackTraceView.AnyThreadsRunning():
      disconnect()
    else:
      def handle_choice( choice ):
        if choice == 1:
          # yes
          arguments[ 'terminateDebuggee' ] = True
        elif choice == 2:
          # no
          arguments[ 'terminateDebuggee' ] = False
        elif choice <= 0:
          # Abort
          return
        # Else, use server default

        disconnect()

      utils.Confirm( self._api_prefix,
                     "Terminate debuggee?",
                     handle_choice,
                     default_value = 3,
                     options = [ '(Y)es', '(N)o', '(D)efault' ],
                     keys = [ 'y', 'n', 'd' ] )


  def _PrepareAttach( self, adapter_config, launch_config ):
    attach_config = adapter_config.get( 'attach' )

    if not attach_config:
      return

    if 'remote' in attach_config:
      # FIXME: We almost want this to feed-back variables to be expanded later,
      # e.g. expand variables when we use them, not all at once. This would
      # remove the whole %PID% hack.
      remote = attach_config[ 'remote' ]
      remote_exec_cmd = self._GetRemoteExecCommand( remote )

      # FIXME: Why does this not use self._GetCommands ?
      pid_cmd = remote_exec_cmd + remote[ 'pidCommand' ]

      self._logger.debug( 'Getting PID: %s', pid_cmd )
      pid = subprocess.check_output( pid_cmd ).decode( 'utf-8' ).strip()
      self._logger.debug( 'Got PID: %s', pid )

      if not pid:
        # FIXME: We should raise an exception here or something
        utils.UserMessage( 'Unable to get PID', persist = True )
        return

      if 'initCompleteCommand' in remote:
        initcmd = remote_exec_cmd + remote[ 'initCompleteCommand' ][ : ]
        for index, item in enumerate( initcmd ):
          initcmd[ index ] = item.replace( '%PID%', pid )

        self._on_init_complete_handlers.append(
          lambda: subprocess.check_call( initcmd ) )

      commands = self._GetCommands( remote, 'attach' )

      for command in commands:
        cmd = remote_exec_cmd + command

        for index, item in enumerate( cmd ):
          cmd[ index ] = item.replace( '%PID%', pid )

        self._logger.debug( 'Running remote app: %s', cmd )
        self._remote_term = terminal.LaunchTerminal(
            self._api_prefix,
            {
                'args': cmd,
                'cwd': os.getcwd()
            },
            self._codeView._window,
            self._remote_term )
    else:
      if attach_config[ 'pidSelect' ] == 'ask':
        prop = attach_config[ 'pidProperty' ]
        if prop not in launch_config:
          pid = utils.AskForInput( 'Enter PID to attach to: ' )
          if pid is None:
            return
          launch_config[ prop ] = pid
        return
      elif attach_config[ 'pidSelect' ] == 'none':
        return

      raise ValueError( 'Unrecognised pidSelect {0}'.format(
        attach_config[ 'pidSelect' ] ) )

    if 'delay' in attach_config:
      utils.UserMessage( f"Waiting ( { attach_config[ 'delay' ] } )..." )
      vim.command( f'sleep { attach_config[ "delay" ] }' )


  def _PrepareLaunch( self, command_line, adapter_config, launch_config ):
    run_config = adapter_config.get( 'launch', {} )

    if 'remote' in run_config:
      remote = run_config[ 'remote' ]
      remote_exec_cmd = self._GetRemoteExecCommand( remote )
      commands = self._GetCommands( remote, 'run' )

      for index, command in enumerate( commands ):
        cmd = remote_exec_cmd + command[ : ]
        full_cmd = []
        for item in cmd:
          if isinstance( command_line, list ):
            if item == '%CMD%':
              full_cmd.extend( command_line )
            else:
              full_cmd.append( item )
          else:
            full_cmd.append( item.replace( '%CMD%', command_line ) )

        self._logger.debug( 'Running remote app: %s', full_cmd )
        self._remote_term = terminal.LaunchTerminal(
            self._api_prefix,
            {
                'args': full_cmd,
                'cwd': os.getcwd()
            },
            self._codeView._window,
            self._remote_term )

    if 'delay' in run_config:
      utils.UserMessage( f"Waiting ( {run_config[ 'delay' ]} )..." )
      vim.command( f'sleep { run_config[ "delay" ] }' )



  def _GetSSHCommand( self, remote ):
    ssh = [ 'ssh' ] + remote.get( 'ssh', {} ).get( 'args', [] )
    if 'account' in remote:
      ssh.append( remote[ 'account' ] + '@' + remote[ 'host' ] )
    else:
      ssh.append( remote[ 'host' ] )

    return ssh

  def _GetDockerCommand( self, remote ):
    docker = [ 'docker', 'exec' ]
    docker.append( remote[ 'container' ] )
    return docker

  def _GetRemoteExecCommand( self, remote ):
    is_ssh_cmd = any( key in remote for key in [ 'ssh',
                                                 'host',
                                                 'account', ] )
    is_docker_cmd = 'container' in remote

    if is_ssh_cmd:
      return self._GetSSHCommand( remote )
    elif is_docker_cmd:
      return self._GetDockerCommand( remote )
    raise ValueError( 'Could not determine remote exec command' )


  def _GetCommands( self, remote, pfx ):
    commands = remote.get( pfx + 'Commands', None )

    if isinstance( commands, list ):
      return commands
    elif commands is not None:
      raise ValueError( "Invalid commands; must be list" )

    command = remote[ pfx + 'Command' ]

    if isinstance( command, str ):
      command = shlex.split( command )

    if not isinstance( command, list ):
      raise ValueError( "Invalid command; must be list/string" )

    if not command:
      raise ValueError( 'Could not determine commands for ' + pfx )

    return [ command ]

  def _Initialise( self ):
    self._splash_screen = utils.DisplaySplash(
      self._api_prefix,
      self._splash_screen,
      "Initializing debug adapter..." )

    # For a good explaination as to why this sequence is the way it is, see
    # https://github.com/microsoft/vscode/issues/4902#issuecomment-368583522
    #
    # In short, we do what VSCode does:
    # 1. Send the initialize request and wait for the reply
    # 2a. When we recieve the initialize reply, send the launch/attach request
    # 2b. When we receive the initialized notification, send the breakpoints
    #    - if supportsConfigurationDoneRequest, send it
    #    - else, send the empty exception breakpoints request
    # 3. When we have recieved both the receive the launch/attach reply *and*
    #    the connfiguration done reply (or, if we didn't send one, a response to
    #    the empty exception breakpoints request), we request threads
    # 4. The threads response triggers things like scopes and triggers setting
    #    the current frame.
    #
    def handle_initialize_response( msg ):
      self._server_capabilities = msg.get( 'body' ) or {}
      self._breakpoints.SetServerCapabilities( self._server_capabilities )
      self._variablesView.SetServerCapabilities( self._server_capabilities )
      self._Launch()

    self._connection.DoRequest( handle_initialize_response, {
      'command': 'initialize',
      'arguments': {
        'adapterID': self._adapter.get( 'name', 'adapter' ),
        'clientID': 'vimspector',
        'clientName': 'vimspector',
        'linesStartAt1': True,
        'columnsStartAt1': True,
        'locale': 'en_GB',
        'pathFormat': 'path',
        'supportsVariableType': True,
        'supportsVariablePaging': False,
        'supportsRunInTerminalRequest': True,
        'supportsMemoryReferences': True
      },
    } )


  def OnFailure( self, reason, request, message ):
    msg = "Request for '{}' failed: {}\nResponse: {}".format( request,
                                                              reason,
                                                              message )
    self._outputView.Print( 'server', msg )


  def _Prepare( self ):
    self._on_init_complete_handlers = []

    self._logger.debug( "LAUNCH!" )
    self._launch_config = {}
    # TODO: Should we use core_utils.override for this? That would strictly be a
    # change in behaviour as dicts in the specific configuration would merge
    # with dicts in the adapter, where before they would overlay
    self._launch_config.update( self._adapter.get( 'configuration', {} ) )
    self._launch_config.update( self._configuration[ 'configuration' ] )

    request = self._configuration.get(
      'remote-request',
      self._launch_config.get( 'request', 'launch' ) )

    if request == "attach":
      self._splash_screen = utils.DisplaySplash(
        self._api_prefix,
        self._splash_screen,
        "Attaching to debuggee..." )

      self._PrepareAttach( self._adapter, self._launch_config )
    elif request == "launch":
      self._splash_screen = utils.DisplaySplash(
        self._api_prefix,
        self._splash_screen,
        "Launching debuggee..." )

      # FIXME: This cmdLine hack is not fun.
      self._PrepareLaunch( self._configuration.get( 'remote-cmdLine', [] ),
                           self._adapter,
                           self._launch_config )

    # FIXME: name is mandatory. Forcefully add it (we should really use the
    # _actual_ name, but that isn't actually remembered at this point)
    if 'name' not in self._launch_config:
      self._launch_config[ 'name' ] = 'test'


  def _Launch( self ):
    def failure_handler( reason, msg ):
      text = [
        'Launch Failed',
        '',
        reason,
        '',
        'Use :VimspectorReset to close'
      ]
      self._logger.info( "Launch failed: %s", '\n'.join( text ) )
      self._splash_screen = utils.DisplaySplash( self._api_prefix,
                                                 self._splash_screen,
                                                 text )

    self._connection.DoRequest(
      lambda msg: self._OnLaunchComplete(),
      {
        'command': self._launch_config[ 'request' ],
        'arguments': self._launch_config
      },
      failure_handler )


  def _OnLaunchComplete( self ):
    self._launch_complete = True
    self._LoadThreadsIfReady()

  def _OnInitializeComplete( self ):
    self._init_complete = True
    self._LoadThreadsIfReady()

  def _LoadThreadsIfReady( self ):
    # NOTE: You might think we should only load threads on a stopped event,
    # but the spec is clear:
    #
    #   After a successful launch or attach the development tool requests the
    #   baseline of currently existing threads with the threads request and
    #   then starts to listen for thread events to detect new or terminated
    #   threads.
    #
    # Of course, specs are basically guidelines. MS's own cpptools simply
    # doesn't respond top threads request when attaching via gdbserver. At
    # least it would apear that way.
    #
    # As it turns out this is due to a bug in gdbserver which means that
    # attachment doesn't work due to sending the signal to the process group
    # leader rather than the process. The workaround is to manually SIGTRAP the
    # PID.
    #
    if self._launch_complete and self._init_complete:
      self._splash_screen = utils.HideSplash( self._api_prefix,
                                              self._splash_screen )

      for h in self._on_init_complete_handlers:
        h()
      self._on_init_complete_handlers = []

      self._stackTraceView.LoadThreads( True )


  @IfConnected()
  @RequiresUI()
  def PrintDebugInfo( self ):
    def Line():
      return ( "--------------------------------------------------------------"
               "------------------" )

    def Pretty( obj ):
      if obj is None:
        return [ "None" ]
      return [ Line() ] + json.dumps( obj, indent=2 ).splitlines() + [ Line() ]


    debugInfo = [
      "Vimspector Debug Info",
      Line(),
      f"ConnectionType: { self._connection_type }",
      "Adapter: " ] + Pretty( self._adapter ) + [
      "Configuration: " ] + Pretty( self._configuration ) + [
      f"API Prefix: { self._api_prefix }",
      f"Launch/Init: { self._launch_complete } / { self._init_complete }",
      f"Workspace Root: { self._workspace_root }",
      "Launch Config: " ] + Pretty( self._launch_config ) + [
      "Server Capabilities: " ] + Pretty( self._server_capabilities ) + [
      "Line Breakpoints: " ] + Pretty( self._breakpoints._line_breakpoints ) + [
      "Func Breakpoints: " ] + Pretty( self._breakpoints._func_breakpoints ) + [
      "Ex Breakpoints: " ] + Pretty( self._breakpoints._exception_breakpoints )

    self._outputView.ClearCategory( 'DebugInfo' )
    self._outputView.Print( "DebugInfo", debugInfo )
    self.ShowOutput( "DebugInfo" )


  def OnEvent_loadedSource( self, msg ):
    pass


  def OnEvent_capabilities( self, msg ):
    self._server_capabilities.update(
      ( msg.get( 'body' ) or {} ).get( 'capabilities' ) or {} )


  def OnEvent_initialized( self, message ):
    def onBreakpointsDone():
      self._breakpoints.Refresh()
      if self._server_capabilities.get( 'supportsConfigurationDoneRequest' ):
        self._connection.DoRequest(
          lambda msg: self._OnInitializeComplete(),
          {
            'command': 'configurationDone',
          }
        )
      else:
        self._OnInitializeComplete()

    self._breakpoints.SetConfiguredBreakpoints(
      self._configuration.get( 'breakpoints', {} ) )
    self._breakpoints.UpdateUI( onBreakpointsDone )

  def OnEvent_thread( self, message ):
    self._stackTraceView.OnThreadEvent( message[ 'body' ] )


  def OnEvent_breakpoint( self, message ):
    reason = message[ 'body' ][ 'reason' ]
    bp = message[ 'body' ][ 'breakpoint' ]
    if reason == 'changed':
      self._breakpoints.UpdatePostedBreakpoint( bp )
    elif reason == 'new':
      self._breakpoints.AddPostedBreakpoint( bp )
    elif reason == 'removed':
      self._breakpoints.DeletePostedBreakpoint( bp )
    else:
      utils.UserMessage(
        'Unrecognised breakpoint event (undocumented): {0}'.format( reason ),
        persist = True )

  def OnRequest_runInTerminal( self, message ):
    params = message[ 'arguments' ]

    if not params.get( 'cwd' ) :
      params[ 'cwd' ] = self._workspace_root
      self._logger.debug( 'Defaulting working directory to %s',
                          params[ 'cwd' ] )

    term_id = self._codeView.LaunchTerminal( params )

    response = {
      'processId': int( utils.Call(
        'vimspector#internal#{}term#GetPID'.format( self._api_prefix ),
        term_id ) )
    }

    self._connection.DoResponse( message, None, response )

  def OnEvent_terminated( self, message ):
    # The debugging _session_ has terminated. This does not mean that the
    # debuggee has terminated (that's the exited event).
    #
    # We will handle this when the server actually exists.
    #
    # FIXME we should always wait for this event before disconnecting closing
    # any socket connection
    self.SetCurrentFrame( None )


  def OnEvent_exited( self, message ):
    utils.UserMessage( 'The debuggee exited with status code: {}'.format(
      message[ 'body' ][ 'exitCode' ] ) )
    self._stackTraceView.OnExited( message )
    self._codeView.SetCurrentFrame( None )

  def OnEvent_process( self, message ):
    utils.UserMessage( 'The debuggee was started: {}'.format(
      message[ 'body' ][ 'name' ] ) )

  def OnEvent_module( self, message ):
    pass

  def OnEvent_continued( self, message ):
    self._stackTraceView.OnContinued( message[ 'body' ] )
    self._codeView.SetCurrentFrame( None )

  def Clear( self ):
    self._codeView.Clear()
    self._stackTraceView.Clear()
    self._variablesView.Clear()

  def OnServerExit( self, status ):
    self._logger.info( "The server has terminated with status %s",
                       status )
    self.Clear()

    if self._connection is not None:
      # Can be None if the server dies _before_ StartDebugSession vim function
      # returns
      self._connection.Reset()

    self._stackTraceView.ConnectionClosed()
    self._variablesView.ConnectionClosed()
    self._outputView.ConnectionClosed()
    self._breakpoints.ConnectionClosed()

    self._ResetServerState()

    if self._run_on_server_exit:
      self._logger.debug( "Running server exit handler" )
      callback = self._run_on_server_exit
      self._run_on_server_exit = None
      callback()
    else:
      self._logger.debug( "No server exit handler" )

  def OnEvent_output( self, message ):
    if self._outputView:
      self._outputView.OnOutput( message[ 'body' ] )

  def OnEvent_stopped( self, message ):
    event = message[ 'body' ]
    reason = event.get( 'reason' ) or '<protocol error>'
    description = event.get( 'description' )
    text = event.get( 'text' )

    if description:
      explanation = description + '(' + reason + ')'
    else:
      explanation = reason

    if text:
      explanation += ': ' + text

    msg = 'Paused in thread {0} due to {1}'.format(
      event.get( 'threadId', '<unknown>' ),
      explanation )
    utils.UserMessage( msg, persist = True )

    if self._outputView:
      self._outputView.Print( 'server', msg )

    self._stackTraceView.OnStopped( event )

  def BreakpointsAsQuickFix( self ):
    return self._breakpoints.BreakpointsAsQuickFix()

  def ListBreakpoints( self ):
    self._breakpoints.ToggleBreakpointsView()

  def ToggleBreakpointViewBreakpoint( self ):
    self._breakpoints.ToggleBreakpointViewBreakpoint()

  def ToggleAllBreakpointsViewBreakpoint( self ):
    self._breakpoints.ToggleAllBreakpointsViewBreakpoint()

  def DeleteBreakpointViewBreakpoint( self ):
    self._breakpoints.ClearBreakpointViewBreakpoint()

  def JumpToBreakpointViewBreakpoint( self ):
    self._breakpoints.JumpToBreakpointViewBreakpoint()

  def ToggleBreakpoint( self, options ):
    return self._breakpoints.ToggleBreakpoint( options )


  def RunTo( self, file_name, line ):
    self.ClearTemporaryBreakpoints()
    self.SetLineBreakpoint( file_name,
                            line,
                            { 'temporary': True },
                            lambda: self.Continue() )

  @IfConnected()
  def GoTo( self, file_name, line ):
    def failure_handler( reason, *args ):
      utils.UserMessage( f"Can't jump to location: {reason}", error=True )

    def handle_targets( msg ):
      targets = msg.get( 'body', {} ).get( 'targets', [] )
      if not targets:
        failure_handler( "No targets" )
        return

      if len( targets ) == 1:
        target_selected = 0
      else:
        target_selected = utils.SelectFromList( "Which target?", [
          t[ 'label' ] for t in targets
        ], ret = 'index' )

      if target_selected is None:
        return

      self._connection.DoRequest( None, {
        'command': 'goto',
        'arguments': {
          'threadId': self._stackTraceView.GetCurrentThreadId(),
          'targetId': targets[ target_selected ][ 'id' ]
        },
      }, failure_handler )

    if not self._server_capabilities.get( 'supportsGotoTargetsRequest', False ):
      failure_handler( "Server doesn't support it" )
      return

    self._connection.DoRequest( handle_targets, {
      'command': 'gotoTargets',
      'arguments': {
        'source': {
          'path': utils.NormalizePath( file_name )
        },
        'line': line
      },
    }, failure_handler )


  def ClearTemporaryBreakpoints( self ):
    return self._breakpoints.ClearTemporaryBreakpoints()

  def SetLineBreakpoint( self, file_name, line_num, options, then = None ):
    return self._breakpoints.SetLineBreakpoint( file_name,
                                                line_num,
                                                options,
                                                then )

  def ClearLineBreakpoint( self, file_name, line_num ):
    return self._breakpoints.ClearLineBreakpoint( file_name, line_num )

  def ClearBreakpoints( self ):
    return self._breakpoints.ClearBreakpoints()

  def AddFunctionBreakpoint( self, function, options ):
    return self._breakpoints.AddFunctionBreakpoint( function, options )


def PathsToAllGadgetConfigs( vimspector_base, current_file ):
  yield install.GetGadgetConfigFile( vimspector_base )
  for p in sorted( glob.glob(
    os.path.join( install.GetGadgetConfigDir( vimspector_base ),
                  '*.json' ) ) ):
    yield p

  yield utils.PathToConfigFile( '.gadgets.json',
                                os.path.dirname( current_file ) )


def PathsToAllConfigFiles( vimspector_base, current_file, filetypes ):
  for ft in filetypes + [ '_all' ]:
    for p in sorted( glob.glob(
      os.path.join( install.GetConfigDirForFiletype( vimspector_base, ft ),
                    '*.json' ) ) ):
      yield p

  for ft in filetypes:
    yield utils.PathToConfigFile( f'.vimspector.{ft}.json',
                                  os.path.dirname( current_file ) )

  yield utils.PathToConfigFile( '.vimspector.json',
                                os.path.dirname( current_file ) )
