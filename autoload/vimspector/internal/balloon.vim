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
let s:nvim_related_win = 0

function! vimspector#internal#balloon#closeCallback() abort
  if has('nvim')
    call nvim_win_close(s:float_win, v:true)
    call nvim_win_close(s:nvim_related_win, v:true)
  else
    call popup_close(s:float_win)
  endif

  let s:float_win = 0
  let s:nvim_related_win = 0
  return py3eval('_vimspector_session._CleanUpTooltip()')
endfunction

function! vimspector#internal#balloon#CreateTooltip(is_hover, ...)
  let body = []
  if a:0 > 0
    let body = a:1
  endif

  " tooltip dimensions
  let max_height = 5
  let max_width = 50

  if has('nvim')
    " generate border for the float window by creating a background buffer and
    " overlaying the content buffer
    " see https://github.com/neovim/neovim/issues/9718#issuecomment-546603628
    let top = "╭" . repeat("─", max_width) . "╮"
    let mid = "│" . repeat(" ", max_width) . "│"
    let bot = "╰" . repeat("─", max_width) . "╯"
    let lines = [top] + repeat([mid], max_height) + [bot]

    let buf_id = nvim_create_buf(v:false, v:true)
    call nvim_buf_set_lines(buf_id, 0, -1, v:true, lines)

    " default the dimensions for now. they can be easily overwritten later
    let opts = {
          \ 'relative': 'cursor',
          \ 'width': max_width + 2,
          \ 'height': max_height + 2,
          \ 'col': 0,
          \ 'row': 1,
          \ 'anchor': 'NW',
          \ 'style': 'minimal'
          \ }
    " this is the border window
    let s:nvim_related_win = nvim_open_win(buf_id, 0, opts)
    call nvim_win_set_option(s:nvim_related_win, 'wrap', v:true)
    call nvim_win_set_option(s:nvim_related_win, 'cursorline', v:true)
    call nvim_win_set_option(s:nvim_related_win, 'signcolumn', 'no')
    call nvim_win_set_option(s:nvim_related_win, 'relativenumber', v:false)
    call nvim_win_set_option(s:nvim_related_win, 'number', v:false)

    " when calculating where to display the content window, we need to account
    " for the border
    set winhl=Normal:Floating
    let opts.row += 1
    let opts.height -= 2
    let opts.col += 2
    let opts.width -= 4

    " create the content window
    let buf_id = nvim_create_buf(v:false, v:true)
    call nvim_buf_set_lines(buf_id, 0, -1, v:true, body)
    call nvim_buf_set_option(buf_id, 'modifiable', v:false)
    let s:float_win = nvim_open_win(buf_id, v:false, opts)

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
      autocmd WinLeave * :call vimspector#internal#balloon#closeCallback() | autocmd! vimspector#internal#balloon#nvim_float
    augroup END

  else
    " assume we are inside vim
    func! MouseFilter(winid, key)
      if index(["\<leftmouse>", "\<2-leftmouse>"], a:key) >= 0
        let mouse_coords = getmousepos()
        " close the popup if mouse is clicked outside the window
        if mouse_coords['winid'] != a:winid
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
        call vimspector#internal#balloon#closeCallback()

        return 1
      endif

      return 0
    endfunc

    if s:float_win != 0
      call vimspector#internal#balloon#closeCallback()
    endif

    let config = {
      \ 'cursorline': 1,
      \ 'wrap': 0,
      \ 'filtermode': "n",
      \ 'maxwidth': max_width,
      \ 'maxheight': max_height,
      \ 'scrollbar': 1,
      \ 'border': []
      \ }
    if a:is_hover
      let config['filter'] = "MouseFilter"
      let config['mousemoved'] = [0, 0, 0]
      let config['close'] = "button"
      let config['drag'] = 1
      let config['resize'] = 1
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
