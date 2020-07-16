package com.vimspector.test;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

public class TestApplication {
  private static List<String> getAdditionalArgs() {
    List<String> list = new ArrayList<>();
    for( Map.Entry<String,String> e : System.getenv().entrySet() ) {
      list.add( e.getKey() + " = " + e.getValue() );
    }
    return list;
  }

  private static class Bass extends Base {
    String bass = "Pump";
    @Override
    public String DoSomething() {
      if ( Math.random() % 3 == 0 ) {
        return bass;
      }
      return super.DoSomething();
    }
  }

  private static <T extends Base> void DoGeneric( T b ) {
    TestGeneric<T> foo = new TestGeneric<>( b );
    foo.DoSomethingUseful();
  }

  public static void main( String[] args ) {
    int numEntries = 0;
    for ( String s : args ) {
      System.out.println( "Arg: " + s );
      ++numEntries;
    }
    for ( String s : TestApplication.getAdditionalArgs() ) {
      System.out.println( "Env: " + s );
      ++numEntries;
    }
    System.out.println( "Number of entries: " + numEntries );

    DoGeneric( new Bass() );
  }
}


