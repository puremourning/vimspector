function! SetUp()
  call vimspector#test#setup#SetUpWithMappings( v:null )
  py3 import vim
  py3 __import__( 'vimspector' )
endfunction

function! TearDown()
  call vimspector#test#setup#TearDown()
endfunction

function! s:RunPyFile( file_name )
  redir => py_output
  try
    let v:errmsg = ''
    silent! execute 'py3file python/' .. a:file_name
  finally
    redir END
    call TestLog( [ a:file_name .. ' output:' ] + split( py_output, '\n' ) )
  endtry

  if v:errmsg !=# ''
    call assert_report( v:errmsg )
  endif
endfunction

function! Test_ExpandReferencesInDict()
  call SkipNeovim()
  call s:RunPyFile( 'Test_ExpandReferencesInDict.py' )
endfunction

function! Test_CoreUtils()
  call SkipNeovim()
  call s:RunPyFile( 'Test_CoreUtils.py' )
endfunction
