let s:fn='../support/test/python/simple_python/main.py'

function! SetUp()
  call vimspector#test#setup#SetUpWithMappings( 'HUMAN' )
endfunction

function! ClearDown()
  call vimspector#test#setup#ClearDown()
endfunction

function! s:StartDebugging( ... )
  if a:0 == 0
    let config = #{
          \   fn: s:fn,
          \   line: 23,
          \   col: 1,
          \   launch: #{ configuration: 'run' }
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

function! Test_SimpleWatches()
  call s:StartDebugging()

  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, 25, 1 )

  " Add a wtch
  call vimspector#AddWatch( 't' )
  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, 26, 1 )

  " Delete a watch expression
  call win_gotoid( g:vimspector_session_windows.watches )
  call setpos( '.', [ 0, 3, 1 ] )
  call feedkeys( "\<Del>", 'xt' )

  call WaitForAssert( {->
        \   assert_equal(
        \     [
        \         'Watches: ----',
        \     ],
        \     getbufline( winbufnr( g:vimspector_session_windows.watches ),
        \                 1,
        \                 '$' )
        \   )
        \ } )

  call assert_equal( 'python',
                   \ getbufvar(
                   \   winbufnr( g:vimspector_session_windows.watches ),
                   \   '&syntax' ) )

  call vimspector#StepInto()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, 13, 1 )
  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, 14, 1 )
  call vimspector#AddWatch( 'i' )

  call WaitForAssert( {->
        \   assert_equal(
        \     [
        \         'Watches: ----',
        \         'Expression: i',
        \         ' *- Result: 0',
        \     ],
        \     getbufline( winbufnr( g:vimspector_session_windows.watches ),
        \                 1,
        \                 '$' )
        \   )
        \ } )

  call vimspector#AddWatch( 'i+1' )

  call WaitForAssert( {->
        \   assert_equal(
        \     [
        \         'Watches: ----',
        \         'Expression: i',
        \         '  - Result: 0',
        \         'Expression: i+1',
        \         ' *- Result: 1',
        \     ],
        \     getbufline( winbufnr( g:vimspector_session_windows.watches ),
        \                 1,
        \                 '$' )
        \   )
        \ } )

  call vimspector#AddWatch( 'i+2' )

  call WaitForAssert( {->
        \   assert_equal(
        \     [
        \         'Watches: ----',
        \         'Expression: i',
        \         '  - Result: 0',
        \         'Expression: i+1',
        \         '  - Result: 1',
        \         'Expression: i+2',
        \         ' *- Result: 2',
        \     ],
        \     getbufline( winbufnr( g:vimspector_session_windows.watches ),
        \                 1,
        \                 '$' )
        \   )
        \ } )

  " Delete that middle watch
  call win_gotoid( g:vimspector_session_windows.watches )
  call setpos( '.', [ 0, 4, 1 ] )
  call vimspector#DeleteWatch()

  call WaitForAssert( {->
        \   assert_equal(
        \     [
        \         'Watches: ----',
        \         'Expression: i',
        \         '  - Result: 0',
        \         'Expression: i+2',
        \         ' *- Result: 2',
        \     ],
        \     getbufline( winbufnr( g:vimspector_session_windows.watches ),
        \                 1,
        \                 '$' )
        \   )
        \ } )

  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, 15, 1 )
  call WaitForAssert( {->
        \   assert_equal(
        \     [
        \         'Watches: ----',
        \         'Expression: i',
        \         '  - Result: 0',
        \         'Expression: i+2',
        \         '  - Result: 2',
        \     ],
        \     getbufline( winbufnr( g:vimspector_session_windows.watches ),
        \                 1,
        \                 '$' )
        \   )
        \ } )

  " Delete the top watch
  call win_gotoid( g:vimspector_session_windows.watches )
  call setpos( '.', [ 0, 3, 1 ] )
  call vimspector#DeleteWatch()

  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, 13, 1 )
  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, 14, 1 )
  call WaitForAssert( {->
        \   assert_equal(
        \     [
        \         'Watches: ----',
        \         'Expression: i+2',
        \         ' *- Result: 3',
        \     ],
        \     getbufline( winbufnr( g:vimspector_session_windows.watches ),
        \                 1,
        \                 '$' )
        \   )
        \ } )
  call vimspector#test#setup#Reset()
  %bwipe!
