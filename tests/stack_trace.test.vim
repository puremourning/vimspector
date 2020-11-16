let s:fn='testdata/cpp/simple/threads.cpp'

function! SetUp()
  call vimspector#test#setup#SetUpWithMappings( 'HUMAN' )
endfunction

function! ClearDown()
  call vimspector#test#setup#ClearDown()
endfunction

function! s:StartDebugging()
  exe 'edit ' . s:fn
  call vimspector#SetLineBreakpoint( s:fn, 13 )
  call vimspector#Launch()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, 13, 1 )
endfunction

function! Test_Multiple_Threads()
  call vimspector#SetLineBreakpoint( s:fn, 41 )
  call vimspector#SetLineBreakpoint( s:fn, 51 )
  call s:StartDebugging()

  call vimspector#Continue()

  " As we step through the thread creation we should get Thread events

  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, 41, 1 )
  call vimspector#Continue()

  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, 41, 1 )
  call vimspector#Continue()

  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, 41, 1 )
  call vimspector#Continue()

  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, 41, 1 )
  call vimspector#Continue()

  " This is the last one
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, 41, 1 )
  call vimspector#Continue()

  " So we break out of the loop
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( s:fn, 51, 1 )

  call vimspector#ClearBreakpoints()
  call vimspector#test#setup#Reset()
  %bwipe!
endfunction
