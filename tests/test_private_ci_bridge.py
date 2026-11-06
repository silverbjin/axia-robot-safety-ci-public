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

    def test_no_motion_gazebo_threefold_cannot_promote_final_gate(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'prelocal_report.json'
            source.write_text(json.dumps({
                'status': 'P1_PRELOCAL_PARTIAL_3X', 'passed_runs': 3,
                'gate_accepted': False,
                'g03_g04_gazebo_fault_acceptance': 'NOT_RUN'
            }), encoding='utf-8')
            with contextlib.redirect_stdout(io.StringIO()) as buffer:
                bridge.verify_gazebo_report(folder, 3)
            self.assertIn('READONLY_READY_ONLY', buffer.getvalue())
            self.assertIn('"goal_sent": false', buffer.getvalue())
            self.assertIn('"gate_accepted": false', buffer.getvalue())

    def test_tenfold_requires_full_count_and_no_fault_acceptance(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'prelocal_report.json'
            source.write_text(json.dumps({
                'status': 'P1_PRELOCAL_STABILITY_10X_READY', 'passed_runs': 9,
                'gate_accepted': False,
                'g03_g04_gazebo_fault_acceptance': 'NOT_RUN'
            }), encoding='utf-8')
            with self.assertRaisesRegex(bridge.GateBlocked, 'PRIVATE_REPORT_GATE_BLOCKED'):
                bridge.verify_gazebo_report(folder, 10)
            source.write_text(json.dumps({
                'status': 'P1_PRELOCAL_STABILITY_10X_READY', 'passed_runs': 10,
                'gate_accepted': False,
                'g03_g04_gazebo_fault_acceptance': 'ACCEPTED'
            }), encoding='utf-8')
            with self.assertRaisesRegex(bridge.GateBlocked, 'PRIVATE_REPORT_GATE_BLOCKED'):
                bridge.verify_gazebo_report(folder, 10)

    def test_real_ros_fault_files_target_pinned_private_repo(self):
        self.assertEqual(len(bridge.FAKE_FAULT_FILES), 3)
        self.assertIn('tests/ros_integration/test_p1_t06_faults.py',
                      bridge.FAKE_FAULT_FILES)
        self.assertIn('tests/ros_integration/test_p1_t04_action.py',
                      bridge.FAKE_FAULT_FILES)
        self.assertIn('tests/ros_integration/test_p1_t05_launch.py',
                      bridge.FAKE_FAULT_FILES)

    def test_private_evidence_diagnostics_redacts_arbitrary_source_strings(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            record = root / 'run_1'
            record.mkdir()
            secret = 'PRIVATE_INSTRUCTOR_SOURCE_OR_TOKEN_SHOULD_NEVER_LOG'
            (record / 'startup_verdict.json').write_text(json.dumps({
                'status': secret, 'failed_gate': secret,
                'stages': [{'status': 'PASS', 'detail': secret}]
            }))
            (record / 'scan_timing.json').write_text(json.dumps({
                'status': 'SCAN_TIMING_REQUIRES_CALIBRATION',
                'gaps_over_timeout_total': 7, 'reason': secret,
            }))
            capture = io.StringIO()
            with contextlib.redirect_stdout(capture):
                records = bridge.private_evidence_diagnostics(root, 1)
            self.assertNotIn(secret, capture.getvalue())
            self.assertIn('"startup": "UNRECOGNIZED"', capture.getvalue())
            self.assertIn('"startup_failed_gate": "UNRECOGNIZED"', capture.getvalue())
            self.assertEqual(records[0]['scan_gaps_over_0_5s'], 7)

    def test_private_evidence_diagnostics_missing_cannot_pass(self):
        with tempfile.TemporaryDirectory() as folder:
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                records = bridge.private_evidence_diagnostics(folder, 3)
            self.assertEqual(len(records), 3)
            self.assertTrue(all(not x['gate_accepted'] for x in records))
            self.assertTrue(all(x['startup'] == 'MISSING' for x in records))

    def test_clock_reason_must_be_allowlisted_without_raw_private_diagnostic(self):
        with tempfile.TemporaryDirectory() as root:
            folder = Path(root) / 'run_1'
            folder.mkdir()
            secret = 'DO_NOT_PRINT_A_HIDDEN_STACKTRACE'
            (folder / 'clock_diagnostics.json').write_text(json.dumps({
                'status': 'BLOCKED', 'reason': secret, 'exception': secret
            }), encoding='utf-8')
            capture = io.StringIO()
            with contextlib.redirect_stdout(capture):
                rows = bridge.private_evidence_diagnostics(root, 1)
            self.assertEqual(rows[0]['clock_probe_reason'], 'UNRECOGNIZED')
            self.assertNotIn(secret, capture.getvalue())

    def test_redacted_supervisor_callback_rtf_and_shutdown_cannot_print_private_values(self):
        with tempfile.TemporaryDirectory() as root:
            folder = Path(root) / 'run_1'
            folder.mkdir()
            secret = 'PRIVATE_SUPERVISOR_STACKTRACE_NO_PUBLISH'
            (folder / 'supervisor_prestart.json').write_text(json.dumps({
                'last_message': {'health_diagnostics': {
                    'scan_callback_intervals': 50,
                    'scan_callback_gaps_over_timeout': 2,
                    'scan_callback_invalid_intervals': 0,
                    'scan_callback_max_gap_sec': 0.62,
                    'raw_trace': secret}},
                'clock_rtf': {'status': 'RTF_OBSERVED', 'rtf': 0.8, 'trace': secret}
            }))
            (folder / 'shutdown_verdict.json').write_text(json.dumps({
                'status': 'SHUTDOWN_INCONCLUSIVE',
                'lifecycle_shutdown_acknowledged': False,
                'fatal_signatures': [secret]
            }))
            capture = io.StringIO()
            with contextlib.redirect_stdout(capture):
                rows = bridge.private_evidence_diagnostics(root, 1)
            self.assertNotIn(secret, capture.getvalue())
            self.assertEqual(rows[0]['callback_intervals'], 50)
            self.assertEqual(rows[0]['callback_gaps_over_0_5s'], 2)
            self.assertEqual(rows[0]['rtf'], 0.8)
            self.assertEqual(rows[0]['shutdown_fatal_count'], 1)
            self.assertEqual(rows[0]['shutdown'], 'SHUTDOWN_INCONCLUSIVE')

    def test_private_rtm_failure_allowlist_never_prints_private_filenames(self):
        with tempfile.TemporaryDirectory() as root:
            folder = Path(root) / 'run_1'
            folder.mkdir()
            secret = 'INSTRUCTOR_PRIVATE_FILE_NAME_OR_PATH'
            (Path(root) / 'prelocal_report.json').write_text(json.dumps({
                'runs': [{'run_id': 1, 'status': 'BLOCKED',
                          'failures': ['SUPERVISOR_SCAN_CALLBACK_OVERRUN',
                                       'SHA_MISMATCH:' + secret, secret]}]
            }), encoding='utf-8')
            capture = io.StringIO()
            with contextlib.redirect_stdout(capture):
                rows = bridge.private_evidence_diagnostics(root, 1)
            self.assertEqual(rows[0]['rtm_blockers'],
                ['SUPERVISOR_SCAN_CALLBACK_OVERRUN', 'SHA_MISMATCH',
                 'UNRECOGNIZED'])
            self.assertNotIn(secret, capture.getvalue())

    def test_ros_fake_suite_isolation_has_unique_domain_and_process(self):
        suites = bridge.isolated_fault_suites()
        self.assertEqual(len(suites), 3)
        self.assertEqual(len({s[0] for s in suites}), 3)
        self.assertEqual(len({s[2] for s in suites}), 3)
        self.assertEqual([s[1] for s in suites], list(bridge.FAKE_FAULT_FILES))
        self.assertTrue(all(0 < s[2] < 232 for s in suites))

    def test_t06_collection_is_exact_and_private_case_names_not_logged(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'private_tests.py'
            private_marker = 'hidden_secret_identifier'
            path.write_text(''.join(
                f'def test_{private_marker}_{index}(): pass\n'
                for index in range(7)), encoding='utf-8')
            result = bridge.private_pytest_cases(path)
            self.assertEqual(len(result), 7)
            self.assertTrue(all(private_marker in x for x in result))
            path.write_text('def test_only_one(): pass\n', encoding='utf-8')
            with self.assertRaisesRegex(bridge.GateBlocked, 'T06_COLLECTION_MISMATCH'):
                bridge.private_pytest_cases(path)

    def test_t06_failure_classifier_returns_only_published_enum(self):
        with tempfile.TemporaryDirectory() as temp:
            marker = 'HIDDEN_PRIVATE_TRACE_ABC'
            junit = Path(temp) / 'run.xml'
            junit.write_text(
                '<testsuite tests="1" failures="1">'
                '<testcase classname="hidden" name="hidden">'
                '<failure message="Goal authorization missing; ' + marker + '">'
                + marker + '</failure></testcase></testsuite>', encoding='utf-8')
            capture = io.StringIO()
            with contextlib.redirect_stdout(capture):
                reason = bridge.classify_private_junit_failure(junit)
            self.assertEqual(reason, 'GOAL_AUTHORIZATION')
            self.assertNotIn(marker, capture.getvalue())

    def test_t06_each_case_uses_unique_domain_and_subprocess(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            p = root / bridge.FAKE_FAULT_FILES[0]
            p.parent.mkdir(parents=True)
            p.write_text(''.join(f'def test_synthetic_{i}(): pass\n'
                                 for i in range(7)), encoding='utf-8')
            calls = []
            def fake_scrub(stage, cmd, cwd, env, tmpdir, duration, junit=None):
                calls.append((stage, cmd, env.get('ROS_DOMAIN_ID')))
            with mock.patch.object(bridge, 'scrubbed_run', side_effect=fake_scrub):
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    bridge.run_isolated_t06(root, {}, root, root / 'install/setup.bash')
            self.assertEqual([x[0] for x in calls],
                             [f'T06_R{repeat}_CASE_{i:02d}'
                              for repeat in range(1,4) for i in range(1,8)])
            self.assertEqual([x[2] for x in calls],
                             [str(i) for i in range(181,202)])
            self.assertIn('"blocked_cases": 0', output.getvalue())
            self.assertIn('"repetitions": 3', output.getvalue())
            self.assertNotIn('test_synthetic_', output.getvalue())

    def test_t06_isolated_failures_never_publish_private_tracebacks(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            p = root / bridge.FAKE_FAULT_FILES[0]
            p.parent.mkdir(parents=True)
            p.write_text(''.join(f'def test_synthetic_{i}(): pass\n'
                                 for i in range(7)), encoding='utf-8')
            marker = 'SECRET_JUNIT_TEST_BODY'
            def fake_scrub(stage, cmd, cwd, env, tmpdir, duration, junit=None):
                if stage in ('T06_R2_CASE_02', 'T06_R3_CASE_05'):
                    Path(junit).write_text(
                        '<testsuite tests="1" failures="1"><testcase>'
                        '<failure message="initial health never ready"> '
                        + marker + '</failure></testcase></testsuite>', encoding='utf-8')
                    raise bridge.GateBlocked('PRIVATE_STAGE_BLOCKED')
            output = io.StringIO()
            with mock.patch.object(bridge, 'scrubbed_run', side_effect=fake_scrub):
                with contextlib.redirect_stdout(output):
                    with self.assertRaisesRegex(bridge.GateBlocked, 'T06_ISOLATED_CASES_BLOCKED'):
                        bridge.run_isolated_t06(root, {}, root, root / 'install/setup.bash')
            self.assertIn('"blocked_cases": 2', output.getvalue())
            self.assertIn('"case": "T06-02"', output.getvalue())
            self.assertIn('"repeat": 2', output.getvalue())
            self.assertIn('"case": "T06-05"', output.getvalue())
            self.assertIn('"repeat": 3', output.getvalue())
            self.assertIn('"reason": "BOOT_HEALTH"', output.getvalue())
            self.assertNotIn(marker, output.getvalue())
            self.assertNotIn('test_synthetic_', output.getvalue())

    def test_parallel_workflow_independent_core_gates_and_strict_aggregation(self):
        text = (Path(__file__).resolve().parents[1] /
                '.github/workflows/instructor-sealed-bridge.yml').read_text()
        self.assertIn('fail-fast: false', text)
        self.assertIn('unit-middleware', text)
        self.assertIn('fake-faults', text)
        self.assertIn('gazebo3', text)
        self.assertIn('instructor-prelocal-aggregate:', text)
        self.assertIn("needs.instructor-core.result", text)
        self.assertIn('gate_accepted=false', text)
        self.assertNotIn('pull_request_target:', text)
        self.assertIn('persist-credentials: false', text)

    def test_private_diagnostic_window_teardown_is_allowlisted_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run = root / 'run_1'
            run.mkdir()
            secret = 'PRIVATE_SUPERVISOR_TRACE_NEVER_IN_PUBLIC_LOG'
            (root / 'prelocal_report.json').write_text(json.dumps({
                'observation_warnings': [
                    'run_1:BOOT_CALLBACK_OVERRUN_BEFORE_STABLE_WINDOW',
                    'run_1:' + secret]}), encoding='utf-8')
            (run / 'supervisor_prestart.json').write_text(json.dumps({
                'observer_scan_intervals': 21,
                'observer_scan_gaps_over_0p5s': 1,
                'observer_scan_max_gap_sec': 0.55,
                'scan_stable_window': {'status': 'WINDOW_VERIFIED',
                    'intervals': 15, 'over_0p5s': 0, 'invalid': 0},
                'clock_rtf': {'status': 'RTF_OBSERVED', 'rtf': 1.0,
                              'clock_samples': 34, 'secret': secret}
            }), encoding='utf-8')
            (run / 'shutdown_control.json').write_text(json.dumps({
                'status': 'SHUTDOWN_BLOCKED', 'reason': secret,
                'managers': {
                    'navigation': {'success': False,
                                   'discovery_wall_sec': 0.61,
                                   'response_wall_sec': 45.1,
                                   'secret': secret}}
            }), encoding='utf-8')
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rows = bridge.private_evidence_diagnostics(root, 1)
            self.assertNotIn(secret, output.getvalue())
            self.assertEqual(rows[0]['observer_scan_gaps_over_0_5s'], 1)
            self.assertEqual(rows[0]['scan_window_status'], 'WINDOW_VERIFIED')
            self.assertEqual(rows[0]['clock_samples'], 34)
            self.assertEqual(rows[0]['shutdown_control_reason'], 'UNRECOGNIZED')
            self.assertEqual(rows[0]['navigation_shutdown_ack'], False)
            self.assertEqual(rows[0]['navigation_response_wall_sec'], 45.1)
            self.assertEqual(rows[0]['observation_warnings'],
                             ['BOOT_CALLBACK_OVERRUN_BEFORE_STABLE_WINDOW'])

    def test_private_pin_matches_exact_workflow_checkout_sha(self):
        workflow = (Path(__file__).resolve().parents[1] /
                    '.github/workflows/instructor-sealed-bridge.yml').read_text()
        self.assertIn('ref: ' + bridge.PIN, workflow)

    def test_readonly_localization_prepause_is_explicit_and_never_a_motion_gate(self):
        self.assertEqual(bridge.preloc_settings('gazebo3'), (3, False))
        self.assertEqual(bridge.preloc_settings('gazebo3-prepause'), (3, True))
        # Failed PAUSE trial cannot silently turn 10x release into an experiment.
        self.assertEqual(bridge.preloc_settings('gazebo10'), (10, False))
        for invalid in ('fake-faults', 'unit-middleware', 'gazebo0', 'gazebo5'):
            with self.assertRaisesRegex(bridge.GateBlocked, 'UNSUPPORTED_GATE'):
                bridge.preloc_settings(invalid)

    def test_protected_workflow_uses_experimental_gazebo3_and_exact_private_pin(self):
        workflow=(Path(__file__).resolve().parents[1] /
                  '.github/workflows/instructor-sealed-bridge.yml').read_text()
        self.assertIn('gate: [unit-middleware, fake-faults, gazebo3]',workflow)
        self.assertNotIn('gate: [unit-middleware, fake-faults, gazebo3-prepause]',workflow)
        self.assertIn('ref: ' + bridge.PIN, workflow)
        self.assertIn('fail-fast: false',workflow)

    def test_localization_timeout_diagnostic_never_logs_arbitrary_private_data(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp)/'run_1'
            folder.mkdir()
            marker='PRIVATE_LOC_STACK_TRACE_DO_NOT_EXPOSE'
            (folder/'shutdown_control.json').write_text(json.dumps({
                'status':'SHUTDOWN_BLOCKED',
                'reason':'LOCALIZATION_SERVICE_RESPONSE_TIMEOUT',
                'prepause_requested':False,
                'managers':{
                    'localization':{
                        'success':False,
                        'service_ready_after_timeout':True,
                        'managed_nodes_after_timeout':{
                            'amcl':'ACTIVE', 'map_server':marker},
                        'prepause':{'success':False,'reason':marker}
                    }}
            }),encoding='utf-8')
            captured=io.StringIO()
            with contextlib.redirect_stdout(captured):
                rows=bridge.private_evidence_diagnostics(temp,1)
            result=rows[0]
            self.assertNotIn(marker,captured.getvalue())
            self.assertIs(result['localization_service_ready_after_timeout'],True)
            self.assertEqual(result['amcl_state_after_timeout'],'ACTIVE')
            self.assertEqual(result['map_server_state_after_timeout'],'UNAVAILABLE')
            self.assertIs(result['prepause_requested'],False)
            self.assertEqual(result['shutdown_control_reason'],
                             'LOCALIZATION_SERVICE_RESPONSE_TIMEOUT')

    def test_prepause_timeout_reason_is_enum_not_private_message(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp)/'run_1'
            folder.mkdir()
            (folder/'shutdown_control.json').write_text(json.dumps({
                'status':'SHUTDOWN_BLOCKED',
                'reason':'LOCALIZATION_PREPAUSE_SERVICE_RESPONSE_TIMEOUT',
                'prepause_requested':True,
                'managers':{'localization':{'prepause':{'success':False}}}
            }),encoding='utf-8')
            captured=io.StringIO()
            with contextlib.redirect_stdout(captured):
                row=bridge.private_evidence_diagnostics(temp,1)[0]
            self.assertEqual(row['shutdown_control_reason'],
                             'LOCALIZATION_PREPAUSE_SERVICE_RESPONSE_TIMEOUT')
            self.assertIs(row['localization_prepause_ack'],False)

    def test_manager_liveness_probe_is_allowlisted_and_private_strings_hidden(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp)/'run_1'
            folder.mkdir()
            secret='PRIVATE_NAV2_STACK_DONT_PUBLISH'
            (folder/'shutdown_control.json').write_text(json.dumps({
                'status':'SHUTDOWN_BLOCKED',
                'reason':'LOCALIZATION_SERVICE_RESPONSE_TIMEOUT',
                'managers':{'localization':{
                    'success':False, 'manager_active_after_timeout':'NO_RESPONSE',
                    'managed_nodes_after_timeout':{'amcl':'ACTIVE',
                                                  'map_server':'ACTIVE'},
                    'secret':secret}}}),encoding='utf-8')
            output=io.StringIO()
            with contextlib.redirect_stdout(output):
                result=bridge.private_evidence_diagnostics(temp,1)[0]
            self.assertEqual(result['localization_manager_active_after_timeout'],
                             'NO_RESPONSE')
            self.assertNotIn(secret,output.getvalue())
            (folder/'shutdown_control.json').write_text(json.dumps({
                'status':'SHUTDOWN_BLOCKED',
                'reason':'LOCALIZATION_SERVICE_RESPONSE_TIMEOUT',
                'managers':{'localization':{
                    'success':False,
                    'manager_active_after_timeout':secret}}}),encoding='utf-8')
            with contextlib.redirect_stdout(io.StringIO()):
                result=bridge.private_evidence_diagnostics(temp,1)[0]
            self.assertEqual(result['localization_manager_active_after_timeout'],
                             'UNAVAILABLE')

    def test_private_checkout_sha_is_same_across_script_and_both_workflow_jobs(self):
        workflow=(Path(__file__).resolve().parents[1] /
                  '.github/workflows/instructor-sealed-bridge.yml').read_text()
        self.assertEqual(workflow.count('ref: '+bridge.PIN),2)
        self.assertNotIn('pull_request_target:',workflow)
