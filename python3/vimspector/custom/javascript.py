# vimspector - A multi-language debugging system for Vim
# Copyright 2022 Ben Jackson
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

import logging

from vimspector.debug_session import DebugSession
from vimspector import session_manager, utils


class VsCodeJsDebug( object ):
  parent: DebugSession

  def __init__( self, debug_session: DebugSession ):
    self.parent = debug_session
    self._logger = logging.getLogger(
      __name__ + '.' + str( debug_session.session_id ) )
    utils.SetUpLogging( self._logger, debug_session.session_id )


  def OnRequest_attachedChildSession( self, message ):
    # This adapter is a POS, so we actually have to do something completely
    # bonkers here and re-initialize with a completely new configuration
    self._logger.debug( f"attachChildSession: { message }" )
    launch_arguments = message[ 'arguments' ][ 'config' ]

    adapter = {
      'host': '127.0.0.1', # presumably...
      'port': launch_arguments[ '__jsDebugChildServer' ],
    }

    session = session_manager.Get().NewSession( self.parent._api_prefix )

    # Inject the launch config (HACK!). This will actually mean that the
    # configuration passed below is ignored.
    session._launch_config = launch_arguments

    # FIXME: We probably do need to add a StartWithLauncArguments and somehow
    # tell the new session that it shoud not support "Restart" requests ?
    #
    # In fact, what even would Reset do... ?
    session._breakpoints.Copy( self.parent._breakpoints )
    session._StartWithConfiguration( { 'configuration': launch_arguments },
                                     adapter )

    self.parent._connection.DoResponse( message, None, {} )
