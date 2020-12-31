# vimspector - A multi-language debugging system for Vim
# Copyright 2020 Ben Jackson
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

import os
import logging
import json
import glob
import shlex

from vimspector import install, installer, utils, gadgets
from vimspector.vendor.json_minify import minify

_logger = logging.getLogger( __name__ )
utils.SetUpLogging( _logger )

# We cache this once, and don't allow it to change (FIXME?)
VIMSPECTOR_HOME = utils.GetVimspectorBase()

# cache of what the user entered for any option we ask them
USER_CHOICES = {}



def GetAdapters( current_file ):
  adapters = {}
  for gadget_config_file in PathsToAllGadgetConfigs( VIMSPECTOR_HOME,
                                                     current_file ):
    _logger.debug( f'Reading gadget config: {gadget_config_file}' )
    if not gadget_config_file or not os.path.exists( gadget_config_file ):
      continue

    with open( gadget_config_file, 'r' ) as f:
      a =  json.loads( minify( f.read() ) ).get( 'adapters' ) or {}
      adapters.update( a )

  return adapters


def PathsToAllGadgetConfigs( vimspector_base, current_file ):
  yield install.GetGadgetConfigFile( vimspector_base )
  for p in sorted( glob.glob(
    os.path.join( install.GetGadgetConfigDir( vimspector_base ),
                  '*.json' ) ) ):
    yield p

  yield utils.PathToConfigFile( '.gadgets.json',
                                os.path.dirname( current_file ) )


def GetConfigurations( adapters, current_file, filetypes ):
  configurations = {}
  for launch_config_file in PathsToAllConfigFiles( VIMSPECTOR_HOME,
                                                   current_file,
                                                   filetypes ):
    _logger.debug( f'Reading configurations from: {launch_config_file}' )
    if not launch_config_file or not os.path.exists( launch_config_file ):
      continue

    with open( launch_config_file, 'r' ) as f:
      database = json.loads( minify( f.read() ) )
      configurations.update( database.get( 'configurations' ) or {} )
      adapters.update( database.get( 'adapters' ) or {} )

  # We return the last config file inspected which is the most specific one
  # (i.e. the project-local one)
  return launch_config_file, configurations


def PathsToAllConfigFiles( vimspector_base, current_file, filetypes ):
  for ft in filetypes + [ '_all' ]:
    for p in sorted( glob.glob(
      os.path.join( install.GetConfigDirForFiletype( vimspector_base, ft ),
                    '*.json' ) ) ):
      yield p

  for ft in filetypes:
    yield utils.PathToConfigFile( f'.vimspector.{ft}.json',
                                  os.path.dirname( current_file ) )

  yield utils.PathToConfigFile( '.vimspector.json',
                                os.path.dirname( current_file ) )


def SelectConfiguration( launch_variables, configurations ):
  if 'configuration' in launch_variables:
    configuration_name = launch_variables.pop( 'configuration' )
  elif ( len( configurations ) == 1 and
         next( iter( configurations.values() ) ).get( "autoselect", True ) ):
    configuration_name = next( iter( configurations.keys() ) )
  else:
    # Find a single configuration with 'default' True and autoselect not False
    defaults = { n: c for n, c in configurations.items()
                 if c.get( 'default', False ) is True
                 and c.get( 'autoselect', True ) is not False }

    if len( defaults ) == 1:
      configuration_name = next( iter( defaults.keys() ) )
    else:
      configuration_name = utils.SelectFromList(
        'Which launch configuration?',
        sorted( configurations.keys() ) )

  if not configuration_name or configuration_name not in configurations:
    return None, None

  configuration = configurations[ configuration_name ]

  return configuration_name, configuration


def SuggestConfiguration( current_file, filetypes ):
  nothing = None, None
  templates = []
  filetypes = set( filetypes )

  for gadget_name, gadget in gadgets.GADGETS.items():
    spec = {}
    spec.update( gadget.get( 'all', {} ) )
    spec.update( gadget.get( install.GetOS(), {} ) )

    for template in spec.get( 'templates', [] ):
      if filetypes.intersection( template.get( 'filetypes', set() ) ):
        templates.append( template )

  if not templates:
    return nothing

  template_idx = utils.SelectFromList(
    'No debug configurations were found for this project, '
    'Would you like to use one of the following templates?',
    [ t[ 'description' ] for t in templates ],
    ret = 'index' )

  if template_idx is None:
    return nothing

  template = templates[ template_idx ]

  config_index = utils.SelectFromList(
    'Which configuration?',
    [ c[ 'description' ] for c in template[ 'configurations' ] ],
    ret = 'index' )

  if config_index is None:
    return nothing

  configuration = template[ 'configurations' ][ config_index ]
  configuration_name = utils.AskForInput( 'Give the config a name: ',
                                          configuration[ 'description' ] )

  configuration[ 'launch_configuration' ][ 'generated' ] = {
    'name': configuration_name,
    'path': os.path.join( os.path.dirname( current_file ), '.vimspector.json' ),
  }

  return configuration_name, configuration[ 'launch_configuration' ]


