# vimspector - A multi-language debugging system for Vim
# Copyright 2018 Ben Jackson
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import logging
import os
import contextlib
import vim
import json
import subprocess
import shlex
import collections
import re
import typing
import base64

from vimspector.core_utils import memoize
from vimspector.vendor.hexdump import hexdump

LOG_FILE = os.path.expanduser( os.path.join( '~', '.vimspector.log' ) )
NVIM_NAMESPACE = None

_log_handler = logging.FileHandler( LOG_FILE, mode = 'w', encoding = 'utf-8' )

_log_handler.setFormatter(
  logging.Formatter( '%(asctime)s - %(levelname)s - %(filename)s:%(lineno)s - '
                     '%(context)s - %(message)s' ) )


class ContextLogFilter( logging.Filter ):
  context: str

  def __init__( self, context ):
    self.context = str( context )

  def filter( self, record: logging.LogRecord ):
    if self.context is None:
      record.context = 'UNKNOWN'
    else:
      record.context = self.context

    return True


def SetUpLogging( logger, context = None ):
  logger.setLevel( logging.DEBUG )
  if _log_handler not in logger.handlers:
    logger.addHandler( _log_handler )
    logger.addFilter( ContextLogFilter( context ) )


_logger = logging.getLogger( __name__ )
SetUpLogging( _logger )


def BufferNumberForFile( file_name, create = True ):
  with NoAutocommands():
    return int( vim.eval( "bufnr( '{0}', {1} )".format(
      Escape( file_name ),
      int( create ) ) ) )


def BufferForFile( file_name ):
  return vim.buffers[ BufferNumberForFile( file_name ) ]


def BufferExists( file_name ):
  return bool( int ( vim.eval( f"bufexists( '{ Escape( file_name ) }' )" ) ) )


def BufferLineValue( file_name: str, line_num: int ) -> str:
  if not BufferExists( file_name ):
    return ''
  Call( 'bufload', file_name )
  buf = BufferForFile( file_name )
  try:
    return buf[ line_num - 1 ]
  except IndexError:
    return ''


def NewEmptyBuffer():
  bufnr = int( vim.eval( 'bufadd("")' ) )
  Call( 'bufload', bufnr )
  return vim.buffers[ bufnr ]


def AllWindowsForBuffer( buf ):
  for w in vim.current.tabpage.windows:
    if w.buffer == buf:
      yield w


def WindowForBuffer( buf ):
  i = AllWindowsForBuffer( buf )
  return next( i, None )


def OpenFileInCurrentWindow( file_name ):
  buffer_number = BufferNumberForFile( file_name )
  if vim.current.buffer.number == buffer_number:
    return False

  try:
    vim.current.buffer = vim.buffers[ buffer_number ]
  except vim.error as e:
    if 'E325' not in str( e ):
      raise

  return True


COMMAND_HANDLERS = {}


def OnCommandWithLogComplete( session_id, name, exit_code ):
  cb = COMMAND_HANDLERS.get( str( session_id ) + '.' + name )
  if cb:
    cb( exit_code )


def SetUpCommandBuffer( session_id,
                        cmd,
                        name,
                        api_prefix,
                        completion_handler = None ):
  COMMAND_HANDLERS[ str( session_id ) + '.' + name ] = completion_handler

  buf = Call( f'vimspector#internal#{api_prefix}job#StartCommandWithLog',
              session_id,
              cmd,
              name )

  if buf is None:
    raise RuntimeError( "Unable to start job {}: {}".format( cmd, name ) )
  elif int( buf ) <= 0:
    raise RuntimeError( "Unable to get all streams for job {}: {}".format(
      name,
      cmd ) )

  return vim.buffers[ int( buf ) ]


def CleanUpCommand( session_id, name, api_prefix ):
  return vim.eval(
    'vimspector#internal#{}job#CleanUpCommand( {}, "{}" )'.format(
      api_prefix,
      session_id,
      name ) )


