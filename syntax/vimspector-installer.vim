if exists( 'b:current_syntax' )
  finish
endif

let b:current_syntax = 'vimspector-installer'

syn match VimspectorGadget /[^ ]*\ze@/
syn match VimspectorGadgetVersion /@\@<=[^ ]*\ze\.\.\./


syn keyword VimspectorInstalling Installing
syn keyword VimspectorDone  Done
syn keyword VimspectorSkip  Skip
syn keyword VimspectorError Failed FAILED

hi default link VimspectorInstalling Constant
hi default link VimspectorDone  DiffAdd
hi default link VimspectorSkip  DiffAdd
hi default link VimspectorError WarningMsg
hi default link VimspectorGadget String
hi default link VimspectorGadgetVersion Identifier
