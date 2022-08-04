" This test does nothing except check the test framework itself
function! SetUp() abort
  call vimspector#test#setup#SetUpWithMappings( v:null )
endfunction

function! Test_Can_Run_In_NeoVim()
  call assert_true( 1 )
endfunction

