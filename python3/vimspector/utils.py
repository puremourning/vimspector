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

_log_handler = logging.FileHandler( os.path.expanduser( '~/.vimspector.log' ),
                                    mode = 'w' )
_log_handler.setFormatter(
    logging.Formatter( '%(asctime)s - %(levelname)s - %(message)s' ) )


def SetUpLogging( logger ):
  logger.setLevel( logging.DEBUG )
  if _log_handler not in logger.handlers:
    logger.addHandler( _log_handler )


def BufferNumberForFile( file_name ):
  return int( vim.eval( 'bufnr( "{0}", 1 )'.format( file_name ) ) )


def BufferForFile( file_name ):
  return vim.buffers[ BufferNumberForFile( file_name ) ]


def OpenFileInCurrentWindow( file_name ):
  buffer_number = BufferNumberForFile( file_name )
  try:
    vim.command( 'bu {0}'.format( buffer_number ) )
  except vim.error as e:
    if 'E325' not in str( e ):
      raise

  return vim.buffers[ buffer_number ]


def SetUpCommandBuffer( cmd, name ):
  bufs = vim.eval(
    'vimspector#internal#job#StartCommandWithLog( {}, "{}" )'.format(
      json.dumps( cmd ),
      name ) )

  if bufs is None:
    raise RuntimeError( "Unable to start job {}: {}".format( cmd, name ) )
  elif not all( b > 0 for b in bufs ):
    raise RuntimeError( "Unable to get all streams for job {}: {}".format(
      name,
      cmd ) )

  UserMessage( 'Bufs: {}'.format( [ int( b ) for b in bufs ] ), persist = True )

  return [ vim.buffers[ b ] for b in bufs ]


def CleanUpCommand( name ):
  return vim.eval( 'vimspector#internal#job#CleanUpCommand( "{}" )'.format(
    name ) )


def SetUpScratchBuffer( buf, name ):
  buf.options[ 'buftype' ] = 'nofile'
  buf.options[ 'swapfile' ] = False
  buf.options[ 'modifiable' ] = False
  buf.options[ 'modified' ] = False
  buf.options[ 'readonly' ] = True
  buf.options[ 'buflisted' ] = False
  buf.options[ 'bufhidden' ] = 'wipe'
  buf.name = name


def SetUpHiddenBuffer( buf, name ):
  buf.options[ 'buftype' ] = 'nofile'
  buf.options[ 'swapfile' ] = False
  buf.options[ 'modifiable' ] = False
  buf.options[ 'modified' ] = False
  buf.options[ 'readonly' ] = True
  buf.options[ 'buflisted' ] = False
  buf.options[ 'bufhidden' ] = 'hide'
  buf.name = name


def SetUpPromptBuffer( buf, name, prompt, callback, hidden=False ):
  # This feature is _super_ new, so only enable when available
  if not int( vim.eval( "exists( '*prompt_setprompt' )" ) ):
    return SetUpScratchBuffer( buf, name )

  buf.options[ 'buftype' ] = 'prompt'
  buf.options[ 'swapfile' ] = False
  buf.options[ 'modifiable' ] = True
  buf.options[ 'modified' ] = False
  buf.options[ 'readonly' ] = False
  buf.options[ 'buflisted' ] = False
  buf.options[ 'bufhidden' ] = 'wipe' if not hidden else 'hide'
  buf.name = name

  vim.eval( "prompt_setprompt( {0}, '{1}' )".format( buf.number,
                                                     Escape( prompt ) ) )
  vim.eval( "prompt_setcallback( {0}, function( '{1}' ) )".format(
    buf.number,
    Escape( callback ) ) )



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
  # TODO: Don't trigger autoccommands when shifting windows
  old_window = vim.current.window
  try:
    yield
  finally:
    vim.current.window = old_window


@contextlib.contextmanager
def RestoreCurrentBuffer( window ):
  # TODO: Don't trigger autoccommands when shifting buffers
  old_buffer = window.buffer
  try:
    yield
  finally:
    with RestoreCurrentWindow():
      vim.current.window = window
      vim.current.buffer = old_buffer


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


