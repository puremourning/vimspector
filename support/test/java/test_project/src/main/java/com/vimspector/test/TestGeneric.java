package com.vimspector.test;

class TestGeneric<T extends Base> {
  T base;

  public TestGeneric( T b )
  {
    this.base = b;
  }

  public String DoSomethingUseful() {
    String s = "A B C" + base.DoSomething();

    return s.replace( "B", "C" );
  }
}
