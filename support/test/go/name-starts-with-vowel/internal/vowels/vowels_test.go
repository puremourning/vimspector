package vowels

import (
	"fmt"
	"testing"
)

func TestNameStartsWithVowel(t *testing.T) {
	testCases := []struct {
		input          string
		expectedOutput bool
	}{
		{
			input:          "Simon",
			expectedOutput: false,
		},
		{
			input:          "Andy",
			expectedOutput: true,
		},
	}
	for _, tt := range testCases {
		t.Run(fmt.Sprintf("%s should product %t", tt.input, tt.expectedOutput), func(t *testing.T) {
			out := NameStartsWithVowel(tt.input)
			if out != tt.expectedOutput {
				t.Errorf("%s produced %t, when %t was expected", tt.input, out, tt.expectedOutput)
			}
		})
	}
}
