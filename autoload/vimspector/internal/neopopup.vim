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

" Neovim's float window API, like its job/channel API is painful to use
" compared to Vim's so we have to employ more hacks

" We can't seem to pass a Window handle back to the python, so we have to
" maintain yet another cached here
let s:db = {}
let s:next_id = 0


function! s:MessageToList( message ) abort
  if type( a:message ) == type( [] )
    let message = a:message
  else
    let message = [ a:message ]
  endif
  return message
endfunction

function! s:GetSplashConfig( message ) abort
  let l = max( map( a:message, 'len( v:val )' ) )
  let h = len( a:message )

  return { 'relative':   'editor',
         \ 'width':      l,
         \ 'height':     h,
         \ 'col':        ( &columns / 2 ) - ( l / 2 ),
         \ 'row':        ( &lines / 2 ) - h / 2,
         \ 'anchor':     'NW',
         \ 'style':      'minimal',
         \ 'focusable':  v:false,
         \ }
endfunction

function! vimspector#internal#neopopup#DisplaySplash( message ) abort
  let message = s:MessageToList( a:message )
  let buf = nvim_create_buf(v:false, v:true)
  call nvim_buf_set_lines(buf, 0, -1, v:true, message )

  let win = nvim_open_win(buf, 0, s:GetSplashConfig( message ) )
  call nvim_win_set_option(win, 'wrap', v:false)
  call nvim_win_set_option(win, 'colorcolumn', '')

  let id = s:next_id
  let s:next_id += 1
  let s:db[ id ] = { 'win': win, 'buf': buf }
  return id
endfunction

function! vimspector#internal#neopopup#UpdateSplash( id, message ) abort
  let splash = s:db[ a:id ]
  let message = s:MessageToList( a:message )
  call nvim_buf_set_lines( splash.buf, 0, -1, v:true, message )
  call nvim_win_set_config( splash.win, s:GetSplashConfig( message ) )
  return a:id
endfunction

function! vimspector#internal#neopopup#HideSplash( id ) abort
  let splash = s:db[ a:id ]
  call nvim_win_close( splash.win, v:true )
  call nvim_buf_delete( splash.buf, {} )
  unlet s:db[ a:id ]
  return v:null
endfunction

function! vimspector#internal#neopopup#Confirm( confirm_id,
                                              \ text,
                                              \ options,
                                              \ default_value,
                                              \ keys ) abort

  " Neovim doesn't have an equivalent of popup_dialog, and it's way too much
  " effort to write one, so we just use confirm()...
  " Annoyingly we can't use confirm() here because for some reason it doesn't
  " render properly in a channel callback. So we use input() and mimic dialog
  " behaviour.
  let prompt = a:text
  for opt in a:options
    let prompt .= ' ' . opt
  endfor
  let prompt .= ': '

  try
    let result = input( prompt, a:keys[ a:default_value - 1 ] )
  catch /.*/
    let result = -1
  endtry

  " Map the results to what the vim popup stuff would return (s:ConfirmCallback
  " in popup.vim), i.e.:
  "  - 1-based index of selected item, or
  "  - -1 or 0 for cancellation
  if result ==# ''
    " User pressed ESC/ctrl-c
    let result = -1
  else
    let index = 1
    for k in a:keys
      if k ==? result
        let result = index
        break
      endif
      let index += 1
    endfor

    if index > len( a:keys )
      let result = -1
    endif
  endif

  py3 __import__( 'vimspector', fromlist = [ 'utils' ] ).utils.ConfirmCallback(
        \ int( vim.eval( 'a:confirm_id' ) ),
        \ int( vim.eval( 'result' ) ) )
endfunction

" Boilerplate {{{
let &cpoptions=s:save_cpo
unlet s:save_cpo
" }}}

