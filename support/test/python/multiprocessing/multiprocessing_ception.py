import time
import multiprocessing as mp


def Priant( where, i ):
  print( f"in {where} x is {i}" )


def First( remaining ):
  print( f"P{remaining} starting" )
  ctx = mp.get_context( 'fork' )
  p2 = None
  if remaining > 1:
    p2 = ctx.Process( target=First, args=( remaining - 1, ), name='SubSub' )
    p2.start()

  for i in range( 10 ):
    Priant( f'First {remaining}', i )
    time.sleep( 0.1 )

  if p2:
    p2.join()

  print( f"P{remaining} done" )


if __name__ == '__main__':
  # Even though this is supposedly buggy on macOS, it's required to avoid an
  # additional sub-process which makes testing awkward
  ctx = mp.get_context( 'fork' )
  print( "main" )
  p1 = ctx.Process( target=First, args=( 2, ), name='Sub' )

  p1.start()

  print( ctx.current_process() )
  print( ctx.active_children() )

  for i in range( 20 ):
    Priant( 'main', i )
    time.sleep( 0.5 )

  p1.join()

  print( "Done" )
