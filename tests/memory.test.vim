let s:fn='testdata/cpp/simple/struct.cpp'

function! SetUp()
  call vimspector#test#setup#SetUpWithMappings( 'HUMAN' )
  let g:vimspector_variables_display_mode = 'compact'
endfunction

function! TearDown()
  call vimspector#test#setup#TearDown()
endfunction

" TODO: SkipIf: Big endian system!
" Vimspector/CodeLLDB doesn't actually work on any big endian system to my
" knowledge.

function! s:StartDebugging( ... )
  if a:0 == 0
    let config = #{
          \   fn: s:fn,
          \   line: 26,
          \   col: 7,
          \   launch: #{ configuration: 'CodeLLDB' }
          \ }
  else
    let config = a:1
  endif

  execute 'edit' config.fn
  call setpos( '.', [ 0, config.line, config.col ] )
  call vimspector#ToggleBreakpoint()
  call vimspector#LaunchWithSettings( config.launch )
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer(
        \ config.fn,
        \ config.line,
        \ config.col )
endfunction


function! Test_DumpMemory_VariableWindow()
  call SkipNeovim()
  call s:StartDebugging()

  let x000000000000000 = '0x[0-9A-F]\{16}'

  call WaitForAssert( {->
        \   AssertMatchList(
        \     [
        \       '- Scope: Local',
        \       ' \*+ : {.*}',
        \       ' \*+ t: {i:0, c:''\\0'', fffff:0}',
        \       '+ Scope: Static',
        \       '+ Scope: Global',
        \       '+ Scope: Registers',
        \     ],
        \     GetBufLine( winbufnr( g:vimspector_session_windows.variables ),
        \                 1,
        \                 '$' )
        \   )
        \ } )

  call win_gotoid( g:vimspector_session_windows.variables )
  call cursor( [ 3, 1 ] )
  call vimspector#ReadMemory( #{ length: 9, offset: 0 } )

  call win_gotoid( g:vimspector_session_windows.code )
  call WaitForAssert( {->
        \   AssertMatchList(
        \     [
        \       '--------------------------------------------------------------------------------------',
        \       'Address             Bytes                                             Text',
        \       '--------------------------------------------------------------------------------------',
        \       x000000000000000..': 00 00 00 00 00 00 00 00  00                       .........',
        \     ],
        \     GetBufLine( winbufnr( g:vimspector_session_windows.code ),
        \                 -3,
        \                 '$' )
        \   )
        \ } )

  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer(
        \ s:fn,
        \ 27,
        \ v:null )
  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer(
        \ s:fn,
        \ 28,
        \ v:null )

  call win_gotoid( g:vimspector_session_windows.variables )
  call cursor( [ 3, 1 ] )
  call vimspector#ReadMemory( #{ length: 9, offset: 0 } )
  call WaitForAssert( {->
        \   AssertMatchList(
        \     [
        \       '--------------------------------------------------------------------------------------',
        \       'Address             Bytes                                             Text',
        \       '--------------------------------------------------------------------------------------',
        \       x000000000000000..': 01 00 00 00 63 00 00 00  00                       ....c....',
        \     ],
        \     GetBufLine( winbufnr( g:vimspector_session_windows.code ),
        \                 -3,
        \                 '$' )
        \   )
        \ } )

  call win_gotoid( g:vimspector_session_windows.variables )
  call cursor( [ 3, 1 ] )
  " Trigger the default configured mapping and answer the prompts
  py3 <<EOF
from unittest import mock
with mock.patch( 'vimspector.utils.InputSave' ):
  vim.eval( 'feedkeys( ",m\<C-u>5\<CR>\<CR>", "xt" )' )
EOF
  call WaitForAssert( {->
        \   AssertMatchList(
        \     [
        \       x000000000000000..': 01 00 00 00 63                                    ....c',
        \     ],
        \     GetBufLine( winbufnr( g:vimspector_session_windows.code ),
        \                 '$',
        \                 '$' )
        \   )
        \ } )


  call vimspector#test#setup#Reset()
  %bwipeout!
endfunction