endfunction

function! Test_ExpandVariables()
  let fn =  'testdata/cpp/simple/struct.cpp'
  call s:StartDebugging( #{ fn: fn, line: 24, col: 1, launch: #{
        \   configuration: 'run-to-breakpoint'
        \ } } )

  " Make sure the Test t is initialised
  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 26, 1 )

  call WaitForAssert( {->
        \   assert_equal(
        \     [
        \       '- Scope: Locals',
        \       ' *+ t (Test): {...}',
        \     ],
        \     getbufline( winbufnr( g:vimspector_session_windows.variables ),
        \                 1,
        \                 '$' )
        \   )
        \ } )
  call assert_equal( 'cpp',
                   \ getbufvar(
                   \   winbufnr( g:vimspector_session_windows.variables ),
                   \   '&syntax' ) )

  " Expand
  call win_gotoid( g:vimspector_session_windows.variables )
  call setpos( '.', [ 0, 2, 1 ] )
  call feedkeys( "\<CR>", 'xt' )

  call WaitForAssert( {->
        \   AssertMatchist(
        \     [
        \       '- Scope: Locals',
        \       ' \*- t (Test): {...}',
        \       '   \*- i (int): 0',
        \       '   \*- c (char): 0 ''\\0\{1,3}''',
        \       '   \*- fffff (float): 0',
        \       '   \*+ another_test (AnotherTest):\( {...}\)\?',
        \     ],
        \     getbufline( winbufnr( g:vimspector_session_windows.variables ),
        \                 1,
        \                 '$' )
        \   )
        \ } )

  " Step - stays expanded
  call vimspector#StepOver()
  call WaitForAssert( {->
        \   AssertMatchist(
        \     [
        \       '- Scope: Locals',
        \       '  - t (Test): {...}',
        \       '   \*- i (int): 1',
        \       '    - c (char): 0 ''\\0\{1,3}''',
        \       '    - fffff (float): 0',
        \       '    + another_test (AnotherTest):\( {...}\)\?',
        \     ],
        \     getbufline( winbufnr( g:vimspector_session_windows.variables ),
        \                 1,
        \                 '$' )
        \   )
        \ } )

  " Collapse
  call win_gotoid( g:vimspector_session_windows.variables )
  call setpos( '.', [ 0, 2, 1 ] )
  call feedkeys( "\<CR>", 'xt' )
  call WaitForAssert( {->
        \   assert_equal(
        \     [
        \       '- Scope: Locals',
        \       '  + t (Test): {...}',
        \     ],
        \     getbufline( winbufnr( g:vimspector_session_windows.variables ),
        \                 1,
        \                 '$' )
        \   )
        \ } )

  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 28, 1 )
  call WaitForAssert( {->
        \   assert_equal(
        \     [
        \       '- Scope: Locals',
        \       '  + t (Test): {...}',
        \     ],
        \     getbufline( winbufnr( g:vimspector_session_windows.variables ),
        \                 1,
        \                 '$' )
        \   )
        \ } )

  call win_gotoid( g:vimspector_session_windows.variables )
  call setpos( '.', [ 0, 2, 1 ] )
  call feedkeys( "\<CR>", 'xt' )
  call WaitForAssert( {->
        \   AssertMatchist(
        \     [
        \       '- Scope: Locals',
        \       '  - t (Test): {...}',
        \       '   \*- i (int): 1',
        \       '   \*- c (char): 99 ''c''',
        \       '   \*- fffff (float): 0',
        \       '   \*+ another_test (AnotherTest):\( {...}\)\?',
        \     ],
        \     getbufline( winbufnr( g:vimspector_session_windows.variables ),
        \                 1,
        \                 '$' )
        \   )
        \ } )

  " Collapse the 'inexpensive' scope and see that it stays collapsed
  " Exapand - see that the changed value is highlighted
  call win_gotoid( g:vimspector_session_windows.variables )
  call setpos( '.', [ 0, 1, 1 ] )
  call feedkeys( "\<CR>", 'xt' )
  call WaitForAssert( {->
        \   assert_equal(
        \     [
        \       '+ Scope: Locals',
        \     ],
        \     getbufline( winbufnr( g:vimspector_session_windows.variables ),
        \                 1,
        \                 '$' )
        \   )
        \ } )

  " Stays collpased through step
  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 30, 1 )
  call WaitForAssert( {->
        \   assert_equal(
        \     [
        \       '+ Scope: Locals',
        \     ],
        \     getbufline( winbufnr( g:vimspector_session_windows.variables ),
        \                 1,
        \                 '$' )
        \   )
        \ } )

  " Cpptools keeps the same "Locals" scope, so it stays collapsed even throught
  " step-in
  call vimspector#StepInto()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 18, 1 )
  call WaitForAssert( {->
        \   assert_equal(
        \     [
        \       '+ Scope: Locals',
        \     ],
        \     getbufline( winbufnr( g:vimspector_session_windows.variables ),
        \                 1,
        \                 '$' )
        \   )
        \ } )

  call vimspector#test#setup#Reset()
  %bwipe!
