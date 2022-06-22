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

scriptencoding utf-8

let s:popup_win_id = 0
let s:nvim_border_win_id = 0
"
" tooltip dimensions
let s:min_width = 1
let s:min_height = 1
let s:max_width = 80
let s:max_height = 20

let s:is_neovim = has( 'nvim' )


" This is used as the balloonexpr in vim to show the Tooltip at the hover
" position
function! vimspector#internal#balloon#HoverEvalTooltip() abort
  return py3eval( '_vimspector_session.HoverEvalTooltip('
                \ . ' int( vim.eval( "v:beval_winnr" ) ) + 1,'
                \ . ' int( vim.eval( "v:beval_bufnr" ) ),'
                \ . ' int( vim.eval( "v:beval_lnum" ) ),'
                \ . ' vim.eval( "v:beval_text"),'
                \ . ' 1 )' )
endfunction

function! vimspector#internal#balloon#CreateTooltip( is_hover, ... ) abort
  let body = []
  if a:0 > 0
    let body = a:1
  endif

  if s:popup_win_id != 0
    call vimspector#internal#balloon#Close()
  endif

  if s:is_neovim
    call s:CreateNeovimTooltip( body )
  else
    let config = {
      \ 'wrap': 0,
      \ 'filtermode': 'n',
      \ 'maxwidth': s:max_width,
      \ 'maxheight': s:max_height,
      \ 'minwidth': s:min_width,
      \ 'minheight': s:min_height,
      \ 'scrollbar': 1,
      \ 'border': [],
      \ 'padding': [ 0, 1, 0, 1],
      \ 'drag': 1,
      \ 'resize': 1,
      \ 'close': 'button',
      \ 'callback': 'vimspector#internal#balloon#CloseCallback',
      \ }

    let config = vimspector#internal#popup#SetBorderChars( config )

    if a:is_hover
      let config[ 'filter' ] = 'vimspector#internal#balloon#MouseFilter'
      let config[ 'mousemoved' ] = [ 0, 0, 0 ]
      let s:popup_win_id = popup_beval( body, config )
    else
      let config[ 'filter' ] = 'vimspector#internal#balloon#CursorFilter'
      let config[ 'moved' ] = 'any'
      let config[ 'cursorline' ] = 1
      let config[ 'mapping' ] = 0
      let s:popup_win_id = popup_atcursor( body, config )
    endif

  endif

  return s:popup_win_id
endfunction

" Filters for vim {{{
function! vimspector#internal#balloon#MouseFilter( winid, key ) abort
  if a:key ==# "\<Esc>"
    call vimspector#internal#balloon#Close()
    return 0
  endif

  if index( [ "\<leftmouse>", "\<2-leftmouse>" ], a:key ) < 0
    return 0
  endif

  let handled = 0
  let mouse_coords = getmousepos()

  " close the popup if mouse is clicked outside the window
  if mouse_coords[ 'winid' ] != a:winid
    call vimspector#internal#balloon#Close()
    return 0
  endif

  " place the cursor according to the click
  call win_execute( a:winid,
                  \ ':call cursor( '
                  \ . mouse_coords[ 'line' ]
                  \ . ', '
                  \ . mouse_coords[ 'column' ]
                  \ . ' )' )

  " expand the variable if we got double click
  if a:key ==? "\<2-leftmouse>"
    call py3eval( '_vimspector_session.ExpandVariable('
                \ . 'buf = vim.buffers[ ' .  winbufnr( a:winid ) . ' ],'
                \ . 'line_num = ' . line( '.', a:winid )
                \ . ')' )
    let handled = 1
  endif

  return handled
endfunction

function! s:MatchKey( key, candidates ) abort
  for candidate in a:candidates
    " If the mapping string looks like a special character, then try and
    " expand it. This is... a hack. The whole thing only works if the mapping
    " is a single key (anyway), and so we assume any string starting with < is a
    " special key (which will be the common case) and try and map it. If it
    " fails... it fails.
    if candidate[ 0 ] ==# '<'
      try
        execute 'let candidate = "\' . candidate . '"'
      endtry
    endif

    if candidate ==# a:key
      return v:true
    endif
  endfor

  return v:false
endfunction

function! vimspector#internal#balloon#CursorFilter( winid, key ) abort
  let mappings = py3eval(
        \ "__import__( 'vimspector',"
        \."            fromlist = [ 'settings' ] ).settings.Dict("
        \."              'mappings' )[ 'variables' ]" )

  if index( [ "\<LeftMouse>", "\<2-LeftMouse>" ], a:key ) >= 0
    return vimspector#internal#balloon#MouseFilter( a:winid, a:key )
  endif

  if s:MatchKey( a:key, mappings.expand_collapse )
    call py3eval( '_vimspector_session.ExpandVariable('
                \ . 'buf = vim.buffers[ ' .  winbufnr( a:winid ) . ' ],'
                \ . 'line_num = ' . line( '.', a:winid )
                \ . ')' )
    return 1
  elseif s:MatchKey( a:key, mappings.set_value )
    call py3eval( '_vimspector_session.SetVariableValue('
                \ . 'buf = vim.buffers[ ' .  winbufnr( a:winid ) . ' ],'
                \ . 'line_num = ' . line( '.', a:winid )
                \ . ')' )
    return 1
  endif

  return popup_filter_menu( a:winid, a:key )
