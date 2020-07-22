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
import string
import functools
import subprocess
import shlex



LOG_FILE = os.path.expanduser( os.path.join( '~', '.vimspector.log' ) )

_log_handler = logging.FileHandler( LOG_FILE, mode = 'w' )

_log_handler.setFormatter(
    logging.Formatter( '%(asctime)s - %(levelname)s - %(message)s' ) )


def SetUpLogging( logger ):
  logger.setLevel( logging.DEBUG )
  if _log_handler not in logger.handlers:
    logger.addHandler( _log_handler )


_logger = logging.getLogger( __name__ )
SetUpLogging( _logger )


def BufferNumberForFile( file_name ):
  return int( vim.eval( "bufnr( '{0}', 1 )".format( Escape( file_name ) ) ) )


def BufferForFile( file_name ):
  return vim.buffers[ BufferNumberForFile( file_name ) ]


def NewEmptyBuffer():
  bufnr = int( vim.eval( 'bufadd("")' ) )
  Call( 'bufload', bufnr )
  return vim.buffers[ bufnr ]


def WindowForBuffer( buf ):
  for w in vim.current.tabpage.windows:
    if w.buffer == buf:
      return w

  return None


def OpenFileInCurrentWindow( file_name ):
  buffer_number = BufferNumberForFile( file_name )
  try:
    vim.current.buffer = vim.buffers[ buffer_number ]
  except vim.error as e:
    if 'E325' not in str( e ):
      raise

  return vim.buffers[ buffer_number ]


COMMAND_HANDLERS = {}


def OnCommandWithLogComplete( name, exit_code ):
  cb = COMMAND_HANDLERS.get( name )
  if cb:
    cb( exit_code )
  else:
    UserMessage( f'Job complete: { name } (exit status: { exit_code })' )


def SetUpCommandBuffer( cmd, name, api_prefix, completion_handler = None ):
  COMMAND_HANDLERS[ name ] = completion_handler

  buf = Call( f'vimspector#internal#{api_prefix}job#StartCommandWithLog',
              cmd,
              name )

  if buf is None:
    raise RuntimeError( "Unable to start job {}: {}".format( cmd, name ) )
  elif int( buf ) <= 0:
    raise RuntimeError( "Unable to get all streams for job {}: {}".format(
      name,
      cmd ) )

  return vim.buffers[ int( buf ) ]


def CleanUpCommand( name, api_prefix ):
  return vim.eval( 'vimspector#internal#{}job#CleanUpCommand( "{}" )'.format(
    api_prefix,
    name ) )


def CleanUpHiddenBuffer( buf ):
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


def SetUpPromptBuffer( buf, name, prompt, callback ):
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
  buf.name = name

  vim.eval( "prompt_setprompt( {0}, '{1}' )".format( buf.number,
                                                     Escape( prompt ) ) )
  vim.eval( "prompt_setcallback( {0}, function( '{1}' ) )".format(
    buf.number,
    Escape( callback ) ) )


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
  # TODO: Don't trigger autocommands when shifting windows
  old_tabpage = vim.current.tabpage
  old_window = vim.current.window
  try:
    yield
  finally:
    if old_tabpage.valid and old_window.valid:
      vim.current.tabpage = old_tabpage
      vim.current.window = old_window


@contextlib.contextmanager
def RestoreCurrentBuffer( window ):
  old_buffer = window.buffer
  try:
    yield
  finally:
    if window.valid:
      with RestoreCurrentWindow():
        vim.current.window = window
        vim.current.buffer = old_buffer


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
    vim.current.tabpage = tabpage
    yield


@contextlib.contextmanager
def LetCurrentWindow( window ):
  with RestoreCurrentWindow():
    JumpToWindow( window )
    yield


@contextlib.contextmanager
def LetCurrentBuffer( buf ):
  with RestoreCursorPosition():
    with RestoreCurrentBuffer( vim.current.window ):
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


def PathToConfigFile( file_name, from_directory = None ):
  if not from_directory:
    p = os.getcwd()
  else:
    p = os.path.abspath( os.path.realpath( from_directory ) )

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
  vim.eval( 'inputsave()' )
  try:
    yield
  finally:
    vim.eval( 'inputrestore()' )


def SelectFromList( prompt, options ):
  with InputSave():
    display_options = [ prompt ]
    display_options.extend( [ '{0}: {1}'.format( i + 1, v )
                              for i, v in enumerate( options ) ] )
    try:
      selection = int( vim.eval(
        'inputlist( ' + json.dumps( display_options ) + ' )' ) ) - 1
      if selection < 0 or selection >= len( options ):
        return None
      return options[ selection ]
    except KeyboardInterrupt:
      return None


