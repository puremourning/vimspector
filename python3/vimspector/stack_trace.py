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
import os
import logging

from vimspector import utils


# TODO: Need to do something a bit like the Variables stuff
#
# class Thread:
#   PAUSED = 0
#   RUNNING = 1
#   state = RUNNING
#
#   thread: dict
#   stacktrace: list
#
#   def __init__( self, thread ):
#     self.thread = thread
#     self.stacktrace = None
#
#   def ShouldExpand( self, current_thread_id ):
#     return self.thread[ 'id' ] == current_thread_id


class StackTraceView( object ):
  class ThreadRequestState:
    NO = 0
    REQUESTING = 1
    PENDING = 2

  def __init__( self, session, win ):
    self._logger = logging.getLogger( __name__ )
    utils.SetUpLogging( self._logger )

    self._buf = win.buffer
    self._session = session
    self._connection = None

    self._current_thread = None
    self._current_frame = None
    self._current_syntax = ""

    self._threads = []
    self._sources = {}
    self._scratch_buffers = []

    utils.SetUpHiddenBuffer( self._buf, 'vimspector.StackTrace' )
    utils.SetUpUIWindow( win )

    vim.command( 'nnoremap <silent> <buffer> <CR> '
                 ':<C-U>call vimspector#GoToFrame()<CR>' )
    vim.command( 'nnoremap <silent> <buffer> <2-LeftMouse> '
                 ':<C-U>call vimspector#GoToFrame()<CR>' )

    self._line_to_frame = {}
    self._line_to_thread = {}

    self._requesting_threads = StackTraceView.ThreadRequestState.NO
    self._pending_thread_request = None


  def GetCurrentThreadId( self ):
    return self._current_thread

  def GetCurrentFrame( self ):
    return self._current_frame

  def Clear( self ):
    self._current_frame = None
    self._current_thread = None
    self._current_syntax = ""
    self._threads = []
    self._sources = {}
    with utils.ModifiableScratchBuffer( self._buf ):
      utils.ClearBuffer( self._buf )

  def ConnectionUp( self, connection ):
    self._connection = connection

  def ConnectionClosed( self ):
    self.Clear()
    self._connection = None
    self._requesting_threads = StackTraceView.ThreadRequestState.NO
    self._pending_thread_request = None

  def Reset( self ):
    self.Clear()
    utils.CleanUpHiddenBuffer( self._buf )
    for b in self._scratch_buffers:
      utils.CleanUpHiddenBuffer( b )

    self._scratch_buffers = []
    self._buf = None
    self._requesting_threads = StackTraceView.ThreadRequestState.NO
    self._pending_thread_request = None

  def LoadThreads( self, infer_current_frame, reason = '' ):
    if self._requesting_threads != StackTraceView.ThreadRequestState.NO:
      self._requesting_threads = StackTraceView.ThreadRequestState.PENDING
      self._pending_thread_request = ( infer_current_frame, reason )
      return

    def consume_threads( message ):
      if self._requesting_threads == StackTraceView.ThreadRequestState.PENDING:
        # We may have hit a thread event, so try again.
        self._requesting_threads = StackTraceView.ThreadRequestState.NO
        self.LoadThreads( *self._pending_thread_request )
        return

      if not message[ 'body' ][ 'threads' ]:
        # This is a protocol error. It is required to return at least one!
        utils.UserMessage( 'Protocol error: Server returned no threads',
                           persist = False,
                           error = True )

      self._requesting_threads = StackTraceView.ThreadRequestState.NO
      self._pending_thread_request = None
      self._threads.clear()

      requesting = False
      for thread in message[ 'body' ][ 'threads' ]:
        self._threads.append( thread )

        if infer_current_frame and thread[ 'id' ] == self._current_thread:
          self._LoadStackTrace( thread, True, reason )
          requesting = True
        elif infer_current_frame and self._current_thread is None:
          self._current_thread = thread[ 'id' ]
          self._LoadStackTrace( thread, True, reason )
          requesting = True

      if not requesting:
        self._DrawThreads()

    def failure_handler( reason, msg ):
      # Make sure we request them again if the request fails
      self._requesting_threads = StackTraceView.ThreadRequestState.NO
      self._pending_thread_request = None

    self._requesting_threads = StackTraceView.ThreadRequestState.REQUESTING
    self._connection.DoRequest( consume_threads, {
      'command': 'threads',
    }, failure_handler )

  def _DrawThreads( self, running = False ):
    self._line_to_frame.clear()
    self._line_to_thread.clear()

    with ( utils.ModifiableScratchBuffer( self._buf ),
           utils.RestoreCursorPosition() ):
      utils.ClearBuffer( self._buf )

      for thread in self._threads:
        if self._current_thread == thread[ 'id' ]:
          icon = '^' if '_frames' not in thread else '>'
        else:
          icon = '+' if '_frames' not in thread else '-'

        # FIXME: We probably need per-thread status here
        if running:
          status = ' (running)'
        else:
          status = ''

        line = utils.AppendToBuffer(
          self._buf,
          f'{icon} Thread: {thread["name"]}{status}' )

        self._line_to_thread[ line ] = thread
        self._DrawStackTrace( thread )

  def _LoadStackTrace( self,
                       thread,
                       infer_current_frame,
                       reason = '' ):
    def consume_stacktrace( message ):
      thread[ '_frames' ] = message[ 'body' ][ 'stackFrames' ]
      if infer_current_frame:
        for frame in thread[ '_frames' ]:
          if self._JumpToFrame( frame, reason ):
            break

      self._DrawThreads()

    self._connection.DoRequest( consume_stacktrace, {
      'command': 'stackTrace',
      'arguments': {
        'threadId': thread[ 'id' ],
      }
    } )

  def ExpandFrameOrThread( self ):
    if vim.current.buffer != self._buf:
      return

    current_line = vim.current.window.cursor[ 0 ]

    if current_line in self._line_to_frame:
      self._JumpToFrame( self._line_to_frame[ current_line ] )
    elif current_line in self._line_to_thread:
      thread = self._line_to_thread[ current_line ]
      if '_frames' in thread:
        del thread[ '_frames' ]
        self._DrawThreads()
      else:
        self._LoadStackTrace( thread, False )

  def _JumpToFrame( self, frame, reason = '' ):
    def do_jump():
      if 'line' in frame and frame[ 'line' ] > 0:
        self._current_frame = frame
        return self._session.SetCurrentFrame( self._current_frame, reason )
      return False

    source = frame.get( 'source' ) or {}
    if source.get( 'sourceReference', 0 ) > 0:
      def handle_resolved_source( resolved_source ):
        frame[ 'source' ] = resolved_source
        do_jump()
      self._ResolveSource( source, handle_resolved_source )
      # The assumption here is that we _will_ eventually find something to jump
      # to
      return True
    else:
      return do_jump()

  def OnContinued( self, threadId = None ):
    # FIXME: This tends to create a very flickery stack trace when steppping.
    # Maybe we shouldn't remove the frames, but just update the running status?
    # for thread in self._threads:
    #   if threadId is None or thread[ 'id' ] == threadId:
    #     thread.pop( '_frames', None )
    self._DrawThreads( running=True )

  def OnStopped( self, event ):
    if 'threadId' in event:
      self._current_thread = event[ 'threadId' ]
    elif event.get( 'allThreadsStopped', False ) and self._threads:
      self._current_thread = self._threads[ 0 ][ 'id' ]

    self.LoadThreads( True, 'stopped' )

  def OnThreadEvent( self, event ):
    if event[ 'reason' ] == 'started' and self._current_thread is None:
      self._current_thread = event[ 'threadId' ]
      self.LoadThreads( True )
    else:
      self.LoadThreads( False )

  def _DrawStackTrace( self, thread ):
    if '_frames' not in thread:
      return

    stackFrames = thread[ '_frames' ]

    for frame in stackFrames:
      if frame.get( 'source' ):
        source = frame[ 'source' ]
      else:
        source = { 'name': '<unknown>' }

      if 'name' not in source:
        source[ 'name' ] = os.path.basename( source.get( 'path', 'unknwon' ) )

      if frame.get( 'presentationHint' ) == 'label':
        # Sigh. FOr some reason, it's OK for debug adapters to completely ignore
        # the protocol; it seems that the chrome adapter sets 'label' and
        # doesn't set 'line'
        line = utils.AppendToBuffer(
          self._buf,
          '  {0}: {1}'.format( frame[ 'id' ], frame[ 'name' ] ) )
      else:
        line = utils.AppendToBuffer(
          self._buf,
          '  {0}: {1}@{2}:{3}'.format( frame[ 'id' ],
                                       frame[ 'name' ],
                                       source[ 'name' ],
                                       frame[ 'line' ] ) )

      self._line_to_frame[ line ] = frame

  def _ResolveSource( self, source, and_then ):
    source_reference = int( source[ 'sourceReference' ] )
    try:
      and_then( self._sources[ source_reference ] )
    except KeyError:
      # We must retrieve the source contents from the server
      self._logger.debug( "Requesting source: %s", source )

      def consume_source( msg ):
        self._sources[ source_reference ] = source

        buf_name = os.path.join( '_vimspector_tmp',
                                 source.get( 'path', source[ 'name' ] ) )

        self._logger.debug( "Received source %s: %s", buf_name, msg )

        buf = utils.BufferForFile( buf_name )
        self._scratch_buffers.append( buf )
        utils.SetUpHiddenBuffer( buf, buf_name )
        source[ 'path' ] = buf_name
        with utils.ModifiableScratchBuffer( buf ):
          utils.SetBufferContents( buf, msg[ 'body' ][ 'content' ] )

        and_then( self._sources[ source_reference ] )

      self._session._connection.DoRequest( consume_source, {
        'command': 'source',
        'arguments': {
          'sourceReference': source[ 'sourceReference' ],
          'source': source
        }
      } )

  def SetSyntax( self, syntax ):
    self._current_syntax = utils.SetSyntax( self._current_syntax,
                                            syntax,
                                            self._buf )
