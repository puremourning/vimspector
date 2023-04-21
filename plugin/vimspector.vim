" vimspector - A multi-language debugging system for Vim
" Copyright 2018 Ben Jackson
"
" Licensed under the Apache License, Version 2.0 (the "License");
" you may not use this file except in compliance with the License.
" You may obtain a copy of the License at
"
"   http://www.apache.org/licenses/LICENSE-2.0
"
" Unless required by applicable law or agreed to in writing, software
" distributed under the License is distributed on an "AS IS" BASIS,
" WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
" See the License for the specific language governing permissions and
" limitations under the License.

if !has( 'python3' )
  augroup VimspectorNoPython
    autocmd!
    autocmd VimEnter *
          \   echohl WarningMsg
          \ | echom 'Vimspector unavailable: Requires Vim compiled with +python3'
          \ | echohl None
  augroup END
  finish
endif

" Boilerplate {{{
let s:save_cpo = &cpoptions
set cpoptions&vim

function! s:restore_cpo()
  let &cpoptions=s:save_cpo
  unlet s:save_cpo
endfunction

if exists( 'g:loaded_vimpector' )
  call s:restore_cpo()
  finish
endif
"}}}

let g:loaded_vimpector = 1
let g:vimspector_home = expand( '<sfile>:p:h:h' )

let s:mappings = get( g:, 'vimspector_enable_mappings', '' )

" Let the <Plug>mapping can be repeated with the "." command, it's powered by
" [repeat.vim](https://github.com/tpope/vim-repeat).
function! s:SetRepeat( map ) abort
  try
    call repeat#set( a:map )
  catch /^Vim\%((\a\+)\)\=:E117:/
    " Catch 'E117: Unknown function' exception if the user doesn't have the
    " 'repeat.vim' installed.
  endtry
endfunction

nnoremap <silent> <Plug>VimspectorContinue
      \ :<c-u>call <SID>SetRepeat( "\<Plug>VimspectorContinue" )<CR>
      \:<c-u>call vimspector#Continue()<CR>
nnoremap <silent> <Plug>VimspectorLaunch
      \ :<c-u>call vimspector#Launch( v:true )<CR>
nnoremap <silent> <Plug>VimspectorStop
      \ :<c-u>call vimspector#Stop()<CR>
nnoremap <silent> <Plug>VimspectorRestart
      \ :<c-u>call vimspector#Restart()<CR>
nnoremap <silent> <Plug>VimspectorPause
      \ :<c-u>call vimspector#Pause()<CR>
nnoremap <silent> <Plug>VimspectorToggleBreakpoint
      \ :<c-u>call <SID>SetRepeat( "\<Plug>VimspectorToggleBreakpoint" )<CR>
      \:<c-u>call vimspector#ToggleBreakpoint()<CR>
nnoremap <silent> <Plug>VimspectorToggleConditionalBreakpoint
      \ :<c-u>call <SID>SetRepeat( "\<Plug>VimspectorToggleConditionalBreakpoint" )<CR>
      \:<c-u>call vimspector#ToggleAdvancedBreakpoint()<CR>
nnoremap <silent> <Plug>VimspectorAddFunctionBreakpoint
      \ :<c-u>call <SID>SetRepeat( "\<Plug>VimspectorAddFunctionBreakpoint" )<CR>
      \:<c-u>call vimspector#AddFunctionBreakpoint( expand( '<cexpr>' ) )<CR>
nnoremap <silent> <Plug>VimspectorStepOver
      \ :<c-u>call <SID>SetRepeat( "\<Plug>VimspectorStepOver" )<CR>
      \:<c-u>call vimspector#StepOver()<CR>
nnoremap <silent> <Plug>VimspectorStepInto
      \ :<c-u>call <SID>SetRepeat( "\<Plug>VimspectorStepInto" )<CR>
      \:<c-u>call vimspector#StepInto()<CR>