def CleanUpHiddenBuffer( buf ):
  if not buf.valid:
    return

  try:
    vim.command( 'bdelete! {}'.format( buf.number ) )
  except vim.error as e:
    # FIXME: For now just ignore the "no buffers were deleted" error
    if 'E516' not in str( e ):
      raise


def SetUpScratchBuffer( buf, name ):
  SetUpHiddenBuffer( buf, name )
  buf.options[ 'bufhidden' ] = 'wipe'


def SetUpHiddenBuffer( buf, name ):
  buf.options[ 'buftype' ] = 'nofile'
  buf.options[ 'swapfile' ] = False
  buf.options[ 'modifiable' ] = False
  buf.options[ 'modified' ] = False
  buf.options[ 'readonly' ] = True
  buf.options[ 'buflisted' ] = False
  buf.options[ 'bufhidden' ] = 'hide'
  buf.name = name


def SetUpPromptBuffer( buf, name, prompt, callback, omnifunc ):
  # This feature is _super_ new, so only enable when available
  if not Exists( '*prompt_setprompt' ):
    return SetUpHiddenBuffer( buf, name )

  buf.options[ 'buftype' ] = 'prompt'
  buf.options[ 'swapfile' ] = False
  buf.options[ 'modifiable' ] = True
  buf.options[ 'modified' ] = False
  buf.options[ 'readonly' ] = False
  buf.options[ 'buflisted' ] = False
  buf.options[ 'bufhidden' ] = 'hide'
  buf.options[ 'textwidth' ] = 0
  buf.options[ 'omnifunc' ] = omnifunc
  buf.name = name

  vim.eval( "prompt_setprompt( {0}, '{1}' )".format( buf.number,
                                                     Escape( prompt ) ) )
  vim.eval( "prompt_setcallback( {0}, function( '{1}' ) )".format(
    buf.number,
    Escape( callback ) ) )

  # This serves a few purposes, mainly to ensure that completion systems have
  # something to work with. In particular it makes YCM use its identifier engine
  # and you can config ycm to trigger semantic (annoyingly, synchronously) using
  # some let g:ycm_auto_trggier
  Call( 'setbufvar', buf.number, '&filetype', 'VimspectorPrompt' )


def SetUpUIWindow( win ):
  win.options[ 'wrap' ] = False
  win.options[ 'number' ] = False
  win.options[ 'relativenumber' ] = False
  win.options[ 'signcolumn' ] = 'no'
  win.options[ 'spell' ] = False
  win.options[ 'list' ] = False


@contextlib.contextmanager
def ModifiableScratchBuffer( buf ):
  if buf.options[ 'modifiable' ]:
    yield
    return

  buf.options[ 'modifiable' ] = True
  buf.options[ 'readonly' ] = False
  try:
    yield
  finally:
    buf.options[ 'modifiable' ] = False
    buf.options[ 'readonly' ] = True


@contextlib.contextmanager
def NoAutocommands():
  with TemporaryVimOption( 'eventignore', 'all' ):
    yield


@contextlib.contextmanager
def RestoreCursorPosition():
  current_pos = vim.current.window.cursor
  try:
    yield
  finally:
    vim.current.window.cursor = (
      min( current_pos[ 0 ], len( vim.current.buffer ) ),
      current_pos[ 1 ] )


@contextlib.contextmanager
def RestoreCurrentWindow():
  old_tabpage = vim.current.tabpage
  old_window = vim.current.window
  try:
    yield
  finally:
    if old_tabpage.valid and old_window.valid:
      with NoAutocommands():
        vim.current.tabpage = old_tabpage
        vim.current.window = old_window


@contextlib.contextmanager
def RestoreCurrentBuffer( window ):
  old_buffer = window.buffer
  try:
    yield
  finally:
    if window.valid:
      Call( 'win_execute', WindowID( window ), f'bu { old_buffer.number }' )


