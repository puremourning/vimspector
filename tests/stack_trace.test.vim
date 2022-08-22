let s:fn='testdata/cpp/simple/threads.cpp'

function! SetUp()
  call vimspector#test#setup#SetUpWithMappings( 'HUMAN' )
endfunction

function! TearDown()
  call vimspector#test#setup#TearDown()
endfunction

function! s:StartDebugging()
  exe 'edit ' . s:fn
  call vimspector#SetLineBreakpoint( s:fn, 15 )
  call vimspector#LaunchWithSettings( #{ configuration: 'run-to-breakpoint' } )
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, 15, 1 )
endfunction

function! Test_Multiple_Threads_Continue()
  let thread_l = 67
  let notify_l = 74

  call vimspector#SetLineBreakpoint( s:fn, thread_l )
  call vimspector#SetLineBreakpoint( s:fn, notify_l )
  call s:StartDebugging()

  call vimspector#Continue()

  " As we step through the thread creation we should get Thread events

  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, thread_l, 1 )
  call cursor( 1, 1 )
  call WaitForAssert( {->
        \   AssertMatchList(
        \     [
        \         '- Thread [0-9]\+: .* (paused)',
        \         '  .*: .*@threads.cpp:' . string( thread_l )
        \     ],
        \     GetBufLine( winbufnr( g:vimspector_session_windows.stack_trace ),
        \                 1,
        \                 2 )
        \   )
        \ } )
  call vimspector#Continue()

  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, thread_l, 1 )
  call cursor( 1, 1 )
  call WaitForAssert( {->
        \   AssertMatchList(
        \     [
        \         '- Thread [0-9]\+: .* (paused)',
        \         '  .*: .*@threads.cpp:' . string( thread_l )
        \     ],
        \     GetBufLine( winbufnr( g:vimspector_session_windows.stack_trace ),
        \                 1,
        \                 2 )
        \   )
        \ } )
  call WaitForAssert( {->
        \   AssertMatchList(
        \     [
        \         '+ Thread [0-9]\+: .* (paused)',
        \     ],
        \     GetBufLine( winbufnr( g:vimspector_session_windows.stack_trace ),
        \                 '$',
        \                 '$' )
        \   )
        \ } )
  call vimspector#Continue()

  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, thread_l, 1 )
  call cursor( 1, 1 )
  call WaitForAssert( {->
        \   AssertMatchList(
        \     [
        \         '- Thread [0-9]\+: .* (paused)',
        \         '  .*: .*@threads.cpp:' . string( thread_l )
        \     ],
        \     GetBufLine( winbufnr( g:vimspector_session_windows.stack_trace ),
        \                 1,
        \                 2 )
        \   )
        \ } )
  call WaitForAssert( {->
        \   AssertMatchList(
        \     [
        \         '+ Thread [0-9]\+: .* (paused)',
        \     ],
        \     GetBufLine( winbufnr( g:vimspector_session_windows.stack_trace ),
        \                 '$',
        \                 '$' )
        \   )
        \ } )
  call vimspector#Continue()

  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, thread_l, 1 )
  call cursor( 1, 1 )
  call WaitForAssert( {->
        \   AssertMatchList(
        \     [
        \         '- Thread [0-9]\+: .* (paused)',
        \         '  .*: .*@threads.cpp:' . string( thread_l )
        \     ],
        \     GetBufLine( winbufnr( g:vimspector_session_windows.stack_trace ),
        \                 1,
        \                 2 )
        \   )
        \ } )
  call WaitForAssert( {->
        \   AssertMatchList(
        \     [
        \         '+ Thread [0-9]\+: .* (paused)',
        \     ],
        \     GetBufLine( winbufnr( g:vimspector_session_windows.stack_trace ),
        \                 '$',
        \                 '$' )
        \   )
        \ } )
  call vimspector#Continue()

  " This is the last one
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, thread_l, 1 )
  call cursor( 1, 1 )
  call WaitForAssert( {->
        \   AssertMatchList(
        \     [
        \         '- Thread [0-9]\+: .* (paused)',
        \         '  .*: .*@threads.cpp:' . string( thread_l )
        \     ],
        \     GetBufLine( winbufnr( g:vimspector_session_windows.stack_trace ),
        \                 1,
        \                 2 )
        \   )
        \ } )
  call WaitForAssert( {->
        \   AssertMatchList(
        \     [
        \         '+ Thread [0-9]\+: .* (paused)',
        \     ],
        \     GetBufLine( winbufnr( g:vimspector_session_windows.stack_trace ),
        \                 '$',
        \                 '$' )
        \   )
        \ } )
  call vimspector#Continue()

  " So we break out of the loop
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, notify_l, 1 )
  call WaitForAssert( {->
        \   AssertMatchList(
        \     [
        \         '- Thread [0-9]\+: .* (paused)',
        \         '  .*: .*@threads.cpp:' . string( notify_l )
        \     ],
        \     GetBufLine( winbufnr( g:vimspector_session_windows.stack_trace ),
        \                 1,
        \                 2 )
        \   )
        \ } )
  call WaitForAssert( {->
        \   AssertMatchList(
        \     [
        \         '+ Thread [0-9]\+: .* (paused)',
        \     ],
        \     GetBufLine( winbufnr( g:vimspector_session_windows.stack_trace ),
        \                 '$',
        \                 '$' )
        \   )
        \ } )

  call vimspector#ClearBreakpoints()
  call vimspector#test#setup#Reset()
  %bwipe!
