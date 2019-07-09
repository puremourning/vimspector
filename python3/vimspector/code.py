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

from vimspector import utils


class CodeView( object ):
  def __init__( self, window ):
    self._window = window

    self._logger = logging.getLogger( __name__ )
    utils.SetUpLogging( self._logger )

    self._next_sign_id = 1
    self._breakpoints = defaultdict( list )
    self._signs = {
      'vimspectorPC': None,
      'breakpoints': []
    }

    with utils.LetCurrentWindow( self._window ):
      vim.command( 'nnoremenu WinBar.Continue :call vimspector#Continue()<CR>' )
      vim.command( 'nnoremenu WinBar.Next :call vimspector#StepOver()<CR>' )
      vim.command( 'nnoremenu WinBar.Step :call vimspector#StepInto()<CR>' )
      vim.command( 'nnoremenu WinBar.Finish :call vimspector#StepOut()<CR>' )
      vim.command( 'nnoremenu WinBar.Pause :call vimspector#Pause()<CR>' )
      vim.command( 'nnoremenu WinBar.Stop :call vimspector#Stop()<CR>' )
      vim.command( 'nnoremenu WinBar.Restart :call vimspector#Restart()<CR>' )
      vim.command( 'nnoremenu WinBar.Reset :call vimspector#Reset()<CR>' )

      vim.command( 'sign define vimspectorPC text=-> texthl=Search' )


  def SetCurrentFrame( self, frame ):
    if self._signs[ 'vimspectorPC' ]:
      vim.command( 'sign unplace {} group=VimspectorCode'.format(
        self._signs[ 'vimspectorPC' ] ) )
      self._signs[ 'vimspectorPC' ] = None

    if not frame or not frame.get( 'source' ):
      return False

    if 'path' not in frame[ 'source' ]:
      return False

    utils.JumpToWindow( self._window )

    try:
      utils.OpenFileInCurrentWindow( frame[ 'source' ][ 'path' ] )
    except vim.error:
      self._logger.exception( 'Unexpected vim error opening file {}'.format(
        frame[ 'source' ][ 'path' ] ) )
      return False

    # SIC: column is 0-based, line is 1-based in vim. Why? Nobody knows.
    self._window.cursor = ( frame[ 'line' ], frame[ 'column' ]  - 1 )

    self._signs[ 'vimspectorPC' ] = self._next_sign_id
    self._next_sign_id += 1

    vim.command( 'sign place {0} group=VimspectorCode priority=20 '
                                 'line={1} name=vimspectorPC '
                                 'file={2}'.format(
                                   self._signs[ 'vimspectorPC' ],
                                   frame[ 'line' ],
                                   frame[ 'source' ][ 'path' ] ) )

    return True

  def Clear( self ):
    if self._signs[ 'vimspectorPC' ]:
      vim.command( 'sign unplace {} group=VimspectorCode'.format(
        self._signs[ 'vimspectorPC' ] ) )
      self._signs[ 'vimspectorPC' ] = None

    self._UndisplaySigns()

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

  def DeleteBreakpoint( self, bp ):
    if 'id' not in bp:
      return

    for _, breakpoint_list in self._breakpoints.items():
      for index, breakpoint in enumerate( breakpoint_list ):
        if 'id' in breakpoint and breakpoint[ 'id' ] == bp[ 'id' ]:
          del breakpoint_list[ index ]
          return

    # Not found. Shrug.

  def _UndisplaySigns( self ):
    for sign_id in self._signs[ 'breakpoints' ]:
      vim.command( 'sign unplace {} group=VimspectorCode'.format( sign_id ) )

    self._signs[ 'breakpoints' ].clear()

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
        vim.command(
          'sign place {0} group=VimspectorCode priority=9 '
                          'line={1} '
                          'name={2} '
                          'file={3}'.format(
                            sign_id,
                            breakpoint[ 'line' ],
                            'vimspectorBP' if breakpoint[ 'verified' ]
                            else 'vimspectorBPDisabled',
                            file_name ) )


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

    options = {
      'vertical': 1,
      'norestore': 1,
      'cwd': cwd,
      'env': env,
    }

    buffer_number = None
    with utils.TemporaryVimOptions( { 'splitright': True,
                                      'equalalways': False } ):
      with utils.LetCurrentWindow( self._window ):
        # TODO/FIXME: Do something about closing this when we reset ?
        vim_cmd =  'vimspector#term#start( {}, {} )'.format(
            json.dumps( args ),
            json.dumps( options ) )

        self._logger.debug( 'Start terminal: {}'.format( vim_cmd ) )

        buffer_number = int( vim.eval( vim_cmd ) )

    if buffer_number is None or buffer_number <= 0:
      # TODO: Do something better like reject the request?
      raise ValueError( "Unable to start terminal" )

    return buffer_number
