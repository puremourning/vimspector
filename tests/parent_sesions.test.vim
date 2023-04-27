let s:fn='../support/test/python/simple_python/main.py'

function! SetUp()
  call vimspector#test#setup#SetUpWithMappings( 'HUMAN' )
endfunction

function! TearDown()
  call vimspector#test#setup#TearDown()
endfunction


function! s:StartDebugging( ... )
  let config = #{
        \   fn: s:fn,
        \   line: 23,
        \   col: 1,
        \   launch: #{ configuration: 'run' }
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

function! SessionID()
  return py3eval( '_vimspector_session.session_id' )
endfunction

function! Test_Multiple_Root_Sessions_Works()
  " Init vimspector session
  call vimspector#Reset()
  call assert_match( '^Unnamed-[0-9]\+$', vimspector#GetSessionName() )
  call s:StartDebugging()
  call assert_equal( 'run', vimspector#GetSessionName() )
  call assert_equal( 2, tabpagenr() )
  call assert_equal( 2, tabpagenr( '$' ) )
  VimspectorRenameSession One
  call assert_equal( 'One', vimspector#GetSessionName() )
  normal! 1gt
  call assert_equal( 'One', vimspector#GetSessionName() )
  call assert_equal( 1, tabpagenr() )
  VimspectorNewSession Two
  call assert_equal( 'Two', vimspector#GetSessionName() )
  call s:StartDebugging()
  call assert_equal( 'Two', vimspector#GetSessionName() )
  call assert_equal( 3, tabpagenr() )
  call assert_equal( 3, tabpagenr( '$' ) )

  VimspectorSwitchToSession One
  call assert_equal( 2, tabpagenr() )
  call assert_equal( 3, tabpagenr( '$' ) )
  let one_win = win_getid()
  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, 25, 1 )
  call assert_equal( win_getid(), one_win )
  VimspectorToggleLog

  VimspectorSwitchToSession Two
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, 23, 1 )
  call assert_equal( 3, tabpagenr() )
  call assert_equal( 3, tabpagenr( '$' ) )
  let two_win = win_getid()
  call assert_notequal( two_win, one_win )
  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, 25, 1 )
  call assert_equal( win_getid(), two_win )
  VimspectorToggleLog


  call vimspector#Reset()
  call vimspector#test#setup#WaitForSessionReset( SessionID() )

  VimspectorSwitchToSession One
  call vimspector#Reset()
  call vimspector#test#setup#WaitForReset()

  %bwipe!
endfunction