@contextlib.contextmanager
def AnyWindowForBuffer( buf ):
  # Only checks the current tab page, which is what we want
  current_win = WindowForBuffer( buf )
  if current_win is not None:
    with LetCurrentWindow( current_win ):
      yield
  else:
    with LetCurrentBuffer( buf ):
      yield


@contextlib.contextmanager
def LetCurrentTabpage( tabpage ):
  with RestoreCurrentWindow():
    with NoAutocommands():
      vim.current.tabpage = tabpage
    yield


@contextlib.contextmanager
def LetCurrentWindow( window ):
  with RestoreCurrentWindow():
    with NoAutocommands():
      JumpToWindow( window )
    yield


@contextlib.contextmanager
def LetCurrentBuffer( buf ):
  with RestoreCursorPosition():
    with RestoreCurrentBuffer( vim.current.window ):
      with NoAutocommands():
        vim.current.buffer = buf
      yield


def JumpToWindow( window ):
  vim.current.tabpage = window.tabpage
  vim.current.window = window


@contextlib.contextmanager
def TemporaryVimOptions( opts ):
  old_value = {}
  try:
    for option, value in opts.items():
      old_value[ option ] = vim.options[ option ]
      vim.options[ option ] = value

    yield
  finally:
    for option, value in old_value.items():
      vim.options[ option ] = value


@contextlib.contextmanager
def TemporaryVimOption( opt, value ):
  old_value = vim.options[ opt ]
  vim.options[ opt ] = value
  try:
    yield
  finally:
    vim.options[ opt ] = old_value


def DirectoryOfCurrentFile():
  return os.path.dirname( NormalizePath( vim.current.buffer.name ) )


def PathToConfigFile( file_name, from_directory = None ):
  if not from_directory:
    p = os.getcwd()
  else:
    p = NormalizePath( os.path.realpath( from_directory ) )

  while True:
    candidate = os.path.join( p, file_name )
    if os.path.exists( candidate ):
      return candidate

    parent = os.path.dirname( p )
    if parent == p:
      return None
    p = parent


def Escape( msg ):
  return msg.replace( "'", "''" )


def UserMessage( msg, persist=False, error=False ):
  if persist:
    _logger.warning( 'User Msg: ' + msg )
  else:
    _logger.info( 'User Msg: ' + msg )

  cmd = 'echom' if persist else 'echo'
  vim.command( 'redraw' )
  try:
    if error:
      vim.command( "echohl WarningMsg" )
    for line in msg.split( '\n' ):
      vim.command( "{0} '{1}'".format( cmd, Escape( line ) ) )
  finally:
    vim.command( 'echohl None' ) if error else None
  vim.command( 'redraw' )


@contextlib.contextmanager
def InputSave():
  if vim.vars.get( 'vimspector_batch_mode', False ):
    yield
    return

  vim.eval( 'inputsave()' )
  try:
    yield
  finally:
    vim.eval( 'inputrestore()' )


def SelectFromList( prompt, options, ret='label' ):
  with InputSave():
    display_options = [ prompt ]
    display_options.extend( [ '{0}: {1}'.format( i + 1, v )
                              for i, v in enumerate( options ) ] )
    try:
      selection = int( vim.eval(
        'inputlist( ' + json.dumps( display_options ) + ' )' ) ) - 1
      if selection < 0 or selection >= len( options ):
        return None
      if ret == 'index':
        return selection
      else:
        return options[ selection ]
    except ( KeyboardInterrupt, vim.error ):
      return None


def AskForInput( prompt, default_value = None, completion = None ):
  if default_value is None:
    default_value = ''

  args = [ prompt, default_value ]

  if completion is not None:
    if completion == 'expr':
      args.append( 'custom,vimspector#CompleteExpr' )
    else:
      args.append( completion )

  with InputSave():
    try:
      return Call( 'input', *args )
    except ( KeyboardInterrupt, vim.error ):
      return None


CONFIRM = {}
CONFIRM_ID = 0


def ConfirmCallback( confirm_id, result ):
  try:
    handler = CONFIRM.pop( confirm_id )
  except KeyError:
    UserMessage( f"Internal error: unexpected callback id { confirm_id }",
                 persist = True,
                 error = True )
    return

  handler( result )


