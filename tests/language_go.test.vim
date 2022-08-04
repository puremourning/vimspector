function! SetUp()
  call vimspector#test#setup#SetUpWithMappings( v:null )
endfunction

function! ClearDown()
  call vimspector#test#setup#ClearDown()
endfunction

" Legacy vscode-go {{{

function! SetUp_Test_Go_Simple_Legacy()
  let g:vimspector_enable_mappings = 'HUMAN'
endfunction

function! Test_Go_Simple_Legacy()
  let fn='hello-world.go'
  lcd ../support/test/go/hello_world
  exe 'edit ' . fn
  call setpos( '.', [ 0, 4, 1 ] )

  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 4, 1 )
  call vimspector#test#signs#AssertSignGroupEmptyAtLine( 'VimspectorBP', 4 )

  " Add the breakpoint
  call feedkeys( "\<F9>", 'xt' )
  call vimspector#test#signs#AssertSignGroupSingletonAtLine( 'VimspectorBP',
                                                           \ 4,
                                                           \ 'vimspectorBP',
                                                           \ 9 )

  call setpos( '.', [ 0, 1, 1 ] )

  " Here we go. Start Debugging
  call vimspector#LaunchWithSettings( { 'configuration': 'run-legacy' } )
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 4, 1 )

  " Step
  call feedkeys( "\<F10>", 'xt' )

  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 5, 1 )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer( fn, 5 )
        \ } )

  call vimspector#test#setup#Reset()

  lcd -
  %bwipeout!
endfunction

function! Test_Go_Simple_Adhoc_Config_Legacy()
  let fn='hello-world.go'
  lcd ../support/test/go/hello_world
  exe 'edit ' . fn
  call setpos( '.', [ 0, 4, 1 ] )

  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 4, 1 )
  call vimspector#test#signs#AssertSignGroupEmptyAtLine( 'VimspectorBP', 4 )

  " Add the breakpoint
  call vimspector#ToggleBreakpoint()
  call vimspector#test#signs#AssertSignGroupSingletonAtLine( 'VimspectorBP',
                                                           \ 4,
                                                           \ 'vimspectorBP',
                                                           \ 9 )

  call setpos( '.', [ 0, 1, 1 ] )

  " Here we go. Start Debugging
  call vimspector#LaunchWithConfigurations({
  \  'run': {
  \    'adapter': 'vscode-go',
  \    'default': v:true,
  \    'configuration': {
  \      'request': 'launch',
  \      'program': '${workspaceRoot}/hello-world.go',
  \      'mode': 'debug',
  \      'trace': v:true,
  \      'env': { 'GO111MODULE': 'off' }
  \    }
  \  },
  \ })
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 4, 1 )

  " Step
  call vimspector#StepOver()

  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 5, 1 )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer( fn, 5 )
        \ } )

  call vimspector#test#setup#Reset()

  lcd -
  %bwipeout!
endfunction


function! Test_Run_To_Cursor_Legacy()
  let fn='hello-world.go'
  lcd ../support/test/go/hello_world
  exe 'edit ' . fn

  call vimspector#SetLineBreakpoint( fn, 4 )
  call vimspector#LaunchWithSettings( { 'configuration': 'run-legacy' } )
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 4, 1 )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer( fn, 4 )
        \ } )

  call cursor( 5, 1 )
  call vimspector#RunToCursor()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 5, 1 )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer( fn, 5 )
        \ } )

  call vimspector#test#setup#Reset()
  lcd -
  %bwipeout!
endfunction

" }}}
"
" Delve-dap {{{

function! SetUp_Test_Go_Simple_Delve()
  let g:vimspector_enable_mappings = 'HUMAN'
endfunction

