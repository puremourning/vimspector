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

scriptencoding utf-8

" Compiler plugin to help running vimspector tests

if exists('current_compiler')
  finish
endif
let current_compiler = 'vimspector_test'

setlocal errorformat=
        \Found\ errors\ in\ %f:%.%#:

let s:run_tests = findfile( 'run_tests', '.;' )
let s:root_dir = fnamemodify( s:run_tests, ':h' )
let &l:makeprg=fnamemodify( s:run_tests, ':p' ) . ' $* 2>&1'

let s:make_cmd = get( g:, 'vimspector_test_make_cmd', 'Make' )

" If :Make doesn't exist, then use :make
if ! exists( ':' . s:make_cmd )
  let s:make_cmd = 'make'
endif

let s:standard_test_args = ' --quick --report messages '
if has( 'nvim' )
  let s:standard_test_args .= ' --exe nvim '
endif

function! VimGetCurrentFunction()
  echom s:GetCurrentFunction()[ 0 ]
endfunction

function! s:GetCurrentFunction()
  " Store the cursor position; we'll need to reset it
  let [ buf, row, col, offset ] = getpos( '.' )

  let [ test_function, test_function_line ] = [ v:null, -1 ]

  let pattern = '\V\C\s\*func\%\(tion\)\?!\?\s\+\(\<\w\+\>\)\.\*\$'

  let lnum = prevnonblank( '.' )

  " Find the top-level method and class
  while lnum > 0
    call cursor( lnum, 1 )
    let lnum = search( pattern, 'bcnWz' )

    if lnum <= 0
      call cursor( row, col )
      return [ test_function, test_function_line ]
    endif

    let this_decl = substitute( getline( lnum ), pattern, '\1', '' )
    let this_decl_is_test = match( this_decl, '\V\C\^Test_' ) >= 0

    if this_decl_is_test
      let [ test_function, test_function_line ] = [ this_decl, lnum ]

      if indent( lnum ) == 0
        call cursor( row, col )
        return [ test_function, test_function_line ]
      endif
    endif

    let lnum = prevnonblank( lnum - 1 )
  endwhile

  return [ v:null, -1 ]
endfunction

function! s:RunTestUnderCursorInVimspector()
  update
  let l:test_func_name = s:GetCurrentFunction()[ 0 ]

  if l:test_func_name ==# ''
    echo 'No test method found'
    return
  endif

  echo "Running test '" . l:test_func_name . "'"

  call vimspector#LaunchWithSettings( {
        \ 'configuration': 'Run test',
        \ 'TestFunction': l:test_func_name
        \ } )
endfunction

function! s:RunAllTestsInVimspector()
  update
  call vimspector#LaunchWithSettings( {
        \ 'configuration': 'Run script',
        \ } )
endfunction


function! s:RunTestUnderCursorWithDebugpy()
  let $TEST_WITH_DEBUGPY = 1
  try
    call s:RunTestUnderCursor()
  finally
    let $TEST_WITH_DEBUGPY = 0
  endtry
endfunction

function! s:RunTestUnderCursor()
  update
  let l:test_func_name = s:GetCurrentFunction()[ 0 ]

  if l:test_func_name ==# ''
    echo 'No test method found'
    return
  endif

  echo "Running test '" . l:test_func_name . "'"

  let l:test_arg = expand( '%:p:t' ) . ':' . l:test_func_name
  let l:cwd = getcwd()
  execute 'lcd ' . s:root_dir
  try
    execute s:make_cmd
          \ . s:standard_test_args
          \ . get( g:, 'vimspector_test_args', '' ) . ' '
          \ . l:test_arg
  finally
    execute 'lcd ' . l:cwd
  endtry
endfunction

function! s:RunTest()
  update
  let l:cwd = getcwd()
  execute 'lcd ' . s:root_dir
  try
    execute s:make_cmd
          \ . s:standard_test_args
          \ . get( g:, 'vimspector_test_args', '' )
          \ . ' %:p:t'
  finally
    execute 'lcd ' . l:cwd
  endtry
endfunction

function! s:RunAllTests()
  update
  let l:cwd = getcwd()
  execute 'lcd ' . s:root_dir
  try
    execute s:make_cmd
          \ . s:standard_test_args
          \ . get( g:, 'vimspector_test_args', '' )
  finally
    execute 'lcd ' . l:cwd
  endtry
endfunction

if ! has( 'gui_running' )
  " ® is right-option+r
  nnoremap <buffer> ® :call <SID>RunTest()<CR>
  nnoremap <buffer> <leader>® :call <SID>RunAllTestsInVimspector()<CR>
  " £ is right-option+r
  nnoremap <buffer> Â :call <SID>RunAllTests()<CR>
  " † is right-option+t
  nnoremap <buffer> † :call <SID>RunTestUnderCursor()<CR>
  nnoremap <buffer> <leader>† :call <SID>RunTestUnderCursorInVimspector()<CR>
  nnoremap <buffer> <leader><leader>† :call <SID>RunTestUnderCursorWithDebugpy()<CR>
  " å is the right-option+q
  nnoremap <buffer> å :cfirst<CR>
  " å is the right-option+a
  nnoremap <buffer> œ :cnext<CR>
  " å is the right-option+f
  nnoremap <buffer> ƒ :FuncLine<CR>
  " Ω is the right-option+z
  nnoremap <buffer> Ω :cprevious<CR>
endif

function! s:GoToCurrentFunctionLine( ... )
  if a:0 < 1
    call inputsave()
    let lnum = str2nr( input( 'Enter line num: ' ) )
    call inputrestore()
  else
    let lnum = a:1
  endif

  let [ f, l ] = s:GetCurrentFunction()
  if f is v:null
    return
  endif

  let lnum += l

  echo 'Function' f 'at line' l '(jump to line ' lnum . ')'

  call cursor( [ lnum, indent( lnum ) ] )
endfunction

command! -buffer -nargs=? -bar
      \ FuncLine
      \ :call s:GoToCurrentFunctionLine( <f-args> )
