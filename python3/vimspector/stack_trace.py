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
import typing

from vimspector import utils, signs, settings


class Thread:
  """The state of a single thread."""
  PAUSED = 0
  RUNNING = 1
  TERMINATED = 3
  state = RUNNING

  stopped_event: typing.Dict
  thread: typing.Dict
  stacktrace: typing.List[ typing.Dict ]
  id: str

  def __init__( self, thread ):
    self.id = thread[ 'id' ]
    self.stopped_event = None
    self.Update( thread )

  def Update( self, thread ):
    self.thread = thread
    self.stacktrace = None

  def Paused( self, event ):
    self.state = Thread.PAUSED
    self.stopped_event = event

  def Continued( self ):
    self.state = Thread.RUNNING
    self.stopped_event = None
    self.Collapse()

  def Exited( self ):
    self.state = Thread.TERMINATED
    self.stopped_event = None

  def State( self ):
    if self.state == Thread.PAUSED:
      return self.stopped_event.get( 'description' ) or 'paused'
    elif self.state == Thread.RUNNING:
      return 'running'
    return 'terminated'

  def Expand( self, stack_trace ):
    self.stacktrace = stack_trace

  def Collapse( self ):
    self.stacktrace = None

  def IsExpanded( self ):
    return self.stacktrace is not None

  def CanExpand( self ):
    return self.state == Thread.PAUSED


