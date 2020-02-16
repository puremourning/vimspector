#!/usr/bin/env python3

# vimspector - A multi-language debugging system for Vim
# Copyright 2019 Ben Jackson
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

if sys.version_info.major < 3:
  sys.exit( "You need to run this with python 3. Your version is " +
            '.'.join( map( str, sys.version_info[ :3 ] ) ) )

import argparse
import os
import string
import subprocess
import traceback
import json
import functools
import operator
import glob

# Include vimspector source, for utils
sys.path.insert( 1, os.path.join( os.path.dirname( __file__ ),
                                  'python3' ) )

from vimspector import install, installer

GADGETS = {
  'vscode-cpptools': {
    'language': 'c',
    'download': {
      'url': 'https://github.com/Microsoft/vscode-cpptools/releases/download/'
             '${version}/${file_name}',
    },
    'do': lambda name, root, gadget: InstallCppTools( name, root, gadget ),
    'all': {
      'version': '0.26.3',
    },
    'linux': {
      'file_name': 'cpptools-linux.vsix',
      'checksum':
        'd660367fbedd6acaffcc233c1d41ef280ff79aeba81846b86bf9bd97b4887379'
    },
    'macos': {
      'file_name': 'cpptools-osx.vsix',
      'checksum':
        'ca0793dd1dfd70757491da80cf04b2b15631048b572de2ebe3864f9eed96dff9',
    },
    'windows': {
      'file_name': 'cpptools-win32.vsix',
      'checksum': None,
    },
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
      },
    },
  },
  'vscode-python': {
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
  },
  'debugpy': {
    'language': 'python',
    'download': {
      'url': 'https://github.com/microsoft/debugpy/archive/${file_name}'
    },
    'all': {
      'version': '1.0.0b1',
      'file_name': 'v1.0.0b1.zip',
      'checksum':
        'eb26ac276213bcf26aaeadd7c3c284f7a20f43b63331822831a783dea558e60e'
    },
    'do': lambda name, root, gadget: InstallDebugpy( name, root, gadget ),
    'adapters': {
      'debugpy': {
        "command": [
          sys.executable,
          "${gadgetDir}/debugpy/build/lib/debugpy/adapter"
        ],
        "name": "debugpy",
        "configuration": {
          "python": sys.executable
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
      'version': '0.23.0',
      'file_name': 'vscode-java-debug-0.23.0.vsix',
      'checksum':
        'f98a35c8dd4f3079ecd9657b04f1edbfea04c364c0fbf7eee1285f942782710b',
    },
    'adapters': {
      "vscode-java": {
        "name": "vscode-java",
        "port": "ask",
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
      'ref': 'f5c56b7067661ce84e205765060224076569ae0e', # master 26/10/2019
    },
    'do': lambda name, root, gadget: InstallTclProDebug( name, root, gadget )
  },
  'netcoredbg': {
    'language': 'csharp',
    'enabled': False,
    'download': {
      'url': 'https://github.com/Samsung/netcoredbg/releases/download/latest/'
             '${file_name}',
      'format': 'tar',
    },
    'all': {
      'version': 'master'
    },
    'macos': {
      'file_name': 'netcoredbg-osx-master.tar.gz',
      'checksum':
        'c1dc6ed58c3f5b0473cfb4985a96552999360ceb9795e42d9c9be64af054f821',
    },
    'linux': {
      'file_name': 'netcoredbg-linux-master.tar.gz',
      'checksum': '',
    },
    'do': lambda name, root, gadget: installer.MakeSymlink(
      gadget_dir,
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
      },
    }
  },
  'vscode-mono-debug': {
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
      'version': '0.15.8',
      'checksum':
          '723eb2b621b99d65a24f215cb64b45f5fe694105613a900a03c859a62a810470',
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
      },
    }
  },
  'vscode-bash-debug': {
    'language': 'bash',
    'download': {
      'url': 'https://github.com/rogalmic/vscode-bash-debug/releases/'
             'download/${version}/${file_name}',
    },
    'all': {
      'file_name': 'bash-debug-0.3.6.vsix',
      'version': 'v0.3.6',
      'checksum':
        '502ee5732851fc4f309294fc296a291b1a114008a1fbcb232f3763be2b8d9c1f',
    },
    'do': lambda name, root, gadget: InstallBashDebug( name, root, gadget ),
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
  'vscode-go': {
    'language': 'go',
    'download': {
      'url': 'https://github.com/microsoft/vscode-go/releases/download/'
             '${version}/${file_name}'
    },
    'all': {
      'version': '0.11.4',
      'file_name': 'Go-0.11.4.vsix',
      'checksum':
        'ff7d7b944da5448974cb3a0086f4a2fd48e2086742d9c013d6964283d416027e'
    },
    'adapters': {
      'vscode-go': {
        'name': 'delve',
        'command': [
          'node',
          '${gadgetDir}/vscode-go/out/src/debugAdapter/goDebug.js'
        ],
      },
    },
  },
  'vscode-php-debug': {
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
  },
  'vscode-node-debug2': {
    'language': 'node',
    'enabled': False,
    'repo': {
      'url': 'https://github.com/microsoft/vscode-node-debug2',
      'ref': 'v1.42.0',
    },
    'do': lambda name, root, gadget: InstallNodeDebug( name, root, gadget ),
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
  'debugger-for-chrome': {
    'language': 'chrome',
    'enabled': False,
    'download': {
      'url': 'https://marketplace.visualstudio.com/_apis/public/gallery/'
             'publishers/msjsdiag/vsextensions/'
             'debugger-for-chrome/${version}/vspackage',
      'target': 'msjsdiag.debugger-for-chrome-4.12.0.vsix.gz',
      'format': 'zip.gz',
    },
    'all': {
      'version': '4.12.0',
      'file_name': 'msjsdiag.debugger-for-chrome-4.12.0.vsix',
      'checksum':
        '0df2fe96d059a002ebb0936b0003e6569e5a5c35260dc3791e1657d27d82ccf5'
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
}


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

  installer.MakeExtensionSymlink( vimspector_base, name, root )


def InstallBashDebug( name, root, gadget ):
  installer.MakeExecutable( os.path.join( root,
                                          'extension',
                                          'bashdb_dir',
                                          'bashdb' ) )
  installer.MakeExtensionSymlink( vimspector_base, name, root )


def InstallDebugpy( name, root, gadget ):
  wd = os.getcwd()
  root = os.path.join( root, 'debugpy-{}'.format( gadget[ 'version' ] ) )
  os.chdir( root )
  try:
    subprocess.check_call( [ sys.executable, 'setup.py', 'build' ] )
  finally:
    os.chdir( wd )

  installer.MakeSymlink( gadget_dir, name, root )


def InstallTclProDebug( name, root, gadget ):
  configure = [ './configure' ]

  if OS == 'macos':
    # Apple removed the headers from system frameworks because they are
    # determined to make life difficult. And the TCL configure scripts are super
    # old so don't know about this. So we do their job for them and try and find
    # a tclConfig.sh.
    #
    # NOTE however that in Apple's infinite wisdom, installing the "headers" in
    # the other location is actually broken because the paths in the
    # tclConfig.sh are pointing at the _old_ location. You actually do have to
    # run the package installation which puts the headers back in order to work.
    # This is why the below list is does not contain stuff from
    # /Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform
    #  '/Applications/Xcode.app/Contents/Developer/Platforms'
    #    '/MacOSX.platform/Developer/SDKs/MacOSX.sdk/System'
    #    '/Library/Frameworks/Tcl.framework',
    #  '/Applications/Xcode.app/Contents/Developer/Platforms'
    #    '/MacOSX.platform/Developer/SDKs/MacOSX.sdk/System'
    #    '/Library/Frameworks/Tcl.framework/Versions'
    #    '/Current',
    for p in [ '/usr/local/opt/tcl-tk/lib' ]:
      if os.path.exists( os.path.join( p, 'tclConfig.sh' ) ):
        configure.append( '--with-tcl=' + p )
        break


  with installer.CurrentWorkingDir( os.path.join( root, 'lib', 'tclparser' ) ):
    subprocess.check_call( configure )
    subprocess.check_call( [ 'make' ] )

  installer.MakeSymlink( gadget_dir, name, root )


def InstallNodeDebug( name, root, gadget ):
  node_version = subprocess.check_output( [ 'node', '--version' ],
                                          universal_newlines=True ).strip()
  print( "Node.js version: {}".format( node_version ) )
  if list( map( int, node_version[ 1: ].split( '.' ) ) ) >= [ 12, 0, 0 ]:
    print( "Can't install vscode-debug-node2:" )
    print( "Sorry, you appear to be running node 12 or later. That's not "
           "compatible with the build system for this extension, and as far as "
           "we know, there isn't a pre-built independent package." )
    print( "My advice is to install nvm, then do:" )
    print( "  $ nvm install --lts 10" )
    print( "  $ nvm use --lts 10" )
    print( "  $ ./install_gadget.py --enable-node ..." )
    raise RuntimeError( 'Invalid node environent for node debugger' )

  with installer.CurrentWorkingDir( root ):
    subprocess.check_call( [ 'npm', 'install' ] )
    subprocess.check_call( [ 'npm', 'run', 'build' ] )
  installer.MakeSymlink( gadget_dir, name, root )


def InstallGagdet( name, gadget, failed, all_adapters ):
  try:
    v = {}
    v.update( gadget.get( 'all', {} ) )
    v.update( gadget.get( OS, {} ) )

    if 'download' in gadget:
      if 'file_name' not in v:
        raise RuntimeError( "Unsupported OS {} for gadget {}".format( OS,
                                                                      name ) )

      destination = os.path.join( gadget_dir, 'download', name, v[ 'version' ] )

      url = string.Template( gadget[ 'download' ][ 'url' ] ).substitute( v )

      file_path = installer.DownloadFileTo(
        url,
        destination,
        file_name = gadget[ 'download' ].get( 'target' ),
        checksum = v.get( 'checksum' ),
        check_certificate = not args.no_check_certificate )

      root = os.path.join( destination, 'root' )
      installer.ExtractZipTo(
        file_path,
        root,
        format = gadget[ 'download' ].get( 'format', 'zip' ) )
    elif 'repo' in gadget:
      url = string.Template( gadget[ 'repo' ][ 'url' ] ).substitute( v )
      ref = string.Template( gadget[ 'repo' ][ 'ref' ] ).substitute( v )

      destination = os.path.join( gadget_dir, 'download', name )
      installer.CloneRepoTo( url, ref, destination )
      root = destination

    if 'do' in gadget:
      gadget[ 'do' ]( name, root, v )
    else:
      installer.MakeExtensionSymlink( vimspector_base, name, root )

    all_adapters.update( gadget.get( 'adapters', {} ) )

    print( "Done installing {}".format( name ) )
  except Exception as e:
    traceback.print_exc()
    failed.append( name )
    print( "FAILED installing {}: {}".format( name, e ) )


vimspector_base = os.path.dirname( __file__ )
OS = install.GetOS()
gadget_dir = install.GetGadgetDir( vimspector_base, OS )

print( 'OS = ' + OS )
print( 'gadget_dir = ' + gadget_dir )

parser = argparse.ArgumentParser(
  description = 'Install DAP Servers for use with Vimspector.',
  epilog =
    """
    If you're not sure, normally --all is enough to get started.

    Custom server definitions can be defined in JSON files, allowing
    installation of arbitrary servers packaged in one of the ways that this
    installer understands.

    The format of the file can be found on the Vimspector reference guide:
    https://puremourning.github.io/vimspector
    """
)
parser.add_argument( '--all',
                     action = 'store_true',
                     help = 'Enable all supported completers' )

parser.add_argument( '--force-all',
                     action = 'store_true',
                     help = 'Enable all unsupported completers' )

parser.add_argument( '--no-gadget-config',
                     action = 'store_true',
                     help = "Don't write the .gagets.json, just install" )

parser.add_argument( '--enable-custom',
                     dest='custom_gadget_file',
                     action='append',
                     nargs='*',
                     default = [],
                     help = 'Read custom gadget from supplied file. This '
                            'can be supplied multiple times and each time '
                            'multiple files can be passed.' )

done_languages = set()
for name, gadget in GADGETS.items():
  lang = gadget[ 'language' ]
  if lang in done_languages:
    continue

  done_languages.add( lang )
  if not gadget.get( 'enabled', True ):
    parser.add_argument(
      '--force-enable-' + lang,
      action = 'store_true',
      help = 'Install the unsupported {} debug adapter for {} support'.format(
        name,
        lang ) )
    continue

  parser.add_argument(
    '--enable-' + lang,
    action = 'store_true',
    help = 'Install the {} debug adapter for {} support'.format(
      name,
      lang ) )

  parser.add_argument(
    '--disable-' + lang,
    action = 'store_true',
    help = "Don't install the {} debug adapter for {} support "
           '(when supplying --all)'.format( name, lang ) )

parser.add_argument(
    "--no-check-certificate",
    action = "store_true",
    help = "Do not verify SSL certificates for file downloads."
)

args = parser.parse_args()

if args.force_all and not args.all:
  args.all = True

CUSTOM_GADGETS = {}
custom_files = glob.glob( os.path.join( vimspector_base,
                                        'gadgets',
                                        'custom',
                                        '*.json' ) )
for custom_file_name in functools.reduce( operator.add,
                                          args.custom_gadget_file,
                                          custom_files ):
  with open( custom_file_name, 'r' ) as custom_file:
    CUSTOM_GADGETS.update( json.load( custom_file ) )


failed = []
all_adapters = {}
for name, gadget in GADGETS.items():
  if not gadget.get( 'enabled', True ):
    if ( not args.force_all
         and not getattr( args, 'force_enable_' + gadget[ 'language' ] ) ):
      continue
  else:
    if not args.all and not getattr( args, 'enable_' + gadget[ 'language' ] ):
      continue
    if getattr( args, 'disable_' + gadget[ 'language' ] ):
      continue

  InstallGagdet( name,
                 gadget,
                 failed,
                 all_adapters )


for name, gadget in CUSTOM_GADGETS.items():
  InstallGagdet( name, gadget, failed, all_adapters )

adapter_config = json.dumps ( { 'adapters': all_adapters },
                              indent=2,
                              sort_keys=True )

if args.no_gadget_config:
  print( "" )
  print( "Would write the following gadgets: " )
  print( adapter_config )
else:
  with open( install.GetGadgetConfigFile( vimspector_base ), 'w' ) as f:
    f.write( adapter_config )

if failed:
  raise RuntimeError( 'Failed to install gadgets: {}'.format(
    ','.join( failed ) ) )
