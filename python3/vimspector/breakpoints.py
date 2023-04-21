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
import operator
import typing

import json
from vimspector import utils, signs, settings, disassembly, session_manager
from vimspector.debug_adapter_connection import DebugAdapterConnection


def _JumpToBreakpoint( qfbp ):
  if not qfbp[ 'lnum' ]:
    return

  success = int( vim.eval(
      f'win_gotoid( bufwinid( \'{ qfbp[ "filename" ] }\' ) )' ) )

  try:
    if not success:
      with utils.TemporaryVimOptions( { 'equalalways': False } ):
        # Split from whatever the previous window was. This is roughly
        # consistent with the quickfix window, assuming that everyone in the
        # world sets 'switchbuf=uselast', which they don't and isn't the
        # default.
        vim.command( 'silent! wincmd p' )
        vim.command( "leftabove split {}".format( qfbp[ 'filename' ] ) )

    utils.SetCursorPosInWindow( vim.current.window, qfbp[ 'lnum' ], 1 )
  except vim.error as e:
    # 'filename' or 'lnum' might be missing,
    # so don't trigger an exception here by referring to them
    utils.UserMessage( f"Unable to jump to file: { str( e ) }",
                       persist = True,
                       error = True )


class BreakpointsView( object ):
  def __init__( self, session_id ):
    self._win = None
    self._buffer = None
    self._buffer_name = utils.BufferNameForSession( 'vimspector.Breakpoints',
                                                    session_id )
    self._breakpoint_list = []

  def _HasWindow( self ):
    return self._win is not None and self._win.valid

  def _HasBuffer( self ):
    return self._buffer is not None and self._buffer.valid

  def _UpdateView( self, breakpoint_list, show=True ):
    if show and not self._HasWindow():
      if self._HasBuffer():
        with utils.NoAutocommands():
          vim.command( f'botright { settings.Int( "bottombar_height" ) }split' )
        vim.current.buffer = self._buffer
      else:
        with utils.NoAutocommands():
          vim.command( f'botright { settings.Int( "bottombar_height" ) }new' )
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
        utils.SetUpHiddenBuffer( self._buffer, self._buffer_name )

      self._win = vim.current.window

      utils.UpdateSessionWindows( {
        'breakpoints': utils.WindowID( self._win )
      } )

      utils.SetSyntax( '', 'vimspector-breakpoints', self._buffer )

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


