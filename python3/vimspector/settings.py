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


import vim
import builtins
from vimspector import utils


def Get( option: str, default=None, cls=str ):
  return cls( utils.GetVimValue( vim.vars,
                                 f'vimspector_{ option }',
                                 default ) )


def Int( option: str, default=0 ):
  return Get( option, default=default, cls=builtins.int )


def List( option: str, default=[] ):
  return utils.GetVimList( vim.vars, f'vimspector_{ option }', default )
