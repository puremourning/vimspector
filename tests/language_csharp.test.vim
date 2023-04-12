function! SetUp()
  call vimspector#test#setup#SetUpWithMappings( v:null )
endfunction

function! TearDown()
  call vimspector#test#setup#TearDown()
endfunction

function! SetUp_Test_Go_Simple()
  let g:vimspector_enable_mappings = 'HUMAN'
endfunction

function! SkipUnsupported() abort
  "call SkipOn( 'arm64', 'Darwin' )
endfunction

function! Test_CSharp_Simple_Adhoc_Config()
  call SkipNeovim()
  call SkipUnsupported()
  let fn='Program.cs'
  lcd ../support/test/csharp
  exe 'edit ' . fn

  call vimspector#SetLineBreakpoint( fn, 31 )
  call vimspector#LaunchWithConfigurations( {
    \ 'launch - netcoredbg': {
    \   'adapter': 'netcoredbg',
    \   'configuration': {
    \     'request': 'launch',
    \     'program': '${workspaceRoot}/bin/Debug/netcoreapp6.0/csharp.dll',
    \     'args': [],
    \     'stopAtEntry': v:false
    \   },
    \   'breakpoints': { 'exception': {
    \     'user-unhandled': '',
    \     'all': ''
    \   } },
    \ }
  \ } )
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 31, 7 )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer( fn, 31 )
        \ } )

  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 32, 12 )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer( fn, 32 )
        \ } )

  call vimspector#test#setup#Reset()

  lcd -
  %bwipeout!
endfunction

function! Test_CSharp_Simple_VimDict_Config()
  call vimspector#test#setup#PushSetting( 'vimspector_adapters', {
  \   'test_adapter': {
  \     'extends': 'netcoredbg',
  \   }
  \ } )
  call vimspector#test#setup#PushSetting( 'vimspector_configurations', {
  \   'test_configuration': {
  \     'adapter': 'test_adapter',
  \     'configuration': {
  \       'request': 'launch',
  \       'default': v:true,
  \       'program': '${workspaceRoot}/bin/Debug/netcoreapp6.0/csharp.dll',
  \       'args': [],
  \       'stopAtEntry': v:false
  \     },
    \   'breakpoints': { 'exception': {
    \     'user-unhandled': '',
    \     'all': ''
    \   } },
  \   },
  \   'ignored_configuration': { 'adapter': 'does_not_exist' }
  \ } )
  call SkipUnsupported()
  let fn='Program.cs'
  lcd ../support/test/csharp
  exe 'edit ' . fn

  call vimspector#SetLineBreakpoint( fn, 31 )
  call vimspector#LaunchWithSettings(
        \ { 'configuration': 'test_configuration' } )
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 31, 7 )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer( fn, 31 )
        \ } )

  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 32, 12 )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer( fn, 32 )
        \ } )

  call vimspector#test#setup#Reset()

  lcd -
  %bwipeout!
endfunction

function! Test_CSharp_Simple_VimDict_Config_TruthyDefault()
  call vimspector#test#setup#PushSetting( 'vimspector_adapters', {
  \   'test_adapter': {
  \     'extends': 'netcoredbg',
  \   }
  \ } )
  call vimspector#test#setup#PushSetting( 'vimspector_configurations', {
  \   'test_configuration': {
  \     'adapter': 'test_adapter',
  \     'configuration': {
  \       'request': 'launch',
  \       'default': 1,
  \       'program': '${workspaceRoot}/bin/Debug/netcoreapp6.0/csharp.dll',
  \       'args': [],
  \       'stopAtEntry': v:false
  \     },
    \   'breakpoints': { 'exception': {
  \       'user-unhandled': '',
  \       'all': ''
  \     } },
  \   },
  \   'ignored_configuration': { 'adapter': 'does_not_exist' }
  \ } )
  call SkipUnsupported()
  let fn='Program.cs'
  lcd ../support/test/csharp
  exe 'edit ' . fn

  call vimspector#SetLineBreakpoint( fn, 31 )
  call vimspector#LaunchWithSettings(
        \ { 'configuration': 'test_configuration' } )
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 31, 7 )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer( fn, 31 )
        \ } )

  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 32, 12 )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer( fn, 32 )
        \ } )

  call vimspector#test#setup#Reset()

  lcd -
  %bwipeout!
endfunction

function! Test_CSharp_Simple_VimDict_Config_Autoselect()
  call vimspector#test#setup#PushSetting( 'vimspector_adapters', {
  \   'test_adapter': {
  \     'extends': 'netcoredbg',
  \   }
  \ } )
  call vimspector#test#setup#PushSetting( 'vimspector_configurations', {
  \   'test_configuration': {
  \     'adapter': 'test_adapter',
  \     'configuration': {
  \       'request': 'launch',
  \       'program': '${workspaceRoot}/bin/Debug/netcoreapp6.0/csharp.dll',
  \       'args': [],
  \       'stopAtEntry': v:false
  \     },
  \     'breakpoints': { 'exception': {
  \       'user-unhandled': '',
  \       'all': ''
  \     } },
  \   },
  \   'ignored_configuration': { 'adapter': 'does_not_exist', 'autoselect': 0 }
  \ } )
  call SkipUnsupported()
  let fn='Program.cs'
  lcd ../support/test/csharp
  exe 'edit ' . fn

  call vimspector#SetLineBreakpoint( fn, 31 )
  call vimspector#LaunchWithSettings(
        \ { 'configuration': 'test_configuration' } )
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 31, 7 )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer( fn, 31 )
        \ } )

  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 32, 12 )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer( fn, 32 )
        \ } )

  call vimspector#test#setup#Reset()

  lcd -
  %bwipeout!
endfunction

function! Test_CSharp_Simple()
  call SkipUnsupported()

  let fn='Program.cs'
  lcd ../support/test/csharp
  exe 'edit ' . fn

  call vimspector#SetLineBreakpoint( fn, 31 )
  call vimspector#LaunchWithSettings( {
        \ 'configuration': 'launch - netcoredbg'
        \ } )
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 31, 7 )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer( fn, 31 )
        \ } )

  call vimspector#StepOver()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 32, 12 )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer( fn, 32 )
        \ } )

  call vimspector#test#setup#Reset()

  lcd -
  %bwipeout!
endfunction


function! Test_Run_To_Cursor()
  call SkipUnsupported()
  let fn='Program.cs'
  lcd ../support/test/csharp
  exe 'edit ' . fn

  call vimspector#SetLineBreakpoint( fn, 31 )
  call vimspector#LaunchWithSettings( {
        \ 'configuration': 'launch - netcoredbg'
        \ } )
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 31, 7 )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer( fn, 31 )
        \ } )

  call cursor( 33, 1 )
  call vimspector#RunToCursor()
  call vimspector#test#signs#AssertCursorIsAtLineInBuffer( fn, 33, 1 )
  call WaitForAssert( {->
        \ vimspector#test#signs#AssertPCIsAtLineInBuffer( fn, 33 )
        \ } )

  call vimspector#test#setup#Reset()
  lcd -
  %bwipeout!
endfunction

