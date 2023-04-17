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


class Debugpy( object ):
  parent: DebugSession

  def __init__( self, debug_session: DebugSession ):
    self.parent = debug_session

  def OnRequest_startDebugging( self, message ):
    config = message[ 'arguments' ][ 'configuration' ]
    adapter = config[ 'connect' ]
    adapter[ 'custom_handler' ] = self.parent._adapter[ 'custom_handler' ]
    self.parent._DoStartDebuggingRequest(
      message,
      message[ 'arguments' ][ 'request' ],
      message[ 'arguments' ][ 'configuration' ],
      adapter )
    # Indicate that we have processed this request
    return True
