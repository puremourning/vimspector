#include <iostream>

namespace
{
  void foo( int bar )
  {
    int unused;

    printf( "%d\n", bar );
  }
}

int main( int argc, char ** )
{
  printf( "this is a test %d\n", argc );
  foo( argc );
  char c = 'a';
  char arr[4] = "abc";
  return 0;
}
