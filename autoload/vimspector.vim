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
  finish
endif

" Boilerplate {{{
let s:save_cpo = &cpoptions
set cpoptions&vim
" }}}

function! s:Debug( ... ) abort
  py3 <<EOF
if _vimspector_session is not None:
  _vimspector_session._logger.debug( *vim.eval( 'a:000' ) )
EOF
endfunction


" In vim, py3eval( 'None' ) returns v:none
" In neovim, py3eval( 'None' ) returns v:null
"
" Vim != Neovim. Go figure.
let s:None = has( 'nvim' ) ? v:null : v:none

function! s:Initialised() abort
  return exists( 's:enabled' )
endfunction

function! s:Enabled() abort
  if !s:Initialised()
    let s:enabled = vimspector#internal#state#Reset()
  endif

  if s:enabled && py3eval( '_vimspector_session is None' )
    " We have no active session, so create one
    call vimspector#internal#state#NewSession( {} )
  endif

  return s:enabled
endfunction

function! vimspector#NewSession( ... ) abort
  if !s:Enabled()
    return
  endif

  let options = {}
  if a:0 > 0
    call extend( options, { 'session_name': a:1 } )
  endif

  call vimspector#internal#state#NewSession( options )
endfunction

function! vimspector#SwitchToSession( name ) abort
  if !s:Enabled()
    return
  endif

  py3 << EOF
s = _vimspector_session_man.FindSessionByName( vim.eval( 'a:name' ) )
if s is not None:
  _VimspectorSwitchTo( s )
EOF
endfunction

function! vimspector#DestroySession( name ) abort
  if !s:Enabled()
    return
  endif

  py3 << EOF

s = _vimspector_session_man.FindSessionByName( vim.eval( 'a:name' ) )
if s is not None:
  s = _vimspector_session_man.DestroyRootSession( s, _vimspector_session )
  _VimspectorMakeActive( s )

EOF
endfunction

function! vimspector#CompleteSessionName( ArgLead, CmdLine, CursorPos ) abort
  " Don't call s:Enabled() because we don't want this function to initialise a
  " new session
  if !s:Initialised() || !s:enabled || py3eval( '_vimspector_session is None' )
    return ''
  endif
  return py3eval( '"\n".join( _vimspector_session_man.GetSessionNames() )' )
endfunction

function! vimspector#GetSessionName() abort
  if !s:Initialised() || !s:enabled || py3eval( '_vimspector_session is None' )
    return ''
  endif

  return py3eval( '_vimspector_session.Name()' )
endfunction

function! vimspector#GetSessionID() abort
  if !s:Initialised() || !s:enabled || py3eval( '_vimspector_session is None' )
    return ''
  endif

  return py3eval( '_vimspector_session.session_id' )
endfunction

function! vimspector#RenameSession( name ) abort
  if !s:Enabled()
    return
  endif
  py3 _vimspector_session.name = vim.eval( 'a:name' )
endfunction

function! vimspector#Launch( ... ) abort
  if !s:Enabled()
    return
  endif
  py3 _vimspector_session.Start( *vim.eval( 'a:000' ) )
endfunction

function! vimspector#LaunchWithConfigurations( configurations ) abort
  if !s:Enabled()
    return
  endif
  py3 _vimspector_session.Start(
        \ adhoc_configurations = vim.eval( 'a:configurations' ) )
endfunction

function! vimspector#LaunchWithSettings( settings ) abort
  if !s:Enabled()
    return
  endif
  py3 _vimspector_session.Start( launch_variables = vim.eval( 'a:settings' ) )
endfunction

function! vimspector#Reset( ... ) abort
  if !s:Enabled()
    return
  endif
  if a:0 == 0
    let options = {}
  else
    let options = a:1
  endif
  py3 _vimspector_session.Reset( **vim.eval( 'options' ) )
endfunction

function! vimspector#Restart() abort
  if !s:Enabled()
    return
  endif
  py3 _vimspector_session.Restart()
endfunction

