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

from vimspector import utils


class Expandable:
  EXPANDED_BY_USER = 2
  EXPANDED_BY_US = 1
  COLLAPSED_BY_USER = 0
  COLLAPSED_BY_DEFAULT = None

  """Base for anything which might contain a hierarchy of values represented by
  a 'variablesReference' to be resolved by the 'variables' request. Records the
  current state expanded/collapsed. Implementations just implement
  VariablesReference to get the variables."""
  def __init__( self ):
    self.variables: typing.List[ 'Variable' ] = None
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

  @abc.abstractmethod
  def VariablesReference( self ):
    assert False


class Scope( Expandable ):
  """Holds an expandable scope (a DAP scope dict), with expand/collapse state"""
  def __init__( self, scope: dict ):
    super().__init__()
    self.scope = scope

  def VariablesReference( self ):
    return self.scope.get( 'variablesReference', 0 )

  def Update( self, scope ):
    self.scope = scope


class WatchResult( Expandable ):
  """Holds the result of a Watch expression with expand/collapse."""
  def __init__( self, result: dict ):
    super().__init__()
    self.result = result
    # A new watch result is marked as changed
    self.changed = True

  def VariablesReference( self ):
    return self.result.get( 'variablesReference', 0 )

  def Update( self, result ):
    self.changed = False
    if self.result[ 'result' ] != result[ 'result' ]:
      self.changed = True
    self.result = result


class WatchFailure( WatchResult ):
  def __init__( self, reason ):
    super().__init__( { 'result': reason } )
    self.changed = True


class Variable( Expandable ):
  """Holds one level of an expanded value tree. Also itself expandable."""
  def __init__( self, variable: dict ):
    super().__init__()
    self.variable = variable
    # A new variable appearing is marked as changed
    self.changed = True

  def VariablesReference( self ):
    return self.variable.get( 'variablesReference', 0 )

  def Update( self, variable ):
    self.changed = False
    if self.variable[ 'value' ] != variable[ 'value' ]:
      self.changed = True
    self.variable = variable


class Watch:
  """Holds a user watch expression (DAP request) and the result (WatchResult)"""
  def __init__( self, expression: dict ):
    self.result: WatchResult
    self.line = None

    self.expression = expression
    self.result = None


class View:
  lines: typing.Dict[ int, Expandable ]
  draw: typing.Callable

  def __init__( self, win, lines, draw ):
    self.lines = lines
    self.draw = draw
    self.buf = win.buffer

    utils.SetUpUIWindow( win )


