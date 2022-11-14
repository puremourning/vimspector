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

import platform
import os
from vimspector.core_utils import memoize


@memoize
def GetOS():
  if platform.system() == 'Darwin':
    return 'macos'
  elif platform.system() == 'Windows':
    return 'windows'
  else:
    return 'linux'


@memoize
def GetPlatform():
  machine = platform.machine()

  try:
    from vimspector.vendor import cpuinfo
  except Exception:
    return 'unknown'

  machine_info = cpuinfo._parse_arch( machine )

  machine_map = {
    ( 'X86_64', 64 ): 'x86_64',
    ( 'X86_32', 32 ): 'x86',
    ( 'ARM_8', 64 ): 'arm64',
    ( 'ARM_7', 32 ): 'armv7'
  }

  try:
    return machine_map[ machine_info ]
  except KeyError:
    return 'unknown'


@memoize
def GetOSPlatform():
  return GetOS() + '_' + GetPlatform()


def mkdirs( p ):
  try:
    os.makedirs( p )
  except FileExistsError:
    pass


def MakeInstallDirs( vimspector_base ):
  mkdirs( GetGadgetConfigDir( vimspector_base ) )
  mkdirs( GetConfigDirForFiletype( vimspector_base, '_all' ) )


@memoize
def GetGadgetDir( vimspector_base ):
  return os.path.join( os.path.abspath( vimspector_base ), 'gadgets', GetOS() )


def GetManifestFile( vimspector_base ):
  return os.path.join( GetGadgetDir( vimspector_base ),
                       '.gadgets.manifest.json' )


def GetGadgetConfigFile( vimspector_base ):
  return os.path.join( GetGadgetDir( vimspector_base ), '.gadgets.json' )


def GetGadgetConfigDir( vimspector_base ):
  return os.path.join( GetGadgetDir( vimspector_base ), '.gadgets.d' )


def GetConfigDirForFiletype( vimspector_base, filetype ):
  if not filetype:
    filetype = 'default'

  return os.path.join( os.path.abspath( vimspector_base ),
                       'configurations',
                       GetOS(),
                       filetype )