endfunction

function! Test_ExpandWatch()
  let fn =  'testdata/cpp/simple/struct.cpp'
  call s:StartDebugging( #{ fn: fn, line: 24, col: 1, launch: #{
        \   configuration: 'run-to-breakpoint'
        \ } } )

  " Make sure the Test t is initialised
  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 26, 1 )

  call win_gotoid( g:vimspector_session_windows.watches )
  call feedkeys( "it\<CR>", 'xt' )

  call WaitForAssert( {->
        \   assert_equal(
        \     [
        \       'Watches: ----',
        \       'Expression: t',
        \       ' *+ Result: {...}',
        \     ],
        \     getbufline( winbufnr( g:vimspector_session_windows.watches ),
        \                 1,
        \                 '$' )
        \   )
        \ } )
  call assert_equal( 'cpp',
                   \ getbufvar(
                   \   winbufnr( g:vimspector_session_windows.watches ),
                   \   '&syntax' ) )

  " Expand
  call win_gotoid( g:vimspector_session_windows.watches )
  call setpos( '.', [ 0, 3, 1 ] )
  call feedkeys( "\<CR>", 'xt' )

  call WaitForAssert( {->
        \   AssertMatchist(
        \     [
        \       'Watches: ----',
        \       'Expression: t',
        \       ' \*- Result: {...}',
        \       '   \*- i (int): 0',
        \       '   \*- c (char): 0 ''\\0\{1,3}''',
        \       '   \*- fffff (float): 0',
        \       '   \*+ another_test (AnotherTest):\( {...}\)\?',
        \     ],
        \     getbufline( winbufnr( g:vimspector_session_windows.watches ),
        \                 1,
        \                 '$' )
        \   )
        \ } )

  " Step - stays expanded
  call vimspector#StepOver()
  call WaitForAssert( {->
        \   AssertMatchist(
        \     [
        \       'Watches: ----',
        \       'Expression: t',
        \       '  - Result: {...}',
        \       '   \*- i (int): 1',
        \       '    - c (char): 0 ''\\0\{1,3}''',
        \       '    - fffff (float): 0',
        \       '    + another_test (AnotherTest):\( {...}\)\?',
        \     ],
        \     getbufline( winbufnr( g:vimspector_session_windows.watches ),
        \                 1,
        \                 '$' )
        \   )
        \ } )

  " Collapse
  call win_gotoid( g:vimspector_session_windows.watches )
  call setpos( '.', [ 0, 3, 1 ] )
  call feedkeys( "\<CR>", 'xt' )
  call WaitForAssert( {->
        \   assert_equal(
        \     [
        \       'Watches: ----',
        \       'Expression: t',
        \       '  + Result: {...}',
        \     ],
        \     getbufline( winbufnr( g:vimspector_session_windows.watches ),
        \                 1,
        \                 '$' )
        \   )
        \ } )

  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 28, 1 )
  call WaitForAssert( {->
        \   assert_equal(
        \     [
        \       'Watches: ----',
        \       'Expression: t',
        \       '  + Result: {...}',
        \     ],
        \     getbufline( winbufnr( g:vimspector_session_windows.watches ),
        \                 1,
        \                 '$' )
        \   )
        \ } )

  call win_gotoid( g:vimspector_session_windows.watches )
  call setpos( '.', [ 0, 3, 1 ] )
  call feedkeys( "\<CR>", 'xt' )
  call WaitForAssert( {->
        \   AssertMatchist(
        \     [
        \       'Watches: ----',
        \       'Expression: t',
        \       '  - Result: {...}',
        \       '    - i (int): 1',
        \       '    - c (char): 99 ''c''',
        \       '    - fffff (float): 0',
        \       '    + another_test (AnotherTest):\( {...}\)\?',
        \     ],
        \     getbufline( winbufnr( g:vimspector_session_windows.watches ),
        \                 1,
        \                 '$' )
        \   )
        \ } )

  call vimspector#test#setup#Reset()
  %bwipe!
