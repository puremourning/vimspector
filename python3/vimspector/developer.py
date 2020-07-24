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


import sys
import os

from vimspector import install, utils, installer


def SetUpDebugpy( wait=False, port=5678 ):
  sys.path.insert(
    1,
    os.path.join( install.GetGadgetDir( utils.GetVimspectorBase() ),
                  'debugpy',
                  'build',
                  'lib' ) )
  import debugpy

  exe = sys.executable
  try:
    # debugpy uses sys.executable (which is `vim`, so we hack it)
    sys.executable = installer.PathToAnyWorkingPython3()
    debugpy.listen( port )
  finally:
    sys.executable = exe

  if wait:
    debugpy.wait_for_client()
