from bead.test import TestCase

from . import test_fixtures as fixtures


class Test_status(TestCase, fixtures.RobotAndBeads):

    # tests

    def test(self, robot, beads, bead_with_inputs, bead_a):
        robot.cli('develop', bead_with_inputs)
        robot.cd(bead_with_inputs)
        robot.cli('input', 'load', 'input_a')
        robot.cli('status')

        assert bead_with_inputs in robot.stdout
        assert bead_a in robot.stdout

        bead_a = beads[bead_a]
        bead_with_inputs = beads[bead_with_inputs]
        assert bead_with_inputs.kind not in robot.stdout
        assert bead_a.kind not in robot.stdout
        assert bead_a.timestamp_str in robot.stdout
        assert bead_a.content_id not in robot.stdout

    def test_verbose(self, robot, beads, bead_with_inputs, bead_a):
        robot.cli('develop', bead_with_inputs)
        robot.cd(bead_with_inputs)
        robot.cli('status', '-v')

        assert bead_with_inputs in robot.stdout
        assert bead_a in robot.stdout

        bead_a = beads[bead_a]
        bead_with_inputs = beads[bead_with_inputs]
        assert bead_with_inputs.kind in robot.stdout
        assert bead_a.kind in robot.stdout
        assert bead_a.timestamp_str in robot.stdout
        assert bead_a.content_id in robot.stdout

    def test_inputs_not_in_known_boxes(
            self, robot, beads, bead_with_inputs, bead_a):
        robot.cli('develop', bead_with_inputs)
        robot.cd(bead_with_inputs)

        robot.reset()
        robot.cli('status')

        assert bead_with_inputs in robot.stdout
        assert 'no candidates :(' in robot.stdout

        bead_a = beads[bead_a]
        assert bead_with_inputs in robot.stdout
        assert bead_a.timestamp_str in robot.stdout

    def test_verbose_inputs_not_in_known_boxes(
            self, robot, beads, bead_with_inputs, bead_a):
        robot.cli('develop', bead_with_inputs)
        robot.cd(bead_with_inputs)
        robot.reset()
        robot.cli('status', '--verbose')

        assert bead_with_inputs in robot.stdout
        assert 'no candidates :(' in robot.stdout

        bead_a = beads[bead_a]
        bead_with_inputs = beads[bead_with_inputs]
        assert bead_with_inputs.kind in robot.stdout
        assert bead_a.kind in robot.stdout
        assert bead_a.timestamp_str in robot.stdout
        assert bead_a.content_id in robot.stdout

    def test_invalid_workspace(self, robot):
        robot.cli('status')
        assert 'WARNING' in robot.stderr
