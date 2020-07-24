let s:fn='../support/test/python/simple_python/main.py'

function! SetUp()
  call vimspector#test#setup#SetUpWithMappings( 'HUMAN' )
endfunction

function! ClearDown()
  call vimspector#test#setup#ClearDown()
endfunction

function! s:StartDebugging()
  exe 'edit ' . s:fn
  call setpos( '.', [ 0, 23, 1 ] )
  call vimspector#ToggleBreakpoint()
  call vimspector#LaunchWithSettings( { 'configuration': 'run' } )
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, 23, 1 )
endfunction

function! Test_StandardLayout()
  call s:StartDebugging()

  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, 25, 1 )

  call assert_equal(
        \ [ 'row', [
        \   [ 'col', [
        \     [ 'leaf', g:vimspector_session_windows.variables ],
        \     [ 'leaf', g:vimspector_session_windows.watches ],
        \     [ 'leaf', g:vimspector_session_windows.stack_trace ],
        \   ] ],
        \   [ 'col', [
        \     [ 'row', [
        \       [ 'leaf', g:vimspector_session_windows.code ],
        \       [ 'leaf', g:vimspector_session_windows.terminal ],
        \     ] ],
        \     [ 'leaf', g:vimspector_session_windows.output ],
        \   ] ]
        \ ] ],
        \ winlayout( g:vimspector_session_windows.tabpage ) )

  call vimspector#test#setup#Reset()
  %bwipe!
endfunction

function! Test_CloseVariables()
  call s:StartDebugging()

  call win_execute( g:vimspector_session_windows.variables, 'q' )
  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, 25, 1 )

  call assert_equal(
        \ [ 'row', [
        \   [ 'col', [
        \     [ 'leaf', g:vimspector_session_windows.watches ],
        \     [ 'leaf', g:vimspector_session_windows.stack_trace ],
        \   ] ],
        \   [ 'col', [
        \     [ 'row', [
        \       [ 'leaf', g:vimspector_session_windows.code ],
        \       [ 'leaf', g:vimspector_session_windows.terminal ],
        \     ] ],
        \     [ 'leaf', g:vimspector_session_windows.output ],
        \   ] ]
        \ ] ],
        \ winlayout( g:vimspector_session_windows.tabpage ) )

  call vimspector#test#setup#Reset()
  %bwipe!
endfunction

