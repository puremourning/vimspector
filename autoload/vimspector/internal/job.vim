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

function! s:_OnServerData( jobid, data, event ) abort
  py3 _vimspector_session.OnChannelData( vim.eval( 'join(a:data, "\n")' ) )
endfunction

function! s:_OnServerError( jobid, data, event ) abort
  py3 _vimspector_session.OnServerStderr( vim.eval( 'join(a:data, "\n")' ) )
endfunction

function! s:_OnExit( jobid, status, event ) abort
  echom 'Channel exit with status ' . a:status
  unlet s:job
  py3 _vimspector_session.OnServerExit( vim.eval( 'a:status' ) )
endfunction

function! vimspector#internal#job#Send( msg ) abort
  if ! exists( 's:job' )
    echom "Can't send message: Job was not initialised correctly"
    redraw
    return 0
  endif

  call vimspector#async#job#send( s:job, a:msg )
  return 1
endfunction

function! vimspector#internal#job#StartDebugSession( config ) abort
  if exists( 's:job' )
    echom 'Not starging: Job is already running'
    redraw
    return v:none
  endif

  let s:job = vimspector#async#job#start( a:config[ 'command' ],
        \                {
        \                    'on_exit': funcref( 's:_OnExit' ),
        \                    'on_stdout': funcref( 's:_OnServerData' ),
        \                    'on_stderr': funcref( 's:_OnServerError' ),
        \                    'cwd': a:config[ 'cwd' ],
        \                }
        \              )
       "\                    'env': a:config[ 'env' ],

  echom 'Started job, id is: ' . s:job
  redraw

  if s:job == -1
    echom 'Unable to start job'
    redraw
    return v:false
  endif

  return v:true
endfunction

function! vimspector#internal#job#StopDebugSession() abort
  if !exists( 's:job' )
    echom "Not stopping session: Job doesn't exist"
    redraw
    return
  endif

  echom 'Terminating job'
  redraw
  call vimspector#async#job#stop( s:job )
  unlet s:job
endfunction

function! vimspector#internal#job#Reset() abort
  call vimspector#internal#job#StopDebugSession()
endfunction

function! vimspector#internal#job#StartCommandWithLog( cmd, category ) abort
  if ! exists( 's:commands' )
    let s:commands = {}
  endif

  if ! has_key( s:commands, a:category )
    let s:commands[ a:category ] = []
  endif

  let l:index = len( s:commands[ a:category ] )

  let l:job = vimspector#async#job#start(
        \ a:cmd,
        \ {
        \   'out_io': 'buffer',
        \   'in_io': 'null',
        \   'err_io': 'buffer',
        \   'out_name': '_vimspector_log_' . a:category . '_out',
        \   'err_name': '_vimspector_log_' . a:category . '_err',
        \   'out_modifiable': 0,
        \   'err_modifiable': 0,
        \ } )

  call add( s:commands[ a:category ], l:job )

  if l:job < 0
    echom 'Unable to start job for ' . a:cmd
    redraw
    return v:none
  endif

  let l:stdout = bufnr('_vimspector_log_' . a:category . '_out')
  let l:stderr = bufnr('_vimspector_log_' . a:category . '_err')

  return [ l:stdout, l:stderr ]
endfunction


function! vimspector#internal#job#CleanUpCommand( category ) abort
  if ! exists( 's:commands' )
    let s:commands = {}
  endif

  if ! has_key( s:commands, a:category )
    return
  endif
  for j in s:commands[ a:category ]
    call vimspector#async#job#stop( j )
  endfor

  unlet s:commands[ a:category ]
endfunction

" Boilerplate {{{
let &cpoptions=s:save_cpo
unlet s:save_cpo
" }}}
