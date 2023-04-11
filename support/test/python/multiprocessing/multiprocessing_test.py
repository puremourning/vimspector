import time
import multiprocessing as mp


def First():
  for i in range( 10 ):
    print( f"in first x {i}" )
    time.sleep( 0.1 )


if __name__ == '__main__':
  print( "main" )
  p1 = mp.Process( target=First )

  p1.start()

  for i in range( 20 ):
    print( f'in main i {i}' )
    time.sleep( 0.5 )

  p1.join()

  print( "Done" )
