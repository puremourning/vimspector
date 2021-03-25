# vimspector - A multi-language debugging system for Vim
# Copyright 2021 Ben Jackson
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
from vimspector import session_manager

from typing import Sequence


class Debugpy( object ):
  parent: DebugSession
  sessions: Sequence[ DebugSession ]

  def __init__( self, debug_session: DebugSession ):
    self.parent = debug_session


  def OnEvent_debugpyAttach( self, message ):
    # Debugpy sends us the contents of a launch request that we should use. We
    # probaly just jave to guess the rest
    launch_argyments = message[ 'body' ]
    session = session_manager.Get().NewSession( self.parent._api_prefix )

    # Inject the launch config (HACK!). This will actually mean that the
    # configuration passed below is ignored.
    session._launch_config = launch_argyments

    # FIXME: We probably do need to add a StartWithLauncArguments and somehow
    # tell the new session that it shoud not support "Restart" requests ?
    #
    # In fact, what even would Reset do... ?
    session._StartWithConfiguration( self.parent._configuration,
                                     self.parent._adapter )