endfunction

function! Test_Multiple_Threads_Step()
  let thread_l = 67
  if $VIMSPECTOR_MIMODE ==# 'lldb'
    " }
    let thread_n = thread_l + 1
  else
    " for ....
    let thread_n = 49
  endif
  let notify_l = 74

  call vimspector#SetLineBreakpoint( s:fn, thread_l )
  call vimspector#SetLineBreakpoint( s:fn, notify_l )
  call s:StartDebugging()
  call vimspector#Continue()

  " As we step through the thread creation we should get Thread events

  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, thread_l, 1 )
  call WaitForAssert( {->
        \   AssertMatchList(
        \     [
        \         '- Thread [0-9]\+: .* (paused)',
        \         '  .*: .*@threads.cpp:' . string( thread_l )
        \     ],
        \     GetBufLine( winbufnr( g:vimspector_session_windows.stack_trace ),
        \                 1,
        \                 2 )
        \   )
        \ } )
  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, thread_n, 1 )
  call WaitForAssert( {->
        \   AssertMatchList(
        \     [
        \         '+ Thread [0-9]\+: .* (paused)',
        \     ],
        \     GetBufLine( winbufnr( g:vimspector_session_windows.stack_trace ),
        \                 '$',
        \                 '$' )
        \   )
        \ } )
  call vimspector#Continue()

  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, thread_l, 1 )
  call WaitForAssert( {->
        \   AssertMatchList(
        \     [
        \         '+ Thread [0-9]\+: .* (paused)',
        \     ],
        \     GetBufLine( winbufnr( g:vimspector_session_windows.stack_trace ),
        \                 '$',
        \                 '$' )
        \   )
        \ } )
  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, thread_n, 1 )
  call WaitForAssert( {->
        \   AssertMatchList(
        \     [
        \         '+ Thread [0-9]\+: .* (paused)',
        \         '+ Thread [0-9]\+: .* (paused)',
        \     ],
        \     GetBufLine( winbufnr( g:vimspector_session_windows.stack_trace ),
        \                 -1,
        \                 '$' )
        \   )
        \ } )
  call vimspector#Continue()

  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, thread_l, 1 )
  call WaitForAssert( {->
        \   AssertMatchList(
        \     [
        \         '+ Thread [0-9]\+: .* (paused)',
        \         '+ Thread [0-9]\+: .* (paused)',
        \     ],
        \     GetBufLine( winbufnr( g:vimspector_session_windows.stack_trace ),
        \                 -1,
        \                 '$' )
        \   )
        \ } )
  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, thread_n, 1 )
  call WaitForAssert( {->
        \   AssertMatchList(
        \     [
        \         '+ Thread [0-9]\+: .* (paused)',
        \         '+ Thread [0-9]\+: .* (paused)',
        \         '+ Thread [0-9]\+: .* (paused)',
        \     ],
        \     GetBufLine( winbufnr( g:vimspector_session_windows.stack_trace ),
        \                 -2,
        \                 '$' )
        \   )
        \ } )
  call vimspector#Continue()


  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, thread_l, 1 )
  call WaitForAssert( {->
        \   AssertMatchList(
        \     [
        \         '+ Thread [0-9]\+: .* (paused)',
        \         '+ Thread [0-9]\+: .* (paused)',
        \         '+ Thread [0-9]\+: .* (paused)',
        \     ],
        \     GetBufLine( winbufnr( g:vimspector_session_windows.stack_trace ),
        \                 -2,
        \                 '$' )
        \   )
        \ } )
  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, thread_n, 1 )
  call WaitForAssert( {->
        \   AssertMatchList(
        \     [
        \         '+ Thread [0-9]\+: .* (paused)',
        \         '+ Thread [0-9]\+: .* (paused)',
        \         '+ Thread [0-9]\+: .* (paused)',
        \         '+ Thread [0-9]\+: .* (paused)',
        \     ],
        \     GetBufLine( winbufnr( g:vimspector_session_windows.stack_trace ),
        \                 -3,
        \                 '$' )
        \   )
        \ } )
  call vimspector#Continue()


  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, thread_l, 1 )
  call WaitForAssert( {->
        \   AssertMatchList(
        \     [
        \         '+ Thread [0-9]\+: .* (paused)',
        \         '+ Thread [0-9]\+: .* (paused)',
        \         '+ Thread [0-9]\+: .* (paused)',
        \         '+ Thread [0-9]\+: .* (paused)',
        \     ],
        \     GetBufLine( winbufnr( g:vimspector_session_windows.stack_trace ),
        \                 -3,
        \                 '$' )
        \   )
        \ } )
  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, thread_n, 1 )
  call WaitForAssert( {->
        \   AssertMatchList(
        \     [
        \         '+ Thread [0-9]\+: .* (paused)',
        \         '+ Thread [0-9]\+: .* (paused)',
        \         '+ Thread [0-9]\+: .* (paused)',
        \         '+ Thread [0-9]\+: .* (paused)',
        \         '+ Thread [0-9]\+: .* (paused)',
        \     ],
        \     GetBufLine( winbufnr( g:vimspector_session_windows.stack_trace ),
        \                 -4,
        \                 '$' )
        \   )
        \ } )
  call vimspector#Continue()


  " So we break out of the loop
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, notify_l, 1 )
  call WaitForAssert( {->
        \   AssertMatchList(
        \     [
        \         '+ Thread [0-9]\+: .* (paused)',
        \         '+ Thread [0-9]\+: .* (paused)',
        \         '+ Thread [0-9]\+: .* (paused)',
        \         '+ Thread [0-9]\+: .* (paused)',
        \         '+ Thread [0-9]\+: .* (paused)',
        \     ],
        \     GetBufLine( winbufnr( g:vimspector_session_windows.stack_trace ),
        \                 -4,
        \                 '$' )
        \   )
        \ } )

  call vimspector#ClearBreakpoints()
  call vimspector#test#setup#Reset()
  %bwipe!
