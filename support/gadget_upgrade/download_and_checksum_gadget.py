#!/usr/bin/env python3

import sys
import os
import string
import fnmatch

if '--help' in sys.argv:
  print( f"Usage: { os.path.basename( __file__ ) } [-v] gadget [gadget2 ...]" )
  print( "" )
  print( "Each gadget is a glob (fnmatch), so use * to do all " )
  exit(0)

VERBOSE = 0
if '-v' in sys.argv:
  VERBOSE = 1
  sys.argv = list( filter( lambda x: x != "-v", sys.argv ) )

# Gaim access to vimspector libs
sys.path.insert(
  1,
  os.path.abspath( os.path.join( os.path.dirname( __file__ ),
                                 '..',
                                 '..',
                                 'python3' ) )
)

from vimspector import install, installer, gadgets

gadgets_to_sum = sys.argv[ 1: ]
results = []

for gadget_name in gadgets.GADGETS.keys():
  include = False
  for requested_gadget in gadgets_to_sum:
    if fnmatch.fnmatch( gadget_name, requested_gadget ):
      include = True
      break

  if not include:
    if VERBOSE:
      print( f"Skipping { gadget_name } (not in { gadgets_to_sum })" )
    continue

  if VERBOSE:
    print( f"Processing { gadget_name }..." )

  gadget = gadgets.GADGETS[ gadget_name ]
  if 'download' not in gadget:
    print(
      f"WARNING: Gadget not downloadable (probably a git clone?) {gadget_name}",
      file=sys.stderr )
    continue

  root = os.path.join( os.path.abspath( os.path.dirname( __file__ ) ),
                       'download' )

  last_url = ''
  seen_checksums = set()
  for OS in 'linux', 'macos', 'windows':
    for PLATFORM in 'x86_64', 'arm64', 'x86', 'armv7':
      spec = {}
      spec.update( gadget.get( 'all', {} ) )
      spec.update( gadget.get( OS, {} ) )
      spec.update( gadget.get( OS + '_' + PLATFORM, {} ) )

      if spec.get( 'checksum', None ):
        print( f"WARNING: { PLATFORM } for { OS } for { gadget_name } "
                "has a checksum configured already. Probably you forgot to "
                "clear it." )

      url = string.Template( gadget[ 'download' ][ 'url' ] ).substitute( spec )
      if url == last_url:
        # Probably not different for this arch
        continue

      version = spec.get( 'version', 'vUnknown' )
      destination = os.path.join( root, gadget_name, OS, PLATFORM, version )

      file_path = installer.DownloadFileTo(
        url,
        destination,
        file_name = gadget[ 'download' ].get( 'target' ),
        checksum = spec.get( 'checksum' ) )

      checksum = installer.GetChecksumSHA254( file_path )
      if checksum in seen_checksums:
        continue
      seen_checksums.add( checksum )

      last_url = url
      results.append(
        f"{ gadget_name } { version } { OS }_{ PLATFORM }: { checksum }" )

for result in results:
  print( result )
