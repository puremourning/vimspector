function! SetUp()
  call vimspector#test#setup#SetUpWithMappings( v:null )
endfunction

function! TearDown()
  call vimspector#test#setup#TearDown()
endfunction

function Test_Get_Configurations()
  lcd ../support/test/csharp/

  let configs = vimspector#GetConfigurations()
  call assert_equal( [
                   \   'launch - netcoredbg',
                   \   'launch - netcoredbg - with debug log',
                   \   'launch - mono',
                   \ ],
                   \ configs )

  lcd -
  %bwipe!
endfunction

function! Test_Get_Configurations_FilteredFiletypes()
  edit ../support/test/multiple_filetypes/test.js
  call assert_equal( [ 'Node' ], vimspector#GetConfigurations() )
  edit ../support/test/multiple_filetypes/test.py
  call assert_equal( [ 'Python' ], vimspector#GetConfigurations() )
  edit ../support/test/multiple_filetypes/.vimspector.json
  call assert_equal( [], vimspector#GetConfigurations() )
  %bwipe!
endfunction

function! Test_PickConfiguration_FilteredFiletypes()
  call ThisTestIsFlaky()
  let fn = '../support/test/multiple_filetypes/test.js'
  exe 'edit ' . fn
  normal! G
  call vimspector#SetLineBreakpoint( fn, 1 )
  call vimspector#Launch()
  call WaitForAssert( { ->
        \ vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 1, 1  )
        \ } )
  call vimspector#test#setup#Reset()

  let fn = '../support/test/multiple_filetypes/test.py'
  exe 'edit ' . fn
  normal! G
  call vimspector#SetLineBreakpoint( fn, 1 )
  call vimspector#Launch()
  call WaitForAssert( { ->
        \ vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 1, 1  )
        \ } )

  call vimspector#test#setup#Reset()
  %bwipe!
endfunction

function Test_Get_Configurations_VimDict()
  call SkipNeovim()
  call vimspector#test#setup#PushSetting( 'vimspector_configurations', #{
        \ test_config: #{
        \    extends: 'launch - netcoredbg'
        \   }
        \ } )
  lcd ../support/test/csharp/

  let configs = vimspector#GetConfigurations()
  call assert_equal( [
        \   'test_config',
        \   'launch - netcoredbg',
        \   'launch - netcoredbg - with debug log',
        \   'launch - mono',
        \ ],
        \ configs )

  lcd -
  %bwipe!
endfunction