function! Test_CloseWatches()
  call s:StartDebugging()

  call win_execute( g:vimspector_session_windows.watches, 'q' )
  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, 25, 1 )

  " Add a wtch
  call vimspector#AddWatch( 't' )
  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, 26, 1 )

  call assert_equal(
        \ [ 'row', [
        \   [ 'col', [
        \     [ 'leaf', g:vimspector_session_windows.variables ],
        \     [ 'leaf', g:vimspector_session_windows.stack_trace ],
        \   ] ],
        \   [ 'col', [
        \     [ 'row', [
        \       [ 'leaf', g:vimspector_session_windows.code ],
        \       [ 'leaf', g:vimspector_session_windows.terminal ],
        \     ] ],
        \     [ 'leaf', g:vimspector_session_windows.output ],
        \   ] ]
        \ ] ],
        \ winlayout( g:vimspector_session_windows.tabpage ) )

  " Replace the variables view with a watches view!
  call win_execute( g:vimspector_session_windows.variables,
                  \ 'bu vimspector.Watches' )

  " Delete a watch expression
  call win_gotoid( g:vimspector_session_windows.variables )
  call setpos( '.', [ 0, 3, 1 ] )
  call feedkeys( "\<Del>", 'xt' )

  call WaitForAssert( {->
        \   assert_equal(
        \     [
        \         'Watches: ----',
        \     ],
        \     getbufline( winbufnr( g:vimspector_session_windows.variables ),
        \                 1,
        \                 '$' )
        \   )
        \ } )


  call vimspector#StepInto()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, 13, 1 )
  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, 14, 1 )
  call vimspector#AddWatch( 'i' )

  call WaitForAssert( {->
        \   assert_equal(
        \     [
        \         'Watches: ----',
        \         'Expression: i',
        \         ' *- Result: 0',
        \     ],
        \     getbufline( winbufnr( g:vimspector_session_windows.variables ),
        \                 1,
        \                 '$' )
        \   )
        \ } )

  call vimspector#AddWatch( 'i+1' )

  call WaitForAssert( {->
        \   assert_equal(
        \     [
        \         'Watches: ----',
        \         'Expression: i',
        \         '  - Result: 0',
        \         'Expression: i+1',
        \         ' *- Result: 1',
        \     ],
        \     getbufline( winbufnr( g:vimspector_session_windows.variables ),
        \                 1,
        \                 '$' )
        \   )
        \ } )

  call vimspector#AddWatch( 'i+2' )

  call WaitForAssert( {->
        \   assert_equal(
        \     [
        \         'Watches: ----',
        \         'Expression: i',
        \         '  - Result: 0',
        \         'Expression: i+1',
        \         '  - Result: 1',
        \         'Expression: i+2',
        \         ' *- Result: 2',
        \     ],
        \     getbufline( winbufnr( g:vimspector_session_windows.variables ),
        \                 1,
        \                 '$' )
        \   )
        \ } )

  " Delete that middle watch
  call win_gotoid( g:vimspector_session_windows.variables )
  call setpos( '.', [ 0, 4, 1 ] )
  call vimspector#DeleteWatch()

  call WaitForAssert( {->
        \   assert_equal(
        \     [
        \         'Watches: ----',
        \         'Expression: i',
        \         '  - Result: 0',
        \         'Expression: i+2',
        \         ' *- Result: 2',
        \     ],
        \     getbufline( winbufnr( g:vimspector_session_windows.variables ),
        \                 1,
        \                 '$' )
        \   )
        \ } )

  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, 15, 1 )
  call WaitForAssert( {->
        \   assert_equal(
        \     [
        \         'Watches: ----',
        \         'Expression: i',
        \         '  - Result: 0',
        \         'Expression: i+2',
        \         '  - Result: 2',
        \     ],
        \     getbufline( winbufnr( g:vimspector_session_windows.variables ),
        \                 1,
        \                 '$' )
        \   )
        \ } )

  " Delete the top watch
  call win_gotoid( g:vimspector_session_windows.variables )
  call setpos( '.', [ 0, 3, 1 ] )
  call vimspector#DeleteWatch()

  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, 13, 1 )
  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, 14, 1 )
  call WaitForAssert( {->
        \   assert_equal(
        \     [
        \         'Watches: ----',
        \         'Expression: i+2',
        \         ' *- Result: 3',
        \     ],
        \     getbufline( winbufnr( g:vimspector_session_windows.variables ),
        \                 1,
        \                 '$' )
        \   )
        \ } )
  call vimspector#test#setup#Reset()
  %bwipe!
endfunction

function! Test_CloseStackTrace()
  call s:StartDebugging()

  call win_execute( g:vimspector_session_windows.stack_trace, 'q' )
  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, 25, 1 )

  call assert_equal(
        \ [ 'row', [
        \   [ 'col', [
        \     [ 'leaf', g:vimspector_session_windows.variables ],
        \     [ 'leaf', g:vimspector_session_windows.watches ],
        \   ] ],
        \   [ 'col', [
        \     [ 'row', [
        \       [ 'leaf', g:vimspector_session_windows.code ],
        \       [ 'leaf', g:vimspector_session_windows.terminal ],
        \     ] ],
        \     [ 'leaf', g:vimspector_session_windows.output ],
        \   ] ]
        \ ] ],
        \ winlayout( g:vimspector_session_windows.tabpage ) )

  call vimspector#test#setup#Reset()
  %bwipe!
endfunction

function! Test_CloseOutput()
  call s:StartDebugging()

  call win_execute( g:vimspector_session_windows.output, 'q' )
  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, 25, 1 )

  call assert_equal(
        \ [ 'row', [
        \   [ 'col', [
        \     [ 'leaf', g:vimspector_session_windows.variables ],
        \     [ 'leaf', g:vimspector_session_windows.watches ],
        \     [ 'leaf', g:vimspector_session_windows.stack_trace ],
        \   ] ],
        \   [ 'leaf', g:vimspector_session_windows.code ],
        \   [ 'leaf', g:vimspector_session_windows.terminal ],
        \ ] ],
        \ winlayout( g:vimspector_session_windows.tabpage ) )

  call vimspector#test#setup#Reset()
  %bwipe!
endfunction

