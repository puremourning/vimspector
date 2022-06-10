#!/usr/bin/env python3

import sys
import os
import string

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
for gadget_name in gadgets_to_sum:
  if gadget_name not in gadgets.GADGETS:
    print( f"WARNING: Unknown gadget {gadget_name}", file=sys.stderr )
    continue

  gadget = gadgets.GADGETS[ gadget_name ]
  if 'download' not in gadget:
    print(
      f"WARNING: Gadget not downloadable (probably a git clone?) {gadget_name}",
      file=sys.stderr )

  destination = '.'

  last_url = ''
  for OS in 'linux', 'macos', 'windows':
    for PLATFORM in 'x86_64', 'x86', 'arm64':
      spec = {}
      spec.update( gadget.get( 'all', {} ) )
      spec.update( gadget.get( OS, {} ) )
      spec.update( gadget.get( OS + '_' + PLATFORM, {} ) )

      url = string.Template( gadget[ 'download' ][ 'url' ] ).substitute( spec )
      if url == last_url:
        # Probably not different for this arch
        continue

      file_path = installer.DownloadFileTo(
        url,
        destination,
        file_name = gadget[ 'download' ].get( 'target' ),
        checksum = spec.get( 'checksum' ) )

      checksum = installer.GetChecksumSHA254( file_path )
      results.append( f"{ gadget_name } { OS }_{ PLATFORM }: { checksum }" )

for result in results:
  print( result )
