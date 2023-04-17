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
      'version': '1.14.5',
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
        '68348700fa21cad910c9a7fdee21a7fbf1121fb9f8eb491c0359ca45e09ccae4',
    },
    'linux_arm64': {
      'file_name': 'cpptools-linux-aarch64.vsix',
      'checksum':
        'bea5b38d34eedcfc8072af8febc8ba2fc0426b80a9849971d2af9214bf70c69b',
    },
    'linux_armv7': {
      'file_name': 'cpptools-linux-armhf.vsix',
      'checksum':
        '8ee834bead728dfe64f344bd8e30e61bd29778286c5acc9406b6c4d6281b4ab6',
    },
    'macos': {
      'file_name': 'cpptools-osx.vsix',
      'checksum':
        '02435e6ea60b0257b238291fb759572da3b943cb4af93711ba6af3a32735a474',
    },
    'macos_arm64': {
      'file_name': 'cpptools-osx-arm64.vsix',
      'checksum':
        '5a6fecd27bbedfefeabf77ab4638159da60478f77e306b73887b82e98fabd037',
    },
    'windows': {
      'file_name': 'cpptools-win32.vsix',
      'checksum':
        'e8f9fdd47026c21fc2e7ad6df6c3fca9a524a0bb8cf7b5f4329959469800dc8c',
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
        '8822922d671fb0a35c186f6868b57862914c1605452e0a0146077a69cf8c9d79',
    },
  },
  'debugpy': {
    'language': 'python',
    'download': {
      'url': 'https://github.com/microsoft/debugpy/archive/${file_name}'
    },
    'all': {
      'version': '1.6.7',
      'file_name': 'v1.6.7.zip',
      'checksum':
        '59b441c3ddac3de9d47fd75a1766cf5636f09b281f907717c769149f86aa106e'
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
      'version': '2.2.0-974'
    },
    'macos': {
      'file_name': 'netcoredbg-osx-amd64.tar.gz',
      'checksum':
        '6991d00da35c55b31775eb4fe4bae3b931e2b3b2d326208ba2fefdba59114441',
    },
    'linux': {
      'file_name': 'netcoredbg-linux-amd64.tar.gz',
      'checksum':
        '439b92e4f6c39b5cde520e449c8062b67405dbe46db8e04c134ea2937bfa338e',
    },
    'linux_arm64': {
      'file_name': 'netcoredbg-linux-arm64.tar.gz',
      'checksum':
        '37aee82240d8bbbbc12971e44c8e762b783a92223f00521835ce6cb0512e64c3',
    },
    'windows': {
      'file_name': 'netcoredbg-win64.zip',
      'checksum':
        '11796043a7f6b0f1d47d26f46ed424606acf32bbf8aedae4a66a8073c9308deb',
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
      'version': '1.20.1',
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
  'vscode-js-debug': {
    'language': 'node',
    'enabled': False,
    'download': {
      'url': 'https://github.com/microsoft/vscode-js-debug/releases/download/'
             '${version}/${file_name}',
      'format': 'tar',
    },
    'all': {
      'file_name': 'js-debug-dap-v1.77.0.tar.gz',
      'version': 'v1.77.0',
      'checksum':
        '162460aa4086cef37573af7a97e6693bd309716e02ac6fbdff424cdd416f7a41',
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
  'vscode-node-debug2': {
    'language': 'node_legacy',
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
      'version': 'v1.9.0',
    },
    'macos': {
      'file_name': 'codelldb-x86_64-darwin.vsix',
      'checksum':
        '72e3a0a26dc43975723bc25ff2489aeb4bf3ca65a7112734b1ff6a76969e5bfe',
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
        'cbfd547761ecfb6ea643f7dfbea080afddefccb003623a0e954969f569efb9cf',
    },
    'linux': {
      'file_name': 'codelldb-x86_64-linux.vsix',
      'checksum':
        '27af4b0821fd1843b04d3fa0ea1ecfb202cda6b869b67205685a29079caa22b7',
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
        '879ac7cf1c6a7944f82c42ee8b8d3da79abf084d8539abba6551ac6b6bb5ce54',
    },
    'linux_armv7': {
      'file_name': 'codelldb-arm-linux.vsix',
      'checksum':
        '211a68f25a1e28323e2f3101cd89438888b1e4bc182988c40f6a7a4162f390b1',
    },
    'windows': {
      'file_name': 'codelldb-x86_64-windows.vsix',
      'checksum':
        'f961cdee239e78c789ea4e1e0929d055e1c7257ecad5f1fb1cc6f72ca3814791',
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
