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

import abc
import vim
import logging
from functools import partial
import typing

from vimspector import utils, settings
from vimspector.debug_adapter_connection import DebugAdapterConnection


class Expandable:
  EXPANDED_BY_USER = 2
  EXPANDED_BY_US = 1
  COLLAPSED_BY_USER = 0
  COLLAPSED_BY_DEFAULT = None

  connection: DebugAdapterConnection

  """Base for anything which might contain a hierarchy of values represented by
  a 'variablesReference' to be resolved by the 'variables' request. Records the
  current state expanded/collapsed. Implementations just implement
  VariablesReference to get the variables."""
  def __init__( self,
                connection: DebugAdapterConnection,
                container: 'Expandable' = None ):
    self.variables: typing.List[ 'Variable' ] = None
    self.container: Expandable = container
    self.connection = connection
    # None is Falsy and represents collapsed _by default_. WHen set to False,
    # this means the user explicitly collapsed it. When True, the user expanded
    # it (or we expanded it by default).
    self.expanded: int = Expandable.COLLAPSED_BY_DEFAULT

  def IsExpanded( self ):
    return bool( self.expanded )

  def ShouldDrawDrillDown( self ):
    return self.IsExpanded() and self.variables is not None

  def IsExpandable( self ):
    return self.VariablesReference() > 0

  def IsContained( self ):
    return self.container is not None

  @abc.abstractmethod
  def VariablesReference( self ):
    assert False

  def MemoryReference( self ):
    assert None

  @abc.abstractmethod
  def HoverText( self ):
    return ""


class Scope( Expandable ):
  """Holds an expandable scope (a DAP scope dict), with expand/collapse state"""
  def __init__( self, connection: DebugAdapterConnection, scope: dict ):
    super().__init__( connection )
    self.scope = scope

  def VariablesReference( self ):
    return self.scope.get( 'variablesReference', 0 )

  def MemoryReference( self ):
    return None

  def Update( self, scope ):
    self.scope = scope

  def HoverText( self ):
    return ""


class WatchResult( Expandable ):
  """Holds the result of a Watch expression with expand/collapse."""
  def __init__( self, connection: DebugAdapterConnection, result: dict ):
    super().__init__( connection )
    self.result = result
    # A new watch result is marked as changed
    self.changed = True

  def VariablesReference( self ):
    return self.result.get( 'variablesReference', 0 )

  def MemoryReference( self ):
    return self.result.get( 'memoryReference' )

  def Update( self, result ):
    self.changed = False
    if self.result[ 'result' ] != result[ 'result' ]:
      self.changed = True
    self.result = result

  def HoverText( self ):
    if not self.result:
      return None

    return (
      f"Type:  { self.result.get( 'type', '<unknown>' ) }\n"
      f"Value: { self.result.get( 'result', '<unknown>' ) }"
    )


class WatchFailure( WatchResult ):
  def __init__( self, connection: DebugAdapterConnection, reason ):
    super().__init__( connection, { 'result': reason } )
    self.changed = True


class Variable( Expandable ):
  """Holds one level of an expanded value tree. Also itself expandable."""
  def __init__( self,
                connection: DebugAdapterConnection,
                container: Expandable, variable: dict ):
    super().__init__( connection = connection, container = container )
    self.variable = variable
    # A new variable appearing is marked as changed
    self.changed = True

  def VariablesReference( self ):
    return self.variable.get( 'variablesReference', 0 )

  def MemoryReference( self ):
    return self.variable.get( 'memoryReference' )

  def Update( self, variable ):
    self.changed = False
    if self.variable[ 'value' ] != variable[ 'value' ]:
      self.changed = True
    self.variable = variable

  def HoverText( self ):
    if not self.variable:
      return None

    return (
      f"Name:  { self.variable.get( 'name', '<unknown>' ) }\n"
      f"Type:  { self.variable.get( 'type', '<unknown>' ) }\n"
      f"Value: { self.variable.get( 'value', '<unknown>' ) }"
    )


