package main

import (
	"bufio"
	"fmt"
	"os"
	"strconv"
)

func fibonacci(c, quit chan int) {
	x, y := 0, 1
	for {
		select {
		case c <- x:
			x, y = y, x+y
		case <-quit:
			fmt.Println("quit")
			return
		}
	}
}

func main() {
	c := make(chan int)
	quit := make(chan int)
	in := make(chan string)
	go func() {
		scanner := bufio.NewScanner(os.Stdin)
		for scanner.Scan() {
			fmt.Println( ":" )
			in <- scanner.Text()
		}
	}()
	go func() {
		for {
			cmd, _ := <-in
			fmt.Println( "GOT: ", cmd )
			if cmd == "quit" {
				quit <- 0
				return
			}
			n, err := strconv.Atoi(cmd)
			if err == nil {
				for i := 0; i < n ; i++ {
					fmt.Println(<-c)
				}
			} else {
				fmt.Println( "Unrecognised: ", cmd, err )
			}
		}
	}()
	fibonacci(c, quit)
}
