scriptencoding utf-8
let s:fn='../support/test/python/simple_python/main.py'

function! SetUp()
  let g:vimspector_ui_mode = get( s:, 'vimspector_ui_mode', 'horizontal' )
  call vimspector#test#setup#SetUpWithMappings( 'HUMAN' )
endfunction

function! TearDown()
  call vimspector#test#setup#TearDown()
endfunction

function! s:StartDebugging()
  exe 'edit ' . s:fn
  call setpos( '.', [ 0, 23, 1 ] )
  call vimspector#ToggleBreakpoint()
  call vimspector#LaunchWithSettings( { 'configuration': 'run' } )
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, 23, 1 )
endfunction

function! SetUp_Test_StandardLayout()
  call vimspector#test#setup#PushOption( 'columns', 200 )
endfunction

function! Test_StandardLayout()
  call s:StartDebugging()

  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, 25, 1 )

  call assert_equal( 'horizontal', g:vimspector_session_windows.mode )
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

function! TearDown_Test_StandardLayout()
  call vimspector#test#setup#PopOption( 'columns' )
endfunction

function! SetUp_Test_NarrowLayout()
  call vimspector#test#setup#PushOption( 'columns', 100 )
  let s:vimspector_ui_mode = 'vertical'
endfunction

function! Test_NarrowLayout()
  call SkipNeovim()
  call s:StartDebugging()

  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, 25, 1 )

  call assert_equal( 'vertical', g:vimspector_session_windows.mode )
  call assert_equal(
        \ [ 'col', [
        \   [ 'row', [
        \     [ 'leaf', g:vimspector_session_windows.variables ],
        \     [ 'leaf', g:vimspector_session_windows.watches ],
        \     [ 'leaf', g:vimspector_session_windows.stack_trace ],
        \   ] ],
        \   [ 'leaf', g:vimspector_session_windows.code ],
        \   [ 'leaf', g:vimspector_session_windows.terminal ],
        \   [ 'leaf', g:vimspector_session_windows.output ],
        \ ] ],
        \ winlayout( g:vimspector_session_windows.tabpage ) )

  call vimspector#test#setup#Reset()
  %bwipe!
endfunction

function! TearDown_Test_NarrowLayout()
  unlet s:vimspector_ui_mode
  call vimspector#test#setup#PopOption( 'columns' )
endfunction

function! SetUp_Test_AutoLayoutTerminalVert()
  let s:vimspector_ui_mode = 'auto'
  call vimspector#test#setup#PushOption( 'columns', 250 )
  call vimspector#test#setup#PushOption( 'lines', 30 )
endfunction

function! Test_AutoLayoutTerminalVert()
  call s:StartDebugging()

  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, 25, 1 )

  call assert_equal( 'horizontal', g:vimspector_session_windows.mode )
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

function! TearDown_Test_AutoLayoutTerminalVert()
  unlet s:vimspector_ui_mode
  call vimspector#test#setup#PopOption( 'lines' )
  call vimspector#test#setup#PopOption( 'columns' )
endfunction

function! SetUp_Test_AutoLayoutTerminalHorizVert()
  let s:vimspector_ui_mode = 'auto'
  " Wide enough to be horizontal layout, but not wide enough to fully fit the
  " terminal, with enough rows to fit the max terminal below
  call vimspector#test#setup#PushOption( 'columns',
        \ 50 + 82 + 3 + 2 + 12 )
  call vimspector#test#setup#PushOption( 'lines', 50 )
endfunction

function! Test_AutoLayoutTerminalHorizVert()
  call s:StartDebugging()

  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, 25, 1 )

  call assert_equal( 'horizontal', g:vimspector_session_windows.mode )
  call assert_equal(
        \ [ 'row', [
        \   [ 'col', [
        \     [ 'leaf', g:vimspector_session_windows.variables ],
        \     [ 'leaf', g:vimspector_session_windows.watches ],
        \     [ 'leaf', g:vimspector_session_windows.stack_trace ],
        \   ] ],
        \   [ 'col', [
        \     [ 'leaf', g:vimspector_session_windows.code ],
        \     [ 'leaf', g:vimspector_session_windows.terminal ],
        \     [ 'leaf', g:vimspector_session_windows.output ],
        \   ] ]
        \ ] ],
        \ winlayout( g:vimspector_session_windows.tabpage ) )

  call vimspector#test#setup#Reset()
  %bwipe!