function! vimspector#ClearBreakpoints() abort
  if !s:Enabled()
    return
  endif
  py3 _vimspector_session.ClearBreakpoints()
endfunction

let s:extended_breakpoint_properties = [
      \ { 'prop': 'condition', 'msg': 'Enter condition expression' },
      \ { 'prop': 'hitCondition', 'msg': 'Enter hit count expression' },
      \ { 'prop': 'logMessage',
      \   'msg': 'Enter log expression (to make log point)' },
    \ ]

function! s:AskForInput( ... ) abort
  return py3eval( '__import__( "vimspector", fromlist=[ "utils" ] )'
                \ . '.utils.AskForInput( *vim.eval( "a:000" ) )' )
endfunction

function! s:GetAdvancedBreakpointOptions() abort
  let options = {}
  for spec in s:extended_breakpoint_properties
    let response = s:AskForInput( spec.msg . ': ' )
    if response is s:None
      return s:None
    elseif response !=# ''
      let options[ spec.prop ] = response
    endif
  endfor

  return options
endfunction


function! vimspector#ToggleAdvancedBreakpoint() abort
  let options = s:GetAdvancedBreakpointOptions()
  if options is s:None
    return
  endif
  call vimspector#ToggleBreakpoint( options )
endfunction

function! vimspector#ToggleBreakpoint( ... ) abort
  if !s:Enabled()
    return
  endif
  if a:0 == 0
    let options = {}
  else
    let options = a:1
  endif
  py3 _vimspector_session.ToggleBreakpoint( vim.eval( 'options' ) )
endfunction

function! vimspector#SetAdvancedLineBreakpoint() abort
  if !s:Enabled()
    return
  endif
  let filename = s:AskForInput( 'File: ', expand( '#' ), 'file' )
  if filename ==# '' || filename is s:None
    return
  endif
  let line = s:AskForInput( 'Line number: ' )
  if line ==# '' || line is s:None
    return
  endif
  let options = s:GetAdvancedBreakpointOptions()
  if options is s:None
    return
  endif
  return vimspector#SetLineBreakpoint( filename, line, options )
endfunction

function! vimspector#SetLineBreakpoint( file_name, line_num, ... ) abort
  if !s:Enabled()
    return
  endif
  if a:0 == 0
    let options = {}
  else
    let options = a:1
  endif
  py3 _vimspector_session.SetLineBreakpoint(
        \ vim.eval( 'a:file_name' ),
        \ int( vim.eval( 'a:line_num' ) ),
        \ vim.eval( 'options' ) )
endfunction

function! vimspector#ClearLineBreakpoint( file_name, line_num ) abort
  if !s:Enabled()
    return
  endif
  py3 _vimspector_session.ClearLineBreakpoint(
        \ vim.eval( 'a:file_name' ),
        \ int( vim.eval( 'a:line_num' ) ) )
endfunction


function! vimspector#RunToCursor() abort
  if !s:Enabled()
    return
  endif
  py3 _vimspector_session.RunTo(
        \ vim.eval( "expand( '%' )" ),
        \ int( vim.eval( "line( '.' )" ) ) )
endfunction


function! vimspector#GoToCurrentLine() abort
  if !s:Enabled()
    return
  endif
  py3 _vimspector_session.GoTo(
        \ vim.eval( "expand( '%' )" ),
        \ int( vim.eval( "line( '.' )" ) ) )
endfunction


function! vimspector#AddFunctionBreakpoint( function, ... ) abort
  if !s:Enabled()
    return
  endif
  if a:0 == 0
    let options = {}
  else
    let options = a:1
  endif
  py3 _vimspector_session.AddFunctionBreakpoint( vim.eval( 'a:function' ),
                                               \ vim.eval( 'options' ) )
endfunction


function! vimspector#AddAdvancedFunctionBreakpoint() abort
  if !s:Enabled()
    return
  endif
  let function = s:AskForInput( 'Function: ', s:None, 'tag' )
  if function ==# '' || function == s:None
    return
  endif
  let options = s:GetAdvancedBreakpointOptions()
  if options is s:None
    return
  endif
  return vimspector#AddFunctionBreakpoint( function, options )
