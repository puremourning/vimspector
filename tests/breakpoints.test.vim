function! SetUp()
  call vimspector#test#setup#SetUpWithMappings( v:none )
endfunction

function! ClearDown()
  call vimspector#test#setup#ClearDown()
endfunction

function! SetUp_Test_Mappings_Are_Added_HUMAN()
  let g:vimspector_enable_mappings = 'HUMAN'
endfunction

function! Test_Mappings_Are_Added_HUMAN()
  call assert_true( hasmapto( 'vimspector#Continue()' ) )
  call assert_false( hasmapto( 'vimspector#Launch()' ) )
  call assert_true( hasmapto( 'vimspector#Stop()' ) )
  call assert_true( hasmapto( 'vimspector#Restart()' ) )
  call assert_true( hasmapto( 'vimspector#ToggleBreakpoint()' ) )
  call assert_true( hasmapto( 'vimspector#AddFunctionBreakpoint' ) )
  call assert_true( hasmapto( 'vimspector#StepOver()' ) )
  call assert_true( hasmapto( 'vimspector#StepInto()' ) )
  call assert_true( hasmapto( 'vimspector#StepOut()' ) )
endfunction

function! SetUp_Test_Mappings_Are_Added_VISUAL_STUDIO()
  let g:vimspector_enable_mappings = 'VISUAL_STUDIO'
endfunction

function! Test_Mappings_Are_Added_VISUAL_STUDIO()
  call assert_true( hasmapto( 'vimspector#Continue()' ) )
  call assert_false( hasmapto( 'vimspector#Launch()' ) )
  call assert_true( hasmapto( 'vimspector#Stop()' ) )
  call assert_true( hasmapto( 'vimspector#Restart()' ) )
  call assert_true( hasmapto( 'vimspector#ToggleBreakpoint()' ) )
  call assert_true( hasmapto( 'vimspector#AddFunctionBreakpoint' ) )
  call assert_true( hasmapto( 'vimspector#StepOver()' ) )
  call assert_true( hasmapto( 'vimspector#StepInto()' ) )
  call assert_true( hasmapto( 'vimspector#StepOut()' ) )
endfunction

function! SetUp_Test_Signs_Placed_Using_API_Are_Shown()
  let g:vimspector_enable_mappings = 'VISUAL_STUDIO'
endfunction

function! Test_Signs_Placed_Using_API_Are_Shown()
  " We need a real file
  edit testdata/cpp/simple/simple.cpp
  call feedkeys( "/printf\<CR>", 'xt' )

  " Set breakpoint
  call vimspector#ToggleBreakpoint()

  call assert_true( exists( '*vimspector#ToggleBreakpoint' ) )
  call vimspector#test#signs#AssertSignGroupSingletonAtLine( 'VimspectorBP',
                                                           \ line( '.' ),
                                                           \ 'vimspectorBP' )

  " Disable breakpoint
  call vimspector#ToggleBreakpoint()
  call vimspector#test#signs#AssertSignGroupSingletonAtLine(
        \ 'VimspectorBP',
        \ line( '.' ),
        \ 'vimspectorBPDisabled' )

  " Remove breakpoint
  call vimspector#ToggleBreakpoint()

  call vimspector#test#signs#AssertSignGroupEmptyAtLine( 'VimspectorBP',
                                                       \ line( '.' ) )

  call vimspector#ClearBreakpoints()
  call vimspector#test#signs#AssertSignGroupEmpty( 'VimspectorBP' )
  call vimspector#test#signs#AssertSignGroupEmpty( 'VimspectorCode' )

  %bwipeout!
endfunction

function! SetUp_Test_Use_Mappings_HUMAN()
  let g:vimspector_enable_mappings = 'HUMAN'
endfunction

