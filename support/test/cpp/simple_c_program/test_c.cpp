#include <cstdio>
#include <cstdlib>
#include <iostream>

namespace Test
{
  struct TestStruct
  {
    bool  isInt;

    union {
      int somethingInt;
      char somethingChar;
    } something;

    char big[ sizeof(void*) * 100 ];
  };

  TestStruct _t;

  void bar( TestStruct b )
  {
    std::string s;
    s += b.isInt ? "An int" : "A char";
    std::cout << s << '\n';
  }

  void foo( TestStruct m )
  {
    TestStruct t{ true, {11}, {} };
    bar( t );
  }
}


int main ( int argc, char ** argv )
{
  int x{ 10 };

  printf( "HOME: %s\n", getenv( "HOME" ) );

  Test::TestStruct t{ true, {99}, { ' ', } };
  foo( t ); // ADL!

  for ( int i = 0; i < 100 ; ++i ) {
    Test::foo( { true, {i}, {0} } );
  }

  t.big[ sizeof(void*) * 0 ] = 'r';
  t.big[ sizeof(void*) * 1 ] = 'o';
  t.big[ sizeof(void*) * 2 ] = 'f';
  t.big[ sizeof(void*) * 3 ] = 'l';
  //t.big[ sizeof(void*) * 4 ] = '0';

  std::cout << t.big << '\n';

  return 0;
}
