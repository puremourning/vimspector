from vimspector import utils, settings

import os
import vim


class Terminal:
  window = None
  buffer_number: int = None


def LaunchTerminal( api_prefix,
                    params,
                    window_for_start,
                    existing_term ):
  if not existing_term:
    term = Terminal()
  else:
    term = existing_term

  cwd = params[ 'cwd' ] or os.getcwd()
  args = params[ 'args' ] or []
  env = params.get( 'env' ) or {}

  term_options = {
    'vertical': 1,
    'norestore': 1,
    'cwd': cwd,
    'env': env,
  }

  if not window_for_start or not window_for_start.valid:
    # TOOD: Where? Maybe we should just use botright vertical ...
    window_for_start = vim.current.window

  if term.window is not None and term.window.valid:
    if not term.buffer_number:
      raise AssertionError
    window_for_start = term.window
    if ( term.window.buffer.number == term.buffer_number
         and int( utils.Call( 'vimspector#internal#{}term#IsFinished'.format(
                                api_prefix ),
                              term.buffer_number ) ) ):
      term_options[ 'curwin' ] = 1
    else:
      term_options[ 'vertical' ] = 0

  buffer_number = None
  terminal_window = None
  with utils.LetCurrentWindow( window_for_start ):
    # If we're making a vertical split from the code window, make it no more
    # than 80 columns and no fewer than 10. Also try and keep the code window
    # at least 82 columns
    if term_options[ 'vertical' ] and not term_options.get( 'curwin', 0 ):
      term_options[ 'term_cols' ] = max(
        min ( int( vim.eval( 'winwidth( 0 )' ) )
                   - settings.Int( 'code_minwidth' ),
              settings.Int( 'terminal_maxwidth' ) ),
        settings.Int( 'terminal_minwidth' )
      )

    buffer_number = int(
      utils.Call(
        'vimspector#internal#{}term#Start'.format( api_prefix ),
        args,
        term_options ) )
    terminal_window = vim.current.window

  if buffer_number is None or buffer_number <= 0:
    # TODO: Do something better like reject the request?
    raise ValueError( "Unable to start terminal" )

  term.window = terminal_window
  term.buffer_number = buffer_number

  vim.vars[ 'vimspector_session_windows' ][ 'terminal' ] = utils.WindowID(
    term.window,
    vim.current.tabpage )
  with utils.RestoreCursorPosition():
    with utils.RestoreCurrentWindow():
      with utils.RestoreCurrentBuffer( vim.current.window ):
        vim.command( 'doautocmd User VimspectorTerminalOpened' )

  return term
