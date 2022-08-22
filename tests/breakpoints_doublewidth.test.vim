let s:init = 0

function! SetUp()
  set ambiwidth=double
  call vimspector#test#setup#SetUpWithMappings( v:null )
  call ThisTestIsFlaky()

  if ! s:init
    let s:break_main_line = FunctionBreakOnBrace() ? 14 : 15
    let s:break_foo_line = FunctionBreakOnBrace() ? 6 : 9
    let s:init = 1
  endif
  
  " legacy test with disable breakpoint behaviour
  let g:vimspector_toggle_disables_breakpoint = 1
endfunction

function! TearDown()
  call vimspector#test#setup#TearDown()
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
                                                           \ 'vimspectorBP',
                                                           \ 9 )

  " Disable breakpoint
  call vimspector#ToggleBreakpoint()
  call vimspector#test#signs#AssertSignGroupSingletonAtLine(
        \ 'VimspectorBP',
        \ line( '.' ),
        \ 'vimspectorBPDisabled',
        \ 9 )

  " Remove breakpoint
  call vimspector#ToggleBreakpoint()

  call vimspector#test#signs#AssertSignGroupEmptyAtLine( 'VimspectorBP',
                                                       \ line( '.' ) )

  call vimspector#ClearBreakpoints()
  call vimspector#test#signs#AssertSignGroupEmpty( 'VimspectorBP' )
  call vimspector#test#signs#AssertSignGroupEmpty( 'VimspectorBP' )

  call vimspector#test#setup#Reset()
  %bwipeout!
endfunction

function! SetUp_Test_Use_Mappings_HUMAN()
  let g:vimspector_enable_mappings = 'HUMAN'
endfunction

function! Test_Use_Mappings_HUMAN()
  call SkipNeovim()
  lcd testdata/cpp/simple
  edit simple.cpp
  call setpos( '.', [ 0, 16, 1 ] )

  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'simple.cpp', 16, 1 )
  call vimspector#test#signs#AssertSignGroupEmptyAtLine( 'VimspectorBP', 16 )

  " Add the breakpoint
  call feedkeys( "\<F9>", 'xt' )
  call vimspector#test#signs#AssertSignGroupSingletonAtLine( 'VimspectorBP',
                                                           \ 16,
                                                           \ 'vimspectorBP',
                                                           \ 9 )

  " Disable the breakpoint
  call feedkeys( "\<F9>", 'xt' )
  call vimspector#test#signs#AssertSignGroupSingletonAtLine(
        \ 'VimspectorBP',
        \ 16,
        \ 'vimspectorBPDisabled',
        \ 9 )

  " Delete the breakpoint
  call feedkeys( "\<F9>", 'xt' )
  call vimspector#test#signs#AssertSignGroupEmptyAtLine( 'VimspectorBP', 16 )

  " Add it again
  call feedkeys( "\<F9>", 'xt' )
  call vimspector#test#signs#AssertSignGroupSingletonAtLine(
        \ 'VimspectorBP',
        \ 16,
        \ 'vimspectorBP',
        \ 9 )

  " Here we go. Start Debugging
  call feedkeys( "\<F5>", 'xt' )

  call assert_equal( 2, len( gettabinfo() ) )
  let cur_tabnr = tabpagenr()
  call assert_equal( 5, len( gettabinfo( cur_tabnr )[ 0 ].windows ) )

  " break on main
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'simple.cpp', s:break_main_line, 1 )

  " Cont
  " Here we go. Start Debugging
  call feedkeys( "\<F5>", 'xt' )

  " breakpoint
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'simple.cpp', 16, 1 )

  " Step
  call feedkeys( "\<F10>", 'xt' )

  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'simple.cpp', 17, 1 )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer( 'simple.cpp', 17 )
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

  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'simple.cpp', s:break_main_line, 1 )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer( 'simple.cpp', s:break_main_line )
        \ } )

  call vimspector#test#setup#Reset()

  lcd -
  %bwipeout!
endfunction

function! SetUp_Test_DisableBreakpointWhileDebugging()
  let g:vimspector_enable_mappings = 'HUMAN'
endfunction

