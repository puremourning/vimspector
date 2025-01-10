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


GADGETS = {
  'vscode-cpptools': {
    'language': [ 'c', 'cpp', 'rust' ],
    'download': {
      'url': 'https://github.com/Microsoft/vscode-cpptools/releases/download/'
             'v${version}/${file_name}',
    },
    'do': lambda name, root, gadget: installer.InstallCppTools( name,
                                                                root,
                                                                gadget ),
    'all': {
      'version': '1.22.9',
      "adapters": {
        "vscode-cpptools": {
          "name": "cppdbg",
          "command": [
            "${gadgetDir}/vscode-cpptools/debugAdapters/bin/OpenDebugAD7"
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
      'file_name': 'cpptools-linux-x64.vsix',
      'checksum':
        '44c01555dc398149e174a31569aeae0ef2d182437bf175c7c25ad5f6a76fe6c1',
    },
    'linux_arm64': {
      'file_name': 'cpptools-linux-aarch64.vsix',
      'checksum':
        'c9a0b23ae4898e3c291fd2bffb41a14bc06fd3af2e07b8a17ffe9aef4c80574e',
    },
    'linux_armv7': {
      'file_name': 'cpptools-linux-armhf.vsix',
      'checksum':
        'c644bbdd56abb37ecf455ca64cb70f07d17399bda2f2a4e20c9b57e40a11ef0f',
    },
    'macos': {
      'file_name': 'cpptools-osx.vsix',
      'checksum':
        'bda9204b6d75996a84a2cd9829736f99c8b4747b41544a4bd569b888fa635249',
    },
    'macos_arm64': {
      'file_name': 'cpptools-osx-arm64.vsix',
      'checksum':
        'fa836b1ff3311e8303af612b6597c5c81e3a8573dfbf28d0576e811de97e5427',
    },
    'windows_XX': {
      'file_name': 'cpptools-win32.vsix',
      'checksum':
        '2c0004c3c828030df1d4c53f4e421d2e03d86b47f96fa1efe0691e88f4d56dd6',
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
    'windows_arm64': {
      'file_name': 'cpptools-win-arm64.vsix',
      'checksum':
        '2ba1f66bdb53935db10898477150ffdfab1c5d73bc0f0649e52377b95fafacc1',
    },
    "windows": {
        "file_name": "cpptools-windows-x64.vsix",
        "checksum": "8cfeab3a2693b736fefc17e5ce6ec63cf0e955352c2d1f57c2dea4b9d38cec9b",
    },
  },
  'debugpy': {
    'language': 'python',
    'download': {
      'url': 'https://github.com/microsoft/debugpy/archive/${file_name}'
    },
    'all': {
      'version': '1.8.11',
      'file_name': 'v1.8.11.zip',
      'checksum':
        ''
    },
    'do': lambda name, root, gadget: installer.InstallDebugpy( name,
                                                               root,
                                                               gadget ),
    'adapters': {
      'debugpy': {
        "command": [
          sys.executable,
          "${gadgetDir}/debugpy/build/lib/debugpy/adapter"
        ],
        "name": "debugpy",
        "configuration": {
          "python": sys.executable
        },
        'custom_handler': 'vimspector.custom.python.Debugpy'
      }
    },
  },
  'debugpy-python2': {
    'language': 'python2',
    'enabled': False,
    'download': {
      'url': 'https://github.com/microsoft/debugpy/archive/${file_name}'
    },
    'all': {
      # Don't update - this is the last version that supports python2
      'version': '1.5.1',
      'file_name': 'v1.5.1.zip',
      'checksum':
        '00cf8235b88880bc2d8f59e8f6585208a43e6f14017cdf11d3a0bb2aeb4fff79'
    },
    'do': lambda name, root, gadget: installer.InstallDebugpy( name,
                                                               root,
                                                               gadget ),
    'adapters': {
      'debugpy-python2': {
        "command": [
          sys.executable,
          "${gadgetDir}/debugpy-python2/build/lib/debugpy/adapter"
        ],
        "name": "debugpy",
        "configuration": {
          "python": sys.executable
        },
        'custom_handler': 'vimspector.custom.python.Debugpy'
      }
    },
  },
  'vscode-java-debug': {
    'language': 'java',
    'enabled': False,
    'download': {
      'url': 'https://github.com/microsoft/vscode-java-debug/releases/download/'
             '${version}/${file_name}',
    },
    'all': {
      'version': '0.52.0',
      'file_name': 'vscjava.vscode-java-debug-0.52.0.vsix',
      'checksum':
        '5a3273dfafb96712822e3ebc4b7d018b30c816cb8888a5c291d12bc6aedd19c5',
    },
    'adapters': {
      "vscode-java": {
        "name": "vscode-java",
        "port": "${DAPPort}",
        "configuration": {
          "cwd": "${workspaceRoot}"
        },
        'custom_handler': 'vimspector.custom.java.JavaDebugAdapter'
      }
    },
  },
  'java-language-server': {
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
      # Don't update - deprecated
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
  },
  'tclpro': {
    'language': 'tcl',
    'repo': {
      'url': 'https://github.com/puremourning/TclProDebug',
      'ref': 'master'
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
  },
  'netcoredbg': {
    'language': [ 'csharp', 'fsharp', 'vbnet' ],
    'enabled': False,
    'download': {
      'url': ( 'https://github.com/Samsung/netcoredbg/releases/download/'
               '${version}/${file_name}' ),
      'format': 'tar',
    },
    'all': {
      'version': '2.2.3-992'
    },
    'macos': {
      'file_name': 'netcoredbg-osx-amd64.tar.gz',
      'checksum':
        '1e32d77e77978b6886b6c56251ca9fc730af4fda72d819e676e6591bd978b37f',
    },
    'linux': {
      'file_name': 'netcoredbg-linux-amd64.tar.gz',
      'checksum':
        '1d168670a0ce299622c89f94908d8f79fbe0f2c81294785eec16fe64c448e466',
    },
    'linux_arm64': {
      'file_name': 'netcoredbg-linux-arm64.tar.gz',
      'checksum':
        'f9909bff95311e95fa4dae145683663d9b76fe8b0140ad700fdd7e149043810b',
    },
    'windows': {
      'file_name': 'netcoredbg-win64.zip',
      'checksum':
        '6eeaff24a72e96ceb694e8897ff4f0f2327e7ed76ca33eff5360807d93adb8ce',
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
  },
  'vscode-bash-debug': {
    'language': 'bash',
    'download': {
      'url': 'https://github.com/rogalmic/vscode-bash-debug/releases/'
             'download/${release}/${file_name}',
    },
    'all': {
      'file_name': 'bash-debug-0.3.9.vsix',
      'version': '0.3.9',
      'release': 'untagged-438733f35feb8659d939',
      'checksum':
        '7605265eb3de643f0817d9b1870eec0d36a7de5a0d50628edb59937f1515fabc',
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
          "argsString": "",
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
  },
  'delve': {
    'language': 'go',
    'do': lambda name, root, gadget: installer.InstallDelve( name,
                                                             root,
                                                             gadget ),
    'all': {
      'path': 'github.com/go-delve/delve/cmd/dlv',
      'version': '1.23.1',
    },
    'adapters': {
      "delve": {
        "variables": {
          "port": "${unusedLocalPort}",
          "dlvFlags": "",
          "listenOn": "127.0.0.1",
        },
        "command": [
          "${gadgetDir}/delve/bin/dlv",
          "dap",
          "--listen",
          "${listenOn}:${port}",
          "*${dlvFlags}",
        ],
        "tty": True, # because delve is a special snowflake and uses its own
                     # controlling tty for the debuggee
        "port": "${port}"
      }
    }
  },
  'vscode-go': {
    'language': 'go',
    'download': {
      'url': 'https://github.com/golang/vscode-go/releases/download/'
             'v${version}/${file_name}'
    },
    'all': {
      # Don't update - deprecated
      'version': '0.30.0',
      'file_name': 'go-0.30.0.vsix',
      'checksum':
        '',
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
          # If the delva adapter is also installed, use that by default.
          "dlvToolPath": "${gadgetDir}/delve/bin/dlv"
        }
      },
    },
  },
  'vscode-php-debug': {
    'language': 'php',
    'enabled': False,
    'download': {
      'url':
        'https://github.com/xdebug/vscode-php-debug/releases/download/'
        '${version}/${file_name}',
    },
    'all': {
      'version': 'v1.33.0',
      'file_name': 'php-debug-1.33.0.vsix',
      'checksum':
        'e31252c1bf5d648cea7c6a28a3c7b51a0b886a66f044b5e17118402f14095b76',
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
  },
  'vscode-js-debug': {
    'language': 'node',
    'enabled': False,
    'download': {
      'url': 'https://github.com/microsoft/vscode-js-debug/releases/download/'
             '${version}/${file_name}',
      'format': 'tar',
    },
    'all': {
      'file_name': 'js-debug-dap-v1.82.0.tar.gz',
      'version': 'v1.82.0',
      'checksum':
        '7295e743c718e3b24b7a6cd838d1bdd448c159d8baaf821693b9f265fc477118',
    },
    'model': 'simple',
    'adapters': {
      'js-debug': {
        'variables': {
          'port': '${unusedLocalPort}'
        },
        'custom_handler': 'vimspector.custom.js.JsDebug',
        'command': [
          'node',
          '${gadgetDir}/vscode-js-debug/js-debug/src/dapDebugServer.js',
          '${port}',
          '127.0.0.1'
        ],
        'port': '${port}',
        'host': '127.0.0.1',
        'configuration': {
          'type': 'pwa-node',
          'console': 'integratedTerminal'
        }
      },
    },
  },
  'vscode-firefox-debug': {
    'language': 'firefox',
    'enabled': False,
    'download': {
      'url': 'https://marketplace.visualstudio.com/_apis/public/gallery'
              '/publishers/firefox-devtools/vsextensions/'
              'vscode-firefox-debug/${version}/vspackage',
      'target': 'firefox-devtools.vscode-firefox-debug-${version}.vsix.gz',
      'format': 'zip.gz',
    },
    'all': {
      'version': '2.9.8',
      'file_name': 'firefox-devtools.vscode-firefox-debug-2.9.8.vsix',
      'checksum':
        'f36038b14e87e1a4dae29a1c31b462b630d793d95c0cf40ed350d0511e9e1606'
    },
    'adapters': {
      'firefox': {
        'name': 'debugger-for-firefox',
        'type': 'firefox',
        'command': [
          'node',
          '${gadgetDir}/vscode-firefox-debug/dist/adapter.bundle.js'
        ],
      },
    },
  },
  'debugger-for-chrome': {
    'language': 'chrome',
    'enabled': False,
    'download': {
      'url': 'https://marketplace.visualstudio.com/_apis/public/gallery/'
             'publishers/msjsdiag/vsextensions/'
             'debugger-for-chrome/${version}/vspackage',
      'target': 'msjsdiag.debugger-for-chrome-${version}.vsix.gz',
      'format': 'zip.gz',
    },
    'all': {
      'version': '4.13.0',
      'file_name': 'msjsdiag.debugger-for-chrome-4.13.0.vsix',
      'checksum':
        '7c6c7a84db2323f86d52b3683d5bfe4a206074a58f791d271845407859d49c5b'
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
  },
  'CodeLLDB': {
    'language': [ 'c', 'cpp', 'rust' ],
    'enabled': True,
    'download': {
      'url': 'https://github.com/vadimcn/vscode-lldb/releases/download/'
             '${version}/${file_name}',
    },
    'all': {
      'version': 'v1.11.0',
    },
    'macos': {
      'file_name': 'codelldb-darwin-x64.vsix',
      'checksum':
        '5be44ccc6d1e44a0cad5c67458a6968c0c6baf091093005221d467f10dd68dc6',
      'make_executable': [
        'adapter/codelldb',
        'lldb/bin/debugserver',
        'lldb/bin/lldb',
        'lldb/bin/lldb-argdumper',
      ],
    },
    'macos_arm64': {
      'file_name': 'codelldb-darwin-arm64.vsix',
      'checksum':
        '6634c094def2463d38b7b220bcebb49bac81391ef2e9988c4d41e88a996d726c',
    },
    'linux': {
      'file_name': 'codelldb-linux-x64.vsix',
      'checksum':
        'b857287f70a18a4fc2d7563aa9fdbcfa9cb2b37d5666fc78394fc8131ee335e2',
      'make_executable': [
        'adapter/codelldb',
        'lldb/bin/lldb',
        'lldb/bin/lldb-server',
        'lldb/bin/lldb-argdumper',
      ],
    },
    'linux_arm64': {
      'file_name': 'codelldb-linux-arm64.vsix',
      'checksum':
        'ebbd358dddc1538384cdfb94823da85d13a7a3a4c3eac466de8bb5394f81386a',
    },
    'linux_armv7': {
      'file_name': 'codelldb-linux-armhf.vsix',
      'checksum':
        'a22f1b38a94a94cb2cb814399de9da153cd2ddb2539b97353f05b60668fe0e9f',
    },
    'windows': {
      'file_name': 'codelldb-win32-x64.vsix',
      'checksum':
        '375807832e2e9e41dd66f000200d4a55978977f3f10ad9799286f1f9fbe017e6',
      'make_executable': []
    },
    'adapters': {
      'CodeLLDB': {
        'name': 'CodeLLDB',
        'type': 'CodeLLDB',
        "command": [
          "${gadgetDir}/CodeLLDB/adapter/codelldb",
        ],
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
  },
  'local-lua-debugger-vscode': {
    'language': 'lua',
    'enabled': True,
    'repo': {
      'url': 'https://github.com/tomblind/local-lua-debugger-vscode.git',
      'ref': 'release-${version}'
    },
    'all': {
      'version': '0.3.3',
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
  },
}
