#!/usr/bin/env python

import os


def Main():
  print( os.environ.get( 'Something', 'ERROR' ) )
  print( os.environ.get( 'SomethingElse', 'ERROR' ) )

  for k, v in os.environ:
    print( f'{ k } = "{ v }"' )


Main()

