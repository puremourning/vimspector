let s:fn='../support/test/python/simple_python/main.py'

function! SetUp()
  call vimspector#test#setup#SetUpWithMappings( 'HUMAN' )
  let g:vimspector_variables_display_mode = 'full'

  let s:setup_func_line = FunctionBreakOnBrace() ? 17 : 18
endfunction

function! TearDown()
  call vimspector#test#setup#TearDown()
endfunction

function! ConsoleBufferName()
  " return 'vimspector.Console'

  let session_id = py3eval( '_vimspector_session.session_id' )
  return 'vimspector.Console[' .. session_id .. ']'
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
  call SkipNeovim()
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
        \       '+ Scope: Registers',
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
        \   AssertMatchList(
        \     [
        \       '- Scope: Locals',
        \       ' \*- t (Test): {...}',
        \       '   \*- i (int): 0',
        \       '   \*- c (char): 0 ''\\0\{1,3}''',
        \       '   \*- fffff (float): 0',
        \       '   \*+ another_test (AnotherTest):\( {...}\)\?',
        \       '+ Scope: Registers',
        \     ],
        \     getbufline( winbufnr( g:vimspector_session_windows.variables ),
        \                 1,
        \                 '$' )
        \   )
        \ } )

  " Step - stays expanded
  call vimspector#StepOver()
  call WaitForAssert( {->
        \   AssertMatchList(
        \     [
        \       '- Scope: Locals',
        \       '  - t (Test): {...}',
        \       '   \*- i (int): 1',
        \       '    - c (char): 0 ''\\0\{1,3}''',
        \       '    - fffff (float): 0',
        \       '    + another_test (AnotherTest):\( {...}\)\?',
        \       '+ Scope: Registers',
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
        \       '+ Scope: Registers',
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
        \       '+ Scope: Registers',
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
        \   AssertMatchList(
        \     [
        \       '- Scope: Locals',
        \       '  - t (Test): {...}',
        \       '   \*- i (int): 1',
        \       '   \*- c (char): 99 ''c''',
        \       '   \*- fffff (float): 0',
        \       '   \*+ another_test (AnotherTest):\( {...}\)\?',
        \       '+ Scope: Registers',
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
        \       '+ Scope: Registers',
        \     ],
        \     getbufline( winbufnr( g:vimspector_session_windows.variables ),
        \                 1,
        \                 '$' )
        \   )
        \ } )

  " Stays collapsed through step
  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 30, 1 )
  call WaitForAssert( {->
        \   assert_equal(
        \     [
        \       '+ Scope: Locals',
        \       '+ Scope: Registers',
        \     ],
        \     getbufline( winbufnr( g:vimspector_session_windows.variables ),
        \                 1,
        \                 '$' )
        \   )
        \ } )

  " Cpptools keeps the same "Locals" scope, so it stays collapsed even through
  " we step-in
  call vimspector#StepInto()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, s:setup_func_line, 1 )
  call WaitForAssert( {->
        \   assert_equal(
        \     [
        \       '+ Scope: Locals',
        \       '+ Scope: Registers',
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
  call SkipNeovim()
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
        \   AssertMatchList(
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
        \   AssertMatchList(
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
        \   AssertMatchList(
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
  call assert_equal( bufnr( ConsoleBufferName() ),
                   \ winbufnr( g:vimspector_session_windows.output ) )
  call WaitForAssert( {->
        \   assert_equal(
        \     [
        \       '1'
        \     ],
        \     getbufline( bufnr( ConsoleBufferName() ), '$', '$' )
        \   )
        \ } )

  let len = getbufinfo( ConsoleBufferName() )[ 0 ].linecount

  call WaitForAssert( {->
        \   assert_equal(
        \     [
        \       'Evaluating: t.i',
        \       '1'
        \     ],
        \     getbufline( bufnr( ConsoleBufferName() ), len-1, '$' )
        \   )
        \ } )
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer(
        \ ConsoleBufferName(), len, v:null )

  call vimspector#test#setup#Reset()
  %bwipe!
endfunction


function Test_EvaluateInput()
  let fn =  'testdata/cpp/simple/struct.cpp'
  call s:StartDebugging( #{ fn: fn, line: 24, col: 1, launch: #{
        \   configuration: 'run-to-breakpoint'
        \ } } )

  " Make sure the Test t is initialised
  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 26, 1 )
  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 27, 1 )

  VimspectorEval (int) printf("hello")

  call assert_equal( bufnr( ConsoleBufferName() ),
                   \ winbufnr( g:vimspector_session_windows.output ) )
  call WaitForAssert( {->
        \   assert_equal(
        \     [
        \       'Evaluating: (int) printf("hello")',
        \       '5'
        \     ],
        \     GetBufLine( bufnr( ConsoleBufferName() ), -1 )
        \   )
        \ } )
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer(
        \ ConsoleBufferName(),
        \ getbufinfo( ConsoleBufferName() )[ 0 ].linecount,
        \ v:null )

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
  call assert_equal( bufnr( ConsoleBufferName() ),
                   \ winbufnr( g:vimspector_session_windows.output ) )

  call feedkeys( "it.i\<CR>", 'xt' )
  call WaitForAssert( {->
        \   assert_equal(
        \     [
        \       '1'
        \     ],
        \     getbufline( bufnr( ConsoleBufferName() ), '$', '$' )
        \   )
        \ } )

  let len = getbufinfo( ConsoleBufferName() )[ 0 ].linecount

  call WaitForAssert( {->
        \   assert_equal(
        \     [
        \       '> t.i',
        \       '',
        \       '1'
        \     ],
        \     getbufline( bufnr( ConsoleBufferName() ), len-2, '$' )
        \   )
        \ } )
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer(
        \ ConsoleBufferName(), len, v:null )

  call vimspector#test#setup#Reset()
  %bwipe!
endfunction

function! Test_EvaluateFailure()
  call s:StartDebugging()

  " Add a wtch
  call vimspector#AddWatch( 'test' )
  call WaitForAssert( {->
        \   AssertMatchList(
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
  call assert_equal( bufnr( ConsoleBufferName() ),
                   \ winbufnr( g:vimspector_session_windows.output ) )
  call WaitForAssert( {->
        \   assert_equal(
        \     [
        \       "NameError: name 'test' is not defined"
        \     ],
        \     getbufline( bufnr( ConsoleBufferName() ), '$', '$' )
        \   )
        \ } )

  call vimspector#test#setup#Reset()
  %bwipe!
endfunction

function! Test_VariableEval()
  call SkipNeovim()
  let fn =  'testdata/cpp/simple/struct.cpp'
  call s:StartDebugging( #{ fn: fn, line: 24, col: 1, launch: #{
        \   configuration: 'run-to-breakpoint'
        \ } } )

  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 26, 1 )

  " leader is ,
  xmap <buffer> <Leader>d <Plug>VimspectorBalloonEval
  nmap <buffer> <Leader>d <Plug>VimspectorBalloonEval

  "evaluate the prev line
  call setpos( '.', [ 0, 24, 8 ] )
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 24, 8 )
  call feedkeys( ',d', 'xt' )

  call WaitForAssert( {->
        \   AssertNotNull( g:vimspector_session_windows.eval )
        \ } )

  call WaitForAssert( {->
        \   AssertMatchList(
        \     [
        \       '{...}',
        \       ' - i: 0',
        \       ' - c: 0 ''\\0\{1,3}''',
        \       ' - fffff: 0',
        \       ' + another_test: ',
        \     ],
        \     getbufline( winbufnr( g:vimspector_session_windows.eval ),
        \                 1,
        \                 '$' )
        \   )
        \ } )

  "Close
  call feedkeys( "\<Esc>", 'xt' )

  call WaitForAssert( {->
        \ AssertNull( g:vimspector_session_windows.eval )
        \ } )

  " test selection
  call setpos( '.', [ 0, 24, 8 ] )
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 24, 8 )

  call feedkeys( 'viw,d', 'xt' )

  call WaitForAssert( {->
        \ AssertNotNull( g:vimspector_session_windows.eval )
        \ } )

  call WaitForAssert( {->
        \   AssertMatchList(
        \     [
        \       '{...}',
        \       ' - i: 0',
        \       ' - c: 0 ''\\0\{1,3}''',
        \       ' - fffff: 0',
        \       ' + another_test: ',
        \     ],
        \     getbufline( winbufnr( g:vimspector_session_windows.eval ),
        \                 1,
        \                 '$' )
        \   )
        \ } )

  "Close
  call feedkeys( "\<Esc>", 'xt' )

  call WaitForAssert( {->
        \ AssertNull( g:vimspector_session_windows.eval )
        \ } )

  " Get back to normal mode
  call feedkeys( "\<Esc>", 'xt' )

  " Evaluation error
  call setpos( '.', [ 0, 25, 1 ] )
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 25, 1 )
  call feedkeys( ',d', 'xt' )

  call WaitForAssert( {->
        \   AssertNotNull( g:vimspector_session_windows.eval )
        \ } )

  call WaitForAssert( {->
        \   AssertMatchList(
        \     [
        \       'Evaluation error',
        \     ],
        \     getbufline( winbufnr( g:vimspector_session_windows.eval ),
        \                 1,
        \                 '$' )
        \   )
        \ } )

  "Close
  call feedkeys( "\<Esc>", 'xt' )

  call WaitForAssert( {->
        \ AssertNull( g:vimspector_session_windows.eval )
        \ } )

  call vimspector#test#setup#Reset()
  %bwipe!
endfunction

function! Test_VariableEvalExpand()
  call SkipNeovim()
  let fn =  'testdata/cpp/simple/struct.cpp'
  call s:StartDebugging( #{ fn: fn, line: 24, col: 1, launch: #{
        \   configuration: 'run-to-breakpoint'
        \ } } )

  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 26, 1 )

  " leader is ,
  xmap <buffer> <Leader>d <Plug>VimspectorBalloonEval
  nmap <buffer> <Leader>d <Plug>VimspectorBalloonEval

  "evaluate the prev line
  call setpos( '.', [ 0, 24, 8 ] )
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 24, 8 )
  call feedkeys( ',d', 'xt' )

  call WaitForAssert( {->
        \ AssertNotNull( g:vimspector_session_windows.eval )
        \ } )

  call WaitForAssert( {->
        \   AssertMatchList(
        \     [
        \       '{...}',
        \       ' - i: 0',
        \       ' - c: 0 ''\\0\{1,3}''',
        \       ' - fffff: 0',
        \       ' + another_test: ',
        \     ],
        \     getbufline( winbufnr( g:vimspector_session_windows.eval ),
        \                 1,
        \                 '$' )
        \   )
        \ } )

  " Expand
  call feedkeys( "jjjj\<CR>", 'xt' )

  call WaitForAssert( {->
        \   AssertMatchList(
        \     [
        \       '{...}',
        \       ' - i: 0',
        \       ' - c: 0 ''\\0\{1,3}''',
        \       ' - fffff: 0',
        \       ' - another_test: ',
        \       '   - choo: 0 ''\\0\{1,3}''',
        \       '   + ints: '
        \     ],
        \     getbufline( winbufnr( g:vimspector_session_windows.eval ),
        \                 1,
        \                 '$' )
        \   )
        \ } )

  "Collapse
  call feedkeys( "\<CR>", 'xt' )

  call WaitForAssert( {->
        \   AssertMatchList(
        \     [
        \       '{...}',
        \       ' - i: 0',
        \       ' - c: 0 ''\\0\{1,3}''',
        \       ' - fffff: 0',
        \       ' + another_test: ',
        \     ],
        \     getbufline( winbufnr( g:vimspector_session_windows.eval ),
        \                 1,
        \                 '$' )
        \   )
        \ } )

  "Close
  call feedkeys( "\<Esc>", 'xt' )

  call WaitForAssert( {->
        \ AssertNull( g:vimspector_session_windows.eval )
        \ } )

  call vimspector#test#setup#Reset()
  %bwipe!
