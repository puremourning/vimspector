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


gadgets.RegisterGadget( 'netcoredbg', {
  'language': 'csharp',
  'enabled': False,
  'download': {
    'url': ( 'https://github.com/Samsung/netcoredbg/releases/download/'
             '${version}/${file_name}' ),
    'format': 'tar',
  },
  'all': {
    'version': '1.2.0-635'
  },
  'macos': {
    'file_name': 'netcoredbg-osx.tar.gz',
    'checksum':
      '71c773e34d358950f25119bade7e3081c4c2f9d71847bd49027ca5792e918beb',
  },
  'linux': {
    'file_name': 'netcoredbg-linux-bionic.tar.gz',
    'checksum': '',
  },
  'windows': {
    'file_name': 'netcoredbg-win64.zip',
    'checksum': '',
  },
  'do': lambda name, root, gadget: installer.MakeSymlink(
    name,
    os.path.join( root, 'netcoredbg' ) ),
  'adapters': {
    'netcoredbg': {
      "name": "netcoredbg",
      "command": [
        "${gadgetDir}/netcoredbg/netcoredbg",
        "--interpreter=vscode"
      ],
      "attach": {
        "pidProperty": "processId",
        "pidSelect": "ask"
      },
      "configuration": {
        "cwd": "${workspaceRoot}"
      }
    },
  }
} )
