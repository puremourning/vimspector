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


import os
from vimspector import gadgets, installer


# FIXME: InstallGeneric would work here
def InstallBashDebug( name, root, gadget ):
  installer.MakeExecutable( os.path.join( root,
                                          'extension',
                                          'bashdb_dir',
                                          'bashdb' ) )
  installer.MakeExtensionSymlink( name, root )


gadgets.RegisterGadget( 'vscode-bash-debug', {
  'language': 'bash',
  'download': {
    'url': 'https://github.com/rogalmic/vscode-bash-debug/releases/'
           'download/${version}/${file_name}',
  },
  'all': {
    'file_name': 'bash-debug-0.3.7.vsix',
    'version': 'v0.3.7',
    'checksum':
      '7b73e5b4604375df8658fb5a72c645c355785a289aa785a986e508342c014bb4',
  },
  'do': lambda name, root, gadget: InstallBashDebug( name, root, gadget ),
  'adapters': {
    "vscode-bash": {
      "name": "bashdb",
      "command": [
        "node",
        "${gadgetDir}/vscode-bash-debug/out/bashDebug.js"
      ],
      "variables": {
        "BASHDB_HOME": "${gadgetDir}/vscode-bash-debug/bashdb_dir"
      },
      "configuration": {
        "request": "launch",
        "type": "bashdb",
        "program": "${file}",
        "args": [],
        "env": {},
        "pathBash": "bash",
        "pathBashdb": "${BASHDB_HOME}/bashdb",
        "pathBashdbLib": "${BASHDB_HOME}",
        "pathCat": "cat",
        "pathMkfifo": "mkfifo",
        "pathPkill": "pkill",
        "cwd": "${workspaceRoot}",
        "terminalKind": "integrated",
      }
    }
  }
} )
