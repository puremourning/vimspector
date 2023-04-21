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
  'ui_mode':            'auto',
  'bottombar_height':   10,
  'disassembly_height': 20,
  'variables_display_mode': 'compact', # compact/full

  # For ui_mode = 'horizontal':
  'sidebar_width':      50,
  'code_minwidth':      82,
  'terminal_maxwidth':  80,
  'terminal_minwidth':  10,

  # For ui_mode = 'vertical':
  'topbar_height':      15,
  'code_minheight':     20,
  'terminal_maxheight': 15,
  'terminal_minheight': 5,

  # WinBar
  'enable_winbar':      True,

  # Session files
  'session_file_name': '.vimspector.session',

  # Breakpoints
  'toggle_disables_breakpoint': False,

  # Signs
  'sign_priority': {
    'vimspectorPC':            200,
    'vimspectorPCBP':          200,
    'vimspectorNonActivePC':   9, # must be same as vimspectorBP* to combine
    'vimspectorBP':            9,
    'vimspectorBPCond':        9,
    'vimspectorBPLog':         9,
    'vimspectorBPDisabled':    9,
    'vimspectorCurrentThread': 200,
    'vimspectorCurrentFrame':  200,
  },

  # Presentation hints
  'presentation_hint_hl': {
    # Source.presentationHint
    'emphasize': 'Title',
    'deemphasize': 'Conceal',

    # StackFrame.presentationHint
    'label': 'NonText',
    'subtle': 'Conceal',

    # Scope.presentationHint
    'arguments': 'Title',
    'locals': 'Title',
    'registers': 'Title',

    # VariablePresentaionHint.kind
    'property': 'Identifier',
    'method': 'Function',
    'class': 'Type',
    'data': 'String',
  },

  # Installer
  'install_gadgets': [],

  # Mappings
  'mappings': {
    'variables': {
      'expand_collapse': [ '<CR>', '<2-LeftMouse>' ],
      'delete': [ '<Del>' ],
      'set_value': [ '<C-CR>', '<leader><CR>' ],
      'read_memory': [ '<leader>m' ],
    },
    'stack_trace': {
      'expand_or_jump': [ '<CR>', '<2-LeftMouse>' ],
      'focus_thread': [ '<leader><CR>' ],
    },
    'breakpoints': {
      'toggle': [ 't', '<F9>' ],
      'toggle_all': [ 'T' ],
      'delete': [ 'dd', '<Del>' ],
      'add_line': [ 'i', 'a', 'o', '<Insert>' ],
      'add_func': [ 'I', 'A', 'O', '<leader><Insert>' ],
      'jump_to': [ '<2-LeftMouse>', '<Enter>' ]
    }
  },

  # Custom
  'java_hotcodereplace_mode': 'ask',

  # Debug configs
  'adapters': {},
  'configurations': {},
}


def Get( option: str, cls=str ):
  return cls( utils.GetVimValue( vim.vars,
                                 f'vimspector_{ option }',
                                 DEFAULTS.get( option, cls() ) ) )


def Int( option: str ):
  return Get( option, cls=builtins.int )


def Bool( option: str ):
  return bool( Int( option ) )


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

LIST_TYPE = list
if hasattr( vim, 'List' ):
  LIST_TYPE = vim.List


def _IsDict( o ):
  return isinstance( o, DICT_TYPE ) or isinstance( o, dict )


def _IsList( o ):
  return isinstance( o, LIST_TYPE ) or isinstance( o, list )


def Dict( option ):
  return _UpdateDict(
    dict( DEFAULTS.get( option, {} ) ),
    DictNoBytes( vim.vars.get( f'vimspector_{ option }', DICT_TYPE() ) ) )


def ObjectNoBytes( o ):
  if o is None:
    return None

  if isinstance( o, bytes ):
    o = o.decode( 'utf-8' )
  elif _IsDict( o ):
    o = DictNoBytes( o )
  elif _IsList( o ):
    new_o = []
    for i in o:
      new_o.append( ObjectNoBytes( i ) )
    o = new_o
  return o


def DictNoBytes( d ):
  if d is None:
    return d

  r = {}
  for k, v in d.items():
    if isinstance( k, bytes ):
      k = k.decode( 'utf-8' )
    r[ k ] = ObjectNoBytes( v )
  return r


def _UpdateDict( target, override ):
  """Apply the updates in |override| to the dict |target|. This is like
  dict.update, but recursive. i.e. if the existing element is a dict, then
  override elements of the sub-dict rather than wholesale replacing.
  e.g.
  UpdateDict(
    {
      'outer': { 'inner': { 'key': 'oldValue', 'existingKey': True } }
    },
    {
      'outer': { 'inner': { 'key': 'newValue' } },
      'newKey': { 'newDict': True },
    }
  )
  yields:
    {
      'outer': {
        'inner': {
           'key': 'newValue',
           'existingKey': True
        }
      },
      'newKey': { newDict: True }
    }
  """

  for key, value in override.items():
    current_value = target.get( key )
    if not _IsDict( current_value ):
      target[ key ] = value
    elif _IsDict( value ):
      target[ key ] = _UpdateDict( current_value, value )
    else:
      target[ key ] = value

  return target
