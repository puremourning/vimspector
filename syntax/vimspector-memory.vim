" Based on xxd syntax file by Charles E. Campbell

" quit when a syntax file was already loaded
if exists("b:current_syntax")
  finish
endif

syn match vimspectormemAddress "^[0-9a-fA-F]\+:" contains=vimspectormemSep
syn match vimspectormemAddress "0x[0-9a-fA-F]\+"
syn match vimspectormemSep     contained    ":"
syn match vimspectormemAscii   "  .\{,16\}\r\=$"hs=s+2 contains=vimspectormemDot
syn match vimspectormemDot     contained    "[.\r]"

syn keyword vimspectormemHeader Offset Bytes Text Length Reference
syn match vimspectormemHeader   "^-\{80}$"

hi def link vimspectormemAddress Constant
hi def link vimspectormemSep     Identifier
hi def link vimspectormemAscii   Statement
hi def link vimspectormemHeader  Title

let b:current_syntax = "vimspector-memory"

" vim: ts=4
