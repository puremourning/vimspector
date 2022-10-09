if exists( 'b:current_syntax' )
  finish
endif

runtime! syntax/asm.vim
unlet b:current_syntax

syn match VimspectorDisassemblyHexNibble "\<[A-F0-9]\{2}\>" display

hi def link VimspectorDisassemblyHexNibble asmHexadecimal

let b:current_syntax = 'vimspector-disassembly'
