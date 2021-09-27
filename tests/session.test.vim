function! SetUp()
  call vimspector#test#setup#SetUpWithMappings( 'HUMAN' )
endfunction

function! ClearDown()
  call vimspector#test#setup#ClearDown()
endfunction

function! Test_Save_Session_Specify_Path_Not_Running_Breakpoints()
  let moo = 'moo.py'
  let cow = 'cow.py'
  lcd ../support/test/python/multiple_files

  call vimspector#SetLineBreakpoint( moo, 6 )
  call vimspector#SetLineBreakpoint( moo, 9, { 'logMessage': 'test' } )
  call vimspector#SetLineBreakpoint( cow, 15, { 'condition': '1==2' } )

  execute 'edit' moo
  call WaitForAssert( {->
        \vimspector#test#signs#AssertSignGroupSingletonAtLine(
          \ 'VimspectorBP',
          \ 6,
          \ 'vimspectorBP',
          \ 9 ) } )
  call WaitForAssert( {->
        \vimspector#test#signs#AssertSignGroupSingletonAtLine(
          \ 'VimspectorBP',
          \ 9,
          \ 'vimspectorBPLog',
          \ 9 ) } )

  execute 'edit' cow
  call WaitForAssert( {->
        \vimspector#test#signs#AssertSignGroupSingletonAtLine(
          \ 'VimspectorBP',
          \ 15,
          \ 'vimspectorBPCond',
          \ 9 ) } )

  let save_file = tempname()
  execute 'VimspectorMkSession' save_file
  call assert_true( filereadable( save_file ) )
  " check it looks valid ?
  call json_decode( join( readfile( save_file ), '\n' ) )
  call vimspector#ClearBreakpoints()

  execute 'edit' moo
  call WaitForAssert( {->
        \vimspector#test#signs#AssertSignGroupEmptyAtLine(
          \ 'VimspectorBP',
          \ 6 ) } )
  call WaitForAssert( {->
        \vimspector#test#signs#AssertSignGroupEmptyAtLine(
          \ 'VimspectorBP',
          \ 9 ) } )

  execute 'edit' cow
  call WaitForAssert( {->
        \vimspector#test#signs#AssertSignGroupEmptyAtLine(
          \ 'VimspectorBP',
          \ 15 ) } )

  execute 'VimspectorLoadSession' save_file

  execute 'edit' moo
  call WaitForAssert( {->
        \vimspector#test#signs#AssertSignGroupSingletonAtLine(
          \ 'VimspectorBP',
          \ 6,
          \ 'vimspectorBP',
          \ 9 ) } )
  call WaitForAssert( {->
        \vimspector#test#signs#AssertSignGroupSingletonAtLine(
          \ 'VimspectorBP',
          \ 9,
          \ 'vimspectorBPLog',
          \ 9 ) } )

  execute 'edit' cow
  call WaitForAssert( {->
        \vimspector#test#signs#AssertSignGroupSingletonAtLine(
          \ 'VimspectorBP',
          \ 15,
          \ 'vimspectorBPCond',
          \ 9 ) } )

  call vimspector#test#setup#Reset()
  lcd -
  silent! call delete( save_file )
  %bwipeout!
endfunction

