"""Public, synthetic guard tests. Never import private instructor code."""
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
from unittest import TestCase, mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import private_ci_bridge as bridge


class ProtectedBridgeTests(TestCase):
    def test_absent_checkout_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(bridge.GateBlocked, 'CHECKOUT_MISSING'):
                bridge.validate_private_commit(Path(folder) / 'missing')

    def test_unexpected_checkout_sha_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            spoof = mock.Mock(returncode=0, stdout='00' * 20 + '\n')
            with mock.patch.object(bridge.subprocess, 'run', return_value=spoof):
                with self.assertRaisesRegex(bridge.GateBlocked, 'PRIVATE_SHA_MISMATCH'):
                    bridge.validate_private_commit(folder)

    def test_junit_zero_tests_can_never_count_as_pass(self):
        with tempfile.TemporaryDirectory() as folder:
            xml = Path(folder) / 'zero.xml'
            xml.write_text('<testsuites><testsuite tests="0" failures="0" errors="0" skipped="0"/></testsuites>')
            with mock.patch.object(bridge.subprocess, 'run', return_value=mock.Mock(returncode=0)):
                sink = io.StringIO()
                with contextlib.redirect_stdout(sink):
                    with self.assertRaisesRegex(bridge.GateBlocked, 'PRIVATE_STAGE_BLOCKED'):
                        bridge.scrubbed_run('UNIT', ['ignored'], folder, {}, folder, 3, xml)
                self.assertIn('"status": "BLOCKED"', sink.getvalue())

    def test_private_output_never_reaches_public_stdout(self):
        with tempfile.TemporaryDirectory() as folder:
            private_marker = 'INSTRUCTOR_HIDDEN_TEST_TOP_SECRET_STRING'
            def synthetic_run(command, cwd, env, stdout, stderr, timeout, check):
                stdout.write(private_marker.encode('utf-8'))
                return mock.Mock(returncode=0)
            capture = io.StringIO()
            with mock.patch.object(bridge.subprocess, 'run', side_effect=synthetic_run):
                with contextlib.redirect_stdout(capture):
                    result = bridge.scrubbed_run('UNIT', ['ignored'], folder, {}, folder, 3)
            self.assertNotIn(private_marker, capture.getvalue())
            self.assertFalse(result['private_log_uploaded'])
            self.assertTrue((Path(folder) / 'unit.private.log').read_text().startswith(private_marker))

    def test_empty_report_fails_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(bridge.GateBlocked, 'PRIVATE_REPORT_MISSING'):
                bridge.verify_gazebo_report(folder, 3)

    def test_report_requires_no_acceptance_promotion(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'prelocal_report.json').write_text(json.dumps({
                'status': 'P1_PRELOCAL_PARTIAL_3X', 'passed_runs': 3,
                'gate_accepted': True}))
            with self.assertRaisesRegex(bridge.GateBlocked, 'PRIVATE_REPORT_GATE_BLOCKED'):
                bridge.verify_gazebo_report(root, 3)
    def test_skipped_tests_fail_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            xml = Path(folder) / 'skipped.xml'
            xml.write_text('<testsuites><testsuite tests="2" failures="0" errors="0" skipped="1"/></testsuites>')
            with mock.patch.object(bridge.subprocess, 'run', return_value=mock.Mock(returncode=0)):
                capture = io.StringIO()
                with contextlib.redirect_stdout(capture):
                    with self.assertRaisesRegex(bridge.GateBlocked, 'PRIVATE_STAGE_BLOCKED'):
                        bridge.scrubbed_run('UNIT', ['ignored'], folder, {}, folder, 3, xml)
                self.assertIn('"status": "BLOCKED"', capture.getvalue())

    def test_ros_pythonpath_is_preserved_with_private_paths(self):
        """Regression: old bridge replaced Jazzy site-packages -> all ROS tests skipped."""
        with tempfile.TemporaryDirectory() as root:
            base = {'PYTHONPATH': '/opt/ros/jazzy/lib/python3.12/site-packages',
                    'ROS_DOMAIN_ID': '0'}
            env = bridge.private_runtime_env(root, base)
            self.assertIn('/opt/ros/jazzy/lib/python3.12/site-packages',
                          env['PYTHONPATH'].split(':'))
            self.assertEqual(env['PYTHONPATH'].split(':')[0],
                             str(Path(root) / 'ros2_ws/src/axia_safety_supervisor'))
            self.assertEqual(env['ROS_DOMAIN_ID'], '167')
            self.assertEqual(env['GITHUB_SHA'], bridge.PIN)
            self.assertEqual(base['ROS_DOMAIN_ID'], '0')

    def test_ros_overlay_sources_setup_before_pytest_without_shell_injection(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'install' / 'setup.bash'
            cmd = bridge.bash_with_ros_overlay(path, ['python3', '-m', 'pytest', '-q'])
            self.assertEqual(cmd[0:2], ['bash', '-c'])
            self.assertEqual(cmd[4], str(path))
            self.assertEqual(cmd[5:], ['python3', '-m', 'pytest', '-q'])
            self.assertIn('source "$1"', cmd[2])

    def test_build_fails_closed_when_package_not_installed(self):
        with tempfile.TemporaryDirectory() as root:
            env = {}
            calls = []
            def fake_scrubbed(stage, command, workdir, env, tmpdir, limit):
                calls.append(stage)
            with mock.patch.object(bridge, 'scrubbed_run', side_effect=fake_scrubbed):
                with self.assertRaisesRegex(bridge.GateBlocked, 'COLCON_SETUP_MISSING'):
                    bridge.ros_workspace_build(Path(root), env, Path(root))
            self.assertEqual(calls, ['ROS_RUNTIME_IMPORT', 'COLCON_BUILD'])
