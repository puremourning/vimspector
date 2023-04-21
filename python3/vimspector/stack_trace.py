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

# Because flake8 wants this to be defined, but it's a circular import, so we
# can't do it in proper code;
# https://adamj.eu/tech/2021/05/13/python-type-hints-how-to-fix-circular-imports
from typing import TYPE_CHECKING
if TYPE_CHECKING:
  from vimspector.debug_session import DebugSession


class ThreadRequestState:
  NO = 0
  REQUESTING = 1
  PENDING = 2


class Thread:
  """The state of a single thread."""
  PAUSED = 0
  RUNNING = 1
  TERMINATED = 3
  state = RUNNING

  stopped_event: typing.Dict
  thread: typing.Dict
  session: "Session"
  stacktrace: typing.List[ typing.Dict ]
  id: str

  def __init__( self, session: "Session", thread ):
    self.session = session
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


class Session( object ):
  threads: typing.List[ Thread ]
  session: "DebugSession"
  requesting_threads = ThreadRequestState.NO
  pending_thread_request = None
  sources: dict

  def __init__( self, session: "DebugSession" ):
    self.session = session
    self.threads = []
    self.sources = {}


class StackTraceView( object ):
  # FIXME: Make into a dict by id ?
  _sessions: typing.List[ Session ]
  _line_to_thread: typing.Dict[ int, Thread ]

  def __init__( self, session_id, win ):
    self._logger = logging.getLogger(
      __name__ + '.' + str( session_id ) )
    utils.SetUpLogging( self._logger, session_id )

    self._buf = win.buffer

    self._sessions = []

    self._current_session = None
    self._current_thread = None
    self._current_frame = None
    self._current_syntax = ""

    self._scratch_buffers = []

    # FIXME: This ID is by group, so should be module scope
    self._current_thread_sign_id = 0 # 1 when used
    self._current_frame_sign_id = 0 # 2 when used
    self._top_of_stack_signs = []

    utils.SetUpHiddenBuffer(
      self._buf,
      utils.BufferNameForSession( 'vimspector.StackTrace', session_id ) )
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
        vim.command( 'nnoremenu <silent> 1.2 WinBar.+/- '
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



  def GetCurrentSession( self ):
    if not self._current_session:
      return None
    return self._current_session.session

  def GetCurrentThreadId( self ):
    return self._current_thread

  def GetCurrentFrame( self ):
    return self._current_frame

  def Clear( self ):
    self._sessions.clear()

    self._current_session = None
    self._current_frame = None
    self._current_thread = None
    self._current_syntax = ""
    if self._current_thread_sign_id:
      signs.UnplaceSign( self._current_thread_sign_id, 'VimspectorStackTrace' )
    self._current_thread_sign_id = 0
    if self._current_frame_sign_id:
      signs.UnplaceSign( self._current_frame_sign_id, 'VimspectorStackTrace' )
    self._current_frame_sign_id = 0
    for sign_id in self._top_of_stack_signs:
      signs.UnplaceSign( sign_id, 'VimspectorStackTrace' )
    self._top_of_stack_signs = []

    with utils.ModifiableScratchBuffer( self._buf ):
      utils.ClearBuffer( self._buf )


  def ConnectionClosed( self, session ):
    self._sessions[ : ] = [ s for s in self._sessions if s.session != session ]


  def Reset( self ):
    self.Clear()
    utils.CleanUpHiddenBuffer( self._buf )
    for b in self._scratch_buffers:
      utils.CleanUpHiddenBuffer( b )
    self._scratch_buffers = []
    self._buf = None


  def AddSession( self, debug_session: "DebugSession" ):
    self._sessions.append( Session( debug_session ) )


  def FindSession( self, debug_session: "DebugSession" ):
    for s in self._sessions:
      if s.session == debug_session:
        return s

    return None


  def LoadThreads( self,
                   debug_session,
                   infer_current_frame,
                   reason = '',
                   stopEvent = None ):

    s = self.FindSession( debug_session )

    if s is None:
      return

    if s.requesting_threads != ThreadRequestState.NO:
      s.requesting_threads = ThreadRequestState.PENDING
      s.pending_thread_request = ( infer_current_frame,
                                   reason,
                                   stopEvent )
      return

    def consume_threads( message ):
      requesting = False
      if s.requesting_threads == ThreadRequestState.PENDING:
        # We may have hit a thread event, so try again.
        # Note that we do have to process this message though to ensure that our
        # thread states are all correct.
        s.requesting_threads = ThreadRequestState.NO
        self.LoadThreads( s.session, *s.pending_thread_request )
        requesting = True

      s.requesting_threads = ThreadRequestState.NO
      s.pending_thread_request = None

      if not ( message.get( 'body' ) or {} ).get( 'threads' ):
        # This is a protocol error. It is required to return at least one!
        # But about 100% of servers break the protocol.
        return

      existing_threads = s.threads[ : ]
      s.threads.clear()

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
          thread = Thread( s, t )

        s.threads.append( thread )

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
            self._current_session = s
            self._current_thread = thread.id
            if thread.CanExpand():
              self._LoadStackTrace( thread, True, reason )
              requesting = True

      if not requesting:
        self._DrawThreads()

    def failure_handler( reason, msg ):
      # Make sure we request them again if the request fails
      s.requesting_threads = ThreadRequestState.NO
      s.pending_thread_request = None

    s.requesting_threads = ThreadRequestState.REQUESTING
    debug_session.Connection().DoRequest( consume_threads, {
      'command': 'threads',
    }, failure_handler )

  def _DrawThreads( self ):
    self._line_to_frame.clear()
    self._line_to_thread.clear()

    if self._current_thread_sign_id:
      signs.UnplaceSign( self._current_thread_sign_id, 'VimspectorStackTrace' )
    else:
      self._current_thread_sign_id = 1

    if self._current_frame_sign_id:
      signs.UnplaceSign( self._current_frame_sign_id, 'VimspectorStackTrace' )
    else:
      self._current_frame_sign_id = 2

    for sign_id in self._top_of_stack_signs:
      signs.UnplaceSign( sign_id, 'VimspectorStackTrace' )
    self._top_of_stack_signs = []

    with utils.ModifiableScratchBuffer( self._buf ):
      with utils.RestoreCursorPosition():
        utils.ClearBuffer( self._buf )

        for s in self._sessions:
          if len( self._sessions ) > 1:
            line = utils.AppendToBuffer(
              self._buf,
              [ '---', f'Session: { s.session.DisplayName() }' ],
              hl = 'CursorLineNr' )

          for thread in s.threads:
            icon = '+' if not thread.IsExpanded() else '-'
            line = utils.AppendToBuffer(
              self._buf,
              f'{icon} Thread {thread.id}: {thread.thread["name"]} '
              f'({thread.State()})',
              hl = 'Title' )

            if self._current_session == s and self._current_thread == thread.id:
              signs.PlaceSign( self._current_thread_sign_id,
                               'VimspectorStackTrace',
                               'vimspectorCurrentThread',
                               self._buf.name,
                               line )

              for win in utils.AllWindowsForBuffer( self._buf ):
                utils.SetCursorPosInWindow(
                  win,
                  line,
                  make_visible = utils.VisiblePosition.TOP )

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
          if self._JumpToFrame( thread, frame, reason ):
            break

      self._DrawThreads()

    thread.session.session.Connection().DoRequest( consume_stacktrace, {
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
    self._current_session = thread.session
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
      self._JumpToFrame( thread, frame )
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
      self._JumpToFrame( thread, frame )



  def _GetFrameOffset( self, delta ):
    thread: Thread
    for thread in self._current_session.threads:
      if thread.id != self._current_thread:
        continue

      if not thread.stacktrace:
        return None, None

      frame_idx = None
      for index, frame in enumerate( thread.stacktrace ):
        if frame == self._current_frame:
          frame_idx = index
          break

      if frame_idx is not None:
        target_idx = frame_idx + delta
        if target_idx >= 0 and target_idx < len( thread.stacktrace ):
          return thread, thread.stacktrace[ target_idx ]

      break
    return None, None


  def UpFrame( self ):
    offset = 1
    while True:
      thread, frame = self._GetFrameOffset( offset )
      if not frame:
        utils.UserMessage( 'Top of stack' )
        return
      elif self._JumpToFrame( thread, frame, 'up' ):
        return
      offset += 1


  def DownFrame( self ):
    offset = -1
    while True:
      thread, frame = self._GetFrameOffset( offset )
      if not frame:
        utils.UserMessage( 'Bottom of stack' )
        return
      elif self._JumpToFrame( thread, frame, 'down' ):
        return
      offset -= 1



  def JumpToProgramCounter( self ):
    thread, frame = self._GetFrameOffset( 0 )
    if not frame:
      utils.UserMessage( 'No current stack frame' )
    else:
      self._JumpToFrame( thread, frame, 'jump' )


  def AnyThreadsRunning( self ):
    for session in self._sessions:
      for thread in session.threads:
        if thread.state != Thread.TERMINATED:
          return True

    return False


  def _JumpToFrame( self, thread: Thread, frame, reason = '' ):
    def do_jump():
      if 'line' in frame and frame[ 'line' ] > 0:
        self._current_session = thread.session
        self._current_thread = thread.id
        self._current_frame = frame
        self._DrawThreads()
        return thread.session.session.SetCurrentFrame( self._current_frame,
                                                       reason )
      return False

    source = frame.get( 'source' ) or {}
    if source.get( 'sourceReference', 0 ) > 0:
      def handle_resolved_source( resolved_source ):
        frame[ 'source' ] = resolved_source
        do_jump()
      self._ResolveSource( thread, source, handle_resolved_source )
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
      thread.session.session.Connection().DoRequest(
        lambda msg: self.OnContinued( thread.session.session, {
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
      thread.session.session.Connection().DoRequest( None, {
        'command': 'pause',
        'arguments': {
          'threadId': thread.id,
        },
      } )
    else:
      utils.UserMessage(
        f'Thread cannot be modified in state {thread.State()}' )


  def OnContinued( self, debug_session, event = None ):
    threadId = None
    allThreadsContinued = True
    session = self.FindSession( debug_session )

    if session is None:
      return

    if event is not None:
      threadId = event[ 'threadId' ]
      allThreadsContinued = event.get( 'allThreadsContinued', False )

    for thread in session.threads:
      if allThreadsContinued:
        thread.Continued()
      elif thread.id == threadId:
        thread.Continued()
        break

    self._DrawThreads()

  def OnStopped( self, debug_session, event ):
    threadId = event.get( 'threadId' )
    allThreadsStopped = event.get( 'allThreadsStopped', False )
    session = self.FindSession( debug_session )

    if session is None:
      return

    # Work out if we should change the current thread
    if threadId is not None:
      self._current_session = session
      self._current_thread = threadId
    elif self._current_thread is None and allThreadsStopped and session.threads:
      self._current_session = session
      self._current_thread = session.threads[ 0 ].id

    self.LoadThreads( debug_session, True, 'stopped', event )

  def OnThreadEvent( self, debug_session, event ):
    infer_current_frame = False
    session = self.FindSession( debug_session )

    if session is None:
      return

    if event[ 'reason' ] == 'exited':
      for thread in session.threads:
        if thread.id == event[ 'threadId' ]:
          thread.Exited()
          break
      self._DrawThreads()
      return

    if event[ 'reason' ] == 'started' and self._current_thread is None:
      self._current_session = session
      self._current_thread = event[ 'threadId' ]
      infer_current_frame = True

    self.LoadThreads( debug_session, infer_current_frame )


  def OnExited( self, debug_session, event ):
    session = self.FindSession( debug_session )

    if session is None:
      return

    for thread in session.threads:
      thread.Exited()

    self._DrawThreads()


  def _DrawStackTrace( self, thread: Thread ):
    if not thread.IsExpanded():
      return

    set_top_of_stack = False
    for frame in thread.stacktrace:
      if frame.get( 'source' ):
        source = frame[ 'source' ]
      else:
        source = { 'name': '<unknown>' }

      if 'name' not in source:
        source[ 'name' ] = os.path.basename( source.get( 'path', 'unknown' ) )

      hl = settings.Dict( 'presentation_hint_hl' ).get(
        frame.get( 'presentationHint',
                   source.get( 'presentationHint',
                               'normal' ) ) )

      if frame.get( 'presentationHint' ) == 'label':
        # Sigh. FOr some reason, it's OK for debug adapters to completely ignore
        # the protocol; it seems that the chrome adapter sets 'label' and
        # doesn't set 'line'
        line = utils.AppendToBuffer(
          self._buf,
          '  {0}: {1}'.format( frame[ 'id' ], frame[ 'name' ] ),
          hl = hl )
      else:
        line = utils.AppendToBuffer(
          self._buf,
          '  {0}: {1}@{2}:{3}'.format( frame[ 'id' ],
                                       frame[ 'name' ],
                                       source[ 'name' ],
                                       frame[ 'line' ] ),
          hl = hl )

      if ( thread.session == self._current_session and
           self._current_frame is not None and
           self._current_frame[ 'id' ] == frame[ 'id' ] ):
        set_top_of_stack = True
        signs.PlaceSign( self._current_frame_sign_id,
                         'VimspectorStackTrace',
                         'vimspectorCurrentFrame',
                         self._buf.name,
                         line )
      elif not set_top_of_stack:
        if 'source' in frame and 'path' in frame[ 'source' ]:
          set_top_of_stack = True
          sign_id = len( self._top_of_stack_signs ) + 100
          self._top_of_stack_signs.append( sign_id )
          signs.PlaceSign( sign_id,
                           'VimspectorStackTrace',
                           'vimspectorNonActivePC',
                           self._buf.name,
                           line )

          if utils.BufferExists( frame[ 'source' ][ 'path' ] ):
            sign_id = len( self._top_of_stack_signs ) + 100
            self._top_of_stack_signs.append( sign_id )
            signs.PlaceSign( sign_id,
                             'VimspectorStackTrace',
                             'vimspectorNonActivePC',
                             frame[ 'source' ][ 'path' ],
                             frame[ 'line' ] )


      self._line_to_frame[ line ] = ( thread, frame )

  def _ResolveSource( self, thread: Thread, source, and_then ):
    source_reference = int( source[ 'sourceReference' ] )
    try:
      and_then( thread.session.sources[ source_reference ] )
    except KeyError:
      # We must retrieve the source contents from the server
      self._logger.debug( "Requesting source: %s", source )

      def consume_source( msg ):
        thread.session.sources[ source_reference ] = source

        buf_name = os.path.join( '_vimspector_tmp',
                                 str( thread.session.session.session_id ),
                                 source.get( 'path', source[ 'name' ] ) )

        self._logger.debug( "Received source %s: %s", buf_name, msg )

        buf = utils.BufferForFile( buf_name )
        self._scratch_buffers.append( buf )
        utils.SetUpHiddenBuffer( buf,
                                 utils.BufferNameForSession(
                                   buf_name,
                                   thread.session.session.session_id ) )
        source[ 'path' ] = buf_name
        with utils.ModifiableScratchBuffer( buf ):
          utils.SetBufferContents( buf, msg[ 'body' ][ 'content' ] )

        and_then( thread.session.sources[ source_reference ] )

      thread.session.session.Connection().DoRequest( consume_source, {
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
