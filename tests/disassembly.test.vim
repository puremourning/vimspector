let s:fn='testdata/cpp/simple/tiny.c'
let s:buf = '_vimspector_disassembly'
" Need to make this small enough that this many lines fit on the screen as the
" fixed position in this test require that.
let s:dlines = 5
if has( 'nvim' )
  " Making these tests work with neovim is tricky because for some reason it
  " always says "not enough room" whereas vim works with the same layout!
  let g:vimspector_enable_winbar = 0
  let s:offset = 1
else
  let s:offset = 0
endif
let s:dpc = s:dlines + s:offset

function! SetUp()
  let g:vimspector_disassembly_height = s:dlines
  call vimspector#test#setup#SetUpWithMappings( 'HUMAN' )
endfunction

function! TearDown()
  call vimspector#test#setup#TearDown()
endfunction

function! s:StartDebugging( ... )
  let config = #{
        \   fn: s:fn,
        \   line: 3,
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


function! Test_Disassembly_Open_Close()
  call s:StartDebugging()
  call vimspector#ShowDisassembly()

  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:buf, s:dpc, 1 )
  let winid = g:vimspector_session_windows.disassembly
  call assert_false( &wrap )
  call assert_inrange( getwininfo( winid )[ 0 ].topline,
                     \ getwininfo( winid )[ 0 ].botline,
                     \ s:dpc )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer(
            \ s:buf,
            \ s:dpc,
            \ 'VimspectorDisassembly' )
        \ } )
  quit

  call vimspector#ShowDisassembly()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:buf, s:dpc, 1 )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer(
            \ s:buf,
            \ s:dpc,
            \ 'VimspectorDisassembly' )
        \ } )
  VimspectorReset
  call vimspector#test#setup#WaitForReset()

  call vimspector#test#setup#Reset()
  %bwipeout!
endfunction

function! Test_Disassembly_StepGranularity_Mappings()
  call s:StartDebugging()
  call vimspector#ShowDisassembly()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:buf, s:dpc, 1 )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer(
            \ s:buf,
            \ s:dpc,
            \ 'VimspectorDisassembly' )
        \ } )
  let winid = g:vimspector_session_windows.disassembly

  " The default mappings (i.e. F10 etc.) behave according to the current window
  "
  " Step over instruction
  call cursor( 1, 1)
  call feedkeys( "\<F10>", 'xt' )
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:buf, s:dpc, 1 )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer(
            \ s:buf,
            \ s:dpc,
            \ 'VimspectorDisassembly' )
        \ } )

  " Jumps from within the disassembly view jump to the disassembly view
  call cursor( 1, 1)
  call vimspector#JumpToProgramCounter()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:buf, s:dpc, 1 )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer(
            \ s:buf,
            \ s:dpc,
            \ 'VimspectorDisassembly' )
        \ } )
  call assert_equal( 'vimspector-disassembly', &syntax )

  " Check we're still on the same source line (which just about works on the
  " supported architectures)

  call win_gotoid( g:vimspector_session_windows.code )
  call vimspector#JumpToProgramCounter()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, 3, 1 )

  " steps from code window are line steps
  call cursor( 1, 1 )
  call feedkeys( "\<F10>", 'xt' )
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, 4, 1 )

  call vimspector#test#setup#Reset()
  %bwipeout!
endfunction

function! Test_Disassembly_StepGranularity_API()
  call s:StartDebugging()
  call vimspector#ShowDisassembly()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:buf, s:dpc, 1 )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer(
            \ s:buf,
            \ s:dpc,
            \ 'VimspectorDisassembly' )
        \ } )
  let winid = g:vimspector_session_windows.disassembly

  " The default mappings (i.e. F10 etc.) behave according to the current window
  "
  " Step over instruction
  call cursor( 1, 1)
  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:buf, s:dpc, 1 )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer(
            \ s:buf,
            \ s:dpc,
            \ 'VimspectorDisassembly' )
        \ } )

  " Jumps from within the disassembly view jump to the disassembly view
  call cursor( 1, 1)
  call vimspector#JumpToProgramCounter()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:buf, s:dpc, 1 )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer(
            \ s:buf,
            \ s:dpc,
            \ 'VimspectorDisassembly' )
        \ } )

  " Check we're still on the same source line (which just about works on the
  " supported architectures)
  call win_gotoid( g:vimspector_session_windows.code )
  call vimspector#JumpToProgramCounter()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, 3, 1 )

  " steps from code window are line steps
  call cursor( 1, 1 )
  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, 4, 1 )

  call vimspector#test#setup#Reset()
  %bwipeout!
endfunction

