let s:init = 0

function! SetUp()
  call vimspector#test#setup#SetUpWithMappings( v:null )

  if ! s:init
    let s:break_main_line = FunctionBreakOnBrace() ? 14 : 15
    let s:break_foo_line = FunctionBreakOnBrace() ? 6 : 9
    let s:init = 1
  endif
endfunction

function! TearDown()
  call vimspector#test#setup#TearDown()
endfunction

function! SetUp_Test_Mappings_Are_Added_HUMAN()
  let g:vimspector_enable_mappings = 'HUMAN'
endfunction

function! Test_Mappings_Are_Added_HUMAN()
  call assert_true( hasmapto( 'vimspector#Continue()' ) )
  call assert_false( hasmapto( 'vimspector#Launch()' ) )
  call assert_true( hasmapto( 'vimspector#Stop()' ) )
  call assert_true( hasmapto( 'vimspector#Restart()' ) )
  call assert_true( hasmapto( 'vimspector#ToggleBreakpoint()' ) )
  call assert_true( hasmapto( 'vimspector#AddFunctionBreakpoint' ) )
  call assert_true( hasmapto( 'vimspector#StepOver()' ) )
  call assert_true( hasmapto( 'vimspector#StepInto()' ) )
  call assert_true( hasmapto( 'vimspector#StepOut()' ) )
  call assert_true( hasmapto( 'vimspector#RunToCursor()' ) )
endfunction

function! SetUp_Test_Mappings_Are_Added_VISUAL_STUDIO()
  let g:vimspector_enable_mappings = 'VISUAL_STUDIO'
endfunction

function! Test_Mappings_Are_Added_VISUAL_STUDIO()
  call assert_true( hasmapto( 'vimspector#Continue()' ) )
  call assert_false( hasmapto( 'vimspector#Launch()' ) )
  call assert_true( hasmapto( 'vimspector#Stop()' ) )
  call assert_true( hasmapto( 'vimspector#Restart()' ) )
  call assert_true( hasmapto( 'vimspector#ToggleBreakpoint()' ) )
  call assert_true( hasmapto( 'vimspector#AddFunctionBreakpoint' ) )
  call assert_true( hasmapto( 'vimspector#StepOver()' ) )
  call assert_true( hasmapto( 'vimspector#StepInto()' ) )
  call assert_true( hasmapto( 'vimspector#StepOut()' ) )
endfunction

function! SetUp_Test_Use_Mappings_HUMAN()
  let g:vimspector_enable_mappings = 'HUMAN'
endfunction

function! Test_Use_Mappings_HUMAN()
  call SkipNeovim()
  call ThisTestIsFlaky()
  lcd testdata/cpp/simple
  edit simple.cpp
  call setpos( '.', [ 0, 16, 1 ] )

  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'simple.cpp', 16, 1 )
  call vimspector#test#signs#AssertSignGroupEmptyAtLine( 'VimspectorBP', 16 )

  " Add the breakpoint
  call feedkeys( "\<F9>", 'xt' )
  call vimspector#test#signs#AssertSignGroupSingletonAtLine( 'VimspectorBP',
                                                           \ 16,
                                                           \ 'vimspectorBP',
                                                           \ 9 )

  " Delete the breakpoint
  call feedkeys( "\<F9>", 'xt' )
  call vimspector#test#signs#AssertSignGroupEmptyAtLine( 'VimspectorBP', 16 )

  " Add and clear using API
  call vimspector#SetLineBreakpoint( 'simple.cpp', 16 )
  call vimspector#test#signs#AssertSignGroupSingletonAtLine( 'VimspectorBP',
                                                           \ 16,
                                                           \ 'vimspectorBP',
                                                           \ 9 )

  call vimspector#ClearLineBreakpoint( 'simple.cpp', 16 )
  call vimspector#test#signs#AssertSignGroupEmptyAtLine( 'VimspectorBP', 16 )

  " Add it again
  call feedkeys( "\<F9>", 'xt' )
  call vimspector#test#signs#AssertSignGroupSingletonAtLine(
        \ 'VimspectorBP',
        \ 16,
        \ 'vimspectorBP',
        \ 9 )

  " Here we go. Start Debugging
  call feedkeys( "\<F5>", 'xt' )

  call assert_equal( 2, len( gettabinfo() ) )
  let cur_tabnr = tabpagenr()
  call assert_equal( 5, len( gettabinfo( cur_tabnr )[ 0 ].windows ) )

  " break on main
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'simple.cpp', s:break_main_line, 1 )

  " Cont
  " Here we go. Start Debugging
  call feedkeys( "\<F5>", 'xt' )

  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'simple.cpp', 16, 1 )

  " Run to cursor (note , is the mapleader)
  call cursor( 9, 1 )
  call feedkeys( ",\<F8>", 'xt' )
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'simple.cpp', 9, 1 )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer( 'simple.cpp', 9 )
        \ } )

  " Step
  call feedkeys( "\<F10>", 'xt' )

  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'simple.cpp', 10, 1 )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer( 'simple.cpp', 10 )
        \ } )

  " Stop
  call feedkeys( "\<F3>", 'xt' )
  call WaitForAssert( {->
        \ assert_equal( [],
        \               getbufline( g:vimspector_session_windows.variables,
        \                           1,
        \                           '$' ) )
        \ } )
  call WaitForAssert( {->
        \ assert_equal( [],
        \               getbufline( g:vimspector_session_windows.stack_trace,
        \                           1,
        \                           '$' ) )
        \ } )
  call WaitForAssert( {->
        \ assert_equal( [],
        \               getbufline( g:vimspector_session_windows.watches,
        \                           1,
        \                           '$' ) )
        \ } )

  call vimspector#test#setup#Reset()

  lcd -
  %bwipeout!
