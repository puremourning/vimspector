package main

import (
	"fmt"

	"example.com/internal/vowels"
)

func main() {
	names := []string{"Simon", "Bob", "Jennifer", "Amy", "Duke", "Elizabeth"}

	for _, n := range names {
		if vowels.NameStartsWithVowel(n) {
			fmt.Printf("%s starts with a vowel!\n", n)
			continue
		}

		fmt.Printf("%s does not start with a vowel!\n", n)
	}
}
