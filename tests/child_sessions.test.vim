let s:fn='../support/test/python/multiprocessing/multiprocessing_test.py'

function! SetUp()
  call vimspector#test#setup#SetUpWithMappings( 'HUMAN' )
endfunction

function! TearDown()
  call vimspector#test#setup#TearDown()
endfunction


function! s:StartDebugging( ... )
  let config = #{
        \   fn: s:fn,
        \   line: 6,
        \   col: 1,
        \   launch: #{ configuration: 'run-to-breakpoint' }
        \ }
  if a:0 > 0
    call extend( config, a:1 )
  endif

  execute 'edit' config.fn
  call cursor( 1, 1 )
  call vimspector#SetLineBreakpoint( config.fn, config.line )
  call vimspector#LaunchWithSettings( config.launch )
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer(
        \ config.fn,
        \ config.line,
        \ config.col )
endfunction

function! Test_Python_MultiProcessing()
  " For some reason the 'fork' mp style causes crashes in debugpy at least on
  " macOS (but only when using neovim!). And for the tests to be stable, we need
  " to ensure there's only 1 child launched. With the default 'launch' behaviour
  " of multiprocessing, we get arbitrary ordering for the additional watchdog
  " chld process
  call SkipNeovim()
  call s:StartDebugging()

  call WaitForAssert( {->
        \   AssertMatchList(
        \     [
        \         '---',
        \         'Session: run-to-breakpoint ([0-9]\+)',
        \         '- Thread [0-9]\+: MainThread (paused)',
        \         '  [0-9]\+: Priant@multiprocessing_test.py:6',
        \         '  [0-9]\+: <module>@multiprocessing_test.py:28',
        \         '---',
        \         'Session: Subprocess [0-9]\+ ([0-9]\+)',
        \         '- Thread [0-9]\+: MainThread (paused)',
        \         '  [0-9]\+: Priant@multiprocessing_test.py:6',
        \         '  [0-9]\+: First@multiprocessing_test.py:11',
        \         '  [0-9]\+: <module>@multiprocessing_test.py:22',
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
          \ 8,
          \ 'vimspectorCurrentThread',
          \ 200 ) } )
  call WaitForAssert( { ->
        \ vimspector#test#signs#AssertSignGroupSingletonAtLine(
          \ 'VimspectorStackTrace',
          \ 9,
          \ 'vimspectorCurrentFrame',
          \ 200 ) } )
  wincmd w

  " Step in 2nd process, check signs
  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, 12, 1 )

  call WaitForAssert( {->
        \   AssertMatchList(
        \     [
        \         '---',
        \         'Session: run-to-breakpoint ([0-9]\+)',
        \         '- Thread [0-9]\+: MainThread (paused)',
        \         '  [0-9]\+: Priant@multiprocessing_test.py:6',
        \         '  [0-9]\+: <module>@multiprocessing_test.py:28',
        \         '---',
        \         'Session: Subprocess [0-9]\+ ([0-9]\+)',
        \         '- Thread [0-9]\+: MainThread (paused)',
        \         '  [0-9]\+: First@multiprocessing_test.py:12',
        \         '  [0-9]\+: <module>@multiprocessing_test.py:22',
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
          \ 8,
          \ 'vimspectorCurrentThread',
          \ 200 ) } )
  call WaitForAssert( { ->
        \ vimspector#test#signs#AssertSignGroupSingletonAtLine(
          \ 'VimspectorStackTrace',
          \ 9,
          \ 'vimspectorCurrentFrame',
          \ 200 ) } )
  wincmd w
  call WaitForAssert( { ->
        \ vimspector#test#signs#AssertSignGroupSingletonAtLine(
          \ 'VimspectorStackTrace',
          \ 6,
          \ 'vimspectorNonActivePC',
          \ 9 ) } )
  call WaitForAssert( { ->
        \ vimspector#test#signs#AssertSignGroupSingletonAtLine(
          \ 'VimspectorCode',
          \ 12,
          \ 'vimspectorPC',
          \ 200 ) } )


  " Switch to 1st process, check signs
  call win_gotoid( g:vimspector_session_windows.stack_trace )
  call cursor( 4, 1 )
  call vimspector#GoToFrame()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, 6, 1 )
  call WaitForAssert( { ->
        \ vimspector#test#signs#AssertSignGroupSingletonAtLine(
          \ 'VimspectorStackTrace',
          \ 12,
          \ 'vimspectorNonActivePC',
          \ 9 ) } )
  call WaitForAssert( { ->
        \ vimspector#test#signs#AssertSignGroupSingletonAtLine(
          \ 'VimspectorCode',
          \ 6,
          \ 'vimspectorPCBP',
          \ 200 ) } )

  call win_gotoid( g:vimspector_session_windows.stack_trace )
  call WaitForAssert( { ->
        \ vimspector#test#signs#AssertSignGroupSingletonAtLine(
          \ 'VimspectorStackTrace',
          \ 3,
          \ 'vimspectorCurrentThread',
          \ 200 ) } )
  call WaitForAssert( { ->
        \ vimspector#test#signs#AssertSignGroupSingletonAtLine(
          \ 'VimspectorStackTrace',
          \ 4,
          \ 'vimspectorCurrentFrame',
          \ 200 ) } )
  wincmd w

  " TODO: Should probably toggle breakpoint and show that it applies to both
  " sessions

  " TODO: should probably do a load of tests for the new watch and scopes
  " behaviour

  " TODO: should test some subprocesses finishing (child first, then root first)

  call vimspector#test#setup#Reset()
  %bwipe!
