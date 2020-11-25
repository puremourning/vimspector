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


from vimspector import gadgets, installer


def InstallNodeDebug( name, root, gadget ):
  with installer.CurrentWorkingDir( root ):
    installer.CheckCall( [ 'npm', 'install' ] )
    installer.CheckCall( [ 'npm', 'run', 'build' ] )
  installer.MakeSymlink( name, root )


gadgets.RegisterGadget( 'vscode-node-debug2', {
  'language': 'node',
  'enabled': False,
  'repo': {
    'url': 'https://github.com/microsoft/vscode-node-debug2',
    'ref': 'v1.42.5'
  },
  'do': lambda name, root, gadget: InstallNodeDebug( name, root, gadget ),
  'adapters': {
    'vscode-node': {
      'name': 'node2',
      'type': 'node2',
      'command': [
        'node',
        '${gadgetDir}/vscode-node-debug2/out/src/nodeDebug.js'
      ]
    },
  },
} )