endfunction

function! SetUp_Test_Use_Mappings_HUMAN_Disable()
  let g:vimspector_enable_mappings = 'HUMAN'
  call vimspector#test#setup#PushSetting(
        \ 'vimspector_toggle_disables_breakpoint', 1 )
endfunction

function! Test_Use_Mappings_HUMAN_Disable()
  call SkipNeovim()
  call ThisTestIsFlaky()
  lcd testdata/cpp/simple
  edit simple.cpp
  call setpos( '.', [ 0, 16, 1 ] )

  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'simple.cpp', 16, 1 )
  call vimspector#test#signs#AssertSignGroupEmptyAtLine( 'VimspectorBP', 16 )

  " Add the breakpoint
  call feedkeys( "\<F9>", 'xt' )
  call vimspector#test#signs#AssertSignGroupSingletonAtLine( 'VimspectorBP',
                                                           \ 16,
                                                           \ 'vimspectorBP',
                                                           \ 9 )

  " Disable the breakpoint
  call feedkeys( "\<F9>", 'xt' )
  call vimspector#test#signs#AssertSignGroupSingletonAtLine(
        \ 'VimspectorBP',
        \ 16,
        \ 'vimspectorBPDisabled',
        \ 9 )

  " Delete the breakpoint
  call feedkeys( "\<F9>", 'xt' )
  call vimspector#test#signs#AssertSignGroupEmptyAtLine( 'VimspectorBP', 16 )

  " Add and clear using API
  call vimspector#SetLineBreakpoint( 'simple.cpp', 16 )
  call vimspector#test#signs#AssertSignGroupSingletonAtLine( 'VimspectorBP',
                                                           \ 16,
                                                           \ 'vimspectorBP',
                                                           \ 9 )

  call vimspector#ClearLineBreakpoint( 'simple.cpp', 16 )
  call vimspector#test#signs#AssertSignGroupEmptyAtLine( 'VimspectorBP', 16 )

  " Add it again
  call feedkeys( "\<F9>", 'xt' )
  call vimspector#test#signs#AssertSignGroupSingletonAtLine(
        \ 'VimspectorBP',
        \ 16,
        \ 'vimspectorBP',
        \ 9 )

  " Here we go. Start Debugging
  call feedkeys( "\<F5>", 'xt' )

  call assert_equal( 2, len( gettabinfo() ) )
  let cur_tabnr = tabpagenr()
  call assert_equal( 5, len( gettabinfo( cur_tabnr )[ 0 ].windows ) )

  " break on main
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'simple.cpp', s:break_main_line, 1 )

  " Cont
  " Here we go. Start Debugging
  call feedkeys( "\<F5>", 'xt' )

  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'simple.cpp', 16, 1 )

  " Run to cursor (note , is the mapleader)
  call cursor( 9, 1 )
  call feedkeys( ",\<F8>", 'xt' )
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'simple.cpp', 9, 1 )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer( 'simple.cpp', 9 )
        \ } )

  " Step
  call feedkeys( "\<F10>", 'xt' )

  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( 'simple.cpp', 10, 1 )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer( 'simple.cpp', 10 )
        \ } )

  " Stop
  call feedkeys( "\<F3>", 'xt' )
  call WaitForAssert( {->
        \ assert_equal( [],
        \               getbufline( g:vimspector_session_windows.variables,
        \                           1,
        \                           '$' ) )
        \ } )
  call WaitForAssert( {->
        \ assert_equal( [],
        \               getbufline( g:vimspector_session_windows.stack_trace,
        \                           1,
        \                           '$' ) )
        \ } )
  call WaitForAssert( {->
        \ assert_equal( [],
        \               getbufline( g:vimspector_session_windows.watches,
        \                           1,
        \                           '$' ) )
        \ } )

  call vimspector#test#setup#Reset()

  lcd -
  %bwipeout!