endfunction

function! TearDown_Test_AutoLayoutTerminalHorizVert()
  unlet s:vimspector_ui_mode
  call vimspector#test#setup#PopOption( 'lines' )
  call vimspector#test#setup#PopOption( 'columns' )
endfunction

function! SetUp_Test_AutoLayoutTerminalHorizVertButNotEnoughLines()
  let s:vimspector_ui_mode = 'auto'
  " Wide enough to be horizontal layout, but not wide enough to fully fit the
  " terminal, with enough rows to fit the max terminal below, but there are not
  " enough lines to do this
  call vimspector#test#setup#PushOption( 'columns',
        \ 50 + 82 + 3 + 2 + 12 )
  call vimspector#test#setup#PushOption( 'lines', 20 )
endfunction

function! Test_AutoLayoutTerminalHorizVertButNotEnoughLines()
  call s:StartDebugging()

  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, 25, 1 )

  call assert_equal( 'horizontal', g:vimspector_session_windows.mode )
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
        \   ] ],
        \ ] ],
        \ winlayout( g:vimspector_session_windows.tabpage ) )

  call vimspector#test#setup#Reset()
  %bwipe!
endfunction

function! TearDown_Test_AutoLayoutTerminalHorizVertButNotEnoughLines()
  unlet s:vimspector_ui_mode
  call vimspector#test#setup#PopOption( 'lines' )
  call vimspector#test#setup#PopOption( 'columns' )
endfunction

function! SetUp_Test_AutoLayoutTerminalHoriz()
  let s:vimspector_ui_mode = 'vertical'
  " Vertical layout, but we split the terminal horizonally
  call vimspector#test#setup#PushOption( 'columns', 200 )
  call vimspector#test#setup#PushOption( 'lines', 50 )
endfunction

function! Test_AutoLayoutTerminalHoriz()
  call s:StartDebugging()

  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, 25, 1 )

  call assert_equal( 'vertical', g:vimspector_session_windows.mode )
  call assert_equal(
        \ [ 'col', [
        \   [ 'row', [
        \     [ 'leaf', g:vimspector_session_windows.variables ],
        \     [ 'leaf', g:vimspector_session_windows.watches ],
        \     [ 'leaf', g:vimspector_session_windows.stack_trace ],
        \   ] ],
        \   [ 'row', [
        \     [ 'leaf', g:vimspector_session_windows.code ],
        \     [ 'leaf', g:vimspector_session_windows.terminal ],
        \   ] ],
        \   [ 'leaf', g:vimspector_session_windows.output ],
        \ ] ],
        \ winlayout( g:vimspector_session_windows.tabpage ) )

  call vimspector#test#setup#Reset()
  %bwipe!
endfunction

function! TearDown_Test_AutoLayoutTerminalHoriz()
  unlet s:vimspector_ui_mode
  call vimspector#test#setup#PopOption( 'lines' )
  call vimspector#test#setup#PopOption( 'columns' )
endfunction

function! SetUp_Test_AutoLayoutTerminalVertVert()
  let s:vimspector_ui_mode = 'auto'
  " Not wide enough to go horizontal, but wide enough to put the terminal and
  " code vertically split
  call vimspector#test#setup#PushOption( 'columns', 80 )
  call vimspector#test#setup#PushOption( 'lines', 50 )
endfunction

function! Test_AutoLayoutTerminalVertVert()
  call s:StartDebugging()

  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, 25, 1 )

  call assert_equal( 'vertical', g:vimspector_session_windows.mode )
  call assert_equal(
        \ [ 'col', [
        \   [ 'row', [
        \     [ 'leaf', g:vimspector_session_windows.variables ],
        \     [ 'leaf', g:vimspector_session_windows.watches ],
        \     [ 'leaf', g:vimspector_session_windows.stack_trace ],
        \   ] ],
        \   [ 'leaf', g:vimspector_session_windows.code ],
        \   [ 'leaf', g:vimspector_session_windows.terminal ],
        \   [ 'leaf', g:vimspector_session_windows.output ],
        \ ] ],
        \ winlayout( g:vimspector_session_windows.tabpage ) )

  call vimspector#test#setup#Reset()
  %bwipe!
