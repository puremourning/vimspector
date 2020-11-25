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


from vimspector import gadgets


gadgets.RegisterGadget( 'debugger-for-chrome', {
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
} )
