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
from vimspector import utils, settings


class JavaDebugAdapter( object ):
  def __init__( self, debug_session: DebugSession ):
    self.debug_session = debug_session

  def OnEvent_hotcodereplace( self, message ):
    # Hack for java debug server hot-code-replace
    body = message.get( 'body' ) or {}

    if body.get( 'type' ) != 'hotcodereplace':
      return

    if body.get( 'changeType' ) == 'BUILD_COMPLETE':
      def handler( result ):
        if result == 1:
          self.debug_session._connection.DoRequest( None, {
            'command': 'redefineClasses',
            'arguments': {},
          } )

      mode = settings.Get( 'java_hotcodereplace_mode' )
      if mode == 'ask':
        utils.Confirm( self.debug_session._api_prefix,
                       'Code has changed, hot reload?',
                       handler,
                       default_value = 1 )
      elif mode == 'always':
        self.debug_session._connection.DoRequest( None, {
          'command': 'redefineClasses',
          'arguments': {},
        } )
    elif body.get( 'message' ):
      utils.UserMessage( 'Hot code replace: ' + body[ 'message' ] )