class VariablesView( object ):
  def __init__( self, variables_win, watches_win ):
    self._logger = logging.getLogger( __name__ )
    utils.SetUpLogging( self._logger )

    self._connection = None
    self._current_syntax = ''

    def AddExpandMappings():
      vim.command( 'nnoremap <silent> <buffer> <CR> '
                   ':<C-u>call vimspector#ExpandVariable()<CR>' )
      vim.command( 'nnoremap <silent> <buffer> <2-LeftMouse> '
                   ':<C-u>call vimspector#ExpandVariable()<CR>' )

    # Set up the "Variables" buffer in the variables_win
    self._scopes: typing.List[ Scope ] = []
    self._vars = View( variables_win, {}, self._DrawScopes )
    utils.SetUpHiddenBuffer( self._vars.buf, 'vimspector.Variables' )
    with utils.LetCurrentWindow( variables_win ):
      AddExpandMappings()

    # Set up the "Watches" buffer in the watches_win (and create a WinBar in
    # there)
    self._watches: typing.List[ Watch ] = []
    self._watch = View( watches_win, {}, self._DrawWatches )
    utils.SetUpPromptBuffer( self._watch.buf,
                             'vimspector.Watches',
                             'Expression: ',
                             'vimspector#AddWatchPrompt',
                             'vimspector#OmniFuncWatch' )
    with utils.LetCurrentWindow( watches_win ):
      AddExpandMappings()
      vim.command(
        'nnoremap <buffer> <DEL> :call vimspector#DeleteWatch()<CR>' )

      if utils.UseWinBar():
        vim.command( 'nnoremenu 1.1 WinBar.New '
                     ':call vimspector#AddWatch()<CR>' )
        vim.command( 'nnoremenu 1.2 WinBar.Expand/Collapse '
                     ':call vimspector#ExpandVariable()<CR>' )
        vim.command( 'nnoremenu 1.3 WinBar.Delete '
                     ':call vimspector#DeleteWatch()<CR>' )

    # Set the (global!) balloon expr if supported
    has_balloon      = int( vim.eval( "has( 'balloon_eval' )" ) )
    has_balloon_term = int( vim.eval( "has( 'balloon_eval_term' )" ) )

    self._oldoptions = {}
    if has_balloon or has_balloon_term:
      self._oldoptions = {
        'balloonexpr': vim.options[ 'balloonexpr' ],
        'balloondelay': vim.options[ 'balloondelay' ],
      }
      vim.options[ 'balloonexpr' ] = 'vimspector#internal#balloon#BalloonExpr()'
      vim.options[ 'balloondelay' ] = 250

    if has_balloon:
      self._oldoptions[ 'ballooneval' ] = vim.options[ 'ballooneval' ]
      vim.options[ 'ballooneval' ] = True

    if has_balloon_term:
      self._oldoptions[ 'balloonevalterm' ] = vim.options[ 'balloonevalterm' ]
      vim.options[ 'balloonevalterm' ] = True

    self._is_term = not bool( int( vim.eval( "has( 'gui_running' )" ) ) )

  def Clear( self ):
    with utils.ModifiableScratchBuffer( self._vars.buf ):
      utils.ClearBuffer( self._vars.buf )
    with utils.ModifiableScratchBuffer( self._watch.buf ):
      utils.ClearBuffer( self._watch.buf )
    self._current_syntax = ''

  def ConnectionUp( self, connection ):
    self._connection = connection

  def ConnectionClosed( self ):
    self.Clear()
    self._connection = None

  def Reset( self ):
    for k, v in self._oldoptions.items():
      vim.options[ k ] = v

    utils.CleanUpHiddenBuffer( self._vars.buf )
    utils.CleanUpHiddenBuffer( self._watch.buf )

  def LoadScopes( self, frame ):
    def scopes_consumer( message ):
      new_scopes = []
      expanded_some_scope = False
      for scope_body in message[ 'body' ][ 'scopes' ]:
        # Find it in the scopes list
        found = False
        for index, s in enumerate( self._scopes ):
          if s.scope[ 'name' ] == scope_body[ 'name' ]:
            found = True
            scope = s
            break

        if not found:
          scope = Scope( scope_body )
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
          self._connection.DoRequest( partial( self._ConsumeVariables,
                                               self._DrawScopes,
                                               scope ), {
            'command': 'variables',
            'arguments': {
              'variablesReference': scope.VariablesReference(),
            },
          } )

      self._scopes = new_scopes
      self._DrawScopes()

    self._connection.DoRequest( scopes_consumer, {
      'command': 'scopes',
      'arguments': {
        'frameId': frame[ 'id' ]
      },
    } )

  def AddWatch( self, frame, expression ):
    watch = {
      'expression': expression,
      'context': 'watch',
    }
    if frame:
      watch[ 'frameId' ] = frame[ 'id' ]

    self._watches.append( Watch( watch ) )
    self.EvaluateWatches()

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

  def EvaluateWatches( self ):
    for watch in self._watches:
      self._connection.DoRequest(
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
      watch.result = WatchResult( message[ 'body' ] )

    if ( watch.result.IsExpandable() and
         watch.result.IsExpanded() ):
      self._connection.DoRequest( partial( self._ConsumeVariables,
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

    watch.result = WatchFailure( reason )
    self._DrawWatches()

  def ExpandVariable( self ):
    if vim.current.buffer == self._vars.buf:
      view = self._vars
    elif vim.current.buffer == self._watch.buf:
      view = self._watch
    else:
      return

    current_line = vim.current.window.cursor[ 0 ]
    if current_line not in view.lines:
      return

    variable = view.lines[ current_line ]

    if variable.IsExpanded():
      # Collapse
      variable.expanded = Expandable.COLLAPSED_BY_USER
      view.draw()
      return

    if not variable.IsExpandable():
      return

    variable.expanded = Expandable.EXPANDED_BY_USER
    self._connection.DoRequest( partial( self._ConsumeVariables,
                                         view.draw,
                                         variable ), {
      'command': 'variables',
      'arguments': {
        'variablesReference': variable.VariablesReference()
      },
    } )

  def _DrawVariables( self, view,  variables, indent ):
    assert indent > 0
    for variable in variables:
      line = utils.AppendToBuffer(
        view.buf,
        '{indent}{marker}{icon} {name} ({type_}): {value}'.format(
          # We borrow 1 space of indent to draw the change marker
          indent = ' ' * ( indent - 1 ),
          marker = '*' if variable.changed else ' ',
          icon = '+' if ( variable.IsExpandable()
                          and not variable.IsExpanded() ) else '-',
          name = variable.variable[ 'name' ],
          type_ = variable.variable.get( 'type', '' ),
          value = variable.variable.get( 'value',
                                         '<unknown>' ) ).split( '\n' ) )
      view.lines[ line ] = variable

      if variable.ShouldDrawDrillDown():
        self._DrawVariables( view, variable.variables, indent + 2 )

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
        utils.AppendToBuffer( self._watch.buf, 'Watches: ----' )
        for watch in self._watches:
          line = utils.AppendToBuffer( self._watch.buf,
                                       'Expression: '
                                       + watch.expression[ 'expression' ] )
          watch.line = line
          self._DrawWatchResult( 2, watch )

  def _DrawScope( self, indent, scope ):
    icon = '+' if scope.IsExpandable() and not scope.IsExpanded() else '-'

    line = utils.AppendToBuffer( self._vars.buf,
                                 '{0}{1} Scope: {2}'.format(
                                   ' ' * indent,
                                   icon,
                                   scope.scope[ 'name' ] ) )
    self._vars.lines[ line ] = scope

    if scope.ShouldDrawDrillDown():
      indent += 2
      self._DrawVariables( self._vars, scope.variables, indent )

  def _DrawWatchResult( self, indent, watch ):
    if not watch.result:
      return

    assert indent > 0
    icon = '+' if ( watch.result.IsExpandable() and
                    not watch.result.IsExpanded() ) else '-'

    line =  '{indent}{marker}{icon} Result: {result}'.format(
      # We borrow 1 space of indent to draw the change marker
      indent = ' ' * ( indent - 1 ),
      marker = '*' if watch.result.changed else ' ',
      icon = icon,
      result = watch.result.result.get( 'result', '<unknown>' ) )

    line = utils.AppendToBuffer( self._watch.buf, line.split( '\n' ) )
    self._watch.lines[ line ] = watch.result

    if watch.result.ShouldDrawDrillDown():
      indent = 4
      self._DrawVariables( self._watch, watch.result.variables, indent )

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
        variable = Variable( variable_body )
      else:
        variable.Update( variable_body )

      new_variables.append( variable )

      if variable.IsExpandable() and variable.IsExpanded():
        self._connection.DoRequest( partial( self._ConsumeVariables,
                                             draw,
                                             variable ), {
          'command': 'variables',
          'arguments': {
            'variablesReference': variable.VariablesReference()
          },
        } )

    parent.variables = new_variables

    draw()

  def ShowBalloon( self, frame, expression ):
    """Callback to display variable under cursor `:h ballonexpr`"""
    if not self._connection:
      return ''

    def handler( message ):
      # TODO: this result count be expandable, but we have no way to allow the
      # user to interact with the balloon to expand it, unless we use a popup
      # instead, but even then we don't really want to trap the cursor.
      body = message[ 'body' ]
      result = body[ 'result' ]
      if result is None:
        result = 'null'
      display = [
        'Type: ' + body.get( 'type', '<unknown>' ),
        'Value: ' + result
      ]
      utils.DisplayBaloon( self._is_term, display )

    def failure_handler( reason, message ):
      display = [ reason ]
      utils.DisplayBaloon( self._is_term, display )

    # Send async request
    self._connection.DoRequest( handler, {
      'command': 'evaluate',
      'arguments': {
        'expression': expression,
        'frameId': frame[ 'id' ],
        'context': 'hover',
      }
    }, failure_handler )

    # Return working (meanwhile)
    return '...'


  def SetSyntax( self, syntax ):
    self._current_syntax = utils.SetSyntax( self._current_syntax,
                                            syntax,
                                            self._vars.buf,
                                            self._watch.buf )

# vim: sw=2
