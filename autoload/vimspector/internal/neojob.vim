" vimspector - A multi-language debugging system for Vim
" Copyright 2020 Ben Jackson
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

let s:jobs = {}
let s:commands = {}



function! s:_OnEvent( session_id, chan_id, data, event ) abort
  if v:exiting isnot# v:null
    return
  endif

  if !has_key( s:jobs, a:session_id ) || a:chan_id != s:jobs[ a:session_id ]
    return
  endif

  " In neovim, the data argument is a list.
  if a:event ==# 'stdout'
    py3 _VimspectorSession( vim.eval( 'a:session_id' ) ).OnChannelData(
          \ '\n'.join( vim.eval( 'a:data' ) ) )
  elseif a:event ==# 'stderr'
    py3 _VimspectorSession( vim.eval( 'a:session_id' ) ).OnServerStderr(
          \ '\n'.join( vim.eval( 'a:data' ) ) )
  elseif a:event ==# 'exit'
    redraw
    unlet s:jobs[ a:session_id ]
    py3 _VimspectorSession( vim.eval( 'a:session_id' ) ).OnServerExit(
          \ vim.eval( 'a:data' ) )
  endif
endfunction

function! vimspector#internal#neojob#StartDebugSession(
      \ session_id,
      \ config ) abort
  if has_key( s:jobs, a:session_id )
    echom 'Not starting: Job is already running'
    redraw
    return v:false
  endif


  " HACK: Workaround for 'env' not being supported.

  let old_env={}
  try
    let old_env = vimspector#internal#neoterm#PrepareEnvironment(
          \ a:config[ 'env' ] )
    let s:jobs[ a:session_id ] = jobstart( a:config[ 'command' ],
          \                {
          \                    'on_stdout': funcref( 's:_OnEvent',
          \                                          [ a:session_id ] ),
          \                    'on_stderr': funcref( 's:_OnEvent',
          \                                          [ a:session_id ] ),
          \                    'on_exit': funcref( 's:_OnEvent',
          \                                        [ a:session_id ] ),
          \                    'cwd': a:config[ 'cwd' ],
          \                    'env': a:config[ 'env' ],
          \                }
          \              )
  finally
    call vimspector#internal#neoterm#ResetEnvironment( a:config[ 'env' ],
                                                     \ old_env )
  endtry

  return v:true
endfunction

function! vimspector#internal#neojob#JobIsRunning( job ) abort
  return jobwait( [ a:job ], 0 )[ 0 ] == -1
endfunction

function! vimspector#internal#neojob#Send( session_id, msg ) abort
  if ! has_key( s:jobs, a:session_id )
    echom "Can't send message: Job was not initialised correctly"
    redraw
    return 0
  endif

  if !vimspector#internal#neojob#JobIsRunning( s:jobs[ a:session_id ] )
    echom "Can't send message: Job is not running"
    redraw
    return 0
  endif

  call chansend( s:jobs[ a:session_id ], a:msg )
  return 1
endfunction

function! vimspector#internal#neojob#StopDebugSession( session_id ) abort
  if !has_key( s:jobs, a:session_id )
    return
  endif

  if vimspector#internal#neojob#JobIsRunning( s:jobs[ a:session_id ] )
    redraw
    call jobstop( s:jobs[ a:session_id ] )
  endif
endfunction

function! vimspector#internal#neojob#Reset( session_id ) abort
  call vimspector#internal#neojob#StopDebugSession( a:session_id )
endfunction