endfunction

function! vimspector#StepOver( ... ) abort
  if !s:Enabled()
    return
  endif
  if a:0 == 0
    let args = {}
  else
    let args = a:1
  endif
  py3 _vimspector_session.StepOver( **vim.eval( 'args' ) )
endfunction

function! vimspector#StepInto( ... ) abort
  if !s:Enabled()
    return
  endif
  if a:0 == 0
    let args = {}
  else
    let args = a:1
  endif
  py3 _vimspector_session.StepInto( **vim.eval( 'args' ) )
endfunction

function! vimspector#StepOut( ... ) abort
  if !s:Enabled()
    return
  endif
  if a:0 == 0
    let args = {}
  else
    let args = a:1
  endif
  py3 _vimspector_session.StepOut( **vim.eval( 'args' ) )
endfunction

function! vimspector#StepSOver() abort
  return vimspector#StepOver( { 'granularity': 'statement' } )
endfunction

function! vimspector#StepSInto() abort
  return vimspector#StepInto( { 'granularity': 'statement' } )
endfunction

function! vimspector#StepSOut() abort
  return vimspector#StepOut( { 'granularity': 'statement' } )
endfunction

function! vimspector#StepIOver() abort
  return vimspector#StepOver( { 'granularity': 'instruction' } )
endfunction

function! vimspector#StepIInto() abort
  return vimspector#StepInto( { 'granularity': 'instruction' } )
endfunction

function! vimspector#StepIOut() abort
  return vimspector#StepOut( { 'granularity': 'instruction' } )
endfunction

function! vimspector#Continue() abort
  if !s:Enabled()
    return
  endif
  py3 _vimspector_session.Continue()
endfunction

function! vimspector#Pause() abort
  if !s:Enabled()
    return
  endif
  py3 _vimspector_session.Pause()
endfunction

function! vimspector#PauseContinueThread() abort
  if !s:Enabled()
    return
  endif
  py3 _vimspector_session.PauseContinueThread()
endfunction

function! vimspector#SetCurrentThread() abort
  if !s:Enabled()
    return
  endif
  py3 _vimspector_session.SetCurrentThread()
endfunction

function! vimspector#Stop( ... ) abort
  if !s:Enabled()
    return
  endif
  if a:0 == 0
    let options = {}
  else
    let options = a:1
  endif
  py3 _vimspector_session.Stop( **vim.eval( 'options' ) )
endfunction

function! vimspector#ExpandVariable() abort
  if !s:Enabled()
    return
  endif
  py3 _vimspector_session.ExpandVariable()
endfunction

function! vimspector#SetVariableValue( ... ) abort
  if !s:Enabled()
    return
  endif
  if a:0 == 0
    py3 _vimspector_session.SetVariableValue()
  else
    py3 _vimspector_session.SetVariableValue( new_value = vim.eval( 'a:1' ) )
  endif
endfunction

function! vimspector#ReadMemory( ... ) abort
  if !s:Enabled()
    return
  endif
  let opts = {}
  if a:0 > 0
    let opts = a:1
  endif
  py3 _vimspector_session.ReadMemory( **vim.eval( 'opts' ) )
endfunction

function! vimspector#ShowDisassembly( ... ) abort
  if !s:Enabled()
    return
  endif
  py3 _vimspector_session.ShowDisassembly()
endfunction

function! vimspector#DeleteWatch() abort
  if !s:Enabled()
    return
  endif
  py3 _vimspector_session.DeleteWatch()
endfunction

function! vimspector#GoToFrame() abort
  if !s:Enabled()
    return
  endif
  py3 _vimspector_session.ExpandFrameOrThread()
endfunction

function! vimspector#UpFrame() abort
  if !s:Enabled()
    return
  endif
  py3 _vimspector_session.UpFrame()
endfunction

function! vimspector#DownFrame() abort
  if !s:Enabled()
    return
  endif
  py3 _vimspector_session.DownFrame()
