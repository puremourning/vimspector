#!/usr/bin/env python3

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

import sys

if sys.version_info.major < 3:
  sys.exit( "You need to run this with python 3. Your version is " +
            '.'.join( map( str, sys.version_info[ :3 ] ) ) )

import argparse
import os
import json
import functools
import operator
import glob

# Include vimspector source, for utils
sys.path.insert( 1, os.path.join( os.path.dirname( __file__ ),
                                  'python3' ) )

from vimspector import install, installer, gadgets
from vimspector.vendor.json_minify import minify

# ------------------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------------------


parser = argparse.ArgumentParser(
  formatter_class = argparse.RawDescriptionHelpFormatter,
  description = 'Install DAP Servers for use with Vimspector.',
  epilog =
    """
    If you're not sure, normally --all is enough to get started.

    Custom server definitions can be defined in JSON files, allowing
    installation of arbitrary servers packaged in one of the ways that this
    installer understands.

    The format of the file can be found on the Vimspector reference guide:
    https://puremourning.github.io/vimspector

    NOTE: This script should usually _not_ be run under `sudo` or as root. It
    downloads and extracts things only to directories under its own path. No
    system files or folders are chnaged by this script. If you really want to
    run under sudo, pass --sudo, but this is _almost certainly_ the wrong thing
    to do.
    """
)
parser.add_argument( '--all',
                     action = 'store_true',
                     help = 'Enable all supported completers' )

parser.add_argument( '--force-all',
                     action = 'store_true',
                     help = 'Enable all unsupported completers' )

parser.add_argument( '--upgrade',
                     action = 'store_true',
                     help = 'Only update adapters changed from the manifest' )

parser.add_argument( '--quiet',
                     action = 'store_true',
                     help = 'Suppress installation output' )

parser.add_argument( '--verbose',
                     action = 'store_true',
                     help = 'Force installation output' )

parser.add_argument( '--basedir',
                     action = 'store',
                     help = 'Advanced option. '
                            'Base directory under which to keep gadgets, '
                            'configurations, etc.. Default: vimspector '
                            'installation dir. Useful for developers or '
                            'multi-user installations' )

parser.add_argument( '--no-gadget-config',
                     action = 'store_true',
                     help = "Don't write the .gagets.json, just install" )

parser.add_argument( '--update-gadget-config',
                     action = 'store_true',
                     help =
                       "Update the gadget config rather than overwrite it" )

parser.add_argument( '--enable-custom',
                     dest='custom_gadget_file',
                     action='append',
                     nargs='*',
                     default = [],
                     help = 'Read custom gadget from supplied file. This '
                            'can be supplied multiple times and each time '
                            'multiple files can be passed.' )

parser.add_argument( '--sudo',
                     action='store_true',
                     help = "If you're really really really sure you want to "
                            "run this as root via sudo, pass this flag." )

done_languages = set()
for name, gadget in gadgets.Gadgets().items():
  lang = gadget[ 'language' ]
  if lang in done_languages:
    continue

  done_languages.add( lang )
  if not gadget.get( 'enabled', True ):
    parser.add_argument(
      '--force-enable-' + lang,
      action = 'store_true',
      help = 'Install the unsupported {} debug adapter for {} support'.format(
        name,
        lang ) )
    continue

  parser.add_argument(
    '--enable-' + lang,
    action = 'store_true',
    help = 'Install the {} debug adapter for {} support'.format(
      name,
      lang ) )

  parser.add_argument(
    '--disable-' + lang,
    action = 'store_true',
    help = "Don't install the {} debug adapter for {} support "
           '(when supplying --all)'.format( name, lang ) )

parser.add_argument(
    "--no-check-certificate",
    action = "store_true",
    help = "Do not verify SSL certificates for file downloads."
)

args = parser.parse_args()

installer.AbortIfSUperUser( args.sudo )

vimspector_base = os.path.dirname( __file__ )
if args.basedir:
  vimspector_base = os.path.abspath( args.basedir )

install.MakeInstallDirs( vimspector_base )
installer.Configure( vimspector_base = vimspector_base,
                     quiet = args.quiet and not args.verbose,
                     no_check_certificate = args.no_check_certificate )

if args.force_all and not args.all:
  args.all = True

CUSTOM_GADGETS = {}
custom_files = glob.glob( os.path.join( vimspector_base,
                                        'gadgets',
                                        'custom',
                                        '*.json' ) )
for custom_file_name in functools.reduce( operator.add,
                                          args.custom_gadget_file,
                                          custom_files ):
  with open( custom_file_name, 'r' ) as custom_file:
    CUSTOM_GADGETS.update( json.loads( minify( custom_file.read() ) ) )


failed = []
succeeded = []
all_adapters = installer.ReadAdapters(
  read_existing = args.update_gadget_config )
manifest = installer.Manifest()

for name, gadget in gadgets.Gadgets().items():
  if not gadget.get( 'enabled', True ):
    if ( not args.force_all
         and not getattr( args, 'force_enable_' + gadget[ 'language' ] ) ):
      continue
  else:
    if not args.all and not getattr( args, 'enable_' + gadget[ 'language' ] ):
      continue
    if getattr( args, 'disable_' + gadget[ 'language' ] ):
      continue

  if not args.upgrade:
    manifest.Clear( name )

  installer.InstallGagdet( name,
                           gadget,
                           manifest,
                           succeeded,
                           failed,
                           all_adapters )


for name, gadget in CUSTOM_GADGETS.items():
  if not args.upgrade:
    manifest.Clear( name )

  installer.InstallGagdet( name,
                           gadget,
                           manifest,
                           succeeded,
                           failed,
                           all_adapters )

if args.no_gadget_config:
  print( "" )
  print( "Would write the following gadgets: " )
  installer.WriteAdapters( all_adapters, to_file = sys.stdout )
else:
  installer.WriteAdapters( all_adapters )

manifest.Write()

if args.basedir:
  print( "" )
  print( "***NOTE***: You set --basedir to " + args.basedir +
         ". Therefore you _must_ ensure this is in your vimrc:\n"
         "let g:vimspector_base_dir='" + vimspector_base + "'" )

if succeeded:
  print( "Done" )
  print( "The following adapters were installed successfully:\n - {}".format(
    '\n - '.join( succeeded ) ) )

if failed:
  sys.exit( 'Failed to install adapters:\n * {}{}'.format(
    '\n * '.join( failed ),
    "\nRe-run with --verbose for more info on failures"
       if args.quiet and not args.verbose else '' ) )
