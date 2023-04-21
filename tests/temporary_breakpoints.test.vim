function! SetUp()
  call vimspector#test#setup#SetUpWithMappings( v:null )
endfunction

function! TearDown()
  call vimspector#test#setup#TearDown()
endfunction

function s:Start()
  call vimspector#SetLineBreakpoint( 'moo.py', 13 )
  call vimspector#Launch()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'moo.py', 1, 1 )
  call vimspector#test#signs#AssertPCIsAtLineInBuffer( 'moo.py', 1 )
  call vimspector#Continue()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'moo.py', 13, 1 )
  call vimspector#test#signs#AssertPCIsAtLineInBuffer( 'moo.py', 13 )
endfunction

function Test_Run_To_Cursor_Simple()
  call SkipNeovim()
  " Run to a position that will certainly be executed
  lcd ../support/test/python/multiple_files
  call vimspector#SetLineBreakpoint( 'moo.py', 13 )
  call s:Start()

  call cursor( 8, 27 )
  call vimspector#RunToCursor()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'moo.py', 8, 27 )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer( 'moo.py', 8 )
        \ } )
  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'moo.py', 9, 1 )
  call vimspector#test#signs#AssertPCIsAtLineInBuffer( 'moo.py', 9 )
  " Check there is no breakpoint set on line 8
  call WaitForAssert( {->
      \ vimspector#test#signs#AssertSignGroupEmptyAtLine( 'VimspectorBP', 8 )
      \ } )
  call vimspector#test#setup#Reset()
  lcd -
  %bwipe!
endfunction

function Test_Run_To_Cursor_On_NonBreaking_Line()
  call SkipNeovim()
  " Run to a position that will certainly be executed, but is not a real line
  lcd ../support/test/python/multiple_files
  call vimspector#SetLineBreakpoint( 'moo.py', 13 )
  call s:Start()

  call cursor( 7, 1 )
  " Interestingly, debugpy moves the breakpoint to the previous line, which is
  " kinda annoying
  call vimspector#RunToCursor()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'moo.py', 6, 1 )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer( 'moo.py', 6 )
        \ } )
  call vimspector#StepOver()
  " It's a loop, so we go up a line
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'moo.py', 5, 1 )
  call vimspector#test#signs#AssertPCIsAtLineInBuffer( 'moo.py', 5 )

  " Check there is no breakpoint set on lines 7 and 6:
  "  7 - where we put the 'temporary' breakpoint
  "  6 - where it got placed
  "
  " FIXME: This is broken, we don't _know_ that the breakpoint that was hit was
  " the temporary one, and there's no way to know.
  "
  " I wonder if the relocated breakpoint can be matched with the _original_
  " breakpoint
  call WaitForAssert( {->
      \ vimspector#test#signs#AssertSignGroupEmptyAtLine( 'VimspectorBP', 7 )
      \ } )
  call WaitForAssert( {->
      \ vimspector#test#signs#AssertSignGroupEmptyAtLine( 'VimspectorBP', 6 )
      \ } )
  call vimspector#test#setup#Reset()
  lcd -
  %bwipe!
endfunction

function Test_Run_To_Cursor_Different_File()
  call SkipNeovim()
  " Run into a different file
  " Run to a position that will certainly be executed, but is not a real line
  lcd ../support/test/python/multiple_files
  call vimspector#SetLineBreakpoint( 'moo.py', 13 )
  call s:Start()

  edit cow.py
  call cursor( 2, 1 )
  call vimspector#RunToCursor()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'cow.py', 2, 1 )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer( 'cow.py', 2 )
        \ } )

  bu moo.py
  call cursor( 9, 12 )
  call vimspector#RunToCursor()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'moo.py', 9, 12 )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer( 'moo.py', 9 )
        \ } )

  call vimspector#test#setup#Reset()
  lcd -
  %bwipe!
endfunction

function Test_Run_To_Cursor_Hit_Another_Breakpoint()
  call SkipNeovim()
  " Run to cursor, but hit a non-temporary breakpoint
  lcd ../support/test/python/multiple_files
  call vimspector#SetLineBreakpoint( 'moo.py', 13 )
  call s:Start()

  call vimspector#SetLineBreakpoint( 'moo.py', 5 )
  call cursor( 6, 1 )

  call vimspector#RunToCursor()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'moo.py', 5, 1 )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer( 'moo.py', 5 )
        \ } )

  " The temporary breakpoint is still there
  call vimspector#test#signs#AssertSignGroupSingletonAtLine(
        \ 'VimspectorBP',
        \ 6,
        \ 'vimspectorBP',
        \ 9 )

  call vimspector#ClearLineBreakpoint( 'moo.py', 5 )

  call cursor( 8, 1 )
  call vimspector#RunToCursor()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'moo.py', 8, 1 )
  call WaitForAssert( {->
      \ vimspector#test#signs#AssertPCIsAtLineInBuffer( 'moo.py', 8 )
      \ } )
  call WaitForAssert( {->
      \  vimspector#test#signs#AssertSignGroupEmptyAtLine( 'VimspectorBP', 6 )
      \ } )

  call vimspector#test#setup#Reset()
  lcd -
  %bwipe!
