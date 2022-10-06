scriptencoding utf-8

let cpo = &cpo
set cpo&

" Custom process picker {{{

function! PickProcessWithFzf( ... ) abort
  if a:0 == 0
    let source = 'ps -e'
  else
    let source = 'ps -e | grep ' .. a:1
  endif

  return split( fzf#run( fzf#wrap( { 'source': source }, 1 ) )[ 0 ] )[ 0 ]
endfunction

let g:vimspector_custom_process_picker_func = 'PickProcessWithFzf'

" }}}

let &cpo=cpo
