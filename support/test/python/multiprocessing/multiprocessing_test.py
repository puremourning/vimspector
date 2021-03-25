import time
import multiprocessing as mp


def First():
  for _ in range( 100 ):
    print( "in first" )
    time.sleep( 0.1 )


def Second():
  for _ in range( 100 ):
    print( "in second" )
    time.sleep( 0.1 )


print( "main" )
p1 = mp.Process( target=First )
p2 = mp.Process( target=Second )

p1.start()
p2.start()

p1.join()
p2.join()

print( "Done" )
