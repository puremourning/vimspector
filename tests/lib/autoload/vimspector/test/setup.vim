function! vimspector#test#setup#SetUpWithMappings( mappings ) abort
  if exists ( 'g:loaded_vimpector' )
    unlet g:loaded_vimpector
  endif

  if a:mappings != v:null
    let g:vimspector_enable_mappings = a:mappings
  endif

  source vimrc

  " This is a bit of a hack
  runtime! plugin/**/*.vim

  augroup VimspectorTestSwap
    au!
    au SwapExists * let v:swapchoice = 'e'
  augroup END

  " If requested, launch debugpy
  if exists( '$TEST_WITH_DEBUGPY' ) &&
        \ $TEST_WITH_DEBUGPY != '0' &&
        \ !exists( 'g:debugpy_loaded' )
    let g:debugpy_loaded = 1
    py3 __import__( 'vimspector',
                  \ fromlist=[ 'developer' ] ).developer.SetUpDebugpy(
                  \   wait=True )
  endif
endfunction

function! vimspector#test#setup#PushSetting( setting, value ) abort
  if !exists( 's:SETTING' )
    let s:SETTING = {}
  endif

  if has_key( g:, a:setting )
    let s:SETTING[ a:setting ] = g:[ a:setting ]
  else
    let s:SETTING[ a:setting ] = v:null
  endif
  call TestLog( 'Overriding ' . a:setting . ' to ' . string( a:value ) )
  let g:[ a:setting ] = a:value
endfunction

function! vimspector#test#setup#TearDown() abort
  if exists( 's:SETTING' )
    for key in keys( s:SETTING )
      call TestLog( 'Resetting ' . key . ' to ' . string( s:SETTING[ key ] ) )
      if s:SETTING[ key ] is v:null
        call remove( g:, key )
      else
        let g:[ key ] = s:SETTING[ key ]
      endif
    endfor
  endif

  unlet! s:SETTING
endfunction

function! vimspector#test#setup#WaitForReset() abort
  call WaitForAssert( {-> assert_equal( 1, len( gettabinfo() ) ) } )
  call WaitForAssert( {->
        \ assert_true( pyxeval( '_vimspector_session is None or ' .
        \                       '_vimspector_session._connection is None' ) )
        \ } )
  call WaitForAssert( {->
        \ assert_true( pyxeval( '_vimspector_session is None or ' .
        \                       '_vimspector_session._uiTab is None' ) )
        \ }, 10000 )

  call vimspector#test#signs#AssertSignGroupEmpty( 'VimspectorCode' )
endfunction

function! vimspector#test#setup#Reset() abort
  call vimspector#Reset()
  call vimspector#test#setup#WaitForReset()

  call vimspector#ClearBreakpoints()
  call vimspector#test#signs#AssertSignGroupEmpty( 'VimspectorBP' )

  if exists( '*vimspector#internal#state#Reset' )
    call vimspector#internal#state#Reset()
  endif

  if exists( '*popup_clear' )
    call popup_clear()
  endif
endfunction

let s:g_stack = {}

function! vimspector#test#setup#PushGlobal( name, value ) abort
  if !has_key( s:g_stack, a:name )
    let s:g_stack[ a:name ] = []
  endif

  let old_value = get( g:, a:name, v:null )
  call add( s:g_stack[ a:name ], old_value )
  let g:[ a:name ] = a:value

  return old_value
endfunction

function! vimspector#test#setup#PopGlobal( name ) abort
  if !has_key( s:g_stack, a:name ) || len( s:g_stack[ a:name ] ) == 0
    return v:null
  endif

  let old_value = s:g_stack[ a:name ][ -1 ]
  call remove( s:g_stack[ a:name ], -1 )

  if old_value is v:null
    silent! call remove( g:, a:name )
  else
    let g:[ a:name ] = old_value
  endif

  return old_value
endfunction

let s:o_stack = {}

function! vimspector#test#setup#PushOption( name, value ) abort
  if !has_key( s:o_stack, a:name )
    let s:o_stack[ a:name ] = []
  endif

  let old_value = v:null
  execute 'let old_value = &' . a:name
  call add( s:o_stack[ a:name ], old_value )
  execute 'set ' . a:name . '=' . a:value
  return old_value
endfunction

function! vimspector#test#setup#PopOption( name ) abort
  if !has_key( s:o_stack, a:name ) || len( s:o_stack[ a:name ] ) == 0
    return v:null
  endif

  let old_value = s:o_stack[ a:name ][ -1 ]
  call remove( s:o_stack[ a:name ], -1 )

  execute 'set ' . a:name . '=' . old_value
  return old_value
endfunction

