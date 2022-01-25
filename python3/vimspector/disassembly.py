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

from vimspector import signs, utils


class DisassemblyView( object ):
  def __init__( self, window, connection, api_prefix ):
    self._window = window
    self._api_prefix = api_prefix
    self._connection = connection

    self._scratch_buffers = []

    with utils.LetCurrentWindow( self._window ):
      if utils.UseWinBar():
        pass

    signs.DefineProgramCounterSigns()


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

    def handler( msg ):
      self._ShowInstructions( frame,
                              instructionPointerReference,
                              msg.get( 'body', {} ).get( 'instructions' ) )

    self._connection.DoRequest( handler, {
      'command': 'disassemble',
      'arguments': {
        'memoryReference': instructionPointerReference,
        'offset': 0,
        'instructionOffset': 0,
        'instructionCount': 60,
        'resolveSymbols': True
      }
    } )



  def _ShowInstructions( self, frame, ref, instructions ):
    if not self._window.valid:
      return

    if not instructions:
      return

    buf_name = os.path.join( '_vimspector_disassembly', ref )
    buf = utils.BufferForFile( buf_name )
    self._scratch_buffers.append( buf )
    utils.SetUpHiddenBuffer( buf, buf_name )
    with utils.ModifiableScratchBuffer( buf ):
      utils.SetBufferContents( buf, [
        i[ 'instruction' ] for i in instructions
      ] )

    with utils.LetCurrentWindow( self._window ):
      utils.OpenFileInCurrentWindow( buf_name )


  def Clear( self ):
    pass


  def Reset( self ):
    self.Clear()

    for b in self._scratch_buffers:
      utils.CleanUpHiddenBuffer( b )

    self._scratch_buffers = []
