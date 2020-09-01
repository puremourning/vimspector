function! SetUp()
  call vimspector#test#setup#SetUpWithMappings( v:none )
endfunction

function! ClearDown()
  call vimspector#test#setup#ClearDown()
endfunction

function! SetUp_Test_Python_Simple()
  let g:vimspector_enable_mappings = 'HUMAN'
endfunction

function! Test_Python_Simple()
  let fn='main.py'
  lcd ../support/test/python/simple_python
  exe 'edit ' . fn
  call setpos( '.', [ 0, 6, 1 ] )

  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 6, 1 )
  call vimspector#test#signs#AssertSignGroupEmptyAtLine( 'VimspectorBP', 6 )

  " Add the breakpoint
  call feedkeys( "\<F9>", 'xt' )
  call vimspector#test#signs#AssertSignGroupSingletonAtLine( 'VimspectorBP',
                                                           \ 6,
                                                           \ 'vimspectorBP',
                                                           \ 9 )

  call setpos( '.', [ 0, 1, 1 ] )

  " Here we go. Start Debugging
  call vimspector#LaunchWithSettings( { 'configuration': 'run' } )
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 6, 1 )

  " Step
  call feedkeys( "\<F10>", 'xt' )

  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 7, 1 )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer( fn, 7 )
        \ } )

  call vimspector#test#setup#Reset()

  lcd -
  %bwipeout!
endfunction

function! SetUp_Test_Python_Remote_Attach()
  let g:vimspector_enable_mappings = 'HUMAN'
endfunction

function! Test_Python_Remote_Attach()
  lcd ../support/test/python/simple_python
  let fn='main.py'
  exe 'edit ' . fn

  let ready = v:false
  function! ReceiveFromLauncher( ch, data ) closure
    if a:data ==# '*** Launching ***'
      let ready = v:true
    endif
  endfunction

  let jobid = job_start( [ './run_with_debugpy' ], {
        \ 'out_mode': 'nl',
        \ 'out_cb': funcref( 'ReceiveFromLauncher' ),
        \ } )

  " Wait up to 60s for the debugee to be launched (the script faffs with
  " virtualenvs etc.)
  call WaitFor( {-> ready == v:true }, 60000 )

  call setpos( '.', [ 0, 6, 1 ] )

  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 6, 1 )
  call vimspector#test#signs#AssertSignGroupEmptyAtLine( 'VimspectorBP', 6 )

  " Add the breakpoint
  call feedkeys( "\<F9>", 'xt' )
  call vimspector#test#signs#AssertSignGroupSingletonAtLine( 'VimspectorBP',
                                                           \ 6,
                                                           \ 'vimspectorBP',
                                                           \ 9 )

  call setpos( '.', [ 0, 1, 1 ] )

  " Here we go. Start Debugging (note will wait up to 10s for the script to do
  " its virtualenv thing)
  call vimspector#LaunchWithSettings( {
        \   'configuration': 'attach',
        \   'port': 5678,
        \   'host': 'localhost'
        \ } )
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 6, 1 )

  " Step
  call feedkeys( "\<F10>", 'xt' )

  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 7, 1 )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer( fn, 7 )
        \ } )

  call vimspector#test#setup#Reset()
  call job_stop( jobid )
  lcd -
  %bwipeout!
endfunction