function! s:_OnCommandEvent( session_id, category, id, data, event ) abort
  if v:exiting isnot# v:null
    return
  endif

  if a:event ==# 'stdout' || a:event ==# 'stderr'
    if a:data == ['']
      return
    endif

    if ! has_key( s:commands, a:session_id )
      return
    endif

    if !has_key( s:commands[ a:session_id ], a:category )
      return
    endif

    if !has_key( s:commands[ a:session_id ][ a:category ], a:id )
      return
    endif

    if a:event ==# 'stdout'
      let buffer = s:commands[ a:session_id ][ a:category ][ a:id ].stdout
    elseif a:event ==# 'stderr'
      let buffer = s:commands[ a:session_id ][ a:category ][ a:id ].stderr
    endif

    try
      call bufload( buffer )
    catch /E325/
      " Ignore E325/ATTENTION
    endtry


    let numlines = py3eval( "len( vim.buffers[ int( vim.eval( 'buffer' ) ) ] )" )
    let last_line = getbufline( buffer, '$' )[ 0 ]

    call s:MakeBufferWritable( buffer )
    try
      if numlines == 1 && last_line ==# ''
        call setbufline( buffer, 1, a:data[ 0 ] )
      else
        call setbufline( buffer, '$', last_line . a:data[ 0 ] )
      endif

      call appendbufline( buffer, '$', a:data[ 1: ] )
    finally
      call s:MakeBufferReadOnly( buffer )
      call setbufvar( buffer, '&modified', 0 )
    endtry

    " if the buffer is visible, scroll it, but don't allow autocommands to fire,
    " as this may close the current window!
    let w = bufwinnr( buffer )
    if w > 0
      let cw = winnr()
      try
        noautocmd execute w . 'wincmd w'
        noautocmd normal! Gz-
      finally
        noautocmd execute cw . 'wincmd w'
      endtry
    endif
  elseif a:event ==# 'exit'
    py3 __import__( "vimspector",
          \         fromlist = [ "utils" ] ).utils.OnCommandWithLogComplete(
          \           vim.eval( 'a:session_id' ),
          \           vim.eval( 'a:category' ),
          \           int( vim.eval( 'a:data' ) ) )
  endif
endfunction

function! s:SetUpHiddenBuffer( buffer ) abort
  call setbufvar( a:buffer, '&hidden', 1 )
  call setbufvar( a:buffer, '&bufhidden', 'hide' )
  call setbufvar( a:buffer, '&wrap', 0 )
  call setbufvar( a:buffer, '&swapfile', 0 )
  call setbufvar( a:buffer, '&textwidth', 0 )
  call s:MakeBufferReadOnly( a:buffer )
endfunction

function! s:MakeBufferReadOnly( buffer ) abort
  call setbufvar( a:buffer, '&modifiable', 0 )
  call setbufvar( a:buffer, '&readonly', 1 )
endfunction

function! s:MakeBufferWritable( buffer ) abort
  call setbufvar( a:buffer, '&readonly', 0 )
  call setbufvar( a:buffer, '&modifiable', 1 )
endfunction


function! vimspector#internal#neojob#StartCommandWithLog(
      \ session_id,
      \ cmd,
      \ category ) abort
  if ! has_key( s:commands, a:session_id )
    let s:commands[ a:session_id ] = {}
  endif

  if ! has_key( s:commands[ a:session_id ], a:category )
    let s:commands[ a:session_id ][ a:category ] = {}
  endif

  let buf = bufnr( '_vimspector_log_' . a:category, v:true )

  " FIXME: This largely duplicates the same stuff in the python layer, but we
  " don't want to potentially mess up Vim behaviour where the job output is
  " attached to a buffer set up by Vim. So we sort o mimic that here.
  call s:SetUpHiddenBuffer( buf )

  let id = jobstart(a:cmd,
        \          {
        \            'on_stdout': funcref( 's:_OnCommandEvent',
        \                                  [ a:session_id, a:category ] ),
        \            'on_stderr': funcref( 's:_OnCommandEvent',
        \                                  [ a:session_id, a:category ] ),
        \            'on_exit': funcref( 's:_OnCommandEvent',
        \                                [ a:session_id, a:category ] ),
        \          } )

  let s:commands[ a:session_id ][ a:category ][ id ] = {
        \ 'stdout': buf,
        \ 'stderr': buf
        \ }

  return buf
endfunction

function! vimspector#internal#neojob#CleanUpCommand(
      \ session_id,
      \ category ) abort
  if ! has_key( s:commands, a:session_id )
    return
  endif

  if ! has_key( s:commands[ a:session_id ], a:category )
    return
  endif

  for id in keys( s:commands[ a:session_id ][ a:category ] )
    let id = str2nr( id )
    if jobwait( [ id ], 0 )[ 0 ] == -1
      call jobstop( id )
    endif
    call jobwait( [ id ], -1 )
  endfor
  unlet! s:commands[ a:session_id ][ a:category ]
endfunction

" Boilerplate {{{
let &cpoptions=s:save_cpo
unlet s:save_cpo
" }}}
