from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import os
import sys

from bead.workspace import Workspace, CurrentDirWorkspace
from bead import spec as bead_spec
from bead.archive import Archive
from bead import repos
from . import arg_help
from . import arg_metavar
from bead.tech.timestamp import time_from_user
from .environment import Environment

ERROR_EXIT = 1


def die(msg):
    sys.stderr.write('ERROR: ')
    sys.stderr.write(msg)
    sys.stderr.write('\n')
    sys.exit(ERROR_EXIT)


def warning(msg):
    sys.stderr.write('WARNING: ')
    sys.stderr.write(msg)
    sys.stderr.write('\n')


def OPTIONAL_WORKSPACE(parser):
    '''
    Define `workspace` as option, defaulting to current directory
    '''
    parser.arg(
        '--workspace', '-w', metavar=arg_metavar.WORKSPACE,
        type=Workspace, default=CurrentDirWorkspace(),
        help=arg_help.WORKSPACE)


class get_env:
    '''
    Make an Environment when called.

    It will also create a missing config directory and provides a meaningful
    text when used as default for an argparse argument.
    '''

    def __init__(self, config_dir):
        self.config_dir = config_dir

    def __call__(self):
        config_dir = self.config_dir
        try:
            os.makedirs(config_dir)
        except OSError:
            assert os.path.isdir(config_dir)
        return Environment(config_dir / 'env.json')

    def __repr__(self):
        return 'Environment at {}'.format(self.config_dir)


def OPTIONAL_ENV(parser):
    '''
    Define `env` as option, defaulting to environment config in user's home directory
    '''
    config_dir = parser.defaults['config_dir']
    parser.arg(
        '--environment', metavar=arg_metavar.ENV,
        dest='get_env',
        type=get_env, default=get_env(config_dir),
        help=arg_help.ENV)


class DefaultArgSentinel(object):
    '''
    I am a sentinel for default values.

    I.e. If you see me, it means that you got the default value.

    I also provide human sensible description for the default value.
    '''

    def __init__(self, description):
        self.description = description

    def __repr__(self):
        return self.description


def tag(tag, parse):
    '''
    Make a function that parses and tags its input

    parse is a function with one parameter,
    it is expected to raise a ValueError if there is any problem
    '''
    return lambda value: (tag, parse(value))


def _parse_time(timeish):
    return time_from_user(timeish)


def _parse_start_of_name(name):
    return name + '*'


def arg_bead_query(parser):
    group = parser.argparser.add_argument_group(
        'bead query',
        'Restrict the bead version with these options')
    arg = group.add_argument
    # TODO: implement more options
    # -r, --repo, --repository

    # bead_filters
    BEAD_QUERY = 'bead_query'
    arg('-o', '--older', '--older-than', dest=BEAD_QUERY,
        metavar='TIMEDEF', type=tag(bead_spec.OLDER_THAN, _parse_time))
    arg('-n', '--newer', '--newer-than', dest=BEAD_QUERY,
        metavar='TIMEDEF', type=tag(bead_spec.NEWER_THAN, _parse_time))
    arg('--start-of-name', dest=BEAD_QUERY,
        metavar='START-OF-BEAD-NAME',
        type=tag(bead_spec.BEAD_NAME_GLOB, _parse_start_of_name))

    # match reducers
    # -N, --next
    # -P, --prev, --previous
    # --newest, --latest (default)
    # --oldest

BEAD_QUERY = arg_bead_query


def arg_bead_ref_base(nargs, default):
    '''
    Declare bead_ref_base argument - either a name or a file or something special
    '''
    def declare(parser):
        parser.arg(
            'bead_ref_base', metavar=arg_metavar.BEAD_REF, help=arg_help.BEAD_REF,
            nargs=nargs, type=str, default=default)
    return declare


def BEAD_REF_BASE_defaulting_to(name):
    return arg_bead_ref_base(nargs='?', default=name)

BEAD_REF_BASE = arg_bead_ref_base(nargs=None, default=None)


class BeadReference:
    bead = Archive
    default_workspace = Workspace


class ArchiveReference(BeadReference):
    def __init__(self, archive_path):
        self.archive_path = archive_path

    @property
    def bead(self):
        if os.path.isfile(self.archive_path):
            return Archive(self.archive_path)
        raise LookupError('Not a file', self.archive_path)

    @property
    def default_workspace(self):
        return Workspace(self.bead.name)


class RepoQueryReference(BeadReference):
    def __init__(self, workspace_name, query, repositories, index=-1):
        # index: like python list indices 0 = first, -1 = last
        self.workspace_name = workspace_name
        self.query = query
        if index < 0:
            self.order = bead_spec.NEWEST_FIRST
            self.limit = -index
        else:
            self.order = bead_spec.OLDEST_FIRST
            self.limit = index + 1
        self.repositories = list(repositories)

    @property
    def bead(self):
        matches = []
        for repo in self.repositories:
            matches.extend(repo.find_beads(self.query, self.order, self.limit))
            # XXX: order_and_limit_beads is called twice - first in find_beads
            matches = repos.order_and_limit_beads(matches, self.order, self.limit)
        if len(matches) == self.limit:
            return matches[-1]
        raise LookupError

    @property
    def default_workspace(self):
        return Workspace(self.workspace_name)


def get_bead_ref(env, bead_ref_base, bead_query):
    if os.path.sep in bead_ref_base and os.path.isfile(bead_ref_base):
        return ArchiveReference(bead_ref_base)

    query = list(bead_query or [])

    if bead_ref_base:
        query = [(bead_spec.BEAD_NAME_GLOB, bead_ref_base)] + query

    # TODO: calculate and add index parameter (--next, --prev)
    return RepoQueryReference(bead_ref_base, query, env.get_repos())
