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
from collections import defaultdict

from vimspector import utils, settings, signs


class CodeView( object ):
  def __init__( self, window, api_prefix ):
    self._window = window
    self._api_prefix = api_prefix

    self._terminal_window = None
    self._terminal_buffer_number = None
    self.current_syntax = None

    self._logger = logging.getLogger( __name__ )
    utils.SetUpLogging( self._logger )

    self._next_sign_id = 1
    self._breakpoints = defaultdict( list )
    self._signs = {
      'vimspectorPC': None,
      'breakpoints': []
    }
    self._current_frame = None

    with utils.LetCurrentWindow( self._window ):
      vim.command( 'nnoremenu WinBar.■\\ Stop :call vimspector#Stop()<CR>' )
      vim.command( 'nnoremenu WinBar.▶\\ Cont :call vimspector#Continue()<CR>' )
      vim.command( 'nnoremenu WinBar.▷\\ Pause :call vimspector#Pause()<CR>' )
      vim.command( 'nnoremenu WinBar.↷\\ Next :call vimspector#StepOver()<CR>' )
      vim.command( 'nnoremenu WinBar.→\\ Step :call vimspector#StepInto()<CR>' )
      vim.command( 'nnoremenu WinBar.←\\ Out :call vimspector#StepOut()<CR>' )
      vim.command( 'nnoremenu WinBar.⟲: :call vimspector#Restart()<CR>' )
      vim.command( 'nnoremenu WinBar.✕ :call vimspector#Reset()<CR>' )

      if not signs.SignDefined( 'vimspectorPC' ):
        signs.DefineSign( 'vimspectorPC',
                          text = '▶',
                          texthl = 'MatchParen',
                          linehl = 'CursorLine' )
      if not signs.SignDefined( 'vimspectorPCBP' ):
        signs.DefineSign( 'vimspectorPCBP',
                          text = '●▶',
                          texthl = 'MatchParen',
                          linehl = 'CursorLine' )


  def _UndisplayPC( self ):
    if self._signs[ 'vimspectorPC' ]:
      signs.UnplaceSign( self._signs[ 'vimspectorPC' ], 'VimspectorCode' )
      self._signs[ 'vimspectorPC' ] = None


  def _DisplayPC( self ):
    frame = self._current_frame
    if not frame:
      return

    self._UndisplayPC()

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

    try:
      signs.PlaceSign( self._signs[ 'vimspectorPC' ],
                       'VimspectorCode',
                       sign,
                       frame[ 'source' ][ 'path' ],
                       frame[ 'line' ] )
    except vim.error as e:
      # Ignore 'invalid buffer name'
      if 'E158' not in str( e ):
        raise


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
    self._DisplayPC()

    if not self._window.valid:
      return False

    utils.JumpToWindow( self._window )
    try:
      utils.OpenFileInCurrentWindow( frame[ 'source' ][ 'path' ] )
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

    return True

  def Clear( self ):
    if self._signs[ 'vimspectorPC' ]:
      signs.UnplaceSign( self._signs[ 'vimspectorPC' ], 'VimspectorCode' )
      self._signs[ 'vimspectorPC' ] = None

    self._current_frame = None
    self._UndisplaySigns()
    self.current_syntax = None

  def Reset( self ):
    self.ClearBreakpoints()
    self.Clear()

  def AddBreakpoints( self, source, breakpoints ):
    for breakpoint in breakpoints:
      if 'source' not in breakpoint:
        if source:
          breakpoint[ 'source' ] = source
        else:
          self._logger.warn( 'missing source in breakpoint {0}'.format(
            json.dumps( breakpoint ) ) )
          continue

      self._breakpoints[ breakpoint[ 'source' ][ 'path' ] ].append(
        breakpoint )

    self._logger.debug( 'Breakpoints at this point: {0}'.format(
      json.dumps( self._breakpoints, indent = 2 ) ) )

    self.ShowBreakpoints()

  def UpdateBreakpoint( self, bp ):
    if 'id' not in bp:
      self.AddBreakpoints( None, [ bp ] )

    for _, breakpoint_list in self._breakpoints.items():
      for index, breakpoint in enumerate( breakpoint_list ):
        if 'id' in breakpoint and breakpoint[ 'id' ] == bp[ 'id' ]:
          breakpoint_list[ index ] = bp
          self.ShowBreakpoints()
          return

    # Not found. Assume new
    self.AddBreakpoints( None, [ bp ] )

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
    # kind = params.get( 'kind', 'integrated' )

    # FIXME: We don't support external terminals, and only open in the
    # integrated one.

    cwd = params[ 'cwd' ]
    args = params[ 'args' ]
    env = params.get( 'env', {} )

    term_options = {
      'vertical': 1,
      'norestore': 1,
      'cwd': cwd,
      'env': env,
    }

    if self._window.valid:
      window_for_start = self._window
    else:
      # TOOD: Where? Maybe we should just use botright vertical ...
      window_for_start = vim.current.window

    if self._terminal_window is not None and self._terminal_window.valid:
      assert self._terminal_buffer_number
      window_for_start = self._terminal_window
      if ( self._terminal_window.buffer.number == self._terminal_buffer_number
           and int( utils.Call( 'vimspector#internal#{}term#IsFinished'.format(
                                  self._api_prefix ),
                                self._terminal_buffer_number ) ) ):
        term_options[ 'curwin' ] = 1
      else:
        term_options[ 'vertical' ] = 0

    buffer_number = None
    terminal_window = None
    with utils.LetCurrentWindow( window_for_start ):
      # If we're making a vertical split from the code window, make it no more
      # than 80 columns and no fewer than 10. Also try and keep the code window
      # at least 82 columns
      if term_options[ 'vertical' ] and not term_options.get( 'curwin', 0 ):
        term_options[ 'term_cols' ] = max(
          min ( int( vim.eval( 'winwidth( 0 )' ) )
                     - settings.Int( 'code_minwidth' ),
                settings.Int( 'terminal_maxwidth' ) ),
          settings.Int( 'terminal_minwidth' )
        )

      buffer_number = int(
        utils.Call(
          'vimspector#internal#{}term#Start'.format( self._api_prefix ),
          args,
          term_options ) )
      terminal_window = vim.current.window

    if buffer_number is None or buffer_number <= 0:
      # TODO: Do something better like reject the request?
      raise ValueError( "Unable to start terminal" )

    self._terminal_window = terminal_window
    self._terminal_buffer_number = buffer_number

    vim.vars[ 'vimspector_session_windows' ][ 'terminal' ] = utils.WindowID(
      self._terminal_window,
      vim.current.tabpage )
    with utils.RestoreCursorPosition():
      with utils.RestoreCurrentWindow():
        with utils.RestoreCurrentBuffer( vim.current.window ):
          vim.command( 'doautocmd User VimspectorTerminalOpened' )

    return buffer_number
