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
    'norestore': 1,
    'cwd': cwd,
    'env': env,
  }

  if settings.Get( 'ui_mode' ) == 'horizontal':
    # force-horizontal
    term_options[ 'vertical' ] = 1
  elif utils.GetVimValue( vim.vars[ 'vimspector_session_windows' ],
                          'mode' ) == 'horizontal':
    # horizontal, which means that we should have enough space for:
    #  - sidebar
    #  - code min
    #  - term min width
    #  - + 2 vertical spaders
    #  - + 3 columns for signs
    term_options[ 'vertical' ] = 1

    # if we don't have enough space for terminal_maxwidth, then see if we have
    # enough vertically for terminal_maxheight, in which case,
    # that seems a better fit
    term_horiz_max = ( settings.Int( 'sidebar_width' ) +
                       1 + 2 + 3 +
                       settings.Int( 'code_minwidth' ) +
                       1 + settings.Int( 'terminal_maxwidth' ) )
    term_vert_max = ( settings.Int( 'bottombar_height' ) + 1 +
                      settings.Int( 'code_minheight' ) + 1 +
                      settings.Int( 'terminal_minheight' ) )

    if ( vim.options[ 'columns' ] < term_horiz_max and
         vim.options[ 'lines' ] >= term_vert_max ):
      # Looks like it, let's try that layout
      term_options[ 'vertical' ] = 0


  else:
    # vertical - we need enough space horizontally for the code+terminal, but we
    # may fit better with code above terminal
    term_options[ 'vertical' ] = 0

    term_horiz_max = ( settings.Int( 'code_minwidth' ) + 3 +
                       settings.Int( 'terminal_maxwidth' ) + 1 )

    if vim.options[ 'columns' ] > term_horiz_max:
      term_options[ 'vertical' ] = 1


  if not window_for_start or not window_for_start.valid:
    # TODO: Where? Maybe we should just use botright vertical ...
    window_for_start = vim.current.window

  if term.window is not None and term.window.valid:
    assert term.buffer_number
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
    if term_options.get( 'curwin', 0 ):
      pass
    elif term_options[ 'vertical' ]:
      term_options[ 'term_cols' ] = max(
        min ( int( vim.eval( 'winwidth( 0 )' ) )
                   - settings.Int( 'code_minwidth' ),
              settings.Int( 'terminal_maxwidth' ) ),
        settings.Int( 'terminal_minwidth' )
      )
    else:
      term_options[ 'term_rows' ] = max(
        min ( int( vim.eval( 'winheight( 0 )' ) )
                   - settings.Int( 'code_minheight' ),
              settings.Int( 'terminal_maxheight' ) ),
        settings.Int( 'terminal_minheight' )
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

  utils.UpdateSessionWindows( {
    'terminal': utils.WindowID( term.window, vim.current.tabpage )
  } )
  with utils.RestoreCursorPosition():
    with utils.RestoreCurrentWindow():
      with utils.RestoreCurrentBuffer( vim.current.window ):
        vim.command( 'doautocmd User VimspectorTerminalOpened' )

  return term
