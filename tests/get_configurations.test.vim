function! SetUp()
  call vimspector#test#setup#SetUpWithMappings( v:none )
endfunction

function! ClearDown()
  call vimspector#test#setup#ClearDown()
endfunction

function Test_Get_Configurations()
  lcd ../support/test/csharp/

  let configs = vimspector#GetConfigurations()
  call assert_equal([
              \ 'launch - netcoredbg',
              \ 'launch - mono',
              \ ], configs)

  lcd -
  %bwipe!
endfunction

