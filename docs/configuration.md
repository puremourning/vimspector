---
title: Configuration
---


This document defines the supported format for project and adapter configuration
for Vimspector.

<!--ts-->
  * [Concepts](#concepts)
     * [Debug adapter configuration](#debug-adapter-configuration)
     * [Debug profile configuration](#debug-profile-configuration)
     * [Replacements and variables](#replacements-and-variables)
  * [Configuration Format](#configuration-format)
  * [Files and locations](#files-and-locations)
  * [Adapter configurations](#adapter-configurations)
  * [Debug configurations](#debug-configurations)
     * [Exception breakpionts](#exception-breakpionts)
  * [Predefined Variables](#predefined-variables)
  * [Appendix: Editor configuration](#appendix-editor-configuration)

<!-- Added by: ben, at: Tue 28 Jan 2020 08:47:40 GMT -->

<!--te-->

## Concepts

As Vimspector supports debugging arbitrary projects, you need to tell it a few
deatils about what you want to debug, and how to go about doing that.

In order to debug things, Vimspector requires a Debug Adapter which bridges
between Vimspector and the actual debugger tool. Vimspector can be used with any
debug adapter that implements the [Debug Adapter Protocol][dap].

For each debugging session, you provide a _debug configuration_ which includes
things like:

- The debug adapter to use (and possibly how to launch and configure it).
- How to connect to the remote host, if remote debugging.
- How to launch or attach to your process.

Along with optional additional configuration for things like:

- Exception breakpoints

### Debug adapter configuration

The adapter to use for a particular debug session can be specified inline within
the _debug configuration_, but more usually the debug adapter is defined
separately and just referenced from the _debug configuration_.

The adapter configuration includes things like:

* How to launch or connect to the debug adapter
* How to configure it for PID attachment
* How to set up remote debugging, such as how to launch the process remotely
  (for example, under `gdbserver`, `ptvsd`, etc.)

### Debug profile configuration

Projects can have many different debug profiles. For example you might have all
of the following, for a given source tree:

* Remotely launch c++ the process, and break on `main`
* Locally Python test and break exception
* Remotely attach to a c++ process
* Locally launch a bash script
* Attach to a JVM listening on a port

Each of these represents a different use case and a different _debug
configuration_. As mentioned above, a _debug configuration_ is essentially:

* The adapter to use
* The type of session (launch or attach), and whether or not to do it remotely
* The configuration to pass to the adapter in order to launch or attach to the
  process.

The bulk of the configuration is the last of these, which comprises
adapter-specific options, as the Debug Adapter Protocol does not specify any
standard for launch or attach configuration.

### Replacements and variables

Vimspector _debug configuration_ is intended to be as general as possible, and
to be committed to source control so that debugging your applications becomes a
simple, quick and pain-free habit (e.g. answering questions like "what happens
if..." with "just hit F5 and step through!").

Therefore it's important to abstract certain details, like runtime and
build-time paths, and to parameterise the _debug configuration_. Vimspector
provides a simple mechanism to do this with `${replacement}` style replacements.

The values available within the `${...}` are defined below, but in summary the
following are supported:

* Environment variables, such as `${PATH}`
* Predefined variables, such as `${workspaceRoot}`, `${file}` etc.
* Configuration-defined variables, either provided by the adapter configuration
  or debug configuration, or from running a simple shell command.
* Anything else you like - the user will be asked to provide a value.

If the latter 2 are confusing, for now, suffice to say that they are how
Vimspector allows parameterisation of debug sessions. The [Vimspector
website][website-getting-started] has a good example of where this sort of thing
is useful: accepting the name of a test to run.

But for now, consider the following example snippet:

```json
{
  "configurations": {
    "example-debug-configuration": {
      // This is a single-line comment  explaining the purpose
      "adapter": "example-adapter-name",
      "variables": {
        "SecretToken": { // Variables should start with upper-case letters
          "shell" : [ "cat", "${HOME}/.secret_token" ]
        }
      },
      "configuration": {
        "request": "launch" /* or it could be "attach" */,
        "program": [
          "${fileBasenameNoExtension}",
          "-c", "configuration_file.cfg",
          "-u", "${USER}",
          "--test-identifier", "${TestIdentifier}",
          "--secret-token", "${SecretToken}"
        ]
      },
      "breakpoints": {
        "exception": {
          "caught": "",
          "uncaught": "Y"
        }
      }
    }
  }
}
```

In this (fictitious) example the `program` launch configuration item contains
the following variable substitutions:

* `${fileBasenameNoExtension}` - this is a [Predefined
  Variable](#predefined-variables), set by Vimspector to the base name of the
  file that's opened in Vim, with its extension removed (`/path/to/xyz.cc` ->
  `xyz`).
* `${USER}` - this refers to the Environment Variable `USER`.
* `${TestIdentifier}` - this variable is not defined, so the user is asked to
  provide a value interactively when starting debugging. Vimspector remembers
  what they said and provides it as the default should they debug again.
* `${SecretToken}` - this variable is provided by the configuration's
  `variables` block. Its value is taken from the `strip`ped result of running
  the shell command. Note these variables can be supplied by both the debug and
  adapter configurations and can be either static strings or shell commands.

### The splat operator

Often we want to create a single `.vimspector.json` entry which encompasses many
use cases, as it is tedious to write every use case/start up option in JSON.
This is why we have the replacement variables after all.

Frequently debug adapters request command arguments as a JSON array, for
example:

```json
    "args": [ "one", "two three", "four" ],
```

To help with this sort of case, vimspector supports a 'splat' operator for
replacement variables apperaing within lists. The syntax is: `"*${var}`, which
means roughly "splice the contents of `${var}` into the list at this position".
`${var}` is parsed like a shell command (using python's `shlex` parser) and each
word is added as a list item.

For example:

```json
   "args": [ "*${CommandLineArgs}" ]
```

This would:

* Ask the user to provide the variable `CommandLineArgs`. Let's say they entered
  `one "two three" four`
* Split `CommandLineArgs` like shell arguments: `one`, `two three` and `four`
* Set `args` in the settings dict to: `[ "one", "two three", "four" ]`

You can also combine with static values:

```json
   "args": [ "First", "*${CommandLineArgs}", "Last" ]
```

This would yield the intuitive result:
`[ "First",  "one", "two three", "four", "Last" ]`

## Configuration Format

All Vimspector configuration is defined in a JSON object. The complete
specification of this object is available in the [JSON Schema][schema], but
the basic format for the configuration object is:

```
{
  "adapters": { <object mapping name to <adapter configuration> },
  "configurations": { <object mapping name to <debug configuration> }
}
```

The `adapters` key is actually optional, as `<adapter configuration>` can be
embedded within `<debug configuration>`, though this is not recommended usage.

## Files and locations

The above configuration object is constructed from a number of configuration
files, by merging objects in a specified order.

In a minimal sense, the only file required is a `.vimspector.json` file in the
root of your project which defines the [full configuration object][schema], but
it is usually useful to split the `adapters` configuration into a separate file
(or indeed one file per debug adapter).

The following sections describe the files that are read and use the following
abbreviations:

* `<vimspector home>` means the path to the Vimspector installation (such as
  `$HOME/.vim/pack/vimspector/start/vimspector`)
* `<OS>` is either `macos` or `linux` depending on the host operating system.
* `<filetype>` is the Vim fileytype. Where multiple filetypes are in effect,
  typically all filetypes are checked.

## Adapter configurations

Vimspector reads a series of files to build the `adapters` object. The
`adapters` objects are merged in such a way that a definition for an adapter
named `example-adapter` in a later file _completely replaces_ a previous
definition.

* `<vimspector home>/gadgets/<OS>/.gadgets.json` - the file written by
  `install_gadget.py` and not usually edited by users.
* `<vimspector home>/gadgets/<OS>/.gadgets.d/*.json` (sorted alphabetically).
  These files are user-supplied and override the above.
* The first such `.gadgets.json` file found in all parent directories of the
  file open in Vim.
* The `.vimspector.json` and any filetype-specific configurations (see below)

In all cases, the required format is:

```
{
  "$schema": "https://puremourning.github.io/vimspector/schema/gadgets.schema.json#",
  "adapters": {
    "<adapter name>": {
      <adapter configuration>
    }
  }
}
```

Each adapters block can define any number of adapters. As mentioned, if the same
adapter name exists in multiple files, the last one read takes precedence and
_completely replaces_ the previous configuration. In particular that means you
can't just override one option, you have to override the whole block.

Adapter configurations are re-read at the start of each debug session.

The specification for the gadget object is defined in the [gadget schema][].

## Debug configurations

There are two locations for debug configurations for a project:

* `<vimspector home>/configurations/<OS>/<filetype>/*.json`
* `.vimspector.json` in the project source

Typically, the debug configurations are read from `.vimspector.json`. The file
is found (like `.gadgets.json` above) by recursively searching up the directory
hierarchy from the directory of the file open in Vim. The first file found is
read and no further searching is done.

Only a single `.vimspector.json` is read. If one is found, the location of this
file is used for `${workspaceRoot}` and other workspace-relative paths.

In addition, users can create filetype-specific configurations in the vimspector
installation directory. This can be useful where the parameters for the debug
session for a particular filetype are always known in advance, or can always be
entered by the user. This allows for debugging to "just work" without any
modification to the project source (no need to add a `.vimspector.json`). In
this case, the `${workspaceRoot}` and workspace-relative paths are interpreted
relative to the file open in Vim. This isn't ideal, but there is no other
obvious way to default this variable.

As with gadgets, any debug configurations appearing within `.vimspector.json`
override any that appear in the common configuration dir.

Debug configurations are re-read at the start of each debug session, so
modifications are picked up without any restarts of Vim.

The specification for the gadget object is defined in the [schema][], but a
typical example looks like this:

```
{
  "$schema": "https://puremourning.github.io/vimspector/schema/vimspector.schema.json#",
  "configurations": {
    "<configuation name>": {
      "adapter": "<adapter name>",
      "configuration": {
        "request": "<launch or attach>",
        <debug configutation>
      }
    }
  }
}
```

### Exception breakpionts

Debug adapters have arbitrary configuration for exception breakpoints. Normally
this is presented as a series of question to the user on startnig the debug
session. The question includes the name of the exception breakpoint option,
the default and the list of valid responses (usually `Y` or `N`).

You can pre-configure the answers to these questions in the `breakpoints`
section of the debug configuration. For each question, take the name provided
and configure the response `exception` mapping in the `breakpoints` mapping.  If
the configured response is empty string, the debug adapter default will be used.

Referring to the above example, the following tells the debug adapter to use the
default value for `caught` exceptoins and to break on `uncaught` exception:

```
{
  "configurations": {
    "example-debug-configuration": {
      "adapter": "example-adapter-name",
      "breakpoints": {
        "exception": {
          "caught": "",
          "uncaught": "Y"
        }
      },
      ...
```

## Predefined Variables

The following variables are provided:

* `${dollar}` - has the value `$`, can be used to enter a literal dollar
* `$$` - a literal dollar
* `${workspaceRoot}` - the path of the folder where `.vimspector.json` was
  found
* `${workspaceFolder}` - the path of the folder where `.vimspector.json` was
  found
* `${gadgetDir}` - path to the OS-specifc gadget dir (`<vimspector
  home>/gadgets/<OS>`)
* `${file}` - the current opened file
* `${relativeFile}` - the current opened file relative to workspaceRoot
* `${fileBasename}` - the current opened file's basename
* `${fileBasenameNoExtension}` - the current opened file's basename with no
  file extension
* `${fileDirname}` - the current opened file's dirname
* `${fileExtname}` - the current opened file's extension
* `${cwd}` - the current working directory of the active window on launch

## Appendix: Configuration file format

The configuration files are text files which must be UTF-8 encoded. They
contain a single JSON object, along with optional comments.

Comments are "c-style", i.e.:

* `// single line comment ...`
* `/* inline comment */`

There is much debate about whether JSON files should contain comments. I have
added them because they are useful in the context of configuration files.
Unforutnately this may mean your editor doesn't like them (they are strictly
invalid JSON) so it's up to you if you use them.

Technically, Vimspector uses [JSON
minify](https://github.com/getify/JSON.minify) to strip comments before parsing
the JSON.

## Appendix: Editor configuration

If you would like some assistance with writing the JSON files, and your editor
of choice has a way to use a language server, you can use the
[VSCode JSON language server][vscode-json].

It is recommended to include the `$schema` declaration as in the above examples,
but if that isn't present, the following [JSON language server
configuration][json-ls-config] is recommened to load the schema from the
Internet:

```json
{
  "json": {
    "schemas": [
      {
        "fileMatch": [ ".vimspector.json" ],
        "url": "https://puremourning.github.io/vimspector/schema/vimspector.schema.json"
      },
      {
        "fileMatch": [ ".gadgets.json", ".gadgets.d/*.json" ],
        "url": "https://puremourning.github.io/vimspector/schema/gadgets.schema.json"
      }
    ]
  }
}
```

If your language server client of choice happens to be [YouCompleteMe][], then
the following `.ycm_extra_conf.py` is good enough to get you going, after
following the instructions in the [lsp-examples][] repo to get the server set
up:

```python
VIMSPECTOR_HOME = '/path/to/vimspector' # TODO: Change this

def Settings( **kwargs ):
  if kwargs[ 'language' ] == 'json':
    return {
      'ls': {
        'json': {
          'schemas': [
            {
              'fileMatch': [ '.vimspector.json' ],
              'url': f'file://{VIMSPECTOR_HOME}/docs/schema/vimspector.schema.json'
            },
            {
              'fileMatch': [ '.gadgets.json', '.gadgets.d/*.json' ],
              'url': f'file://{VIMSPECTOR_HOME}/docs/schema/gadgets.schema.json'
            }
          ]
        }
      }
    }

  return None # Or your existing Settings definition....
```

This configuration can be adapted to any other LSP-based editor configuration
and is provided just as an example.

[dap]: https://microsoft.github.io/debug-adapter-protocol/
[schema]: http://puremourning.github.io/vimspector/vimspector.schema.json
[gadget-schema]: http://puremourning.github.io/vimspector/gadgets.schema.json
[YouCompleteMe]: https://github.com/ycm-core/YouCompleteMe
[lsp-examples]: https://github.com/ycm-core/lsp-examples
[vscode-json]: https://github.com/vscode-langservers/vscode-json-languageserver
[json-ls-config]: https://github.com/vscode-langservers/vscode-json-languageserver#settings
