#include <array>
#include <iostream>

int main( int argc, char** argv )
{
  if ( ( argc - 1 ) % 2 )
  {
    std::cerr << "Unbalanced arguments" << std::endl;
    return 1;
  }

  for ( int i=1; i < argc; i += 2 )
  {
    std::cout << argv[ i ]
              << ": "
              << argv[ i + 1 ]
              << std::endl;
  }

  return 0;
}
