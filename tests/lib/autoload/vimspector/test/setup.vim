function! vimspector#test#setup#SetUpWithMappings( mappings ) abort
  if exists ( 'g:loaded_vimpector' )
    unlet g:loaded_vimpector
  endif

  if a:mappings != v:none
    let g:vimspector_enable_mappings = a:mappings
  endif

  source vimrc

  " This is a bit of a hack
  runtime! plugin/**/*.vim

  augroup VimspectorTestSwap
    au!
    au SwapExists * let v:swapchoice = 'e'
  augroup END

endfunction

function! vimspector#test#setup#ClearDown() abort
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

  call popup_clear()
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
