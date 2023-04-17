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

let s:jobs = {}
let s:commands = {}

function! s:_OnServerData( session_id, channel, data ) abort
  if !has_key( s:jobs, a:session_id ) ||
        \ ch_getjob( a:channel ) isnot s:jobs[ a:session_id ]
    call ch_log( 'Get data after process exit' )
    return
  endif

  py3 _VimspectorSession( vim.eval( 'a:session_id' ) ).OnChannelData(
        \ vim.eval( 'a:data' ) )
endfunction

function! s:_OnServerError( session_id, channel, data ) abort
  if !has_key( s:jobs, a:session_id ) ||
        \ ch_getjob( a:channel ) isnot s:jobs[ a:session_id ]
    call ch_log( 'Get data after process exit' )
    return
  endif

  py3 _VimspectorSession( vim.eval( 'a:session_id' ) ).OnServerStderr(
        \ vim.eval( 'a:data' ) )
endfunction


" FIXME: We should wait until both the exit_cb _and_ the channel closed callback
" have been received before OnServerExit?

function! s:_OnExit( session_id, channel, status ) abort
  if !has_key( s:jobs, a:session_id ) ||
        \ ch_getjob( a:channel ) isnot s:jobs[ a:session_id ]
    call ch_log( 'Unexpected exit callback' )
    return
  endif

  echom 'Channel exit with status ' . a:status
  redraw
  if has_key( s:jobs, a:session_id )
    unlet s:jobs[ a:session_id ]
  endif
  py3 _VimspectorSession( vim.eval( 'a:session_id' ) ).OnServerExit(
        \ vim.eval( 'a:status' ) )
endfunction

function! s:_OnClose( session_id, channel ) abort
  if !has_key( s:jobs, a:session_id ) ||
        \ ch_getjob( a:channel ) isnot s:jobs[ a:session_id ]
    call ch_log( 'Channel closed after exit' )
    return
  endif

  echom 'Channel closed'
  redraw
endfunction

function! vimspector#internal#job#StartDebugSession( session_id, config ) abort
  if has_key( s:jobs, a:session_id )
    echom 'Not starting: Job is already running'
    redraw
    return v:false
  endif

  let s:jobs[ a:session_id ] = job_start( a:config[ 'command' ],
        \                {
        \                    'in_mode': 'raw',
        \                    'out_mode': 'raw',
        \                    'err_mode': 'raw',
        \                    'exit_cb': funcref( 's:_OnExit',
        \                                        [ a:session_id ] ),
        \                    'close_cb': funcref( 's:_OnClose',
        \                                         [ a:session_id ] ),
        \                    'out_cb': funcref( 's:_OnServerData',
        \                                       [ a:session_id ] ),
        \                    'err_cb': funcref( 's:_OnServerError',
        \                                        [ a:session_id ] ),
        \                    'stoponexit': 'term',
        \                    'env': a:config[ 'env' ],
        \                    'cwd': a:config[ 'cwd' ],
        \                }
        \              )

  if !has_key( s:jobs, a:session_id )
    " The job died immediately after starting and we cleaned up
    return v:false
  endif

  let status = job_status( s:jobs[ a:session_id ] )

  echom 'Started job, status is: ' . status
  redraw

  if status !=# 'run'
    return v:false
  endif

  return v:true
endfunction

function! vimspector#internal#job#Send( session_id, msg ) abort
  if ! has_key( s:jobs, a:session_id )
    echom "Can't send message: Job was not initialised correctly"
    redraw
    return 0
  endif

  let job = s:jobs[ a:session_id ]

  if job_status( job ) !=# 'run'
    echom "Can't send message: Job is not running"
    redraw
    return 0
  endif

  let ch = job_getchannel( job )
  if ch ==# 'channel fail'
    echom 'Channel was closed unexpectedly!'
    redraw
    return 0
  endif

  call ch_sendraw( ch, a:msg )
  return 1
endfunction

function! vimspector#internal#job#StopDebugSession( session_id ) abort
  if ! has_key( s:jobs, a:session_id )
    echom "Not stopping session: Job doesn't exist"
    redraw
    return
  endif

  let job = s:jobs[ a:session_id ]

  if job_status( job ) ==# 'run'
    echom 'Terminating job'
    redraw
    call job_stop( job, 'kill' )
  endif
endfunction

function! vimspector#internal#job#Reset( session_id ) abort
  call vimspector#internal#job#StopDebugSession( a:session_id )
endfunction

function! s:_OnCommandExit( session_id, category, ch, code ) abort
  py3 __import__( "vimspector",
        \         fromlist = [ "utils" ] ).utils.OnCommandWithLogComplete(
        \           vim.eval( 'a:session_id' ),
        \           vim.eval( 'a:category' ),
        \           int( vim.eval( 'a:code' ) ) )
endfunction

function! vimspector#internal#job#StartCommandWithLog(
      \ session_id,
      \ cmd,
      \ category ) abort
  if ! exists( 's:commands' )
    let s:commands = {}
  endif

  if ! has_key( s:commands, a:session_id )
    let s:commands[ a:session_id ] = {}
  endif

  if ! has_key( s:commands[ a:session_id ], a:category )
    let s:commands[ a:session_id ][ a:category ] = []
  endif

  let l:index = len( s:commands[ a:session_id ][ a:category ] )

  let buf = '_vimspector_log_' . a:session_id . '_' . a:category

  call add( s:commands[ a:session_id ][ a:category ], job_start(
        \ a:cmd,
        \ {
        \   'out_io': 'buffer',
        \   'err_io': 'buffer',
        \   'out_msg': 0,
        \   'err_msg': 0,
        \   'out_name': buf,
        \   'err_name': buf,
        \   'exit_cb': funcref( 's:_OnCommandExit',
        \                       [ a:session_id, a:category ] ),
        \   'out_modifiable': 0,
        \   'err_modifiable': 0,
        \   'stoponexit': 'kill'
        \ } ) )

  if job_status( s:commands[ a:session_id ][ a:category ][ index ] ) !=# 'run'
    echom 'Unable to start job for ' . string( a:cmd )
    redraw
    return v:none
  endif

  return bufnr( buf )
endfunction


function! vimspector#internal#job#CleanUpCommand( session_id, category ) abort
  if ! exists( 's:commands' )
    let s:commands = {}
  endif

  if ! has_key( s:commands, a:session_id )
    let s:commands[ a:session_id ] = {}
  endif

  if ! has_key( s:commands[ a:session_id ], a:category )
    return
  endif
  for j in s:commands[ a:session_id ][ a:category ]
    call job_stop( j, 'kill' )
  endfor

  unlet s:commands[ a:session_id ][ a:category ]

  if len( s:commands[ a:session_id ] ) == 0
    unlet s:commands[ a:session_id ]
  endif
endfunction

" Boilerplate {{{
let &cpoptions=s:save_cpo
unlet s:save_cpo
" }}}
