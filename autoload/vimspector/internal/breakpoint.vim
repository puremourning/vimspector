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
"

function! vimspector#internal#breakpoint#CloseBreakpointView(winid) abort
  if a:winid >= 0
    call win_gotoid(a:winid)
    close
  endif

  call py3eval( '_vimspector_session.CloseBreakpointsCallback()' )
endfunction

function! vimspector#internal#breakpoint#CreateBreakpointView(lines, winid) abort
  let old_winid = win_getid()
  let old_curs_pos = getpos( '.' )
  if a:winid < 0
    botright 10new

    setlocal buftype=nofile
    setlocal bufhidden=delete
    setlocal noswapfile
    setlocal nobuflisted
  else
    call win_gotoid(a:winid)
  endif

  let curr_winid = win_getid()

  setlocal noreadonly
  setlocal modifiable

  %delete

  call append( 0, a:lines )

  setlocal readonly
  setlocal nomodifiable

  augroup vimspector#internal#breakpoint#breakpoint_view
    autocmd!
    autocmd WinClosed <buffer>
          \ :call vimspector#internal#breakpoint#CloseBreakpointView(-1)
  augroup END

  nnoremap <silent> <buffer> t
          \ :<C-u>call py3eval( '_vimspector_session.ToggleBreakpointViewBreakpoint()' )<CR>
  nnoremap <silent> <buffer> c
          \ :<C-u>call py3eval( '_vimspector_session.ClearBreakpointViewBreakpoint()' )<CR>
  nnoremap <silent> <buffer> <Enter>
          \ :<C-u>call py3eval( '_vimspector_session.JumpToBreakpointViewBreakpoint()' )<CR>
  nnoremap <silent> <buffer> <2-LeftMouse>
          \ :<C-u>call py3eval( '_vimspector_session.JumpToBreakpointViewBreakpoint()' )<CR>

  " restore focus to the initial window
  call win_gotoid( old_winid )

  " if we were inside the breakpoint view already,
  " also restore the cursor position
  if old_winid == curr_winid
    call setpos('.', old_curs_pos)
  endif

  return curr_winid
endfunction