function Test_DisableBreakpointWhileDebugging()
  call SkipNeovim()
  lcd testdata/cpp/simple
  edit simple.cpp
  call setpos( '.', [ 0, 15, 1 ] )

  " Test stopAtEntry behaviour
  call feedkeys( "\<F5>", 'xt' )

  call vimspector#test#signs#AssertCursorIsAtLineInBuffer(
        \ 'simple.cpp',
        \ s:break_main_line, 1 )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer(
          \ 'simple.cpp',
          \ s:break_main_line )
        \ } )
  call vimspector#test#signs#AssertSignGroupEmpty( 'VimspectorBP' )

  call setpos( '.', [ 0, 16, 1 ] )

  " Add the breakpoint
  call feedkeys( "\<F9>", 'xt' )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertSignGroupSingletonAtLine(
          \ 'VimspectorBP',
          \ 16,
          \ 'vimspectorBP',
          \ 9 )
        \ } )

  " disable the breakpoint
  call feedkeys( "\<F9>", 'xt' )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertSignGroupSingletonAtLine(
          \ 'VimspectorBP',
          \ 16,
          \ 'vimspectorBPDisabled',
          \ 9 )
        \ } )

  " Delete the breakpoint
  call feedkeys( "\<F9>", 'xt' )
  call assert_true( empty( vimspector#GetBreakpointsAsQuickFix() ),
                  \ vimspector#GetBreakpointsAsQuickFix() )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertSignGroupEmptyAtLine( 'VimspectorBP',
                                                          \ 16 )
        \ } )

  call setpos( '.', [ 0, 1, 1 ] )
  call vimspector#SetLineBreakpoint( 'simple.cpp', 16 )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertSignGroupSingletonAtLine(
           \ 'VimspectorBP',
           \ 16,
           \ 'vimspectorBP',
           \ 9 )
        \ } )

  " Run to breakpoint
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
        \ 'vimspectorBP',
        \ 9 )

  " Disable the breakpoint
  call setpos( '.', [ bufnr( 'simple.cpp' ), 16, 1 ] )
  call feedkeys( "\<F9>", 'xt' )
  call vimspector#test#signs#AssertSignGroupSingletonAtLine(
        \ 'VimspectorBP',
        \ 16,
        \ 'vimspectorBPDisabled',
        \ 9 )

  " And delete it
  call feedkeys( "\<F9>", 'xt' )
  call vimspector#test#signs#AssertSignGroupEmptyAtLine(
        \ 'VimspectorBP',
        \ 16 )

  call vimspector#ClearBreakpoints()
  call vimspector#test#signs#AssertSignGroupEmpty( 'VimspectorBP' )
  call vimspector#test#signs#AssertSignGroupEmpty( 'VimspectorBP' )

  lcd -
  call vimspector#test#setup#Reset()
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
                                                           \ 'vimspectorBP',
                                                           \ 9 )

  " Insert a line above the breakpoint
  call append( 22, '  # Test' )
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 26, 5 )
  call vimspector#test#signs#AssertSignGroupSingletonAtLine( 'VimspectorBP',
                                                           \ 26,
                                                           \ 'vimspectorBP',
                                                           \ 9 )

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
                                                           \ 'vimspectorBP',
                                                           \ 9 )
  call feedkeys( "\<F9>", 'xt' )
  call vimspector#test#signs#AssertSignGroupSingletonAtLine(
        \ 'VimspectorBP',
        \ 26,
        \ 'vimspectorBPDisabled',
        \ 9 )
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

  " Add the conditional breakpoint (, is mapleader)
  call feedkeys( ",\<F9>argc==0\<CR>\<CR>\<CR>", 'xt' )
  call vimspector#test#signs#AssertSignGroupSingletonAtLine( 'VimspectorBP',
                                                           \ 16,
                                                           \ 'vimspectorBPCond',
                                                           \ 9 )

  " Disable the breakpoint
  call feedkeys( "\<F9>", 'xt' )
  call vimspector#test#signs#AssertSignGroupSingletonAtLine(
        \ 'VimspectorBP',
        \ 16,
        \ 'vimspectorBPDisabled',
        \ 9 )

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
        \ 'vimspectorBPCond',
        \ 9 )
  call setpos( '.', [ 0, 9, 1 ] )
  call vimspector#ToggleBreakpoint()
  call vimspector#test#signs#AssertSignGroupSingletonAtLine(
        \ 'VimspectorBP',
        \ 9,
        \ 'vimspectorBP',
        \ 9 )

  call setpos( '.', [ 0, 17, 1 ] )
  call vimspector#ToggleBreakpoint( { 'condition': 'argc == 1' } )
  call vimspector#test#signs#AssertSignGroupSingletonAtLine(
        \ 'VimspectorBP',
        \ 17,
        \ 'vimspectorBPCond',
        \ 9 )

  call setpos( '.', [ 0, 1, 1 ] )

  " Start debugging
  call vimspector#Continue()
  " break on main
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'simple.cpp', s:break_main_line, 1 )

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
  call ThisTestIsFlaky()

  let fn = '../support/test/python/simple_python/main.py'
  exe 'edit' fn
  call setpos( '.', [ 0, 14, 1 ] )

  " Add the conditional breakpoint (3 times) (, is mapleader)
  call feedkeys( ",\<F9>\<CR>3\<CR>\<CR>", 'xt' )
  call vimspector#test#signs#AssertSignGroupSingletonAtLine(
        \ 'VimspectorBP',
        \ 14,
        \ 'vimspectorBPCond',
        \ 9 )

  call vimspector#LaunchWithSettings( { 'configuration': 'run' } )
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 14, 1 )

  " difficult to check if we really did run 3 times, so just use the watch
  " window (also, tests the watch window!)
  call vimspector#AddWatch( 'i' )
  call WaitForAssert( {->
        \       assert_equal( [ ' *- Result: 2' ],
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
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'simple.cpp', s:break_main_line, 1 )
  call vimspector#Continue()
  " break on func
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'simple.cpp', s:break_foo_line, 1 )
  call vimspector#test#setup#Reset()
  lcd -
  %bwipeout!
endfunction

function! Test_Function_Breakpoint_Condition()
  lcd testdata/cpp/simple
  edit simple.cpp
  call vimspector#AddFunctionBreakpoint( 'foo', { 'condition': '1' } )
  call vimspector#Launch()
  " break on main
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'simple.cpp', s:break_main_line, 1 )
  call vimspector#Continue()
  " break on func
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'simple.cpp', s:break_foo_line, 1 )
  call vimspector#test#setup#Reset()
  lcd -
  %bwipeout!
