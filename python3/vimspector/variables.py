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
from collections import namedtuple
from functools import partial
import typing

from vimspector import utils

View = namedtuple( 'View', [ 'win', 'lines', 'draw' ] )



class Expandable:
  """Base for anything which might contain a hierarchy of values represented by
  a 'variablesReference' to be resolved by the 'variables' request. Records the
  current state expanded/collapsed. Implementations just implement
  VariablesReference to get the variables."""
  def __init__( self ):
    self.variables: typing.List[ 'Variable' ] = None
    # None is Falsy and represents collapsed _by default_. WHen set to False,
    # this means the user explicitly collapsed it. When True, the user expanded
    # it.
    self.expanded: bool = None

  def IsCollapsedByUser( self ):
    return self.expanded is False

  def IsExpandedByUser( self ):
    return self.expanded is True

  def ShouldDrawDrillDown( self ):
    return self.IsExpandedByUser() and self.variables is not None

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


class WatchResult( Expandable ):
  """Holds the result of a Watch expression with expand/collapse."""
  def __init__( self, result: dict ):
    super().__init__()
    self.result = result

  def VariablesReference( self ):
    return self.result.get( 'variablesReference', 0 )


class Variable( Expandable ):
  """Holds one level of an expanded value tree. Also itself expandable."""
  def __init__( self, variable: dict ):
    super().__init__()
    self.variable = variable

  def VariablesReference( self ):
    return self.variable.get( 'variablesReference', 0 )


class Watch:
  """Holds a user watch expression (DAP request) and the result (WatchResult)"""
  def __init__( self, expression: dict ):
    self.result: WatchResult

    self.expression = expression
    self.result = None


