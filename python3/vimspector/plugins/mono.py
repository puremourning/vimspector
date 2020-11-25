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


from vimspector import gadgets


gadgets.RegisterGadget( 'vscode-mono-debug', {
  'language': 'csharp',
  'enabled': False,
  'download': {
    'url': 'https://marketplace.visualstudio.com/_apis/public/gallery/'
           'publishers/ms-vscode/vsextensions/mono-debug/${version}/'
           'vspackage',
    'target': 'vscode-mono-debug.vsix.gz',
    'format': 'zip.gz',
  },
  'all': {
    'file_name': 'vscode-mono-debug.vsix',
    'version': '0.16.2',
    'checksum':
        '121eca297d83daeeb1e6e1d791305d1827998dbd595c330086b3b94d33dba3b9',
  },
  'adapters': {
    'vscode-mono-debug': {
      "name": "mono-debug",
      "command": [
        "mono",
        "${gadgetDir}/vscode-mono-debug/bin/Release/mono-debug.exe"
      ],
      "attach": {
        "pidSelect": "none"
      },
      "configuration": {
        "cwd": "${workspaceRoot}",
        "console": "integratedTerminal",
        "args": [],
        "env": {}
      }
    },
  }
} )
