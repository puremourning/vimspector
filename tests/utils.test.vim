function! SetUp()
  call vimspector#test#setup#SetUpWithMappings( v:none )
  py3 import vim
  py3 __import__( 'vimspector' )
endfunction

function! ClearDown()
  call vimspector#test#setup#ClearDown()
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
  call s:RunPyFile( 'Test_ExpandReferencesInDict.py' )
endfunction