endfunction

function! Test_UpDownStack()
  call SkipNeovim()
  let fn='../support/test/python/simple_python/main.py'
  exe 'edit ' . fn
  call setpos( '.', [ 0, 6, 1 ] )

  call vimspector#SetLineBreakpoint( fn, 15 )
  call vimspector#LaunchWithSettings( { 'configuration': 'run' } )
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 15, 1 )
  call WaitForAssert( {->
        \   AssertMatchList(
        \     [
        \         '- Thread 1: MainThread (paused)',
        \         '  2: DoSomething@main.py:15',
        \         '  3: __init__@main.py:8',
        \         '  4: Main@main.py:23',
        \         '  5: <module>@main.py:29',
        \     ],
        \     GetBufLine( winbufnr( g:vimspector_session_windows.stack_trace ),
        \                 1,
        \                 '$' )
        \   )
        \ } )
  call win_gotoid( g:vimspector_session_windows.stack_trace )
  call WaitForAssert( { ->
        \ vimspector#test#signs#AssertSignGroupSingletonAtLine(
          \ 'VimspectorStackTrace',
          \ 1,
          \ 'vimspectorCurrentThread',
          \ 200 ) } )
  call WaitForAssert( { ->
        \ vimspector#test#signs#AssertSignGroupSingletonAtLine(
          \ 'VimspectorStackTrace',
          \ 2,
          \ 'vimspectorCurrentFrame',
          \ 200 ) } )
  wincmd w

  call vimspector#DownFrame()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 15, 1 )
  call WaitForAssert( {->
        \   AssertMatchList(
        \     [
        \         '- Thread 1: MainThread (paused)',
        \         '  2: DoSomething@main.py:15',
        \         '  3: __init__@main.py:8',
        \         '  4: Main@main.py:23',
        \         '  5: <module>@main.py:29',
        \     ],
        \     GetBufLine( winbufnr( g:vimspector_session_windows.stack_trace ),
        \                 1,
        \                 '$' )
        \   )
        \ } )
  call win_gotoid( g:vimspector_session_windows.stack_trace )
  call WaitForAssert( { ->
        \ vimspector#test#signs#AssertSignGroupSingletonAtLine(
          \ 'VimspectorStackTrace',
          \ 1,
          \ 'vimspectorCurrentThread',
          \ 200 ) } )
  call WaitForAssert( { ->
        \ vimspector#test#signs#AssertSignGroupSingletonAtLine(
          \ 'VimspectorStackTrace',
          \ 2,
          \ 'vimspectorCurrentFrame',
          \ 200 ) } )
  wincmd w


  call vimspector#UpFrame()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 8, 1 )
  call WaitForAssert( {->
        \   AssertMatchList(
        \     [
        \         '- Thread 1: MainThread (paused)',
        \         '  2: DoSomething@main.py:15',
        \         '  3: __init__@main.py:8',
        \         '  4: Main@main.py:23',
        \         '  5: <module>@main.py:29',
        \     ],
        \     GetBufLine( winbufnr( g:vimspector_session_windows.stack_trace ),
        \                 1,
        \                 '$' )
        \   )
        \ } )
  call win_gotoid( g:vimspector_session_windows.stack_trace )
  call WaitForAssert( { ->
        \ vimspector#test#signs#AssertSignGroupSingletonAtLine(
          \ 'VimspectorStackTrace',
          \ 1,
          \ 'vimspectorCurrentThread',
          \ 200 ) } )
  call WaitForAssert( { ->
        \ vimspector#test#signs#AssertSignGroupSingletonAtLine(
          \ 'VimspectorStackTrace',
          \ 3,
          \ 'vimspectorCurrentFrame',
          \ 200 ) } )
  wincmd w


  call feedkeys( "\<Plug>VimspectorUpFrame", 'x' )
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 23, 1 )
  call WaitForAssert( {->
        \   AssertMatchList(
        \     [
        \         '- Thread 1: MainThread (paused)',
        \         '  2: DoSomething@main.py:15',
        \         '  3: __init__@main.py:8',
        \         '  4: Main@main.py:23',
        \         '  5: <module>@main.py:29',
        \     ],
        \     GetBufLine( winbufnr( g:vimspector_session_windows.stack_trace ),
        \                 1,
        \                 '$' )
        \   )
        \ } )
  call win_gotoid( g:vimspector_session_windows.stack_trace )
  call WaitForAssert( { ->
        \ vimspector#test#signs#AssertSignGroupSingletonAtLine(
          \ 'VimspectorStackTrace',
          \ 1,
          \ 'vimspectorCurrentThread',
          \ 200 ) } )
  call WaitForAssert( { ->
        \ vimspector#test#signs#AssertSignGroupSingletonAtLine(
          \ 'VimspectorStackTrace',
          \ 4,
          \ 'vimspectorCurrentFrame',
          \ 200 ) } )
  wincmd w


  call feedkeys( "\<Plug>VimspectorDownFrame", 'x' )
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 8, 1 )
  call WaitForAssert( {->
        \   AssertMatchList(
        \     [
        \         '- Thread 1: MainThread (paused)',
        \         '  2: DoSomething@main.py:15',
        \         '  3: __init__@main.py:8',
        \         '  4: Main@main.py:23',
        \         '  5: <module>@main.py:29',
        \     ],
        \     GetBufLine( winbufnr( g:vimspector_session_windows.stack_trace ),
        \                 1,
        \                 '$' )
        \   )
        \ } )
  call win_gotoid( g:vimspector_session_windows.stack_trace )
  call WaitForAssert( { ->
        \ vimspector#test#signs#AssertSignGroupSingletonAtLine(
          \ 'VimspectorStackTrace',
          \ 1,
          \ 'vimspectorCurrentThread',
          \ 200 ) } )
  call WaitForAssert( { ->
        \ vimspector#test#signs#AssertSignGroupSingletonAtLine(
          \ 'VimspectorStackTrace',
          \ 3,
          \ 'vimspectorCurrentFrame',
          \ 200 ) } )
  wincmd w


  call vimspector#DownFrame()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 15, 1 )
  call WaitForAssert( {->
        \   AssertMatchList(
        \     [
        \         '- Thread 1: MainThread (paused)',
        \         '  2: DoSomething@main.py:15',
        \         '  3: __init__@main.py:8',
        \         '  4: Main@main.py:23',
        \         '  5: <module>@main.py:29',
        \     ],
        \     GetBufLine( winbufnr( g:vimspector_session_windows.stack_trace ),
        \                 1,
        \                 '$' )
        \   )
        \ } )
  call win_gotoid( g:vimspector_session_windows.stack_trace )
  call WaitForAssert( { ->
        \ vimspector#test#signs#AssertSignGroupSingletonAtLine(
          \ 'VimspectorStackTrace',
          \ 1,
          \ 'vimspectorCurrentThread',
          \ 200 ) } )
  call WaitForAssert( { ->
        \ vimspector#test#signs#AssertSignGroupSingletonAtLine(
          \ 'VimspectorStackTrace',
          \ 2,
          \ 'vimspectorCurrentFrame',
          \ 200 ) } )
  wincmd w



  call vimspector#ClearBreakpoints()
  call vimspector#test#setup#Reset()
  %bwipe!
endfunction

function! Test_JumpToProgramCounter()
  let l:break_main_line = FunctionBreakOnBrace() ? 14 : 15
  let l:break_foo_line = FunctionBreakOnBrace() ? 6 : 9
  lcd testdata/cpp/simple
  let fn = 'simple.cpp'
  exe 'edit ' .. fn

  call vimspector#SetLineBreakpoint( fn, 16 )
  call vimspector#Launch()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn,
                                                         \ break_main_line,
                                                         \ 1 )

  function! TestJumpToPCAux( line ) closure abort
    call cursor( [ 1, 1 ] )
    call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 1, 1 )
    call vimspector#JumpToProgramCounter()
    call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, a:line, 1 )
  endfunction

  call vimspector#Continue()
  call TestJumpToPCAux( 16 )
  call vimspector#StepInto()
  call TestJumpToPCAux( break_foo_line )

  edit struct.cpp
  call vimspector#JumpToProgramCounter()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, break_foo_line, 1 )

  call vimspector#ClearBreakpoints()
  call vimspector#test#setup#Reset()
  delfunc TestJumpToPCAux
  %bwipe!
endfunction