endfunction

function! vimspector#AddWatch( ... ) abort
  if !s:Enabled()
    return
  endif
  if a:0 == 0
    let expr = s:AskForInput( 'Enter watch expression: ',
                            \ '',
                            \ 'custom,vimspector#CompleteExpr' )
  else
    let expr = a:1
  endif

  if expr ==# ''
    return
  endif

  py3 _vimspector_session.AddWatch( vim.eval( 'expr' ) )
endfunction

function! vimspector#AddWatchPrompt( expr ) abort
  if !s:Enabled()
    return
  endif
  stopinsert
  setlocal nomodified
  call vimspector#AddWatch( a:expr )
endfunction

function! vimspector#Evaluate( expr ) abort
  if !s:Enabled()
    return
  endif
  py3 _vimspector_session.ShowOutput( 'Console' )
  py3 _vimspector_session.EvaluateConsole( vim.eval( 'a:expr' ), True )
endfunction

function! vimspector#EvaluateConsole( expr ) abort
  if !s:Enabled()
    return
  endif
  stopinsert
  setlocal nomodified
  py3 _vimspector_session.EvaluateConsole( vim.eval( 'a:expr' ), False )
endfunction

function! vimspector#ShowOutput( ... ) abort
  if !s:Enabled()
    return
  endif
  if a:0 == 1
    py3 _vimspector_session.ShowOutput( vim.eval( 'a:1' ) )
  else
    py3 _vimspector_session.ShowOutput( 'Console' )
  endif
endfunction

function! vimspector#ShowOutputInWindow( win_id, category ) abort
  if !s:Enabled()
    return
  endif
  py3 __import__( 'vimspector',
        \         fromlist = [ 'output' ] ).output.ShowOutputInWindow(
        \           int( vim.eval( 'a:win_id' ) ),
        \           vim.eval( 'a:category' ) )
endfunction

function! vimspector#ToggleLog() abort
  if !s:Enabled()
    return
  endif
  py3 _vimspector_session.ToggleLog()
endfunction

function! vimspector#ListBreakpoints() abort
  if !s:Enabled()
    return
  endif
  py3 _vimspector_session.ListBreakpoints()
endfunction

function! vimspector#GetBreakpointsAsQuickFix() abort
  if !s:Enabled()
    return
  endif
  return py3eval( '_vimspector_session.BreakpointsAsQuickFix()' )
endfunction

function! vimspector#ToggleBreakpointViewBreakpoint() abort
  if !s:Enabled()
    return
  endif
  py3 _vimspector_session.ToggleBreakpointViewBreakpoint()
endfunction

function! vimspector#ToggleAllBreakpointsViewBreakpoint() abort
  if !s:Enabled()
    return
  endif
  py3 _vimspector_session.ToggleAllBreakpointsViewBreakpoint()
endfunction

function! vimspector#DeleteBreakpointViewBreakpoint() abort
  if !s:Enabled()
    return
  endif
  py3 _vimspector_session.DeleteBreakpointViewBreakpoint()
endfunction

function! vimspector#JumpToBreakpointViewBreakpoint() abort
  if !s:Enabled()
    return
  endif
  py3 _vimspector_session.JumpToBreakpointViewBreakpoint()
endfunction

function! vimspector#JumpToNextBreakpoint() abort
  if !s:Enabled()
    return
  endif
  py3 _vimspector_session.JumpToNextBreakpoint()
endfunction

function! vimspector#JumpToPreviousBreakpoint() abort
  if !s:Enabled()
    return
  endif
  py3 _vimspector_session.JumpToPreviousBreakpoint()
endfunction

function! vimspector#JumpToProgramCounter() abort
  if !s:Enabled()
    return
  endif
  py3 _vimspector_session.JumpToProgramCounter()
endfunction

function! vimspector#GetConfigurations() abort
  if !s:Enabled()
    return
  endif
  let configurations = py3eval(
        \ 'list( _vimspector_session.GetConfigurations( {} )[ 1 ].keys() )'
        \ . ' if _vimspector_session else []' )
  return configurations
