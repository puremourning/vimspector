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
import logging

import json
from vimspector import utils, signs, settings


class BreakpointsView( object ):
  def __init__( self ):
    self._win = None
    self._buffer = None
    self._breakpoint_list = []

  def _HasWindow( self ):
    return self._win is not None and self._win.valid

  def _HasBuffer( self ):
    return self._buffer is not None and self._buffer.valid

  def _UpdateView( self, breakpoint_list, show=True ):
    if show and not self._HasWindow():
      vim.command( f'botright { settings.Int( "bottombar_height" ) }new' )
      self._win = vim.current.window
      if self._HasBuffer():
        vim.current.buffer = self._buffer
      else:
        self._buffer = vim.current.buffer
        mappings = settings.Dict( 'mappings' )[ 'breakpoints' ]
        groups = {
          'toggle': 'ToggleBreakpointViewBreakpoint',
          'toggle_all': 'ToggleAllBreakpointsViewBreakpoint',
          'delete': 'DeleteBreakpointViewBreakpoint',
          'jump_to': 'JumpToBreakpointViewBreakpoint',
          'add_line': 'SetAdvancedLineBreakpoint',
          'add_func': 'AddAdvancedFunctionBreakpoint'
        }
        for key, func in groups.items():
          for mapping in utils.GetVimList( mappings, key ):
            vim.command( f'nnoremap <silent> <buffer> { mapping } '
                         ':<C-u>call '
                         f'vimspector#{ func }()<CR>' )
        utils.SetUpHiddenBuffer( self._buffer,
                                 "vimspector.Breakpoints" )

      # neovim madness need to re-assign the dict to trigger rpc call
      # see https://github.com/neovim/pynvim/issues/261
      session_wins = vim.vars[ 'vimspector_session_windows' ]
      session_wins[ 'breakpoints' ] = utils.WindowID( self._win )
      vim.vars[ 'vimspector_session_windows' ] = session_wins

      # set highlighting
      vim.eval( "matchadd( 'WarningMsg', 'ENABLED', 100 )" )
      vim.eval( "matchadd( 'WarningMsg', 'VERIFIED', 100 )" )
      vim.eval( "matchadd( 'LineNr', 'DISABLED', 100 )" )
      vim.eval( "matchadd( 'LineNr', 'PENDING', 100 )" )
      vim.eval( "matchadd( 'Title', '\\v^\\S+:{0,}', 100 )" )

      if utils.UseWinBar():
        vim.command( 'nnoremenu <silent> 1.1 WinBar.Delete '
                     ':call vimspector#DeleteBreakpointViewBreakpoint()<CR>' )
        vim.command( 'nnoremenu <silent> 1.2 WinBar.Toggle '
                     ':call vimspector#ToggleBreakpointViewBreakpoint()<CR>' )
        vim.command( 'nnoremenu <silent> 1.2 WinBar.*Toggle '
                     ':call'
                       ' vimspector#ToggleAllBreakpointsViewBreakpoint()<CR>' )
        vim.command( 'nnoremenu <silent> 1.3 WinBar.Jump\\ To '
                     ':call vimspector#JumpToBreakpointViewBreakpoint()<CR>' )
        # TODO: Add tests for this function
        vim.command( 'nnoremenu <silent> 1.4 WinBar.+Line '
                     ':call vimspector#SetAdvancedLineBreakpoint()<CR>' )
        vim.command( 'nnoremenu <silent> 1.4 WinBar.+Function '
                     ':call vimspector#AddAdvancedFunctionBreakpoint()<CR>' )
        vim.command( 'nnoremenu <silent> 1.4 WinBar.Clear '
                     ':call vimspector#ClearBreakpoints()<CR>' )
        vim.command( 'nnoremenu <silent> 1.4 WinBar.Save '
                     ':call vimspector#WriteSessionFile()<CR>' )
        vim.command( 'nnoremenu <silent> 1.4 WinBar.Load '
                     ':call vimspector#ReadSessionFile()<CR>' )

      # we want to maintain the height of the window
      self._win.options[ "winfixheight" ] = True

    self._breakpoint_list = breakpoint_list

    def FormatEntry( el ):
      prefix = ''
      if el.get( 'type' ) == 'L':
        prefix = '{}:{} '.format( os.path.basename( el.get( 'filename' ) ),
                                  el.get( 'lnum' ) )

      return '{}{}'.format( prefix, el.get( 'text' ) )

    if self._HasBuffer():
      with utils.ModifiableScratchBuffer( self._buffer ):
        with utils.RestoreCursorPosition():
          utils.SetBufferContents( self._buffer,
                                   list( map( FormatEntry, breakpoint_list ) ) )

  def CloseBreakpoints( self ):
    if not self._HasWindow():
      return

    with utils.LetCurrentTabpage( self._win.tabpage ):
      vim.command( "{}close".format( self._win.number ) )
      self._win = None

  def GetBreakpointForLine( self ):
    if not self._HasBuffer():
      return

    if vim.current.buffer.number != self._buffer.number:
      return None

    if not self._breakpoint_list:
      return None

    line_num = vim.current.window.cursor[ 0 ]
    index = max( 0, min( len( self._breakpoint_list ) - 1, line_num - 1 ) )
    return self._breakpoint_list[ index ]

  def ToggleBreakpointView( self, breakpoint_list ):
    if self._HasWindow():
      old_tabpage_number = self._win.tabpage.number
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
    self._UpdateView( breakpoint_list, show=False )


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
    self._awaiting_bp_responses = 0
    self._pending_send_breakpoints = None


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
    self._awaiting_bp_responses = 0
    self._pending_send_breakpoints = None

    self._ClearServerBreakpointData()
    self.UpdateUI()


    # NOTE: we don't reset self._exception_breakpoints because we don't want to
    # re-ask the user every time for the sane info.

    # FIXME: If the adapter type changes, we should probably forget this ?


  def ToggleBreakpointsView( self ):
    self._breakpoints_view.ToggleBreakpointView( self.BreakpointsAsQuickFix() )

  def ToggleBreakpointViewBreakpoint( self ):
    bp = self._breakpoints_view.GetBreakpointForLine()
    if not bp:
      return

    if bp.get( 'type' ) == 'F':
      self.ClearFunctionBreakpoint( bp.get( 'filename' ) )
    else:
      self._ToggleBreakpoint( None,
                              bp.get( 'filename' ),
                              bp.get( 'lnum' ),
                              should_delete = False )

  def ToggleAllBreakpointsViewBreakpoint( self ):
    # Try and guess the best action - if more breakpoitns are currently enabled
    # than disabled, then disable all. Otherwise, enable all.
    enabled = 0
    disabled = 0
    for filename, bps in self._line_breakpoints.items():
      for bp in bps:
        if bp[ 'state' ] == 'ENABLED':
          enabled += 1
        else:
          disabled += 1

    if enabled > disabled:
      new_state = 'DISABLED'
    else:
      new_state = 'ENABLED'

    for filename, bps in self._line_breakpoints.items():
      for bp in bps:
        bp[ 'state' ] = new_state

    # FIXME: We don't really handle 'DISABLED' state for function breakpoints,
    # so they are not touched
    self.UpdateUI()

  def JumpToBreakpointViewBreakpoint( self ):
    bp = self._breakpoints_view.GetBreakpointForLine()
    if not bp:
      return

    if bp.get( 'type' ) != 'L':
      return

    success = int( vim.eval(
        f'win_gotoid( bufwinid( \'{ bp[ "filename" ] }\' ) )' ) )

    try:
      if not success:
        vim.command( "leftabove split {}".format( bp[ 'filename' ] ) )

      utils.SetCursorPosInWindow( vim.current.window, bp[ 'lnum' ], 1 )
    except vim.error:
      # 'filename' or 'lnum' might be missing,
      # so don't trigger an exception here by refering to them
      utils.UserMessage( "Unable to jump to file",
                         persist = True,
                         error = True )


  def ClearBreakpointViewBreakpoint( self ):
    bp = self._breakpoints_view.GetBreakpointForLine()
    if not bp:
      return

    if bp.get( 'type' ) == 'F':
      self.ClearFunctionBreakpoint( bp.get( 'filename' ) )
    else:
      self.ClearLineBreakpoint( bp.get( 'filename' ), bp.get( 'lnum' ) )

  def BreakpointsAsQuickFix( self ):
    qf = []
    for file_name, breakpoints in self._line_breakpoints.items():
      for bp in breakpoints:
        self._SignToLine( file_name, bp )

        line = bp[ 'line' ]
        if 'server_bp' in bp:
          server_bp = bp[ 'server_bp' ]
          line = server_bp.get( 'line', line )
          if server_bp[ 'verified' ]:
            state = 'VERIFIED'
            valid = 1
          else:
            state = 'PENDING'
            valid = 0
        else:
          state = bp[ 'state' ]
          valid = 1

        qf.append( {
          'filename': file_name,
          'lnum': line,
          'col': 1,
          'type': 'L',
          'valid': valid,
          'text': "Line breakpoint - {}: {}".format(
            state,
            json.dumps( bp[ 'options' ] ) )
        } )
    for bp in self._func_breakpoints:
      qf.append( {
        'filename': bp[ 'function' ],
        'lnum': 1,
        'col': 1,
        'type': 'F',
        'valid': 0,
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
    file_name = utils.NormalizePath( file_name )
    for index, bp in enumerate( self._line_breakpoints[ file_name ] ):
      self._SignToLine( file_name, bp )
      if bp[ 'line' ] == line:
        return bp, index

    return None, None

  def _FindPostedBreakpoint( self, breakpoint_id ):
    if breakpoint_id is None:
      return None

    for filepath, breakpoint_list in self._line_breakpoints.items():
      for index, bp in enumerate( breakpoint_list ):
        server_bp = bp.get( 'server_bp', {} )
        if 'id' in server_bp and server_bp[ 'id' ] == breakpoint_id:
          return bp

    return None


  def _ClearServerBreakpointData( self ):
    for _, breakpoints in self._line_breakpoints.items():
      for bp in breakpoints:
        if 'server_bp' in bp:
          # Unplace the sign. If the sign was moved by the server, then we don't
          # want a subsequent call to _SignToLine to override the user's
          # breakpoint location with the server one. This is not what users
          # typicaly expect, and we may (soon) call something that eagerly calls
          # _SignToLine, such as _ShowBreakpoints,
          if 'sign_id' in bp:
            signs.UnplaceSign( bp[ 'sign_id' ], 'VimspectorBP' )
            del bp[ 'sign_id' ]

          del bp[ 'server_bp' ]


  def _CopyServerLineBreakpointProperties( self, bp, server_bp ):
    # we are just updating position of the existing breakpoint
    bp[ 'server_bp' ] = server_bp

  def UpdatePostedBreakpoint( self, server_bp ):
    bp = self._FindPostedBreakpoint( server_bp.get( 'id' ) )
    if bp is None:
      self._logger.warn( "Unexpected update to breakpoint with id %s:"
                         "breakpiont not found. %s",
                         server_bp.get( 'id' ),
                         server_bp )
      return

    self._CopyServerLineBreakpointProperties( bp, server_bp )
    # Render the breakpoitns, but don't send any updates, as this leads to a
    # feedback loop
    self._render_subject.emit()


  def AddPostedBreakpoint( self, server_bp ):
    source = server_bp.get( 'source' )
    if not source or 'path' not in source:
      self._logger.warn( 'missing source/path in server breakpoint {0}'.format(
        json.dumps( server_bp ) ) )
      return

    if 'line' not in server_bp:
      # There's nothing we can really add without a line
      return

    existing_bp, _ = self._FindLineBreakpoint( source[ 'path' ],
                                               server_bp[ 'line' ] )

    if existing_bp is None:
      self._logger.debug( "Adding new breakpoint from server %s", server_bp )
      self._PutLineBreakpoint( source[ 'path' ],
                               server_bp[ 'line' ],
                               {},
                               server_bp )
    else:
      # This probably should not happen, but update the existing breakpoint that
      # happens to be on this line
      self._CopyServerLineBreakpointProperties( existing_bp, server_bp )

    # Render the breakpoitns, but don't send any updates, as this leads to a
    # feedback loop
    self._render_subject.emit()


  def DeletePostedBreakpoint( self, server_bp ):
    bp = self._FindPostedBreakpoint( server_bp.get( 'id' ) )

    if bp is None:
      return

    del bp[ 'server_bp' ]
    # Render the breakpoitns, but don't send any updates, as this leads to a
    # feedback loop
    self._render_subject.emit()


  def IsBreakpointPresentAt( self, file_path, line ):
    return self._FindLineBreakpoint( file_path, line )[ 0 ] is not None

  def _PutLineBreakpoint( self, file_name, line, options, server_bp = None ):
    path = utils.NormalizePath( file_name )
    bp = {
      'state': 'ENABLED',
      'line': line,
      'options': options,
      # 'sign_id': <filled in when placed>,
      #
      # Used by other breakpoint types (specified in options):
      # 'condition': ...,
      # 'hitCondition': ...,
      # 'logMessage': ...
    }

    if server_bp is not None:
      self._CopyServerLineBreakpointProperties( bp, server_bp )

    self._line_breakpoints[ path ].append( bp )


  def _DeleteLineBreakpoint( self, bp, file_name, index ):
    if 'sign_id' in bp:
      signs.UnplaceSign( bp[ 'sign_id' ], 'VimspectorBP' )
    del self._line_breakpoints[ utils.NormalizePath( file_name ) ][ index ]

  def _ToggleBreakpoint( self, options, file_name, line, should_delete = True ):
    if not file_name:
      return

    # We only disable when *toggling* in the breakpoints window
    # (should_delete=False), or for legacy reasons, when a switch is set
    can_disble = not should_delete or settings.Bool(
      'toggle_disables_breakpoint' )

    bp, index = self._FindLineBreakpoint( file_name, line )
    if bp is None:
      # ADD
      self._PutLineBreakpoint( file_name, line, options )
    elif bp[ 'state' ] == 'ENABLED' and can_disble:
      # DISABLE
      bp[ 'state' ] = 'DISABLED'
    elif not should_delete:
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
    # FIXME: We should use the _FindPostedBreakpoint here instead, as that's way
    # more accurate at this point. Some servers can now identifyt he breakpoint
    # ID that actually triggered too. For now, we still have
    # _UpdateServerBreakpoints change the _user_ breakpiont line and we check
    # for that _here_, though we could check ['server_bp']['line']
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


  def _UpdateServerBreakpoints( self, breakpoints, bp_idxs ):
    for bp_idx, user_bp in bp_idxs:
      if bp_idx >= len( breakpoints ):
        # Just can't trust servers ?
        self._logger.debug( "Server Error - invalid breakpoints list did not "
                            "contain entry for temporary breakpoint at index "
                            f"{ bp_idx } i.e. { user_bp }" )
        continue

      server_bp = breakpoints[ bp_idx ]
      self._CopyServerLineBreakpointProperties( user_bp, server_bp )
      is_temporary = bool( user_bp[ 'options' ].get( 'temporary' ) )

      if not is_temporary:
        # We don't modify the 'user" breakpiont
        continue

      if 'line' not in server_bp or not server_bp[ 'verified' ]:
        utils.UserMessage(
          "Unable to set temporary breakpoint at line "
          f"{ user_bp[ 'line' ] } execution will continue...",
          persist = True,
          error = True )
        continue

      self._logger.debug( f"Updating temporary breakpoint { user_bp } line "
                          f"{ user_bp[ 'line' ] } to { server_bp[ 'line' ] }" )

      # if it was moved, update the user-breakpoint so that we unset it
      # again properly
      user_bp[ 'line' ] = server_bp[ 'line' ]


  def AddFunctionBreakpoint( self, function, options ):
    self._func_breakpoints.append( {
      'state': 'ENABLED',
      'function': function,
      'options': options,
      # Specified in options:
      # 'condition': ...,
      # 'hitCondition': ...,
    } )

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
    if self._awaiting_bp_responses > 0:
      self._pending_send_breakpoints = ( doneHandler, )
      return

    self._awaiting_bp_responses = 0

    def response_received( *failure_args ):
      self._awaiting_bp_responses -= 1

      if failure_args and self._connection:
        reason, msg = failure_args
        utils.UserMessage( 'Unable to set breakpoint: {0}'.format( reason ),
                           persist = True,
                           error = True )

      if self._awaiting_bp_responses > 0:
        return

      if doneHandler:
        doneHandler()

      if bool( self._pending_send_breakpoints ):
        args = self._pending_send_breakpoints
        self._pending_send_breakpoints = None
        self.SendBreakpoints( *args )


    def response_handler( msg, bp_idxs = [] ):
      server_bps = ( msg.get( 'body' ) or {} ).get( 'breakpoints' ) or []
      self._UpdateServerBreakpoints( server_bps, bp_idxs )
      response_received()


    # NOTE: Must do this _first_ otherwise we might send requests and get
    # replies before we finished sending all the requests.
    if self._exception_breakpoints is None:
      self._SetUpExceptionBreakpoints( self._configured_breakpoints )


    # TODO: add the _configured_breakpoints to line_breakpoints

    for file_name, line_breakpoints in self._line_breakpoints.items():
      bp_idxs = []
      breakpoints = []
      for bp in line_breakpoints:
        bp.pop( 'server_bp', None )

        self._SignToLine( file_name, bp )
        if 'sign_id' in bp:
          signs.UnplaceSign( bp[ 'sign_id' ], 'VimspectorBP' )

        if bp[ 'state' ] != 'ENABLED':
          continue

        dap_bp = {}
        dap_bp.update( bp[ 'options' ] )
        dap_bp.update( { 'line': bp[ 'line' ] } )

        dap_bp.pop( 'temporary', None )

        bp_idxs.append( [ len( breakpoints ), bp ] )

        breakpoints.append( dap_bp )


      source = {
        'name': os.path.basename( file_name ),
        'path': file_name,
      }

      self._awaiting_bp_responses += 1
      self._connection.DoRequest(
        # The source=source here is critical to ensure that we capture each
        # source in the iteration, rather than ending up passing the same source
        # to each callback.
        lambda msg, bp_idxs=bp_idxs: response_handler( msg, bp_idxs ),
        {
          'command': 'setBreakpoints',
          'arguments': {
            'source': source,
            'breakpoints': breakpoints,
            'sourceModified': False, # TODO: We can actually check this
          },
        },
        failure_handler = response_received
      )

    # TODO: Add the _configured_breakpoints to function breakpoints

    if self._server_capabilities.get( 'supportsFunctionBreakpoints' ):
      self._awaiting_bp_responses += 1
      breakpoints = []
      for bp in self._func_breakpoints:
        bp.pop( 'server_bp', None )
        if bp[ 'state' ] != 'ENABLED':
          continue
        dap_bp = {}
        dap_bp.update( bp[ 'options' ] )
        dap_bp.update( { 'name': bp[ 'function' ] } )
        breakpoints.append( dap_bp )

      # FIXME(Ben): The function breakpoints response actually returns
      # 'Breakpoint' objects. The point is that there is a server_bp for each
      # function breakpoint as well as every line breakpoint. We need to
      # implement that:
      #  - pass the indices in here
      #  - make _FindPostedBreakpoint also search function breakpionts
      #  - make sure that ConnectionClosed also cleares the server_bp data for
      #    function breakpionts
      #  - make sure that we have tests for this, because i'm sure we don't!
      self._connection.DoRequest(
        lambda msg: response_handler( msg ),
        {
          'command': 'setFunctionBreakpoints',
          'arguments': {
            'breakpoints': breakpoints,
          }
        },
        failure_handler = response_received
      )

    if self._exception_breakpoints:
      self._awaiting_bp_responses += 1
      self._connection.DoRequest(
        lambda msg: response_received(),
        {
          'command': 'setExceptionBreakpoints',
          'arguments': self._exception_breakpoints
        },
        failure_handler = response_received
      )

    if self._awaiting_bp_responses == 0 and doneHandler:
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
    self._breakpoints_view.RefreshBreakpoints( self.BreakpointsAsQuickFix() )
    self._ShowBreakpoints()

  def Save( self ):
    # Need to copy line breakpoints, because we have to remove the 'sign_id'
    # and 'server_bp' properties. Otherwise we might end up loading junk
    line = {}
    for file_name, breakpoints in self._line_breakpoints.items():
      bps = [ dict( bp ) for bp in breakpoints ]
      for bp in bps:
        # Save the actual position not the currently stored one, in case user
        # inserted more lines. This is more what the user expects, as it's where
        # the sign is on their screen.
        self._SignToLine( file_name, bp )
        # Don't save dynamic info like sign_id and the server's breakpoint info
        bp.pop( 'sign_id', None )
        bp.pop( 'server_bp', None )
      line[ file_name ] = bps

    return {
      'line': line,
      'function': self._func_breakpoints,
      'exception': self._exception_breakpoints
    }


  def Load( self, save_data ):
    self.ClearBreakpoints()
    self._line_breakpoints = defaultdict( list, save_data.get( 'line', {} ) )
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

        line = bp[ 'line' ]
        if 'server_bp' in bp:
          server_bp = bp[ 'server_bp' ]
          line = server_bp.get( 'line', line )
          verified = server_bp[ 'verified' ]
        else:
          verified = self._connection is None

        sign = ( 'vimspectorBPDisabled'
                   if bp[ 'state' ] != 'ENABLED' or not verified
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
                           line )

  def _SignToLine( self, file_name, bp ):
    if self._connection is not None:
      return

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