class Watch:
  """Holds a user watch expression (DAP request) and the result (WatchResult)"""
  def __init__( self, connection: DebugAdapterConnection, expression: dict ):
    self.result: WatchResult
    self.line = None
    self.connection = connection

    self.expression = expression
    self.result = None

  def SetCurrentFrame( self, connection, frame ):
    if self.connection is None:
      self.connection = connection
    elif self.connection != connection:
      return

    self.expression[ 'frameId' ] = frame[ 'id' ]

  @staticmethod
  def New( connection, frame, expression, context ):
    watch = {
      'expression': expression,
      'context': context,
    }
    if frame:
      watch[ 'frameId' ] = frame[ 'id' ]

    return Watch( connection, watch )


class View:
  lines: typing.Dict[ int, Expandable ]
  draw: typing.Callable
  syntax: str

  def __init__( self, win, lines, draw ):
    self.lines = lines
    self.draw = draw
    self.syntax = None
    if win is not None:
      self.buf = win.buffer
      utils.SetUpUIWindow( win )


class BufView( View ):
  def __init__( self, buf, lines, draw ):
    super().__init__( None, lines, draw )
    self.buf = buf


def AddExpandMappings( mappings = None ):
  if mappings is None:
    mappings = settings.Dict( 'mappings' )[ 'variables' ]
  for mapping in utils.GetVimList( mappings, 'expand_collapse' ):
    vim.command( f'nnoremap <silent> <buffer> { mapping } '
                 ':<C-u>call vimspector#ExpandVariable()<CR>' )

  for mapping in utils.GetVimList( mappings, 'set_value' ):
    vim.command( f'nnoremap <silent> <buffer> { mapping } '
                 ':<C-u>call vimspector#SetVariableValue()<CR>' )
  for mapping in utils.GetVimList( mappings, 'read_memory' ):
    vim.command( f'nnoremap <silent> <buffer> { mapping } '
                 ':<C-u>call vimspector#ReadMemory()<CR>' )



