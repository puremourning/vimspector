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

from vimspector.debug_session import DebugSession

# Singleton
_session_manager = None


class SessionManager:
  next_session_id = 0
  sessions = {}

  # TODO: Move breakpoints _out_ of the DebugSession and store/manage them
  # here. That may help with all the duplicated signs. Or perhaps hack further
  # by informing the _child_ session of its parent, and have it use the parent's
  # breakpoints. Actually that may be better first step.


  def NewSession( self, *args, **kwargs ):
    session_id = self.next_session_id
    self.next_session_id += 1
    session = DebugSession( session_id, self, *args, **kwargs )
    self.sessions[ session_id ] = session

    return session


  def DestroySession( self, session: DebugSession ):
    # TODO: Call this!
    del self.sessions[ session.session_id ]


  def GetSession( self, session_id ):
    return self.sessions.get( session_id )


  def SessionForTab( self, tabnr ):
    for _, session in self.sessions.items():
      if session.HasUI() and session._uiTab.number == int( tabnr ):
        return session

    return None


def Get():
  global _session_manager
  if _session_manager is None:
    _session_manager = SessionManager()

  return _session_manager
