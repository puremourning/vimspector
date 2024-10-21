package main
import "fmt"

type Toaster struct {
	Power int
	Colour string
}

type Test struct {
	Test string
	Toast Toaster
}

func main() {
  var v = "test"
	test := Test{
		Test: "This is\na\ntest",
		Toast: Toaster{
			Power: 10,
			Colour: "green",
		},
	}
  fmt.Println("hello world: " + v)
	fmt.Println("Hi " + test.Test)
}
