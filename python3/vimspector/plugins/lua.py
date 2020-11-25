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


def InstallLuaLocal( name, root, gadget ):
  with installer.CurrentWorkingDir( root ):
    installer.CheckCall( [ 'npm', 'install' ] )
    installer.CheckCall( [ 'npm', 'run', 'build' ] )
  installer.MakeSymlink( name, root )


gadgets.RegisterGadget( 'local-lua-debugger-vscode', {
  'language': 'lua',
  'enabled': True,
  'repo': {
    'url': 'https://github.com/tomblind/local-lua-debugger-vscode.git',
    'ref': 'release-${version}'
  },
  'all': {
    'version': '0.2.0',
  },
  'do': lambda name, root, gadget: InstallLuaLocal( name, root, gadget ),
  'adapters': {
    'lua-local': {
      'command': [
        'node',
        '${gadgetDir}/local-lua-debugger-vscode/extension/debugAdapter.js'
      ],
      'name': 'lua-local',
      'configuration': {
        'interpreter': 'lua',
        'extensionPath': '${gadgetDir}/local-lua-debugger-vscode'
      }
    }
  },
} )
