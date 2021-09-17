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

from vimspector import utils, install

import vim
import json
import typing


class TabBuffer( object ):
  def __init__( self, buf, index ):
    self.buf = buf
    self.index = index
    self.flag = False
    self.is_job = False
    self.syntax = None


BUFFER_MAP = {
  'console': 'Console',
  'stdout': 'Console',
  'output': 'Console',
  'stderr': 'stderr',
  'telemetry': None,
}


def CategoryToBuffer( category ):
  return BUFFER_MAP.get( category, category )


VIEWS = set()


def ShowOutputInWindow( win_id, category ):
  for view in VIEWS:
    if view._window.valid and utils.WindowID( view._window ) == win_id:
      view.ShowOutput( category )
      return

  raise ValueError( f'Unable to find output object for win id {win_id}!' )


class OutputView( object ):
  """Container for a 'tabbed' window of buffers that can be used to display
  files or the output of commands."""
  _buffers: typing.Dict[ str, TabBuffer ]

  def __init__( self, window, api_prefix ):
    self._window = window
    self._buffers = {}
    self._api_prefix = api_prefix
    VIEWS.add( self )

  def Print( self, category, text: typing.Union[ str, list ] ):
    if not isinstance( text, list ):
      text = text.splitlines()

    self._Print( category, text )

  def OnOutput( self, event ):
    category = CategoryToBuffer( event.get( 'category' ) or 'output' )
    text_lines = event[ 'output' ].splitlines()
    if 'data' in event:
      text_lines.extend( json.dumps( event[ 'data' ],
                                     indent = 2 ).splitlines() )

    self._Print( category, text_lines )

  def _Print( self, category, text_lines ):
    if category is None:
      # This category is supressed
      return

    if category not in self._buffers:
      self._CreateBuffer( category )

    buf = self._buffers[ category ].buf

    with utils.ModifiableScratchBuffer( buf ):
      utils.AppendToBuffer( buf, text_lines )

    self._ToggleFlag( category, True )

    # Scroll the buffer
    if self._window.valid:
      with utils.RestoreCurrentWindow():
        with utils.RestoreCurrentBuffer( self._window ):
          self._ShowOutput( category )

  def Reset( self ):
    self.Clear()
    VIEWS.remove( self )


  def Clear( self ):
    for category, tab_buffer in self._buffers.items():
      self._CleanUpBuffer( category, tab_buffer )

    # FIXME: nunmenu the WinBar ?
    self._buffers = {}


  def ClearCategory( self, category: str ):
    if category not in self._buffers:
      return

    self._CleanUpBuffer( category, self._buffers[ category ] )


  def _CleanUpBuffer( self, category: str, tab_buffer: TabBuffer ):
    if tab_buffer.is_job:
      utils.CleanUpCommand( category, self._api_prefix )

    utils.CleanUpHiddenBuffer( tab_buffer.buf )


  def WindowIsValid( self ):
    return self._window.valid

  def UseWindow( self, win ):
    assert not self._window.valid
    self._window = win
    # TODO: Sorting of the WinBar ?
    for category, _ in self._buffers.items():
      self._RenderWinBar( category )


  def _ShowOutput( self, category ):
    if not self._window.valid:
      return

    utils.JumpToWindow( self._window )
    vim.current.buffer = self._buffers[ category ].buf
    vim.command( 'normal G' )

  def ShowOutput( self, category ):
    self._ToggleFlag( category, False )
    self._ShowOutput( category )

  def _ToggleFlag( self, category, flag ):
    if self._buffers[ category ].flag != flag:
      self._buffers[ category ].flag = flag

      if self._window.valid:
        with utils.LetCurrentWindow( self._window ):
          self._RenderWinBar( category )


  def RunJobWithOutput( self, category, cmd, **kwargs ):
    self._CreateBuffer( category, cmd = cmd, **kwargs )


  def _CreateBuffer( self,
                     category,
                     file_name = None,
                     cmd = None,
                     completion_handler = None,
                     syntax = None ):

    buf_to_delete = None
    if ( not self._buffers
         and self._window is not None
         and self._window.valid
         and not self._window.buffer.name ):
      # If there's an empty buffer in the current window that we're not using,
      # delete it. We could try and use it, but that complicates the call to
      # SetUpCommandBuffer
      buf_to_delete = self._window.buffer

    if file_name is not None:
      assert cmd is None
      if install.GetOS() == "windows":
        # FIXME: Can't display fiels in windows (yet?)
        return

      cmd = [ 'tail', '-F', '-n', '+1', '--', file_name ]

    if cmd is not None:
      out = utils.SetUpCommandBuffer(
        cmd,
        category,
        self._api_prefix,
        completion_handler = completion_handler )

      self._buffers[ category ] = TabBuffer( out, len( self._buffers ) )
      self._buffers[ category ].is_job = True
      self._RenderWinBar( category )
    else:
      if category == 'Console':
        name = 'vimspector.Console'
      else:
        name = 'vimspector.Output:{0}'.format( category )

      tab_buffer = TabBuffer( utils.NewEmptyBuffer(), len( self._buffers ) )

      self._buffers[ category ] = tab_buffer

      if category == 'Console':
        utils.SetUpPromptBuffer( tab_buffer.buf,
                                 name,
                                 '> ',
                                 'vimspector#EvaluateConsole',
                                 'vimspector#OmniFuncConsole' )
      else:
        utils.SetUpHiddenBuffer( tab_buffer.buf, name )

      self._RenderWinBar( category )

    self._buffers[ category ].syntax = utils.SetSyntax(
      self._buffers[ category ].syntax,
      syntax,
      self._buffers[ category ].buf )

    if buf_to_delete:
      with utils.RestoreCurrentWindow():
        self._ShowOutput( category )
      utils.CleanUpHiddenBuffer( buf_to_delete )

  def _RenderWinBar( self, category ):
    if not utils.UseWinBar():
      return

    if not self._window.valid:
      return

    with utils.LetCurrentWindow( self._window ):
      tab_buffer = self._buffers[ category ]

      try:
        if tab_buffer.flag:
          vim.command( 'nunmenu WinBar.{}'.format( utils.Escape( category ) ) )
        else:
          vim.command( 'nunmenu WinBar.{}*'.format( utils.Escape( category ) ) )
      except vim.error as e:
        # E329 means the menu doesn't exist; ignore that.
        if 'E329' not in str( e ):
          raise

      vim.command(
        "nnoremenu <silent> 1.{0} WinBar.{1}{2} "
        ":call vimspector#ShowOutputInWindow( {3}, '{1}' )<CR>".format(
          tab_buffer.index,
          utils.Escape( category ),
          '*' if tab_buffer.flag else '',
          utils.WindowID( self._window ) ) )

  def GetCategories( self ):
    return list( self._buffers.keys() )

  def AddLogFileView( self, file_name = utils.LOG_FILE ):
    self._CreateBuffer( 'Vimspector', file_name = file_name )


class DAPOutputView( OutputView ):
  """Specialised OutputView which adds the DAP Console (REPL)"""
  def __init__( self, *args ):
    super().__init__( *args )

    self._connection = None
    for b in set( BUFFER_MAP.values() ):
      if b is not None:
        self._CreateBuffer( b )

    self.AddLogFileView()
    self._ShowOutput( 'Console' )

  def ConnectionUp( self, connection ):
    self._connection = connection

  def ConnectionClosed( self ):
    # Don't clear because output is probably still useful
    self._connection = None

  def Evaluate( self, frame, expression, verbose ):
    if verbose:
      self._Print( 'Console', f"Evaluating: { expression }" )

    def print_result( message ):
      result = message[ 'body' ][ 'result' ]
      if result is None:
        result = '<no result>'
      self._Print( 'Console', result.splitlines() )

    def print_failure( reason, msg ):
      self._Print( 'Console', reason.splitlines() )

    request = {
      'command': 'evaluate',
      'arguments': {
        'expression': expression,
        'context': 'repl',
      }
    }

    if frame:
      request[ 'arguments' ][ 'frameId' ] = frame[ 'id' ]

    self._connection.DoRequest( print_result,
                                request,
                                print_failure )