endfunction

function! Test_Logpoint()
  lcd testdata/cpp/simple

  edit printer.cpp
  call vimspector#SetLineBreakpoint(
        \ 'printer.cpp',
        \ 14,
        \ { 'logMessage': 'i is {i}' } )
  call vimspector#SetLineBreakpoint( 'printer.cpp', 20 )

  call vimspector#test#signs#AssertSignGroupSingletonAtLine(
        \ 'VimspectorBP',
        \ 14,
        \ 'vimspectorBPLog',
        \ 9 )

  call vimspector#LaunchWithSettings( { 'configuration': 'CodeLLDB' } )
  " CodeLLDB returns different columns on mac and linux, of course
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer(
        \ 'printer.cpp',
        \ 20,
        \ v:null )

  " FIXME: Display of braekpoints while debugging is kinda broken. we should
  " really base it off the user-entered breakpoints and show that this is a
  " logpoint not a breakpoint
  call vimspector#test#signs#AssertSignGroupSingletonAtLine(
        \ 'VimspectorBP',
        \ 14,
        \ 'vimspectorBPLog',
        \ 9 )


  VimspectorShowOutput
  call assert_equal( bufnr( 'vimspector.Console' ),
                   \ winbufnr( g:vimspector_session_windows.output ) )
  call WaitForAssert( {->
        \   AssertMatchList(
        \     [
          \       'i is 1',
          \       'i is 3',
          \       'i is 5',
          \       'i is 7',
        \     ],
        \     GetBufLine( winbufnr( g:vimspector_session_windows.output ), -3 )
        \   )
        \ } )


  call vimspector#test#setup#Reset()
  lcd -
  %bwipeout!
endfunction

