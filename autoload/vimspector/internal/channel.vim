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

function! s:_OnServerData( channel, data ) abort
  if !exists( 's:ch' ) || s:ch isnot a:channel
    return
  endif

  py3 << EOF
_vimspector_session.OnChannelData( vim.eval( 'a:data' ) )
EOF
endfunction

function! s:_OnClose( channel ) abort
  if !exists( 's:ch' ) || s:ch isnot a:channel
    return
  endif

  echom 'Channel closed'
  redraw
  unlet s:ch
  py3 _vimspector_session.OnServerExit( 0 )
endfunction

function! vimspector#internal#channel#StartDebugSession( config ) abort

  if exists( 's:ch' )
    echo 'Channel is already running'
    return v:false
  endif

  " If we _also_ have a command line, then start the actual job. This allows for
  " servers which start up and listen on some port
  if has_key( a:config, 'command' ) && !get( a:config, 'tty', 0 )
    let s:job = job_start( a:config[ 'command' ],
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

  echo 'Connecting to ' . l:addr . '... (waiting fo up to 10 seconds)'
  let s:ch = ch_open( l:addr,
        \             {
        \                 'mode': 'raw',
        \                 'callback': funcref( 's:_OnServerData' ),
        \                 'close_cb': funcref( 's:_OnClose' ),
        \                 'waittime': 10000,
        \             }
        \           )

  if ch_status( s:ch ) !=# 'open'
    unlet! s:ch
    echom 'Unable to connect to' l:addr
    redraw
    return v:false
  endif

  return v:true
endfunction

function! vimspector#internal#channel#Send( msg ) abort
  call ch_sendraw( s:ch, a:msg )
  return 1
endfunction

function! vimspector#internal#channel#Timeout( id ) abort
  py3 << EOF
_vimspector_session.OnRequestTimeout( vim.eval( 'a:id' ) )
EOF
endfunction

function! vimspector#internal#channel#StopDebugSession() abort

  if exists( 's:job' )
    " We started the job, so we need to kill it and wait to read all the data
    " from the socket

    if job_status( s:job ) ==# 'run'
      call job_stop( s:job, 'term' )
    endif

    while job_status( s:job ) ==# 'run'
      call job_stop( s:job, 'kill' )
    endwhile

    unlet s:job

    if exists( 's:ch' ) && count( [ 'closed', 'fail' ], ch_status( s:ch ) ) == 0
      " We're going to block on this channel reading, then manually call the
      " close callback, so remove the automatic close callback to avoid tricky
      " re-entrancy
      call ch_setoptions( s:ch, { 'close_cb': '' } )
    endif

  elseif exists( 's:ch' ) &&
          \ count( [ 'closed', 'fail' ], ch_status( s:ch ) ) == 0

    " channel is open, close it and trigger the callback. The callback is _not_
    " triggered when manually calling ch_close. if we get here and the channel
    " is not open, then we there is a _OnClose callback waiting for us, so do
    " nothing.
    call ch_close( s:ch )
  endif

  " block until we've read all data from the socket and handled it.
  while count( [ 'open', 'buffered' ],  ch_status( s:ch ) ) == 1
    let data = ch_read( s:ch, { 'timeout': 10 } )
    call s:_OnServerData( s:ch, data )
  endwhile
  call s:_OnClose( s:ch )
endfunction

function! vimspector#internal#channel#Reset() abort
  if exists( 's:ch' ) || exists( 's:job' )
    call vimspector#internal#channel#StopDebugSession()
  endif
endfunction

" Boilerplate {{{
let &cpoptions=s:save_cpo
unlet s:save_cpo
" }}}

