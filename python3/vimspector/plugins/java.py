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


gadgets.RegisterGadget( 'java-language-server', {
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
} )


gadgets.RegisterGadget( 'vscode-java-debug', {
  'language': 'java',
  'enabled': False,
  'download': {
    'url': 'https://github.com/microsoft/vscode-java-debug/releases/download/'
           '${version}/${file_name}',
  },
  'all': {
    'version': '0.26.0',
    'file_name': 'vscjava.vscode-java-debug-0.26.0.vsix',
    'checksum':
      'de49116ff3a3c941dad0c36d9af59baa62cd931e808a2ab392056cbb235ad5ef',
  },
  'adapters': {
    "vscode-java": {
      "name": "vscode-java",
      "port": "${DAPPort}",
      "configuration": {
        "cwd": "${workspaceRoot}"
      }
    }
  },
} )
