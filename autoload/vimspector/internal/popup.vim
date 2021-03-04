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

function! vimspector#internal#popup#DisplaySplash( message ) abort
  return popup_dialog( a:message, {} )
endfunction

function! vimspector#internal#popup#UpdateSplash( id, message ) abort
  call popup_settext( a:id, a:message )
  return a:id
endfunction

function! vimspector#internal#popup#HideSplash( id ) abort
  call popup_hide( a:id )
endfunction

function! s:YesNoDefaultFilter( default_value, id, key ) abort
  if a:key ==# "\<CR>" || a:key ==# 'D' || a:key ==# 'd'
    call popup_close( a:id, a:default_value )
  endif

  return popup_filter_yesno( a:id, a:key )
endfunction

function! s:ConfirmCallback( confirm_id, id, result ) abort
  py3 __import__( 'vimspector', fromlist = [ 'utils' ] ).utils.ConfirmCallback(
        \ int( vim.eval( 'a:confirm_id' ) ),
        \ int( vim.eval( 'a:result' ) ) )
endfunction

function! vimspector#internal#popup#Confirm(
      \ confirm_id,
      \ text,
      \ default_value ) abort
  let text = a:text
  if type( a:text ) != v:t_list
    let text = [ a:text ]
  endif

  call extend( text, [ '', '(Y)es (N)o (D)efault' ] )

  return popup_dialog( text, {
        \   'callback': function( 's:ConfirmCallback', [ a:confirm_id ] ),
        \   'filter': function( 's:YesNoDefaultFilter', [ a:default_value ] )
        \ } )
endfunction

" Boilerplate {{{
let &cpoptions=s:save_cpo
unlet s:save_cpo
" }}}
