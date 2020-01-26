# Contributing to Vimspector

Contributions to Vimspector are always welcome. Contributions can take many
forms, such as:

* Raising, responding to, or reacting to Issues or Pull Requests
* Testing new in-progress changes and providing feedback
* Discussing in the Gitter channel
* etc.

At all times the [code of conduct](#code-of-conduct) applies.

## Issues

The GitHub issue tracker is for *bug reports* and *features requests* for the
Vimspector project, and on-topic comments and follow-ups to them. It is not for
general discussion, general support or for any other purpose.

Please do not be offended if your Issue or comment is closed or hidden, for any
of the following reasons:

* The issue template was not completed
* The issue or comment is off-topic
* The issue does not represent a Vimspector bug or feature request
* etc.

But above all else, please *please* complete the issue template. I know it is a
little tedious to get all the various diagnostics, but you *must* provide them,
*even if you think they are irrelevant*. This is important, because the
maintainer(s) can quickly cross-check theories by inspecting the provided
diagnostics without having to spend time asking for them, and waiting for the
response. This means *you get a better answer, faster*. So it's worth it,
honestly.

## Pull Requests

When contributing pull requests, I ask that:

* You provide a clear and complete summary of the change, the use case and how
  the change was tested.
* You avoid using APIs that are not available in the versions listed in the
  dependencies on README.md
* You add tests for your PR.
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
   follow the instructions for running tets directly.
1. Directly: Run `./install_gadget.py --all` and then `./run_tests`. Note that
   this depends on your runtime environment and might not match CI. I recommend
   running the tests in the docker container.

When tests fail, they dump a load of logs to a directory for each failed tests.
Usually the most useful output is `messages`, which tells you what actually
failed.

For more infomration on the test framework, see
[this article](https://vimways.org/2019/a-test-to-attest-to/), authored by the
Vimspector creator.

# Code of conduct

Please see [code of conduct](CODE_OF_CONDUCT.md).