endfunction

function! Test_NodeJsDebug_Simple()
  let fn = '../support/test/node/simple/simple.js'
  call s:StartDebugging( #{ fn: fn, line: 10, launch: #{
        \ configuration: 'run - js-debug'
        \ } } )

  " See that breakpoitns basically work
  call vimspector#SetLineBreakpoint( fn, 6 )
  call WaitForAssert( { ->
        \ vimspector#test#signs#AssertSignGroupSingletonAtLine(
          \ 'VimspectorBP',
          \ 6,
          \ 'vimspectorBP',
          \ 9 ) } )

  " @show
  call vimspector#ListBreakpoints()
  call WaitForAssert( {->
          \ AssertMatchList( [
          \   'simple.js:10 Line breakpoint - VERIFIED: {}',
          \   'simple.js:6 Line breakpoint - VERIFIED: {}',
          \ ],
          \ GetBufLine(
                      \ winbufnr( g:vimspector_session_windows.breakpoints ),
                      \ 1,
                      \ '$' ) ) } )
  " @hide
  call vimspector#ListBreakpoints()
  call vimspector#Continue()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 6, 5 )

  call WaitForAssert( {->
      \   AssertMatchList(
      \     [
      \         '---',
      \         'Session: run - js-debug ([0-9]\+)',
      \         '---',
      \         'Session: simple.js \[[0-9]\+\] ([0-9]\+)',
      \         '- Thread [0-9]\+: simple.js \[[0-9]\+\] (Paused on breakpoint)',
      \         '  [0-9]\+: toast@.*/simple.js:6',
      \     ],
      \     GetBufLine( winbufnr( g:vimspector_session_windows.stack_trace ),
      \                 1,
      \                 6 )
      \   )
      \ } )


  call vimspector#test#setup#Reset()
  %bwipe!
endfunction

function! Test_BPMovedByServer_Simple()
  let fn = '../support/test/node/simple/simple.js'
  call s:StartDebugging( #{ fn: fn, line: 10, launch: #{
        \ configuration: 'run - js-debug'
        \ } } )

  " Gets moved back to line 6
  call vimspector#SetLineBreakpoint( fn, 7 )
  call WaitForAssert( { ->
        \ vimspector#test#signs#AssertSignGroupSingletonAtLine(
          \ 'VimspectorBP',
          \ 6,
          \ 'vimspectorBP',
          \ 9 ) } )

  " @show
  call vimspector#ListBreakpoints()
  call WaitForAssert( {->
          \ AssertMatchList( [
          \   'simple.js:10 Line breakpoint - VERIFIED: {}',
          \   'simple.js:6 Line breakpoint - VERIFIED: {}',
          \ ],
          \ GetBufLine(
                      \ winbufnr( g:vimspector_session_windows.breakpoints ),
                      \ 1,
                      \ '$' ) ) } )
  " @hide
  call vimspector#ListBreakpoints()
  call vimspector#Continue()
  " Note the cursor is on the end of the previous line. Seems the debugger
  " actually _does_ break _after_ the line (the bp is placed on the closecurly)
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 6, 32 )

  " close down
  call vimspector#Reset()
  call vimspector#test#setup#WaitForReset()

  " @show
  call vimspector#ListBreakpoints()
  call WaitForAssert( {->
          \ AssertMatchList( [
          \   'simple.js:10 Line breakpoint - ENABLED: {}',
          \   'simple.js:7 Line breakpoint - ENABLED: {}',
          \ ],
          \ GetBufLine(
                      \ winbufnr( g:vimspector_session_windows.breakpoints ),
                      \ 1,
                      \ '$' ) ) } )
  " @hide
  call vimspector#test#setup#Reset()
  %bwipe!
endfunction