function! Test_Use_Mappings_HUMAN()
  lcd testdata/cpp/simple
  edit simple.cpp
  call setpos( '.', [ 0, 15, 1 ] )

  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'simple.cpp', 15, 1 )
  call vimspector#test#signs#AssertSignGroupEmptyAtLine( 'VimspectorBP', 15 )

  " Add the breakpoint
  call feedkeys( "\<F9>", 'xt' )
  call vimspector#test#signs#AssertSignGroupSingletonAtLine( 'VimspectorBP',
                                                           \ 15,
                                                           \ 'vimspectorBP' )

  " Disable the breakpoint
  call feedkeys( "\<F9>", 'xt' )
  call vimspector#test#signs#AssertSignGroupSingletonAtLine(
        \ 'VimspectorBP',
        \ 15,
        \ 'vimspectorBPDisabled' )

  " Delete the breakpoint
  call feedkeys( "\<F9>", 'xt' )
  call vimspector#test#signs#AssertSignGroupEmptyAtLine( 'VimspectorBP', 15 )

  " Add it again
  call feedkeys( "\<F9>", 'xt' )
  call vimspector#test#signs#AssertSignGroupSingletonAtLine(
        \ 'VimspectorBP',
        \ 15,
        \ 'vimspectorBP' )

  " Here we go. Start Debugging
  call feedkeys( "\<F5>", 'xt' )

  call assert_equal( 2, len( gettabinfo() ) )
  let cur_tabnr = tabpagenr()
  call assert_equal( 5, len( gettabinfo( cur_tabnr )[ 0 ].windows ) )

  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'simple.cpp', 15, 1 )

  " Step
  call feedkeys( "\<F10>", 'xt' )

  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'simple.cpp', 16, 1 )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer( 'simple.cp', 16 )
        \ } )

  call vimspector#test#setup#Reset()

  lcd -
  %bwipeout!
endfunction

function! SetUp_Test_StopAtEntry()
  let g:vimspector_enable_mappings = 'HUMAN'
endfunction

function Test_StopAtEntry()
  lcd testdata/cpp/simple
  edit simple.cpp
  call setpos( '.', [ 0, 1, 1 ] )

  " Test stopAtEntry behaviour
  call feedkeys( "\<F5>", 'xt' )

  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'simple.cpp', 15, 1 )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer( 'simple.cpp', 15 )
        \ } )

  call vimspector#test#setup#Reset()

  lcd -
  %bwipeout!
endfunction

function! SetUp_Test_DisableBreakpointWhileDebugging()
  let g:vimspector_enable_mappings = 'HUMAN'
endfunction

function Test_DisableBreakpointWhileDebugging()
  lcd testdata/cpp/simple
  edit simple.cpp
  call setpos( '.', [ 0, 15, 1 ] )

  " Test stopAtEntry behaviour
  call feedkeys( "\<F5>", 'xt' )

  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'simple.cpp', 15, 1 )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer( 'simple.cpp', 15 )
        \ } )
  call vimspector#test#signs#AssertSignGroupEmpty( 'VimspectorBP' )

  call setpos( '.', [ 0, 16, 1 ] )

  " Add the breakpoint
  call feedkeys( "\<F9>", 'xt' )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertSignGroupSingletonAtLine(
          \ 'VimspectorCode',
          \ 16,
          \ 'vimspectorBP' )
        \ } )

  " Remove the breakpoint
  call feedkeys( "\<F9>", 'xt' )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertSignGroupEmptyAtLine( 'VimspectorCode',
                                                          \ 16 )
        \ } )

  " Add the breakpoint
  call feedkeys( "\<F9>", 'xt' )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertSignGroupSingletonAtLine(
           \ 'VimspectorCode',
           \ 16,
           \ 'vimspectorBP' )
        \ } )

  " Run to breakpoint
  call setpos( '.', [ 0, 15, 1 ] )
  call feedkeys( "\<F5>", 'xt' )
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'simple.cpp', 16, 1 )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer( 'simple.cpp', 16 )
        \ } )

  call vimspector#Reset()
  call WaitForAssert( {->
        \ assert_true ( pyxeval( '_vimspector_session._connection is None' ) )
        \ } )
  call WaitForAssert( {->
        \ assert_true( pyxeval( '_vimspector_session._uiTab is None' ) )
        \ } )

  " Check breakpoint is now a user breakpoint
  call setpos( '.', [ bufnr( 'simple.cpp' ), 1, 1 ] )
  call vimspector#test#signs#AssertSignGroupSingletonAtLine(
        \ 'VimspectorBP',
        \ 16,
        \ 'vimspectorBP' )

  " Disable the breakpoint
  call setpos( '.', [ bufnr( 'simple.cpp' ), 16, 1 ] )
  call feedkeys( "\<F9>", 'xt' )
  call vimspector#test#signs#AssertSignGroupSingletonAtLine(
        \ 'VimspectorBP',
        \ 16,
        \ 'vimspectorBPDisabled' )

  " And delete it
  call feedkeys( "\<F9>", 'xt' )
  call vimspector#test#signs#AssertSignGroupEmptyAtLine(
        \ 'VimspectorBP',
        \ 16 )

  call vimspector#ClearBreakpoints()
  call vimspector#test#signs#AssertSignGroupEmpty( 'VimspectorBP' )
  call vimspector#test#signs#AssertSignGroupEmpty( 'VimspectorCode' )

  lcd -
  %bwipeout!