endfunction

function! Test_InvalidBreakpoint()
  " Run to cursor, but hit a non-temporary breakpoint
  lcd ../support/test/python/multiple_files
  call vimspector#SetLineBreakpoint( 'moo.py', 13 )
  call s:Start()

  call vimspector#SetLineBreakpoint( 'moo.py', 9 )

  edit .vimspector.json
  call cursor( 1, 1 )
  call vimspector#RunToCursor()

  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'moo.py', 9, 1 )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer( 'moo.py', 9 )
        \ } )

  call vimspector#test#setup#Reset()
  lcd -
  %bwipe!
endfunction

function! Test_StartDebuggingWithRunToCursor()
  call SkipNeovim()
  lcd ../support/test/python/multiple_files
  edit moo.py
  call cursor( 9, 1 )
  call vimspector#RunToCursor()
  " Stop on entry is still hit
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'moo.py', 1, 1 )
  call vimspector#test#signs#AssertPCIsAtLineInBuffer( 'moo.py', 1 )
  call vimspector#test#signs#AssertSignGroupSingletonAtLine(
        \ 'VimspectorBP',
        \ 9,
        \ 'vimspectorBP',
        \ 9 )

  call vimspector#Continue()
  " Runs to cursor
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'moo.py', 9, 1 )
  call vimspector#test#signs#AssertPCIsAtLineInBuffer( 'moo.py', 9 )

  call vimspector#StepOver()
  " And claers the temp breakpoint
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'moo.py', 8, 1 )
  call vimspector#test#signs#AssertPCIsAtLineInBuffer( 'moo.py', 8 )

  call WaitForAssert( {->
      \ vimspector#test#signs#AssertSignGroupEmptyAtLine( 'VimspectorBP', 9 )
      \ } )

  call vimspector#test#setup#Reset()
  lcd -
  %bwipe!
endfunction

function! Test_Run_To_Cursor_Existing_Line_BP()
  call SkipNeovim()
  lcd ../support/test/python/multiple_files
  edit moo.py
  call s:Start()
  call vimspector#SetLineBreakpoint( 'moo.py', 5 )
  call vimspector#SetLineBreakpoint( 'moo.py', 8 )

  call WaitForAssert( { ->
        \ vimspector#test#signs#AssertSignGroupSingletonAtLine(
          \ 'VimspectorBP',
          \ 5,
          \ 'vimspectorBP',
          \ 9 )
        \ } )
  call WaitForAssert( { ->
        \ vimspector#test#signs#AssertSignGroupSingletonAtLine(
          \ 'VimspectorBP',
          \ 8,
          \ 'vimspectorBP',
          \ 9 )
        \ } )

  call vimspector#Continue()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'moo.py', 5, 1 )

  call WaitForAssert( { ->
        \ vimspector#test#signs#AssertSignGroupSingletonAtLine(
          \ 'VimspectorCode',
          \ 5,
          \ 'vimspectorPCBP',
          \ 200 )
        \ } )
  call WaitForAssert( { ->
        \ vimspector#test#signs#AssertSignGroupSingletonAtLine(
          \ 'VimspectorBP',
          \ 8,
          \ 'vimspectorBP',
          \ 9 )
        \ } )

  " So we don't loop and hit the loop breakpoint first...
  call vimspector#ClearLineBreakpoint( 'moo.py', 5 )

  call cursor( 8, 1 )
  call vimspector#RunToCursor()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'moo.py', 8, 1 )

  call WaitForAssert( { ->
        \ vimspector#test#signs#AssertSignGroupSingletonAtLine(
          \ 'VimspectorCode',
          \ 8,
          \ 'vimspectorPCBP',
          \ 200 )
        \ } )

  call cursor( 1, 1 )
  " the loop breakpoint is still there and hit again
  call vimspector#Continue()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'moo.py', 8, 1 )

  call vimspector#test#setup#Reset()
  lcd -
  %bwipe!
endfunction