nnoremap <silent> <Plug>VimspectorStepOut
      \ :<c-u>call <SID>SetRepeat( "\<Plug>VimspectorStepOut" )<CR>
      \:<c-u>call vimspector#StepOut()<CR>

nnoremap <silent> <Plug>VimspectorRunToCursor
      \ :<c-u>call <SID>SetRepeat( "\<Plug>VimspectorRunToCursor" )<CR>
      \:<c-u>call vimspector#RunToCursor()<CR>
nnoremap <silent> <Plug>VimspectorGoToCurrentLine
      \ :<c-u>call <SID>SetRepeat( "\<Plug>VimspectorGoToCurrentLine" )<CR>
      \:<c-u>call vimspector#GoToCurrentLine()<CR>

" Eval for normal mode
nnoremap <silent> <Plug>VimspectorBalloonEval
      \ :<c-u>call <SID>SetRepeat( "\<Plug>VimspectorBalloonEval" )<CR>
      \:<c-u>call vimspector#ShowEvalBalloon( 0 )<CR>
" And for visual modes
xnoremap <silent> <Plug>VimspectorBalloonEval
      \ :<c-u>call <SID>SetRepeat( "\<Plug>VimspectorBalloonEval" )<CR>
      \:<c-u>call vimspector#ShowEvalBalloon( 1 )<CR>
nnoremap <silent> <Plug>VimspectorUpFrame
      \ :<c-u>call <SID>SetRepeat( "\<Plug>VimspectorUpFrame" )<CR>
      \:<c-u>call vimspector#UpFrame()<CR>
nnoremap <silent> <Plug>VimspectorDownFrame
      \ :<c-u>call <SID>SetRepeat( "\<Plug>VimspectorDownFrame" )<CR>
      \:<c-u>call vimspector#DownFrame()<CR>
nnoremap <silent> <Plug>VimspectorJumpToNextBreakpoint
      \ :<c-u>call <SID>SetRepeat( "\<Plug>VimspectorJumpToNextBreakpoint" )<CR>
      \ :<c-u>call vimspector#JumpToNextBreakpoint()<CR>
nnoremap <silent> <Plug>VimspectorJumpToPreviousBreakpoint
      \ :<c-u>call <SID>SetRepeat( "\<Plug>VimspectorJumpToPreviousBreakpoint" )<CR>
      \ :<c-u>call vimspector#JumpToPreviousBreakpoint()<CR>
nnoremap <silent> <Plug>VimspectorJumpToProgramCounter
      \ :<c-u>call vimspector#JumpToProgramCounter()<CR>

nnoremap <silent> <Plug>VimspectorBreakpoints
      \ :<c-u>call vimspector#ListBreakpoints()<CR>
nnoremap <silent> <Plug>VimspectorDisassemble
      \ :<c-u>call vimspector#ShowDisassembly()<CR>

if s:mappings ==# 'VISUAL_STUDIO'
  nmap <F5>         <Plug>VimspectorContinue
  nmap <S-F5>       <Plug>VimspectorStop
  nmap <C-S-F5>     <Plug>VimspectorRestart
  nmap <F6>         <Plug>VimspectorPause
  nmap <F8>         <Plug>VimspectorJumpToNextBreakpoint
  nmap <S-F8>       <Plug>VimspectorJumpToPreviousBreakpoint
  nmap <F9>         <Plug>VimspectorToggleBreakpoint
  nmap <S-F9>       <Plug>VimspectorAddFunctionBreakpoint
  nmap <F10>        <Plug>VimspectorStepOver
  nmap <F11>        <Plug>VimspectorStepInto
  nmap <S-F11>      <Plug>VimspectorStepOut
  nmap <M-8>        <Plug>VimspectorDisassemble
