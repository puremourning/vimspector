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
    py3 import vim
    py3 _vimspector_session = __import__(
          \ "vimspector",
          \ fromlist=[ "debug_session" ] ).debug_session.DebugSession(
          \   vim.eval( 's:prefix' ) )
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

if '_vimspector_session' in globals() and _vimspector_session:
  if int( vim.eval( 's:is_neovim' ) ) and _vimspector_session.IsUITab(
    int( vim.eval( 'a:afile' ) ) ):
    _vimspector_session.Reset( interactive = False )
  elif not _vimspector_session.HasUI():
    _vimspector_session.Reset( interactive = False )

EOF
endfunction

" Boilerplate {{{
let &cpoptions=s:save_cpo
unlet s:save_cpo
" }}}
