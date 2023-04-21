import time
import multiprocessing as mp


def Priant( where, i ):
  print( f"in {where} x is {i}" )


def First( inst, remaining ):
  print( f"I{inst}C{remaining} starting" )
  p2 = None
  if remaining > 1:
    p2 = mp.Process( target=First, args=( inst, remaining - 1, ), name='SubSub' )
    p2.start()

  for i in range( 10 ):
    Priant( f'First I{inst}C{remaining}', i )
    time.sleep( 0.1 )

  if p2:
    p2.join()

  print( f"I{inst}C{remaining} done" )


if __name__ == '__main__':
  # Even though this is supposedly buggy on macOS, it's required to avoid an
  # additional sub-process which makes testing awkward
  print( "main" )
  ps = []
  for p in range( 5 ):
    px = mp.Process( target=First, args=( p, 3, ), name='Sub' )
    px.start()

  print( f"Main starting with len( mp.active_children() ) active children" )

  for i in range( 10 ):
    Priant( 'main', i )
    time.sleep( 0.5 )

  for p in ps:
    p.join()

  print( "MainDone" )
