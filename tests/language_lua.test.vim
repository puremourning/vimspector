function! SetUp()
  let g:vimspector_enable_mappings = 'HUMAN'
  call vimspector#test#setup#SetUpWithMappings( v:none )
endfunction

function! ClearDown()
  call vimspector#test#setup#ClearDown()
endfunction


function! BaseTest( configuration )
  let fn='simple.lua'
  lcd ../support/test/lua/simple
  exe 'edit ' . fn

  call vimspector#SetLineBreakpoint( fn, 5 )
  call vimspector#LaunchWithSettings( { 'configuration': a:configuration } )

  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 5, 1 )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer( fn, 5 )
        \ } )

  " Step
  call feedkeys( "\<F10>", 'xt' )

  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 6, 1 )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer( fn, 6 )
        \ } )

  call vimspector#test#setup#Reset()

  lcd -
  %bwipeout!
endfunction


function! Test_Lua_Simple()
  call BaseTest( 'lua' )
endfunction


function! Test_Lua_Luajit()
  call BaseTest( 'luajit' )
endfunction


function! Test_Lua_Love()
  let fn='main.lua'
  lcd ../support/test/lua/love-headless
  exe 'edit ' . fn

  call vimspector#SetLineBreakpoint( fn, 8 )
  call vimspector#LaunchWithSettings( { 'configuration': 'love' } )

  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 8, 1 )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer( fn, 8 )
        \ } )

  " Step
  call feedkeys( "\<F10>", 'xt' )

  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 9, 1 )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer( fn, 9 )
        \ } )

  call vimspector#test#setup#Reset()

  lcd -
  %bwipeout!
endfunction