endfunction

function! Test_SetVariableValue_Local()
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
        \       '+ Scope: Registers',
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
        \   AssertMatchList(
        \     [
        \       '- Scope: Locals',
        \       ' \*- t (Test): {...}',
        \       '   \*- i (int): 0',
        \       '   \*- c (char): 0 ''\\0\{1,3}''',
        \       '   \*- fffff (float): 0',
        \       '   \*+ another_test (AnotherTest):\( {...}\)\?',
        \       '+ Scope: Registers',
        \     ],
        \     getbufline( winbufnr( g:vimspector_session_windows.variables ),
        \                 1,
        \                 '$' )
        \   )
        \ } )

  call setpos( '.', [ 0, 3, 1 ] )

  " We can't just fire the keys to the inpit prompt because we use inputsave()
  " and inputrestore(), so mock that out and fire away.
  py3 <<EOF
from unittest import mock
with mock.patch( 'vimspector.utils.InputSave' ):
  vim.eval( 'feedkeys( "\<C-CR>\<C-u>100\<CR>", "xt" )' )
EOF

  call WaitForAssert( {->
        \   AssertMatchList(
        \     [
        \       '- Scope: Locals',
        \       ' \*- t (Test): {...}',
        \       '   \*- i (int): 100',
        \       '   \*- c (char): 0 ''\\0\{1,3}''',
        \       '   \*- fffff (float): 0',
        \       '   \*+ another_test (AnotherTest):\( {...}\)\?',
        \       '+ Scope: Registers',
        \     ],
        \     getbufline( winbufnr( g:vimspector_session_windows.variables ),
        \                 1,
        \                 '$' )
        \   )
        \ } )

  " Now set it via the more comforable scripting interface
  call vimspector#SetVariableValue( '1234' )

  call WaitForAssert( {->
        \   AssertMatchList(
        \     [
        \       '- Scope: Locals',
        \       ' \*- t (Test): {...}',
        \       '   \*- i (int): 1234',
        \       '   \*- c (char): 0 ''\\0\{1,3}''',
        \       '   \*- fffff (float): 0',
        \       '   \*+ another_test (AnotherTest):\( {...}\)\?',
        \       '+ Scope: Registers',
        \     ],
        \     getbufline( winbufnr( g:vimspector_session_windows.variables ),
        \                 1,
        \                 '$' )
        \   )
        \ } )

  " Something fails
  call vimspector#SetVariableValue( 'this is invalid' )

  call WaitForAssert( {->
        \   AssertMatchList(
        \     [
        \       '- Scope: Locals',
        \       ' \*- t (Test): {...}',
        \       '   \*- i (int): 1234',
        \       '   \*- c (char): 0 ''\\0\{1,3}''',
        \       '   \*- fffff (float): 0',
        \       '   \*+ another_test (AnotherTest):\( {...}\)\?',
        \       '+ Scope: Registers',
        \     ],
        \     getbufline( winbufnr( g:vimspector_session_windows.variables ),
        \                 1,
        \                 '$' )
        \   )
        \ } )


  call vimspector#test#setup#Reset()
  %bwipe!