function! Test_DumpMemory_WatchWindow()
  call SkipNeovim()
  call s:StartDebugging()

  let x000000000000000 = '0x[0-9A-F]\{16}'

  call WaitForAssert( {->
        \   AssertMatchList(
        \     [
        \       '- Scope: Local',
        \       ' \*+ : {.*}',
        \       ' \*+ t: {i:0, c:''\\0'', fffff:0}',
        \       '+ Scope: Static',
        \       '+ Scope: Global',
        \       '+ Scope: Registers',
        \     ],
        \     GetBufLine( winbufnr( g:vimspector_session_windows.variables ),
        \                 1,
        \                 '$' )
        \   )
        \ } )

  call vimspector#AddWatch( 't' )
  call WaitForAssert( {->
        \   AssertMatchList(
        \     [
        \       'Watches: ----',
        \       'Expression: t',
        \       ' \*+ Result: {i:0, c:''\\0'', fffff:0}',
        \     ],
        \     GetBufLine( winbufnr( g:vimspector_session_windows.watches ),
        \                 1,
        \                 '$' )
        \   )
        \ } )

  call win_gotoid( g:vimspector_session_windows.watches )
  call cursor( [ 3, 1 ] )
  call vimspector#ExpandVariable()

  call WaitForAssert( {->
        \   AssertMatchList(
        \     [
        \       'Watches: ----',
        \       'Expression: t',
        \       ' \*- Result: {i:0, c:''\\0'', fffff:0}',
        \       '   \*- i: 0',
        \       '   \*- c: ''\\0''',
        \       '   \*- fffff: 0',
        \       '   \*+ another_test: {choo:''\\0''}',
        \     ],
        \     GetBufLine( winbufnr( g:vimspector_session_windows.watches ),
        \                 1,
        \                 '$' )
        \   )
        \ } )

  call cursor( [ 4, 1 ] )
  call vimspector#ReadMemory( #{ length: 9, offset: 0 } )

  call win_gotoid( g:vimspector_session_windows.code )
  call WaitForAssert( {->
        \   AssertMatchList(
        \     [
        \       '--------------------------------------------------------------------------------------',
        \       'Address             Bytes                                             Text',
        \       '--------------------------------------------------------------------------------------',
        \       x000000000000000..': 00 00 00 00 00 00 00 00  00                       .........',
        \     ],
        \     GetBufLine( winbufnr( g:vimspector_session_windows.code ),
        \                 -3,
        \                 '$' )
        \   )
        \ } )

  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer(
        \ s:fn,
        \ 27,
        \ v:null )
  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer(
        \ s:fn,
        \ 28,
        \ v:null )

  call win_gotoid( g:vimspector_session_windows.watches )
  call cursor( [ 4, 1 ] )
  call vimspector#ReadMemory( #{ length: 9, offset: 0 } )
  call WaitForAssert( {->
        \   AssertMatchList(
        \     [
        \       '--------------------------------------------------------------------------------------',
        \       'Address             Bytes                                             Text',
        \       '--------------------------------------------------------------------------------------',
        \       x000000000000000..': 01 00 00 00 63 00 00 00  00                       ....c....',
        \     ],
        \     GetBufLine( winbufnr( g:vimspector_session_windows.code ),
        \                 -3,
        \                 '$' )
        \   )
        \ } )

  call win_gotoid( g:vimspector_session_windows.watches )
  call cursor( [ 5, 1 ] )
  " Trigger the default configured mapping and answer the prompts
  py3 <<EOF
from unittest import mock
with mock.patch( 'vimspector.utils.InputSave' ):
  vim.eval( 'feedkeys( ",m\<C-u>1\<CR>\<CR>", "xt" )' )
EOF
  call WaitForAssert( {->
        \   AssertMatchList(
        \     [
        \       x000000000000000..': 63                                                c',
        \     ],
        \     GetBufLine( winbufnr( g:vimspector_session_windows.code ),
        \                 '$',
        \                 '$' )
        \   )
        \ } )


  call vimspector#test#setup#Reset()
  %bwipeout!
endfunction