def Confirm( api_prefix,
             prompt,
             handler,
             default_value = 2,
             options: list = None,
             keys: list = None ):
  # TODO: Implement a queue here? If calling code calls Confirm (async) multiple
  # times, we... well what happens?!
  if not options:
    options = [ '(Y)es', '(N)o' ]
  if not keys:
    keys = [ 'y', 'n' ]

  global CONFIRM_ID
  CONFIRM_ID += 1
  CONFIRM[ CONFIRM_ID ] = handler
  Call( f'vimspector#internal#{ api_prefix }popup#Confirm',
        CONFIRM_ID,
        prompt,
        options,
        default_value,
        keys )


def AppendToBuffer( buf,
                    line_or_lines,
                    modified=False,
                    hl = None ):
  line = 1
  try:
    # After clearing the buffer (using buf[:] = None) there is always a single
    # empty line in the buffer object and no "is empty" method.
    if len( buf ) > 1 or buf[ 0 ]:
      line = len( buf ) + 1
      buf.append( line_or_lines )

    elif isinstance( line_or_lines, str ):
      line = 1
      buf[ -1 ] = line_or_lines
    else:
      line = 1
      buf[ : ] = line_or_lines
  except Exception:
    # There seem to be a lot of Vim bugs that lead to E315, whose help says that
    # this is an internal error. Ignore the error, but write a trace to the log.
    _logger.exception(
      'Internal error while updating buffer %s (%s)', buf.name, buf.number )
  finally:
    if not modified:
      buf.options[ 'modified' ] = False

  if len( buf ) > 0:
    HighlightTextSection( buf,
                          hl = hl,
                          start_line = line,
                          start_col = 1,
                          end_line = len( buf ),
                          end_col = len( buf[ -1 ] ) )

  # Return the first Vim line number (1-based) that we just set.
  return line


def ClearBuffer( buf, modified = False ):
  ClearTextPropertiesForBuffer( buf )
  buf[ : ] = None
  if not modified:
    buf.options[ 'modified' ] = False


def SetBufferContents( buf, lines, modified=False ):
  try:
    # FIXME: Really any iteratble list-like type would work here (iterable isn't
    # enough because strings are iterable)
    if not isinstance( lines, list ):
      lines = lines.splitlines()

    buf[ : ] = lines
  finally:
    buf.options[ 'modified' ] = modified


def IsCurrent( window, buf ):
  return vim.current.window == window and vim.current.window.buffer == buf


def ExpandReferencesInObject( obj, mapping, calculus, user_choices ):
  if isinstance( obj, dict ):
    ExpandReferencesInDict( obj, mapping, calculus, user_choices )
  elif isinstance( obj, list ):
    j_offset = 0
    obj_copy = list( obj )

    for i, _ in enumerate( obj_copy ):
      j = i + j_offset
      if ( isinstance( obj_copy[ i ], str ) and
           len( obj_copy[ i ] ) > 2 and
           obj_copy[ i ][ 0:2 ] == '*$' ):
        # *${something} - expand list in place
        value = ExpandReferencesInString( obj_copy[ i ][ 1: ],
                                          mapping,
                                          calculus,
                                          user_choices )
        obj.pop( j )
        j_offset -= 1
        for opt_index, opt in enumerate( shlex.split( value ) ):
          obj.insert( j + opt_index, opt )
          j_offset += 1
      else:
        obj[ j ] = ExpandReferencesInObject( obj_copy[ i ],
                                             mapping,
                                             calculus,
                                             user_choices )
  elif isinstance( obj, str ):
    obj = ExpandReferencesInString( obj, mapping, calculus, user_choices )

  return obj