endfunction

function! vimspector#CompleteOutput( ArgLead, CmdLine, CursorPos ) abort
  if !s:Enabled()
    return ''
  endif
  let buffers = py3eval( '_vimspector_session.GetOutputBuffers() '
                       \ . ' if _vimspector_session else []' )
  return buffers
endfunction

function! vimspector#CompleteExpr( ArgLead, CmdLine, CursorPos ) abort
  if !s:Enabled()
    return ''
  endif

  let col = len( a:ArgLead )
  let prev_non_keyword_char = match( a:ArgLead[ 0 : col - 1 ], '\k*$' ) + 1

  return join( py3eval( '_vimspector_session.GetCommandLineCompletions( '
                      \ . 'vim.eval( "a:ArgLead" ), '
                      \ . 'int( vim.eval( "prev_non_keyword_char" ) ) )' ),
             \ "\n" )
endfunction

let s:latest_completion_request = {}

function! vimspector#CompleteFuncSync( prompt, find_start, query ) abort
  if py3eval( 'not _vimspector_session' )
    if a:find_start
      return -3
    endif
    return s:None
  endif

  if a:find_start

    " We're busy
    if !empty( s:latest_completion_request )
      return -3
    endif

    let line = getline( line( '.' ) )[ len( a:prompt ) : ]
    let col = col( '.' ) - len( a:prompt )

    " It seems that most servers don't implement the 'start' parameter, which is
    " clearly necessary, as they all seem to assume a specific behaviour, which
    " is undocumented.

    let s:latest_completion_request.items =
          \ py3eval( '_vimspector_session.GetCompletionsSync( '
                   \.'  vim.eval( "line" ), '
                   \.'  int( vim.eval( "col" ) ) )' )

    let s:latest_completion_request.line = line
    let s:latest_completion_request.col = col

    let prev_non_keyword_char = match( line[ 0 : col - 1 ], '\k*$' ) + 1
    let query_len = col - prev_non_keyword_char

    let start_pos = col
    for item in s:latest_completion_request.items
      if !has_key( item, 'start' ) || !has_key( item, 'length' )
        " The specification states that if start is not supplied, isertion
        " should be at the requested column. But about 0 of the servers actually
        " implement that
        " (https://github.com/microsoft/debug-adapter-protocol/issues/138)
        let item.start = prev_non_keyword_char
        let item.length = query_len
      else
        " For some reason, the returned start value is 0-indexed even though we
        " use columnsStartAt1
        let item.start += 1
      endif

      if !has_key( item, 'text' )
        let item.text = item.label
      endif

      if item.start < start_pos
        let start_pos = item.start
      endif
    endfor

    let s:latest_completion_request.start_pos = start_pos
    let s:latest_completion_request.prompt = a:prompt

    " call s:Debug( 'FindStart: %s', {
    "       \ 'line': line,
    "       \ 'col': col,
    "       \ 'prompt': len( a:prompt ),
    "       \ 'start_pos': start_pos,
    "       \ 'returning': ( start_pos + len( a:prompt ) ) - 1,
    "       \ } )

    " start_pos is 1-based and the return of findstart is 0-based
    return ( start_pos + len( a:prompt ) ) - 1
  else
    let items = []
    let pfxlen = len( s:latest_completion_request.prompt )
    for item in s:latest_completion_request.items
      if item.start > s:latest_completion_request.start_pos
        " fix up the text (insert anything that is already present in the line
        " that would be erased by the fixed-up earlier start position)
        "
        " both start_pos and item.start are 1-based
        let item.text = s:latest_completion_request.line[
              \ s:latest_completion_request.start_pos + pfxlen - 1 :
              \  item.start + pfxlen - 1 ] . item.text
      endif

      if item.length > len( a:query )
        " call s:Debug( 'Rejecting %s, length is greater than %s',
        "       \ item,
        "       \ len( a:query ) )
        continue
      endif

      call add( items, { 'word': item.text,
                       \ 'abbr': item.label,
                       \ 'menu': get( item, 'type', '' ),
                       \ 'icase': 1,
                       \ } )
    endfor
    let s:latest_completion_request = {}

    " call s:Debug( 'Items: %s', items )
    return { 'words': items, 'refresh': 'always' }
  endif
