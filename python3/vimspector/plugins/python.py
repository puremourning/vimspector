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

import sys
import os
from vimspector import gadgets, installer


def InstallDebugpy( name, root, gadget ):
  wd = os.getcwd()
  root = os.path.join( root, 'debugpy-{}'.format( gadget[ 'version' ] ) )
  os.chdir( root )
  try:
    installer.CheckCall( [ sys.executable, 'setup.py', 'build' ] )
  finally:
    os.chdir( wd )

  installer.MakeSymlink( name, root )


gadgets.RegisterGadget( 'debugpy', {
  'language': 'python',
  'download': {
    'url': 'https://github.com/microsoft/debugpy/archive/${file_name}'
  },
  'all': {
    'version': '1.0.0b12',
    'file_name': 'v1.0.0b12.zip',
    'checksum':
      '210632bba2221fbb841c9785a615258819ceec401d1abdbeb5f2326f12cc72a1'
  },
  'do': lambda name, root, gadget: InstallDebugpy( name, root, gadget ),
  'adapters': {
    'debugpy': {
      "command": [
        sys.executable, # TODO: Will this work from within Vim ?
        "${gadgetDir}/debugpy/build/lib/debugpy/adapter"
      ],
      "name": "debugpy",
      "configuration": {
        "python": sys.executable, # TODO: Will this work from within Vim ?
        # Don't debug into subprocesses, as this leads to problems (vimspector
        # doesn't support the custom messages)
        # https://github.com/puremourning/vimspector/issues/141
        "subProcess": False,
      }
    }
  },
} )


gadgets.RegisterGadget( 'vscode-python', {
  'language': 'python.legacy',
  'enabled': False,
  'download': {
    'url': 'https://github.com/Microsoft/vscode-python/releases/download/'
           '${version}/${file_name}',
  },
  'all': {
    'version': '2019.11.50794',
    'file_name': 'ms-python-release.vsix',
    'checksum':
      '6a9edf9ecabed14aac424e6007858068204a3638bf3bb4f235bd6035d823acc6',
  },
  'adapters': {
    "vscode-python": {
      "name": "vscode-python",
      "command": [
        "node",
        "${gadgetDir}/vscode-python/out/client/debugger/debugAdapter/main.js",
      ],
    }
  },
} )