# Based on the python standard library string.Template().substitute, enhanced to
# add ${name:default} parsing, and to remove the unnecessary generality.
VAR_MATCH = re.compile(
  r"""
    \$(?:                               # A dollar, followed by...
      (?P<escaped>\$)                |  # Another dollar = escaped
      (?P<named>[_a-z][_a-z0-9]*)    |  # or An identifier - named param
      {(?P<braced>[_a-z][_a-z0-9]*)} |  # or An {identifier} - braced param
      {(?P<braceddefault>               # or An {id:default} - default param, as
        (?P<defname>[_a-z][_a-z0-9]*)   #   an ID
        :                               #   then a colon
        (?P<default>(?:\\}|[^}])*)      #   then anything up to }, or a \}
      )}                             |  #   then a }
      (?P<invalid>)                     # or Something else - invalid
    )
  """,
  re.IGNORECASE | re.VERBOSE )


class MissingSubstitution( Exception ):
  def __init__( self, name, default_value = None ):
    self.name = name
    self.default_value = default_value


def _Substitute( template, mapping ):
  def convert( mo ):
    # Check the most common path first.
    named = mo.group( 'named' ) or mo.group( 'braced' )
    if named is not None:
      if named not in mapping:
        raise MissingSubstitution( named )
      return str( mapping[ named ] )

    if mo.group( 'escaped' ) is not None:
      return '$'

    if mo.group( 'braceddefault' ) is not None:
      named = mo.group( 'defname' )
      if named not in mapping:
        raise MissingSubstitution(
          named,
          mo.group( 'default' ).replace( '\\}', '}' ) )
      return str( mapping[ named ] )

    if mo.group( 'invalid' ) is not None:
      raise ValueError( f"Invalid placeholder in string { template }" )

    raise ValueError( 'Unrecognized named group in pattern', VAR_MATCH )

  return VAR_MATCH.sub( convert, template )


def ExpandReferencesInString( orig_s,
                              mapping,
                              calculus,
                              user_choices ):
  s = os.path.expanduser( orig_s )
  s = os.path.expandvars( s )

  # Parse any variables passed in in mapping, and ask for any that weren't,
  # storing the result in mapping
  bug_catcher = 0
  while bug_catcher < 100:
    ++bug_catcher

    try:
      s = _Substitute( s, mapping )
      break
    except MissingSubstitution as e:
      key = e.name

      if key in calculus:
        mapping[ key ] = calculus[ key ]()
      else:
        default_value = user_choices.get( key )
        # Allow _one_ level of additional substitution. This allows a very real
        # use case of "program": ${program:${file\\}}
        if default_value is None and e.default_value is not None:
          try:
            default_value = _Substitute( e.default_value, mapping )
          except MissingSubstitution as e2:
            if e2.name in calculus:
              default_value = calculus[ e2.name ]()
            else:
              default_value = e.default_value

        mapping[ key ] = AskForInput( 'Enter value for {}: '.format( key ),
                                      default_value,
                                      'file' )

        if mapping[ key ] is None:
          raise KeyboardInterrupt

        user_choices[ key ] = mapping[ key ]
        _logger.debug( "Value for %s not set in %s (from %s): set to %s",
                       key,
                       s,
                       orig_s,
                       mapping[ key ] )
    except ValueError as e:
      UserMessage( 'Invalid $ in string {}: {}'.format( s, e ),
                   persist = True )
      break

  return s


def CoerceType( mapping: typing.Dict[ str, typing.Any ], key: str ):
  DICT_TYPES = {
    'json': json.loads,
    's': str
  }

  parts = key.split( '#' )
  if len( parts ) > 1 and parts[ -1 ] in DICT_TYPES.keys():
    value = mapping.pop( key )

    new_type = parts[ -1 ]
    key = '#'.join( parts[ 0 : -1 ] )

    mapping[ key ] = DICT_TYPES[ new_type ]( value )


# TODO: Should we just run the substitution on the whole JSON string instead?
# That woul dallow expansion in bool and number values, such as ports etc. ?
def ExpandReferencesInDict( obj, mapping, calculus, user_choices ):
  for k in list( obj.keys() ):
    obj[ k ] = ExpandReferencesInObject( obj[ k ],
                                         mapping,
                                         calculus,
                                         user_choices )
    CoerceType( obj, k )


