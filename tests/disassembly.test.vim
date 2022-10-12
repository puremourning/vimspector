let s:fn='testdata/cpp/simple/tiny.c'

let s:buf = '_vimspector_disassembly'

function! SetUp()
  call vimspector#test#setup#SetUpWithMappings( 'HUMAN' )
endfunction

function! TearDown()
  call vimspector#test#setup#TearDown()
endfunction

function! s:StartDebugging( ... )
  if a:0 == 0
    let config = #{
          \   fn: s:fn,
          \   line: 3,
          \   col: 1,
          \   launch: #{ configuration: 'run-to-breakpoint' }
          \ }
  else
    let config = a:1
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


function! Test_Disassembly_Open_Close()
  " TODO: SKip neovim because the winbar changes the calculations
  call s:StartDebugging()
  call vimspector#ShowDisassembly()

  " By default we use a height of 20, so the PC is at line 20, which is
  " screenline 10
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:buf, 20, 1 )
  let winid = g:vimspector_session_windows.disassembly
  " But we have a winbar, which just overwrites the top line, so the first line
  " displayed is 11, and we lose one line
  call assert_equal( 11, getwininfo( winid )[0].topline )
  call assert_equal( 29, getwininfo( winid )[0].botline )
  call assert_equal( 19, getwininfo( winid )[0].height )
  quit

  call vimspector#ShowDisassembly()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:buf, 20, 1 )
  VimspectorReset
  call vimspector#test#setup#WaitForReset()

  call vimspector#test#setup#Reset()
  %bwipeout!
endfunction

function! Test_Disassembly_StepGranularity()
  " TODO: SKip neovim because the winbar changes the calculations
  call s:StartDebugging()
  call vimspector#ShowDisassembly()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:buf, 20, 1 )
  let winid = g:vimspector_session_windows.disassembly


  call vimspector#test#setup#Reset()
  %bwipeout!
endfunction