function! Test_Disassembly_StepInGranularity_API()
  call s:StartDebugging()
  call vimspector#ShowDisassembly()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:buf, s:dpc, 1 )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer(
            \ s:buf,
            \ s:dpc,
            \ 'VimspectorDisassembly' )
        \ } )
  let winid = g:vimspector_session_windows.disassembly

  " The default mappings (i.e. F10 etc.) behave according to the current window
  "
  " Step over instruction
  call cursor( 1, 1)
  call vimspector#StepInto()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:buf, s:dpc, 1 )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer(
            \ s:buf,
            \ s:dpc,
            \ 'VimspectorDisassembly' )
        \ } )

  " Jumps from within the disassembly view jump to the disassembly view
  call cursor( 1, 1)
  call vimspector#JumpToProgramCounter()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:buf, s:dpc, 1 )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer(
            \ s:buf,
            \ s:dpc,
            \ 'VimspectorDisassembly' )
        \ } )

  " Check we're still on the same source line (which just about works on the
  " supported architectures)
  call win_gotoid( g:vimspector_session_windows.code )
  call vimspector#JumpToProgramCounter()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, 3, 1 )

  " steps from code window are line steps
  call cursor( 1, 1 )
  call vimspector#StepInto()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, 4, 1 )

  call vimspector#test#setup#Reset()
  %bwipeout!
endfunction

function! Test_Disassembly_StepGranularity_API_CodeLLDB()
  call s:StartDebugging( #{
        \ col: v:null,
        \ launch: #{ configuration: 'CodeLLDB' }
        \ } )
  call vimspector#ShowDisassembly()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:buf, s:dpc, 1 )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer(
            \ s:buf,
            \ s:dpc,
            \ 'VimspectorDisassembly' )
        \ } )
  let winid = g:vimspector_session_windows.disassembly

  " The default mappings (i.e. F10 etc.) behave according to the current window
  "
  " Step over instruction
  call cursor( 1, 1)
  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:buf, s:dpc, 1 )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer(
            \ s:buf,
            \ s:dpc,
            \ 'VimspectorDisassembly' )
        \ } )

  " Jumps from within the disassembly view jump to the disassembly view
  call cursor( 1, 1)
  call vimspector#JumpToProgramCounter()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:buf, s:dpc, 1 )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer(
            \ s:buf,
            \ s:dpc,
            \ 'VimspectorDisassembly' )
        \ } )

  " Check we're still on the same source line (which just about works on the
  " supported architectures)
  "
  " NOTE: codelldb is so good, it actually includes the column number and moves
  " us to the + operator (on arm64 at least). But this isn't consistent across
  " macOS and linux and arm and x86, so we don't check for it.
  "
  call win_gotoid( g:vimspector_session_windows.code )
  call vimspector#JumpToProgramCounter()
  " call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, 3, 18 )
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, 3, v:null )

  " steps from code window are line steps
  call cursor( 1, 1 )
  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, 4, 10 )

  call vimspector#test#setup#Reset()
  %bwipeout!
endfunction

function! Test_Disassembly_StepInGranularity_API_Direct()
  call s:StartDebugging()
  call vimspector#ShowDisassembly()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:buf, s:dpc, 1 )
  let winid = g:vimspector_session_windows.disassembly

  " The default mappings (i.e. F10 etc.) behave according to the current window
  "
  " Step over instruction
  call win_gotoid( g:vimspector_session_windows.code )
  call vimspector#StepIOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, 3, 1 )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer( s:fn, 3 )
        \ } )

  " Check we're still on the same source line (which just about works on the
  " steps from code window are line steps
  call win_gotoid( winid )
  call vimspector#StepSOver()
  call cursor(1,1)
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:buf, s:dpc, 1 )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer( s:fn, 4 )
        \ } )

  call win_gotoid( g:vimspector_session_windows.code )
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, 4, 1 )

  call vimspector#test#setup#Reset()
  %bwipeout!
endfunction

function! Test_Disassembly_StepInGranularity_API_Direct_CodeLLDB()
  call s:StartDebugging( #{
        \ col: v:null,
        \ launch: #{ configuration: 'CodeLLDB' }
        \ } )
  call vimspector#ShowDisassembly()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:buf, s:dpc, 1 )
  let winid = g:vimspector_session_windows.disassembly

  " The default mappings (i.e. F10 etc.) behave according to the current window
  "
  " Step over instruction
  call win_gotoid( g:vimspector_session_windows.code )
  call vimspector#StepIOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, 3, v:null )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer( s:fn, 3 )
        \ } )

  " Check we're still on the same source line (which just about works on the
  " steps from code window are line steps
  call win_gotoid( winid )
  call vimspector#StepSOver()
  call cursor(1,1)
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:buf, s:dpc, 1 )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer( s:fn, 4 )
        \ } )

  call win_gotoid( g:vimspector_session_windows.code )
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, 4, 10 )

  call vimspector#test#setup#Reset()
  %bwipeout!
endfunction