def AskForInput( prompt, default_value = None ):
  if default_value is None:
    default_option = ''
  else:
    default_option = ", '{}'".format( Escape( default_value ) )

  with InputSave():
    try:
      return vim.eval( "input( '{}' {} )".format( Escape( prompt ),
                                                  default_option ) )
    except KeyboardInterrupt:
      return None


def AppendToBuffer( buf, line_or_lines, modified=False ):
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

  # Return the first Vim line number (1-based) that we just set.
  return line



def ClearBuffer( buf ):
  buf[ : ] = None


def SetBufferContents( buf, lines, modified=False ):
  try:
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
      s = string.Template( s ).substitute( mapping )
      break
    except KeyError as e:
      # HACK: This is seemingly the only way to get the key. str( e ) returns
      # the key surrounded by '' for unknowable reasons.
      key = e.args[ 0 ]

      if key in calculus:
        mapping[ key ] = calculus[ key ]()
      else:
        default_value = user_choices.get( key, None )
        mapping[ key ] = AskForInput( 'Enter value for {}: '.format( key ),
                                      default_value )

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


# TODO: Should we just run the substitution on the whole JSON string instead?
# That woul dallow expansion in bool and number values, such as ports etc. ?
def ExpandReferencesInDict( obj, mapping, calculus, user_choices ):
  for k in obj.keys():
    obj[ k ] = ExpandReferencesInObject( obj[ k ],
                                         mapping,
                                         calculus,
                                         user_choices )


def ParseVariables( variables_list,
                    mapping,
                    calculus,
                    user_choices ):
  new_variables = {}
  new_mapping = mapping.copy()

  if not isinstance( variables_list, list ):
    variables_list = [ variables_list ]

  for variables in variables_list:
    new_mapping.update( new_variables )
    for n, v in variables.items():
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
                                                       mapping,
                                                       calculus,
                                                       user_choices )

  return new_variables


def DisplayBaloon( is_term, display ):
  if not is_term:
    display = '\n'.join( display )

  vim.eval( "balloon_show( {0} )".format(
    json.dumps( display ) ) )


def GetBufferFilepath( buf ):
  if not buf.name:
    return ''

  return os.path.normpath( buf.name )


def ToUnicode( b ):
  if isinstance( b, bytes ):
    return b.decode( 'utf-8' )
  return b


# Call a vimscript function with suplied arguments.
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


def SignDefined( name ):
  if Exists( "*sign_getdefined" ):
    return int( vim.eval( f"len( sign_getdefined( '{ Escape( name ) }' ) )" ) )

  return False


MEMO = {}


def memoize( func ):
  global MEMO

  @functools.wraps( func )
  def wrapper( *args, **kwargs ):
    dct = MEMO.setdefault( func, {} )
    key = ( args, frozenset( kwargs.items() ) )
    try:
      return dct[ key ]
    except KeyError:
      result = func( *args, **kwargs )
      dct[ key ] = result
      return result

  return wrapper


@memoize
def Exists( expr ):
  return int( vim.eval( f'exists( "{ expr }" )' ) )


def SetSyntax( current_syntax, syntax, *args ):
  if not syntax:
    syntax = ''

  if current_syntax == syntax:
    return

  # We use set syn= because just setting vim.Buffer.options[ 'syntax' ]
  # doesn't actually trigger the Syntax autocommand, and i'm not sure that
  # 'doautocmd Syntax' is the right solution or not
  for buf in args:
    Call( 'setbufvar', buf.number, '&syntax', syntax )

  return syntax


def GetBufferFiletypes( buf ):
  ft = ToUnicode( vim.eval( f"getbufvar( {buf.number}, '&ft' )" ) )
  return ft.split( '.' )


def DisplaySplash( api_prefix, splash, text ):
  if splash:
    return Call( f'vimspector#internal#{api_prefix}popup#UpdateSplash',
                 splash,
                 text )
  else:
    return Call( f'vimspector#internal#{api_prefix}popup#DisplaySplash',
                 text )


def HideSplash( api_prefix, splash ):
  if splash:
    Call( f'vimspector#internal#{api_prefix}popup#HideSplash', splash )

  return None


def GetVimString( vim_dict, name, default=None ):

  # FIXME: use 'encoding' ?
  try:
    value = vim_dict[ name ]
  except KeyError:
    return default

  if isinstance( value, bytes ):
    return value.decode( 'utf-8' )
  return value


def GetVimspectorBase():
  return GetVimString( vim.vars,
                       'vimspector_base_dir',
                       os.path.abspath(
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