def ParseVariables( variables_list,
                    mapping,
                    calculus,
                    user_choices ):
  new_variables = {}
  new_mapping = mapping.copy()

  if not isinstance( variables_list, list ):
    variables_list = [ variables_list ]

  variables: typing.Dict[ str, typing.Any ]
  for variables in variables_list:
    new_mapping.update( new_variables )
    for n, v in list( variables.items() ):
      if isinstance( v, dict ):
        if 'shell' in v:
          new_v = v.copy()
          # Bit of a hack. Allows environment variables to be used.
          ExpandReferencesInDict( new_v,
                                  new_mapping,
                                  calculus,
                                  user_choices )

          env = os.environ.copy()
          env.update( new_v.get( 'env' ) or {} )
          cmd = new_v[ 'shell' ]
          if not isinstance( cmd, list ):
            cmd = shlex.split( cmd )

          new_variables[ n ] = subprocess.check_output(
            cmd,
            cwd = new_v.get( 'cwd' ) or os.getcwd(),
            env = env ).decode( 'utf-8' ).strip()

          _logger.debug( "Set new_variables[ %s ] to '%s' from %s from %s",
                         n,
                         new_variables[ n ],
                         new_v,
                         v )
        else:
          raise ValueError(
            "Unsupported variable defn {}: Missing 'shell'".format( n ) )
      else:
        new_variables[ n ] = ExpandReferencesInObject( v,
                                                       new_mapping,
                                                       calculus,
                                                       user_choices )

      CoerceType( new_variables, n )

  return new_variables


def CreateTooltip( display: list, is_hover = False ):
  created_win_id = int( vim.eval(
    "vimspector#internal#balloon#CreateTooltip({}, {})".format(
      int( is_hover ), json.dumps( display )
    )
  ) )

  return created_win_id


def GetBufferFilepath( buf ):
  if not buf.name:
    return ''

  return os.path.normpath( buf.name )


def ToUnicode( b ):
  if isinstance( b, bytes ):
    return b.decode( 'utf-8' )
  return b


# Call a vimscript function with supplied arguments.
def Call( vimscript_function, *args ):
  call = vimscript_function + '('
  for index, arg in enumerate( args ):
    if index > 0:
      call += ', '

    arg_name = 'vimspector_internal_arg_{}'.format( index )
    vim.vars[ arg_name ] = arg
    call += 'g:' + arg_name

  call += ')'
  return vim.eval( call )


@memoize
def Exists( expr ):
  return int( vim.eval( f'exists( "{ expr }" )' ) )


def SetSyntax( current_syntax: str, syntax: str, *buffers ):
  if not syntax:
    syntax = ''

  if current_syntax == syntax:
    return syntax

  # We use set syn= because just setting vim.Buffer.options[ 'syntax' ]
  # doesn't actually trigger the Syntax autocommand, and i'm not sure that
  # 'doautocmd Syntax' is the right solution or not
  for buf in buffers:
    Call( 'setbufvar', buf.number, '&syntax', syntax )

  return syntax


def GetBufferFiletypes( buf ):
  ft = ToUnicode( vim.eval( f"getbufvar( {buf.number}, '&ft' )" ) )
  return ft.split( '.' )


def GetVisualSelection( bufnr ):
  start_line, start_col = vim.current.buffer.mark( "<" )
  end_line, end_col = vim.current.buffer.mark( ">" )


  # lines are 1 based, but columns are 0 based
  # don't ask me why...
  start_line -= 1
  end_line -= 1

  lines = vim.buffers[ bufnr ][ start_line : end_line + 1 ]
  # Do end first, in case it's on the same line as start (as doing start first
  # would change the offset)
  lines[ -1 ] = lines[ -1 ][ : end_col + 1 ]
  lines[ 0 ] = lines[ 0 ][ start_col : ]

  _logger.debug( f'Visual selection: { lines } from '
                 f'{ start_line }/{ start_col } -> { end_line }/{ end_col }' )

  return lines


