import os
import subprocess
import sys
import textwrap
import traceback

from collections.abc import Sequence

import appdirs
from .cmdparse import Parser, Command

from bead.tech.fs import Path
from bead.tech.timestamp import timestamp
from .common import warning
from . import workspace
from . import input
from . import box
from .web import commands as web


def output_of(shell_cmd):
    return subprocess.check_output(shell_cmd, shell=True).decode('utf-8').strip()


class _git:
    def __init__(self):
        try:
            from . import git_info
        except ImportError:
            self.repo = output_of('git config --get remote.origin.url')
            self.branch = output_of('git branch --show-current')
            self.date = output_of("git show HEAD --pretty=tformat:'%cI' --no-patch")
            self.commit = output_of("git show HEAD --pretty=tformat:'%H' --no-patch")
            self.tag = output_of('git describe --tags')
            modified_files = [
                line for line in output_of('git status --porcelain=1').splitlines()
                if not line.startswith('??') and ' bead_cli/git_info.py' not in line]
            self.dirty = modified_files != []
        else:
            self.repo = git_info.GIT_REPO
            self.branch = git_info.GIT_BRANCH
            self.date = git_info.GIT_DATE
            self.commit = git_info.GIT_HASH
            self.tag = git_info.TAG_VERSION
            self.dirty = git_info.DIRTY

        self.version_info = textwrap.dedent(
            '''
            Python:
            ------
            {sys.version}

            Bead source:
            -----------
            origin:  {self.repo}
            branch:  {self.branch}
            date:    {self.date}
            hash:    {self.commit}
            version: {self.tag}{version_suffix}
            '''
        ).format(self=self, sys=sys, version_suffix='-dirty' if self.dirty else '')


git = _git()


class CmdVersion(Command):
    '''
    Show program version info
    '''

    def run(self, args):
        print(git.version_info)


def make_argument_parser(defaults):
    parser = Parser.new(defaults)
    (parser
        .commands(
            ('new', workspace.CmdNew, 'Create and initialize new workspace directory with a new bead.'),
            ('develop', workspace.CmdDevelop, 'Create workspace from specified bead.'),
            ('save', workspace.CmdSave, 'Save workspace in a box.'),
            ('status', workspace.CmdStatus, 'Show workspace information.'),
            ('web', web.CmdWeb, 'Manage/visualize the big picture - connections between beads.'),
            ('zap', workspace.CmdZap, 'Delete workspace.'),
            ('xmeta', box.CmdXmeta, 'eXport eXtended meta attributes to a file next to zip archive.'),
            ('version', CmdVersion, 'Show program version.'),
        ))

    (parser
        .group('input', 'Manage data loaded from other beads')
        .commands(
            ('add', input.CmdAdd, 'Define dependency and load its data.'),
            ('delete', input.CmdDelete, 'Forget all about an input.'),
            ('rm', input.CmdDelete, 'Forget all about an input. (alias for delete)'),
            ('map', input.CmdMap, 'Change the name of the bead from which the input is loaded/updated.'),
            ('update', input.CmdUpdate, 'Update input[s] to newest version or defined bead.'),
            ('load', input.CmdLoad, 'Load data from already defined dependency.'),
            ('unload', input.CmdUnload, 'Unload input data.'),
        ))

    (parser
        .group('box', 'Manage bead boxes')
        .commands(
            ('add', box.CmdAdd, 'Define a box.'),
            ('list', box.CmdList, 'Show known boxes.'),
            ('forget', box.CmdForget, 'Forget a known box.'),
            ('rewire', box.CmdRewire, 'Remap inputs.'),
        ))

    return parser


def run(config_dir: str, argv: Sequence[str]):
    parser_defaults = dict(config_dir=Path(config_dir))
    parser = make_argument_parser(parser_defaults)
    return parser.dispatch(argv)


FAILURE_TEMPLATE = """\
{exception}

If you are using the latest version, and have not reported this error yet
please report this problem by copy-pasting the content of file {error_report}
at {repo}/issues/new
and/or attaching the file to an email to {dev}@gmail.com.

Please make sure you copy-paste from the file {error_report}
and not from the console, as the shown exception text was shortened
for your convenience, thus it is not really helpful in fixing the bug.
"""


def main(run=run):
    if git.dirty:
        warning('test build, DO NOT USE for production!!!')
    config_dir = appdirs.user_config_dir(
        'bead_cli-6a4d9d98-8e64-4a2a-b6c2-8a753ea61daf')
    try:
        retval = run(config_dir, sys.argv[1:])
    except KeyboardInterrupt:
        print("Interrupted :(", file=sys.stderr)
        retval = -1
    except SystemExit:
        raise
    except BaseException:
        # all remaining errors are catched - including RunTimeErrors
        sys_argv = f'{sys.argv!r}'
        exception = traceback.format_exc()
        short_exception = traceback.format_exc(limit=1)
        error_report = os.path.abspath(f'error_{timestamp()}.txt')
        with open(error_report, 'w') as f:
            f.write(f'sys_argv = {sys_argv}\n')
            f.write(f'{exception}\n')
            f.write(f'{git.version_info}\n')
            if git.dirty:
                f.write('WARNING: TEST BUILD, UNKNOWN, UNCOMMITTED CHANGES !!!\n')
        print(
            FAILURE_TEMPLATE.format(
                exception=short_exception,
                error_report=error_report,
                repo='https://github.com/e3krisztian/bead',
                dev='e3krisztian',
            ),
            file=sys.stderr
        )
        retval = -1
    sys.exit(retval)


if __name__ == '__main__':
    main()
