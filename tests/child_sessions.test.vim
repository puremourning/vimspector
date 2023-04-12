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
  " macOS (but only when using neovim!)
  call SkipNeovim()
  call s:StartDebugging()

  call WaitForAssert( {->
        \   AssertMatchList(
        \     [
        \         '--- session [0-9]\+',
        \         '- Thread [0-9]\+: MainThread (paused)',
        \         '  [0-9]\+: Priant@multiprocessing_test.py:6',
        \         '  [0-9]\+: <module>@multiprocessing_test.py:28',
        \         '--- Subprocess [0-9]\+',
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
          \ 6,
          \ 'vimspectorCurrentThread',
          \ 200 ) } )
  call WaitForAssert( { ->
        \ vimspector#test#signs#AssertSignGroupSingletonAtLine(
          \ 'VimspectorStackTrace',
          \ 7,
          \ 'vimspectorCurrentFrame',
          \ 200 ) } )
  wincmd w

  " Step in 2nd process, check signs
  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, 12, 1 )

  call WaitForAssert( {->
        \   AssertMatchList(
        \     [
        \         '--- session [0-9]\+',
        \         '- Thread [0-9]\+: MainThread (paused)',
        \         '  [0-9]\+: Priant@multiprocessing_test.py:6',
        \         '  [0-9]\+: <module>@multiprocessing_test.py:28',
        \         '--- Subprocess [0-9]\+',
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
          \ 6,
          \ 'vimspectorCurrentThread',
          \ 200 ) } )
  call WaitForAssert( { ->
        \ vimspector#test#signs#AssertSignGroupSingletonAtLine(
          \ 'VimspectorStackTrace',
          \ 7,
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
  call cursor( 3, 1 )
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
          \ 2,
          \ 'vimspectorCurrentThread',
          \ 200 ) } )
  call WaitForAssert( { ->
        \ vimspector#test#signs#AssertSignGroupSingletonAtLine(
          \ 'VimspectorStackTrace',
          \ 3,
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


