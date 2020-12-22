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

" Returns: py.ShowBalloon( winnr, expresssion )
function! vimspector#internal#balloon#BalloonExpr() abort
  " winnr + 1 because for *no good reason* winnr is 0 based here unlike
  " everywhere else
  " int() because for *no good reason* winnr is a string.
  return py3eval('_vimspector_session.ShowBalloon('
        \ . 'int( vim.eval( "v:beval_winnr" ) ) + 1,'
        \ . 'vim.eval( "v:beval_text" ) )' )
endfunction

" Returns: py.ShowBalloon( winnr, expresssion )
function! vimspector#internal#balloon#HoverTooltip() abort
  return py3eval('_vimspector_session.ShowTooltip(int( vim.eval( "v:beval_winnr" ) ) + 1 ,vim.eval( "v:beval_text"), 1)')
endfunction


let s:float_win = 0

function! vimspector#internal#balloon#closeCallback() abort
  let s:float_win = 0
  return py3eval('_vimspector_session._CleanUpTooltip()')
endfunction

function! vimspector#internal#balloon#CreateTooltip(is_hover, ...)
  let body = []
  if a:0 > 0
    let body = a:1
  endif

  if has('nvim')
    let buf = nvim_create_buf(v:false, v:true)
    " call nvim_buf_set_option(buf, 'modifiable', v:false)
    call nvim_buf_set_lines(buf, 0, -1, v:true, body)

    " default the dimensions for now. they can be easily overwritten later
    let opts = {
          \ 'relative': 'cursor',
          \ 'width': 50,
          \ 'height': 5,
          \ 'col': 0,
          \ 'row': 1,
          \ 'anchor': 'NW',
          \ 'style': 'minimal'
          \ }
    let s:float_win = nvim_open_win(buf, 0, opts)
    call nvim_win_set_option(s:float_win, 'wrap', v:true)
    call nvim_win_set_option(s:float_win, 'cursorline', v:true)
    call nvim_win_set_option(s:float_win, 'signcolumn', 'no')
    call nvim_win_set_option(s:float_win, 'relativenumber', v:false)
    call nvim_win_set_option(s:float_win, 'number', v:false)

    noa call win_gotoid(s:float_win)

    nnoremap <silent> <buffer> <CR> :<C-u>call vimspector#ExpandVariable()<CR>
    nnoremap <silent> <buffer> <esc> :quit<CR>
    nnoremap <silent> <buffer> <2-LeftMouse>:<C-u>call vimspector#ExpandVariable()<CR>

    " make sure we clean up the float after it loses focus
    augroup vimspector#internal#balloon#nvim_float
      autocmd!
      autocmd WinLeave * :call nvim_win_close(s:float_win, 1) | :call vimspector#internal#balloon#closeCallback() | autocmd! vimspector#internal#balloon#nvim_float
    augroup END

  else
    " assume we are inside vim
    func! MouseFilter(winid, key)
      if index(["\<leftmouse>", "\<2-leftmouse>"], a:key) >= 0
        let mouse_coords = getmousepos()
        " close the popup if mouse is clicked outside the window
        if mouse_coords['winid'] != a:winid
          call popup_close(a:winid)
          call vimspector#internal#balloon#closeCallback()
        endif

        " place the cursor according to the click
        call win_execute(a:winid, ":call cursor(".mouse_coords['line'].", ".mouse_coords['column'].")")

        " expand the variable if we got double click
        if a:key == "\<2-leftmouse>" && mouse_coords['winid'] == a:winid
          " forward line number to python, since vim does not allow us to focus
          " the correct window
          call py3eval("_vimspector_session.ExpandVariable(".line('.', a:winid).")")
        endif

        return 1
      endif
      return 0
    endfunc

    func! CursorFiler(winid, key)
      if index(['j', 'k'], a:key) >= 0
        call win_execute(a:winid, ':normal '.a:key)

        return 1
      elseif a:key == "\<cr>"
        " forward line number to python, since vim does not allow us to focus
        " the correct window
        call py3eval("_vimspector_session.ExpandVariable(".line('.', a:winid).")")

        return 1
      elseif a:key == "\<esc>"
        call popup_close(a:winid)
        call vimspector#internal#balloon#closeCallback()

        return 1
      endif

      return 0
    endfunc

    if s:float_win != 0
      call popup_close(s:float_win)
      call vimspector#internal#balloon#closeCallback()
    endif

    let config = {
      \ 'cursorline': 1,
      \ 'wrap': 1,
      \ 'filtermode': "n",
      \ 'maxwidth': 50,
      \ 'maxheight': 5,
      \ 'scrollbar': 1,
      \ }
    if a:is_hover
      let config['filter'] = "MouseFilter"
      let config['mousemoved'] = [0, 0, 0]
      let s:float_win = popup_beval(body, config)
    else
      let config['filter'] = "CursorFiler"
      let config['moved'] = "any"
      let s:float_win = popup_atcursor(body, config)
    endif

  endif

  return s:float_win
endfunction

" Boilerplate {{{
let &cpoptions=s:save_cpo
unlet s:save_cpo
" }}}