function! Test_Go_Simple_Delve()
  let fn='hello-world.go'
  lcd ../support/test/go/hello_world
  exe 'edit ' . fn
  call setpos( '.', [ 0, 4, 1 ] )

  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 4, 1 )
  call vimspector#test#signs#AssertSignGroupEmptyAtLine( 'VimspectorBP', 4 )

  " Add the breakpoint
  call feedkeys( "\<F9>", 'xt' )
  call vimspector#test#signs#AssertSignGroupSingletonAtLine( 'VimspectorBP',
                                                           \ 4,
                                                           \ 'vimspectorBP',
                                                           \ 9 )

  call setpos( '.', [ 0, 1, 1 ] )

  " Here we go. Start Debugging
  call vimspector#LaunchWithSettings( { 'configuration': 'run-delve' } )
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 4, 1 )

  " Step
  call feedkeys( "\<F10>", 'xt' )

  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 5, 1 )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer( fn, 5 )
        \ } )

  call vimspector#test#setup#Reset()

  lcd -
  %bwipeout!
endfunction

function! Test_Go_Simple_Adhoc_Config_Delve()
  let fn='hello-world.go'
  lcd ../support/test/go/hello_world
  exe 'edit ' . fn
  call setpos( '.', [ 0, 4, 1 ] )

  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 4, 1 )
  call vimspector#test#signs#AssertSignGroupEmptyAtLine( 'VimspectorBP', 4 )

  " Add the breakpoint
  call vimspector#ToggleBreakpoint()
  call vimspector#test#signs#AssertSignGroupSingletonAtLine( 'VimspectorBP',
                                                           \ 4,
                                                           \ 'vimspectorBP',
                                                           \ 9 )

  call setpos( '.', [ 0, 1, 1 ] )

  " Here we go. Start Debugging
  call vimspector#LaunchWithConfigurations({
  \  'run': {
  \    'adapter': 'delve',
  \    'default': v:true,
  \    'configuration': {
  \      'request': 'launch',
  \      'program': '${workspaceRoot}/hello-world.go',
  \      'mode': 'debug',
  \      'trace': v:true,
  \      'env': { 'GO111MODULE': 'off' }
  \    }
  \  },
  \ })
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 4, 1 )

  " Step
  call vimspector#StepOver()

  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 5, 1 )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer( fn, 5 )
        \ } )

  call vimspector#test#setup#Reset()

  lcd -
  %bwipeout!
endfunction


function! Test_Run_To_Cursor_Delve()
  let fn='hello-world.go'
  lcd ../support/test/go/hello_world
  exe 'edit ' . fn

  call vimspector#SetLineBreakpoint( fn, 4 )
  call vimspector#LaunchWithSettings( { 'configuration': 'run-delve' } )
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 4, 1 )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer( fn, 4 )
        \ } )

  call cursor( 5, 1 )
  call vimspector#RunToCursor()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 5, 1 )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer( fn, 5 )
        \ } )

  call vimspector#test#setup#Reset()
  lcd -
  %bwipeout!
endfunction

function! Test_Restart_Delve()
  let fn='hello-world.go'
  lcd ../support/test/go/hello_world
  exe 'edit ' . fn
  call setpos( '.', [ 0, 4, 1 ] )

  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 4, 1 )
  call vimspector#test#signs#AssertSignGroupEmptyAtLine( 'VimspectorBP', 4 )

  " Add the breakpoint
  call vimspector#ToggleBreakpoint()
  call vimspector#test#signs#AssertSignGroupSingletonAtLine( 'VimspectorBP',
                                                           \ 4,
                                                           \ 'vimspectorBP',
                                                           \ 9 )

  call setpos( '.', [ 0, 1, 1 ] )

  " Here we go. Start Debugging
  call vimspector#LaunchWithSettings( { 'configuration': 'run-delve' } )
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 4, 1 )

  " Step
  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 5, 1 )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer( fn, 5 )
        \ } )

  call setpos( '.', [ 0, 1, 1 ] )
  call vimspector#Restart()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 4, 1 )

  " Step
  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 5, 1 )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer( fn, 5 )
        \ } )


  " TODO: check for the terminal?

  call vimspector#test#setup#Reset()
  lcd -
  %bwipeout!
endfunction

" }}}
"
" vim: foldmethod=marker
