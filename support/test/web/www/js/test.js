$(document).ready(function () {
  var getMessage = function () {
    var msg = "this is ";
    msg += "a test";
    msg += " message";
    return msg;
  };

  var obj = {
    test: getMessage(),
    toast: function () {
      return "egg";
    },
    spam: "ham",
  };

  alert("test: " + obj.test);
  alert("toast: " + obj.toast());
});

function calculate(a, b) {
  var i = 0;
  while ( a > b ) {
    a -= b;
    i++;
  }
  return i;
}
