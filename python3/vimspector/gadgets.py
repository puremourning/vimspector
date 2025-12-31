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


VSCODE_EXTENSION_URL = (
  'https://marketplace.visualstudio.com/_apis/public/gallery'
  '/publishers/${publisher}/vsextensions'
  '/${extension}/${version}/vspackage'
)


class VSCodeTarget:
  LINUX_X64 = 'linux-x64'
  LINUX_ARM64 = 'linux-arm64'
  LINUX_ARMV7 = 'linux-armhf'
  MACOS_X64 = 'darwin-x64'
  MACOS_ARM64 = 'darwin-arm64'
  WINDOWS_X64 = 'win32-x64'
  WINDOWS_ARM64 = 'win32-arm64'


def VSCodeExtensionURL( target ):
  return VSCODE_EXTENSION_URL + f'?targetPlatform={target}'


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
      'version': '1.29.3',
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
        '86f205fa618982aadee1638e87cbc923db478cb9bb06ba20984755cad7674184',
    },
    'linux_arm64': {
      'file_name': 'cpptools-linux-arm64.vsix',
      'checksum':
        '7453a551e8428b0f256733b1ede37afdee77214707866af3c33567b1078306ad',
    },
    'linux_armv7': {
      'file_name': 'cpptools-linux-arm32.vsix',
      'checksum':
        '7db91fdde794d6e13d608ca58922fa91837301b8536edca540e2e32c90df68ae',
    },
    'macos': {
      'file_name': 'cpptools-macOS-x64.vsix',
      'checksum':
        '02be992d129a391357bdcef134baffb172ef3f51c8dc3b94b5ad0df212f8f0d6',
    },
    'macos_arm64': {
      'file_name': 'cpptools-macOS-arm64.vsix',
      'checksum':
        '768b4ea2c6c9bbf6e87ee5931f2f007106d6ce28c3152b551484bb6b73cdedce',
    },
    'windows': {
      'file_name': 'cpptools-windows-x64.vsix',
      'checksum':
        '2da32536c180b946b59d94c7269211fd2f7a9e243e854239c7f69d2299c1858a',
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
      'file_name': 'cpptools-windows-arm64.vsix',
      'checksum':
        '4d6fe48036a0841af61429f7a6e85fb4c1d47856ca4d95f08f609136de74a874',
    },
  },
  'debugpy': {
    'language': 'python',
    'download': {
      'url': 'https://github.com/microsoft/debugpy/archive/${file_name}'
    },
    'all': {
      'version': '1.8.19',
      'file_name': 'v1.8.19.zip',
      'checksum':
        # Note: Don't checksum this because GitHub archves are not stable.
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
      'url': VSCODE_EXTENSION_URL,
      'file_name': 'vscjava.vscode-java-debug-${version}.vsix',
      'format': 'zip.gz',
    },
    'all': {
      'publisher': 'vscjava',
      'extension': 'vscode-java-debug',
      'version': '0.58.2025121609', # '0.58.4',
      'file_name': 'vscjava.vscode-java-debug-0.58.4.vsix',
      'checksum':
        '6e28945b136ed28435015cd6144e3dd202ae4c338bbcafebd83a0f112f0bead2',
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
      'version': '3.1.3-1062'
    },
    'linux': {
      'file_name': 'netcoredbg-linux-amd64.tar.gz',
      'checksum':
        '3814341c028c81ff7eea03ac316ad92e9ad7d705d2a00e3e3df269cdc241c763',
    },
    'linux_arm64': {
      'file_name': 'netcoredbg-linux-arm64.tar.gz',
      'checksum':
        'fc9efb691a53932a7fac4b9f67af68ad0c2a4cbe59cb2c1a3c44c64959df2ba4',
    },
    'macos': {
      'file_name': 'netcoredbg-osx-amd64.tar.gz',
      'checksum':
        '49459b066836b6a452f418501d7ecab57bcd7e60d8464faac21ff70b496b8634',
    },
    'windows': {
      'file_name': 'netcoredbg-win64.zip',
      'checksum':
        'c67ae052e0bcb9ce37000f261e2d397a0d5b6615cafe30c868239a78598dfb37',
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
      'version': '1.26.0',
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
  'vscode-php-debug': {
    'language': 'php',
    'enabled': False,
    'download': {
      'url':
        'https://github.com/xdebug/vscode-php-debug/releases/download/'
        '${version}/${file_name}',
    },
    'all': {
      'version': 'v1.39.1',
      'file_name': 'php-debug-1.39.1.vsix',
      'checksum':
        'f618e6539fe3911bba7dda026f71fbb4cf26ea2b59d180816c1ac9f079cd3afd',
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
      'file_name': 'js-debug-dap-v1.105.0.tar.gz',
      'version': 'v1.105.0',
      'checksum':
        '5c3ccc47ee77d82ba796787de452e670478d331719d9332abd49bbde8e5d479c',
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
    # Currently not updating as seems rarely used and does not provide a GitHub
    # release; having to unpack vsix is a pain.
    'language': 'firefox',
    'enabled': False,
    'download': {
      'url': VSCODE_EXTENSION_URL,
      'target': 'firefox-devtools.vscode-firefox-debug-${version}.vsix.gz',
      'format': 'zip.gz',
    },
    'all': {
      'version': '2.9.8',
      'publisher': 'firefox-devtools',
      'extension': 'vscode-firefox-debug',
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
    # Not updating as marked deprecated by Microsoft
    'language': 'chrome',
    'enabled': False,
    'download': {
      'url': VSCODE_EXTENSION_URL,
      'target': 'msjsdiag.debugger-for-chrome-${version}.vsix.gz',
      'format': 'zip.gz',
    },
    'all': {
      'publisher': 'msjsdiag',
      'extension': 'debugger-for-chrome',
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
      'version': 'v1.12.1',
    },
    'linux': {
      'file_name': 'codelldb-linux-x64.vsix',
      'checksum':
        '5d3cdacc4c6f338468ddfc129d740fafb9d856358831810df717d05fd309600a',
      'make_executable': [
        'adapter/codelldb',
        'bin/codelldb-launch',
        'lldb/bin/lldb',
        'lldb/bin/lldb-server',
        'lldb/bin/lldb-argdumper',
      ],
    },
    'linux_arm64': {
      'file_name': 'codelldb-linux-arm64.vsix',
      'checksum':
        'eddb73528c8fe843b24e71a15a60a21367c2b001c1b55af91cec2dcf5dc8cf73',
    },
    'linux_armv7': {
      'file_name': 'codelldb-linux-armhf.vsix',
      'checksum':
        '168ee77e5a602d2449b773967b61272a3de48f44814ac1488e5c05fc974dd6e3',
    },
    'macos': {
      'file_name': 'codelldb-darwin-x64.vsix',
      'checksum':
        '667739305c94dc9a453d30d60e2933b9565bb57a5e2f9de6d524086d2592b039',
      'make_executable': [
        'adapter/codelldb',
        'bin/codelldb-launch',
        'lldb/bin/lldb',
        'lldb/bin/lldb-server',
        'lldb/bin/lldb-argdumper',
      ],
    },
    'macos_arm64': {
      'file_name': 'codelldb-darwin-arm64.vsix',
      'checksum':
        '13297074f9eb4d96387a631a3d844e488d24f68b0354b8b91805118456e89695',
    },
    'windows': {
      'file_name': 'codelldb-win32-x64.vsix',
      'checksum':
        'b87bcc9851a2e502e2c696d0d3b1c4ca5ce2b421f07fceb350f155f77df050b6',
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
