---
name: Bug report
about: Create a report to help us improve
title: ''
labels: ''
assignees: ''

---

**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
List of steps to reproduce

Vimspector config file:

```
paste .vimspector.json here
```

**Expected behavior**
A clear and concise description of what you expected to happen.

**Actual behaviour**
What actually happened, including output, log files etc.

Please include:
* Vimspector log (~/.vimspector.log)
* Output from any or all UI diagnostic tabs (Server, etc.)

**Environemnt**

NOTE: NeoVim is supported only on a best-effort basis. Please check the README
for limitations of neovim. Don't be offended if I ask you to reproduce issues in
Vim.

NOTE: Windows support is experimental and best-efrort only. If you find an
issue related to Windows or windows-isms, consider sending a PR or
discussing on Gitter rather than raising an issue.

* Version of Vimspector: (e.g. output of `git rev-parse HEAD` if cloned or the
  name of the tarball used to install otherwise)

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

**Additional context**
Add any other context about the problem here.
