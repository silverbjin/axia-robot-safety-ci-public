"""Reproduce user WSL2 first failure against pinned real G07 parity logic.

The field TAR's SHA256 and nested manifests were checked separately.
This regression contains only non-identifying facts and imports the exact
native-L2-proven public Student source, never reimplements the safety policy.
"""
from pathlib import Path
import importlib.util
import json
import os
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "d06/scripts/axia_d06_g07_classroom_once.sh"
STUDENT = ROOT / "student/block_B/day07/h01_runtime"
PARITY = STUDENT / "tools/p2_g07_owner_env_parity.py"
SHELL = STUDENT / "scripts/p2_no_goal_smoke_ci.sh"

class FieldOwnerCIParityRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        assert PARITY.is_file() and SHELL.is_file(), "PINNED_STUDENT_CHECKOUT_MISSING"
        spec = importlib.util.spec_from_file_location("p2_g07_field_parity", PARITY)
        cls.parity = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.parity)
        cls.lock = cls.parity.read_lock()

    def test_original_wsl2_owner_pass_ci_mode_rejects_same_machine(self):
        lock = self.lock
        env = {
            "ROS_DISTRO": "jazzy",
            "ROS_AUTOMATIC_DISCOVERY_RANGE": "LOCALHOST",
            "RMW_IMPLEMENTATION": "rmw_fastrtps_cpp",
            "ROS_DOMAIN_ID": "94",
            "GZ_PARTITION": "axia_p2_d06_reproduced",
            "AXIA_P0_SIM_ONLY": "1",
        }
        common = dict(
            installed_debs=lock["packages"],
            installed_hashes=lock["official_file_sha256"],
            env=env,
            os_info={k:lock["os"][k] for k in
                     ("id","version_id","architecture","python_major_minor")},
            wsl_detected=True,
            kernel_release="6.18.40.1-microsoft-standard-WSL2",
            gazebo_version=lock["os"]["gazebo_sim_version"],
        )
        owner = self.parity.assess_snapshot(lock,mode="owner",**common)
        ci = self.parity.assess_snapshot(lock,mode="ci",**common)
        self.assertEqual(owner["status"],"CORE_PARITY_PASS")
        self.assertEqual(owner["mode"],"owner")
        self.assertEqual(owner["mismatch"],{})
        self.assertEqual(owner["checked_packages"],25)
        self.assertEqual(owner["checked_official_files"],5)
        self.assertEqual(ci["status"],"PARITY_BLOCKED")
        self.assertEqual(ci["mismatch"],{"ci_kernel":"CI_NOT_WSL2_REQUIRED"})
        self.assertFalse(ci["goal_sent"])

    def test_actual_pinned_shell_only_uses_ci_mode_in_ci_gate(self):
        src = SHELL.read_text()
        self.assertIn('if [[ "${AXIA_P2_G07_OWNER_PARITY_CHECK:-0}" == 1 ]]; then',src)
        self.assertIn('--mode ci --output "$OUT/g07_userspace_parity.json"',src)
        self.assertIn('P2_G07_NO_GOAL_CI_USERSPACE_PARITY_BLOCKED',src)
        self.assertEqual(src.count('--mode ci --output "$OUT/g07_userspace_parity.json"'),1)

    def test_d06_owner_selects_validated_owner_mode_not_ci_only_gate(self):
        src = RUNNER.read_text()
        owner = src.split("run_verified_owner() {",1)[1].split("\nself_check >/dev/null",1)[0]
        # This *failed* in the uploaded field run. It is NOT a safety TTL
        # relaxation: real Owner core parity still verifies 25/5 separately.
        self.assertIn('AXIA_P2_G07_OWNER_PARITY_CHECK=0',owner)
        self.assertNotIn('AXIA_P2_G07_OWNER_PARITY_CHECK=1',owner)
        self.assertIn('p2_g07_owner_env_parity.py" --mode owner',owner)
        self.assertIn("CORE_PARITY_PASS",owner)
        self.assertIn('AXIA_G07_TASK04_OWNER_MOVING_L3=1',owner)
        self.assertIn('AXIA_G07_CI_SIM_GOAL_ALLOWED=0',owner)
        self.assertNotIn('export GITHUB_ACTIONS=true',owner)

    def test_wsl2_owner_core_parity_is_checked_before_real_child_goal(self):
        src = RUNNER.read_text()
        scope = src.split("run_verified_owner() {",1)[1].split("\\nself_check >/dev/null",1)[0]
        order = [
            scope.index('export AXIA_P2_G07_OWNER_PARITY_CHECK=0'),
            scope.index('p2_g07_owner_env_parity.py" --mode owner'),
            scope.index('D06_G07_OWNER_CORE_PARITY_PASS_PACKAGES25_FILES5_WSL2'),
            scope.index('D06_G07_OWNER_REAL_GAZEBO_RVIZ_MOVING_CANDIDATE_START'),
            scope.index('bash scripts/p2_no_goal_smoke_ci.sh'),
        ]
        self.assertEqual(order, sorted(order),
                         "Owner core parity and WSL2 platform check must precede any Goal")

    def test_no_false_success_after_pre_goal_error(self):
        src = RUNNER.read_text()
        self.assertIn('D06_G07_OWNER_RUNTIME_BLOCKED_RC_',src)
        self.assertIn('D06_G07_OWNER_L3=HOLD_FAILED_OR_BLOCKED',src)
        self.assertIn('AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false',src)
        self.assertIn('D06_G07_OWNER_RAW_SHA256',src)

if __name__=="__main__":
    unittest.main()
