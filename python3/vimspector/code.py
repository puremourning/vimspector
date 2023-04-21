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

import vim
import logging
import os

from vimspector import utils, terminal, signs

# NEXT_SIGN_ID = 1


class CodeView( object ):
  def __init__( self,
                session_id,
                window,
                api_prefix,
                render_event_emitter,
                IsBreakpointPresentAt ):

    self._window = window
    self._api_prefix = api_prefix
    self._render_subject = render_event_emitter.subscribe( self._DisplayPC )
    self._IsBreakpointPresentAt = IsBreakpointPresentAt

    self._terminal = None
    self.current_syntax = None

    self._logger = logging.getLogger( __name__ + '.' + str( session_id ) )
    utils.SetUpLogging( self._logger )

    self._next_sign_id = 1000 * session_id + 1
    self._signs = {
      'vimspectorPC': None,
    }
    self._current_frame = None
    self._scratch_buffers = []

    self._RenderWinBar()
    signs.DefineProgramCounterSigns()


  def _RenderWinBar( self ):
    with utils.LetCurrentWindow( self._window ):
      if utils.UseWinBar():
        utils.SetWinBar(
          ( '■ Stop', 'vimspector#Stop()', ),
          ( '▶ Cont', 'vimspector#Continue()', ),
          ( '▷ Pause', 'vimspector#Pause()', ),
          ( '↷ Next', 'vimspector#StepSOver()', ),
          ( '→ Step', 'vimspector#StepSInto()', ),
          ( '← Out', 'vimspector#StepSOut()', ),
          ( '↺', 'vimspector#Restart()', ),
          ( '✕', 'vimspector#Reset()', )
        )

  def _UndisplayPC( self, clear_pc = True ):
    if clear_pc:
      self._current_frame = None
    if self._signs[ 'vimspectorPC' ]:
      signs.UnplaceSign( self._signs[ 'vimspectorPC' ], 'VimspectorCode' )
      self._signs[ 'vimspectorPC' ] = None

  def IsPCPresentAt( self, file_path, line ):
    frame = self._current_frame

    if not frame:
      return False

    abs_path = utils.NormalizePath( file_path )
    return ( frame[ 'source' ][ 'path' ] == abs_path
      and frame[ 'line' ] == line )


  def _DisplayPC( self ):
    frame = self._current_frame
    if not frame:
      return

    self._UndisplayPC( clear_pc = False )

    # FIXME: Do we really need to keep using up IDs ?
    self._signs[ 'vimspectorPC' ] = self._next_sign_id
    self._next_sign_id += 1
    # FIXME: Do we relly need to keep using up IDs ?
    # FIXME: Why did I add this global sign id?
    # global NEXT_SIGN_ID
    # self._signs[ 'vimspectorPC' ] = NEXT_SIGN_ID
    # NEXT_SIGN_ID += 1

    # If there's also a breakpoint on this line, use vimspectorPCBP
    sign =  'vimspectorPCBP' if self._IsBreakpointPresentAt(
      frame[ 'source' ][ 'path' ], frame[ 'line' ] ) else 'vimspectorPC'

    if utils.BufferExists( frame[ 'source' ][ 'path' ] ):
      signs.PlaceSign( self._signs[ 'vimspectorPC' ],
                       'VimspectorCode',
                       sign,
                       frame[ 'source' ][ 'path' ],
                       frame[ 'line' ] )


  def SetCurrentFrame( self, frame, should_jump_to_location ):
    """Returns True if the code window was updated with the frame, False
    otherwise. False means either the frame is junk, we couldn't find the file
    (or don't have the data) or the code window no longer exits."""

    if not frame or not frame.get( 'source' ):
      self._UndisplayPC()
      return False

    if 'path' not in frame[ 'source' ]:
      self._UndisplayPC()
      return False

    self._current_frame = frame

    if not self._window.valid:
      return False

    with utils.LetCurrentWindow( self._window ):
      try:
        if utils.OpenFileInCurrentWindow( frame[ 'source' ][ 'path' ] ):
          if utils.VimIsNeovim():
            # Sigh: https://github.com/neovim/neovim/issues/23165
            self._RenderWinBar()
        vim.command( 'doautocmd <nomodeline> User VimspectorJumpedToFrame' )
      except vim.error:
        self._logger.exception( 'Unexpected vim error opening file {}'.format(
          frame[ 'source' ][ 'path' ] ) )
        return False

    if should_jump_to_location:
      utils.JumpToWindow( self._window )

    # SIC: column is 0-based, line is 1-based in vim. Why? Nobody knows.
    # Note: max() with 0 because some debug adapters (go) return 0 for the
    # column.
    try:
      utils.SetCursorPosInWindow( self._window,
                                  frame[ 'line' ],
                                  frame[ 'column' ] )
    except vim.error:
      self._logger.exception( "Unable to jump to %s:%s in %s, maybe the file "
                              "doesn't exist",
                              frame[ 'line' ],
                              frame[ 'column' ],
                              frame[ 'source' ][ 'path' ] )
      return False

    # Open any fold at the cursor position
    vim.command( 'normal! zv' )

    self.current_syntax = utils.ToUnicode(
      vim.current.buffer.options[ 'syntax' ] )

    self._DisplayPC()
    return True

  def Clear( self ):
    if self._signs[ 'vimspectorPC' ]:
      signs.UnplaceSign( self._signs[ 'vimspectorPC' ], 'VimspectorCode' )
      self._signs[ 'vimspectorPC' ] = None

    self._UndisplayPC()
    self.current_syntax = None

  def Reset( self ):
    self.Clear()
    self._render_subject.unsubscribe()

    for b in self._scratch_buffers:
      utils.CleanUpHiddenBuffer( b )
    self._scratch_buffers = []

  def Refresh( self ):
    # TODO: just the file ?
    self._DisplayPC()

  def LaunchTerminal( self, params ):
    self._terminal = terminal.LaunchTerminal( self._api_prefix,
                                              params,
                                              window_for_start = self._window,
                                              existing_term = self._terminal )

    # FIXME: Change this tor return the PID rather than having debug_session
    # work that out
    return self._terminal.buffer_number


  def ShowMemory( self, session_id, memoryReference, length, offset, msg ):
    if not self._window.valid:
      return False

    buf_name = os.path.join( '_vimspector_mem',
                             str( session_id ),
                             memoryReference )
    buf = utils.BufferForFile( buf_name )
    self._scratch_buffers.append( buf )
    utils.SetUpHiddenBuffer( buf, buf_name )
    body = msg.get( 'body', {} )
    addr = utils.ParseAddress( body.get( 'address', 0 ) )
    data = body.get( 'data', '' )
    with utils.ModifiableScratchBuffer( buf ):
      utils.SetBufferContents( buf, [
        f'Memory at address { utils.Hex( addr ) }',
        '-' * 86,
          'Address             '
          'Bytes                                             '
          'Text',
        '-' * 86,
      ] )
      utils.AppendToBuffer( buf, utils.Base64ToHexDump( data, addr ) )

    utils.SetSyntax( '', 'vimspector-memory', buf )
    utils.JumpToWindow( self._window )
    utils.OpenFileInCurrentWindow( buf_name )