def SaveConfiguration( configuration ):
  gen = configuration.pop( 'generated', None )
  if not gen:
    return

  if utils.Confirm(
    f'Would you like to save the configuration named "{ gen[ "name" ] }"',
    '&Yes\n&No' ) != 1:
    return

  config_path = utils.AskForInput( 'Enter the path to save to: ',
                                   gen[ 'path' ] )

  if not config_path:
    return

  os.makedirs( os.path.dirname( config_path ), exist_ok = True )
  current_contents = {}

  if os.path.exists( config_path ):
    if utils.Confirm( 'File exists, overwrite?\n(NOTE: comments and '
                      'formatting in the existing file will be LOST!!)',
                      '&Yes\n&No' ) == 1:
      with open( config_path, 'r' ) as f:
        current_contents = json.loads( minify( f.read() ) )

  # TODO: how much of configuration is mangled at this point ?
  # TODO: how about the defaulted arguments? All the refs are replaced at this
  # point?
  current_contents.setdefault( 'configurations', {} )
  current_contents[ 'configurations' ][ gen[ 'name' ] ] = configuration

  with open( config_path, 'w' ) as f:
    json.dump( current_contents, f, indent=2 )

  utils.UserMessage( f'Wrote { config_path }.', persist = True )


def SelectAdapter( api_prefix,
                   debug_session,
                   configuration_name,
                   configuration,
                   adapters,
                   launch_variables ):
  adapter = configuration.get( 'adapter' )

  if isinstance( adapter, str ):
    adapter_dict = adapters.get( adapter )

    if adapter_dict is None:
      suggested_gadgets = installer.FindGadgetForAdapter( adapter )
      if suggested_gadgets:
        response = utils.AskForInput(
          f"The specified adapter '{adapter}' is not "
           "installed. Would you like to install the following gadgets? ",
          ' '.join( suggested_gadgets ) )
        if response:
          new_launch_variables = dict( launch_variables )
          new_launch_variables[ 'configuration' ] = configuration_name

          installer.RunInstaller(
            api_prefix,
            False, # Don't leave open
            *shlex.split( response ),
            then = debug_session.Start( new_launch_variables ) )
          return None
        elif response is None:
          return None

      utils.UserMessage( f"The specified adapter '{adapter}' is not "
                         "available. Did you forget to run "
                         "'install_gadget.py'?",
                         persist = True,
                         error = True )
      return None

    adapter = adapter_dict

  return adapter


def ResolveConfiguration( adapter,
                          configuration,
                          launch_variables,
                          workspace_root,
                          current_file ):
  # Additional vars as defined by VSCode:
  #
  # ${workspaceFolder} - the path of the folder opened in VS Code
  # ${workspaceFolderBasename} - the name of the folder opened in VS Code
  #                              without any slashes (/)
  # ${file} - the current opened file
  # ${relativeFile} - the current opened file relative to workspaceFolder
  # ${fileBasename} - the current opened file's basename
  # ${fileBasenameNoExtension} - the current opened file's basename with no
  #                              file extension
  # ${fileDirname} - the current opened file's dirname
  # ${fileExtname} - the current opened file's extension
  # ${cwd} - the task runner's current working directory on startup
  # ${lineNumber} - the current selected line number in the active file
  # ${selectedText} - the current selected text in the active file
  # ${execPath} - the path to the running VS Code executable
  def relpath( p, relative_to ):
    if not p:
      return ''
    return os.path.relpath( p, relative_to )

  def splitext( p ):
    if not p:
      return [ '', '' ]
    return os.path.splitext( p )

  variables = {
    'dollar': '$', # HACK. Hote '$$' also works.
    'workspaceRoot': workspace_root,
    'workspaceFolder': workspace_root,
    'gadgetDir': install.GetGadgetDir( VIMSPECTOR_HOME ),
    'file': current_file,
  }

  calculus = {
    'relativeFile': lambda: relpath( current_file, workspace_root ),
    'fileBasename': lambda: os.path.basename( current_file ),
    'fileBasenameNoExtension':
      lambda: splitext( os.path.basename( current_file ) )[ 0 ],
    'fileDirname': lambda: os.path.dirname( current_file ),
    'fileExtname': lambda: splitext( os.path.basename( current_file ) )[ 1 ],
    # NOTE: this is the window-local cwd for the current window, *not* Vim's
    # working directory.
    'cwd': os.getcwd,
    'unusedLocalPort': utils.GetUnusedLocalPort,
  }

  # Pretend that vars passed to the launch command were typed in by the user
  # (they may have been in theory)
  USER_CHOICES.update( launch_variables )
  variables.update( launch_variables )

  variables.update(
    utils.ParseVariables( adapter.get( 'variables', {} ),
                          variables,
                          calculus,
                          USER_CHOICES ) )
  variables.update(
    utils.ParseVariables( configuration.get( 'variables', {} ),
                          variables,
                          calculus,
                          USER_CHOICES ) )


  utils.ExpandReferencesInDict( configuration,
                                variables,
                                calculus,
                                USER_CHOICES )
  utils.ExpandReferencesInDict( adapter,
                                variables,
                                calculus,
                                USER_CHOICES )
