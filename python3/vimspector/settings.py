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

DEFAULTS = {
  # UI
  'bottombar_height':  10,
  'sidebar_width':     50,
  'code_minwidth':     82,
  'terminal_maxwidth': 80,
  'terminal_minwidth': 10,

  # Signs
  'sign_priority': {
    'vimspectorPC':         200,
    'vimspectorPCBP':       200,
    'vimspectorBP':         9,
    'vimspectorBPCond':     9,
    'vimspectorBPDisabled': 9,
  },

  # Installer
  'install_gadgets': [],
}


def Get( option: str, default=None, cls=str ):
  return cls( utils.GetVimValue( vim.vars,
                                 f'vimspector_{ option }',
                                 DEFAULTS.get( option, cls() ) ) )


def Int( option: str ):
  return Get( option, cls=builtins.int )


def List( option: str ):
  return utils.GetVimList( vim.vars,
                           f'vimspector_{ option }',
                           DEFAULTS.get( option, [] ) )


# FIXME:
# In Vim, we must use vim.Dictionary because this sorts out the annoying
# keys-as-bytes discrepancy, making things awkward. That said, we still have the
# problem where the _values_ are potentially bytes. It's very tempting to just
# make a deep copy to antive str type here.
# Of course in neovim, it's totally different and you actually get a dict type
# back (though for once, neovim is making life somewhat easier for a change).
DICT_TYPE = dict
if hasattr( vim, 'Dictionary' ):
  DICT_TYPE = vim.Dictionary


def Dict( option: str ):
  d = DICT_TYPE( DEFAULTS.get( option, {} ) )
  d.update( utils.GetVimValue( vim.vars,
                               f'vimspector_{ option }',
                               {} ) )
  return d
