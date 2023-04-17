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

# Singleton
_session_manager = None


class SessionManager:
  next_session_id: int
  sessions: typing.Dict[ int, DebugSession ]

  def __init__( self ):
    self.Reset()


  def Reset( self ):
    self.next_session_id = 0
    self.sessions = {}


  def NewSession( self, *args, **kwargs ) -> DebugSession:
    session_id = self.next_session_id
    self.next_session_id += 1
    session = DebugSession( session_id, self, *args, **kwargs )
    self.sessions[ session_id ] = session

    return session


  def DestroySession( self, session: DebugSession ):
    del self.sessions[ session.session_id ]


  def GetSession( self, session_id ) -> DebugSession:
    return self.sessions.get( session_id )


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
