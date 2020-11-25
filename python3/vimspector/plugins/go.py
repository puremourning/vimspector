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


gadgets.RegisterGadget( 'vscode-go', {
  'language': 'go',
  'download': {
    'url': 'https://github.com/golang/vscode-go/releases/download/'
           'v${version}/${file_name}'
  },
  'all': {
    'version': '0.18.1',
    'file_name': 'Go-0.18.1.vsix',
    'checksum':
      '80d4522c6cf482cfa6141997e5b458034f67d7065d92e1ce24a0456c405d6061',
  },
  'adapters': {
    'vscode-go': {
      'name': 'delve',
      'command': [
        'node',
        '${gadgetDir}/vscode-go/dist/debugAdapter.js'
      ],
      "configuration": {
        "cwd": "${workspaceRoot}",
      }
    },
  },
} )
