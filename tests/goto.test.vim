function! SetUp()
  call vimspector#test#setup#SetUpWithMappings( v:null )
endfunction

function! TearDown()
  call vimspector#test#setup#TearDown()
endfunction

function! Test_GoTo_Single()
  lcd ../support/test/python/simple_python
  edit main.py

  call vimspector#SetLineBreakpoint( 'main.py', 26 )
  call vimspector#LaunchWithSettings( { 'configuration': 'run' } )
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'main.py', 26, 1 )
  call vimspector#test#signs#AssertPCIsAtLineInBuffer( 'main.py', 26 )

  call cursor( 23, 1 )
  call vimspector#GoToCurrentLine()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'main.py', 23, 1 )
  call WaitForAssert( { ->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer( 'main.py', 23 ) } )

  call cursor( 25, 1 )
  call vimspector#GoToCurrentLine()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'main.py', 25, 1 )
  call WaitForAssert( { ->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer( 'main.py', 25 ) } )

  call vimspector#test#setup#Reset()
  lcd -
  %bwipe!
endfunction

function! Test_GoTo_Single_Mapping()
  lcd ../support/test/python/simple_python
  edit main.py

  call vimspector#SetLineBreakpoint( 'main.py', 26 )
  call vimspector#LaunchWithSettings( { 'configuration': 'run' } )
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'main.py', 26, 1 )
  call vimspector#test#signs#AssertPCIsAtLineInBuffer( 'main.py', 26 )

  call cursor( 23, 1 )
  nmap <Leader>g <Plug>VimspectorGoToCurrentLine
  execute 'normal ,g'
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'main.py', 23, 1 )
  call WaitForAssert( { ->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer( 'main.py', 23 ) } )

  call cursor( 25, 1 )
  call vimspector#GoToCurrentLine()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'main.py', 25, 1 )
  call WaitForAssert( { ->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer( 'main.py', 25 ) } )

  call vimspector#test#setup#Reset()
  silent! nunmap <Leader>g
  lcd -
  %bwipe!
endfunction

function! Test_GoTo_FailsGoTo()
  lcd ../support/test/python/simple_python
  edit main.py

  call vimspector#SetLineBreakpoint( 'main.py', 23 )
  call vimspector#LaunchWithSettings( { 'configuration': 'run' } )
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'main.py', 23, 1 )
  call WaitForAssert( { ->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer( 'main.py', 23 ) } )

  call cursor( 15, 10 )
  call vimspector#GoToCurrentLine()
  sleep 100m
  call WaitForAssert( { ->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer( 'main.py', 23 ) } )

  call vimspector#StepOver()
  call WaitForAssert( { ->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer( 'main.py', 25 ) } )

  call vimspector#test#setup#Reset()
  lcd -
  %bwipe!
endfunction

function! Test_GoTo_Multiple()
  " TODO: Can't seem to find any adapters that actually support multiple
endfunction