def DisplaySplash( api_prefix: str, splash, text: typing.Union[ str, list ] ):
  if splash:
    return Call( f'vimspector#internal#{api_prefix}popup#UpdateSplash',
                 splash,
                 text )
  else:
    return Call( f'vimspector#internal#{api_prefix}popup#DisplaySplash',
                 text )


def HideSplash( api_prefix, splash ):
  if splash:
    return Call( f'vimspector#internal#{api_prefix}popup#HideSplash', splash )

  return None


def GetVimValue( vim_dict, name, default=None ):

  # FIXME: use 'encoding' ?
  try:
    value = vim_dict[ name ]
  except ( KeyError, vim.error ):
    return default

  if isinstance( value, bytes ):
    return value.decode( 'utf-8' )
  return value


def GetVimList( vim_dict, name, default=None ):
  try:
    value = vim_dict[ name ]
  except ( KeyError, vim.error ):
    return default

  if not isinstance( value, collections.abc.Iterable ):
    raise ValueError( f"Expected a list for { name }, but found "
                      f"{ type( value ) }" )

  return [ i.decode( 'utf-8' ) if isinstance( i, bytes ) else i for i in value ]


def GetVimspectorBase():
  return GetVimValue( vim.vars,
                     'vimspector_base_dir',
                      NormalizePath(
                        os.path.join( os.path.dirname( __file__ ),
                                      '..',
                                      '..' ) ) )


def GetUnusedLocalPort():
  import socket
  sock = socket.socket()
  # This tells the OS to give us any free port in the range [1024 - 65535]
  sock.bind( ( '', 0 ) )
  port = sock.getsockname()[ 1 ]
  sock.close()
  return port


def WindowID( window, tab=None ):
  if tab is None:
    tab = window.tabpage
  return int( Call( 'win_getid', window.number, tab.number ) )


def GetWindowInfo( window ):
  return Call( 'getwininfo', WindowID( window ) )[ 0 ]


NVIM_WINBAR = {}


def SetWinBarOption( *args ):
  window = vim.current.window
  win_id = WindowID( window )

  NVIM_WINBAR[ win_id ] = []
  winbar = []
  for idx, button in enumerate( args ):
    button, action = button
    winbar.append( '%#ToolbarButton#'
                    f'%{idx}@vimspector#internal#neowinbar#Do@ { button } %X'
                    '%*' )
    NVIM_WINBAR[ win_id ].append( action )

  window.options[ 'winbar' ] = '  '.join( winbar )
  return True


def DoWinBarAction( win_id, idx ):
  action = NVIM_WINBAR[ win_id ][ idx ]
  vim.command( f':call { action }' )


def SetWinBar( *args ):
  if VimIsNeovim():
    return SetWinBarOption( *args )

  vim.command( 'silent! nunmenu WinBar' )
  for idx, button in enumerate( args ):
    button, action = button
    button = button.replace( ' ', '\\ ' )
    vim.command( f'nnoremenu <silent> 1.{idx + 1} '
                 f'WinBar.{ button } '
                 f':call {action}<CR>' )


def UseWinBar():
  from vimspector import settings
  return settings.Bool( 'enable_winbar' ) and VimHasMouseSupport()


@memoize
def VimIsNeovim():
  return int( Call( 'has', 'nvim' ) )


def VimHasMouseSupport():
  mouse = ToUnicode( vim.options[ 'mouse' ] )
  return 'a' in mouse or 'n' in mouse


class VisiblePosition:
  UNCHANGED = None
  TOP = 'zt'
  BOTTOM = 'zb'
  MIDDLE = 'zz'


# Jump to a specific 1-based line/column
def SetCursorPosInWindow( window,
                          line,
                          column = 1,
                          make_visible = VisiblePosition.UNCHANGED ):
  # simplify the interface and make column 1 based, same as line
  column = max( 1, column )
  # ofc column is actually 0 based in vim
  window.cursor = ( line, column - 1 )

  if make_visible:
    Call( 'win_execute', WindowID( window ), f'normal! { make_visible }' )


