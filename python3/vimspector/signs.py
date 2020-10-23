import vim

from vimspector import settings, utils


def SignDefined( name ):
  if utils.Exists( "*sign_getdefined" ):
    return int(
      vim.eval( f"len( sign_getdefined( '{ utils.Escape( name ) }' ) )" )
    )

  return False


def DefineSign( name, text, double_text, texthl, col = 'right', **kwargs ):
  if utils.GetVimValue( vim.options, 'ambiwidth', '' ) == 'double':
    text = double_text

  if col == 'right':
    if int( utils.Call( 'strdisplaywidth', text ) ) < 2:
      text = ' ' + text

  text = text.replace( ' ', r'\ ' )

  cmd = f'sign define { name } text={ text } texthl={ texthl }'
  for key, value in kwargs.items():
    cmd += f' { key }={ value }'

  vim.command( cmd )


def PlaceSign( sign_id, group, name, file_name, line ):
  priority = settings.Dict( 'sign_priority' )[ name ]

  cmd = ( f'sign place { sign_id } '
          f'group={ group } '
          f'name={ name } '
          f'priority={ priority } '
          f'line={ line } '
          f'file={ file_name }' )

  vim.command( cmd )


def UnplaceSign( sign_id, group ):
  vim.command( f'sign unplace { sign_id } group={ group }' )
