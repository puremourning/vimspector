#!/usr/bin/env python3

import hashlib
import sys


def GetChecksumSHA254( file_path ):
  with open( file_path, 'rb' ) as existing_file:
    return hashlib.sha256( existing_file.read() ).hexdigest()


for arg in sys.argv[ 1: ]:
  print( f"{ arg } = { GetChecksumSHA254( arg ) }" )