function! Test_Conditional_Logpoint()
  lcd testdata/cpp/simple

  edit printer.cpp
  call vimspector#SetLineBreakpoint(
        \ 'printer.cpp',
        \ 14,
        \ { 'condition': 'i<4', 'logMessage': 'i is {i}' } )
  call vimspector#SetLineBreakpoint( 'printer.cpp', 20 )

  call vimspector#test#signs#AssertSignGroupSingletonAtLine(
        \ 'VimspectorBP',
        \ 14,
        \ 'vimspectorBPLog',
        \ 9 )

  call vimspector#LaunchWithSettings( { 'configuration': 'CodeLLDB' } )
  " CodeLLDB returns different columns on mac and linux, of course
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer(
        \ 'printer.cpp',
        \ 20,
        \ v:null )

  VimspectorShowOutput
  call assert_equal( bufnr( 'vimspector.Console' ),
                   \ winbufnr( g:vimspector_session_windows.output ) )
  call WaitForAssert( {->
        \   AssertMatchList(
        \     [
          \       'i is 1',
          \       'i is 3',
        \     ],
        \     GetBufLine( winbufnr( g:vimspector_session_windows.output ), -1 )
        \   )
        \ } )


  call vimspector#test#setup#Reset()
  lcd -
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
"   call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'simple.cpp', "   s:break_main_line, 1 )
"   call vimspector#Continue()
"
"   " doesn't break in func, break on line 17
"   call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'simple.cpp', 17, 1 )
"   call vimspector#test#setup#Reset()
"   %bwipeout!
"   throw "xfail cpptools doesn't seem to honour conditions on function bps"
" endfunction

function! s:CheckBreakpointView( expected )
  call WaitForAssert( {->
          \ AssertMatchList( a:expected,
          \ GetBufLine(
                      \ winbufnr( g:vimspector_session_windows.breakpoints ),
                      \ 1,
                      \ '$' ) ) } )
endfunction

function! Test_ListBreakpoints()
  lcd testdata/cpp/simple
  edit simple.cpp
  call setpos( '.', [ 0, 15, 1 ] )
  let main_win_id = win_getid()

  call vimspector#ListBreakpoints()
  " buffer is never actually empty
  call s:CheckBreakpointView( [ '' ] )
  " Cursor jumps to the breakpoint window
  call assert_equal( win_getid(), g:vimspector_session_windows.breakpoints )

  call win_gotoid( main_win_id )
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'simple.cpp', 15, 1 )

  call vimspector#ToggleBreakpoint()
  " call vimspector#ListBreakpoints()
  call s:CheckBreakpointView( [
        \ 'simple.cpp:15 Line breakpoint - ENABLED: {}'
        \ ] )
  call vimspector#ListBreakpoints()

  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'simple.cpp', 15, 1 )

  call vimspector#LaunchWithSettings( { 'configuration': 'run-to-breakpoint' } )
  " break on main
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'simple.cpp', 15, 1 )

  call vimspector#ListBreakpoints()
  call s:CheckBreakpointView( [
        \ 'simple.cpp:15 Line breakpoint - VERIFIED: {}'
        \ ] )
  call vimspector#ListBreakpoints()

  call win_gotoid( main_win_id )
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'simple.cpp', 15, 1 )

  " Add a breakpoint that moves (from line 5 to line 6 or 9)
  call cursor( [ 5, 1 ] )
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'simple.cpp', 5, 1 )
  call vimspector#ToggleBreakpoint()

  call vimspector#ListBreakpoints()
  call s:CheckBreakpointView( [
        \ 'simple.cpp:15 Line breakpoint - VERIFIED: {}',
        \ 'simple.cpp:' . s:break_foo_line . ' Line breakpoint - VERIFIED: {}'
        \ ] )

  call vimspector#ListBreakpoints()

  call vimspector#test#setup#Reset()
  %bwipe!
endfunction

