[![Build Status](https://travis-ci.org/e3krisztian/bead.svg?branch=master)](https://travis-ci.org/e3krisztian/bead)

    B-E-+
     \ \ \
      +-A-D

# BEAD


BEAD is a format for freezing and storing computations while `bead` is a tool that helps
capturing and managing computations in BEAD formats.


## Concept

Given a discrete computation of the form

    output = function(*inputs)

a BEAD captures all three named parts:

- `output` - *data files* (results of the computation)
- `function` - *source code files*, that when run hopefully compute `output` from `inputs`
- `inputs` - are other BEADs' `output` and thus stored as *references to* those *BEADs*

As a special case pure data can be thought of as *constant computation*
having only output but neither inputs nor source code.

A BEAD has some other metadata - notably it has a `kind` property which is shared by
different versions of the conceptually same computation (input or function may be updated/improved)
and a timestamp when the computation was frozen.

The `kind` and timestamp properties enable a meaningful `update` operation on inputs.

New computations get a new, universally unique `kind` (technically an uuid).


## Status

### bead as a tool *is not production ready, yet!*

Although most of the important stuff is implemented, the metadata format is still not fixed,
which might render every existing BEAD incompatible after the change.

Documentation for the tool is non-existent at this point - except for command line help.
The `doc` directory currently contains design fragments - you will be mislead by them as they
are nor describing the current situations nor are they showing the future.


## Install instructions

Ensure you have Python installed.

Run `make executables` to create the `bead` tool:

```
$ python build.py
```

This generates one-file executables for unix, mac, and windows in the `executables` directory:
- `bead` unix & mac
- `bead.cmd` windows

Move/copy the `bead` binary for your platform to some directory on your `PATH`.

E.g.

```
$ cp executables/bead ~/.local/bin
```

If you test it, please give [feedback](../../issues) on
- general usability
- misleading/unclear help (currently: command line help)
- what is missing (I know about documentation)
- what is not working as you would expect

Any other nuisance reported - however minor you think it be - is important and welcome!

Thank you for your interest!


## TODOs

Updated by script ([./ci](https://github.com/e3krisztian/bead/blob/master/ci)), text in this section and afterwards will be overwritten

- [FIXME: die with message when directory already exists](https://github.com/e3krisztian/bead/blob/master/bead_cli/workspace.py#L49)
- [FIXME: robot: environment file should be built by a function in environment](https://github.com/e3krisztian/bead/blob/master/bead_cli/test_robot.py#L36)
- [FIXME: test_archive.given_a_bead is fragile and yields an invalid BEAD](https://github.com/e3krisztian/bead/blob/master/bead/test_archive.py#L46)
- [from tracelog import TRACELOG  # TODO: remove TRACELOG](https://github.com/e3krisztian/bead/blob/master/bead/box.py#L10)
- [TODO: add tests for timestamps, parse_iso8601, parse_timedelta](https://github.com/e3krisztian/bead/blob/master/bead/tech/timestamp.py#L232)
- [TODO: Box: support user maintained directory hierarchy](https://github.com/e3krisztian/bead/blob/master/bead/box.py#L143)
- [TODO: update: assert there is no other argument](https://github.com/e3krisztian/bead/blob/master/bead_cli/input.py#L113)
- [TODO: use a template and render it with passing in all data](https://github.com/e3krisztian/bead/blob/master/bead_cli/workspace.py#L229)
- [XXX: cli parsing: revisit when python 2.x no longer supported](https://github.com/e3krisztian/bead/blob/master/bead_cli/cmdparse.py#L86)
- [XXX: directory itself might be a pattern - is it OK?](https://github.com/e3krisztian/bead/blob/master/bead/box.py#L186)
- [XXX: introspect parameter names, default values, annotations?](https://github.com/e3krisztian/bead/blob/master/bead_cli/cmdparse.py#L121)
- [XXX: is find_beads in use still?](https://github.com/e3krisztian/bead/blob/master/bead/box.py#L158)
- [XXX: list command: use tabulate?](https://github.com/e3krisztian/bead/blob/master/bead_cli/box.py#L60)
- [XXX: try to load smaller inputs?](https://github.com/e3krisztian/bead/blob/master/bead_cli/workspace.py#L159)
- [XXX: (usability) save - support saving directly to a directory outside of workspace](https://github.com/e3krisztian/bead/blob/master/bead_cli/workspace.py#L89)