endfunction

function! vimspector#OmniFuncWatch( find_start, query ) abort
  return vimspector#CompleteFuncSync( 'Expression: ', a:find_start, a:query )
endfunction

function! vimspector#OmniFuncConsole( find_start, query ) abort
  return vimspector#CompleteFuncSync( '> ', a:find_start, a:query )
endfunction

function! vimspector#Install( bang, ... ) abort
  if !s:Enabled()
    return
  endif
  let prefix = vimspector#internal#state#GetAPIPrefix()
  py3 __import__( 'vimspector',
        \         fromlist = [ 'installer' ] ).installer.RunInstaller(
        \           vim.eval( 'prefix' ),
        \           vim.eval( 'a:bang' ) == '!',
        \           *vim.eval( 'a:000' ) )
endfunction

function! vimspector#CompleteInstall( ArgLead, CmdLine, CursorPos ) abort
  if !s:Enabled()
    return
  endif
  return py3eval( '"\n".join('
                \ .   '__import__( "vimspector", fromlist = [ "gadgets" ] )'
                \ .   '.gadgets.GADGETS.keys() '
                \ . ')' )
endfunction

function! vimspector#Update( bang, ... ) abort
  if !s:Enabled()
    return
  endif

  let prefix = vimspector#internal#state#GetAPIPrefix()
  py3 __import__( 'vimspector',
        \         fromlist = [ 'installer' ] ).installer.RunUpdate(
        \           vim.eval( 'prefix' ),
        \           vim.eval( 'a:bang' ) == '!',
        \           *vim.eval( 'a:000' ) )
endfunction

function! vimspector#AbortInstall() abort
  if !s:Enabled()
    return
  endif

  let prefix = vimspector#internal#state#GetAPIPrefix()
  py3 __import__( 'vimspector', fromlist = [ 'installer' ] ).installer.Abort()
endfunction


function! vimspector#OnBufferCreated( file_name ) abort
  if len( a:file_name ) == 0
    return
  endif

  " Don't actually load up vimspector python in autocommands that trigger
  " regularly. We'll only create the session obkect in s:Enabled()
  if !s:Initialised()
    return
  endif

  if !s:Enabled()
    return
  endif

  py3 _vimspector_session.RefreshSigns()
endfunction

function! vimspector#ShowEvalBalloon( is_visual ) abort
  if a:is_visual
    let expr = py3eval( '__import__( "vimspector", fromlist = [ "utils" ] )'
                      \ . '.utils.GetVisualSelection('
                      \ . '    int( vim.eval( "winbufnr( winnr() )" ) ) )' )
    let expr = join( expr, '\n' )
  else
    let expr = expand( '<cexpr>' )
  endif

  let line = line( '.' )

  return py3eval( '_vimspector_session.HoverEvalTooltip('
                \ . ' int( vim.eval( "winnr()" ) ), '
                \ . ' int( vim.eval( "bufnr()" ) ), '
                \ . ' int( vim.eval( "line" ) ), '
                \ . '"' . expr . '", '
                \ . '0 )' )
endfunction

function! vimspector#PrintDebugInfo() abort
  if !s:Enabled()
    return
  endif

  py3 _vimspector_session.PrintDebugInfo()
endfunction

function! vimspector#ReadSessionFile( ... ) abort
  if !s:Enabled()
    return
  endif

  py3 _vimspector_session.ReadSessionFile( *vim.eval( 'a:000' ) )
endfunction

function! vimspector#WriteSessionFile( ... ) abort
  if !s:Enabled()
    return
  endif

  py3 _vimspector_session.WriteSessionFile( *vim.eval( 'a:000' ) )
endfunction

" Boilerplate {{{
let &cpoptions=s:save_cpo
unlet s:save_cpo
" }}}
