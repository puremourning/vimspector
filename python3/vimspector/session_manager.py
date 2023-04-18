# vimspector - A multi-language debugging system for Vim
# Copyright 2020 Ben Jackson
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

import typing
from vimspector.debug_session import DebugSession
from vimspector import utils

# Singleton
_session_manager = None


class SessionManager:
  next_session_id: int
  sessions: typing.Dict[ int, DebugSession ]
  api_prefix: str = ''

  def __init__( self ):
    self.Reset()


  def Reset( self ):
    self.next_session_id = 0
    self.sessions = {}


  def NewSession( self, *args, **kwargs ) -> DebugSession:
    session_id = self.next_session_id
    self.next_session_id += 1
    session = DebugSession( session_id, self, self.api_prefix, *args, **kwargs )
    self.sessions[ session_id ] = session

    return session


  def DestroySession( self, session: DebugSession ):
    try:
      session = self.sessions.pop( session.session_id )
    except KeyError:
      return


  def DestroyRootSession( self,
                          session: DebugSession,
                          active_session: DebugSession ):
    if session.HasUI() or session.Connection():
      utils.UserMessage( "Can't destroy active session; use VimspectorReset",
                         error = True )
      return active_session

    try:
      self.sessions.pop( session.session_id )
      session.Destroy()
    except KeyError:
      utils.UserMessage( "Session doesn't exist", error = True )
      return active_session

    if active_session != session:
      # OK, we're done. No need to change the active session
      return active_session

    # Return the first root session in the list to be the new active one
    for existing_session in self.sessions.values():
      if not existing_session.parent_session:
        return existing_session

    # There are somehow no non-root sessions. Clear the current one. We'll
    # probably create a new one next time the user does anything.
    return None


  def GetSession( self, session_id ) -> DebugSession:
    return self.sessions.get( session_id )


  def GetSessionNames( self ) -> typing.List[ str ]:
    return [ s.Name()
             for s in self.sessions.values()
             if not s.parent_session and s.Name() ]


  def SessionsWithInvalidUI( self ):
    for _, session in self.sessions.items():
      if not session.parent_session and not session.HasUI():
        yield session


  def FindSessionByTab( self, tabnr: int ) -> DebugSession:
    for _, session in self.sessions.items():
      if session.HasUI() and session.IsUITab( tabnr ):
        return session

    return None


  def FindSessionByName( self, name ) -> DebugSession:
    for _, session in self.sessions.items():
      if session.Name() == name:
        return session

    return None


  def SessionForTab( self, tabnr ) -> DebugSession:
    session: DebugSession
    for _, session in self.sessions.items():
      if session.IsUITab( tabnr ):
        return session

    return None


def Get():
  global _session_manager
  if _session_manager is None:
    _session_manager = SessionManager()

  return _session_manager