class VariablesView( object ):
  def __init__( self, connection, variables_win, watches_win ):
    self._logger = logging.getLogger( __name__ )
    utils.SetUpLogging( self._logger )

    self._vars = View( variables_win, {}, self._DrawScopes )
    self._watch = View( watches_win, {}, self._DrawWatches )
    self._connection = connection
    self._current_syntax = ''

    # Allows us to hit <CR> to expand/collapse variables
    with utils.LetCurrentWindow( self._vars.win ):
      vim.command(
        'nnoremap <buffer> <CR> :call vimspector#ExpandVariable()<CR>' )

    # List of current scopes of type Scope
    self._scopes: typing.List[ 'Scope' ] = []

    # List of current Watches of type Watch
    self._watches: typing.List[ 'Watch' ] = []

    # Allows us to hit <CR> to expand/collapse variables
    with utils.LetCurrentWindow( self._watch.win ):
      vim.command(
        'nnoremap <buffer> <CR> :call vimspector#ExpandVariable()<CR>' )
      vim.command(
        'nnoremap <buffer> <DEL> :call vimspector#DeleteWatch()<CR>' )

      vim.command( 'nnoremenu 1.1 WinBar.New '
                   ':call vimspector#AddWatch()<CR>' )
      vim.command( 'nnoremenu 1.2 WinBar.Expand/Collapse '
                   ':call vimspector#ExpandVariable()<CR>' )
      vim.command( 'nnoremenu 1.3 WinBar.Delete '
                   ':call vimspector#DeleteWatch()<CR>' )

    utils.SetUpScratchBuffer( self._vars.win.buffer, 'vimspector.Variables' )
    utils.SetUpPromptBuffer( self._watch.win.buffer,
                             'vimspector.Watches',
                             'Expression: ',
                             'vimspector#AddWatchPrompt' )

    utils.SetUpUIWindow( self._vars.win )
    utils.SetUpUIWindow( self._watch.win )

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
    with utils.ModifiableScratchBuffer( self._vars.win.buffer ):
      utils.ClearBuffer( self._vars.win.buffer )
    with utils.ModifiableScratchBuffer( self._watch.win.buffer ):
      utils.ClearBuffer( self._watch.win.buffer )
    self._current_syntax = ''

  def ConnectionUp( self, connection ):
    self._connection = connection

  def ConnectionClosed( self ):
    self.Clear()
    self._connection = None

  def Reset( self ):
    for k, v in self._oldoptions.items():
      vim.options[ k ] = v

    vim.command( 'bdelete! ' + str( self._watch.win.buffer.number ) )
    vim.command( 'bdelete! ' + str( self._vars.win.buffer.number ) )

  def LoadScopes( self, frame ):
    def scopes_consumer( message ):
      names = set()
      for scope_body in message[ 'body' ][ 'scopes' ]:
        # Find it in the scopes list
        found = False
        for index, s in enumerate( self._scopes ):
          if s.scope[ 'name' ] == scope_body[ 'name' ]:
            found = True
            s.scope = scope_body
            scope = s
            break

        if not found:
          scope = Scope( scope_body )
          self._scopes.append( scope )

        names.add( scope.scope[ 'name' ] )

        if not scope.scope[ 'expensive' ] and not scope.IsCollapsedByUser():
          # Expand any non-expensive scope which is not manually collapsed
          scope.expanded = True

        if scope.IsExpandedByUser():
          self._connection.DoRequest( partial( self._ConsumeVariables,
                                               self._DrawScopes,
                                               scope ), {
            'command': 'variables',
            'arguments': {
              'variablesReference': scope.scope[ 'variablesReference' ]
            },
          } )

      marked = []
      for index, s in enumerate( self._scopes ):
        if s.scope[ 'name' ] not in names:
          marked.append( index )
      for m in marked:
        self._scopes.pop( m )

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
    if vim.current.window != self._watch.win:
      utils.UserMessage( 'Not a watch window' )
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
      self._connection.DoRequest( partial( self._UpdateWatchExpression,
                                           watch ), {
        'command': 'evaluate',
        'arguments': watch.expression,
      } )

  def _UpdateWatchExpression( self, watch: Watch, message: dict ):
    if watch.result is not None:
      watch.result.result = message[ 'body' ]
    else:
      watch.result = WatchResult( message[ 'body' ] )

    if ( watch.result.IsExpandable() and
         watch.result.IsExpandedByUser() ):
      self._connection.DoRequest( partial( self._ConsumeVariables,
                                           self._watch.draw,
                                           watch.result.result ), {
        'command': 'variables',
        'arguments': {
          'variablesReference': watch.result.result[ 'variablesReference' ]
        },
      } )

    self._DrawWatches()

  def ExpandVariable( self ):
    if vim.current.window == self._vars.win:
      view = self._vars
    elif vim.current.window == self._watch.win:
      view = self._watch
    else:
      return

    current_line = vim.current.window.cursor[ 0 ]
    if current_line not in view.lines:
      return

    variable = view.lines[ current_line ]

    if variable.expanded:
      # Collapse
      variable.expanded = False
      view.draw()
      return

    if not variable.IsExpandable():
      return

    variable.expanded = True
    self._connection.DoRequest( partial( self._ConsumeVariables,
                                         view.draw,
                                         variable ), {
      'command': 'variables',
      'arguments': {
        'variablesReference': variable.VariablesReference()
      },
    } )

  def _DrawVariables( self, view,  variables, indent ):
    for variable in variables:
      line = utils.AppendToBuffer(
        view.win.buffer,
        '{indent}{icon} {name} ({type_}): {value}'.format(
          indent = ' ' * indent,
          icon = '+' if ( variable.IsExpandable()
                          and not variable.IsExpandedByUser() ) else '-',
          name = variable.variable[ 'name' ],
          type_ = variable.variable.get( 'type', '<unknown type>' ),
          value = variable.variable.get( 'value',
                                         '<unknown value>' ) ).split( '\n' ) )
      view.lines[ line ] = variable

      if variable.ShouldDrawDrillDown():
        self._DrawVariables( view, variable.variables, indent + 2 )

  def _DrawScopes( self ):
    # FIXME: The drawing is dumb and draws from scratch every time. This is
    # simple and works and makes sure the line-map is always correct.
    # However it is really inefficient, and makes it so that expanded results
    # are collapsed on every step.
    self._vars.lines.clear()
    with utils.RestoreCursorPosition():
      with utils.ModifiableScratchBuffer( self._vars.win.buffer ):
        utils.ClearBuffer( self._vars.win.buffer )
        for scope in self._scopes:
          self._DrawScope( 0, scope )

  def _DrawWatches( self ):
    # FIXME: The drawing is dumb and draws from scratch every time. This is
    # simple and works and makes sure the line-map is always correct.
    # However it is really inefficient, and makes it so that expanded results
    # are collapsed on every step.
    self._watch.lines.clear()
    with utils.RestoreCursorPosition():
      with utils.ModifiableScratchBuffer( self._watch.win.buffer ):
        utils.ClearBuffer( self._watch.win.buffer )
        utils.AppendToBuffer( self._watch.win.buffer, 'Watches: ----' )
        for watch in self._watches:
          line = utils.AppendToBuffer( self._watch.win.buffer,
                                       'Expression: '
                                       + watch.expression[ 'expression' ] )
          watch.line = line
          self._DrawWatchResult( 2, watch )

  def _DrawScope( self, indent, scope ):
    icon = '+' if scope.IsExpandable() and not scope.IsExpandedByUser() else '-'

    line = utils.AppendToBuffer( self._vars.win.buffer,
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

    icon = '+' if ( watch.result.IsExpandable() and
                    not watch.result.IsExpandedByUser() ) else '-'

    result_str = watch.result.result[ 'result' ]
    if result_str is None:
      result_str = '<unknown>'

    line =  '{0}{1} Result: {2}'.format( ' ' * indent, icon, result_str )
    line = utils.AppendToBuffer( self._watch.win.buffer, line.split( '\n' ) )
    self._watch.lines[ line ] = watch.result

    if watch.result.ShouldDrawDrillDown():
      indent = 4
      self._DrawVariables( self._watch, watch.result.variables, indent )

  def _ConsumeVariables( self, draw, parent, message ):
    names = set()

    for variable_body in message[ 'body' ][ 'variables' ]:
      if parent.variables is None:
        parent.variables = []

      # Find the variable in parent
      found = False
      for index, v in enumerate( parent.variables ):
        if v.variable[ 'name' ] == variable_body[ 'name' ]:
          v.variable = variable_body
          variable = v
          found = True
          break

      if not found:
        variable = Variable( variable_body )
        parent.variables.append( variable )

      names.add( variable.variable[ 'name' ] )

      if variable.IsExpandable() and variable.IsExpandedByUser():
        self._connection.DoRequest( partial( self._ConsumeVariables,
                                             draw,
                                             variable ), {
          'command': 'variables',
          'arguments': {
            'variablesReference': variable.VariablesReference()
          },
        } )

    # Delete any variables from parent not seen in this pass
    if parent.variables:
      marked = []
      for index, v in enumerate( parent.variables ):
        if v.variable[ 'name' ] not in names:
          marked.append( index )
      for m in marked:
        parent.variables.pop( m )

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
                                            self._vars.win,
                                            self._watch.win )

# vim: sw=2
