" This script is sourced while editing the .vim file with the tests.
" When the script is successful the .res file will be created.
" Errors are appended to the test.log file.
"
" To execute only specific test functions, add a second argument.  It will be
" matched against the names of the Test_ function.  E.g.:
"	../vim -Nu NONE vimrc -S lib/run_test.vim test_channel.vim open_delay
" The output can be found in the "messages" file.
"
" The test script may contain anything, only functions that start with
" "Test_" are special.  These will be invoked and should contain assert
" functions.  See test_assert.vim for an example.
"
" It is possible to source other files that contain "Test_" functions.  This
" can speed up testing, since Vim does not need to restart.  But be careful
" that the tests do not interfere with each other.
"
" If an error cannot be detected properly with an assert function add the
" error to the v:errors list:
"   call add(v:errors, 'test foo failed: Cannot find xyz')
"
" If preparation for each Test_ function is needed, define a SetUp function.
" It will be called before each Test_ function.
"
" If cleanup after each Test_ function is needed, define a TearDown function.
" It will be called after each Test_ function.
"
" When debugging a test it can be useful to add messages to v:errors:
"   call add(v:errors, "this happened")
"
" But for real debug logging:
"   call ch_log( ",,,message..." )
" Then view it in 'debuglog'

" This prevents inputsave()/inputrestore() when asking for input, which allows
" the tests to use feedkeys() to enter the info.
let g:vimspector_batch_mode = 1

" Let a test take up to 1 minute, unless debugging
let s:single_test_timeout = 60000

" Restrict the runtimepath to the exact minimum needed for testing
let &runtimepath = getcwd() . '/lib'
set runtimepath+=$VIM/vimfiles,$VIMRUNTIME,$VIM/vimfiles/after
if has('packages')
  let &packpath = &runtimepath
endif

if exists( '*ch_logfile' )
  call ch_logfile( 'debuglog', 'w' )
endif

" For consistency run all tests with 'nocompatible' set.
" This also enables use of line continuation.
" vint: Workaround for https://github.com/Vimjas/vint/issues/363
" vint: -ProhibitSetNoCompatible
set nocompatible
" vint: +ProhibitSetNoCompatible

" Use utf-8 by default, instead of whatever the system default happens to be.
" Individual tests can overrule this at the top of the file.
" vint: -ProhibitEncodingOptionAfterScriptEncoding
set encoding=utf-8
" vint: +ProhibitEncodingOptionAfterScriptEncoding

" Avoid stopping at the "hit enter" prompt
set nomore

" Output all messages in English.
lang messages C

" Always use forward slashes.
set shellslash

func s:TestFailed()
    let log = readfile( expand( '~/.vimspector.log' ) )
    let logfile = s:testid_filesafe . '_vimspector.log.testlog'
    call writefile( log, logfile, 's' )
    call add( s:messages, 'Wrote log for failed test: ' . logfile )
endfunc

func! Abort( timer_id )
  if exists( '&debugfunc' ) && &debugfunc !=# ''
    return
  endif

  call assert_report( 'Test timed out!!!' )
  qa!
endfunc

func! TestLog( msg )
  if type( a:msg ) == v:t_string
    let msg = [ a:msg ]
  else
    let msg = a:msg
  endif

  call extend( s:messages, msg )
endfunc

func RunTheTest(test)
  echo 'Executing ' . a:test

  " Avoid stopping at the "hit enter" prompt
  set nomore

  " Avoid a three second wait when a message is about to be overwritten by the
  " mode message.
  set noshowmode

  " Clear any overrides.
  if exists( '*test_override' )
    call test_override('ALL', 0)
  endif

  " Some tests wipe out buffers.  To be consistent, always wipe out all
  " buffers.
  %bwipe!

  " The test may change the current directory. Save and restore the
  " directory after executing the test.
  let s:save_cwd = getcwd()

  if exists('*SetUp_' . a:test)
    try
      exe 'call SetUp_' . a:test
    catch
      call add(v:errors,
            \ 'Caught exception in SetUp_' . a:test . ' before '
            \ . a:test
            \ . ': '
            \ . v:exception
            \ . ' @ '
            \ . g:testpath
            \ . ':'
            \ . v:throwpoint)
    endtry
  endif

  if exists('*SetUp')
    try
      call SetUp()
    catch
      call add(v:errors,
            \ 'Caught exception in SetUp() before '
            \ . a:test
            \ . ': '
            \ . v:exception
            \ . ' @ '
            \ . g:testpath
            \ . ':'
            \ . v:throwpoint)
    endtry
  endif

  call add(s:messages, 'Executing ' . a:test)
  let s:done += 1
  let timer = timer_start( s:single_test_timeout, funcref( 'Abort' ) )

  try
    let s:test = a:test
    let s:testid = g:testpath . ':' . a:test

    let test_filesafe = substitute( a:test, '[)(,:]', '_', 'g' )
    let s:testid_filesafe = g:testpath . '_' . test_filesafe

    augroup EarlyExit
      au!
      au VimLeavePre * call EarlyExit(s:test)
    augroup END

    exe 'call ' . a:test
  catch /^\cskipped/
    call add(s:messages, '    Skipped')
    call add(s:skipped,
          \ 'SKIPPED ' . a:test
          \ . ': '
          \ . substitute(v:exception, '^\S*\s\+', '',  ''))
  catch /^\cxfail/
    if len( v:errors ) == 0
      call add(v:errors,
            \ 'Expected failure but no error in ' . a:test
            \ . ': '
            \ . v:exception
            \ . ' @ '
            \ . g:testpath
            \ . ':'
            \ . v:throwpoint)

      call s:TestFailed()
    else
      let v:errors = []
      call add(s:messages, '    XFAIL' )
      call add(s:skipped,
            \ 'XFAIL ' . a:test
            \ . ': '
            \ . substitute(v:exception, '^\S*\s\+', '',  ''))
    endif
  catch
    call add(v:errors,
          \ 'Caught exception in ' . a:test
          \ . ': '
          \ . v:exception
          \ . ' @ '
          \ . g:testpath
          \ . ':'
          \ . v:throwpoint)

    call s:TestFailed()
  endtry

  au! EarlyExit

  call timer_stop( timer )

  " In case 'insertmode' was set and something went wrong, make sure it is
  " reset to avoid trouble with anything else.
  set noinsertmode

  if exists('*TearDown')
    try
      call TearDown()
    catch
      call add(v:errors,
            \ 'Caught exception in TearDown() after ' . a:test
            \ . ': '
            \ . v:exception
            \ . ' @ '
            \ . g:testpath
            \ . ':'
            \ . v:throwpoint)
    endtry
  endif

  if exists('*TearDown_' . a:test)
    try
      exe 'call TearDown_' . a:test
    catch
      call add(v:errors,
            \ 'Caught exception in TearDown_' . a:test . ' after ' . a:test
            \ . ': '
            \ . v:exception
            \ . ' @ '
            \ . g:testpath
            \ . ':'
            \ . v:throwpoint)
    endtry
  endif

  " Clear any autocommands
  au!

  " Close any extra tab pages and windows and make the current one not modified.
  while tabpagenr('$') > 1
    quit!
  endwhile

  while 1
    let wincount = winnr('$')
    if wincount == 1
      break
    endif
    bwipe!
    if wincount == winnr('$')
      " Did not manage to close a window.
      only!
      break
    endif
  endwhile

  exe 'cd ' . s:save_cwd
