"""Privacy and simulation approval controls for protected real G00 CI."""
import pathlib
import unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
S=(ROOT/"scripts/private_pr52_cloud_g00.py").read_text()
W=(ROOT/".github/workflows/pr52-cloud-g00-real.yml").read_text()

class RealG00CloudPolicy(unittest.TestCase):
    def test_exact_sha_and_github_protection(self):
        pin="dd7dc7d0697933f60735ea3a3e900ed2fc2ad3b7"
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
        self.assertIn("CLOUD_G00_3X_CANDIDATE_REVIEW_PENDING",S)
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
            (run/'source_commit.txt').write_text(source_sha+'\\n')
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

if __name__=="__main__":unittest.main()