function! Test_Custom_Breakpoint_Priority()
  call ThisTestIsFlaky()
  let g:vimspector_sign_priority = {
        \ 'vimspectorPC': 1,
        \ 'vimspectorPCBP': 1,
        \ 'vimspectorBP': 2,
        \ 'vimspectorBPCond': 3,
        \ 'vimspectorBPDisabled': 4
        \ }

  " While not debugging
  lcd testdata/cpp/simple
  edit simple.cpp

  call setpos( '.', [ 0, 15, 1 ] )
  call vimspector#ToggleBreakpoint()
  call vimspector#test#signs#AssertSignGroupSingletonAtLine( 'VimspectorBP',
                                                           \ 15,
                                                           \ 'vimspectorBP',
                                                           \ 2 )
  call setpos( '.', [ 0, 16, 1 ] )
  call vimspector#ToggleBreakpoint()
  call vimspector#ToggleBreakpoint()
  call vimspector#test#signs#AssertSignGroupSingletonAtLine(
        \ 'VimspectorBP',
        \ 16,
        \ 'vimspectorBPDisabled',
        \ 4 )
  call vimspector#ToggleBreakpoint()
  call vimspector#test#signs#AssertSignGroupEmptyAtLine( 'VimspectorBP', 16 )

  call setpos( '.', [ 0, 17, 1 ] )
  call vimspector#ToggleBreakpoint( { 'condition': '1' } )
  call vimspector#test#signs#AssertSignGroupSingletonAtLine(
        \ 'VimspectorBP',
        \ 17,
        \ 'vimspectorBPCond',
        \ 3 )

  " While debugging
  call vimspector#LaunchWithSettings( { 'configuration': 'run-to-breakpoint' } )
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'simple.cpp', 15, 1 )
  call vimspector#test#signs#AssertPCIsAtLineInBuffer( 'simple.cpp', 15 )
  call vimspector#test#signs#AssertSignAtLine(
        \ 'VimspectorBP',
        \ 15,
        \ 'vimspectorBP',
        \ 2 )
  call vimspector#test#signs#AssertSignAtLine(
        \ 'VimspectorCode',
        \ 15,
        \ 'vimspectorPCBP',
        \ 1 )
  call vimspector#test#signs#AssertSignGroupSingletonAtLine( 'VimspectorBP',
                                                           \ 17,
                                                           \ 'vimspectorBPCond',
                                                           \ 3 )

  call vimspector#StepOver()
  " No sign as disabled
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'simple.cpp', 16, 1 )
  call vimspector#test#signs#AssertPCIsAtLineInBuffer( 'simple.cpp', 16 )

  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'simple.cpp', 17, 1 )
  call vimspector#test#signs#AssertPCIsAtLineInBuffer( 'simple.cpp', 17 )

  call vimspector#test#signs#AssertSignGroupSingletonAtLine(
        \ 'VimspectorBP',
        \ 15,
        \ 'vimspectorBP',
        \ 2 )
  call vimspector#test#signs#AssertSignAtLine(
        \ 'VimspectorBP',
        \ 17,
        \ 'vimspectorBPCond',
        \ 3 )
  call vimspector#test#signs#AssertSignAtLine(
        \ 'VimspectorCode',
        \ 17,
        \ 'vimspectorPCBP',
        \ 1 )


  call vimspector#test#setup#Reset()
  lcd -
  %bwipeout!
  unlet! g:vimspector_sign_priority
endfunction

