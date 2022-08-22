function! SetUp()
  call vimspector#test#setup#SetUpWithMappings( 'HUMAN' )
endfunction

function! TearDown()
  call vimspector#test#setup#TearDown()
endfunction

function! Test_Save_Session_Specify_Path_Not_Running_LineBreakpoints()
  lcd ../support/test/python/multiple_files
  let moo = getcwd() . '/moo.py'
  let cow = getcwd() . '/cow.py'

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

  " change directory then load, ensure that we find the right file for the
  " breakpoint
  lcd ../
  %bwipeout!
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

function! Test_Save_Session_Function_Breakpoints()
  " TODO
endfunction

function! Test_Save_Session_Exception_Breakpoints()
  " TODO
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

  call vimspector#Continue()

  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( moo, 6, 1 )
  call vimspector#test#signs#AssertPCIsAtLineInBuffer( moo, 6 )

  call vimspector#test#setup#Reset()
  lcd -
  silent! call delete( save_file )
  %bwipeout!
endfunction

function! SetUp_Test_Save_Session_NoSpecify_Path_While_Running_Watches()
  let g:vimspector_session_file_name = tempname()
endfunction

function! TearDown_Test_Save_NoSession_Specify_Path_While_Running_Watches()
  unlet g:vimspector_session_file_name
endfunction

function! Test_Save_Session_NoSpecify_Path_While_Running_Watches()
  call SkipNeovim()
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

function! Test_Save_User_Choices()
  " TODO
endfunction

function! Test_Load_Session_Add_Breakpoint_In_New_File()
  lcd ../support/test/python/multiple_files
  let moo = getcwd() . '/moo.py'
  let cow = getcwd() . '/cow.py'

  execute 'edit' moo
  call vimspector#SetLineBreakpoint( moo, 6 )
  call vimspector#SetLineBreakpoint( moo, 9, { 'logMessage': 'test' } )

  call WaitForAssert( {->
        \vimspector#test#signs#AssertSignGroupSingletonAtLine(
          \ 'VimspectorBP',
          \ 6,
          \ 'vimspectorBP',
          \ 9 ) } )

  call append( 4, [ '  # test' ] )

  call WaitForAssert( {->
        \vimspector#test#signs#AssertSignGroupSingletonAtLine(
          \ 'VimspectorBP',
          \ 7,
          \ 'vimspectorBP',
          \ 9 ) } )

  let save_file = tempname()
  execute 'VimspectorMkSession' save_file
  call assert_true( filereadable( save_file ) )
  " check it looks valid ?
  let data = json_decode( join( readfile( save_file ), '\n' ) )
  call assert_equal( 7, data.breakpoints.line[ moo ][ 0 ].line )
  call vimspector#ClearBreakpoints()

  call WaitForAssert( {->
        \vimspector#test#signs#AssertSignGroupEmptyAtLine(
          \ 'VimspectorBP',
          \ 7 ) } )

  execute 'VimspectorLoadSession' save_file

  call WaitForAssert( {->
        \vimspector#test#signs#AssertSignGroupSingletonAtLine(
          \ 'VimspectorBP',
          \ 7,
          \ 'vimspectorBP',
          \ 9 ) } )

  execute 'spl' cow
  call cursor( [ 2, 1 ] )
  call vimspector#ToggleBreakpoint()

  call WaitForAssert( {->
        \vimspector#test#signs#AssertSignGroupSingletonAtLine(
          \ 'VimspectorBP',
          \ 2,
          \ 'vimspectorBP',
          \ 9 ) } )

  call append( 0, [ '', '' ] )

  VimspectorMkSession
  VimspectorLoadSession

  call WaitForAssert( {->
        \vimspector#test#signs#AssertSignGroupSingletonAtLine(
          \ 'VimspectorBP',
          \ 4,
          \ 'vimspectorBP',
          \ 9 ) } )


  call vimspector#test#setup#Reset()
  silent! call delete( save_file )
  lcd -
  %bwipeout!
endfunction
