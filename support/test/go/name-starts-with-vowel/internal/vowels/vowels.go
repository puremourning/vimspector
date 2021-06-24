package vowels

import "strings"

func NameStartsWithVowel(name string) bool {
	s := strings.Split(strings.ToLower(name), "")

	return s[0] == "a" || s[0] == "e" || s[0] == "i" || s[0] == "o" || s[0] == "u"
}
