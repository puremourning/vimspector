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

def _VimspectorMakeActive( session ):
  global _vimspector_session

  if '_vimspector_session' not in globals() or _vimspector_session is None:
    _vimspector_session = session
    return True

  if _vimspector_session == session:
    # nothing to do
    return False

  if _vimspector_session is not None:
    _vimspector_session.SwitchFrom()

  _vimspector_session = session
  return True

def _VimspectorSwitchTo( session ):
  global _vimspector_session

  if _VimspectorMakeActive( session ) and _vimspector_session is not None:
    _vimspector_session.SwitchTo()

def _VimspectorSession( session_id ):
  return _vimspector_session_man.GetSession( int( session_id ) )

_vimspector_session_man = __import__(
  "vimspector",
  fromlist=[ "session_manager" ] ).session_manager.Get()

_vimspector_session_man.api_prefix = vim.eval( 's:prefix' )
if '_vimspector_session' in globals() and _vimspector_session is not None:
  _vimspector_session_man.DestroyRootSession( _vimspector_session,
                                              _vimspector_session )
_VimspectorMakeActive( _vimspector_session_man.NewSession() )


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

function! vimspector#internal#state#NewSession( options ) abort
  py3 << EOF
_VimspectorMakeActive(
  _vimspector_session_man.NewSession( **vim.eval( 'a:options' ) ) )
EOF
endfunction

function! vimspector#internal#state#GetAPIPrefix() abort
  return s:prefix
endfunction

function! vimspector#internal#state#TabClosed( afile ) abort
  py3 << EOF

# Try to reset any session which was closed.
if '_vimspector_session_man' in globals():
  if int( vim.eval( 's:is_neovim' ) ):
    # noevim helpfully provides the tab number that was closed in <afile>, so we
    # use that there (it also doesn't correctly invalidate tab objects:
    # https://github.com/neovim/neovim/issues/16327), so we can't use the same
    # code for both. And as usual, when raising bugs against neovim, they are
    # simply closed and never fixed. sigh.
    s = _vimspector_session_man.FindSessionByTab( int( vim.eval( 'a:afile' ) ) )
    if s:
      s.Reset( interactive = False )
  else:
    for session in _vimspector_session_man.SessionsWithInvalidUI():
      session.Reset( interactive = False )

EOF
endfunction

function! vimspector#internal#state#SwitchToSession( id ) abort
  py3 _VimspectorSwitchTo( _VimspectorSession( vim.eval( 'a:id' ) ) )
endfunction


function! vimspector#internal#state#OnTabEnter() abort
  py3 <<EOF
if '_vimspector_session_man' in globals():
  session = _vimspector_session_man.SessionForTab(
    int( vim.eval( 'tabpagenr()' ) ) )

  if session is not None:
    _VimspectorMakeActive( session )
EOF
endfunction


" Boilerplate {{{
let &cpoptions=s:save_cpo
unlet s:save_cpo
" }}}