def PathToConfigFile( file_name ):
  p = os.getcwd()
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


def UserMessage( msg, persist=False ):
  vim.command( 'redraw' )
  cmd = 'echom' if persist else 'echo'
  for line in msg.split( '\n' ):
    vim.command( "{0} '{1}'".format( cmd, Escape( line ) ) )


@contextlib.contextmanager
def InputSave():
  vim.eval( 'inputsave()' )
  try:
    yield
  except Exception:
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


def AskForInput( prompt ):
  # TODO: Handle the ctrl-c and such responses returning empty or something
  with InputSave():
    try:
      return vim.eval( "input( '{0}' )".format( Escape( prompt ) ) )
    except KeyboardInterrupt:
      return ''


def AppendToBuffer( buf, line_or_lines, modified=False ):
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
    logging.getLogger( __name__ ).exception(
      'Internal error while updating buffer %s (%s)', buf.name, buf.number )
  finally:
    if not modified:
      buf.options[ 'modified' ] = False

  # Return the first Vim line number (1-based) that we just set.
  return line



def ClearBuffer( buf ):
  buf[ : ] = None


def IsCurrent( window, buf ):
  return vim.current.window == window and vim.current.window.buffer == buf


# TODO: Should we just run the substitution on the whole JSON string instead?
# That woul dallow expansion in bool and number values, such as ports etc. ?
def ExpandReferencesInDict( obj, mapping, **kwargs ):
  def expand_refs_in_string( s ):
    s = os.path.expanduser( s )
    s = os.path.expandvars( s )

    # Parse any variables passed in in mapping, and ask for any that weren't,
    # storing the result in mapping
    bug_catcher = 0
    while bug_catcher < 100:
      ++bug_catcher

      try:
        s = string.Template( s ).substitute( mapping, **kwargs )
        break
      except KeyError as e:
        # HACK: This is seemingly the only way to get the key. str( e ) returns
        # the key surrounded by '' for unknowable reasons.
        key = e.args[ 0 ]
        mapping[ key ] = AskForInput( 'Enter value for {}: '.format( key ) )
      except ValueError as e:
        UserMessage( 'Invalid $ in string {}: {}'.format( s, e ),
                     persist = True )
        break

    return s

  def expand_refs_in_object( obj ):
    if isinstance( obj, dict ):
      ExpandReferencesInDict( obj, mapping, **kwargs )
    elif isinstance( obj, list ):
      for i, _ in enumerate( obj ):
        # FIXME: We are assuming that it is a list of string, but could be a
        # list of list of a list of dict, etc.
        obj[ i ] = expand_refs_in_object( obj[ i ] )
    elif isinstance( obj, str ):
      obj = expand_refs_in_string( obj )

    return obj

  for k in obj.keys():
    obj[ k ] = expand_refs_in_object( obj[ k ] )


def ParseVariables( variables ):
  new_variables = {}
  for n, v in variables.items():
    if isinstance( v, dict ):
      if 'shell' in v:
        import subprocess
        import shlex

        new_v = v.copy()
        # Bit of a hack. Allows environment variables to be used.
        ExpandReferencesInDict( new_v, {} )

        env = os.environ.copy()
        env.update( new_v.get( 'env' ) or {} )
        cmd = new_v[ 'shell' ]
        if not isinstance( cmd, list ):
          cmd = shlex.split( cmd )

        new_variables[ n ] = subprocess.check_output(
          cmd,
          cwd = new_v.get( 'cwd' ) or os.getcwd(),
          env = env ).decode( 'utf-8' ).strip()
      else:
        raise ValueError(
          "Unsupported variable defn {}: Missing 'shell'".format( n ) )
    else:
      new_variables[ n ] = v

  return new_variables


def DisplayBaloon( is_term, display ):
  if not is_term:
    display = '\n'.join( display )

  vim.eval( "balloon_show( {0} )".format(
    json.dumps( display ) ) )
