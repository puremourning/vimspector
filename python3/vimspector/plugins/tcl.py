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
from vimspector import gadgets, installer, install


def InstallTclProDebug( name, root, gadget ):
  configure = [ 'sh', './configure' ]

  if install.GetOS() == 'macos':
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
    installer.CheckCall( configure )
    installer.CheckCall( [ 'make' ] )

  installer.MakeSymlink( name, root )


gadgets.RegisterGadget( 'tclpro', {
  'language': 'tcl',
  'repo': {
    'url': 'https://github.com/puremourning/TclProDebug',
    'ref': 'v1.0.0'
  },
  'do': lambda name, root, gadget: InstallTclProDebug( name, root, gadget ),
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
} )
