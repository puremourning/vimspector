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


gadgets.RegisterGadget( 'vscode-php-debug', {
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
} )
