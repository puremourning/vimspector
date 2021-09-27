# vimspector - A multi-language debugging system for Vim
# Copyright 2019 Ben Jackson
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

from collections import defaultdict

import vim
import os
from functools import partial
import logging

import json
from vimspector import utils, signs, settings


class BreakpointsView( object ):
  def __init__( self ):
    self._breakpoint_win = None
    self._breakpoint_list = []

  def _UpdateView( self, breakpoint_list ):
    def _formatEntry( el ):
      prefix = ''
      if el.get( 'type' ) == 'L':
        prefix = '{}:{} '.format( os.path.basename( el.get( 'filename' ) ),
          el.get( 'lnum' ) )

      return '{}{}'.format( prefix, el.get( 'text' ) )

    if self._breakpoint_win is None or not self._breakpoint_win.valid:

      vim.command( f'botright { settings.Int( "bottombar_height" ) }new' )
      self._breakpoint_win = vim.current.window

      # neovim madness need to re-assign the dict to trigger rpc call
      # see https://github.com/neovim/pynvim/issues/261
      session_wins = vim.vars[ 'vimspector_session_windows' ]
      session_wins[ 'breakpoints' ] = utils.WindowID( self._breakpoint_win )
      vim.vars[ 'vimspector_session_windows' ] = session_wins

      utils.SetUpScratchBuffer( self._breakpoint_win.buffer,
                                "vimspector.Breakpoints" )

      mappings = settings.Dict( 'mappings' )[ 'breakpoints' ]
      for mapping in utils.GetVimList( mappings, 'toggle' ):
        vim.command( f'nnoremap <silent> <buffer> { mapping } '
                     ':<C-u>call '
                     'vimspector#ToggleBreakpointViewBreakpoint()<CR>' )

      for mapping in utils.GetVimList( mappings, 'delete' ):
        vim.command( f'nnoremap <silent> <buffer> { mapping } '
                     ':<C-u>call '
                     'vimspector#DeleteBreakpointViewBreakpoint()<CR>' )

      for mapping in utils.GetVimList( mappings, 'jump_to' ):
        vim.command( f'nnoremap <silent> <buffer> { mapping } '
                     ':<C-u>call '
                     'vimspector#JumpToBreakpointViewBreakpoint()<CR>' )
      # set highlighting
      vim.eval( "matchadd( 'WarningMsg', 'ENABLED', 100 )" )
      vim.eval( "matchadd( 'LineNr', 'DISABLED', 100 )" )
      vim.eval( "matchadd( 'Title', '\\v^\\S+:{0,}', 100 )" )

      # we want to maintain the height of the window
      self._breakpoint_win.options[ "winfixheight" ] = True

    self._breakpoint_list = breakpoint_list

    breakpoint_list = list( map( _formatEntry, breakpoint_list ) )

    with utils.ModifiableScratchBuffer( self._breakpoint_win.buffer ):
      with utils.RestoreCursorPosition():
        utils.SetBufferContents( self._breakpoint_win.buffer, breakpoint_list )

  def CloseBreakpoints( self ):
    if self._breakpoint_win and self._breakpoint_win.valid:
      with utils.LetCurrentTabpage( self._breakpoint_win.tabpage ):
        vim.command( "{}close".format( self._breakpoint_win.number ) )

  def GetBreakpointForLine( self ):
    if (
      self._breakpoint_win is None
      or not self._breakpoint_win.valid
      or vim.current.window.number != self._breakpoint_win.number
      or not self._breakpoint_list
    ):
      return None

    line_num = int( vim.eval( 'getpos( \'.\' )' )[ 1 ] )

    index = max( 0, min( len( self._breakpoint_list ) - 1, line_num - 1 ) )
    return self._breakpoint_list[ index ]

  def ToggleBreakpointView( self, breakpoint_list ):
    if self._breakpoint_win and self._breakpoint_win.valid:
      old_tabpage_number = self._breakpoint_win.tabpage.number
      # we want to grab current tabpage number now
      # because closing breakpoint view might
      # also close the entire tab
      current_tabpage_number = vim.current.tabpage.number
      self.CloseBreakpoints()
      # if we just closed breakpoint view in a different tab,
      # we want to re-open it in the current tab
      if old_tabpage_number != current_tabpage_number:
        self._UpdateView( breakpoint_list )
    else:
      self._UpdateView( breakpoint_list )

  def RefreshBreakpoints( self, breakpoint_list ):
    if self._breakpoint_win and self._breakpoint_win.valid:
      self._UpdateView( breakpoint_list )


