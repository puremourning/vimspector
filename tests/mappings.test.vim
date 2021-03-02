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
  call assert_true( hasmapto( 'vimspector#RunToCursor()' ) )
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

function! SetUp_Test_Use_Mappings_HUMAN()
  let g:vimspector_enable_mappings = 'HUMAN'
endfunction

function! Test_Use_Mappings_HUMAN()
  call ThisTestIsFlaky()
  lcd testdata/cpp/simple
  edit simple.cpp
  call setpos( '.', [ 0, 15, 1 ] )

  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'simple.cpp', 15, 1 )
  call vimspector#test#signs#AssertSignGroupEmptyAtLine( 'VimspectorBP', 15 )

  " Add the breakpoint
  call feedkeys( "\<F9>", 'xt' )
  call vimspector#test#signs#AssertSignGroupSingletonAtLine( 'VimspectorBP',
                                                           \ 15,
                                                           \ 'vimspectorBP',
                                                           \ 9 )

  " Disable the breakpoint
  call feedkeys( "\<F9>", 'xt' )
  call vimspector#test#signs#AssertSignGroupSingletonAtLine(
        \ 'VimspectorBP',
        \ 15,
        \ 'vimspectorBPDisabled',
        \ 9 )

  " Delete the breakpoint
  call feedkeys( "\<F9>", 'xt' )
  call vimspector#test#signs#AssertSignGroupEmptyAtLine( 'VimspectorBP', 15 )

  " Add and clear using API
  call vimspector#SetLineBreakpoint( 'simple.cpp', 15 )
  call vimspector#test#signs#AssertSignGroupSingletonAtLine( 'VimspectorBP',
                                                           \ 15,
                                                           \ 'vimspectorBP',
                                                           \ 9 )

  call vimspector#ClearLineBreakpoint( 'simple.cpp', 15 )
  call vimspector#test#signs#AssertSignGroupEmptyAtLine( 'VimspectorBP', 15 )

  " Add it again
  call feedkeys( "\<F9>", 'xt' )
  call vimspector#test#signs#AssertSignGroupSingletonAtLine(
        \ 'VimspectorBP',
        \ 15,
        \ 'vimspectorBP',
        \ 9 )

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
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer( 'simple.cpp', 16 )
        \ } )

  " Run to cursor (note , is the mapleader)
  call cursor( 9, 1 )
  call feedkeys( ",\<F8>", 'xt' )
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'simple.cpp', 9, 1 )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer( 'simple.cpp', 9 )
        \ } )

  " Stop
  call feedkeys( "\<F3>", 'xt' )
  call WaitForAssert( {->
        \ assert_equal( [],
        \               getbufline( g:vimspector_session_windows.variables,
        \                           1,
        \                           '$' ) )
        \ } )
  call WaitForAssert( {->
        \ assert_equal( [],
        \               getbufline( g:vimspector_session_windows.stack_trace,
        \                           1,
        \                           '$' ) )
        \ } )
  call WaitForAssert( {->
        \ assert_equal( [],
        \               getbufline( g:vimspector_session_windows.watches,
        \                           1,
        \                           '$' ) )
        \ } )

  call vimspector#test#setup#Reset()

  lcd -
  %bwipeout!
endfunction

