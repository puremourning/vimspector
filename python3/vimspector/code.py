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
import json
import os
from collections import defaultdict

from vimspector import utils, terminal, signs


class CodeView( object ):
  def __init__( self, window, api_prefix ):
    self._window = window
    self._api_prefix = api_prefix

    self._terminal = None
    self.current_syntax = None

    self._logger = logging.getLogger( __name__ )
    utils.SetUpLogging( self._logger )

    # FIXME: This ID is by group, so should be module scope
    self._next_sign_id = 1
    self._breakpoints = defaultdict( list )
    self._signs = {
      'vimspectorPC': None,
      'breakpoints': []
    }
    self._current_frame = None
    self._scratch_buffers = []

    with utils.LetCurrentWindow( self._window ):
      if utils.UseWinBar():
        # Buggy neovim doesn't render correctly when the WinBar is defined:
        # https://github.com/neovim/neovim/issues/12689
        vim.command( 'nnoremenu WinBar.■\\ Stop '
                     ':call vimspector#Stop()<CR>' )
        vim.command( 'nnoremenu WinBar.▶\\ Cont '
                     ':call vimspector#Continue()<CR>' )
        vim.command( 'nnoremenu WinBar.▷\\ Pause '
                     ':call vimspector#Pause()<CR>' )
        vim.command( 'nnoremenu WinBar.↷\\ Next '
                     ':call vimspector#StepOver()<CR>' )
        vim.command( 'nnoremenu WinBar.→\\ Step '
                     ':call vimspector#StepInto()<CR>' )
        vim.command( 'nnoremenu WinBar.←\\ Out '
                     ':call vimspector#StepOut()<CR>' )
        vim.command( 'nnoremenu WinBar.⟲: '
                     ':call vimspector#Restart()<CR>' )
        vim.command( 'nnoremenu WinBar.✕ '
                     ':call vimspector#Reset()<CR>' )

      if not signs.SignDefined( 'vimspectorPC' ):
        signs.DefineSign( 'vimspectorPC',
                          text = '▶',
                          double_text = '▶',
                          texthl = 'MatchParen',
                          linehl = 'CursorLine' )
      if not signs.SignDefined( 'vimspectorPCBP' ):
        signs.DefineSign( 'vimspectorPCBP',
                          text = '●▶',
                          double_text  = '▷',
                          texthl = 'MatchParen',
                          linehl = 'CursorLine' )


  def _UndisplayPC( self, clear_pc = True ):
    if clear_pc:
      self._current_frame = None
    if self._signs[ 'vimspectorPC' ]:
      signs.UnplaceSign( self._signs[ 'vimspectorPC' ], 'VimspectorCode' )
      self._signs[ 'vimspectorPC' ] = None


  def _DisplayPC( self ):
    frame = self._current_frame
    if not frame:
      return

    self._UndisplayPC( clear_pc = False )

    # FIXME: Do we relly need to keep using up IDs ?
    self._signs[ 'vimspectorPC' ] = self._next_sign_id
    self._next_sign_id += 1

    sign = 'vimspectorPC'
    # If there's also a breakpoint on this line, use vimspectorPCBP
    for bp in self._breakpoints.get( frame[ 'source' ][ 'path' ], [] ):
      if 'line' not in bp:
        continue

      if bp[ 'line' ] == frame[ 'line' ]:
        sign = 'vimspectorPCBP'
        break

    if utils.BufferExists( frame[ 'source' ][ 'path' ] ):
      signs.PlaceSign( self._signs[ 'vimspectorPC' ],
                       'VimspectorCode',
                       sign,
                       frame[ 'source' ][ 'path' ],
                       frame[ 'line' ] )


  def SetCurrentFrame( self, frame ):
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

    utils.JumpToWindow( self._window )
    try:
      utils.OpenFileInCurrentWindow( frame[ 'source' ][ 'path' ] )
      vim.command( 'doautocmd <nomodeline> User VimspectorJumpedToFrame' )
    except vim.error:
      self._logger.exception( 'Unexpected vim error opening file {}'.format(
        frame[ 'source' ][ 'path' ] ) )
      return False

    # SIC: column is 0-based, line is 1-based in vim. Why? Nobody knows.
    # Note: max() with 0 because some debug adapters (go) return 0 for the
    # column.
    try:
      self._window.cursor = ( frame[ 'line' ], max( frame[ 'column' ] - 1, 0 ) )
    except vim.error:
      self._logger.exception( "Unable to jump to %s:%s in %s, maybe the file "
                              "doesn't exist",
                              frame[ 'line' ],
                              frame[ 'column' ],
                              frame[ 'source' ][ 'path' ] )
      return False

    self.current_syntax = utils.ToUnicode(
      vim.current.buffer.options[ 'syntax' ] )

    self.ShowBreakpoints()

    return True

  def Clear( self ):
    if self._signs[ 'vimspectorPC' ]:
      signs.UnplaceSign( self._signs[ 'vimspectorPC' ], 'VimspectorCode' )
      self._signs[ 'vimspectorPC' ] = None

    self._UndisplayPC()
    self._UndisplaySigns()
    self.current_syntax = None

  def Reset( self ):
    self.ClearBreakpoints()
    self.Clear()

    for b in self._scratch_buffers:
      utils.CleanUpHiddenBuffer( b )
    self._scratch_buffers = []

  def AddBreakpoints( self, source, breakpoints ):
    for breakpoint in breakpoints:
      source = breakpoint.get( 'source' ) or source
      if not source or 'path' not in source:
        self._logger.warn( 'missing source/path in breakpoint {0}'.format(
          json.dumps( breakpoint ) ) )
        continue

      breakpoint[ 'source' ] = source
      self._breakpoints[ source[ 'path' ] ].append( breakpoint )

    self._logger.debug( 'Breakpoints at this point: {0}'.format(
      json.dumps( self._breakpoints, indent = 2 ) ) )

    self.ShowBreakpoints()


  def AddBreakpoint( self, breakpoint ):
    self.AddBreakpoints( None, [ breakpoint ] )


  def UpdateBreakpoint( self, bp ):
    if 'id' not in bp:
      self.AddBreakpoint( bp )
      return

    for _, breakpoint_list in self._breakpoints.items():
      for index, breakpoint in enumerate( breakpoint_list ):
        if 'id' in breakpoint and breakpoint[ 'id' ] == bp[ 'id' ]:
          breakpoint_list[ index ] = bp
          self.ShowBreakpoints()
          return

    # Not found. Assume new
    self.AddBreakpoint( bp )


  def RemoveBreakpoint( self, bp ):
    for _, breakpoint_list in self._breakpoints.items():
      found_index = None
      for index, breakpoint in enumerate( breakpoint_list ):
        if 'id' in breakpoint and breakpoint[ 'id' ] == bp[ 'id' ]:
          found_index = index
          break

      if found_index is not None:
        del breakpoint_list[ found_index ]
        self.ShowBreakpoints()
        return


  def Refresh( self ):
    # TODO: jsut the file ?
    self.ShowBreakpoints()


  def _UndisplaySigns( self ):
    for sign_id in self._signs[ 'breakpoints' ]:
      signs.UnplaceSign( sign_id, 'VimspectorCode' )

    self._signs[ 'breakpoints' ] = []

  def ClearBreakpoints( self ):
    self._UndisplaySigns()
    self._breakpoints = defaultdict( list )

  def ShowBreakpoints( self ):
    self._UndisplaySigns()

    for file_name, breakpoints in self._breakpoints.items():
      for breakpoint in breakpoints:
        if 'line' not in breakpoint:
          continue

        sign_id = self._next_sign_id
        self._next_sign_id += 1
        self._signs[ 'breakpoints' ].append( sign_id )
        if utils.BufferExists( file_name ):
          signs.PlaceSign( sign_id,
                           'VimspectorCode',
                           'vimspectorBP' if breakpoint[ 'verified' ]
                                          else 'vimspectorBPDisabled',
                           file_name,
                           breakpoint[ 'line' ] )

    # We need to also check if there's a breakpoint on this PC line and chnge
    # the PC
    self._DisplayPC()

  def BreakpointsAsQuickFix( self ):
    qf = []
    for file_name, breakpoints in self._breakpoints.items():
      for breakpoint in breakpoints:
        qf.append( {
            'filename': file_name,
            'lnum': breakpoint.get( 'line', 1 ),
            'col': 1,
            'type': 'L',
            'valid': 1 if breakpoint.get( 'verified' ) else 0,
            'text': "Line breakpoint - {}".format(
              'VERIFIED' if breakpoint.get( 'verified' ) else 'INVALID' )
        } )
    return qf


  def LaunchTerminal( self, params ):
    self._terminal = terminal.LaunchTerminal( self._api_prefix,
                                              params,
                                              window_for_start = self._window,
                                              existing_term = self._terminal )

    # FIXME: Change this tor return the PID rather than having debug_session
    # work that out
    return self._terminal.buffer_number


  def ShowMemory( self, memoryReference, length, msg ):
    if not self._window.valid:
      return False

    buf_name = os.path.join( '_vimspector_mem', memoryReference )
    buf = utils.BufferForFile( buf_name )
    self._scratch_buffers.append( buf )
    utils.SetUpHiddenBuffer( buf, buf_name )
    with utils.ModifiableScratchBuffer( buf ):
      # TODO: The data is encoded in base64, so we need to convert that to the
      # equivalent output of say xxd
      data = msg.get( 'body', {} ).get( 'data', '' )
      utils.SetBufferContents( buf, utils.Base64ToHexDump( data ) )
      buf[ 0:0 ] = [
        f'Memory Dump for Reference {memoryReference} Length: {length} bytes',
        '-' * 80,
        'Offset    Bytes                                             Text',
      ]

    utils.SetSyntax( '', 'xxd', buf )

    utils.JumpToWindow( self._window )
    utils.OpenFileInCurrentWindow( buf_name )
