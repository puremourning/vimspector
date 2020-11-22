# vimspector - A multi-language debugging system for Vim
# Copyright 2019 Ben Jackson
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

from collections import defaultdict

import abc
import vim
import os
import logging

import json
from vimspector import utils, signs


class ServerBreakpointHandler( object ):
  @abc.abstractmethod
  def ClearBreakpoints( self ):
    pass

  @abc.abstractmethod
  def AddBreakpoints( self, source, message ):
    pass


class ProjectBreakpoints( object ):
  def __init__( self ):
    self._connection = None
    self._logger = logging.getLogger( __name__ )
    utils.SetUpLogging( self._logger )

    # These are the user-entered breakpoints.
    self._line_breakpoints = defaultdict( list )
    self._func_breakpoints = []
    self._exception_breakpoints = None
    self._configured_breakpoints = {}

    # FIXME: Remove this. Remove breakpoints nonesense from code.py
    self._breakpoints_handler = None
    self._server_capabilities = {}

    self._next_sign_id = 1

    if not signs.SignDefined( 'vimspectorBP' ):
      signs.DefineSign( 'vimspectorBP',
                        text = '●',
                        double_text = '●',
                        texthl = 'WarningMsg' )

    if not signs.SignDefined( 'vimspectorBPCond' ):
      signs.DefineSign( 'vimspectorBPCond',
                        text = '◆',
                        double_text = '◆',
                        texthl = 'WarningMsg' )

    if not signs.SignDefined( 'vimspectorBPDisabled' ):
      signs.DefineSign( 'vimspectorBPDisabled',
                        text = '●',
                        double_text = '●',
                        texthl = 'LineNr' )


  def ConnectionUp( self, connection ):
    self._connection = connection


  def SetServerCapabilities( self, server_capabilities ):
    self._server_capabilities = server_capabilities


  def ConnectionClosed( self ):
    self._breakpoints_handler = None
    self._server_capabilities = {}
    self._connection = None
    self.UpdateUI()

    # NOTE: we don't reset self._exception_breakpoints because we don't want to
    # re-ask the user every time for the sane info.

    # FIXME: If the adapter type changes, we should probably forget this ?


  def BreakpointsAsQuickFix( self ):
    # FIXME: Handling of breakpoints is a mess, split between _codeView and this
    # object. This makes no sense and should be centralised so that we don't
    # have this duplication and bug factory.
    qf = []
    if self._connection and self._codeView:
      qf = self._codeView.BreakpointsAsQuickFix()
    else:
      for file_name, breakpoints in self._line_breakpoints.items():
        for bp in breakpoints:
          self._SignToLine( file_name, bp )
          qf.append( {
            'filename': file_name,
            'lnum': bp[ 'line' ],
            'col': 1,
            'type': 'L',
            'valid': 1 if bp[ 'state' ] == 'ENABLED' else 0,
            'text': "Line breakpoint - {}: {}".format(
              bp[ 'state' ],
              json.dumps( bp[ 'options' ] ) )
          } )
      # I think this shows that the qf list is not right for this.
      for bp in self._func_breakpoints:
        qf.append( {
          'filename': '',
          'lnum': 1,
          'col': 1,
          'type': 'F',
          'valid': 1,
          'text': "Function breakpoint: {}: {}".format( bp[ 'function' ],
                                                        bp[ 'options' ] ),
        } )

    return qf


  def ClearBreakpoints( self ):
    # These are the user-entered breakpoints.
    for file_name, breakpoints in self._line_breakpoints.items():
      for bp in breakpoints:
        self._SignToLine( file_name, bp )
        if 'sign_id' in bp:
          signs.UnplaceSign( bp[ 'sign_id' ], 'VimspectorBP' )

    self._line_breakpoints = defaultdict( list )
    self._func_breakpoints = []
    self._exception_breakpoints = None

    self.UpdateUI()

  def _FindLineBreakpoint( self, file_name, line ):
    file_name = os.path.abspath( file_name )
    for index, bp in enumerate( self._line_breakpoints[ file_name ] ):
      self._SignToLine( file_name, bp )
      if bp[ 'line' ] == line:
        return bp, index

    return None, None


  def _PutLineBreakpoint( self, file_name, line, options ):
    self._line_breakpoints[ os.path.abspath( file_name ) ].append( {
      'state': 'ENABLED',
      'line': line,
      'options': options,
      # 'sign_id': <filled in when placed>,
      #
      # Used by other breakpoint types (specified in options):
      # 'condition': ...,
      # 'hitCondition': ...,
      # 'logMessage': ...
    } )


  def _DeleteLineBreakpoint( self, bp, file_name, index ):
    if 'sign_id' in bp:
      signs.UnplaceSign( bp[ 'sign_id' ], 'VimspectorBP' )
    del self._line_breakpoints[ os.path.abspath( file_name ) ][ index ]


  def ToggleBreakpoint( self, options ):
    line, _ = vim.current.window.cursor
    file_name = vim.current.buffer.name

    if not file_name:
      return

    bp, index = self._FindLineBreakpoint( file_name, line )
    if bp is None:
      # ADD
      self._PutLineBreakpoint( file_name, line, options )
    elif bp[ 'state' ] == 'ENABLED' and not self._connection:
      # DISABLE
      bp[ 'state' ] = 'DISABLED'
    else:
      # DELETE
      self._DeleteLineBreakpoint( bp, file_name, index )

    self.UpdateUI()


  def SetLineBreakpoint( self, file_name, line_num, options, then = None ):
    bp, _ = self._FindLineBreakpoint( file_name, line_num )
    if bp is not None:
      bp[ 'options' ] = options
      return
    self._PutLineBreakpoint( file_name, line_num, options )
    self.UpdateUI( then )


  def ClearLineBreakpoint( self, file_name, line_num ):
    bp, index = self._FindLineBreakpoint( file_name, line_num )
    if bp is None:
      return
    self._DeleteLineBreakpoint( bp, file_name, index )
    self.UpdateUI()


  def ClearTemporaryBreakpoint( self, file_name, line_num ):
    bp, index = self._FindLineBreakpoint( file_name, line_num )
    if bp is None:
      return
    if bp[ 'options' ].get( 'temporary' ):
      self._DeleteLineBreakpoint( bp, file_name, index )
      self.UpdateUI()


  def ClearTemporaryBreakpoints( self ):
    to_delete = []
    for file_name, breakpoints in self._line_breakpoints.items():
      for index, bp in enumerate( breakpoints ):
        if bp[ 'options' ].get( 'temporary' ):
          to_delete.append( ( bp, file_name, index ) )

    for entry in to_delete:
      self._DeleteLineBreakpoint( *entry )


  def _UpdateTemporaryBreakpoints( self, breakpoints, temp_idxs ):
    # adjust any temporary breakpoints to match the server result
    # TODO: Maybe now is the time to ditch the split breakpoints nonesense
    for temp_idx, user_bp in temp_idxs:
      if temp_idx >= len( breakpoints ):
        # Just can't trust servers ?
        self._logger.debug( "Server Error - invalid breakpoints list did not "
                            "contain entry for temporary breakpoint at index "
                            f"{ temp_idx } i.e. { user_bp }" )
        continue

      bp = breakpoints[ temp_idx ]

      if 'line' not in bp or not bp[ 'verified' ]:
        utils.UserMessage(
          "Unable to set temporary breakpoint at line "
          f"{ user_bp[ 'line' ] } execution will continue...",
          persist = True,
          error = True )

      self._logger.debug( f"Updating temporary breakpoint { user_bp } line "
                          f"{ user_bp[ 'line' ] } to { bp[ 'line' ] }" )

      # if it was moved, update the user-breakpoint so that we unset it
      # again properly
      user_bp[ 'line' ] = bp[ 'line' ]



  def AddFunctionBreakpoint( self, function, options ):
    self._func_breakpoints.append( {
      'state': 'ENABLED',
      'function': function,
      'options': options,
      # Specified in options:
      # 'condition': ...,
      # 'hitCondition': ...,
    } )

    # TODO: We don't really have aanything to update here, but if we're going to
    # have a UI list of them we should update that at this point
    self.UpdateUI()


  def UpdateUI( self, then = None ):
    if self._connection:
      self.SendBreakpoints( then )
    else:
      self._ShowBreakpoints()
      if then:
        then()


  def SetBreakpointsHandler( self, handler ):
    # FIXME: Remove this temporary compat .layer
    self._breakpoints_handler = handler


  def SetConfiguredBreakpoints( self, configured_breakpoints ):
    self._configured_breakpoints = configured_breakpoints


  def SendBreakpoints( self, doneHandler = None ):
    assert self._breakpoints_handler is not None

    # Clear any existing breakpoints prior to sending new ones
    self._breakpoints_handler.ClearBreakpoints()

    awaiting = 0

    def response_received( *failure_args ):
      nonlocal awaiting
      awaiting = awaiting - 1

      if failure_args and self._connection:
        reason, msg = failure_args
        utils.UserMessage( 'Unable to set breakpoint: {0}'.format( reason ),
                           persist = True,
                           error = True )

      if awaiting == 0 and doneHandler:
        doneHandler()

    def response_handler( source, msg, temp_idxs = [] ):
      if msg:
        self._breakpoints_handler.AddBreakpoints( source, msg )

        breakpoints = ( msg.get( 'body' ) or {} ).get( 'breakpoints' ) or []
        self._UpdateTemporaryBreakpoints( breakpoints, temp_idxs )
      response_received()


    # NOTE: Must do this _first_ otherwise we might send requests and get
    # replies before we finished sending all the requests.
    if self._exception_breakpoints is None:
      self._SetUpExceptionBreakpoints( self._configured_breakpoints )


    # TODO: add the _configured_breakpoints to line_breakpoints

    for file_name, line_breakpoints in self._line_breakpoints.items():
      temp_idxs = []
      breakpoints = []
      for bp in line_breakpoints:
        self._SignToLine( file_name, bp )
        if 'sign_id' in bp:
          signs.UnplaceSign( bp[ 'sign_id' ], 'VimspectorBP' )
          del bp[ 'sign_id' ]

        if bp[ 'state' ] != 'ENABLED':
          continue

        dap_bp = {}
        dap_bp.update( bp[ 'options' ] )
        dap_bp.update( { 'line': bp[ 'line' ] } )

        dap_bp.pop( 'temporary', None )

        if bp[ 'options' ].get( 'temporary' ):
          temp_idxs.append( [ len( breakpoints ), bp ] )

        breakpoints.append( dap_bp )


      source = {
        'name': os.path.basename( file_name ),
        'path': file_name,
      }

      awaiting = awaiting + 1
      self._connection.DoRequest(
        # The source=source here is critical to ensure that we capture each
        # source in the iteration, rather than ending up passing the same source
        # to each callback.
        lambda msg, source=source, temp_idxs=temp_idxs: response_handler(
          source,
          msg,
          temp_idxs = temp_idxs ),
        {
          'command': 'setBreakpoints',
          'arguments': {
            'source': source,
            'breakpoints': breakpoints,
          },
          'sourceModified': False, # TODO: We can actually check this
        },
        failure_handler = response_received
      )

    # TODO: Add the _configured_breakpoints to function breakpoints

    if self._server_capabilities.get( 'supportsFunctionBreakpoints' ):
      awaiting = awaiting + 1
      breakpoints = []
      for bp in self._func_breakpoints:
        if bp[ 'state' ] != 'ENABLED':
          continue
        dap_bp = {}
        dap_bp.update( bp[ 'options' ] )
        dap_bp.update( { 'name': bp[ 'function' ] } )
        breakpoints.append( dap_bp )

      self._connection.DoRequest(
        lambda msg: response_handler( None, msg ),
        {
          'command': 'setFunctionBreakpoints',
          'arguments': {
            'breakpoints': breakpoints,
          }
        },
        failure_handler = response_received
      )

    if self._exception_breakpoints:
      awaiting = awaiting + 1
      self._connection.DoRequest(
        lambda msg: response_handler( None, None ),
        {
          'command': 'setExceptionBreakpoints',
          'arguments': self._exception_breakpoints
        },
        failure_handler = response_received
      )

    if awaiting == 0 and doneHandler:
      doneHandler()


  def _SetUpExceptionBreakpoints( self, configured_breakpoints ):
    exception_breakpoint_filters = self._server_capabilities.get(
        'exceptionBreakpointFilters',
        [] )

    if exception_breakpoint_filters or not self._server_capabilities.get(
      'supportsConfigurationDoneRequest' ):
      # Note the supportsConfigurationDoneRequest part: prior to there being a
      # configuration done request, the "exception breakpoints" request was the
      # indication that configuraiton was done (and its response is used to
      # trigger requesting threads etc.). See the note in
      # debug_session.py:_Initialise for more detials
      exception_filters = []
      configured_filter_options = configured_breakpoints.get( 'exception', {} )
      if exception_breakpoint_filters:
        for f in exception_breakpoint_filters:
          default_value = 'Y' if f.get( 'default' ) else 'N'

          if f[ 'filter' ] in configured_filter_options:
            result = configured_filter_options[ f[ 'filter' ] ]

            if isinstance( result, bool ):
              result = 'Y' if result else 'N'

            if not isinstance( result, str ) or result not in ( 'Y', 'N', '' ):
              raise ValueError(
                f"Invalid value for exception breakpoint filter '{f}': "
                f"'{result}'. Must be boolean, 'Y', 'N' or '' (default)" )
          else:
            result = utils.AskForInput(
              "{}: Break on {} (Y/N/default: {})? ".format( f[ 'filter' ],
                                                            f[ 'label' ],
                                                            default_value ),
              default_value )

          if result == 'Y':
            exception_filters.append( f[ 'filter' ] )
          elif not result and f.get( 'default' ):
            exception_filters.append( f[ 'filter' ] )

      self._exception_breakpoints = {
        'filters': exception_filters
      }

      if self._server_capabilities.get( 'supportsExceptionOptions' ):
        # TODO: There are more elaborate exception breakpoint options here, but
        # we don't support them. It doesn't seem like any of the servers really
        # pay any attention to them anyway.
        self._exception_breakpoints[ 'exceptionOptions' ] = []


  def Refresh( self, file_name ):
    # TODO: Just this file ?
    self._ShowBreakpoints()


  def _ShowBreakpoints( self ):
    for file_name, line_breakpoints in self._line_breakpoints.items():
      for bp in line_breakpoints:
        self._SignToLine( file_name, bp )
        if 'sign_id' in bp:
          signs.UnplaceSign( bp[ 'sign_id' ], 'VimspectorBP' )
        else:
          bp[ 'sign_id' ] = self._next_sign_id
          self._next_sign_id += 1

        sign = ( 'vimspectorBPDisabled' if bp[ 'state' ] != 'ENABLED'
                 else 'vimspectorBPCond' if 'condition' in bp[ 'options' ]
                 else 'vimspectorBP' )

        if utils.BufferExists( file_name ):
          signs.PlaceSign( bp[ 'sign_id' ],
                           'VimspectorBP',
                           sign,
                           file_name,
                           bp[ 'line' ] )


  def _SignToLine( self, file_name, bp ):
    if 'sign_id' not in bp:
      return bp[ 'line' ]

    if not utils.BufferExists( file_name ):
      return bp[ 'line' ]

    signs = vim.eval( "sign_getplaced( '{}', {} )".format(
      utils.Escape( file_name ),
      json.dumps( { 'id': bp[ 'sign_id' ], 'group': 'VimspectorBP', } ) ) )

    if len( signs ) == 1 and len( signs[ 0 ][ 'signs' ] ) == 1:
      bp[ 'line' ] = int( signs[ 0 ][ 'signs' ][ 0 ][ 'lnum' ] )

    return bp[ 'line' ]
