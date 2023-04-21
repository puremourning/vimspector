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


let s:channels = {}
let s:jobs = {}


function! s:_OnEvent( session_id, chan_id, data, event ) abort
  if v:exiting isnot# v:null
    return
  endif

  if !has_key( s:channels, a:session_id ) ||
        \ a:chan_id != s:channels[ a:session_id ]
    return
  endif

  if a:data == ['']
    echom 'Channel closed'
    redraw
    unlet s:channels[ a:session_id ]
    py3 _VimspectorSession( vim.eval( 'a:session_id' ) ).OnServerExit( 0 )
  else
    py3 _VimspectorSession( vim.eval( 'a:session_id' ) ).OnChannelData(
          \ '\n'.join( vim.eval( 'a:data' ) ) )
  endif
endfunction

function! vimspector#internal#neochannel#StartDebugSession(
      \ session_id,
      \  config ) abort
  if has_key( s:channels, a:session_id )
    echom 'Not starting: Channel is already running'
    redraw
    return v:false
  endif

  " If we _also_ have a command line, then start the actual job. This allows for
  " servers which start up and listen on some port
  if has_key( a:config, 'command' ) && !get( a:config, 'tty', 0 )
    let old_env={}
    try
      let old_env = vimspector#internal#neoterm#PrepareEnvironment(
            \ a:config[ 'env' ] )
      let s:jobs[ a:session_id ] = jobstart( a:config[ 'command' ],
            \                                {
            \                                    'cwd': a:config[ 'cwd' ],
            \                                    'env': a:config[ 'env' ],
            \                                }
            \                              )
    finally
      call vimspector#internal#neoterm#ResetEnvironment( a:config[ 'env' ],
                                                       \ old_env )
    endtry
  endif

  let l:addr = get( a:config, 'host', '127.0.0.1' ) . ':' . a:config[ 'port' ]

  let attempt = 1
  while attempt <= 10
    echo 'Connecting to ' . l:addr . '... (attempt' attempt 'of 10)'
    try
      let s:channels[ a:session_id ] = sockconnect(
            \ 'tcp',
            \ addr,
            \ { 'on_data': funcref( 's:_OnEvent', [ a:session_id ] ) } )
      redraw
      return v:true
    catch /connection refused/
      sleep 1
    endtry
    let attempt += 1
  endwhile

  echom 'Unable to connect to' l:addr 'after 10 attempts'
  redraw
  return v:false
endfunction

function! vimspector#internal#neochannel#Send( session_id, msg ) abort
  if ! has_key( s:channels, a:session_id )
    echom "Can't send message: Channel was not initialised correctly"
    redraw
    return 0
  endif

  call chansend( s:channels[ a:session_id ], a:msg )
  return 1
endfunction

function! vimspector#internal#neochannel#StopDebugSession( session_id ) abort
  if has_key( s:channels, a:session_id )
    call chanclose( s:channels[ a:session_id ] )
    " It doesn't look like we get a callback after chanclos. Who knows if we
    " will subsequently receive data callbacks.
    call s:_OnEvent( a:session_id, s:channels[ a:session_id ], [ '' ], 'data' )
  endif

  if has_key( s:jobs, a:session_id )
    if vimspector#internal#neojob#JobIsRunning( s:jobs[ a:session_id ] )
      call jobstop( s:jobs[ a:session_id ] )
    endif
    unlet s:jobs[ a:session_id ]
  endif
endfunction

function! vimspector#internal#neochannel#Reset() abort
  call vimspector#internal#neochannel#StopDebugSession()
endfunction

" Boilerplate {{{
let &cpoptions=s:save_cpo
unlet s:save_cpo
" }}}