elseif s:mappings ==# 'HUMAN'
  nmap <F5>         <Plug>VimspectorContinue
  nmap <leader><F5> <Plug>VimspectorLaunch
  nmap <F3>         <Plug>VimspectorStop
  nmap <F4>         <Plug>VimspectorRestart
  nmap <F6>         <Plug>VimspectorPause
  nmap <F9>         <Plug>VimspectorToggleBreakpoint
  nmap <leader><F9> <Plug>VimspectorToggleConditionalBreakpoint
  nmap <F8>         <Plug>VimspectorAddFunctionBreakpoint
  nmap <leader><F8> <Plug>VimspectorRunToCursor
  nmap <F10>        <Plug>VimspectorStepOver
  nmap <F11>        <Plug>VimspectorStepInto
  nmap <F12>        <Plug>VimspectorStepOut
endif

" Session commands
command! -bar -nargs=?
      \ VimspectorNewSession
      \ call vimspector#NewSession( <f-args> )
command! -bar -nargs=1 -complete=custom,vimspector#CompleteSessionName
      \ VimspectorSwitchToSession
      \ call vimspector#SwitchToSession( <f-args> )
command! -bar -nargs=1
      \ VimspectorRenameSession
      \ call vimspector#RenameSession( <f-args> )
command! -bar -nargs=1 -complete=custom,vimspector#CompleteSessionName
      \ VimspectorDestroySession
      \ call vimspector#DestroySession( <f-args> )

command! -bar -nargs=1 -complete=custom,vimspector#CompleteExpr
      \ VimspectorWatch
      \ call vimspector#AddWatch( <f-args> )
command! -bar -nargs=? -complete=customlist,vimspector#CompleteOutput
      \ VimspectorShowOutput
      \ call vimspector#ShowOutput( <f-args> )
command! -bar
      \ VimspectorToggleLog
      \ call vimspector#ToggleLog()
command! -bar
      \ VimspectorDebugInfo
      \ call vimspector#PrintDebugInfo()
command! -nargs=1 -complete=custom,vimspector#CompleteExpr
      \ VimspectorEval
      \ call vimspector#Evaluate( <f-args> )
command! -bar
      \ VimspectorReset
      \ call vimspector#Reset( { 'interactive': v:true } )
command! -bar
      \ VimspectorBreakpoints
      \ call vimspector#ListBreakpoints()
command! -bar
      \ VimspectorDisassemble
      \ call vimspector#ShowDisassembly()

" Installer commands
command! -bar -bang -nargs=* -complete=custom,vimspector#CompleteInstall
      \ VimspectorInstall
      \ call vimspector#Install( <q-bang>, <f-args> )
command! -bar -bang -nargs=*
      \ VimspectorUpdate
      \ call vimspector#Update( <q-bang>, <f-args> )
command! -bar -nargs=0
      \ VimspectorAbortInstall
      \ call vimspector#AbortInstall()

" Session files
command! -bar -nargs=? -complete=file
      \ VimspectorLoadSession
      \ call vimspector#ReadSessionFile( <f-args> )
command! -bar -nargs=? -complete=file
      \ VimspectorMkSession
      \ call vimspector#WriteSessionFile( <f-args> )


" Dummy autocommands so that we can call this whenever
augroup VimspectorUserAutoCmds
  autocmd!
  autocmd User VimspectorUICreated      silent
  autocmd User VimspectorTerminalOpened silent
  autocmd user VimspectorJumpedToFrame  silent
  autocmd user VimspectorDebugEnded     silent
augroup END

" FIXME: Only register this _while_ debugging is active
let g:vimspector_resetting = 0
augroup Vimspector
  autocmd!
  autocmd BufNew * call vimspector#OnBufferCreated( expand( '<afile>' ) )
  autocmd TabClosed *
        \   if !g:vimspector_resetting
        \ |   call vimspector#internal#state#TabClosed( expand( '<afile>' ) )
        \ | endif
  autocmd TabEnter * call vimspector#internal#state#OnTabEnter()
augroup END

" boilerplate {{{
call s:restore_cpo()
" }}}
