# Contributing to Vimspector

Contributions to Vimspector are always welcome. Contributions can take many
forms, such as:

* Raising, responding to, or reacting to Issues or Pull Requests
* Testing new in-progress changes and providing feedback
* Discussing in the Gitter channel
* etc.

At all times the [code of conduct](#code-of-conduct) applies.

## Troubleshooting

It's not completely trivial to configure Vimspector and there is a fairly large
amount of documentation. I know full well that documentation isn't everything,
so the first step in troubleshooting is to try a sample project that's known to
work, to check if the problem is your project configuration rather than an
actual bug.

Therefore before raising an issue for a supported language, please check with
the sample projects in `support/test/<language>` and `tests/testdata/` to see if
the problem is with your project settings, rather than with vimspector. 

Information on these is in [the README](README.md#trying-it-out).

If in doubt, ask on Gitter.

## Diagnostics

Whenever reporting any type of fault, or difficulty in making the plugin
work, please always include _all_ of the diagnostics requested in the
[issue template][issue-template]. Please do not be offended if your request
is ignored if it does not include the requested diagnostics.

The Vimspector log file contains a full trace of the communication between
Vimspector and the debug adapter. This is the primary source of diagnostic
information when something goes wrong that's not a clear Vim traceback.

If you just want to see the Vimspector log file, use `:VimspectorToggleLog`,
which will tail it in a little window (doesn't work on Windows).

## Issues

The GitHub issue tracker is for *bug reports* and *features requests* for the
Vimspector project, and on-topic comments and follow-ups to them. It is not for
general discussion, general support or for any other purpose.

Please **search the issue tracker for similar issues** before creating a new
one. There's no point in duplication; if an existing open issue addresses your
problem, please comment there instead of creating a duplicate. However, if the
issue you found is **closed as resolved** (e.g. with a PR or the original user's
problem was resolved), raise a **new issue**, because you've found a new
problem. Reference the original issue if you think that's useful information.

Closed issues which have been inactive for 60 days will be locked, this helps to
keep discussions focussed. If you believe you are still experiencing an issue
which has been closed, please raise a new issue, completing the issue template.

If you do find a similar _open_ issue, **don't just post 'me too' or similar**
responses. This almost never helps resolve the issue, and just causes noise for
the maintainers. Only post if it will aid the maintainers in solving the issue;
if there are existing diagnostics requested in the thread, perform
them and post the results.

Please do not be offended if your Issue or comment is closed or hidden, for any
of the following reasons:

* The [issue template][issue-template] was not completed
* The issue or comment is off-topic
* The issue does not represent a Vimspector bug or feature request
* The issue cannot be reasonably reproduced using the minimal vimrc
* The issue is a duplicate of an existing issue
* etc.

Issue titles are important. It's not usually helpful to write a title like
`Issue with Vimspector` or `Issue configuring` or even pasting an error message.
Spend a minute to come up with a consise summary of the problem. This helps with
management of issues, with triage, and above all with searching.

But above all else, please *please* complete the issue template. I know it is a
little tedious to get all the various diagnostics, but you *must* provide them,
*even if you think they are irrelevant*. This is important, because the
maintainer(s) can quickly cross-check theories by inspecting the provided
diagnostics without having to spend time asking for them, and waiting for the
response. This means *you get a better answer, faster*. So it's worth it,
honestly.

### Reproduce your issue with the minimal vimrc

Many problems can be caused by unexpected configuration or other plugins. 
Therefore when raising an issue, you must attempt to reproduce your issue
with the minimal vimrc provided, and to provide any additional changes required
to that file in order to reproduce it. The purpose of this is to ensure that
the issue is not a conflict with another plugin, or a problem unique to your
configuration.

If your issue does _not_ reproduce with the minimal vimrc, then you must say so
in the issue report.

The minimal vimrc is in `support/test/minimal_vimrc` and can be used as follows:

```
vim --clean -Nu /path/to/vimspector/support/minimal_vimrc
```

## Pull Requests

Vimspector is open to all contributors with ideas great and small! However,
there is a limit to the intended scope of the plugin and the amount of time the
maintainer has to support and... well... maintain features. It's probably well
understood that the contributor's input typically ends when a PR is megred, but
the maintainers have to keep it working forever.

### Small changes

For bug fixes, documentation changes, gadget version updates, etc. please just
send a PR, I'm super happy to merge these!

If you are unsure, or looking for some pointers, feel free to ask in Gitter, or
mention is in the PR.

### Larger changes

For larger features that might be in any way controversial, or increase the
complexity of the overall plugin, please come to Gitter and talk to the
maintainer(s) first. This saves a lot of potential back-and-forth and makes sure
that we're "on the same page" about the idea and the ongoing maintenance.

In addition, if you like hacking, feel free to raise a PR tagged with `[RFC]` in
the title and we can discuss the idea. I still prefer to discuss these things on
Gitter rather than back-and-forth on GitHub, though.

Please don't be offended if the maintainer(s) request significant rework for (or
perhaps even dismiss) a PR that's not gone through this process.

Please also don't be offended if the maintainer(s) ask if you're willing to
provide ongoing support for the feature. As an OSS project manned entirely in
what little spare time the maintainer(s) have, we're always looking for
contributions and contributors who will help with support and maintenance of
larger new features.

### PR Guidelines

When contributing pull requests, I ask that:

* You provide a clear and complete summary of the change, the use case and how
  the change was tested.
* You avoid using APIs that are not available in the versions listed in the
  dependencies on README.md
* You add tests for your PR.
* You test your changes in both Vim and Neovim at the supported versions (and
  state that in the PR).
* You follow the style of the code as-is; the python code is YCM-stye, it is
  *not* PEP8, nor should it be.

### Running the tests locally

There are 2 ways:

1. In the docker container. The CI tests for linux run in a container, so as to
   ensure a consistent test environment. The container is defined in
   `./tests/ci/`. There is also a container in `./tests/manual` which can be
   used to run the tests interractively. To do this install and start docker,
   then run `./tests/manual/run`.  This will drop you into a bash shell inside
   the linux container with your local vimspector code mounted. You can then
   run the tests with `./run_tests --install --basedir test-base-docker`.
1. Directly: Run `./install_gadget.py --all` and then `./run_tests`. Note that
   this depends on your runtime environment and might not match CI. I recommend
   running the tests in the docker container. If you have your own custom
   gadgets and/or custom configurations (in `vimspector/configurations` and/or
   `vimspector/gadget`, then consider using `./run_tests --install --basedir
   /tmp/vimspector_test` (then delete `/tmp/vimspector_test`). This will install
   the gadgets to that dir and use it for the gadget dir/config dir so that your
   custom configuration won't interfere with the tests.

When tests fail, they dump a load of logs to a directory for each failed tests.
Usually the most useful output is `messages`, which tells you what actually
failed.

For more infomration on the test framework, see
[this article](https://vimways.org/2019/a-test-to-attest-to/), authored by the
Vimspector creator.

### Manual testing within the container

To manually test with Vim within the container, affter running the tests with
`--base-dir test-base-docker`, you can use this:

```
vim --cmd "let g:vimspector_base_dir='$(pwd)/test-base-docker/'" -Nu support/minimal_vimrc
```

This will start with the minimal configuration and use the gadgets installed in
`test-base-docker`. This is especially important if your host system is not
linux.

### Code Style

The code style of the Python code is "YCM" style, because that's how I like it.
`flake8` is used to check for certain errors and code style.

The code style of the Vimscript is largely the same, and it is linted by
`vint`.

To run them:

* (optional) Create and activate a virtual env:
  `python3 -m venv venv ; source venv/bin/activate`
* Install the development dependencies: `pip install -r dev_requirements.txt`
* Run `flake8`: `flake8 python3/ *.py`
* Run `vint`: `vint autoload/ plugin/ tests/`

They're also run by CI, so please check for lint failures. The canonical
definition of the command to run is the command run in CI, i.e. in
`.git/workflows/build.yml`.

### Debugging Vimspector

You can debug vimspector's python code using vimspector! We can use debugpy,
from within Vim's embedded python and connect to it. Here's how:

1. In one instance of vim, run the following to get debugpy to start listening
   for us to connect: `:py3 __import__( 'vimspector', fromlist=[ 'developer' ]
   ).developer.SetUpDebugpy()`

2. In another instance of Vim, set a breakpoint in the vimspector python code
   you want to debug and launch vimspector (e.g. `<F5>`). Select the `Python:
   attach to vim` profile. This will attach to the debugpy running in the other
   vim.

3. Back in the first vim (the debuggee), trigger the vimspector code in
   question, e.g. by starting to debug something else.

4. You'll see it pause, and the 2nd vim (the debugger), you should be able to
   step through and inspect as with any other python remote debugging.

NB. It's also possible to debug the vimscript code using vimspector, but this
requires unreleased vim patches and a fair amount of faff. You can always use
`:debug` (see the help) for this though. 

# Code of conduct

Please see [code of conduct](CODE_OF_CONDUCT.md).

[vint]: https://github.com/Vimjas/vint
[flake8]: https://flake8.pycqa.org/en/latest/
[issue-template]: https://github.com/puremourning/vimspector/blob/master/.github/ISSUE_TEMPLATE/bug_report.md