endfunction

function! SetUp_Test_Insert_Code_Above_Breakpoint()
  let g:vimspector_enable_mappings = 'HUMAN'
endfunction

function! Test_Insert_Code_Above_Breakpoint()
  let fn='main.py'
  lcd ../support/test/python/simple_python
  exe 'edit ' . fn
  call setpos( '.', [ 0, 25, 5 ] )

  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 25, 5 )
  call vimspector#test#signs#AssertSignGroupEmptyAtLine( 'VimspectorBP', 25 )

  " Add the breakpoint
  call feedkeys( "\<F9>", 'xt' )
  call vimspector#test#signs#AssertSignGroupSingletonAtLine( 'VimspectorBP',
                                                           \ 25,
                                                           \ 'vimspectorBP' )

  " Insert a line above the breakpoint
  call append( 22, '  # Test' )
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 26, 5 )
  call vimspector#test#signs#AssertSignGroupSingletonAtLine( 'VimspectorBP',
                                                           \ 26,
                                                           \ 'vimspectorBP' )

  " CHeck that we break at the right point
  call setpos( '.', [ 0, 1, 1 ] )
  call vimspector#LaunchWithSettings( { 'configuration': 'run' } )
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 26, 1 )
  call vimspector#Reset()
  call vimspector#test#setup#WaitForReset()

  " Toggle the breakpoint
  call setpos( '.', [ 0, 26, 1 ] )
  call vimspector#test#signs#AssertSignGroupSingletonAtLine( 'VimspectorBP',
                                                           \ 26,
                                                           \ 'vimspectorBP' )
  call feedkeys( "\<F9>", 'xt' )
  call vimspector#test#signs#AssertSignGroupSingletonAtLine(
        \ 'VimspectorBP',
        \ 26,
        \ 'vimspectorBPDisabled' )
  " Delete it
  call feedkeys( "\<F9>", 'xt' )
  call vimspector#test#signs#AssertSignGroupEmptyAtLine( 'VimspectorBP', 26 )

endfunction

function! SetUp_Test_Conditional_Line_Breakpoint()
  let g:vimspector_enable_mappings = 'HUMAN'
endfunction

