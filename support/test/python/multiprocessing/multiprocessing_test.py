import time
import multiprocessing as mp


def Priant( where, i ):
  print( f"in {where} x is {i}" )


def First():
  for i in range( 10 ):
    Priant( 'First', i )
    time.sleep( 0.1 )


if __name__ == '__main__':
  # Even though this is supposedly buggy on macOS, it's required to avoid an
  # additional sub-process which makes testing awkward
  mp.set_start_method( 'fork' )
  print( "main" )
  p1 = mp.Process( target=First, name='Sub' )

  p1.start()

  print( mp.current_process() )
  print( mp.active_children() )

  for i in range( 20 ):
    Priant( 'main', i )
    time.sleep( 0.5 )

  p1.join()

  print( "Done" )
