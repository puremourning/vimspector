struct AnotherTest
{
  char choo;
  int ints[5];
};

struct Test
{
  int i;
  char c;
  float fffff;

  AnotherTest another_test;
};

static Test SetUp( Test t )
{
  t.another_test.choo = 'p';
  t.another_test.ints[ 0 ] = t.i; return t;
}

int main( int , char ** )
{
  Test t = {};

  t.i = 1;
  t.c = 'c';
  t.fffff = 3.14;

  t = SetUp( t );

  return t.another_test.ints[ 0 ];
}
