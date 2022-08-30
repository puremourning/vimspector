#!/usr/bin/env python3

import sys
import os
import string
import fnmatch

# Gaim access to vimspector libs
sys.path.insert(
  1,
  os.path.abspath( os.path.join( os.path.dirname( __file__ ),
                                 '..',
                                 '..',
                                 'python3' ) )
)

from vimspector import installer, gadgets

gadgets_to_sum = sys.argv[ 1: ]
results = []

for gadget_name in gadgets.GADGETS.keys():
  include = False
  for requested_gadget in gadgets_to_sum:
    if fnmatch.fnmatch( gadget_name, requested_gadget ):
      include = True
      break

  if not include:
    continue

  gadget = gadgets.GADGETS[ gadget_name ]
  if 'download' not in gadget:
    print(
      f"WARNING: Gadget not downloadable (probably a git clone?) {gadget_name}",
      file=sys.stderr )
    continue

  root = os.path.join( os.path.abspath( os.path.dirname( __file__ ) ),
                       'download' )

  last_url = ''
  for OS in 'linux', 'macos', 'windows':
    for PLATFORM in 'x86_64', 'x86', 'arm64':
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
      last_url = url
      results.append(
        f"{ gadget_name } { version } { OS }_{ PLATFORM }: { checksum }" )

for result in results:
  print( result )
