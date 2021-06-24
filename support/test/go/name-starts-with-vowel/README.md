# Purpose

This example comes with two example vimspector configs for the Go programming language.

1) `run-cmd` will launch the main programme under `cmd/namestartswithvowel`.
1) `test-current-file` will run the tests in the current file in debug mode.

## Example use-cases

### run-cmd

* Open `cmd/namestartswithvowel/main.go`
* Add a breakpoint somewhere within the programme
* Start the debugger (`:call vimspector#Continue()` or your relevant keymapping)
* Select the first launch configuration (`1: run-cmd`)

### test-current-file

* Open `internal/vowels/vowels_test.go`
* Add a breakpoint somewhere within the test
* Start the debugger (`:call vimspector#Continue()` or your relevant keymapping)
* Select the second launch configuration (`2: test-current-file`)

## Additional Configuration

There are two additional configuration options specified under `run-cmd`; these parameters configure the maximum string/array size to be shown while debugging.

```
"dlvLoadConfig": {
    "maxArrayValues": 1000,
    "maxStringLen": 1000
}
```