function! Test_Save_Session_Specify_Path_While_Running_Breakpoints()
  let moo = 'moo.py'
  let cow = 'cow.py'
  lcd ../support/test/python/multiple_files

  call vimspector#SetLineBreakpoint( moo, 6 )
  call vimspector#SetLineBreakpoint( moo, 9, { 'logMessage': 'test' } )
  call vimspector#SetLineBreakpoint( cow, 15, { 'condition': '1==2' } )

  execute 'edit' moo
  call WaitForAssert( {->
        \vimspector#test#signs#AssertSignGroupSingletonAtLine(
          \ 'VimspectorBP',
          \ 6,
          \ 'vimspectorBP',
          \ 9 ) } )
  call WaitForAssert( {->
        \vimspector#test#signs#AssertSignGroupSingletonAtLine(
          \ 'VimspectorBP',
          \ 9,
          \ 'vimspectorBPLog',
          \ 9 ) } )

  execute 'edit' cow
  call WaitForAssert( {->
        \vimspector#test#signs#AssertSignGroupSingletonAtLine(
          \ 'VimspectorBP',
          \ 15,
          \ 'vimspectorBPCond',
          \ 9 ) } )

  let save_file = tempname()
  call vimspector#WriteSessionFile( save_file )
  call vimspector#ClearBreakpoints()

  call vimspector#Launch()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( moo, 1, 1 )
  call vimspector#test#signs#AssertPCIsAtLineInBuffer( moo, 1 )

  call vimspector#ReadSessionFile( save_file )

  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( moo, 1, 1 )
  call vimspector#test#signs#AssertPCIsAtLineInBuffer( moo, 1 )

  call WaitForAssert( {->
        \vimspector#test#signs#AssertSignGroupSingletonAtLine(
          \ 'VimspectorCode',
          \ 6,
          \ 'vimspectorBP',
          \ 9 ) } )
  call WaitForAssert( {->
        \vimspector#test#signs#AssertSignGroupSingletonAtLine(
          \ 'VimspectorCode',
          \ 9,
          \ 'vimspectorBP',
          \ 9 ) } )

  execute 'edit' cow
  call WaitForAssert( {->
        \vimspector#test#signs#AssertSignGroupSingletonAtLine(
          \ 'VimspectorCode',
          \ 15,
          \ 'vimspectorBP',
          \ 9 ) } )

  call vimspector#Continue()

  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( moo, 6, 1 )
  call vimspector#test#signs#AssertPCIsAtLineInBuffer( moo, 6 )

  call vimspector#test#setup#Reset()
  lcd -
  silent! call delete( save_file )
  %bwipeout!
endfunction

function! SetUp_Test_Save_Session_Specify_Path_While_Running_Watches()
  let g:vimspector_session_file_name = tempname()
endfunction

function! TearDown_Test_Save_Session_Specify_Path_While_Running_Watches()
  unlet g:vimspector_session_file_name
endfunction

function! Test_Save_Session_Specify_Path_While_Running_Watches()
  let moo = 'moo.py'
  let cow = 'cow.py'
  lcd ../support/test/python/multiple_files
  call vimspector#Launch()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( moo, 1, 1 )
  call vimspector#test#signs#AssertPCIsAtLineInBuffer( moo, 1 )

  call cursor( [ 6, 1 ] )
  call vimspector#RunToCursor()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( moo, 6, 1 )
  call WaitForAssert( { ->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer( moo, 6 )  } )

  call vimspector#AddWatch( 'i' )
  call WaitForAssert( {->
        \   assert_equal(
        \     [
        \         'Watches: ----',
        \         'Expression: i',
        \         ' *- Result: 1',
        \     ],
        \     getbufline( winbufnr( g:vimspector_session_windows.watches ),
        \                 1,
        \                 '$' )
        \   )
        \ } )

  VimspectorMkSession
  call vimspector#test#setup#Reset()

  VimspectorLoadSession
  call vimspector#Launch()

  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( moo, 1, 1 )
  call vimspector#test#signs#AssertPCIsAtLineInBuffer( moo, 1 )
  call cursor( [ 6, 1 ] )
  call vimspector#RunToCursor()

  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( moo, 6, 1 )
  call WaitForAssert( { ->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer( moo, 6 ) } )

  " FIXME: Fails here, i think because we add the watch with the 'wrong'
  " frame ID, so this just gets NameError" name 'i' is not defined.
  call WaitForAssert( {->
        \   assert_equal(
        \     [
        \         'Watches: ----',
        \         'Expression: i',
        \         ' *- Result: 1',
        \     ],
        \     getbufline( winbufnr( g:vimspector_session_windows.watches ),
        \                 1,
        \                 '$' )
        \   )
        \ } )


  silent! call delete( g:vimspector_session_file_name )
  call vimspector#test#setup#Reset()
  lcd -
  %bwipeout!
endfunction
