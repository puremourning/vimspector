if exists( 'b:current_syntax' )
  finish
endif

let b:current_syntax = 'vimspector-breakpoints'

syn keyword VimspectorBPEnabled ENABLED VERIFIED
syn keyword VimspectorBPDisabled DISABLED PENDING

syn match VimspectorBPFileLine /\v^\S+:{0,}/

hi default link VimspectorBPEnabled   WarningMsg
hi default link VimspectorBPDisabled  LineNr
hi default link VimspectorBPFileLine  CursorLineNr
