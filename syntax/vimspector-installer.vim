if exists( 'b:current_syntax' )
  finish
endif

let b:current_syntax = 'vimspector-installer'

syn keyword VimspectorInstalling Installing
syn keyword VimspectorDone  Done
syn keyword VimspectorError Failed FAILED

hi default link VimspectorInstalling Constant
hi default link VimspectorDone  DiffAdd
hi default link VimspectorError WarningMsg