function! Test_CloseOutput_Early()
  augroup TestCustomUI
    au!
    au User VimspectorUICreated
          \ call win_execute( g:vimspector_session_windows.output, 'q' )
  augroup END

  call s:StartDebugging()

  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, 25, 1 )

  call assert_equal(
        \ [ 'row', [
        \   [ 'col', [
        \     [ 'leaf', g:vimspector_session_windows.variables ],
        \     [ 'leaf', g:vimspector_session_windows.watches ],
        \     [ 'leaf', g:vimspector_session_windows.stack_trace ],
        \   ] ],
        \   [ 'leaf', g:vimspector_session_windows.code ],
        \   [ 'leaf', g:vimspector_session_windows.terminal ],
        \ ] ],
        \ winlayout( g:vimspector_session_windows.tabpage ) )

  " Open it again!
  let g:vimspector_bottombar_height = 5
  VimspectorShowOutput Console
  call assert_equal(
        \ [ 'col', [
        \   [ 'row', [
        \     [ 'col', [
        \       [ 'leaf', g:vimspector_session_windows.variables ],
        \       [ 'leaf', g:vimspector_session_windows.watches ],
        \       [ 'leaf', g:vimspector_session_windows.stack_trace ],
        \     ] ],
        \     [ 'leaf', g:vimspector_session_windows.code ],
        \     [ 'leaf', g:vimspector_session_windows.terminal ],
        \   ] ],
        \   [ 'leaf', g:vimspector_session_windows.output ]
        \ ] ],
        \ winlayout( g:vimspector_session_windows.tabpage ) )

  " The actual height reported is the number of lines visible. The WinBar takes
  " 1 screen row, so g:vimspector_bottombar_height -1
  call assert_equal( 4, winheight( g:vimspector_session_windows.output ) )

  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, 26, 1 )

  au! TestCustomUI
  call vimspector#test#setup#Reset()
  %bwipe!
endfunction


function! Test_CustomUI()
  augroup TestCustomUI
    au!
    au User VimspectorUICreated
          \ call win_execute( g:vimspector_session_windows.watches, 'q' )
  augroup END

  call s:StartDebugging()

  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, 25, 1 )

  " Add a watch
  call vimspector#AddWatch( 't' )
  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, 26, 1 )

  call assert_equal(
        \ [ 'row', [
        \   [ 'col', [
        \     [ 'leaf', g:vimspector_session_windows.variables ],
        \     [ 'leaf', g:vimspector_session_windows.stack_trace ],
        \   ] ],
        \   [ 'col', [
        \     [ 'row', [
        \       [ 'leaf', g:vimspector_session_windows.code ],
        \       [ 'leaf', g:vimspector_session_windows.terminal ],
        \     ] ],
        \     [ 'leaf', g:vimspector_session_windows.output ],
        \   ] ]
        \ ] ],
        \ winlayout( g:vimspector_session_windows.tabpage ) )

  au! TestCustomUI
  call vimspector#test#setup#Reset()
  %bwipe!
endfunction


function! s:CustomWinBar()
    call win_gotoid( g:vimspector_session_windows.code)
    aunmenu WinBar
    nnoremenu WinBar.▷\ ᶠ⁵ :call vimspector#Continue()<CR>
    nnoremenu WinBar.↷\ ᶠ¹⁰ :call vimspector#StepOver()<CR>
    nnoremenu WinBar.↓\ ᶠ¹¹ :call vimspector#StepInto()<CR>
    nnoremenu WinBar.↑\ ˢᶠ¹¹ :call vimspector#StepOut()<CR>
    nnoremenu WinBar.❘❘\ ᶠ⁶ :call vimspector#Pause()<CR>
    nnoremenu WinBar.□\ ˢᶠ⁵ :call vimspector#Stop()<CR>
    nnoremenu WinBar.⟲\ ᶜˢᶠ⁵ :call vimspector#Restart()<CR>
    nnoremenu WinBar.✕\ ᶠ⁸ :call vimspector#Reset()<CR>
endfunction


function! Test_CustomWinBar()
  augroup TestCustomWinBar
    au!
    au User VimspectorUICreated
          \ call win_execute( g:vimspector_session_windows.watches, 'q' )
    au User VimspectorUICreated call s:CustomWinBar()
  augroup END

  call s:StartDebugging()

  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, 25, 1 )

  call assert_equal(
        \ [ 'row', [
        \   [ 'col', [
        \     [ 'leaf', g:vimspector_session_windows.variables ],
        \     [ 'leaf', g:vimspector_session_windows.stack_trace ],
        \   ] ],
        \   [ 'col', [
        \     [ 'row', [
        \       [ 'leaf', g:vimspector_session_windows.code ],
        \       [ 'leaf', g:vimspector_session_windows.terminal ],
        \     ] ],
        \     [ 'leaf', g:vimspector_session_windows.output ],
        \   ] ]
        \ ] ],
        \ winlayout( g:vimspector_session_windows.tabpage ) )

  au! TestCustomWinBar
  call vimspector#test#setup#Reset()
  %bwipe!
endfunction
