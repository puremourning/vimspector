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
      'version': '1.11.5',
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
      'file_name': 'cpptools-linux.vsix',
      'checksum':
        'f9e5fbd3e2b20f10c538257ac9dd30665abf53cfaaea403d08eb7a4739b79456',
    },
    'linux_arm64': {
      'file_name': 'cpptools-linux-aarch64.vsix',
      'checksum':
        'feeeddafc3d162039a842a9b7107c33b32b36f8e85b7e13ab918ea2aada48f8f',
    },
    'macos': {
      'file_name': 'cpptools-osx.vsix',
      'checksum':
        'a61abe2bec1016300a8508aee57108d804540f3b4c798dd9be4b87296e256640',
    },
    'macos_arm64': {
      'file_name': 'cpptools-osx-arm64.vsix',
      'checksum':
        '943f68c0082c2ed46f2e9466c71062645a57f9ef448c9d849da60cd5b7a4b495',
    },
    'windows': {
      'file_name': 'cpptools-win32.vsix',
      'checksum':
        '9e9eb748510d481ae388db0393a9a42a04014dde2f9ada87518764763f8455cd',
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
        'cd4ec2f378521c761908574a4e1474bc3b8babaa8b734126e448001fcaaaa58d',
    },
  },
  'debugpy': {
    'language': 'python',
    'download': {
      'url': 'https://github.com/microsoft/debugpy/archive/${file_name}'
    },
    'all': {
      'version': '1.6.3',
      'file_name': 'v1.6.3.zip',
      'checksum':
        '3bc37b5bc82e50efab52d6d2ea4a1ffa5fd3f100ab725d7ff163cd0a7ee9cb40'
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
          "python": sys.executable,
          # Don't debug into subprocesses, as this leads to problems (vimspector
          # doesn't support the custom messages)
          # https://github.com/puremourning/vimspector/issues/141
          "subProcess": False,
        }
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
          "${gadgetDir}/debugpy/build/lib/debugpy/adapter"
        ],
        "name": "debugpy",
        "configuration": {
          "python": sys.executable,
          # Don't debug into subprocesses, as this leads to problems (vimspector
          # doesn't support the custom messages)
          # https://github.com/puremourning/vimspector/issues/141
          "subProcess": False,
        }
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
      'version': '0.43.0',
      'file_name': 'vscjava.vscode-java-debug-0.43.0.vsix',
      'checksum':
        '5df389d248b0b988fefa558d9f0f43a93a3c053b9992a3e13057b2bc465ba7f6',
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
      'version': '2.0.0-915'
    },
    'macos': {
      'file_name': 'netcoredbg-osx-amd64.tar.gz',
      'checksum':
        '466b531e99661546a243bd3c35ac0adfd928acbb53e025f9967e48835cc936dc',
    },
    'linux': {
      'file_name': 'netcoredbg-linux-amd64.tar.gz',
      'checksum':
        '82db34e2e8b5105128ad6b9585ba8830acfc3f33a485dac3b1219bd777fa7b6e',
    },
    'linux_arm64': {
      'file_name': 'netcoredbg-linux-arm64.tar.gz',
      'checksum':
        '3073b2e8820eae153c023432787080a785e4f2a3c792ed6f9fd3b738129774ac',
    },
    'windows': {
      'file_name': 'netcoredbg-win64.zip',
      'checksum':
        '024f342fb5390d4d5c01c815b25911ab426f176be3d4c6e8c81ee2626beb24e2',
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
      'version': '1.9.0',
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
      'version': 'v1.27.0',
      'file_name': 'php-debug-1.27.0.vsix',
      'checksum':
        'ac3997b91017e560336fa98da17a1a3578fb47d5121f93e0b286c2dffb5ff981',
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
  'vscode-node-debug2': {
    'language': 'node',
    'enabled': False,
    'repo': {
      'url': 'https://github.com/microsoft/vscode-node-debug2',
      'ref': 'v1.43.0'
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
      'version': 'v1.7.4',
    },
    'macos': {
      'file_name': 'codelldb-x86_64-darwin.vsix',
      'checksum':
        'f619449a4a151b0944c2c4f194de0b50e6a43e7273768eaf322ccde9a9f1e539',
      'make_executable': [
        'adapter/codelldb',
        'lldb/bin/debugserver',
        'lldb/bin/lldb',
        'lldb/bin/lldb-argdumper',
      ],
    },
    'macos_arm64': {
      'file_name': 'codelldb-aarch64-darwin.vsix',
      'checksum':
        'eb51069b2b68ec073a739e7b8149aa1511b643f1ccb20a7026d086166e06a270',
    },
    'linux': {
      'file_name': 'codelldb-x86_64-linux.vsix',
      'checksum':
        '9f489edbd15aa0ef4ee6386d1cb40f2c7cab703f347ebc7c3f4855fec6e916d2',
      'make_executable': [
        'adapter/codelldb',
        'lldb/bin/lldb',
        'lldb/bin/lldb-server',
        'lldb/bin/lldb-argdumper',
      ],
    },
    'linux_arm64': {
      'file_name': 'codelldb-aarch64-linux.vsix',
      'checksum':
        '64d2586b4b84868ba5d59679d0de5cd74f8c5e04c170abd0da2413034a280528',
    },
    'windows': {
      'file_name': 'codelldb-x86_64-windows.vsix',
      'checksum':
        '7664f3054354f388eb94c3eae803f60ce2c87df7f36e55d44f84e99ec67a7861',
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