function! Test_Conditional_Line_Breakpoint()
  lcd testdata/cpp/simple
  edit simple.cpp
  call setpos( '.', [ 0, 16, 1 ] )

  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'simple.cpp', 16, 1 )
  call vimspector#test#signs#AssertSignGroupEmptyAtLine( 'VimspectorBP', 16 )

  " Add the conditional breakpoint
  call feedkeys( "\\\<F9>argc==0\<CR>\<CR>", 'xt' )
  call vimspector#test#signs#AssertSignGroupSingletonAtLine( 'VimspectorBP',
                                                           \ 16,
                                                           \ 'vimspectorBPCond' )

  " Disable the breakpoint
  call feedkeys( "\<F9>", 'xt' )
  call vimspector#test#signs#AssertSignGroupSingletonAtLine(
        \ 'VimspectorBP',
        \ 16,
        \ 'vimspectorBPDisabled' )

  " Delete the breakpoint
  call feedkeys( "\<F9>", 'xt' )
  call vimspector#test#signs#AssertSignGroupEmptyAtLine( 'VimspectorBP', 16 )

  " Add breakpoint using API:
  "  - on line 16 condition which doesn't match
  "  - then an unconditional one on line 9, unconditional
  "  - then on line 17, condition which matches
  call vimspector#ToggleBreakpoint( { 'condition': 'argc == 0' } )
  call vimspector#test#signs#AssertSignGroupSingletonAtLine(
        \ 'VimspectorBP',
        \ 16,
        \ 'vimspectorBPCond' )
  call setpos( '.', [ 0, 9, 1 ] )
  call vimspector#ToggleBreakpoint()
  call vimspector#test#signs#AssertSignGroupSingletonAtLine(
        \ 'VimspectorBP',
        \ 9,
        \ 'vimspectorBP' )

  call setpos( '.', [ 0, 17, 1 ] )
  call vimspector#ToggleBreakpoint( { 'condition': 'argc == 1' } )
  call vimspector#test#signs#AssertSignGroupSingletonAtLine(
        \ 'VimspectorBP',
        \ 17,
        \ 'vimspectorBPCond' )

  call setpos( '.', [ 0, 1, 1 ] )

  " Start debugging
  call vimspector#Continue()
  " break on main
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'simple.cpp', 15, 1 )

  " Ignore non-matching on line 16, break on line 9
  call vimspector#Continue()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'simple.cpp', 9, 1 )

  " Condition matches on line 17
  call vimspector#Continue()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'simple.cpp', 17, 1 )

  call vimspector#test#setup#Reset()

  lcd -
  %bwipeout!
endfunction

function! SetUp_Test_Conditional_Line_Breakpoint_Hit()
  let g:vimspector_enable_mappings = 'HUMAN'
endfunction

function! Test_Conditional_Line_Breakpoint_Hit()
  let fn = '../support/test/python/simple_python/main.py'
  exe 'edit' fn
  call setpos( '.', [ 0, 14, 1 ] )

  " Add the conditional breakpoint (3 times)
  call feedkeys( "\\\<F9>\<CR>3\<CR>", 'xt' )
  call vimspector#test#signs#AssertSignGroupSingletonAtLine(
        \ 'VimspectorBP',
        \ 14,
        \ 'vimspectorBPCond' )

  call vimspector#LaunchWithSettings( { 'configuration': 'run' } )
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 14, 1 )

  " difficult to check if we really did run 3 times, so just use the watch
  " window (also, tests the watch window!)
  call vimspector#AddWatch( 'i' )
  call WaitForAssert( {->
        \       assert_equal( [ '  - Result: 2' ],
        \                     getbufline( 'vimspector.Watches', '$' ) )
        \ } )


  call vimspector#test#setup#Reset()
  %bwipeout!
endfunction

function! Test_Function_Breakpoint()
  lcd testdata/cpp/simple
  edit simple.cpp
  call vimspector#AddFunctionBreakpoint( 'foo' )
  call vimspector#Launch()
  " break on main
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'simple.cpp', 15, 1 )
  call vimspector#Continue()
  " break on func
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'simple.cpp', 9, 1 )
  call vimspector#test#setup#Reset()
  %bwipeout!
endfunction

function! Test_Function_Breakpoint_Condition()
  lcd testdata/cpp/simple
  edit simple.cpp
  call vimspector#AddFunctionBreakpoint( 'foo', { 'condition': '1' } )
  call vimspector#Launch()
  " break on main
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'simple.cpp', 15, 1 )
  call vimspector#Continue()
  " break on func
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'simple.cpp', 9, 1 )
  call vimspector#test#setup#Reset()
  %bwipeout!
endfunction

" Can't find an adapter that supports conditional function breakpoints which are
" probably pretty niche anyway
"
" function! Test_Function_Breakpoint_Condition_False()
"   lcd testdata/cpp/simple
"   edit simple.cpp
"
"   call vimspector#AddFunctionBreakpoint( 'foo', { 'condition': '0' } )
"   call setpos( '.', [ 0, 17, 1 ] )
"   call vimspector#ToggleBreakpoint()
"   call vimspector#Launch()
"   " break on main
"   call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'simple.cpp', 15, 1 )
"   call vimspector#Continue()
"
"   " doesn't break in func, break on line 17
"   call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'simple.cpp', 17, 1 )
"   call vimspector#test#setup#Reset()
"   %bwipeout!
"   throw "xfail cpptools doesn't seem to honour conditions on function bps"
" endfunction
