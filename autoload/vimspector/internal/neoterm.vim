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

" Ids are unique throughout the life of neovim, but obviously buffer numbers
" aren't
"
" FIXME: Tidy this map when buffers are closed ?
let s:buffer_to_id = {}

function! vimspector#internal#neoterm#PrepareEnvironment( env ) abort
  let old_env = {}

  for key in keys( a:env )
    if exists( '$' . key )
      let old_env[ key ] = getenv( key )
    endif
    call setenv( key, a:env[ key ] )
  endfor

  return old_env
endfunction

function! vimspector#internal#neoterm#ResetEnvironment( env, old_env ) abort
  for key in keys( a:env )
    let value = get( a:old_env, key, v:null )
    call setenv( key, value )
  endfor
endfunction

function! vimspector#internal#neoterm#Start( cmd, opts ) abort
  " Prepare current buffer to be turned into a term if curwin is not set
  if ! get( a:opts, 'curwin', 0 )
    let mods = 'rightbelow '
    if get( a:opts, 'vertical', 0 )
      let mods .= 'vertical '
      let mods .= get( a:opts, 'term_cols', '' )
    else
      let mods .= get( a:opts, 'term_rows', '' )
    endif

    execute mods . 'new'
  endif

  " HACK: Neovim's termopen doesn't support env

  let old_env={}
  try
    let old_env = vimspector#internal#neoterm#PrepareEnvironment(
          \ a:opts[ 'env' ] )
    setlocal nomodified
    let id = termopen( a:cmd, {
          \ 'cwd': a:opts[ 'cwd' ],
          \ 'env': a:opts[ 'env' ],
          \ } )
  finally
    call vimspector#internal#neoterm#ResetEnvironment( a:opts[ 'env' ],
                                                     \ old_env )
  endtry

  let bufnr = bufnr()
  let s:buffer_to_id[ bufnr ] = id
  return bufnr
endfunction

function! s:JobIsRunning( job ) abort
  return jobwait( [ a:job ], 0 )[ 0 ] == -1
endfunction

function! vimspector#internal#neoterm#IsFinished( bufno ) abort
  if !has_key( s:buffer_to_id, a:bufno )
    return v:true
  endif

  return !s:JobIsRunning( s:buffer_to_id[ a:bufno ] )
endfunction

function! vimspector#internal#neoterm#GetPID( bufno ) abort
  if !has_key( s:buffer_to_id, a:bufno )
    return -1
  endif

  return jobpid( s:buffer_to_id[ a:bufno ] )
endfunction

" Boilerplate {{{
let &cpoptions=s:save_cpo
unlet s:save_cpo
" }}}