function! Test_Custom_Breakpoint_Priority_Partial()
  let g:vimspector_sign_priority = {
        \ 'vimspectorBP': 2,
        \ 'vimspectorBPCond': 3,
        \ 'vimspectorBPDisabled': 4
        \ }

  " While not debugging
  lcd testdata/cpp/simple
  edit simple.cpp

  call setpos( '.', [ 0, 15, 1 ] )
  call vimspector#ToggleBreakpoint()
  call vimspector#test#signs#AssertSignGroupSingletonAtLine( 'VimspectorBP',
                                                           \ 15,
                                                           \ 'vimspectorBP',
                                                           \ 2 )
  call setpos( '.', [ 0, 16, 1 ] )
  call vimspector#ToggleBreakpoint()
  call vimspector#ToggleBreakpoint()
  call vimspector#test#signs#AssertSignGroupSingletonAtLine(
        \ 'VimspectorBP',
        \ 16,
        \ 'vimspectorBPDisabled',
        \ 4 )
  call vimspector#ToggleBreakpoint()
  call vimspector#test#signs#AssertSignGroupEmptyAtLine( 'VimspectorBP', 16 )

  call setpos( '.', [ 0, 17, 1 ] )
  call vimspector#ToggleBreakpoint( { 'condition': '1' } )
  call vimspector#test#signs#AssertSignGroupSingletonAtLine(
        \ 'VimspectorBP',
        \ 17,
        \ 'vimspectorBPCond',
        \ 3 )

  " While debugging
  call vimspector#LaunchWithSettings( { 'configuration': 'run-to-breakpoint' } )
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'simple.cpp', 15, 1 )
  call vimspector#test#signs#AssertPCIsAtLineInBuffer( 'simple.cpp', 15 )
  call vimspector#test#signs#AssertSignAtLine(
        \ 'VimspectorBP',
        \ 15,
        \ 'vimspectorBP',
        \ 2 )
  call vimspector#test#signs#AssertSignAtLine(
        \ 'VimspectorCode',
        \ 15,
        \ 'vimspectorPCBP',
        \ 200 )
  call vimspector#test#signs#AssertSignGroupSingletonAtLine( 'VimspectorBP',
                                                           \ 17,
                                                           \ 'vimspectorBPCond',
                                                           \ 3 )

  call vimspector#StepOver()
  " No sign as disabled
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'simple.cpp', 16, 1 )
  call vimspector#test#signs#AssertPCIsAtLineInBuffer( 'simple.cpp', 16 )

  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'simple.cpp', 17, 1 )
  call vimspector#test#signs#AssertPCIsAtLineInBuffer( 'simple.cpp', 17 )

  call vimspector#test#signs#AssertSignGroupSingletonAtLine(
        \ 'VimspectorBP',
        \ 15,
        \ 'vimspectorBP',
        \ 2 )
  call vimspector#test#signs#AssertSignAtLine(
        \ 'VimspectorBP',
        \ 17,
        \ 'vimspectorBPCond',
        \ 3 )
  call vimspector#test#signs#AssertSignAtLine(
        \ 'VimspectorCode',
        \ 17,
        \ 'vimspectorPCBP',
        \ 200 )


  call vimspector#test#setup#Reset()
  lcd -
  %bwipeout!
  unlet! g:vimspector_sign_priority
endfunction


function! Test_Add_Line_BP_In_Other_File_While_Debugging()
  call ThisTestIsFlaky()
  let moo = 'moo.py'
  let cow = 'cow.py'
  lcd ../support/test/python/multiple_files
  exe 'edit' moo

  call vimspector#Launch()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( moo, 1, 1 )
  call vimspector#test#signs#AssertPCIsAtLineInBuffer( moo, 1 )

  call cursor( 6, 3 )
  call vimspector#ToggleBreakpoint()
  call vimspector#test#signs#AssertPCIsAtLineInBuffer( moo, 1 )
  call WaitForAssert( {->
        \vimspector#test#signs#AssertSignGroupSingletonAtLine(
          \ 'VimspectorBP',
          \ 6,
          \ 'vimspectorBP',
          \ 9 ) } )

  exe 'edit' cow
  call cursor( 2, 1 )
  call vimspector#ToggleBreakpoint()
  call vimspector#test#signs#AssertSignGroupEmptyAtLine( 'VimspectorBP', 6 )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertSignGroupSingletonAtLine(
          \ 'VimspectorBP',
          \ 2,
          \ 'vimspectorBP',
          \ 9 ) } )

  call vimspector#Continue()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( moo, 6, 1 )
  call vimspector#test#signs#AssertPCIsAtLineInBuffer( moo, 6 )

  call vimspector#test#signs#AssertSignGroupEmptyAtLine( 'VimspectorBP', 2 )
  call vimspector#test#signs#AssertSignAtLine(
        \ 'VimspectorBP',
        \ 6,
        \ 'vimspectorBP',
        \ 9 )
  call vimspector#test#signs#AssertSignAtLine(
        \ 'VimspectorCode',
        \ 6,
        \ 'vimspectorPCBP',
        \ 200 )

  call vimspector#Continue()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( cow, 2, 1 )
  call vimspector#test#signs#AssertPCIsAtLineInBuffer( cow, 2 )

  call vimspector#test#signs#AssertSignGroupEmptyAtLine( 'VimspectorBP', 6 )
  call vimspector#test#signs#AssertSignAtLine(
        \ 'VimspectorBP',
        \ 2,
        \ 'vimspectorBP',
        \ 9 )
  call vimspector#test#signs#AssertSignAtLine(
        \ 'VimspectorCode',
        \ 2,
        \ 'vimspectorPCBP',
        \ 200 )

  lcd -
  call vimspector#test#setup#Reset()
  %bwipe!
endfunction