# FIXME: This really should be project scope and not associated with a debug
# session. Breakpoints set by the user should be independent and breakpoints for
# the current active session should be associated with the session when they are
# in use.
#
# Otherwise, if we had multiple concurrent _root_ sessions (tabs), how would we
# konw how to associate them when the user presses F9?
#
# For _child_ sessions, we essentially broadcast breakpoints to all connections.
# Perhaps we should do that too, but just hoist this out of the debug session
# when supporting multiple root sessions.
class ProjectBreakpoints( object ):
  _connections: typing.Set[ DebugAdapterConnection ]

  def __init__( self,
                session_id,
                render_event_emitter,
                IsPCPresentAt,
                disassembly_manager: disassembly.DisassemblyView ):
    self._connections = set()
    self._logger = logging.getLogger( __name__ + '.' + str( session_id ) )
    utils.SetUpLogging( self._logger, session_id )

    self._render_subject = render_event_emitter.subscribe( self.Refresh )
    self._IsPCPresentAt = IsPCPresentAt
    self._disassembly_manager = disassembly_manager
    utils.SetUpLogging( self._logger )


    # These are the user-entered breakpoints.
    self._line_breakpoints = defaultdict( list )
    self._func_breakpoints = []
    self._exception_breakpoints = None
    self._configured_breakpoints = {}

    self._server_capabilities = {}

    self._next_sign_id = 1000 * session_id + 1
    self._awaiting_bp_responses = 0
    self._pending_send_breakpoints = []


    self._breakpoints_view = BreakpointsView( session_id )

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


  def AddConnection( self, connection: DebugAdapterConnection ):
    self._connections.add( connection )

  def RemoveConnection( self, connection: DebugAdapterConnection ):
    try:
      self._connections.remove( connection )
    except KeyError:
      pass

  def SetServerCapabilities( self, server_capabilities ):
    self._server_capabilities = server_capabilities

  def SetDisassemblyManager( self, disassembly_manager ):
    self._disassembly_manager = disassembly_manager

  def ConnectionClosed( self, connection: DebugAdapterConnection ):
    self.RemoveConnection( connection )
    self._ClearServerBreakpointData( connection )

    if not self._connections:
      # TODO: This is completely wrong (we should store these per-connection)
      self._server_capabilities = {}
      self._awaiting_bp_responses = 0
      self._pending_send_breakpoints = []

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
      # This should find the breakpoint by the "current" line in lnum. If not,
      # pass an empty options just in case we end up in "ADD" codepath.
      self._ToggleBreakpoint( {},
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

    _JumpToBreakpoint( bp )

  def JumpToNextBreakpoint( self, reverse=False ):
    bps = self._breakpoints_view._breakpoint_list
    if not bps:
      return

    line = vim.current.window.cursor[ 0 ]
    comparator = operator.lt if reverse else operator.gt
    sorted_bps = sorted( bps,
                         key=operator.itemgetter( 'lnum' ),
                         reverse=reverse )
    bp = next( ( bp
                 for bp in sorted_bps
                 if comparator( bp[ 'lnum' ], line ) ),
                None )

    if bp:
      _JumpToBreakpoint( bp )

  def JumpToPreviousBreakpoint( self ):
    self.JumpToNextBreakpoint( reverse=True )

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
          state = 'PENDING'
          valid = 0
          for conn, server_bp in bp[ 'server_bp' ].items():
            if server_bp[ 'verified' ]:
              line = server_bp.get( 'line', line )
              state = 'VERIFIED'
              valid = 1
              break
        else:
          state = bp[ 'state' ]
          valid = 1

        if not line:
          valid = 0
          line_value = ''
        else:
          line_value = utils.BufferLineValue( file_name, line )

        desc = "Line"
        sfx = ''
        if bp[ 'is_instruction_breakpoint' ]:
          desc = "Instruction"
          sfx = f" at { utils.Hex( bp.get( 'address', '<unknown>' ) ) }"

        qf.append( {
          'filename': file_name,
          'lnum': line,
          'col': 1,
          'type': 'L',
          'valid': valid,
          'text': ( f"{desc} breakpoint{sfx} - "
                    f"{state}: {json.dumps( bp['options'] )}"
                    f"\t{ line_value }" )
        } )
    for bp in self._func_breakpoints:
      qf.append( {
        'filename': bp[ 'function' ],
        'lnum': 1,
        'col': 1,
        'type': 'F',
        'valid': 0,
        # NOTE: While we store a 'state' for function breakpoints, it isn't
        # actually used - when toggling, we juse clear the breakpoint.
        # This is lame (FIXME). In general, FIXME - function breakpoints are
        # very limnited and kind of broken.
        'text': "{}: Function breakpoint - {}".format(
          bp[ 'function' ],
          json.dumps( bp[ 'options' ] ) )
      } )

    return qf


  def ClearBreakpoints( self ):
    # These are the user-entered breakpoints.
    self._HideBreakpoints()

    self._line_breakpoints = defaultdict( list )
    self._func_breakpoints = []
    self._exception_breakpoints = None

    self.UpdateUI()


  def _FindLineBreakpoint( self, file_name, line ):
    for bp, index in self._AllBreakpointsOnLine( file_name, line ):
      return bp, index

    return None, None


  def _AllBreakpointsOnLine( self, file_name, line ):
    file_name = utils.NormalizePath( file_name )
    for index, bp in enumerate( self._line_breakpoints[ file_name ] ):
      self._SignToLine( file_name, bp )
      # If we're connected, then operate on the server-bp position, not the
      # user-bp position, as that's what the user sees in the UI (signs, and in
      # the breakpoints window)
      if 'server_bp' in bp:
        for conn, server_bp in bp[ 'server_bp' ].items():
          if server_bp.get( 'line', bp[ 'line' ] ) == line:
            yield bp, index
      elif bp[ 'line' ] == line:
        yield bp, index


  def _FindPostedBreakpoint( self,
                             conn: DebugAdapterConnection,
                             breakpoint_id ):
    if breakpoint_id is None:
      return None

    for filepath, breakpoint_list in self._line_breakpoints.items():
      for index, bp in enumerate( breakpoint_list ):
        server_bp = bp.get( 'server_bp', {} ).get( conn.GetSessionId(), {} )
        if 'id' in server_bp and server_bp[ 'id' ] == breakpoint_id:
          return bp

    return None


  def _ClearServerBreakpointData( self, conn: DebugAdapterConnection ):
    for _, breakpoints in self._line_breakpoints.items():
      for bp in breakpoints:
        if 'server_bp' in bp and conn.GetSessionId() in bp[ 'server_bp' ]:
          # Unplace the sign. If the sign was moved by the server, then we don't
          # want a subsequent call to _SignToLine to override the user's
          # breakpoint location with the server one. This is not what users
          # typically expect, and we may (soon) call something that eagerly
          # calls _SignToLine, such as _ShowBreakpoints,
          if 'sign_id' in bp:
            signs.UnplaceSign( bp[ 'sign_id' ], 'VimspectorBP' )
            del bp[ 'sign_id' ]

          del bp[ 'server_bp' ][ conn.GetSessionId() ]
          if not bp[ 'server_bp' ]:
            del bp[ 'server_bp' ]


      # Clear all instruction breakpoints because they aren't truly portable
      # across sessions.
      #
      # TODO: It might be possible to re-resolve the address stored in the
      # breakpoint, though this would only work in a limited way (as load
      # addresses will frequently not be the same across runs)


      def ShouldKeep( bp ):
        if not bp[ 'is_instruction_breakpoint' ]:
          return True
        if 'address' in bp and bp[ 'session_id' ] != conn.GetSessionId():
          return True
        return False

      breakpoints[ : ] = [ bp for bp in breakpoints if ShouldKeep( bp ) ]


  def _CopyServerLineBreakpointProperties( self,
                                           bp,
                                           conn: DebugAdapterConnection,
                                           server_bp ):
    if bp[ 'is_instruction_breakpoint' ]:
      # For some reason, MIEngine returns random 'line' values for instruction
      # brakpoints
      server_bp.pop( 'line', None )
    bp.setdefault( 'server_bp', {} )[ conn.GetSessionId() ] = server_bp


  def UpdatePostedBreakpoint( self,
                              conn: DebugAdapterConnection,
                              server_bp ):
    bp = self._FindPostedBreakpoint( conn, server_bp.get( 'id' ) )
    if bp is None:
      self._logger.warn( "Unexpected update to breakpoint with id %s:"
                         "breakpiont not found. %s",
                         server_bp.get( 'id' ),
                         server_bp )
      # FIXME ? self.AddPostedBreakpoint( server_bp )
      return

    self._CopyServerLineBreakpointProperties( bp, conn, server_bp )
    # Render the breakpoitns, but don't send any updates, as this leads to a
    # feedback loop
    self._render_subject.emit()

  def AddPostedBreakpoint( self, conn, server_bp ):
    source = server_bp.get( 'source' )
    if not source or 'path' not in source:
      self._logger.warn( 'missing source/path in server breakpoint {0}'.format(
        json.dumps( server_bp ) ) )
      return

    if 'line' not in server_bp:
      # There's nothing we can really add without a line
      # If we get an unsolicited instruction breakpoints it's extremely unlikely
      # that we'd be able to actually use it
      return

    existing_bp, _ = self._FindLineBreakpoint( source[ 'path' ],
                                               server_bp[ 'line' ] )

    if existing_bp is None:
      self._logger.debug( "Adding new breakpoint from server %s", server_bp )
      self._PutLineBreakpoint( source[ 'path' ],
                               server_bp[ 'line' ],
                               {},
                               connection = conn,
                               server_bp = server_bp )
    else:
      # This probably should not happen, but update the existing breakpoint that
      # happens to be on this line
      self._CopyServerLineBreakpointProperties( existing_bp, conn, server_bp )

    # Render the breakpoitns, but don't send any updates, as this leads to a
    # feedback loop
    self._render_subject.emit()


  def DeletePostedBreakpoint( self, conn: DebugAdapterConnection, server_bp ):
    bp = self._FindPostedBreakpoint( conn, server_bp.get( 'id' ) )

    if bp is None:
      return

    del bp[ 'server_bp' ][ conn.GetSessionId() ]
    if not bp[ 'server_bp' ]:
      del bp[ 'server_bp' ]

    # Render the breakpoitns, but don't send any updates, as this leads to a
    # feedback loop
    self._render_subject.emit()


  def IsBreakpointPresentAt( self, file_path, line ):
    return self._FindLineBreakpoint( file_path, line )[ 0 ] is not None

  def _PutLineBreakpoint( self,
                          file_name,
                          line,
                          options,
                          connection: DebugAdapterConnection = None,
                          server_bp = None ):
    is_instruction_breakpoint = ( self._disassembly_manager and
                                  self._disassembly_manager.IsDisassemblyBuffer(
                                    file_name ) )

    path = utils.NormalizePath( file_name )
    bp = {
      'state': 'ENABLED',
      'line': line,
      'options': options,
      # FIXME: This is crap. We should have a proper model for instruction
      # breakpoints where we store the address rather than the "line number".
      # We already have all of the plumbing to do that (give or take), but it
      # requirs some refactoring and not deleting all the instruction
      # breakpoints on server close
      'is_instruction_breakpoint': is_instruction_breakpoint,
      # 'sign_id': <filled in when placed>,
      #
      # Used by other breakpoint types (specified in options):
      # 'condition': ...,
      # 'hitCondition': ...,
      # 'logMessage': ...
    }

    if is_instruction_breakpoint:
      conn: DebugAdapterConnection
      conn, address = self._disassembly_manager.ResolveAddressAtLine( line )
      bp[ 'address' ] = address
      bp[ 'session_id' ] = conn.GetSessionId()

    if server_bp is not None:
      self._CopyServerLineBreakpointProperties( bp, conn, server_bp )

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
    can_disable = not should_delete or settings.Bool(
      'toggle_disables_breakpoint' )

    bp, index = self._FindLineBreakpoint( file_name, line )
    if bp is None:
      # ADD
      self._PutLineBreakpoint( file_name, line, options )
    elif bp[ 'state' ] == 'ENABLED' and can_disable:
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
    else:
      self._PutLineBreakpoint( file_name, line_num, options )
    self.UpdateUI( then )


  def ClearLineBreakpoint( self, file_name, line_num ):
    bp, index = self._FindLineBreakpoint( file_name, line_num )
    if bp is None:
      return
    self._DeleteLineBreakpoint( bp, file_name, index )
    self.UpdateUI()


  def AddTemporaryLineBreakpoint( self,
                                  file_name,
                                  line_num,
                                  options = None,
                                  then = None ):
    the_options = {
      'temporary': True
    }
    if options:
      the_options.update( options )
    self._PutLineBreakpoint( file_name, line_num, the_options )
    self.UpdateUI( then )


  def ClearTemporaryBreakpoint( self, file_name, line_num ):
    # FIXME: We should use the _FindPostedBreakpoint here instead, as that's way
    # more accurate at this point. Some servers can now identifyt he breakpoint
    # ID that actually triggered too. For now, we still have
    # _UpdateServerBreakpoints change the _user_ breakpiont line and we check
    # for that _here_, though we could check ['server_bp']['line']
    updates = False
    for bp, index in self._AllBreakpointsOnLine( file_name, line_num ):
      if bp[ 'options' ].get( 'temporary' ):
        updates = True
        self._DeleteLineBreakpoint( bp, file_name, index )

    if updates:
      self.UpdateUI()

  def ClearTemporaryBreakpoints( self ):
    to_delete = []
    for file_name, breakpoints in self._line_breakpoints.items():
      for index, bp in enumerate( breakpoints ):
        if bp[ 'options' ].get( 'temporary' ):
          to_delete.append( ( bp, file_name, index ) )

    for entry in to_delete:
      self._DeleteLineBreakpoint( *entry )


  def _UpdateServerBreakpoints( self, conn, breakpoints, bp_idxs ):
    for bp_idx, user_bp in bp_idxs:
      if bp_idx >= len( breakpoints ):
        # Just can't trust servers ?
        self._logger.debug( "Server Error - invalid breakpoints list did not "
                            "contain entry for temporary breakpoint at index "
                            f"{ bp_idx } i.e. { user_bp }" )
        continue

      server_bp = breakpoints[ bp_idx ]
      self._CopyServerLineBreakpointProperties( user_bp, conn, server_bp )

      # TODO: Change temporary to be a ref to the actual connection that it's
      # temporary in (i.e. the "current" session when RunToCursor is done) and
      # only set it there. Setting it in all sessions probably won't work.
      is_temporary = bool( user_bp[ 'options' ].get( 'temporary' ) )

      if not is_temporary:
        # We don't modify the 'user" breakpiont
        continue

      # FIXME: Tempoarary instruction breakpoints would not have a line; we
      # would have to rely on the id returning in the hit (which we should
      # probably be doing anyway)
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


  def ClearUI( self ):
    self._HideBreakpoints()
    self._breakpoints_view.CloseBreakpoints()


  def UpdateUI( self, then = None ):
    def callback():
      self._render_subject.emit()
      if then:
        then()

    if self._connections:
      self.SendBreakpoints( callback )
    else:
      callback()

  def SetConfiguredBreakpoints( self, configured_breakpoints ):
    self._configured_breakpoints = configured_breakpoints


  def SendBreakpoints( self, doneHandler = None ):
    if self._awaiting_bp_responses > 0:
      self._pending_send_breakpoints.append( ( doneHandler, ) )
      return

    self._awaiting_bp_responses = 0

    def response_received( *failure_args ):
      self._awaiting_bp_responses -= 1

      if failure_args and len( self._connections ):
        reason, msg = failure_args
        utils.UserMessage( 'Unable to set breakpoint: {0}'.format( reason ),
                           persist = True,
                           error = True )

      if self._awaiting_bp_responses > 0:
        return

      if doneHandler:
        doneHandler()

      if bool( self._pending_send_breakpoints ):
        args = self._pending_send_breakpoints.pop( 0 )
        self.SendBreakpoints( *args )


    def response_handler( conn, msg, bp_idxs = [] ):
      server_bps = ( msg.get( 'body' ) or {} ).get( 'breakpoints' ) or []
      self._UpdateServerBreakpoints( conn, server_bps, bp_idxs )
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
        if bp[ 'is_instruction_breakpoint' ]:
          continue

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

      for connection in self._connections:
        self._awaiting_bp_responses += 1
        connection.DoRequest(
          # The source=source here is critical to ensure that we capture each
          # source in the iteration, rather than ending up passing the same
          # source to each callback.
          lambda msg, conn=connection, bp_idxs=bp_idxs: response_handler(
            conn,
            msg,
            bp_idxs ),
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
      for connection in self._connections:
        self._awaiting_bp_responses += 1
        connection.DoRequest(
          lambda msg, conn=connection: response_handler( conn, msg ),
          {
            'command': 'setFunctionBreakpoints',
            'arguments': {
              'breakpoints': breakpoints,
            }
          },
          failure_handler = response_received
        )

    if self._disassembly_manager:
      for connection in self._connections:
        breakpoints = []
        bp_idxs = []
        for file_name, line_breakpoints in self._line_breakpoints.items():
          for bp in line_breakpoints:
            if not bp[ 'is_instruction_breakpoint' ]:
              continue

            if ( 'address' in bp and
                 bp[ 'session_id' ] != connection.GetSessionId() ):
              continue

            self._SignToLine( file_name, bp )
            bp.pop( 'server_bp', None )

            if 'sign_id' in bp:
              signs.UnplaceSign( bp[ 'sign_id' ], 'VimspectorBP' )

            if bp[ 'state' ] != 'ENABLED':
              continue

            if not bp[ 'line' ]:
              continue

            dap_bp = {}
            dap_bp.update( bp[ 'options' ] )
            dap_bp.update( {
              'instructionReference':
                self._disassembly_manager.GetMemoryReference(),
              'offset':
                self._disassembly_manager.GetOffsetForLine( bp[ 'line' ] ),
            } )

            dap_bp.pop( 'temporary', None )
            bp_idxs.append( [ len( breakpoints ), bp ] )

            breakpoints.append( dap_bp )

        self._awaiting_bp_responses += 1
        connection.DoRequest(
          lambda msg, conn=connection, bp_idxs=bp_idxs: response_handler(
            conn,
            msg,
            bp_idxs ),
          {
            'command': 'setInstructionBreakpoints',
            'arguments': {
              'breakpoints': breakpoints,
            },
          },
          failure_handler = response_received
        )

    if self._exception_breakpoints:
      for connection in self._connections:
        self._awaiting_bp_responses += 1
        connection.DoRequest(
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
      # indication that configuration was done (and its response is used to
      # trigger requesting threads etc.). See the note in
      # debug_session.py:_Initialise for more details
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
      bps = []
      for bp in breakpoints:
        if bp[ 'is_instruction_breakpoint' ]:
          # Don't save instruction breakpoints because the memory references
          # aren't persistent, and neither are load addresses (probably) that
          # they resolve to
          continue

        bp = dict( bp )

        # Save the actual position not the currently stored one, in case user
        # inserted more lines. This is more what the user expects, as it's where
        # the sign is on their screen.
        self._SignToLine( file_name, bp )
        # Don't save dynamic info like sign_id and the server's breakpoint info
        bp.pop( 'sign_id', None )
        bp.pop( 'server_bp', None )
        bps.append( bp )

      if bps:
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
          verified = False
          for conn, server_bp in bp[ 'server_bp' ].items():
            if server_bp[ 'verified' ]:
              line = server_bp.get( 'line', line )
              verified = True
              break
        else:
          verified = len( self._connections ) == 0

        if not line:
          continue

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

  def _HideBreakpoints( self ):
    for file_name, breakpoints in self._line_breakpoints.items():
      for bp in breakpoints:
        self._SignToLine( file_name, bp )
        if 'sign_id' in bp:
          signs.UnplaceSign( bp[ 'sign_id' ], 'VimspectorBP' )
          del bp[ 'sign_id' ]


  def _SignToLine( self, file_name, bp ):
    if bp[ 'is_instruction_breakpoint' ]:
      if self._disassembly_manager and 'address' in bp:
        bp[ 'line' ] = self._disassembly_manager.FindLineForAddress(
          session_manager.Get().GetSession( bp[ 'session_id' ] ).Connection(),
          bp[ 'address' ] )
      return

    if len( self._connections ) > 0:
      return

    if 'sign_id' not in bp:
      return

    if not utils.BufferExists( file_name ):
      return

    signs = vim.eval( "sign_getplaced( '{}', {} )".format(
      utils.Escape( file_name ),
      json.dumps( { 'id': bp[ 'sign_id' ], 'group': 'VimspectorBP', } ) ) )

    if len( signs ) == 1 and len( signs[ 0 ][ 'signs' ] ) == 1:
      bp[ 'line' ] = int( signs[ 0 ][ 'signs' ][ 0 ][ 'lnum' ] )

    return
