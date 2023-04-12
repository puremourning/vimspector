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
  call s:StartDebugging()

  call WaitForAssert( {->
        \   AssertMatchList(
        \     [
        \         '--- session [0-9]\+',
        \         '- Thread 1: MainThread (paused)',
        \         '  2: Priant@multiprocessing_test.py:6',
        \         '  3: <module>@multiprocessing_test.py:28',
        \         '--- Subprocess [0-9]\+',
        \         '- Thread 1: MainThread (paused)',
        \         '  2: Priant@multiprocessing_test.py:6',
        \         '  3: First@multiprocessing_test.py:11',
        \         '  4: <module>@multiprocessing_test.py:22',
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

  call vimspector#test#setup#Reset()
  %bwipe!
endfunction


