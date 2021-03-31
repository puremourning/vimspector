" vimspector - A multi-language debugging system for Vim
" Copyright 2018 Ben Jackson
"
" Licensed under the Apache License, Version 2.0 (the "License");
" you may not use this file except in compliance with the License.
" You may obtain a copy of the License at
"
"   http://www.apache.org/licenses/LICENSE-2.0
"
" Unless required by applicable law or agreed to in writing, software
" distributed under the License is distributed on an "AS IS" BASIS,
" WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
" See the License for the specific language governing permissions and
" limitations under the License.


" Boilerplate {{{
let s:save_cpo = &cpoptions
set cpoptions&vim
" }}}

let s:prefix = ''
let s:is_neovim = 0
if has( 'nvim' )
  let s:is_neovim = 1
  let s:prefix='neo'
endif

function! vimspector#internal#state#Reset() abort
  try
    py3 <<EOF

import vim

_vimspector_session_man = __import__(
  "vimspector",
  fromlist=[ "session_manager" ] ).session_manager.Get()

# Deprecated
_vimspector_session = _vimspector_session_man.NewSession(
  vim.eval( 's:prefix' ) )

def _VimspectorSession( session_id ):
  return _vimspector_session_man.GetSession( int( session_id ) )

EOF
  catch /.*/
    echohl WarningMsg
    echom 'Exception while loading vimspector:' v:exception
    echom 'From:' v:throwpoint
    echom 'Vimspector unavailable: Requires Vim compiled with Python 3.6'
    echohl None
    return v:false
  endtry

  return v:true
endfunction

function! vimspector#internal#state#GetAPIPrefix() abort
  return s:prefix
endfunction

function! vimspector#internal#state#TabClosed( afile ) abort
  py3 << EOF

# reset if:
# - a tab closed
# - the vimspector session exists
# - the vimspector session does _not_ have a UI (which suggests that it was
#   probably the vimspector UI tab that was closed)
#
# noevim helpfully provides the tab number that was closed in <afile>, so we
# use that there (it also doens't correctly invalidate tab objects:
# https://github.com/neovim/neovim/issues/16327)
#
# TODO: set a tab-local variable, or a global which maps tabs to session IDs
# This probably doesn't work now with multiple-sessions

if '_vimspector_session' in globals() and _vimspector_session:
  if int( vim.eval( 's:is_neovim' ) ) and _vimspector_session.IsUITab(
    int( vim.eval( 'a:afile' ) ) ):
    _vimspector_session.Reset( interactive = False )
  elif not _vimspector_session.HasUI():
    _vimspector_session.Reset( interactive = False )

EOF
endfunction

function! vimspector#internal#state#SwitchToSession( id ) abort
  py3 _vimspector_session = _VimspectorSession( vim.eval( 'a:id' ) )
endfunction


function! vimspector#internal#state#OnTabEnter() abort
  py3 <<EOF
session = _vimspector_session_man.SessionForTab(
  int( vim.eval( 'tabpagenr()' ) ) )

if session is not None:
  _vimspector_session = session
EOF
endfunction


" Boilerplate {{{
let &cpoptions=s:save_cpo
unlet s:save_cpo
" }}}
