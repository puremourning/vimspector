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
scriptencoding utf-8


" Boilerplate {{{
let s:save_cpo = &cpoptions
set cpoptions&vim
" }}}

function! vimspector#internal#popup#DisplaySplash( message ) abort
  return popup_dialog( a:message, {
        \ 'close': 'button',
        \ 'drag': 1,
        \ } )
endfunction

function! vimspector#internal#popup#UpdateSplash( id, message ) abort
  call popup_settext( a:id, a:message )
  return a:id
endfunction

function! vimspector#internal#popup#HideSplash( id ) abort
  call popup_close( a:id )
  return v:null
endfunction

let s:current_selection = 0
let s:selections = []
let s:text = []

function! s:UpdatePopup( id ) abort
  let buf = copy( s:text )
  call extend( buf, s:DrawButtons() )
  call popup_settext( a:id, buf )
endfunction

function! s:ConfirmKeyFilter( keys, id, key ) abort
  if a:key ==# "\<CR>"
    call popup_close( a:id, s:current_selection + 1 )
    return 1
  elseif index( [ "\<Tab>", "\<Right>" ], a:key ) >= 0
    let s:current_selection = ( s:current_selection + 1 ) % len( s:selections )
    call s:UpdatePopup( a:id )
    return 1
  elseif index( [ "\<S-Tab>", "\<Left>" ], a:key ) >= 0
    let s:current_selection = s:current_selection == 0
          \ ? len( s:selections ) - 1: s:current_selection - 1
    call s:UpdatePopup( a:id )
    return 1
  elseif a:key ==# "\<Esc>" || a:key ==# "\<C-c>"
    call popup_close( a:id, -1 )
    return 1
  endif

  let index = 1
  for key in a:keys
    if a:key ==? key
      call popup_close( a:id, index )
      return 1
    endif
    let index += 1
  endfor
endfunction

function! s:ConfirmCallback( confirm_id, id, result ) abort
  py3 __import__( 'vimspector', fromlist = [ 'utils' ] ).utils.ConfirmCallback(
        \ int( vim.eval( 'a:confirm_id' ) ),
        \ int( vim.eval( 'a:result' ) ) )
endfunction

function! s:SelectionPosition( idx ) abort
  return a:idx == 0 ? 0 : len( join( s:selections[ : a:idx - 1 ], ' ' ) ) + 1
endfunction

function! s:DrawButtons() abort
  return [ {
        \ 'text': join( s:selections, ' ' ),
        \ 'props': [
          \   {
          \      'col': s:SelectionPosition( s:current_selection ) + 1,
          \      'length': len( s:selections[ s:current_selection ] ),
          \      'type': 'VimspectorSelectedItem'
          \   },
          \ ]
        \ } ]
endfunction

function! vimspector#internal#popup#Confirm(
      \ confirm_id,
      \ text,
      \ options,
      \ default_value,
      \ keys ) abort

  if empty( prop_type_get( 'VimspectorSelectedItem' )  )
    call prop_type_add( 'VimspectorSelectedItem', {
          \ 'highlight': 'PMenuSel'
          \ } )
  endif

  let lines = split( a:text, "\n", v:true )
  let buf = []
  for line in lines
    call add( buf, { 'text': line, 'props': [] } )
  endfor

  call add( buf, { 'text': '', 'props': [] } )

  let s:selections = a:options
  let s:current_selection = ( a:default_value - 1 )

  let s:text = copy( buf )
  call extend( buf, s:DrawButtons() )

  let config = {
        \   'callback': function( 's:ConfirmCallback', [ a:confirm_id ] ),
        \   'filter': function( 's:ConfirmKeyFilter', [ a:keys ] ),
        \   'mapping': v:false,
        \ }
  let config = vimspector#internal#popup#SetBorderChars( config )

  return popup_dialog( buf, config  )
endfunction

function! vimspector#internal#popup#SetBorderChars( config ) abort
  " When ambiwidth is single, use prettier characters for the border. This
  " would look silly when ambiwidth is double.
  if &ambiwidth ==# 'single' && &encoding ==? 'utf-8'
    let a:config[ 'borderchars' ] = [ '─', '│', '─', '│', '╭', '╮', '┛', '╰' ]
  endif

  return a:config
endfunction


" Boilerplate {{{
let &cpoptions=s:save_cpo
unlet s:save_cpo
" }}}
