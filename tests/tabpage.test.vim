function! SetUp()
  call vimspector#test#setup#SetUpWithMappings( 'HUMAN' )
endfunction

function! ClearDown()
  call vimspector#test#setup#ClearDown()
endfunction

function! Test_Step_With_Different_Tabpage()
  lcd testdata/cpp/simple
  edit simple.cpp

  " Add the breakpoint
  " TODO refactor FeedKeys
  15
  call assert_equal( 15, line( '.' ) )
  call feedkeys( "\<F9>", 'xt' )

  " Here we go. Start Debugging
  call feedkeys( "\<F5>", 'xt' )

  call assert_equal( 2, len( gettabinfo() ) )
  let vimspector_tabnr = tabpagenr()
  call WaitForAssert( {->
        \ assert_equal( 'simple.cpp', bufname( '%' ), 'Current buffer' )
        \ }, 10000 )
  call assert_equal( 15, line( '.' ), 'Current line' )
  call assert_equal( 1, col( '.' ), 'Current column' )

  " Switch to the other tab
  normal! gt

  call assert_notequal( vimspector_tabnr, tabpagenr() )

  " trigger some output by hacking into the vimspector python
  call py3eval( '_vimspector_session._outputView.Print( "server",'
            \ . '                                       "This is a test" )' )

  " Step - jumps back to our vimspector tab
  call feedkeys( "\<F10>", 'xt' )

  call WaitForAssert( {-> assert_equal( vimspector_tabnr, tabpagenr() ) } )
  call WaitForAssert( {-> assert_equal( 16, line( '.' ), 'Current line' ) } )
  call assert_equal( 'simple.cpp', bufname( '%' ), 'Current buffer' )
  call assert_equal( 1, col( '.' ), 'Current column' )

  call vimspector#test#setup#Reset()
  lcd -
  %bwipeout!
endfunction

function! Test_All_Buffers_Deleted_NoHidden()
  call ThisTestIsFlaky()

  set nohidden
  lcd testdata/cpp/simple
  edit simple.cpp

  let opts = #{ buflisted: v:true }

  let buffers_before = getbufinfo( opts )

  call setpos( '.', [ 0, 15, 1 ] )
  call vimspector#ToggleBreakpoint()
  call vimspector#Launch()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'simple.cpp', 15, 1 )
  call vimspector#test#signs#AssertPCIsAtLineInBuffer(
        \ 'simple.cpp',
        \ 15 )

  call vimspector#Reset()
  call vimspector#test#setup#WaitForReset()

  call WaitForAssert( {->
        \ assert_equal( len( buffers_before ), len( getbufinfo( opts ) ) ) } )

  set hidden&
  lcd -
  call vimspector#test#setup#Reset()
  %bwipe!
endfunction

function! Test_All_Buffers_Deleted_Hidden()
  call ThisTestIsFlaky()

  set hidden
  lcd testdata/cpp/simple
  edit simple.cpp

  let opts = #{ buflisted: v:true }

  let buffers_before = getbufinfo( opts )

  call setpos( '.', [ 0, 15, 1 ] )
  call vimspector#ToggleBreakpoint()
  call vimspector#Launch()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'simple.cpp', 15, 1 )
  call vimspector#test#signs#AssertPCIsAtLineInBuffer(
        \ 'simple.cpp',
        \ 15 )

  call vimspector#Reset()
  call vimspector#test#setup#WaitForReset()

  call WaitForAssert( {->
        \ assert_equal( len( buffers_before ), len( getbufinfo( opts ) ) ) } )

  set hidden&
  lcd -
  call vimspector#test#setup#Reset()
  %bwipe!
endfunction

function! Test_All_Buffers_Deleted_ToggleLog()
  set hidden
  let buffers_before = getbufinfo( #{ buflisted: 1 } )
  VimspectorToggleLog
  VimspectorToggleLog

  call WaitForAssert( {->
        \ assert_equal( len( buffers_before ),
        \               len( getbufinfo( #{ buflisted: 1 } ) ) ) } )

  call vimspector#test#setup#Reset()
  set hidden&
  %bwipe!
endfunction

let g:vimspector_test_install_done = 0

function! Test_All_Buffers_Deleted_Installer()
  set hidden
  let buffers_before = getbufinfo( #{ buflisted: 1 } )

  augroup Test_All_Buffers_Deleted_Installer
    au!
    au User VimspectorInstallSuccess let g:vimspector_test_install_done = 1
    au User VimspectorInstallFailed let g:vimspector_test_install_done = 1
  augroup END

  VimspectorUpdate

  " The test timeout will take care of this taking too long
  call WaitForAssert(
        \ { -> assert_equal( 1, g:vimspector_test_install_done ) },
        \ 120000 )

  call WaitForAssert( {->
        \ assert_equal( len( buffers_before ),
        \               len( getbufinfo( #{ buflisted: 1 } ) ) ) } )

  call vimspector#test#setup#Reset()
  set hidden&
  au! Test_All_Buffers_Deleted_Installer
  %bwipe!
endfunction
