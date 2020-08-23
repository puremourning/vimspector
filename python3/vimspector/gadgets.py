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


from vimspector import installer
import sys
import os


GADGETS = {}

GADGETS[ 'vscode-cpptools' ] = {
  'language': 'c',
  'download': {
    'url': 'https://github.com/Microsoft/vscode-cpptools/releases/download/'
           '${version}/${file_name}',
  },
  'do': lambda name, root, gadget: installer.InstallCppTools( name,
                                                              root,
                                                              gadget ),
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
}

GADGETS[ 'vscode-python' ] = {
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
}

GADGETS[ 'debugpy' ] = {
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
  'do': lambda name, root, gadget: installer.InstallDebugpy( name,
                                                             root,
                                                             gadget ),
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
}

GADGETS[ 'vscode-java-debug' ] = {
  'language': 'java',
  'enabled': False,
  'download': {
    'url': 'https://github.com/microsoft/vscode-java-debug/releases/download/'
           '${version}/${file_name}',
  },
  'all': {
    'version': '0.26.0',
    'file_name': 'vscjava.vscode-java-debug-0.26.0.vsix',
    'checksum':
      'de49116ff3a3c941dad0c36d9af59baa62cd931e808a2ab392056cbb235ad5ef',
  },
  'adapters': {
    "vscode-java": {
      "name": "vscode-java",
      "port": "${DAPPort}",
      "configuration": {
        "cwd": "${workspaceRoot}"
      }
    }
  },
}

GADGETS[ 'java-language-server' ] = {
  'language': 'javac',
  'enabled': False,
  'download': {
    'url': 'https://marketplace.visualstudio.com/_apis/public/gallery/'
           'publishers/georgewfraser/vsextensions/vscode-javac/${version}/'
           'vspackage',
    'target': 'georgewfraser.vscode-javac-0.2.31.vsix.gz',
    'format': 'zip.gz',
  },
  'all': {
    'version': '0.2.31',
    'file_name': 'georgewfraser.vscode-javac-0.2.31.vsix.gz',
    'checksum':
      '5b0248ec1198d3ece9a9c6b9433b30c22e308f0ae6e4c7bd09cd943c454e3e1d',
  },
  'adapters': {
    "vscode-javac": {
      "name": "vscode-javac",
      "type": "vscode-javac",
      "command": [
        "${gadgetDir}/java-language-server/dist/debug_adapter_mac.sh"
      ],
      "attach": {
        "pidSelect": "none"
      }
    }
  },
}

GADGETS[ 'tclpro' ] = {
  'language': 'tcl',
  'repo': {
    'url': 'https://github.com/puremourning/TclProDebug',
    'ref': 'v1.0.0'
  },
  'do': lambda name, root, gadget: installer.InstallTclProDebug( name,
                                                                 root,
                                                                 gadget ),
  'adapters': {
    "tclpro": {
      "name": "tclpro",
      "type": "tclpro",
      "command": [
        "${gadgetDir}/tclpro/bin/debugadapter"
      ],
      "attach": {
        "pidSelect": "none"
      },
      "configuration": {
        "target": "${file}",
        "args": [ "*${args}" ],
        "tclsh": "tclsh",
        "cwd": "${workspaceRoot}",
        "extensionDirs": [
          "${workspaceRoot}/.tclpro/extensions",
          "${HOME}/.tclpro/extensions",
        ]
      }
    }
  },
}

GADGETS[ 'netcoredbg' ] = {
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
}

GADGETS[ 'vscode-mono-debug' ] = {
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
}

GADGETS[ 'vscode-bash-debug' ] = {
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
  'do': lambda name, root, gadget: installer.InstallBashDebug( name,
                                                               root,
                                                               gadget ),
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
}

GADGETS[ 'vscode-go' ] = {
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
}

GADGETS[ 'vscode-php-debug' ] = {
  'language': 'php',
  'enabled': False,
  'download': {
    'url':
      'https://github.com/felixfbecker/vscode-php-debug/releases/download/'
      '${version}/${file_name}',
  },
  'all': {
    'version': 'v1.13.0',
    'file_name': 'php-debug.vsix',
    'checksum':
      '8a51e593458fd14623c1c89ebab87347b087d67087717f18bcf77bb788052718',
  },
  'adapters': {
    'vscode-php-debug': {
      'name': "php-debug",
      'command': [
        'node',
        "${gadgetDir}/vscode-php-debug/out/phpDebug.js",
      ]
    }
  }
}

GADGETS[ 'vscode-node-debug2' ] = {
  'language': 'node',
  'enabled': False,
  'repo': {
    'url': 'https://github.com/microsoft/vscode-node-debug2',
    'ref': 'v1.42.5'
  },
  'do': lambda name, root, gadget: installer.InstallNodeDebug( name,
                                                               root,
                                                               gadget ),
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
}

GADGETS[ 'debugger-for-chrome' ] = {
  'language': 'chrome',
  'enabled': False,
  'download': {
    'url': 'https://marketplace.visualstudio.com/_apis/public/gallery/'
           'publishers/msjsdiag/vsextensions/'
           'debugger-for-chrome/${version}/vspackage',
    'target': 'msjsdiag.debugger-for-chrome-4.12.10.vsix.gz',
    'format': 'zip.gz',
  },
  'all': {
    'version': '4.12.10',
    'file_name': 'msjsdiag.debugger-for-chrome-4.12.10.vsix',
    'checksum':
      ''
  },
  'adapters': {
    'chrome': {
      'name': 'debugger-for-chrome',
      'type': 'chrome',
      'command': [
        'node',
        '${gadgetDir}/debugger-for-chrome/out/src/chromeDebug.js'
      ],
    },
  },
}

GADGETS[ 'CodeLLDB' ] = {
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
}

GADGETS[ 'local-lua-debugger-vscode' ] = {
  'language': 'lua',
  'enabled': True,
  'repo': {
    'url': 'https://github.com/tomblind/local-lua-debugger-vscode.git',
    'ref': 'release-${version}'
  },
  'all': {
    'version': '0.2.0',
  },
  'do': lambda name, root, gadget: installer.InstallLuaLocal( name,
                                                              root,
                                                              gadget ),
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
}
