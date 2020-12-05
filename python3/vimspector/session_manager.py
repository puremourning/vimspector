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


class SessionManager:
  next_session_id = 0
  sessions = {}
  current_session = None


  def NewSession( self, *args, **kwargs ):
    session_id = self.next_session_id
    self.next_session_id += 1
    session = DebugSession( session_id, self, *args, **kwargs )
    self.sessions[ session_id ] = session

    if self.current_session is None:
      self.current_session = session.session_id

    return session


  def DestroySession( self, session: DebugSession ):
    del self.sessions[ session.session_id ]


  def GetSession( self, session_id ):
    return self.sessions.get( session_id )


  def CurrentSession( self ):
    return self.GetSession( self.current_session )
