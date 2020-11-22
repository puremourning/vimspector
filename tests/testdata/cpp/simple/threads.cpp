#include <chrono>
#include <condition_variable>
#include <cstdlib>
#include <iostream>
#include <mutex>
#include <string_view>
#include <system_error>
#include <thread>
#include <vector>
#include <charconv>
#include <random>

int main( int argc, char ** argv )
{
  int numThreads = {};
  if ( argc < 2 )
  {
    numThreads = 5;
  }
  else
  {
    std::string_view numThreadArg( argv[ 1 ] );
    if ( auto [ p, ec ] = std::from_chars( numThreadArg.begin(),
                                           numThreadArg.end(),
                                           numThreads );
         ec != std::errc() )
    {
      std::cerr << "Usage " << argv[ 0 ] << " <number of threads>\n";
      return 2;
    }
  }

  std::cout << "Creating " << numThreads << " threads" << '\n';

  std::vector<std::thread> threads{};
  threads.reserve( numThreads );

  auto eng = std::default_random_engine() ;
  auto dist = std::uniform_int_distribution<int>( 250, 1000 );

  std::mutex m;
  std::condition_variable v;
  bool ready = false;
  {
    std::lock_guard l(m);

    std::cout << "Preparing..." << '\n';

    for ( int i = 0; i < numThreads; ++i )
    {
      using namespace std::chrono_literals;
      auto tp = [&,tnum=i]() {
        // Wait for the go-ahead
        {
          std::unique_lock l(m);
          while (!ready) {
            v.wait(l);
          }
        }

        std::cout << "Started thread " << tnum << '\n';
        std::this_thread::sleep_for(
          5s + std::chrono::milliseconds( dist( eng ) ) );
        std::cout << "Completed thread " << tnum << '\n';
      };

      threads.emplace_back( tp );
    }

    std::cout << "Ready to go!" << '\n';
    ready = true;
  }

  v.notify_all();

  for ( int i = 0; i < numThreads; ++i )
  {
    threads[ i ].join();
  }

  return 0;
}
