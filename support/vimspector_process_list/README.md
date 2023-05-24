# A simple process lister

This directory contains a very very very simple process lister that _should_
work on macOS, Linux and Windows.

It is _not_ indended to be a complete replacement for `ps` or similar tools, but
may be useful if such tools are not available on your system.

## Build/installation

Requires `go` to build it. Simply:

* `cd` to this directory
* `go build`

Optionally, to "install it", just copy the binary to somewhere in your PATH, and
vimspector will automatically start using it. 

If you just want to use it with Vimspector, then there's no need to "install" it
anywhere: for convenience, Vimspector will also look in this directory if it
doesn't find it in your path.

## Usage

If the binary is found, Vimspector will use it when you put `"${PickProcess()}"`
or `${PickProcess(\"someBinaryName\")}` as a replacement variable in your
configuration.

Usage:

```
vimspector_process_list [pattern]
```

It checks all PIDs and filters out:

 - Binaries which don't match the pattern (which is optional); The pattern is a
   go regular expression, applied to the image name (not the command line).
 - Processes for another user
 - Processes which are not running
 - Zombies

Then it prints a table with columns:

 - `PID [(name)]`: The process ID, and if no pattern was supplied, the image
   name
 - `PPID (name)`: The parent process ID and name
 - `CMDLINE` or `CWD`: If a pattern was supplied, the working directory of the
   process, otherwise the command line (truncated to 40 chars).
 - `START`: The time the process was started

Hopefully this is useful enough to identify your process amongs multiple
instances.
