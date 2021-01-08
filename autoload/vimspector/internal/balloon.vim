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
"
" tooltip dimensions
let s:min_width = 1
let s:min_height = 1
let s:max_width = 80
let s:max_height = 20

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

function! vimspector#internal#balloon#nvim_generate_border(width, height)
  let top = "╭" . repeat("─",a:width + 2) . "╮"
  let mid = "│" . repeat(" ",a:width + 2) . "│"
  let bot = "╰" . repeat("─",a:width + 2) . "╯"
  let lines = [top] + repeat([mid], a:height) + [bot]

  return lines
endfunction

function! vimspector#internal#balloon#nvim_resize_tooltip()
  if !has('nvim') || s:float_win <= 0 || s:nvim_related_win <= 0
    return
  endif

  noa call win_gotoid(s:float_win)
  let buf_lines = getline(1, '$')

  let width = s:min_width
  let height = min([max([s:min_height, len(buf_lines)]), s:max_height])

  " calculate the longest line
  for l in buf_lines
    let width = max([width, len(l)])
  endfor

  let width = min([width, s:max_width])

  let opts = {
        \ 'width': width,
        \ 'height': height,
        \ }
  " resize the content window
  call nvim_win_set_config(s:float_win, opts)

  " resize the border window
  let opts['width'] = width + 4
  let opts['height'] = height + 2
  call nvim_win_set_config(s:nvim_related_win, opts)
  call nvim_buf_set_lines(nvim_win_get_buf(s:nvim_related_win), 0, -1, v:true, vimspector#internal#balloon#nvim_generate_border(width, height))

endfunction

function! vimspector#internal#balloon#CreateTooltip(is_hover, ...)
  let body = []
  if a:0 > 0
    let body = a:1
  endif

  if has('nvim')
    " generate border for the float window by creating a background buffer and
    " overlaying the content buffer
    " see https://github.com/neovim/neovim/issues/9718#issuecomment-546603628
    let buf_id = nvim_create_buf(v:false, v:true)
    call nvim_buf_set_lines(buf_id, 0, -1, v:true, vimspector#internal#balloon#nvim_generate_border(s:max_width, s:max_height))

    " default the dimensions for now. they can be easily overwritten later
    let opts = {
          \ 'relative': 'cursor',
          \ 'width': s:max_width + 2,
          \ 'height': s:max_height + 2,
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
      let handled = 0
      if index(["\<leftmouse>", "\<2-leftmouse>"], a:key) >= 0
        let mouse_coords = getmousepos()
        " close the popup if mouse is clicked outside the window
        if mouse_coords['winid'] != a:winid
          call vimspector#internal#balloon#closeCallback()
        else
          " place the cursor according to the click
          call win_execute(a:winid, ":call cursor(".mouse_coords['line'].", ".mouse_coords['column'].")")

          " expand the variable if we got double click
          if a:key == "\<2-leftmouse>" && mouse_coords['winid'] == a:winid
            " forward line number to python, since vim does not allow us to focus
            " the correct window
            call py3eval("_vimspector_session.ExpandVariable(".line('.', a:winid).")")
            let handled = 1
          endif
        endif
      endif
      return handled
    endfunc

    func! CursorFilter(winid, key)
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
      \ 'wrap': 0,
      \ 'filtermode': "n",
      \ 'maxwidth': s:max_width,
      \ 'maxheight': s:max_height,
      \ 'scrollbar': 1,
      \ 'border': [],
      \ 'padding': [ 0, 1, 0, 1]
      \ }
    if a:is_hover
      let config['filter'] = "MouseFilter"
      let config['mousemoved'] = [0, 0, 0]
      let config['close'] = "button"
      let config['drag'] = 1
      let config['resize'] = 1
      let s:float_win = popup_beval(body, config)
    else
      let config['filter'] = "CursorFilter"
      let config['moved'] = "any"
      let config['cursorline'] = 1
      let s:float_win = popup_atcursor(body, config)
    endif

  endif

  return s:float_win
endfunction

" Boilerplate {{{
let &cpoptions=s:save_cpo
unlet s:save_cpo
" }}}
