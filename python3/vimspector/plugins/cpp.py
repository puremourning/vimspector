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


import json
import os
from vimspector import gadgets, installer


def InstallCppTools( name, root, gadget ):
  extension = os.path.join( root, 'extension' )

  # It's hilarious, but the execute bits aren't set in the vsix. So they
  # actually have javascript code which does this. It's just a horrible horrible
  # hack that really is not funny.
  installer.MakeExecutable( os.path.join( extension,
                                          'debugAdapters',
                                          'OpenDebugAD7' ) )
  with open( os.path.join( extension, 'package.json' ) ) as f:
    package = json.load( f )
    runtime_dependencies = package[ 'runtimeDependencies' ]
    for dependency in runtime_dependencies:
      for binary in dependency.get( 'binaries' ):
        file_path = os.path.abspath( os.path.join( extension, binary ) )
        if os.path.exists( file_path ):
          installer.MakeExecutable( os.path.join( extension, binary ) )

  installer.MakeExtensionSymlink( name, root )


gadgets.RegisterGadget( 'vscode-cpptools', {
  'language': 'c',
  'download': {
    'url': 'https://github.com/Microsoft/vscode-cpptools/releases/download/'
           '${version}/${file_name}',
  },
  'do': lambda name, root, gadget: InstallCppTools( name, root, gadget ),
  'all': {
    'version': '0.27.0',
    "adapters": {
      "vscode-cpptools": {
        "name": "cppdbg",
        "command": [
          "${gadgetDir}/vscode-cpptools/debugAdapters/OpenDebugAD7"
        ],
        "attach": {
          "pidProperty": "processId",
          "pidSelect": "ask"
        },
        "configuration": {
          "type": "cppdbg",
          "args": [],
          "cwd": "${workspaceRoot}",
          "environment": [],
        }
      },
    },
  },
  'linux': {
    'file_name': 'cpptools-linux.vsix',
    'checksum':
      '3695202e1e75a03de18049323b66d868165123f26151f8c974a480eaf0205435',
  },
  'macos': {
    'file_name': 'cpptools-osx.vsix',
    'checksum':
      'cb061e3acd7559a539e5586f8d3f535101c4ec4e8a48195856d1d39380b5cf3c',
  },
  'windows': {
    'file_name': 'cpptools-win32.vsix',
    'checksum':
      'aa294368ed16d48c59e49c8000e146eae5a19ad07b654efed5db8ec93b24229e',
    "adapters": {
      "vscode-cpptools": {
        "name": "cppdbg",
        "command": [
          "${gadgetDir}/vscode-cpptools/debugAdapters/bin/OpenDebugAD7.exe"
        ],
        "attach": {
          "pidProperty": "processId",
          "pidSelect": "ask"
        },
        "configuration": {
          "type": "cppdbg",
          "args": [],
          "cwd": "${workspaceRoot}",
          "environment": [],
          "MIMode": "gdb",
          "MIDebuggerPath": "gdb.exe"
        }
      },
    },
  },
} )


gadgets.RegisterGadget( 'CodeLLDB', {
  'language': 'rust',
  'enabled': True,
  'download': {
    'url': 'https://github.com/vadimcn/vscode-lldb/releases/download/'
           '${version}/${file_name}',
  },
  'all': {
    'version': 'v1.5.3',
  },
  'macos': {
    'file_name': 'codelldb-x86_64-darwin.vsix',
    'checksum':
      '7505bc1cdfcfd1cb981e2996aec62d63577440709bac31dcadb41a3b4b44631a',
    'make_executable': [
      'adapter/codelldb',
      'lldb/bin/debugserver',
      'lldb/bin/lldb',
      'lldb/bin/lldb-argdumper',
    ],
  },
  'linux': {
    'file_name': 'codelldb-x86_64-linux.vsix',
    'checksum':
      'ce7efc3e94d775368e5942a02bf5c326b6809a0b4c389f79ffa6a8f6f6b72139',
    'make_executable': [
      'adapter/codelldb',
      'lldb/bin/lldb',
      'lldb/bin/lldb-server',
      'lldb/bin/lldb-argdumper',
    ],
  },
  'windows': {
    'file_name': 'codelldb-x86_64-windows.vsix',
    'checksum':
      '',
    'make_executable': []
  },
  'adapters': {
    'CodeLLDB': {
      'name': 'CodeLLDB',
      'type': 'CodeLLDB',
      "command": [
        "${gadgetDir}/CodeLLDB/adapter/codelldb",
        "--port", "${unusedLocalPort}"
      ],
      "port": "${unusedLocalPort}",
      "configuration": {
        "type": "lldb",
        "name": "lldb",
        "cargo": {},
        "args": [],
        "cwd": "${workspaceRoot}",
        "env": {},
        "terminal": "integrated",
      }
    },
  },
} )
