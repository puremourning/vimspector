#!/usr/bin/env python

import os


def Main():
  print( os.environ.get( 'Something', 'ERROR' ) )
  print( os.environ.get( 'SomethingElse', 'ERROR' ) )
  print( os.environ.get( 'PATH', 'ERROR' ) )

  for k, v in os.environ.items():
    print( f'{ k } = "{ v }"' )


Main()

