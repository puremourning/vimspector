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


  def SetCurrentFrame( self, frame ):
    if not self._window.valid:
      return

    if not frame:
      # TODO(BenJ): Clear PC
      return

    if 'instructionPointerReference' not in frame:
      # TODO(BenJ): Clear PC
      return

    instructionPointerReference = frame[ 'instructionPointerReference' ]

    self.current_frame = frame;

    def handler( msg ):
      self.current_instructions = msg.get( 'body', {} ).get( 'instructions' ) 
      with utils.RestoreCursorPosition():
        self._DrawInstructions()

    self._connection.DoRequest( handler, {
      'command': 'disassemble',
      'arguments': {
        'memoryReference': instructionPointerReference,
        'offset': 0,
        'instructionOffset': -20,
        'instructionCount': 40, # TODO: what is a good number? window size?
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
    buf = utils.BufferForFile( buf_name )
    self._scratch_buffers.append( buf )
    utils.SetUpHiddenBuffer( buf, buf_name )
    with utils.ModifiableScratchBuffer( buf ):
      utils.SetBufferContents( buf, [
        i['address'] + ":\t" + i[ 'instruction' ]
          for i in self.current_instructions
      ] )

    with utils.LetCurrentWindow( self._window ):
      utils.OpenFileInCurrentWindow( buf_name )

    self._DisplayPC( buf_name )


  def _DisplayPC( self, buf_name ):
    self._UndisplayPC()

    if 'line' not in self.current_frame or self.current_frame[ 'line' ] < 1:
      self._logger.debug( "DisassemblyView(PC): No line in current_frame" )
      return

    if 'path' not in self.current_frame.get( 'source', {} ):
      self._logger.debug( "DisassemblyView(PC): No path in source" )
      return

    current_path = self.current_frame[ 'source' ][ 'path' ]
    current_line = self.current_frame[ 'line' ]

    self._logger.debug(
      "DisassemblyView(PC): Searching for the instruction for %s:%s",
      current_path,
      current_line )

    # Try and map the current frame to instructions
    cur_location = None
    # If not found, assume we are at instruction 0 on the basis that we asked
    # for a 0 offset
    cur_instr_index = 0
    for instr_index, instruction in enumerate( self.current_instructions ):
      if cur_location is None:
        cur_location = instruction.get( 'location' )

      if 'line' not in instruction:
        self._logger.debug( "DisassemblyView(PC): No line in instruction" )
        continue

      line = instruction[ 'line' ]
      location = instruction.get( 'location', cur_location )

      if not location or 'path' not in location:
        # TODO: what about sourceReference
        self._logger.debug( "DisassemblyView(PC): no path in location" )
        continue

      if location[ 'path' ] != current_path:
        self._logger.debug( "DisassemblyView(PC): Path is not for this frame" )
        continue

      if line > current_line:
        self._logger.debug( "DisassemblyView(PC): Line is beyond current PC line" )
        break

      if 'endLine' in instruction and instruction[ 'endLine' ] < current_line:
        self._logger.debug( "DisassemblyView(PC): Line ends before current PC" )
        break

      # Found it
      self._logger.debug( "DisassemblyView(PC): Candidate (%s @ %s:%s)",
                          instr_index,
                          current_path,
                          line )
      cur_instr_index = instr_index

    self._logger.debug( "DisassemblyView(PC): Finished" )
    self._signs[ 'vimspectorPC' ] = SIGN_ID
    signs.PlaceSign( self._signs[ 'vimspectorPC' ],
                     'VimspectorDisassembly',
                     'vimspectorPC',
                     buf_name,
                     cur_instr_index + 1 )

    try:
      utils.SetCursorPosInWindow( self._window,
                                  cur_instr_index + 1,
                                  1,
                                  make_visible = True )
    except vim.error:
      pass

  def _UndisplayPC( self ):
    if self._signs[ 'vimspectorPC' ]:
      signs.UnplaceSign( self._signs[ 'vimspectorPC' ],
                         'VimspectorDisassembly' )
      self._signs[ 'vimspectorPC' ] = None
