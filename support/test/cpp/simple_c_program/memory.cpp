struct Test
{
  int x;
  int y;
};

int main( int argc , char ** argv )
{
  Test x[] = {
    { 1, 2 },
    { 3, 4 },
    { 5, 6 },
  };

  Test y = { 7, 8 };

  x[0].x += argc;
  argv[ 0 ][ 0 ] = 'x' ;

  y.x += **argv;
  y.y += argc * **argv;

  return argc;
}