class VariablesView( object ):
  def __init__( self, session_id, variables_win, watches_win ):
    self._logger = logging.getLogger(
      __name__ + '.' + str( session_id ) )
    utils.SetUpLogging( self._logger, session_id )

    self._current_syntax = ''

    self._variable_eval: Scope = None
    self._variable_eval_view: View = None

    mappings = settings.Dict( 'mappings' )[ 'variables' ]

    # Set up the "Variables" buffer in the variables_win
    self._scopes: typing.List[ Scope ] = []
    self._vars = View( variables_win, {}, self._DrawScopes )
    utils.SetUpHiddenBuffer(
      self._vars.buf,
      utils.BufferNameForSession( 'vimspector.Variables',
                                  session_id ) )
    with utils.LetCurrentWindow( variables_win ):
      if utils.UseWinBar():
        utils.SetWinBar(
          ( 'Set', 'vimspector#SetVariableValue()', ),
          ( 'Dump', 'vimspector#ReadMemory()' )
        )
      AddExpandMappings( mappings )

    # Set up the "Watches" buffer in the watches_win (and create a WinBar in
    # there)
    self._watches: typing.List[ Watch ] = []
    self._watch = View( watches_win, {}, self._DrawWatches )
    utils.SetUpPromptBuffer(
      self._watch.buf,
      utils.BufferNameForSession( 'vimspector.Watches',
                                  session_id ),
      'Expression: ',
      'vimspector#AddWatchPrompt',
      'vimspector#OmniFuncWatch' )

    with utils.LetCurrentWindow( watches_win ):
      AddExpandMappings( mappings )
      for mapping in utils.GetVimList( mappings, 'delete' ):
        vim.command(
          f'nnoremap <buffer> { mapping } :call vimspector#DeleteWatch()<CR>' )

      if utils.UseWinBar():
        utils.SetWinBar(
          ( 'Add', 'vimspector#AddWatch()', ),
          ( 'Delete', 'vimspector#DeleteWatch()', ),
          ( '+/-', 'vimspector#ExpandVariable()', ),
          ( 'Set', 'vimspector#SetVariableValue()', ),
          ( 'Dump', 'vimspector#ReadMemory()', )
        )

    # Set the (global!) balloon expr if supported
    has_balloon      = int( vim.eval( "has( 'balloon_eval' )" ) )
    has_balloon_term = int( vim.eval( "has( 'balloon_eval_term' )" ) )

    self._oldoptions = {}
    if has_balloon or has_balloon_term:
      self._oldoptions = {
        'balloonexpr': vim.options[ 'balloonexpr' ],
        'balloondelay': vim.options[ 'balloondelay' ],
      }
      vim.options[ 'balloonexpr' ] = (
        "vimspector#internal#balloon#HoverEvalTooltip()"
      )

      vim.options[ 'balloondelay' ] = 250

    if has_balloon:
      self._oldoptions[ 'ballooneval' ] = vim.options[ 'ballooneval' ]
      vim.options[ 'ballooneval' ] = True

    if has_balloon_term:
      self._oldoptions[ 'balloonevalterm' ] = vim.options[ 'balloonevalterm' ]
      vim.options[ 'balloonevalterm' ] = True


  def Clear( self ):
    with utils.ModifiableScratchBuffer( self._vars.buf ):
      utils.ClearBuffer( self._vars.buf )
    self.ClearTooltip()


  def ConnectionClosed( self, connection ):
    self._scopes[ : ] = [
      s for s in self._scopes if s.connection != connection
    ]
    for w in self._watches:
      if w.connection == connection:
        w.connection = None


  def Reset( self ):
    for k, v in self._oldoptions.items():
      vim.options[ k ] = v

    utils.CleanUpHiddenBuffer( self._vars.buf )
    utils.CleanUpHiddenBuffer( self._watch.buf )
    self.ClearTooltip()

  def Save( self ):
    return {
      'watches': [
        watch.expression[ 'expression' ] for watch in self._watches
      ]
    }

  def Load( self, save_data ):
    for expression in save_data.get( 'watches', [] ):
      # It's not really possible to save the frameId, so we just supply None
      self._watches.append( Watch.New( None, None, expression, 'watch' ) )

  def LoadScopes( self, connection, frame ):
    def scopes_consumer( message ):
      new_scopes = []
      expanded_some_scope = False
      for scope_body in message[ 'body' ][ 'scopes' ]:
        # Find it in the scopes list
        found = False
        for index, s in enumerate( self._scopes ):
          if ( s.connection == connection and
               s.scope[ 'name' ] == scope_body[ 'name' ] ):
            found = True
            scope = s
            break

        if not found:
          scope = Scope( connection, scope_body )
        else:
          scope.Update( scope_body )

        new_scopes.append( scope )

        # Expand the first non-expensive scope which is not manually collapsed
        if ( not expanded_some_scope
             and not scope.scope.get( 'expensive' )
             and scope.expanded is not Expandable.COLLAPSED_BY_USER ):
          scope.expanded = Expandable.EXPANDED_BY_US
          expanded_some_scope = True
        elif ( expanded_some_scope and scope.expanded is
               Expandable.EXPANDED_BY_US ):
          scope.expanded = Expandable.COLLAPSED_BY_DEFAULT

        if scope.IsExpanded():
          connection.DoRequest( partial( self._ConsumeVariables,
                                         self._DrawScopes,
                                         scope ), {
            'command': 'variables',
            'arguments': {
              'variablesReference': scope.VariablesReference(),
            },
          } )

      self._scopes = new_scopes
      self._DrawScopes()

    connection.DoRequest( scopes_consumer, {
      'command': 'scopes',
      'arguments': {
        'frameId': frame[ 'id' ]
      },
    } )

  def _DrawBalloonEval( self ):
    watch = self._variable_eval
    view = self._variable_eval_view

    with utils.RestoreCursorPosition():
      with utils.ModifiableScratchBuffer( view.buf ):
        utils.ClearBuffer( view.buf )
        view.syntax = utils.SetSyntax( view.syntax,
                                       self._current_syntax,
                                       view.buf )

        self._DrawWatchResult( view,
                               0,
                               watch,
                               is_short = True )

        vim.eval( "vimspector#internal#balloon#ResizeTooltip()" )

  def ClearTooltip( self ):
    # This will actually end up calling CleanUpTooltip via the popup close
    # callback
    vim.eval( 'vimspector#internal#balloon#Close()' )

  def CleanUpTooltip( self ) :
    # remove reference to old tooltip window
    self._variable_eval_view = None
    vim.vars[ 'vimspector_session_windows' ][ 'eval' ] = None

  def HoverEvalTooltip( self, connection, frame, expression, is_hover ):
    """Callback to display variable under cursor `:h ballonexpr`"""
    if not connection:
      return ''

    def handler( message ):

      watch = self._variable_eval
      if watch.result is None or watch.result.connection != connection:
        watch.result = WatchResult( connection, message[ 'body' ] )
      else:
        watch.result.Update( message[ 'body' ] )

      popup_win_id = utils.CreateTooltip( [], is_hover )
      # record the global eval window id
      vim.vars[ 'vimspector_session_windows' ][ 'eval' ] = int( popup_win_id )
      popup_bufnr = int( vim.eval( "winbufnr({})".format( popup_win_id ) ) )

      # We don't need to do any UI window setup here, as it's already done as
      # part of the popup creation, so just pass the buffer to the View instance
      self._variable_eval_view = BufView(
        vim.buffers[ popup_bufnr ],
        {},
        self._DrawBalloonEval
      )

      if watch.result.IsExpandable():
        # Always expand the first level
        watch.result.expanded = Expandable.EXPANDED_BY_US

      if watch.result.IsExpanded():
        connection.DoRequest( partial( self._ConsumeVariables,
                                       self._variable_eval_view.draw,
                                       watch.result ), {
          'command': 'variables',
          'arguments': {
            'variablesReference': watch.result.VariablesReference(),
          },
        } )

      self._DrawBalloonEval()

    def failure_handler( reason, message ):
      display = [ reason ]
      float_win_id = utils.CreateTooltip( display, is_hover )
      # record the global eval window id
      vim.vars[ 'vimspector_session_windows' ][ 'eval' ] = int( float_win_id )

    self._variable_eval = Watch.New( connection,
                                     frame,
                                     expression,
                                     'hover' )

    # Send async request
    connection.DoRequest( handler, {
      'command': 'evaluate',
      'arguments': self._variable_eval.expression,
    }, failure_handler )

    # Return working (meanwhile)
    return ''

  def HoverVarWinTooltip( self, bufnr, lnum, is_hover ):
    variable, view = self._GetVariable( vim.buffers[ bufnr ], lnum )
    if variable is None:
      return ''

    hover = variable.HoverText()
    if hover:
      utils.CreateTooltip( hover.split( '\n' ), is_hover )

    return ''

  def AddWatch( self, connection, frame, expression ):
    self._watches.append( Watch.New( connection, frame, expression, 'watch' ) )
    self.EvaluateWatches( connection, frame )

  def DeleteWatch( self ):
    if vim.current.buffer != self._watch.buf:
      utils.UserMessage( 'Not a watch buffer' )
      return

    current_line = vim.current.window.cursor[ 0 ]

    best_index = -1
    for index, watch in enumerate( self._watches ):
      if ( watch.line is not None
           and watch.line <= current_line
           and watch.line > best_index ):
        best_index = index

    if best_index >= 0:
      del self._watches[ best_index ]
      utils.UserMessage( 'Deleted' )
      self._DrawWatches()
      return

    utils.UserMessage( 'No watch found' )

  def EvaluateWatches( self,
                       fallback_connection: DebugAdapterConnection,
                       current_frame: dict ):

    for watch in self._watches:
      watch.SetCurrentFrame( fallback_connection, current_frame )
      watch.connection.DoRequest(
        partial( self._UpdateWatchExpression, watch ),
        {
          'command': 'evaluate',
          'arguments': watch.expression,
        },
        failure_handler = lambda reason, msg, watch=watch:
            self._WatchExpressionFailed( reason, watch ) )

  def _UpdateWatchExpression( self, watch: Watch, message: dict ):
    if watch.result is not None:
      watch.result.Update( message[ 'body' ] )
    else:
      watch.result = WatchResult( watch.connection, message[ 'body' ] )

    if ( watch.result.IsExpandable() and
         watch.result.IsExpanded() ):
      watch.connection.DoRequest( partial( self._ConsumeVariables,
                                           self._watch.draw,
                                           watch.result ), {
        'command': 'variables',
        'arguments': {
          'variablesReference': watch.result.VariablesReference(),
        },
      } )

    self._DrawWatches()

  def _WatchExpressionFailed( self, reason: str, watch: Watch ):
    if watch.result is not None:
      # We already have a result for this watch. Wut ?
      return

    watch.result = WatchFailure( watch.connection, reason )
    self._DrawWatches()

  def _GetVariable( self, buf = None, line_num = None ):
    none = ( None, None )

    if buf is None:
      buf = vim.current.buffer

    if line_num is None:
      line_num = vim.current.window.cursor[ 0 ]

    if buf == self._vars.buf:
      view = self._vars
    elif buf == self._watch.buf:
      view = self._watch
    elif ( self._variable_eval_view is not None
           and buf == self._variable_eval_view.buf ):
      view = self._variable_eval_view
    else:
      return none

    if line_num not in view.lines:
      return none

    return view.lines[ line_num ], view

  def ExpandVariable( self, buf = None, line_num = None ):
    variable, view = self._GetVariable( buf, line_num )
    if variable is None:
      return

    if variable.IsExpanded():
      # Collapse
      variable.expanded = Expandable.COLLAPSED_BY_USER
      view.draw()
      return

    if not variable.IsExpandable():
      return

    variable.expanded = Expandable.EXPANDED_BY_USER
    variable.connection.DoRequest( partial( self._ConsumeVariables,
                                            view.draw,
                                            variable ), {
      'command': 'variables',
      'arguments': {
        'variablesReference': variable.VariablesReference()
      },
    } )

  def SetVariableValue( self, new_value = None, buf = None, line_num = None ):
    variable: Variable
    view: View

    variable, view = self._GetVariable( buf, line_num )
    if variable is None:
      return

    if not variable.IsContained():
      return

    if new_value is None:
      new_value = utils.AskForInput( 'New Value: ',
                                     variable.variable.get( 'value', '' ),
                                     completion = 'expr' )

    if new_value is None:
      return


    def handler( message ):
      # Annoyingly the response to setVariable request doesn't return a
      # Variable, but some part of it, so take a copy of the existing Variable
      # dict and update it, then call its update method with the updated copy.
      new_variable = dict( variable.variable )
      new_variable.update( message[ 'body' ] )

      # Clear any existing known children (FIXME: Is this the right thing to do)
      variable.variables = None

      # If the variable is expanded, re-request its children
      if variable.IsExpanded():
        variable.connection.DoRequest( partial( self._ConsumeVariables,
                                                view.draw,
                                                variable ), {
          'command': 'variables',
          'arguments': {
            'variablesReference': variable.VariablesReference()
          },
        } )

      variable.Update( new_variable )
      view.draw()

    def failure_handler( reason, message ):
      utils.UserMessage( f'Cannot set value: { reason }', error = True )

    variable.connection.DoRequest( handler, {
      'command': 'setVariable',
      'arguments': {
        'variablesReference': variable.container.VariablesReference(),
        'name': variable.variable[ 'name' ],
        'value': new_value
      },
    }, failure_handler = failure_handler )


  def GetMemoryReference( self ):
    # Get a memoryReference for use in a ReadMemory request
    variable, _ = self._GetVariable( None, None )
    if variable is None:
      return None

    # TODO: Return the connection too!
    return variable.connection, variable.MemoryReference()


  def _DrawVariables( self, view, variables, indent_len, is_short = False ):
    assert indent_len > 0
    for variable in variables:
      text = ''
      # We borrow 1 space of indent to draw the change marker
      indent = ' ' * ( indent_len - 1 )
      marker = '*' if variable.changed else ' '
      icon = '+' if ( variable.IsExpandable()
                      and not variable.IsExpanded() ) else '-'
      name = variable.variable.get( 'name', '' )
      kind = variable.variable.get( 'type', '' )
      value = variable.variable.get( 'value', '<unknown>' )
      hl = settings.Dict( 'presentation_hint_hl' ).get(
        variable.variable.get( 'presentationHint', {} ).get( 'kind',
                                                             'normal' ) )


      # FIXME: If 'value' is multi-line, somehow turn it into an expandable item
      # where the expansion is done "internally", resolving to the multi-line
      # value
      if is_short:
        value = variable.variable.get( 'value', '<unknown>' )
        text = f'{indent}{icon} {name}: {value}'
      elif settings.Get( 'variables_display_mode' ) == 'compact':
        value = variable.variable.get( 'value', '<unknown>' ).splitlines()
        if len( value ) > 0:
          value = value[ 0 ]
        else:
          value = ''

        text = f'{indent}{marker}{icon} {name}: {value}'
      else:
        text = f'{indent}{marker}{icon} {name} ({kind}): {value}'

      line = utils.AppendToBuffer(
        view.buf,
        text.split( '\n' ),
        hl = hl
      )

      view.lines[ line ] = variable

      if variable.ShouldDrawDrillDown():
        self._DrawVariables( view,
                             variable.variables,
                             indent_len + 2,
                             is_short )

  def _DrawScopes( self ):
    # FIXME: The drawing is dumb and draws from scratch every time. This is
    # simple and works and makes sure the line-map is always correct.
    # However it is pretty inefficient.
    self._vars.lines.clear()
    with utils.RestoreCursorPosition():
      with utils.ModifiableScratchBuffer( self._vars.buf ):
        utils.ClearBuffer( self._vars.buf )
        for scope in self._scopes:
          self._DrawScope( 0, scope )

  def _DrawWatches( self ):
    # FIXME: The drawing is dumb and draws from scratch every time. This is
    # simple and works and makes sure the line-map is always correct.
    # However it is pretty inefficient.
    self._watch.lines.clear()
    with utils.RestoreCursorPosition():
      with utils.ModifiableScratchBuffer( self._watch.buf ):
        utils.ClearBuffer( self._watch.buf )
        utils.AppendToBuffer( self._watch.buf, 'Watches: ----', hl = 'Title' )
        for watch in self._watches:
          line = utils.AppendToBuffer( self._watch.buf,
                                       'Expression: '
                                       + watch.expression[ 'expression' ],
                                       hl = 'Title' )
          watch.line = line
          self._DrawWatchResult( self._watch, 2, watch )

  def _DrawScope( self, indent, scope ):
    icon = '+' if scope.IsExpandable() and not scope.IsExpanded() else '-'

    hl = settings.Dict( 'presentation_hint_hl' ).get(
      scope.scope.get( 'presentationHint', 'normal' ) )
    line = utils.AppendToBuffer( self._vars.buf,
                                 '{0}{1} Scope: {2}'.format(
                                   ' ' * indent,
                                   icon,
                                   scope.scope[ 'name' ] ),
                                 hl = hl )
    self._vars.lines[ line ] = scope

    if scope.ShouldDrawDrillDown():
      indent += 2
      self._DrawVariables( self._vars, scope.variables, indent )

  def _DrawWatchResult( self, view, indent_len, watch, is_short = False ):
    if not watch.result:
      return

    assert is_short or indent_len > 0

    if is_short:
      # The first result is always expanded in a hover (short format)
      icon = ''
      marker = ''
      leader = ''
    else:
      icon = '+' if ( watch.result.IsExpandable() and
                      not watch.result.IsExpanded() ) else '-'
      marker = '*' if watch.result.changed else ' '
      leader = ' Result: '

    value = watch.result.result.get( 'result', '<unknown>' )
    # We borrow 1 space of indent to draw the change marker
    indent = ' ' * ( indent_len - 1 )

    if settings.Get( 'variables_display_mode' ) == 'compact':
      value = value.splitlines()
      if len( value ) > 0:
        value = value[ 0 ]
      else:
        value = ''

    line = f'{indent}{marker}{icon}{leader}{value}'

    line = utils.AppendToBuffer( view.buf, line.split( '\n' ) )
    view.lines[ line ] = watch.result

    if watch.result.ShouldDrawDrillDown():
      self._DrawVariables( view,
                           watch.result.variables,
                           indent_len + 2,
                           is_short )

  def _ConsumeVariables( self, draw, parent, message ):
    new_variables = []
    for variable_body in message[ 'body' ][ 'variables' ]:
      if parent.variables is None:
        parent.variables = []

      # Find the variable in parent
      found = False
      for index, v in enumerate( parent.variables ):
        if v.variable[ 'name' ] == variable_body[ 'name' ]:
          variable = v
          found = True
          break
      if not found:
        variable = Variable( parent.connection, parent, variable_body )
      else:
        variable.Update( variable_body )

      new_variables.append( variable )

      if variable.IsExpandable() and variable.IsExpanded():
        variable.connection.DoRequest( partial( self._ConsumeVariables,
                                                draw,
                                                variable ), {
          'command': 'variables',
          'arguments': {
            'variablesReference': variable.VariablesReference()
          },
        } )

    parent.variables = new_variables

    draw()

  def SetSyntax( self, syntax ):
    # TODO: Switch to View.syntax
    self._current_syntax = utils.SetSyntax( self._current_syntax,
                                            syntax,
                                            self._vars.buf,
                                            self._watch.buf )
# vim: sw=2
