from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from ..test import TestCase
from testtools.matchers import Not, Contains

from . import fixtures


class Test_status(TestCase, fixtures.RobotAndBeads):

    # tests

    def test(self, robot, beads, bead_with_inputs, bead_a):
        robot.cli('develop', bead_with_inputs)
        robot.cd(bead_with_inputs)
        robot.cli('status')

        self.assertThat(robot.stdout, Contains(bead_with_inputs))
        self.assertThat(robot.stdout, Contains(bead_a))

        bead_a = beads[bead_a]
        bead_with_inputs = beads[bead_with_inputs]
        self.assertThat(robot.stdout, Not(Contains(bead_with_inputs.bead_uuid)))
        self.assertThat(robot.stdout, Not(Contains(bead_a.bead_uuid)))
        self.assertThat(robot.stdout, Contains(bead_a.timestamp_str))
        self.assertThat(robot.stdout, Not(Contains(bead_a.content_hash)))

    def test_verbose(self, robot, beads, bead_with_inputs, bead_a):
        robot.cli('develop', bead_with_inputs)
        robot.cd(bead_with_inputs)
        robot.cli('status', '-v')

        self.assertThat(robot.stdout, Contains(bead_with_inputs))
        self.assertThat(robot.stdout, Contains(bead_a))

        bead_a = beads[bead_a]
        bead_with_inputs = beads[bead_with_inputs]
        self.assertThat(robot.stdout, Contains(bead_with_inputs.bead_uuid))
        self.assertThat(robot.stdout, Contains(bead_a.bead_uuid))
        self.assertThat(robot.stdout, Contains(bead_a.timestamp_str))
        self.assertThat(robot.stdout, Contains(bead_a.content_hash))

    def test_inputs_not_in_known_repos(
            self, robot, beads, bead_with_inputs, bead_a):
        robot.cli('develop', bead_with_inputs)
        robot.cd(bead_with_inputs)

        robot.reset()
        robot.cli('status')

        self.assertThat(robot.stdout, Contains(bead_with_inputs))
        self.assertThat(robot.stdout, Not(Contains(bead_a)))

        bead_a = beads[bead_a]
        self.assertThat(robot.stdout, Contains(bead_with_inputs))
        self.assertThat(robot.stdout, Contains(bead_a.bead_uuid))
        self.assertThat(robot.stdout, Contains(bead_a.timestamp_str))
        self.assertThat(robot.stdout, Contains(bead_a.content_hash))

    def test_verbose_inputs_not_in_known_repos(
            self, robot, beads, bead_with_inputs, bead_a):
        robot.cli('develop', bead_with_inputs)
        robot.cd(bead_with_inputs)
        robot.reset()
        robot.cli('status', '--verbose')

        self.assertThat(robot.stdout, Contains(bead_with_inputs))
        self.assertThat(robot.stdout, Not(Contains(bead_a)))

        bead_a = beads[bead_a]
        bead_with_inputs = beads[bead_with_inputs]
        self.assertThat(robot.stdout, Contains(bead_with_inputs.bead_uuid))
        self.assertThat(robot.stdout, Contains(bead_a.bead_uuid))
        self.assertThat(robot.stdout, Contains(bead_a.timestamp_str))
        self.assertThat(robot.stdout, Contains(bead_a.content_hash))

    def test_invalid_workspace(self, robot):
        robot.cli('status')
        self.assertThat(robot.stderr, Contains('WARNING'))
