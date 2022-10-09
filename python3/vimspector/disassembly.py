# vimspector - A multi-language debugging system for Vim
# Copyright 2022 Ben Jackson
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

import os
import logging

import vim

from vimspector import signs, utils

SIGN_ID = 1


class DisassemblyView( object ):
  def __init__( self, window, connection, api_prefix ):
    self._logger = logging.getLogger( __name__ )
    utils.SetUpLogging( self._logger )

    self._window = window

    self._api_prefix = api_prefix
    self._connection = connection

    self.current_frame = None
    self.current_instructions = None

    self._scratch_buffers = []
    self._signs = {
      'vimspectorPC': None,
    }

    with utils.LetCurrentWindow( self._window ):
      if utils.UseWinBar():
        vim.command( 'nnoremenu WinBar.■\\ Stop '
                     ':call vimspector#Stop()<CR>' )
        vim.command( 'nnoremenu WinBar.▶\\ Cont '
                     ':call vimspector#Continue()<CR>' )
        vim.command( 'nnoremenu WinBar.▷\\ Pause '
                     ':call vimspector#Pause()<CR>' )
        vim.command( 'nnoremenu WinBar.↷\\ NextI '
                     ':call vimspector#StepIOver()<CR>' )
        vim.command( 'nnoremenu WinBar.→\\ StepI '
                     ':call vimspector#StepIInto()<CR>' )
        vim.command( 'nnoremenu WinBar.←\\ OutI '
                     ':call vimspector#StepIOut()<CR>' )
        vim.command( 'nnoremenu WinBar.⟲: '
                     ':call vimspector#Restart()<CR>' )
        vim.command( 'nnoremenu WinBar.✕ '
                     ':call vimspector#Reset()<CR>' )

    signs.DefineProgramCounterSigns()


  def ConnectionUp( self, connection ):
    self._connection = connection


  def WindowIsValid( self ):
    return self._window is not None and self._window.valid

  def SetCurrentFrame( self, frame ):
    if not self._window.valid:
      return

    if not frame:
      self._UndisplayPC()
      return

    if 'instructionPointerReference' not in frame:
      self._UndisplayPC()
      return

    self._instructionPointerReference = frame[ 'instructionPointerReference' ]
    self.current_frame = frame
    self._RequestInstructions()


  def _RequestInstructions( self ):
    def handler( msg ):
      self.current_instructions = msg.get( 'body', {} ).get( 'instructions' )
      with utils.RestoreCursorPosition():
        self._DrawInstructions()

    self.instruction_offset = -self._window.height
    self.instruction_count = self._window.height * 2

    self._connection.DoRequest( handler, {
      'command': 'disassemble',
      'arguments': {
        'memoryReference': self._instructionPointerReference,
        'offset': 0,
        'instructionOffset': self.instruction_offset,
        'instructionCount': self.instruction_count,
        'resolveSymbols': True
      }
    } )

    # TODO: Window scrolled autocommand to update ?


  def Clear( self ):
    self._UndisplayPC()
    with utils.ModifiableScratchBuffer( self._window.buffer ):
      utils.ClearBuffer( self._window.buffer )


  def Reset( self ):
    self.Clear()

    for b in self._scratch_buffers:
      utils.CleanUpHiddenBuffer( b )

    self._scratch_buffers = []


  def _DrawInstructions( self ):
    if not self._window.valid:
      return

    if not self.current_instructions:
      return

    buf_name = os.path.join(
      '_vimspector_disassembly',
      self.current_frame[ 'instructionPointerReference' ] )

    file_name = ( self.current_frame.get( 'source' ) or {} ).get( 'path' ) or ''
    buf = utils.BufferForFile( buf_name )

    utils.Call( 'setbufvar',
                buf.number,
                'vimspector_disassembly_path',
                file_name )
    utils.Call( 'setbufvar', buf.number, '&filetype', 'vimspector-disassembly' )

    self._scratch_buffers.append( buf )
    utils.SetUpHiddenBuffer( buf, buf_name )
    with utils.ModifiableScratchBuffer( buf ):
      utils.SetBufferContents( buf, [
        f"{ utils.Hex( utils.ParseAddress( i['address'] ) )}:\t"
        f"{ i.get( 'instructionBytes', '' ):20}\t"
        f"{ i[ 'instruction' ] }"
          for i in self.current_instructions
      ] )

    with utils.LetCurrentWindow( self._window ):
      utils.OpenFileInCurrentWindow( buf_name )
      utils.SetUpUIWindow( self._window )
      self._window.options[ 'signcolumn' ] = 'auto'

    self._DisplayPC( buf_name )


  def _DisplayPC( self, buf_name ):
    self._UndisplayPC()

    if len( self.current_instructions ) < self.instruction_count:
      self._logger.warn( "Invalid number of instructions returned by adapter: "
                         "Requested: %s, but got %s",
                         self.instruction_count,
                         len( self.current_instructions ) )
      return

    # otherwise, the current instruction is defined as the one we asked for,
    # accounting for any offset we asked for (note, 1-based line number)
    self._signs[ 'vimspectorPC' ] = SIGN_ID
    pc_line = -self.instruction_offset + 1
    signs.PlaceSign( self._signs[ 'vimspectorPC' ],
                     'VimspectorDisassembly',
                     'vimspectorPC',
                     buf_name,
                     pc_line )

    try:
      utils.SetCursorPosInWindow( self._window,
                                  pc_line,
                                  1,
                                  make_visible = True )
    except vim.error:
      pass

  def _UndisplayPC( self ):
    if self._signs[ 'vimspectorPC' ]:
      signs.UnplaceSign( self._signs[ 'vimspectorPC' ],
                         'VimspectorDisassembly' )
      self._signs[ 'vimspectorPC' ] = None
