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

let s:float_win = 0

function! vimspector#internal#state#CreateTooltip() abort
  if has('nvim')
    let buf = nvim_create_buf(v:false, v:true)
    call nvim_buf_set_lines(buf, 0, -1, v:true, [])

    " default the dimensions for now. they can be easily overwritten later
    let opts = {
          \ 'relative': 'cursor',
          \ 'width': 50,
          \ 'height': 2,
          \ 'col': 0,
          \ 'row': 1,
          \ 'anchor': 'NW',
          \ 'style': 'minimal'
          \ }
    let s:float_win = nvim_open_win(buf, 0, opts)
    call setwinvar(s:float_win, '&wrap', 1)
    call setwinvar(s:float_win, '&cursorline', 1)

    call win_gotoid(s:float_win)

    nnoremap <silent> <buffer> <CR> :<C-u>call vimspector#ExpandVariable()<CR>
    nnoremap <silent> <buffer> <esc>:quit<CR>
    nnoremap <silent> <buffer> <2-LeftMouse>:<C-u>call vimspector#ExpandVariable()<CR>

    " make sure we clean up the float after it loses focus
    augroup vimspector#internal#balloon#nvim_float
      autocmd!
      autocmd WinLeave * :call nvim_win_close(s:float_win, 1) | autocmd! vimspector#internal#balloon#nvim_float
    augroup END

  else
    " assume we are inside vim
    func! MyFilter(winid, key)
      if index(['j', 'k', 'h', 'l'], a:key) >= 0
        call win_execute(a:winid, ':normal '.a:key)
        " do something
        return 1
      elseif a:key == "\<leftmouse>"
        echo 'pressed left mouse'
        let mouse_coords = getmousepos()
        " close the popup if mouse is clicked outside the window
        if mouse_coords['winid'] != a:winid
          call popup_close(a:winid)
        endif

        echo 'clicked line '.mouse_coords['line']
        call win_execute(a:winid, ":call cursor(".mouse_coords['line'].", ".mouse_coords['column'].")")
        return 1
      elseif a:key == "\<cr>"
        echo 'pressed enter at line '.line(".", a:winid)
        echo 'here'
        call vimspector#ExpandVariable()

        return 1
      elseif a:key == "\<esc>"
        call popup_close(a:winid)
        let s:float_win = 0
        return 1
      endif
      return 0
    endfunc

    if s:float_win != 0
      popup_close(s:float_win)
    endif

    let s:float_win = popup_create([], #{
      \ filter: "MyFilter",
      \ cursorline: 1,
      \ wrap: 1,
      \ filtermode: "n",
      \ maxwidth: 50,
      \ maxheight: 5,
      \ scrollbar: 1,
      \ moved: "any",
      \ })

  endif

  return s:float_win
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
  let s:float_win = nvim_open_win(buf, 0, opts)
  call setwinvar(s:float_win, '&wrap', 0)

  augroup vimspector#internal#balloon#nvim_float
    autocmd!
    autocmd CursorMoved * :call nvim_win_close(s:float_win, 1) | autocmd! vimspector#internal#balloon#nvim_float
  augroup END
endfunction
" Boilerplate {{{
let &cpoptions=s:save_cpo
unlet s:save_cpo
" }}}