endfunc

func AfterTheTest()
  if len(v:errors) > 0
    let s:fail += 1
    call s:TestFailed()
    call add(s:errors, 'Found errors in ' . s:testid . ':')
    call extend(s:errors, v:errors)
    let v:errors = []
  endif
endfunc

func EarlyExit(test)
  " It's OK for the test we use to test the quit detection.
  call add(v:errors, 'Test caused Vim to exit: ' . a:test)
  call FinishTesting()
endfunc

" This function can be called by a test if it wants to abort testing.
func FinishTesting()
  exe 'cd ' . s:save_cwd
  call AfterTheTest()

  " Don't write viminfo on exit.
  set viminfo=

  if s:fail == 0
    " Success, create the .res file so that make knows it's done.
    call writefile( [], g:testname . '.res', 's' )
  endif

  if len(s:errors) > 0
    " Append errors to test.log
    let l = []
    if filereadable( 'test.log' )
      let l = readfile( 'test.log' )
    endif
    call extend( l, [ '', 'From ' . g:testpath . ':' ] )
    call extend( l, s:errors )
    call writefile( l, 'test.log', 's' )
  endif

  if s:done == 0
    let message = 'NO tests executed'
  else
    let message = 'Executed ' . s:done . (s:done > 1 ? ' tests' : ' test')
  endif
  echo message
  call add(s:messages, message)
  if s:fail > 0
    let message = s:fail . ' FAILED:'
    echo message
    call add(s:messages, message)
    call extend(s:messages, s:errors)
  endif

  " Add SKIPPED messages
  call extend(s:messages, s:skipped)

  " Append messages to the file "messages"
  let l = []
  if filereadable( 'messages' )
    let l = readfile( 'messages' )
  endif
  call extend( l, [ '', 'From ' . g:testpath . ':' ] )
  call extend( l, s:messages )
  call writefile( l, 'messages', 's' )

  if s:fail > 0
    cquit!
  else
    qall!
  endif
endfunc

" Source the test script.  First grab the file name, in case the script
" navigates away.  g:testname can be used by the tests.
let g:testname = expand('%')
let g:testpath = expand('%:p')
let s:done = 0
let s:fail = 0
let s:errors = []
let s:messages = []
let s:skipped = []
try
  source %
catch
  let s:fail += 1
  call add(s:errors,
        \ 'Caught exception: ' .
        \ v:exception .
        \ ' @ ' . v:throwpoint)
endtry

" Locate Test_ functions and execute them.
redir @q
silent function /^Test_
redir END
let s:tests = split(substitute(@q, 'function \(\k*()\)', '\1', 'g'))

" If there is an extra argument filter the function names against it.
if argc() > 1
  let s:tests = filter(s:tests, 'v:val =~ argv(1)')
endif

" Execute the tests in alphabetical order.
for s:test in sort(s:tests)
  " Silence, please!
  set belloff=all

  call RunTheTest(s:test)

  " Repeat a flaky test.  Give up when:
  " - $TEST_NO_RETRY is not empty
  " - $TEST_NO_RETRY is not 0
  " - it fails five times
  if len(v:errors) > 0
        \ && ( $TEST_NO_RETRY == '' || $TEST_NO_RETRY == '0' )
    for retry in range( 10 )
      call add( s:messages, 'Found errors in ' . s:test . '. Retrying.' )
      call extend( s:messages, v:errors )

      sleep 2

      let v:errors = []
      call RunTheTest(s:test)

      if len(v:errors) == 0
        " Test passed on rerun.
        break
      endif
    endfor
  endif

  call AfterTheTest()
endfor

call FinishTesting()

" vim: shiftwidth=2 sts=2 expandtab
