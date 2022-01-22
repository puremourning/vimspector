function! SetUp()
  call vimspector#test#setup#SetUpWithMappings( v:none )
endfunction

function! ClearDown()
  call vimspector#test#setup#ClearDown()
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

function Test_Get_Nested_Configurations()
  lcd ../support/test/go/hello_world/

  let configs = vimspector#GetConfigurations()
  call assert_equal( [
                   \   'run-legacy',
                   \   'run-delve',
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
  let fn = '../support/test/multiple_filetypes/test.js'
  exe 'edit ' . fn
  normal! G
  call vimspector#Launch()
  call WaitForAssert( { ->
        \ vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 1, 1  )
        \ } )
  call vimspector#test#setup#Reset()

  let fn = '../support/test/multiple_filetypes/test.py'
  exe 'edit ' . fn
  normal! G
  call vimspector#Launch()
  call WaitForAssert( { ->
        \ vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 1, 1  )
        \ } )

  call vimspector#test#setup#Reset()
  %bwipe!
endfunction
