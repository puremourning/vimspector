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
      'version': '1.34.4',
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
        'a20e25a83228d7854a5623c49f00c33737782bfdde874feff417fe2d9b52c002',
    },
    'linux_arm64': {
      'file_name': 'cpptools-linux-arm64.vsix',
      'checksum':
        '9b69e2e8f9e9b4fbcda4faf342f7562a4b9471ef6106f00f9716d808a8117558',
    },
    'linux_armv7': {
      'file_name': 'cpptools-linux-arm32.vsix',
      'checksum':
        '239fea8d96e8fe9bd7ab1179e0a094d3aead792c9fcc3d78ed70fac14412d87e',
    },
    'macos': {
      'file_name': 'cpptools-macOS-x64.vsix',
      'checksum':
        '292d4b547f2d75449d8c93f345b682e4d9eb226f7fc272b0a6799f4d98c67c1c',
    },
    'macos_arm64': {
      'file_name': 'cpptools-macOS-arm64.vsix',
      'checksum':
        'ca2360ae4ebeaa74aa013c7de03d78385952b488079c5dcd5e2c0bfc063d62ea',
    },
    'windows': {
      'file_name': 'cpptools-windows-x64.vsix',
      'checksum':
        '6e199cda39c0ad14cce93eb02fb3d95ec5b7661cef7744b1c04f73320c77f96e',
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
        '5bfc839eaa89f94831869e31cdd546fb61e4f4b807e0f052acbbd7755bad96d6',
    },
  },
  'debugpy': {
    'language': 'python',
    'download': {
      'url': 'https://github.com/microsoft/debugpy/archive/${file_name}'
    },
    'all': {
      'version': '1.8.22',
      'file_name': 'v1.8.22.zip',
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
      'version': '1.27.2',
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
      'version': 'v1.12.3',
    },
    'linux': {
      'file_name': 'codelldb-linux-x64.vsix',
      'checksum':
        '1cd7f386598022b51a5b93b9ffa23e812b23f519cfe1833384ec4bef4bfd1be1',
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
        '0887f67d440554617894266f80706b700907c36b95e6e49d23b95a0e05318101',
    },
    'linux_armv7': {
      'file_name': 'codelldb-linux-armhf.vsix',
      'checksum':
        '20294f0ea876a73c662bb09b1814551a859dc77156564b62c75acf1088ecaf30',
    },
    'macos': {
      'file_name': 'codelldb-darwin-x64.vsix',
      'checksum':
        'e25cc716b94c62c07fec268ff2785d2b797245b160502baef8b9c970a0c4d8e8',
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
        '2f114a990e1b368dd1dbd33c80c0e719767af2d228391ec0df0571c957f9ac91',
    },
    'windows': {
      'file_name': 'codelldb-win32-x64.vsix',
      'checksum':
        'a916e509308dac817732f63ca604a8b93ed29cd16f38a2fa9f0b64ed58e8f51a',
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