class StackTraceView( object ):
  class ThreadRequestState:
    NO = 0
    REQUESTING = 1
    PENDING = 2

  # FIXME: Make into a dict by id ?
  _threads: typing.List[ Thread ]
  _line_to_thread = typing.Dict[ int, Thread ]

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

    # FIXME: This ID is by group, so should be module scope
    self._current_thread_sign_id = 0 # 1 when used
    self._current_frame_sign_id = 0 # 2 when used

    utils.SetUpHiddenBuffer( self._buf, 'vimspector.StackTrace' )
    utils.SetUpUIWindow( win )

    mappings = settings.Dict( 'mappings' )[ 'stack_trace' ]

    with utils.LetCurrentWindow( win ):
      for mapping in utils.GetVimList( mappings, 'expand_or_jump' ):
        vim.command( f'nnoremap <silent> <buffer> { mapping } '
                     ':<C-U>call vimspector#GoToFrame()<CR>' )

      for mapping in utils.GetVimList( mappings, 'focus_thread' ):
        vim.command( f'nnoremap <silent> <buffer> { mapping } '
                     ':<C-U>call vimspector#SetCurrentThread()<CR>' )

      if utils.UseWinBar():
        vim.command( 'nnoremenu <silent> 1.1 WinBar.Pause/Continue '
                     ':call vimspector#PauseContinueThread()<CR>' )
        vim.command( 'nnoremenu <silent> 1.2 WinBar.Expand/Collapse '
                     ':call vimspector#GoToFrame()<CR>' )
        vim.command( 'nnoremenu <silent> 1.3 WinBar.Focus '
                     ':call vimspector#SetCurrentThread()<CR>' )

    win.options[ 'cursorline' ] = False
    win.options[ 'signcolumn' ] = 'auto'


    if not signs.SignDefined( 'vimspectorCurrentThread' ):
      signs.DefineSign( 'vimspectorCurrentThread',
                        text = '▶ ',
                        double_text = '▶',
                        texthl = 'MatchParen',
                        linehl = 'CursorLine' )

    if not signs.SignDefined( 'vimspectorCurrentFrame' ):
      signs.DefineSign( 'vimspectorCurrentFrame',
                        text = '▶ ',
                        double_text = '▶',
                        texthl = 'Special',
                        linehl = 'CursorLine' )

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
    self._threads.clear()
    self._sources = {}
    self._requesting_threads = StackTraceView.ThreadRequestState.NO
    self._pending_thread_request = None
    if self._current_thread_sign_id:
      signs.UnplaceSign( self._current_thread_sign_id, 'VimspectorStackTrace' )
    self._current_thread_sign_id = 0
    if self._current_frame_sign_id:
      signs.UnplaceSign( self._current_frame_sign_id, 'VimspectorStackTrace' )
    self._current_frame_sign_id = 0

    with utils.ModifiableScratchBuffer( self._buf ):
      utils.ClearBuffer( self._buf )

  def ConnectionUp( self, connection ):
    self._connection = connection

  def ConnectionClosed( self ):
    self.Clear()
    self._connection = None

  def Reset( self ):
    self.Clear()
    utils.CleanUpHiddenBuffer( self._buf )
    for b in self._scratch_buffers:
      utils.CleanUpHiddenBuffer( b )
    self._scratch_buffers = []
    self._buf = None

  def LoadThreads( self,
                   infer_current_frame,
                   reason = '',
                   stopEvent = None ):
    if self._requesting_threads != StackTraceView.ThreadRequestState.NO:
      self._requesting_threads = StackTraceView.ThreadRequestState.PENDING
      self._pending_thread_request = ( infer_current_frame,
                                       reason,
                                       stopEvent )
      return

    def consume_threads( message ):
      requesting = False
      if self._requesting_threads == StackTraceView.ThreadRequestState.PENDING:
        # We may have hit a thread event, so try again.
        self._requesting_threads = StackTraceView.ThreadRequestState.NO
        self.LoadThreads( *self._pending_thread_request )
        requesting = True

      self._requesting_threads = StackTraceView.ThreadRequestState.NO
      self._pending_thread_request = None

      if not ( message.get( 'body' ) or {} ).get( 'threads' ):
        # This is a protocol error. It is required to return at least one!
        utils.UserMessage( 'Protocol error: Server returned no threads',
                           persist = False,
                           error = True )
        return

      existing_threads = self._threads[ : ]
      self._threads.clear()

      if stopEvent is not None:
        stoppedThreadId = stopEvent.get( 'threadId' )
        allThreadsStopped = stopEvent.get( 'allThreadsStopped', False )

      # FIXME: This is horribly inefficient
      for t in message[ 'body' ][ 'threads' ]:
        thread = None
        for existing_thread in existing_threads:
          if existing_thread.id == t[ 'id' ]:
            thread = existing_thread
            thread.Update( t )
            break

        if not thread:
          thread = Thread( t )

        self._threads.append( thread )

        # If the threads were requested due to a stopped event, update any
        # stopped thread state. Note we have to do this here (rather than in the
        # stopped event handler) because we must apply this event to any new
        # threads that are received here.
        if stopEvent:
          if allThreadsStopped:
            thread.Paused( stopEvent )
          elif stoppedThreadId is not None and thread.id == stoppedThreadId:
            thread.Paused( stopEvent )

        # If this is a stopped event, load the stack trace for the "current"
        # thread. Don't do this on other thrads requests because some servers
        # just break when that happens.
        #
        # Don't do this if we're also satisfying a cached request already (we'll
        # do it then)
        if infer_current_frame and not requesting:
          if thread.id == self._current_thread:
            if thread.CanExpand():
              self._LoadStackTrace( thread, True, reason )
              requesting = True
          elif self._current_thread is None:
            self._current_thread = thread.id
            if thread.CanExpand():
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

  def _DrawThreads( self ):
    self._line_to_frame.clear()
    self._line_to_thread.clear()

    if self._current_thread_sign_id:
      signs.UnplaceSign( self._current_thread_sign_id, 'VimspectorStackTrace' )
    else:
      self._current_thread_sign_id = 1

    with utils.ModifiableScratchBuffer( self._buf ):
      with utils.RestoreCursorPosition():
        utils.ClearBuffer( self._buf )

        for thread in self._threads:
          icon = '+' if not thread.IsExpanded() else '-'
          line = utils.AppendToBuffer(
            self._buf,
            f'{icon} Thread {thread.id}: {thread.thread["name"]} '
            f'({thread.State()})' )

          if self._current_thread == thread.id:
            signs.PlaceSign( self._current_thread_sign_id,
                             'VimspectorStackTrace',
                             'vimspectorCurrentThread',
                             self._buf.name,
                             line )

          self._line_to_thread[ line ] = thread
          self._DrawStackTrace( thread )

  def _LoadStackTrace( self,
                       thread: Thread,
                       infer_current_frame,
                       reason = '' ):

    def consume_stacktrace( message ):
      thread.Expand( message[ 'body' ][ 'stackFrames' ] )
      if infer_current_frame:
        for frame in thread.stacktrace:
          if self._JumpToFrame( frame, reason ):
            break

      self._DrawThreads()

    self._connection.DoRequest( consume_stacktrace, {
      'command': 'stackTrace',
      'arguments': {
        'threadId': thread.id,
      }
    } )


  def _GetSelectedThread( self ) -> Thread:
    if vim.current.buffer != self._buf:
      return None

    return self._line_to_thread.get( vim.current.window.cursor[ 0 ] )


  def GetSelectedThreadId( self ):
    thread = self._GetSelectedThread()
    return thread.id if thread else thread

  def _SetCurrentThread( self, thread: Thread ):
    self._current_thread = thread.id
    self._DrawThreads()

  def SetCurrentThread( self ):
    thread = self._GetSelectedThread()
    if thread:
      self._SetCurrentThread( thread )
    elif vim.current.buffer != self._buf:
      return
    elif vim.current.window.cursor[ 0 ] in self._line_to_frame:
      thread, frame = self._line_to_frame[ vim.current.window.cursor[ 0 ] ]
      self._SetCurrentThread( thread )
      self._JumpToFrame( frame )
    else:
      utils.UserMessage( "No thread selected" )

  def ExpandFrameOrThread( self ):
    thread = self._GetSelectedThread()

    if thread:
      if thread.IsExpanded():
        thread.Collapse()
        self._DrawThreads()
      elif thread.CanExpand():
        self._LoadStackTrace( thread, False )
      else:
        utils.UserMessage( "Thread is not stopped" )
    elif vim.current.buffer != self._buf:
      return
    elif vim.current.window.cursor[ 0 ] in self._line_to_frame:
      thread, frame = self._line_to_frame[ vim.current.window.cursor[ 0 ] ]
      self._JumpToFrame( frame )



  def _GetFrameOffset( self, delta ):
    thread: Thread
    for thread in self._threads:
      if thread.id != self._current_thread:
        continue

      if not thread.stacktrace:
        return

      frame_idx = None
      for index, frame in enumerate( thread.stacktrace ):
        if frame == self._current_frame:
          frame_idx = index
          break

      if frame_idx is not None:
        target_idx = frame_idx + delta
        if target_idx >= 0 and target_idx < len( thread.stacktrace ):
          return thread.stacktrace[ target_idx ]

      break


  def UpFrame( self ):
    frame = self._GetFrameOffset( 1 )
    if not frame:
      utils.UserMessage( 'Top of stack' )
    else:
      self._JumpToFrame( frame, 'up' )


  def DownFrame( self ):
    frame = self._GetFrameOffset( -1 )
    if not frame:
      utils.UserMessage( 'Bottom of stack' )
    else:
      self._JumpToFrame( frame, 'down' )


  def AnyThreadsRunning( self ):
    for thread in self._threads:
      if thread.state != Thread.TERMINATED:
        return True

    return False


  def _JumpToFrame( self, frame, reason = '' ):
    def do_jump():
      if 'line' in frame and frame[ 'line' ] > 0:
        # Should this set the current _Thread_ too ? If i jump to a frame in
        # Thread 2, should that become the focussed thread ?
        self._current_frame = frame
        self._DrawThreads()
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


  def PauseContinueThread( self ):
    thread = self._GetSelectedThread()
    if thread is None:
      utils.UserMessage( 'No thread selected' )
    elif thread.state == Thread.PAUSED:
      self._session._connection.DoRequest(
        lambda msg: self.OnContinued( {
          'threadId': thread.id,
          'allThreadsContinued': ( msg.get( 'body' ) or {} ).get(
            'allThreadsContinued',
            True )
        } ),
        {
          'command': 'continue',
          'arguments': {
            'threadId': thread.id,
          },
        } )
    elif thread.state == Thread.RUNNING:
      self._session._connection.DoRequest( None, {
        'command': 'pause',
        'arguments': {
          'threadId': thread.id,
        },
      } )
    else:
      utils.UserMessage(
        f'Thread cannot be modified in state {thread.State()}' )


  def OnContinued( self, event = None ):
    threadId = None
    allThreadsContinued = True

    if event is not None:
      threadId = event[ 'threadId' ]
      allThreadsContinued = event.get( 'allThreadsContinued', False )

    for thread in self._threads:
      if allThreadsContinued:
        thread.Continued()
      elif thread.id == threadId:
        thread.Continued()
        break

    self._DrawThreads()

  def OnStopped( self, event ):
    threadId = event.get( 'threadId' )
    allThreadsStopped = event.get( 'allThreadsStopped', False )

    # Work out if we should change the current thread
    if threadId is not None:
      self._current_thread = threadId
    elif self._current_thread is None and allThreadsStopped and self._threads:
      self._current_thread = self._threads[ 0 ].id

    self.LoadThreads( True, 'stopped', event )

  def OnThreadEvent( self, event ):
    infer_current_frame = False
    if event[ 'reason' ] == 'started' and self._current_thread is None:
      self._current_thread = event[ 'threadId' ]
      infer_current_frame = True

    if event[ 'reason' ] == 'exited':
      for thread in self._threads:
        if thread.id == event[ 'threadId' ]:
          thread.Exited()
          break

    self.LoadThreads( infer_current_frame )

  def OnExited( self, event ):
    for thread in self._threads:
      thread.Exited()

  def _DrawStackTrace( self, thread: Thread ):
    if not thread.IsExpanded():
      return

    if self._current_frame_sign_id:
      signs.UnplaceSign( self._current_frame_sign_id, 'VimspectorStackTrace' )
    else:
      self._current_frame_sign_id = 2

    for frame in thread.stacktrace:
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

      if self._current_frame[ 'id' ] == frame[ 'id' ]:
        signs.PlaceSign( self._current_frame_sign_id,
                         'VimspectorStackTrace',
                         'vimspectorCurrentFrame',
                         self._buf.name,
                         line )

      self._line_to_frame[ line ] = ( thread, frame )

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