endfunction

" }}}

" Closing {{{

function! vimspector#internal#balloon#CloseCallback( ... ) abort
  let s:popup_win_id = 0
  let s:nvim_border_win_id = 0
  return py3eval( '_vimspector_session.CleanUpTooltip()' )
endfunction

function! vimspector#internal#balloon#Close() abort
  if s:popup_win_id == 0
    return
  endif

  if s:is_neovim
    call nvim_win_close( s:popup_win_id, v:true )
    call nvim_win_close( s:nvim_border_win_id, v:true )

    call vimspector#internal#balloon#CloseCallback()
  elseif !empty( popup_getoptions( s:popup_win_id ) )
    call popup_close(s:popup_win_id)
  endif
endfunction

" }}}

" Neovim pollyfill {{{

function! vimspector#internal#balloon#ResizeTooltip() abort
  if !s:is_neovim
    " Vim does this for us
    return
  endif

  if s:popup_win_id <= 0 || s:nvim_border_win_id <= 0
    " nothing to resize
    return
  endif

  noautocmd call win_gotoid( s:popup_win_id )
  let buf_lines = getline( 1, '$' )

  let width = s:min_width
  let height = min( [ max( [ s:min_height, len( buf_lines ) ] ),
                  \   s:max_height ] )

  " calculate the longest line
  for l in buf_lines
    let width = max( [ width, len( l ) ] )
  endfor

  let width = min( [ width, s:max_width ] )

  let opts = {
        \ 'width': width,
        \ 'height': height,
        \ }

  " resize the content window
  call nvim_win_set_config( s:popup_win_id, opts )

  " resize the border window
  let opts[ 'width' ] = width + 4
  let opts[ 'height' ] = height + 2

  call nvim_win_set_config( s:nvim_border_win_id, opts )
  call nvim_buf_set_lines( nvim_win_get_buf( s:nvim_border_win_id ),
                         \ 0,
                         \ -1,
                         \ v:true,
                         \ s:GenerateBorder( width, height ) )
endfunction

" neovim doesn't have the border support, so we have to make our own.
" FIXME: This will likely break if the user has `ambiwidth=2`
function! s:GenerateBorder( width, height ) abort

  let top = '╭' . repeat('─',a:width + 2) . '╮'
  let mid = '│' . repeat(' ',a:width + 2) . '│'
  let bot = '╰' . repeat('─',a:width + 2) . '╯'
  let lines = [ top ] + repeat( [ mid ], a:height ) + [ bot ]

  return lines
endfunction

function! s:CreateNeovimTooltip( body ) abort
  " generate border for the float window by creating a background buffer and
  " overlaying the content buffer
  " see https://github.com/neovim/neovim/issues/9718#issuecomment-546603628
  let buf_id = nvim_create_buf( v:false, v:true )
  call nvim_buf_set_lines( buf_id,
                         \ 0,
                         \ -1,
                         \ v:true,
                         \ s:GenerateBorder( s:max_width, s:max_height ) )

  " default the dimensions initially, then we'll calculate the real size and
  " resize it.
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
  let s:nvim_border_win_id = nvim_open_win( buf_id, 0, opts )
  call nvim_win_set_option( s:nvim_border_win_id, 'signcolumn', 'no' )
  call nvim_win_set_option( s:nvim_border_win_id, 'relativenumber', v:false )
  call nvim_win_set_option( s:nvim_border_win_id, 'number', v:false )

  " when calculating where to display the content window, we need to account
  " for the border
  let opts.row += 1
  let opts.height -= 2
  let opts.col += 2
  let opts.width -= 4

  " create the content window
  let buf_id = nvim_create_buf( v:false, v:true )
  call nvim_buf_set_lines( buf_id, 0, -1, v:true, a:body )
  call nvim_buf_set_option( buf_id, 'modifiable', v:false )
  let s:popup_win_id = nvim_open_win( buf_id, v:false, opts )

  " Apparently none of these work, when 'style' is 'minimal'
  call nvim_win_set_option( s:popup_win_id, 'wrap', v:false )
  call nvim_win_set_option( s:popup_win_id, 'cursorline', v:true )
  call nvim_win_set_option( s:popup_win_id, 'signcolumn', 'no' )
  call nvim_win_set_option( s:popup_win_id, 'relativenumber', v:false )
  call nvim_win_set_option( s:popup_win_id, 'number', v:false )

  " Move the cursor into the popup window, as this is the only way we can
  " interact with the popup in neovim
  noautocmd call win_gotoid( s:popup_win_id )

  nnoremap <silent> <buffer> <Esc> <cmd>quit<CR>
  call py3eval( "__import__( 'vimspector', "
              \."            fromlist = [ 'variables' ] )."
              \.'               variables.AddExpandMappings()' )

  " Close the popup whenever we leave this window
  augroup vimspector#internal#balloon#nvim_float
    autocmd!
    autocmd WinLeave <buffer>
          \ :call vimspector#internal#balloon#Close()
          \ | autocmd! vimspector#internal#balloon#nvim_float
  augroup END

  call vimspector#internal#balloon#ResizeTooltip()
endfunction

" }}}


" Boilerplate {{{
let &cpoptions=s:save_cpo
unlet s:save_cpo
" }}}
