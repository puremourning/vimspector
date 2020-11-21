var msg = 'Hello, world!'

var obj = {
  test: 'testing',
  toast: function() {
    return 'toasty' + this.test;
  }
}

console.log( "OK stuff happened " + obj.toast() )
