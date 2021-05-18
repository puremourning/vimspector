---
name: Bug report
about: Create a report to help us improve
title: ''
labels: ''
assignees: ''

---

> DO NOT DELETE THIS TEMPLATE. IF YOU DELETE THIS TEMPLATE AND DO NOT COMPLETE IT, YOUR ISSUE WILL BE CLOSED.

### Describe the bug

> Provide A clear and concise description of what the bug is.

### Minimal reproduciton

> Please answer the following questions

* Does your issue reproduce using `vim --clean -Nu /path/to/vimspector/support/minimal_vimrc` ? \[Yes/No]
* If you are using Neovim, does your issue reproduce using Vim? \[Yes/No]

> List of steps to reproduce:

> 1. Run `vim ---clean Nu /path/to/vimspector/support/minimal_vimrc`
> 2. Open _this project_...
> 3. Press _this sequence of keys_

> Use the following Vimspector config file:

```
paste .vimspector.json here
```

### Expected behaviour

> Provide A clear and concise description of what you expected to happen.

### Actual behaviour

> What actually happened, including output, log files etc.

> Please include:
> * Vimspector log (~/.vimspector.log)
> * Output from any or all UI diagnostic tabs (Server, etc.)

### Environemnt

***NOTE***: NeoVim is supported only on a best-effort basis. Please check the README
for limitations of neovim. Don't be offended if I ask you to reproduce issues in
Vim.

***NOTE***: Windows support is experimental and best-efrort only. If you find an
issue related to Windows or windows-isms, consider sending a PR or
discussing on Gitter rather than raising an issue.

* Version of Vimspector: (e.g. output of `git rev-parse HEAD` if cloned or the
  name of the tarball used to install otherwise)

* Output of `:VimspectorDebugInfo`

```
paste here
```

* Output of `vim --version` or `nvim --version`

```
paste here
```

* Output of `which vim` or `which nvim`:

```
paste here
```

* Output of `:py3 print( __import__( 'sys' ).version )`:

```
paste here
```

* Output of `:py3 import vim`:

```
paste here
```

* Output of `:py3 import vimspector`:

```
paste here
```


* For neovim: output of `:checkhealth`

```
paste here
```

* Operating system: <linux or macOS> and version
  
### Declaration

> Please complete the following declaration. If this declaration is not completed, your issue may be closed without comment.

* I have read and understood [CONTRIBUTING.md](https://github.com/puremourning/vimspector/blob/master/CONTRIBUTING.md) \[Yes/No]


### Additional information

Add any other context about the problem here.
