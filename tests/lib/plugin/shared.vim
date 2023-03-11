
" Functions shared by several tests.

" Only load this script once.
if exists('*WaitFor')
  finish
endif

" Wait for up to five seconds for "expr" to become true.  "expr" can be a
" stringified expression to evaluate, or a funcref without arguments.
" Using a lambda works best.  Example:
"	call WaitFor({-> status == "ok"})
"
" A second argument can be used to specify a different timeout in msec.
"
" When successful the time slept is returned.
" When running into the timeout an exception is thrown, thus the function does
" not return.
func WaitFor(expr, ...)
  let timeout = get(a:000, 0, 10000)
  let slept = s:WaitForCommon(a:expr, v:null, timeout)
  if slept < 0
    throw 'WaitFor() timed out after ' . timeout . ' msec'
  endif
  return slept
endfunc

" Wait for up to five seconds for "assert" to return without adding to v:errors.
" "assert" must be a (lambda) function containing one assert function.
" Example:
"	call WaitForAssert({-> assert_equal("dead", job_status(job)})
"
" A second argument can be used to specify a different timeout in msec.
"
" Return zero for success, one for failure (like the assert function).
func WaitForAssert(assert, ...)
  let timeout = get(a:000, 0, 5000)
  if s:WaitForCommon(v:null, a:assert, timeout) < 0
    return 1
  endif
  return 0
endfunc

" Common implementation of WaitFor() and WaitForAssert().
" Either "expr" or "assert" is not v:null
" Return the waiting time for success, -1 for failure.
func s:WaitForCommon(expr, assert, timeout)
  " using reltime() is more accurate, but not always available
  let slept = 0
  if has('reltime')
    let start = reltime()
  endif

  let iters = 0

  let failed_before = len( v:errors ) > 0

  if failed_before
    let timeout = 250
  else
    let timeout = a:timeout
  endif

  while 1
    let iters += 1
    let errors_before = len( v:errors )
    if type(a:expr) == v:t_func
      let success = a:expr()
    elseif type(a:assert) == v:t_func
      let success = a:assert() == 0 && len( v:errors ) == errors_before
    else
      let success = eval(a:expr)
    endif

    if success
      return slept
    endif

    if iters % 20 == 0
      redraw!
    endif

    if slept >= timeout
      break
    endif

    if type(a:assert) == v:t_func
      " Remove the errors added by the assert function.
      let errors_added = len( v:errors ) - errors_before
      if errors_added > 0
        call remove( v:errors, -1 * errors_added, -1 )
      endif
    endif

    sleep 10m
    if has('reltime')
      let slept = float2nr(reltimefloat(reltime(start)) * 1000)
    else
      let slept += 10
    endif
  endwhile

  return -1  " timed out
endfunc

function! ThisTestIsFlaky()
  " Deprectaed for now
endfunction

" In vim, py3eval( 'None' ) returns v:none, which is not equal v:null
" but are same type v:t_null
" In neovim, py3eval( 'None' ) returns v:null, and v:none does not exist
function! AssertNull( actual ) abort
  return assert_equal( type( v:null ), type( a:actual ),
      \ 'actual: ' .. a:actual  )
endfunction

function! AssertNotNull( actual ) abort
  return assert_notequal( type( v:null ), type( a:actual ),
      \ 'actual: ' .. a:actual  )
endfunction

function! AssertMatchList( expected, actual ) abort
  let ret = assert_equal( len( a:expected ), len( a:actual ), a:actual )
  let len = min( [ len( a:expected ), len( a:actual ) ] )
  let idx = 0
  while idx < len
    let ret += assert_match( a:expected[ idx ], a:actual[ idx ], idx )
    let idx += 1
  endwhile
  return ret
endfunction


" Like getbufline() but support negative numbers for "start" and "end"
" A negative numbers means that many lines before '$'
function! GetBufLine( buf, start, end  = '$' )
  if type( a:start ) != v:t_string && a:start < 0
    let start = getbufinfo( a:buf )[ 0 ].linecount + a:start
  else
    let start = a:start
  endif

  if type( a:end ) != v:t_string && a:end < 0
    let end = getbufinfo( a:buf )[ 0 ].linecount + a:end
  else
    let end = a:end
  endif

  return getbufline( a:buf, start, end )
endfunction

function! SkipNeovim() abort
  if has( 'nvim' )
    throw 'skipped: Neovim'
  endif
endfunction

function! SkipOn( arch, system ) abort
  if trim( system( 'uname -m' ) ) == a:arch &&
        \ trim( system( 'uname -s' ) ) == a:system
    throw 'skipped: Not on this architecture'
  endif
endfunction

function! SkipIf( f, msg ) abort
  if a:f()
    throw 'skipped: ' . a:msg
  endif
endfunction

function! FunctionBreakOnBrace() abort
  " Annoyingly, the behaviour of gcc 8 differs from clang _and_ it differs
  " between x86 and arm
  return trim( system( 'uname -m' ) ) ==# 'x86_64'
        \ && trim( system( 'uname -s' ) ) ==# 'Linux'
endfunction
