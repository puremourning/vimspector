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

let s:channels = {}
let s:jobs = {}

function! s:_OnServerData( session_id, channel, data ) abort
  if !has_key( s:channels, a:session_id ) ||
        \ s:channels[ a:session_id ] isnot a:channel
    return
  endif

  py3 _VimspectorSession( vim.eval( 'a:session_id' ) ).OnChannelData(
        \ vim.eval( 'a:data' ) )
endfunction

function! s:_OnClose( session_id, channel ) abort
  if !has_key( s:channels, a:session_id ) ||
        \ s:channels[ a:session_id ] isnot a:channel
    return
  endif

  echom 'Channel closed'
  redraw
  unlet s:channels[ a:session_id ]
  py3 _VimspectorSession( vim.eval( 'a:session_id' ) ).OnServerExit( 0 )
endfunction

function! vimspector#internal#channel#StartDebugSession(
      \ session_id,
      \ config ) abort

  if has_key( s:channels, a:session_id )
    echo 'Channel is already running'
    return v:false
  endif

  " If we _also_ have a command line, then start the actual job. This allows for
  " servers which start up and listen on some port
  if has_key( a:config, 'command' ) && !get( a:config, 'tty', 0 )
    let s:jobs[ a:session_id ] = job_start( a:config[ 'command' ],
          \                {
          \                    'in_mode': 'raw',
          \                    'out_mode': 'raw',
          \                    'err_mode': 'raw',
          \                    'stoponexit': 'term',
          \                    'env': a:config[ 'env' ],
          \                    'cwd': a:config[ 'cwd' ],
          \                }
          \              )
  endif

  let l:addr = get( a:config, 'host', '127.0.0.1' ) . ':' . a:config[ 'port' ]

  echo 'Connecting to ' . l:addr . '... (waiting for up to 10 seconds)'
  " FIXME: This _always_ waits 10s; the neochannel version is quicker
  let s:channels[ a:session_id ] = ch_open( l:addr,
        \             {
        \                 'mode': 'raw',
        \                 'callback': funcref( 's:_OnServerData',
        \                                       [ a:session_id ] ),
        \                 'close_cb': funcref( 's:_OnClose',
        \                                      [ a:session_id ] ),
        \                 'waittime': 10000,
        \             }
        \           )

  if ch_status( s:channels[ a:session_id ] ) !=# 'open'
    call remove( s:channels, a:session_id )

    echom 'Unable to connect to' l:addr
    redraw
    return v:false
  endif

  return v:true
endfunction

function! vimspector#internal#channel#Send( session_id, msg ) abort
  call ch_sendraw( s:channels[ a:session_id ], a:msg )
  return 1
endfunction

function! vimspector#internal#channel#Timeout( session_id, id ) abort
  py3 _VimspectorSession( vim.eval( 'a:session_id' ) ).OnRequestTimeout(
        \ vim.eval( 'a:id' ) )
endfunction

function! s:_ChannelExists( session_id ) abort
  return has_key( s:channels, a:session_id ) &&
          \ count( [ 'closed', 'fail' ],
          \        ch_status( s:channels[ a:session_id ] ) ) == 0
endfunction

function! vimspector#internal#channel#StopDebugSession( session_id ) abort

  if has_key( s:jobs, a:session_id )
    " We started the job, so we need to kill it and wait to read all the data
    " from the socket

    let job = s:jobs[ a:session_id ]
    if job_status( job ) ==# 'run'
      call job_stop( job, 'term' )
    endif

    while job_status( job ) ==# 'run'
      call job_stop( job, 'kill' )
    endwhile

    call remove( s:jobs, a:session_id )

    if s:_ChannelExists( a:session_id )
      " We're going to block on this channel reading, then manually call the
      " close callback, so remove the automatic close callback to avoid tricky
      " re-entrancy
      call ch_setoptions( s:channels[ a:session_id ], { 'close_cb': '' } )
    endif
  elseif s:_ChannelExists( a:session_id )
    " channel is open, close it and trigger the callback. The callback is _not_
    " triggered when manually calling ch_close. if we get here and the channel
    " is not open, then we there is a _OnClose callback waiting for us, so do
    " nothing.
    call ch_close( s:channels[ a:session_id ] )
  endif

  " block until we've read all data from the socket and handled it.
  while has_key( s:channels, a:session_id ) &&
        \ count( [ 'open', 'buffered' ],
        \       ch_status( s:channels[ a:session_id ] ) ) == 1
    let data = ch_read( s:channels[ a:session_id ], { 'timeout': 10 } )
    call s:_OnServerData( a:session_id, s:channels[ a:session_id ], data )
  endwhile
  if has_key( s:channels, a:session_id )
    call s:_OnClose( a:session_id, s:channels[ a:session_id ] )
  endif
endfunction

function! vimspector#internal#channel#Reset( session_id ) abort
  call vimspector#internal#channel#StopDebugSession( a:session_id )
endfunction

" Boilerplate {{{
let &cpoptions=s:save_cpo
unlet s:save_cpo
" }}}

