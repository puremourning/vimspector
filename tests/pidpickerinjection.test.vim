function! SetUp()
  call vimspector#test#setup#SetUpWithMappings( v:null )
endfunction

function! TearDown()
  call vimspector#test#setup#TearDown()
endfunction

function! Test_PID_Picker_NotCalled_NoArguments_BuiltInPidSelect()
  " Mock AskForInput and do same as below to prove the case where it's not set
endfunction

function! Test_PID_Picker_Called_NoArguments_BuiltInPidSelect_RetInt()
  let fn='test_c.cpp'
  lcd ../support/test/cpp/simple_c_program
  exe 'edit ' . fn

  function! PickProcess() abort
    let s:process_picker_called = v:true
    return 12345 " doesn't matter
  endfunction
  let g:vimspector_custom_process_picker_func = 'PickProcess'

  let s:process_picker_called = v:false
  call vimspector#LaunchWithSettings( { 'configuration': 'cpptools-attach' } )
  call assert_true( s:process_picker_called )
  call vimspector#test#setup#Reset()

  lcd -
  %bwipeout!
endfunction

function! Test_PID_Picker_Called_NoArguments_BuiltInPidSelect_RetStr()
  let fn='test_c.cpp'
  lcd ../support/test/cpp/simple_c_program
  exe 'edit ' . fn

  function! PickProcess() abort
    let s:process_picker_called = v:true
    return '12345' " doesn't matter
  endfunction
  let g:vimspector_custom_process_picker_func = 'PickProcess'

  let s:process_picker_called = v:false
  call vimspector#LaunchWithSettings( { 'configuration': 'cpptools-attach' } )
  call assert_true( s:process_picker_called )
  call vimspector#test#setup#Reset()

  lcd -
  %bwipeout!
endfunction

function! Test_PID_Picker_Called_NoArguments_FromCalculus()
endfunction

function! Test_PID_Picker_Called_WithArguments_FromCalculus()
endfunction
