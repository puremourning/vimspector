function! SetUp()
  call vimspector#test#setup#SetUpWithMappings( v:null )
endfunction

function! TearDown()
  call vimspector#test#setup#TearDown()
endfunction

function! Test_PID_Picker()
  let fn='test_c.cpp'
  lcd ../support/test/cpp/simple_c_program
  exe 'edit ' . fn

  function! PickProcess() abort
    let s:process_picker_called = v:true
    return 12345 " doesn't matter
  endfunction
  let g:vimspector_custom_process_picker_expr = 'PickProcess()'

  let s:process_picker_called = v:false
  call vimspector#LaunchWithSettings( { 'configuration': 'cpptools-attach' } )
  call assert_true(s:process_picker_called)
  call vimspector#test#setup#Reset()

  lcd -
  %bwipeout!
endfunction