endfunction


function Test_EvaluateConsole()
  let fn =  'testdata/cpp/simple/struct.cpp'
  call s:StartDebugging( #{ fn: fn, line: 24, col: 1, launch: #{
        \   configuration: 'run-to-breakpoint'
        \ } } )

  " Make sure the Test t is initialised
  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 26, 1 )
  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 27, 1 )

  VimspectorEval t.i
  call assert_equal( bufnr( 'vimspector.Console' ),
                   \ winbufnr( g:vimspector_session_windows.output ) )
  call WaitForAssert( {->
        \   assert_equal(
        \     [
        \       '1'
        \     ],
        \     getbufline( bufnr( 'vimspector.Console' ), '$', '$' )
        \   )
        \ } )

  let len = getbufinfo( 'vimspector.Console' )[ 0 ].linecount

  call WaitForAssert( {->
        \   assert_equal(
        \     [
        \       'Evaluating: t.i',
        \       '1'
        \     ],
        \     getbufline( bufnr( 'vimspector.Console' ), len-1, '$' )
        \   )
        \ } )
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer(
        \ 'vimspector.Console', len, v:null )

  call vimspector#test#setup#Reset()
  %bwipe!
endfunction


function Test_EvaluatePromptConsole()
  let fn =  'testdata/cpp/simple/struct.cpp'
  call s:StartDebugging( #{ fn: fn, line: 24, col: 1, launch: #{
        \   configuration: 'run-to-breakpoint'
        \ } } )

  " Make sure the Test t is initialised
  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 26, 1 )
  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 27, 1 )

  VimspectorShowOutput
  call assert_equal( bufnr( 'vimspector.Console' ),
                   \ winbufnr( g:vimspector_session_windows.output ) )

  call feedkeys( "it.i\<CR>", 'xt' )
  call WaitForAssert( {->
        \   assert_equal(
        \     [
        \       '1'
        \     ],
        \     getbufline( bufnr( 'vimspector.Console' ), '$', '$' )
        \   )
        \ } )

  let len = getbufinfo( 'vimspector.Console' )[ 0 ].linecount

  call WaitForAssert( {->
        \   assert_equal(
        \     [
        \       '> t.i',
        \       '',
        \       '1'
        \     ],
        \     getbufline( bufnr( 'vimspector.Console' ), len-2, '$' )
        \   )
        \ } )
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer(
        \ 'vimspector.Console', len, v:null )

  call vimspector#test#setup#Reset()
  %bwipe!
endfunction

function! Test_EvaluateFailure()
  call s:StartDebugging()

  " Add a wtch
  call vimspector#AddWatch( 'test' )
  call WaitForAssert( {->
        \   AssertMatchist(
        \     [
        \       'Watches: ----',
        \       'Expression: test',
        \       " *- Result: NameError: name 'test' is not defined",
        \     ],
        \     getbufline( winbufnr( g:vimspector_session_windows.watches ),
        \                 1,
        \                 '$' )
        \   )
        \ } )

  VimspectorEval test
  call assert_equal( bufnr( 'vimspector.Console' ),
                   \ winbufnr( g:vimspector_session_windows.output ) )
  call WaitForAssert( {->
        \   assert_equal(
        \     [
        \       "NameError: name 'test' is not defined"
        \     ],
        \     getbufline( bufnr( 'vimspector.Console' ), '$', '$' )
        \   )
        \ } )

  call vimspector#test#setup#Reset()
  %bwipe!
endfunction