def NormalizePath( filepath ):
  absolute_path = os.path.abspath( filepath )
  return absolute_path if os.path.isfile( absolute_path ) else filepath


def UpdateSessionWindows( d ):
  # neovim madness need to re-assign the dict to trigger rpc call
  # see https://github.com/neovim/pynvim/issues/261
  session_wins = vim.vars[ 'vimspector_session_windows' ]
  session_wins.update( d )
  vim.vars[ 'vimspector_session_windows' ] = session_wins


def SetSessionWindows( d ):
  vim.vars[ 'vimspector_session_windows' ] = d


class Subject( object ):
  def __init__( self, id, emitter ):
    self.__id = id
    self.__emitter = emitter

  def __str__( self ):
    return str( self.__id )

  def unsubscribe( self ):
    self.__emitter.unsubscribe( self )

  def emit( self ):
    self.__emitter.emit()


class EventEmitter( object ):
  def __init__( self ):
    super().__init__()
    self.__next_id = 0
    self.__callbacks = {}

  def subscribe( self, callback ):
    if not callback:
      return None

    self.__next_id += 1
    subscription = Subject( self.__next_id, self )
    self.__callbacks[ subscription ] = callback

    return subscription

  def unsubscribe( self, subscription ):
    if not subscription:
      return

    del self.__callbacks[ subscription ]

  def emit( self ):
    for _, callback in self.__callbacks.items():
      if callback:
        callback()

  def unsubscribe_all( self ):
    self.__callbacks = {}


def Base64ToHexDump( data, base_addr ):
  data = base64.b64decode( data )
  return list( hexdump( data, result = 'generator', base_address = base_addr ) )


def ParseAddress( addr: str ):
  if not addr:
    return 0

  base = 10
  if addr.startswith( '0x' ):
    base = 16

  try:
    return int( addr, base )
  except ValueError:
    return 0


def Hex( val: int ):
  # TODO: is 16 always the right number ? what if your system is 32 bit
  try:
    return f'0x{val:0>16x}'
  except ValueError:
    return f'0x{0:0>16x}'


def BufferNameForSession( name, session_id ):
  return f'{name}[{session_id}]'


def ClearTextPropertiesForBuffer( buf ):
  if VimIsNeovim() and NVIM_NAMESPACE is not None:
    Call( 'nvim_buf_clear_namespace', buf.number, NVIM_NAMESPACE, 0, -1 )
    return

  if Exists( '*prop_clear' ):
    Call( 'prop_clear', 1, len( buf ), { 'bufnr': buf.number } )


def HighlightTextSection( buf,
                          hl,
                          start_line,
                          start_col,
                          end_line,
                          end_col ):

  if not hl:
    return

  if Exists( '*prop_add' ):
    text_property_type = f'vimspector-p-{hl}'
    if int( vim.eval( f'empty( prop_type_get( "{text_property_type}" ) )' ) ):
      Call( 'prop_type_add', text_property_type, {
        'highlight': hl,
        'start_incl': 0,
        'end_incl': 0,
        'priority': 10,
        'combine': 1
      } )

    Call( 'prop_add', start_line, start_col, {
      'bufnr': buf.number,
      'type': text_property_type,
      'end_lnum': end_line,
      'end_col': end_col + 1
    } )
  elif VimIsNeovim():
    global NVIM_NAMESPACE
    if NVIM_NAMESPACE is None:
      NVIM_NAMESPACE = int( Call( 'nvim_create_namespace', 'vimspector' ) )

    Call( 'nvim_buf_set_extmark',
          buf.number,
          NVIM_NAMESPACE,
          start_line - 1,
          start_col - 1,
          {
            'hl_group': hl,
            'end_row': ( end_line - 1 ),
            'end_col': ( end_col - 1 ) + 1,
            'priority': 10,
          } )