endfunction

let s:fn='../support/test/python/simple_python/main.py'
function! s:StartDebugging( ... )
  if a:0 == 0
    let config = #{
          \   fn: s:fn,
          \   line: 23,
          \   col: 1,
          \   launch: #{ configuration: 'run' }
          \ }
  else
    let config = a:1
  endif

  execute 'edit' config.fn
  call setpos( '.', [ 0, config.line, config.col ] )
  call vimspector#ToggleBreakpoint()
  call vimspector#LaunchWithSettings( config.launch )
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer(
        \ config.fn,
        \ config.line,
        \ config.col )
endfunction

function! SetUp_Test_Partial_Mappings_Dict_Override()
call vimspector#test#setup#PushSetting( 'vimspector_mappings', #{
      \    stack_trace: {},
      \    variables: #{
        \    set_value: [ '<Tab>', '<C-CR>' ]
        \  }
      \ }
      \ )
call vimspector#test#setup#PushSetting( 'vimspector_variables_display_mode',
                                      \ 'full' )
endfunction

function! Test_Partial_Mappings_Dict_Override()
  let fn =  'testdata/cpp/simple/struct.cpp'
  call s:StartDebugging( #{ fn: fn, line: 24, col: 1, launch: #{
        \   configuration: 'run-to-breakpoint'
        \ } } )

  " Make sure the Test t is initialised
  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 26, 1 )

  call WaitForAssert( {->
        \   assert_equal(
        \     [
        \       '- Scope: Locals',
        \       ' *+ t (Test): {...}',
        \       '+ Scope: Registers',
        \     ],
        \     getbufline( winbufnr( g:vimspector_session_windows.variables ),
        \                 1,
        \                 '$' )
        \   )
        \ } )
  call assert_equal( 'cpp',
                   \ getbufvar(
                   \   winbufnr( g:vimspector_session_windows.variables ),
                   \   '&syntax' ) )

  " Expand, a mapping which is _not_ overridden
  call win_gotoid( g:vimspector_session_windows.variables )
  call setpos( '.', [ 0, 2, 1 ] )
  call feedkeys( "\<CR>", 'xt' )

  call WaitForAssert( {->
        \   AssertMatchList(
        \     [
        \       '- Scope: Locals',
        \       ' \*- t (Test): {...}',
        \       '   \*- i (int): 0',
        \       '   \*- c (char): 0 ''\\0\{1,3}''',
        \       '   \*- fffff (float): 0',
        \       '   \*+ another_test (AnotherTest):\( {...}\)\?',
        \       '+ Scope: Registers',
        \     ],
        \     getbufline( winbufnr( g:vimspector_session_windows.variables ),
        \                 1,
        \                 '$' )
        \   )
        \ } )

  call setpos( '.', [ 0, 3, 1 ] )

  " Check that we can set the variable using the custom mapping
  "
  " We can't just fire the keys to the inpit prompt because we use inputsave()
  " and inputrestore(), so mock that out and fire away.
  py3 <<EOF
from unittest import mock
with mock.patch( 'vimspector.utils.InputSave' ):
  vim.eval( 'feedkeys( "\<Tab>\<C-u>100\<CR>", "xt" )' )
EOF

  call WaitForAssert( {->
        \   AssertMatchList(
        \     [
        \       '- Scope: Locals',
        \       ' \*- t (Test): {...}',
        \       '   \*- i (int): 100',
        \       '   \*- c (char): 0 ''\\0\{1,3}''',
        \       '   \*- fffff (float): 0',
        \       '   \*+ another_test (AnotherTest):\( {...}\)\?',
        \       '+ Scope: Registers',
        \     ],
        \     getbufline( winbufnr( g:vimspector_session_windows.variables ),
        \                 1,
        \                 '$' )
        \   )
        \ } )

  call vimspector#test#setup#Reset()
  %bwipe!
endfunction

