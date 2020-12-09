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
if has( 'nvim' )
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

" REMOVEME: this is just a temporary thing to get float window working
" Returns: py.ShowBalloon( winnr, expresssion )
function! vimspector#internal#state#Tooltip() abort
  " winnr + 1 because for *no good reason* winnr is 0 based here unlike
  " everywhere else
  " int() because for *no good reason* winnr is a string.
  return py3eval('_vimspector_session.ShowTooltip('
        \ . 'int( vim.eval( "winnr()" ) ) ,'
        \ . 'vim.eval( "expand(\"<cexpr>\")" ) )' )
endfunction

function! vimspector#internal#state#CreateTooltip() abort

endfunction

function! vimspector#internal#state#ShowTooltip()  abort
  return py3eval('_vimspector_session.ShowTooltip(int( vim.eval( "winnr()" ) ) ,vim.eval( "expand(\"<cexpr>\")" ) )')
endfunction

function! vimspector#internal#state#TooltipExec(body) abort
  let buf = nvim_create_buf(v:false, v:true)
  call nvim_buf_set_lines(buf, 0, -1, v:true, a:body)

  " get the max width on a line
  let width = 0
  let maxWidth = winwidth(0)

  for w in a:body
    let width = max([len(w), width])
    " reached the max size, no point in looping more
    if width > maxWidth
      let width = maxWidth
      break
    endif
  endfor


  let opts = { 'relative': 'cursor', 'width': width, 'height': len(a:body), 'col': 0, 'row': 1, 'anchor': 'NW', 'style': 'minimal' }
  let g:float_win = nvim_open_win(buf, 0, opts)
  call setwinvar(g:float_win, '&wrap', 0)

  augroup vimspector#internal#balloon#nvim_float
    autocmd!
    autocmd CursorMoved * :call nvim_win_close(g:float_win, 1) | autocmd! vimspector#internal#balloon#nvim_float
  augroup END
endfunction
" Boilerplate {{{
let &cpoptions=s:save_cpo
unlet s:save_cpo
" }}}