class ProjectBreakpoints( object ):
  def __init__( self, render_event_emitter, IsPCPresentAt ):
    self._connection = None
    self._logger = logging.getLogger( __name__ )
    self._render_subject = render_event_emitter.subscribe( self.Refresh )
    self._IsPCPresentAt = IsPCPresentAt
    utils.SetUpLogging( self._logger )

    # These are the user-entered breakpoints.
    self._line_breakpoints = defaultdict( list )
    self._func_breakpoints = []
    self._exception_breakpoints = None
    self._configured_breakpoints = {}

    self._server_capabilities = {}

    self._next_sign_id = 1

    self._breakpoints_view = BreakpointsView()

    if not signs.SignDefined( 'vimspectorBP' ):
      signs.DefineSign( 'vimspectorBP',
                        text = '●',
                        double_text = '●',
                        texthl = 'WarningMsg' )

    if not signs.SignDefined( 'vimspectorBPCond' ):
      signs.DefineSign( 'vimspectorBPCond',
                        text = '◆',
                        double_text = '◆',
                        texthl = 'WarningMsg' )

    if not signs.SignDefined( 'vimspectorBPLog' ):
      signs.DefineSign( 'vimspectorBPLog',
                        text = '◆',
                        double_text = '◆',
                        texthl = 'SpellRare' )

    if not signs.SignDefined( 'vimspectorBPDisabled' ):
      signs.DefineSign( 'vimspectorBPDisabled',
                        text = '●',
                        double_text = '●',
                        texthl = 'LineNr' )


  def ConnectionUp( self, connection ):
    self._connection = connection

  def SetServerCapabilities( self, server_capabilities ):
    self._server_capabilities = server_capabilities


  def ConnectionClosed( self ):
    self._server_capabilities = {}
    self._connection = None
    self.UpdateUI()

    # NOTE: we don't reset self._exception_breakpoints because we don't want to
    # re-ask the user every time for the sane info.

    # FIXME: If the adapter type changes, we should probably forget this ?

  def ToggleBreakpointsView( self ):
    self._breakpoints_view.ToggleBreakpointView( self.BreakpointsAsQuickFix() )

  def ToggleBreakpointViewBreakpoint( self ):
    bp = self._breakpoints_view.GetBreakpointForLine()
    if bp:
      if bp.get( 'type' ) == 'F':
        self.ClearFunctionBreakpoint( bp.get( 'filename' ) )
      else:
        self._ToggleBreakpoint( None, bp.get( 'filename' ), bp.get( 'lnum' ),
                                False )

  def JumpToBreakpointViewBreakpoint( self ):
    bp = self._breakpoints_view.GetBreakpointForLine()
    if bp and bp.get( 'type' ) != 'F':
      success = int( vim.eval(
          f'win_gotoid( bufwinid( \'{ bp[ "filename" ] }\' ) )' ) )

      if not success:
        vim.command( "leftabove split {}".format( bp.get( 'filename' ) ) )

      vim.eval( "setpos( '.', [0, {}, 1, 1] )".format( bp.get( 'lnum' ) ) )

  def ClearBreakpointViewBreakpoint( self ):
    bp = self._breakpoints_view.GetBreakpointForLine()
    if bp:
      if bp.get( 'type' ) == 'F':
        self.ClearFunctionBreakpoint( bp.get( 'filename' ) )
      else:
        self.ClearLineBreakpoint( bp.get( 'filename' ), bp.get( 'lnum' ) )

  def BreakpointsAsQuickFix( self ):
    qf = []
    for file_name, breakpoints in self._line_breakpoints.items():
      for bp in breakpoints:
        self._SignToLine( file_name, bp )
        qf.append( {
          'filename': file_name,
          'lnum': bp[ 'line' ],
          'col': 1,
          'type': 'L',
          'valid': 1 if bp[ 'state' ] == 'ENABLED' else 0,
          'text': "Line breakpoint - {}: {}".format(
            bp[ 'state' ],
            json.dumps( bp[ 'options' ] ) )
        } )
    for bp in self._func_breakpoints:
      qf.append( {
        'filename': bp[ 'function' ],
        'lnum': 1,
        'col': 1,
        'type': 'F',
        'valid': 1,
        'text': "{}: Function breakpoint - {}".format( bp[ 'function' ],
                                                      bp[ 'options' ] ),
      } )

    return qf


  def ClearBreakpoints( self ):
    # These are the user-entered breakpoints.
    for file_name, breakpoints in self._line_breakpoints.items():
      for bp in breakpoints:
        self._SignToLine( file_name, bp )
        if 'sign_id' in bp:
          signs.UnplaceSign( bp[ 'sign_id' ], 'VimspectorBP' )

    self._line_breakpoints = defaultdict( list )
    self._func_breakpoints = []
    self._exception_breakpoints = None

    self.UpdateUI()


  def _FindLineBreakpoint( self, file_name, line ):
    file_name = _NormaliseFileName( file_name )
    for index, bp in enumerate( self._line_breakpoints[ file_name ] ):
      self._SignToLine( file_name, bp )
      if bp[ 'line' ] == line:
        return bp, index

    return None, None

  def _FindVerifiedBreakpoint( self, breakpoint_id ):
    if breakpoint_id is None:
      return None, None

    for _, breakpoint_list in self._line_breakpoints.items():
      for index, breakpoint in enumerate( breakpoint_list ):
        if 'id' in breakpoint and breakpoint[ 'id' ] == breakpoint_id:
          return breakpoint, index

    return None, None

  def UpdateVerifiedBreakpoint( self, breakpoint ):
    bp, _ = self._FindVerifiedBreakpoint( breakpoint.get( 'id' ) )
    if bp is None:
      return

    # we are just updating position of the existing breakpoint
    bp[ 'line' ]  = breakpoint.get( 'line' )
    self.UpdateUI()

  def AddVerifiedBreakpoints( self, breakpoints ):
    for breakpoint in breakpoints:
      source = breakpoint.get( 'source' )
      if not source or 'path' not in source:
        self._logger.warn( 'missing source/path in breakpoint {0}'.format(
          json.dumps( breakpoint ) ) )
        continue

      self._PutLineBreakpoint( source.get( 'path' ), breakpoint.get( 'line' ),
        None, breakpoint.get( 'id' ) )

    self._logger.debug( 'Breakpoints at this point: {0}'.format(
      json.dumps( self._line_breakpoints, indent = 2 ) ) )


  def DeleteVerifiedBreakpoint( self, breakpoint ):
    bp, index = self._FindVerifiedBreakpoint( breakpoint.get( 'id' ) )

    if bp is not None:
      self._DeleteLineBreakpoint( bp, bp.get( 'path' ), index )

    self.UpdateUI()

  def IsBreakpointPresentAt( self, file_path, line ):
    return self._FindLineBreakpoint( file_path, line )[ 0 ] is not None

  def _PutLineBreakpoint( self, file_name, line, options, id = None ):
    self._line_breakpoints[ _NormaliseFileName( file_name ) ].append( {
      'state': 'ENABLED',
      'line': line,
      'options': options,
      'id': id,
      'path': path
      # 'sign_id': <filled in when placed>,
      #
      # Used by other breakpoint types (specified in options):
      # 'condition': ...,
      # 'hitCondition': ...,
      # 'logMessage': ...
    } )


  def _DeleteLineBreakpoint( self, bp, file_name, index ):
    if 'sign_id' in bp:
      signs.UnplaceSign( bp[ 'sign_id' ], 'VimspectorBP' )
    del self._line_breakpoints[ _NormaliseFileName( file_name ) ][ index ]

  def _ToggleBreakpoint( self, options, file_name, line, shouldDelete = True ):
    if not file_name:
      return

    bp, index = self._FindLineBreakpoint( file_name, line )
    if bp is None:
      # ADD
      self._PutLineBreakpoint( file_name, line, options )
    elif bp[ 'state' ] == 'ENABLED' and not self._connection:
      # DISABLE
      bp[ 'state' ] = 'DISABLED'
    elif not shouldDelete and not self._connection:
      bp[ 'state' ] = 'ENABLED'
    else:
      # DELETE
      self._DeleteLineBreakpoint( bp, file_name, index )

    self.UpdateUI()

  def ClearFunctionBreakpoint( self, function_name ):
    self._func_breakpoints = [ item for item in self._func_breakpoints
                                if item[ 'function' ] != function_name ]
    self.UpdateUI()

  def ToggleBreakpoint( self, options ):
    line, _ = vim.current.window.cursor
    file_name = vim.current.buffer.name
    self._ToggleBreakpoint( options, file_name, line )

  def SetLineBreakpoint( self, file_name, line_num, options, then = None ):
    bp, _ = self._FindLineBreakpoint( file_name, line_num )
    if bp is not None:
      bp[ 'options' ] = options
      return
    self._PutLineBreakpoint( file_name, line_num, options )
    self.UpdateUI( then )


  def ClearLineBreakpoint( self, file_name, line_num ):
    bp, index = self._FindLineBreakpoint( file_name, line_num )
    if bp is None:
      return
    self._DeleteLineBreakpoint( bp, file_name, index )
    self.UpdateUI()


  def ClearTemporaryBreakpoint( self, file_name, line_num ):
    bp, index = self._FindLineBreakpoint( file_name, line_num )
    if bp is None:
      return
    if bp[ 'options' ].get( 'temporary' ):
      self._DeleteLineBreakpoint( bp, file_name, index )
      self.UpdateUI()


  def ClearTemporaryBreakpoints( self ):
    to_delete = []
    for file_name, breakpoints in self._line_breakpoints.items():
      for index, bp in enumerate( breakpoints ):
        if bp[ 'options' ].get( 'temporary' ):
          to_delete.append( ( bp, file_name, index ) )

    for entry in to_delete:
      self._DeleteLineBreakpoint( *entry )


  def _UpdateTemporaryBreakpoints( self, breakpoints, temp_idxs ):
    for temp_idx, user_bp in temp_idxs:
      if temp_idx >= len( breakpoints ):
        # Just can't trust servers ?
        self._logger.debug( "Server Error - invalid breakpoints list did not "
                            "contain entry for temporary breakpoint at index "
                            f"{ temp_idx } i.e. { user_bp }" )
        continue

      bp = breakpoints[ temp_idx ]

      if 'line' not in bp or not bp[ 'verified' ]:
        utils.UserMessage(
          "Unable to set temporary breakpoint at line "
          f"{ user_bp[ 'line' ] } execution will continue...",
          persist = True,
          error = True )

      self._logger.debug( f"Updating temporary breakpoint { user_bp } line "
                          f"{ user_bp[ 'line' ] } to { bp[ 'line' ] }" )

      # if it was moved, update the user-breakpoint so that we unset it
      # again properly
      user_bp[ 'line' ] = bp[ 'line' ]
      # some adapters dont return id
      user_bp[ 'id' ] = bp.get( 'id' )


  def AddFunctionBreakpoint( self, function, options ):
    self._func_breakpoints.append( {
      'state': 'ENABLED',
      'function': function,
      'options': options,
      # Specified in options:
      # 'condition': ...,
      # 'hitCondition': ...,
    } )

    # TODO: We don't really have aanything to update here, but if we're going to
    # have a UI list of them we should update that at this point
    self.UpdateUI()


  def UpdateUI( self, then = None ):
    def callback():
      self._render_subject.emit()
      if then:
        then()

    if self._connection:
      self.SendBreakpoints( callback )
    else:
      callback()

  def SetConfiguredBreakpoints( self, configured_breakpoints ):
    self._configured_breakpoints = configured_breakpoints


  def SendBreakpoints( self, doneHandler = None ):
    awaiting = 0

    def response_received( *failure_args ):
      nonlocal awaiting
      awaiting = awaiting - 1

      if failure_args and self._connection:
        reason, msg = failure_args
        utils.UserMessage( 'Unable to set breakpoint: {0}'.format( reason ),
                           persist = True,
                           error = True )

      if awaiting == 0 and doneHandler:
        doneHandler()

    def response_handler( source, msg, temp_idxs = [] ):
      if msg:
        breakpoints = ( msg.get( 'body' ) or {} ).get( 'breakpoints' ) or []
        self._UpdateTemporaryBreakpoints( breakpoints, temp_idxs )
      response_received()


    # NOTE: Must do this _first_ otherwise we might send requests and get
    # replies before we finished sending all the requests.
    if self._exception_breakpoints is None:
      self._SetUpExceptionBreakpoints( self._configured_breakpoints )


    # TODO: add the _configured_breakpoints to line_breakpoints

    for file_name, line_breakpoints in self._line_breakpoints.items():
      temp_idxs = []
      breakpoints = []
      for bp in line_breakpoints:
        self._SignToLine( file_name, bp )
        if 'sign_id' in bp:
          signs.UnplaceSign( bp[ 'sign_id' ], 'VimspectorBP' )

        if bp[ 'state' ] != 'ENABLED':
          continue

        dap_bp = {}
        dap_bp.update( bp[ 'options' ] )
        dap_bp.update( { 'line': bp[ 'line' ] } )

        dap_bp.pop( 'temporary', None )

        temp_idxs.append( [ len( breakpoints ), bp ] )

        breakpoints.append( dap_bp )


      source = {
        'name': os.path.basename( file_name ),
        'path': file_name,
      }

      awaiting = awaiting + 1
      self._connection.DoRequest(
        # The source=source here is critical to ensure that we capture each
        # source in the iteration, rather than ending up passing the same source
        # to each callback.
        lambda msg, source=source, temp_idxs=temp_idxs: response_handler(
          source,
          msg,
          temp_idxs = temp_idxs ),
        {
          'command': 'setBreakpoints',
          'arguments': {
            'source': source,
            'breakpoints': breakpoints,
          },
          'sourceModified': False, # TODO: We can actually check this
        },
        failure_handler = response_received
      )

    # TODO: Add the _configured_breakpoints to function breakpoints

    if self._server_capabilities.get( 'supportsFunctionBreakpoints' ):
      awaiting = awaiting + 1
      breakpoints = []
      for bp in self._func_breakpoints:
        if bp[ 'state' ] != 'ENABLED':
          continue
        dap_bp = {}
        dap_bp.update( bp[ 'options' ] )
        dap_bp.update( { 'name': bp[ 'function' ] } )
        breakpoints.append( dap_bp )

      self._connection.DoRequest(
        lambda msg: response_handler( None, msg ),
        {
          'command': 'setFunctionBreakpoints',
          'arguments': {
            'breakpoints': breakpoints,
          }
        },
        failure_handler = response_received
      )

    if self._exception_breakpoints:
      awaiting = awaiting + 1
      self._connection.DoRequest(
        lambda msg: response_handler( None, None ),
        {
          'command': 'setExceptionBreakpoints',
          'arguments': self._exception_breakpoints
        },
        failure_handler = response_received
      )

    if awaiting == 0 and doneHandler:
      doneHandler()


  def _SetUpExceptionBreakpoints( self, configured_breakpoints ):
    exception_breakpoint_filters = self._server_capabilities.get(
        'exceptionBreakpointFilters',
        [] )

    if exception_breakpoint_filters or not self._server_capabilities.get(
      'supportsConfigurationDoneRequest' ):
      # Note the supportsConfigurationDoneRequest part: prior to there being a
      # configuration done request, the "exception breakpoints" request was the
      # indication that configuraiton was done (and its response is used to
      # trigger requesting threads etc.). See the note in
      # debug_session.py:_Initialise for more detials
      exception_filters = []
      configured_filter_options = configured_breakpoints.get( 'exception', {} )
      if exception_breakpoint_filters:
        for f in exception_breakpoint_filters:
          default_value = 'Y' if f.get( 'default' ) else 'N'

          if f[ 'filter' ] in configured_filter_options:
            result = configured_filter_options[ f[ 'filter' ] ]

            if isinstance( result, bool ):
              result = 'Y' if result else 'N'

            if not isinstance( result, str ) or result not in ( 'Y', 'N', '' ):
              raise ValueError(
                f"Invalid value for exception breakpoint filter '{f}': "
                f"'{result}'. Must be boolean, 'Y', 'N' or '' (default)" )
          else:
            result = utils.AskForInput(
              "{}: Break on {} (Y/N/default: {})? ".format( f[ 'filter' ],
                                                            f[ 'label' ],
                                                            default_value ),
              default_value )

          if result == 'Y':
            exception_filters.append( f[ 'filter' ] )
          elif not result and f.get( 'default' ):
            exception_filters.append( f[ 'filter' ] )

      self._exception_breakpoints = {
        'filters': exception_filters
      }

      if self._server_capabilities.get( 'supportsExceptionOptions' ):
        # TODO: There are more elaborate exception breakpoint options here, but
        # we don't support them. It doesn't seem like any of the servers really
        # pay any attention to them anyway.
        self._exception_breakpoints[ 'exceptionOptions' ] = []


  def Refresh( self ):
    # TODO: Just this file ?
    self._breakpoints_view.RefreshBreakpoints( self.BreakpointsAsQuickFix() )
    self._ShowBreakpoints()

  def Save( self ):
    # Need to copy line breakpoints, because we have to remove the 'sign_id'
    # and 'id' properties. Otherwise we might end up loading junk
    line = {}
    for file_name, breakpoints in self._line_breakpoints.items():
      bps = [ dict( bp ) for bp in breakpoints ]
      for bp in bps:
        bp.pop( 'sign_id', None )
        bp.pop( 'id', None )
      line[ file_name ] = bps

    return {
      'line': line,
      'function': self._func_breakpoints,
      'exception': self._exception_breakpoints
    }


  def Load( self, save_data ):
    self.ClearBreakpoints()
    self._line_breakpoints = save_data.get( 'line', {} )
    self._func_breakpoints = save_data.get( 'function' , [] )
    self._exception_breakpoints = save_data.get( 'exception', None )

    self.UpdateUI()


  def _ShowBreakpoints( self ):
    for file_name, line_breakpoints in self._line_breakpoints.items():
      for bp in line_breakpoints:
        self._SignToLine( file_name, bp )
        if 'sign_id' in bp:
          signs.UnplaceSign( bp[ 'sign_id' ], 'VimspectorBP' )
        else:
          bp[ 'sign_id' ] = self._next_sign_id
          self._next_sign_id += 1

        sign = ( 'vimspectorBPDisabled' if bp[ 'state' ] != 'ENABLED'
                 else 'vimspectorBPLog'
                   if 'logMessage' in bp[ 'options' ]
                 else 'vimspectorBPCond'
                   if 'condition' in bp[ 'options' ]
                   or 'hitCondition' in bp[ 'options' ]
                 else 'vimspectorBP' )

        if utils.BufferExists( file_name ):
          signs.PlaceSign( bp[ 'sign_id' ],
                           'VimspectorBP',
                           sign,
                           file_name,
                           bp[ 'line' ] )

  def _SignToLine( self, file_name, bp ):
    if 'sign_id' not in bp:
      return bp[ 'line' ]

    if not utils.BufferExists( file_name ):
      return bp[ 'line' ]

    signs = vim.eval( "sign_getplaced( '{}', {} )".format(
      utils.Escape( file_name ),
      json.dumps( { 'id': bp[ 'sign_id' ], 'group': 'VimspectorBP', } ) ) )

    if len( signs ) == 1 and len( signs[ 0 ][ 'signs' ] ) == 1:
      bp[ 'line' ] = int( signs[ 0 ][ 'signs' ][ 0 ][ 'lnum' ] )

    return bp[ 'line' ]


def _NormaliseFileName( file_name ):
  absoluate_path = os.path.abspath( file_name )
  return absoluate_path if os.path.isfile( absoluate_path ) else file_name
