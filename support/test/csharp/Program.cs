using System;

namespace csharp
{
  class Program
  {
    string toaster = "Making round of toast";
    static int max_bread = 100;
    int bread = max_bread;

    void PrintToast( int r ) {
      int this_round = ( max_bread - bread - r);
      Console.WriteLine( this.toaster + ": " + this_round );
    }

    void MakeToast( int rounds ) {
      if (this.bread - rounds < 0) {
        throw new Exception( "No moar bread!" );
      }

      this.bread -= rounds;
      for (int r = 0; r < rounds; ++r) {
        this.PrintToast( r );
      }

      Console.WriteLine( "Got only " + this.bread + " left" );
    }

    static void Main(string[] args)
    {
      Program p = new Program();
      for (int x = 1; x < 10; ++ x) {
        p.MakeToast( x );
      }
    }
  }
}
