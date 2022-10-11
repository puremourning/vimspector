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

import logging

import vim

from vimspector import signs, utils

SIGN_ID = 1


class DisassemblyView( object ):
  def __init__( self, window, connection, api_prefix, render_event_emitter ):
    self._logger = logging.getLogger( __name__ )
    utils.SetUpLogging( self._logger )

    self._render_emitter = render_event_emitter
    self._render_emitter.subscribe( self._DisplayPC )
    self._window = window
    # Initially we don't care about the buffer. We only update it when we have
    # one crated from the request.
    self._buf = None

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

  def ConnectionClosed( self ):
    self._connection = None

  def WindowIsValid( self ):
    return self._window is not None and self._window.valid

  def IsCurrent( self ):
    return vim.current.buffer == self._buf

  def SetCurrentFrame( self, frame, should_jump_to_location ):
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
    self._RequestInstructions( should_jump_to_location )


  def _RequestInstructions( self, should_jump_to_location ):
    def handler( msg ):
      self.current_instructions = msg.get( 'body', {} ).get( 'instructions' )
      self._DrawInstructions( should_jump_to_location )

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


  def Clear( self ):
    self._UndisplayPC()

    with utils.ModifiableScratchBuffer( self._buf ):
      utils.ClearBuffer( self._buf )

    self.current_frame = None
    self.current_instructions = None


  def Reset( self ):
    self.Clear()
    self._buf = None
    for b in self._scratch_buffers:
      utils.CleanUpHiddenBuffer( b )

    self._scratch_buffers = []


  def IsDisassemblyBuffer( self, file_name ):
    if not self._buf:
      return False
    return ( utils.NormalizePath( file_name ) ==
                utils.NormalizePath( self._buf.name ) )

  def GetMemoryReference( self ):
    return self._instructionPointerReference

  def GetOffsetForLine( self, line_num ):
    if line_num <= 0 or line_num > self.instruction_count:
      return None

    # Offset is in bytes
    pc = utils.ParseAddress(
      self.current_instructions[ self._GetPCEntryOffset() ][ 'address' ] )
    req = utils.ParseAddress(
      self.current_instructions[ line_num - 1 ][ 'address' ] )
    return req - pc

  def ResolveAddressAtLine( self, line_num ):
    if line_num <= 0 or line_num > self.instruction_count:
      return None

    return utils.ParseAddress(
      self.current_instructions[ line_num - 1 ][ 'address' ] )

  def FindLineForAddress( self, address ):
    if not self.current_instructions:
      return 0

    for index, instruction in enumerate( self.current_instructions ):
      the_addr = utils.ParseAddress( instruction[ 'address' ] )
      if the_addr == address:
        return index + 1
    return 0

  def _GetPCEntryOffset( self ):
    return -self.instruction_offset

  def GetBufferName( self ):
    if not self._buf:
      return None
    return self._buf.name

  def _DrawInstructions( self, should_jump_to_location ):
    if not self._window.valid:
      return

    if not self.current_instructions:
      return

    buf_name = '_vimspector_disassembly'
    file_name = ( self.current_frame.get( 'source' ) or {} ).get( 'path' ) or ''
    self._buf = utils.BufferForFile( buf_name )

    utils.Call( 'setbufvar',
                self._buf.number,
                'vimspector_disassembly_path',
                file_name )
    utils.Call( 'setbufvar',
                self._buf.number,
                '&filetype',
                'vimspector-disassembly' )

    self._scratch_buffers.append( self._buf )
    utils.SetUpHiddenBuffer( self._buf, buf_name )
    instruction_bytes_len = max( len( i.get( 'instructionBytes', '' ) )
                                 for i in self.current_instructions )
    with utils.ModifiableScratchBuffer( self._buf ):
      utils.SetBufferContents( self._buf, [
        f"{ utils.Hex( utils.ParseAddress( i['address'] ) )}:\t"
        f"{ i.get( 'instructionBytes', '' ):{instruction_bytes_len}}\t"
        f"{ i[ 'instruction' ] }"
          for i in self.current_instructions
      ] )

    with utils.LetCurrentWindow( self._window ):
      utils.OpenFileInCurrentWindow( buf_name )
      utils.SetUpUIWindow( self._window )
      self._window.options[ 'signcolumn' ] = 'yes'

    # Re-render and re-calcaulte breakpoints
    #
    # TODO: If instruction breakpoints are persisted across runs, their
    # addresses might be resolvable now that we've just got the disassembly.
    #
    # But this call won't actually _send_ any breakpoints to the server. THis
    # means that they don't persist properly until you do something which
    # triggers the breakpoints code to re-send all the breakpoints.
    #
    # Anyway, that complexity is why we always clear instruction breakpoints
    # at the end of sessions.
    self._render_emitter.emit()

    try:
      if should_jump_to_location:
        utils.JumpToWindow( self._window )
        utils.SetCursorPosInWindow( self._window,
                                    self._GetPCEntryOffset() + 1,
                                    1,
                                    make_visible = True )
      else:
        with utils.RestoreCursorPosition():
          utils.SetCursorPosInWindow( self._window,
                                      self._GetPCEntryOffset() + 1,
                                      1,
                                      make_visible = True )
    except vim.error as e:
      utils.UserMessage( f"Failed to set cursor position for disassembly: {e}",
                         error = True )



  def _DisplayPC( self ):
    self._UndisplayPC()

    if not self._connection or not self._buf or not self.current_instructions:
      return

    if len( self.current_instructions ) < self.instruction_count:
      self._logger.warn( "Invalid number of instructions returned by adapter: "
                         "Requested: %s, but got %s",
                         self.instruction_count,
                         len( self.current_instructions ) )
      return

    # otherwise, the current instruction is defined as the one we asked for,
    # accounting for any offset we asked for (note, 1-based line number)
    self._signs[ 'vimspectorPC' ] = SIGN_ID * 92
    pc_line = self._GetPCEntryOffset() + 1
    signs.PlaceSign( self._signs[ 'vimspectorPC' ],
                     'VimspectorDisassembly',
                     'vimspectorPC',
                     self._buf.name,
                     pc_line )


  def _UndisplayPC( self ):
    if self._signs[ 'vimspectorPC' ]:
      signs.UnplaceSign( self._signs[ 'vimspectorPC' ],
                         'VimspectorDisassembly' )
      self._signs[ 'vimspectorPC' ] = None