endfunction

function! TearDown_Test_AutoLayoutTerminalVertVert()
  unlet s:vimspector_ui_mode
  call vimspector#test#setup#PopOption( 'lines' )
  call vimspector#test#setup#PopOption( 'columns' )
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
  call SkipNeovim()
  augroup TestCustomWinBar
    au!
    au User VimspectorUICreated call s:CustomWinBar()
  augroup END

  call s:StartDebugging()
  call assert_equal(
        \ ['▷ ᶠ⁵', '↷ ᶠ¹⁰', '↓ ᶠ¹¹', '↑ ˢᶠ¹¹', '❘❘ ᶠ⁶', '□ ˢᶠ⁵', '⟲ ᶜˢᶠ⁵', '✕ ᶠ⁸'],
        \ menu_info( 'WinBar' ).submenus )

  au! TestCustomWinBar
  call vimspector#test#setup#Reset()
  %bwipe!
endfunction

function! Test_NoMouseNoWinBar()
  call SkipNeovim()
  call vimspector#test#setup#PushOption( 'mouse', '' )
  call s:StartDebugging()
  call assert_equal( {}, menu_info( 'WinBar' ) )

  call vimspector#test#setup#Reset()
  %bwipe!
endfunction

function! TearDown_Test_NoMouseNoWinBar()
  call vimspector#test#setup#PopOption( 'mouse' )
endfunction

function! Test_VimspectorJumpedToFrame()
  let s:ended = 0
  let s:au_visited_buffers = {}

  augroup TestVimspectorJumpedToFrame
    au!
    au User VimspectorJumpedToFrame
          \ let s:au_visited_buffers[ bufname() ] = get( s:au_visited_buffers,
          \                                              bufname(),
          \                                              0 ) + 1
    au User VimspectorDebugEnded
          \ let s:ended = 1
  augroup END

  lcd ../support/test/python/multiple_files
  edit moo.py

  let moo = 'moo.py'
  let cow = getcwd() . '/cow.py'

  call vimspector#SetLineBreakpoint( 'moo.py', 13 )
  call vimspector#Launch()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'moo.py', 1, 1 )
  call vimspector#test#signs#AssertPCIsAtLineInBuffer( 'moo.py', 1 )
  let expected = {}
  let expected[ moo ] = 1
  call assert_equal( expected, s:au_visited_buffers )

  call vimspector#Continue()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'moo.py', 13, 1 )
  call vimspector#test#signs#AssertPCIsAtLineInBuffer( 'moo.py', 13 )
  let expected[ moo ] += 1
  call assert_equal( expected, s:au_visited_buffers )

  call vimspector#SetLineBreakpoint( 'cow.py', 2 )
  call vimspector#Continue()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'cow.py', 2, 1 )
  call vimspector#test#signs#AssertPCIsAtLineInBuffer( 'cow.py', 2 )
  let expected[ cow ] = 1
  call assert_equal( expected, s:au_visited_buffers )

  VimspectorReset
  call WaitForAssert( { -> assert_equal( s:ended, 1 ) } )

  au! TestVimspectorJumpedToFrame
  unlet! s:au_visited_buffers
  unlet! s:ended

  call vimspector#test#setup#Reset()
  lcd -
  %bwipe!
endfunction

function! Test_DebugInfo_NotConnected()
  redir => debug_message
  VimspectorDebugInfo
  redir END

  call assert_equal( 'Vimspector not connected, start a debug session first',
        \ trim( debug_message ) )

  call vimspector#test#setup#Reset()
  %bwipe!
endfunction

function! Test_DebugInfo_Connected()
  call s:StartDebugging()

  " Just make sure there are no errors for now
  VimspectorDebugInfo
  call vimspector#test#setup#Reset()
  %bwipe!
endfunction