endfunction

function! Test_SetVariableValue_Watch()
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
        \   AssertMatchList(
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

  call setpos( '.', [ 0, 4, 1 ] )

  " We can't just fire the keys to the inpit prompt because we use inputsave()
  " and inputrestore(), so mock that out and fire away.
  " Note: mapleder is ,
  py3 <<EOF
from unittest import mock
with mock.patch( 'vimspector.utils.InputSave' ):
  vim.eval( 'feedkeys( ",\<CR>\<C-u>100\<CR>", "xt" )' )
EOF


  call WaitForAssert( {->
        \   AssertMatchList(
        \     [
        \       'Watches: ----',
        \       'Expression: t',
        \       ' \*- Result: {...}',
        \       '   \*- i (int): 100',
        \       '   \*- c (char): 0 ''\\0\{1,3}''',
        \       '   \*- fffff (float): 0',
        \       '   \*+ another_test (AnotherTest):\( {...}\)\?',
        \     ],
        \     getbufline( winbufnr( g:vimspector_session_windows.watches ),
        \                 1,
        \                 '$' )
        \   )
        \ } )

  " Now set it via the more comforable scripting interface
  call vimspector#SetVariableValue( '1234' )

  call WaitForAssert( {->
        \   AssertMatchList(
        \     [
        \       'Watches: ----',
        \       'Expression: t',
        \       ' \*- Result: {...}',
        \       '   \*- i (int): 1234',
        \       '   \*- c (char): 0 ''\\0\{1,3}''',
        \       '   \*- fffff (float): 0',
        \       '   \*+ another_test (AnotherTest):\( {...}\)\?',
        \     ],
        \     getbufline( winbufnr( g:vimspector_session_windows.watches ),
        \                 1,
        \                 '$' )
        \   )
        \ } )

  call vimspector#test#setup#Reset()
  %bwipe!
endfunction

function! Test_SetVariableValue_Balloon()
  call SkipNeovim()
  let fn =  'testdata/cpp/simple/struct.cpp'
  call s:StartDebugging( #{ fn: fn, line: 24, col: 1, launch: #{
        \   configuration: 'run-to-breakpoint'
        \ } } )

  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 26, 1 )

  " leader is ,
  xmap <buffer> <Leader>d <Plug>VimspectorBalloonEval
  nmap <buffer> <Leader>d <Plug>VimspectorBalloonEval

  "evaluate the prev line
  call setpos( '.', [ 0, 24, 8 ] )
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 24, 8 )
  call feedkeys( ',d', 'xt' )

  call WaitForAssert( {->
        \   AssertNotNull( g:vimspector_session_windows.eval )
        \ } )

  call WaitForAssert( {->
        \   AssertMatchList(
        \     [
        \       '{...}',
        \       ' - i: 0',
        \       ' - c: 0 ''\\0\{1,3}''',
        \       ' - fffff: 0',
        \       ' + another_test: ',
        \     ],
        \     getbufline( winbufnr( g:vimspector_session_windows.eval ),
        \                 1,
        \                 '$' )
        \   )
        \ } )

  " Move down to the ffff line

  call feedkeys( 'jjj', 'xt' )
  " We can't just fire the keys to the inpit prompt because we use inputsave()
  " and inputrestore(), so mock that out and fire away.
  " Note: mapleder is ,
  py3 <<EOF
from unittest import mock
with mock.patch( 'vimspector.utils.InputSave' ):
  vim.eval( 'feedkeys( "\<C-CR>\<C-u>100\<CR>", "xt" )' )
EOF

  call WaitForAssert( {->
        \   AssertMatchList(
        \     [
        \       '{...}',
        \       ' - i: 0',
        \       ' - c: 0 ''\\0\{1,3}''',
        \       ' - fffff: 100',
        \       ' + another_test: ',
        \     ],
        \     getbufline( winbufnr( g:vimspector_session_windows.eval ),
        \                 1,
        \                 '$' )
        \   )
        \ } )

  call vimspector#test#setup#Reset()
  %bwipe!
endfunction
