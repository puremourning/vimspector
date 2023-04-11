import time
import multiprocessing as mp

def Priant( where, i ):
  print( f"in {where} x is {i}" )


def First():
  for i in range( 10 ):
    Priant( 'First', i )
    time.sleep( 0.1 )


if __name__ == '__main__':
  print( "main" )
  p1 = mp.Process( target=First )

  p1.start()

  for i in range( 20 ):
    Priant( 'main', i )
    time.sleep( 0.5 )

  p1.join()

  print( "Done" )
