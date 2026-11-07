"""Privacy and simulation approval controls for protected real G00 CI."""
import pathlib
import unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
S=(ROOT/"scripts/private_pr52_cloud_g00.py").read_text()
W=(ROOT/".github/workflows/pr52-cloud-g00-real.yml").read_text()

class RealG00CloudPolicy(unittest.TestCase):
    def test_exact_sha_and_github_protection(self):
        pin="13ddf2719d6e9c7ca98148783a06083e6975d8ce"
        self.assertIn(pin,S)
        self.assertIn(pin,W)
        self.assertIn("axia-instructor-sealed",W)
        self.assertIn("secrets.AXIA_CLOUD_CI",W)
        self.assertIn('GITHUB_REPOSITORY',S)
        self.assertIn('GITHUB_ACTOR',S)
    def test_strict_one_goal_per_cold_start(self):
        self.assertIn('for i in (1,2,3):',S)
        self.assertIn('AXIA_T08_MAX_RUNS="1"',S)
        self.assertIn('AXIA_T08_SCENARIO="g00"',S)
        self.assertIn('AXIA_T08_FAULT_APPROVED="NO"',S)
    def test_true_goal_and_raw_custody_no_claimed_acceptance(self):
        self.assertIn("classify_g00_evidence",S)
        self.assertIn("assess_raw_g00",S)
        self.assertIn("r05_bound_pre_send.json",S)
        self.assertIn('"start_ack"]=="START_ACK_VERIFIED"',S)
        self.assertIn('"shutdown"]=="SHUTDOWN_CLEAN"',S)
        self.assertIn('"gate_accepted":False',S)
        self.assertIn("CLOUD_G00_3X_AGE_CIPHER_UPLOADED",S)
        self.assertIn("seal(private,approved_runs,os.environ)",S)
        self.assertIn("CLOUD_G00_3X_CUSTODY_BLOCKED",S)
    def test_no_private_artifact_leak_or_direct_goal_bypass(self):
        self.assertNotIn("upload-artifact",W)
        self.assertNotIn("cat _instructor_private",W)
        self.assertIn("rm -rf _instructor_private",W)
        self.assertNotIn("create_publisher(",S)
        self.assertNotIn("ros2 topic pub",S)
        self.assertNotIn("call_async(",S)
    def test_private_console_is_never_printed_as_raw_error(self):
        self.assertIn("def _blocked_phase(log_file):",S)
        self.assertIn('"CLOUD_CONTEXT_DENIED"',S)
        self.assertIn('"PREFLIGHT_FAKE_ROS_FAILED"',S)
        self.assertIn('"BLOCKED_UNCLASSIFIED"',S)
        self.assertIn('"block_phase":_blocked_phase(log)',S)
        self.assertNotIn("print(content)",S)
    def test_r05_diagnostic_is_allowlisted_and_real_block_line_only(self):
        self.assertIn("def _private_r05_codes(child, private, source_sha):",S)
        self.assertIn('"SUPERVISOR_RECEIPT_TOO_OLD"',S)
        self.assertIn('"r05_reason_codes"',S)
        self.assertIn('blocked_lines=[line for line in content.splitlines() if "[BLOCKED]" in line]',S)
        self.assertIn('"NO_RECORDED_BLOCKED_LINE"',S)
    def test_raw_bag_classifier_returns_only_allowlisted_conditions(self):
        import importlib.util
        import sys
        import tempfile
        from pathlib import Path
        sys.path.insert(0,str(ROOT/'scripts'))
        spec=importlib.util.spec_from_file_location('live_raw_diagnostic',
            ROOT/'scripts/private_pr52_cloud_g00.py')
        mod=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        with tempfile.TemporaryDirectory() as d:
            run=Path(d)
            source_sha=mod.PIN
            self.assertEqual(mod._raw_bag_blocker(run,source_sha)['status'],
                             'SOURCE_MARKER_INVALID')
            (run/'source_commit.txt').write_text(source_sha+chr(10))
            self.assertEqual(mod._raw_bag_blocker(run,source_sha)['status'],
                             'CHECKSUM_MANIFEST_MISSING')
            child=run/'cold_run_01';child.mkdir()
            (child/'checksums.sha256').write_text('')
            self.assertEqual(mod._raw_bag_blocker(run,source_sha)['status'],
                             'ROS_BAG_DIRECTORY_MISSING')
            (child/'rosbag2').mkdir()
            self.assertEqual(mod._raw_bag_blocker(run,source_sha)['status'],
                             'ROS_BAG_METADATA_MISSING')
        self.assertIn('raw_bag_blocker',S)
        self.assertIn('require_live_start_boundary=True',S)
        self.assertNotIn('print(meta.read_text',S)

    def test_protected_environment_is_real_and_no_e_stop(self):
        self.assertIn('CI="true"',S)
        self.assertIn('AXIA_T08_CLOUD_G00_OPT_IN="YES_SIM_ONLY"',S)
        self.assertIn('"certified_estop_verified":False',S)
        self.assertIn('"fault_injected":False',S)


    def test_failed_fake_ros_preflight_reports_only_allowlisted_status(self):
        import importlib.util
        import json
        import sys
        import tempfile
        from pathlib import Path
        sys.path.insert(0,str(ROOT/'scripts'))
        spec=importlib.util.spec_from_file_location(
            'g00_preflight_diag',ROOT/'scripts/private_pr52_cloud_g00.py')
        mod=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            private=root/'partial'/'p1-case'
            private.mkdir(parents=True)
            (private/'summary.json').write_text(json.dumps({
                'overall_status':'FAIL','exit_code':1,
                'blocked_reason':None,
                'stage_results':[
                    {'stage_id':'G02_UNIT','status':'PASS','repeat':1,'tests':4,'failures':0},
                    {'stage_id':'G04_ROS_FAKE','status':'FAIL','repeat':1,
                     'tests':7,'failures':1,'private_trace':'MUST_NOT_LEAK'},
                ],
                'secret':'MUST_NOT_LEAK',
            }))
            report=mod._fake_preflight_diagnostic(root)
            self.assertEqual(report['first_nonpassing_stage'],'G04_ROS_FAKE')
            self.assertEqual(report['first_nonpassing_status'],'FAIL')
            self.assertEqual(report['failed_case_count'],1)
            self.assertNotIn('MUST_NOT_LEAK',json.dumps(report))
            self.assertNotIn(tmp,json.dumps(report))
            self.assertEqual(mod._fake_preflight_diagnostic(root/'missing')['status'],
                             'PREFLIGHT_SUMMARY_MISSING')


    def test_shutdown_blocker_diagnostic_is_redacted(self):
        import importlib.util
        import json
        import sys
        import tempfile
        from pathlib import Path
        sys.path.insert(0,str(ROOT/'scripts'))
        spec=importlib.util.spec_from_file_location(
            'g00_shutdown_diag',ROOT/'scripts/private_pr52_cloud_g00.py')
        mod=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        with tempfile.TemporaryDirectory() as tmp:
            child=Path(tmp)
            (child/'shutdown_control.json').write_text(json.dumps({
                'status':'SHUTDOWN_BLOCKED',
                'reason':'LOCALIZATION_SERVICE_RESPONSE_TIMEOUT',
                'managers':{
                    'navigation':{'success':True},
                    'localization':{'success':False,
                        'manager_active_after_timeout':'NO_RESPONSE',
                        'managed_nodes_after_timeout':{
                            'amcl':'ACTIVE','map_server':'INACTIVE'}}},
                'secret':'MUST_NOT_LEAK'
            }))
            (child/'shutdown_verdict.json').write_text(json.dumps({
                'status':'SHUTDOWN_INCONCLUSIVE',
                'lifecycle_shutdown_acknowledged':False,
                'fatal_signatures':[],
                'private_trace':'MUST_NOT_LEAK'
            }))
            report=mod._shutdown_failure_diagnostic(child)
            self.assertEqual(report['reason_code'],'LOCALIZATION_SERVICE_RESPONSE_TIMEOUT')
            self.assertEqual(report['manager_ack_navigation'],True)
            self.assertEqual(report['manager_ack_localization'],False)
            self.assertEqual(report['manager_active_after_timeout'],'NO_RESPONSE')
            self.assertEqual(report['amcl_state'],'ACTIVE')
            self.assertEqual(report['map_server_state'],'INACTIVE')
            self.assertNotIn('MUST_NOT_LEAK',json.dumps(report))
            self.assertNotIn(tmp,json.dumps(report))
            (child/'shutdown_control.json').write_text('{bad-json')
            self.assertEqual(mod._shutdown_failure_diagnostic(child)['reason_code'],
                             'DIAGNOSTIC_UNAVAILABLE')


    def test_lkg_ledger_never_promotes_previous_sha(self):
        import json
        source=ROOT/'.github/axia/evidence/g00_lkg_20261107.json'
        data=json.loads(source.read_text(encoding='utf-8'))
        self.assertEqual(data['schema'],'axia-p1-g00-lkg-v1')
        self.assertEqual(data['private_source_sha'],
                         'df09426c67536fc2ebabaa2c2ef30453ce169ef7')
        self.assertEqual(data['public_run_id'],42371053889)
        self.assertEqual(data['public_workflow_sha'],
                         'c4d11ab27c926ab8ca554300b76d241df1cf6202')
        self.assertEqual(data['record_scope'],'L2_G00_THREE_CANDIDATE_ONLY')
        self.assertEqual([x['shutdown'] for x in data['runs']],
                         ['SHUTDOWN_CLEAN']*3)
        self.assertTrue(all(x['goal_trace']=='PASS' and
                            x['sealed_raw_bag'] is True and
                            x['candidate'] is True for x in data['runs']))
        self.assertFalse(data['gate_accepted'])
        self.assertFalse(data['off_runner_original_custody_verified'])
        self.assertFalse(data['independent_plaintext_restore_verified'])
        self.assertNotEqual(data['private_source_sha'],
                            '13ddf2719d6e9c7ca98148783a06083e6975d8ce')
        self.assertNotIn('private_stdout',data)
        self.assertNotIn('access_token',data)


    def test_same_job_preflight_proof_reuse_is_bound_and_fail_closed(self):
        import importlib.util
        import sys
        import tempfile
        from pathlib import Path
        sys.path.insert(0,str(ROOT/'scripts'))
        spec=importlib.util.spec_from_file_location(
            'g00_proof_reuse', ROOT/'scripts/private_pr52_cloud_g00.py')
        mod=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            run=root/'one_successful_g00';run.mkdir()
            src=root/'private';src.mkdir()
            expected=mod.PIN
            def okay(*,proof,repo):
                self.assertEqual(repo,src)
                return {'source_commit':expected,'stage_count':12,
                        'gate_accepted':False,'preflight':'VERIFIED_REUSED'}
            self.assertIsNone(mod._verified_shared_preflight_proof(
                src,run,expected,verifier=okay))
            proof=run/'preflight_proof.json'
            proof.write_text('{}')
            self.assertEqual(mod._verified_shared_preflight_proof(
                src,run,expected,verifier=okay),str(proof))
            self.assertIsNone(mod._verified_shared_preflight_proof(
                src,run,'f'*40,verifier=okay))
            self.assertIsNone(mod._verified_shared_preflight_proof(
                src,run,expected,verifier=lambda **k:
                {'source_commit':expected,'stage_count':1,'gate_accepted':False,
                 'preflight':'VERIFIED_REUSED'}))
            self.assertIsNone(mod._verified_shared_preflight_proof(
                src,run,expected,verifier=lambda **k:
                {'source_commit':expected,'stage_count':12,'gate_accepted':True,
                 'preflight':'VERIFIED_REUSED'}))
            proof.unlink()
            proof.symlink_to('/etc/passwd')
            self.assertIsNone(mod._verified_shared_preflight_proof(
                src,run,expected,verifier=okay))
        self.assertIn('if row["candidate"] and i<3:',S)
        self.assertIn('AXIA_T08_PREFLIGHT_PROOF',S)
        self.assertIn('env.pop("AXIA_T08_PREFLIGHT_PROOF",None)',S)


    def test_g00_action_status_gate_diagnostic_redacts_private_evidence(self):
        import importlib.util
        import json
        import sys
        import tempfile
        from pathlib import Path
        sys.path.insert(0,str(ROOT/'scripts'))
        spec=importlib.util.spec_from_file_location(
            'g00_status_diag',ROOT/'scripts/private_pr52_cloud_g00.py')
        mod=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        with tempfile.TemporaryDirectory() as tmp:
            child=Path(tmp)
            self.assertEqual(
                mod._action_status_gate_diagnostic(child)['status'],'MISSING')
            (child/'action_status_ready.json').write_text(json.dumps({
                'status':'STATUS_EVIDENCE_BLOCKED',
                'reason':'STATUS_QOS_NOT_COMPATIBLE',
                'goal_sent':False, 'private_endpoint':'MUST_NOT_LEAK',
                'secret':'MUST_NOT_LEAK'
            }))
            report=mod._action_status_gate_diagnostic(child)
            self.assertEqual(report['status'],'STATUS_EVIDENCE_BLOCKED')
            self.assertEqual(report['reason'],'STATUS_QOS_NOT_COMPATIBLE')
            self.assertNotIn('MUST_NOT_LEAK',json.dumps(report))
            self.assertNotIn(tmp,json.dumps(report))
            (child/'action_status_ready.json').write_text(json.dumps({
                'status':'STATUS_EVIDENCE_BLOCKED',
                'reason':'SECRET_UNLISTED',
                'secret':'MUST_NOT_LEAK'}))
            self.assertEqual(mod._action_status_gate_diagnostic(child)['reason'],
                             'UNCLASSIFIED')
        self.assertEqual(
            mod._blocked_phase.__doc__ is not None,True)
        self.assertIn('STATUS_EVIDENCE_NOT_CONNECTED',
                      (ROOT/'scripts/private_pr52_cloud_g00.py').read_text())

if __name__=="__main__":unittest.main()
