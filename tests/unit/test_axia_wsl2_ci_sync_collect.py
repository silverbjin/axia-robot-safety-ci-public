"""L0 only: AXIA WSL2 owner environment inventory privacy and CI schema regressions."""
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import axia_wsl2_ci_sync_collect as c


def fixture(*, wsl=True):
    return {
        "schema": c.SCHEMA,
        "captured_utc": "2026-11-11T01:23:45+00:00",
        "profile_kind": "wsl2_owner" if wsl else "ci_linux",
        "os": {"id": "ubuntu", "version_id": "24.04", "version_codename": "noble"},
        "wsl2_detected": wsl,
        "apt_packages": {
            "ros-jazzy-nav2-bringup":"1.3.13",
            "ros-jazzy-navigation2":"1.3.13",
            "ros-jazzy-nav2-minimal-tb3-sim":"1.0.1",
            "ros-jazzy-ros-gz":"1.0.24",
        },
        "package_count": 4,
        "ros": {
            "distro":"jazzy",
            "official_file_sha256":{
                "nav2_bringup/launch/tb3_simulation_launch.py":"a"*64,
                "nav2_bringup/params/nav2_params.yaml":"b"*64,
                "nav2_minimal_tb3_sim/worlds/tb3_sandbox.sdf.xacro":"c"*64,
            },
        },
        "commands":{"gz_sim":"8.15.0"},
        "env_allowlist":{"discovery_range":"SUBNET","domain_id":None},
        "runtime_details":{"source_commit_sha_if_explicitly_set":None},
    }


class EnvironmentInventoryTests(unittest.TestCase):

    def test_legacy_ci_schema_and_full_read_only_profile(self):
        self.assertEqual(c.SCHEMA, "axia_ros_jazzy_harmonic_env_v1")
        with mock.patch.object(c, "package_versions", return_value={
                "ros-jazzy-nav2-bringup":"1.3.13"}), \
             mock.patch.object(c, "package_holds", return_value=[]), \
             mock.patch.object(c, "official_hashes", return_value={}), \
             mock.patch.object(c, "safe_version", return_value="8.15.0"), \
             mock.patch.object(c, "mem_total_mib", return_value=8192):
            d=c.create_profile({"ROS_DISTRO":"jazzy","ROS_VERSION":"2",
                                "ROS_AUTOMATIC_DISCOVERY_RANGE":"SUBNET",
                                "ROS_DOMAIN_ID":"", "GZ_PARTITION":"axia_p2_local",
                                "GZ_SIM_RESOURCE_PATH":"/private/worlds",
                                "AXIA_P2_OWNER_PINNED_SHA":"a"*40},mode="owner")
        self.assertEqual(d["ros"]["distro"], "jazzy")
        self.assertEqual(d["env_allowlist"]["discovery_range"], "SUBNET")
        self.assertEqual(d["env_allowlist"]["domain_id"], None)
        self.assertTrue(d["env_allowlist"]["gz_partition_set"])
        self.assertEqual(d["runtime_details"]["source_commit_sha_if_explicitly_set"],"a"*40)
        self.assertFalse(d["runtime_details"]["ci_parity_compared"])
        self.assertFalse(d["runtime_details"]["physical_g07_l3_verified"])

    def test_environment_has_strict_allowlist_not_raw_sensitive_values(self):
        secret="MAGIC_SECRET_TOKEN_DO_NOT_COLLECT"
        env={
            "GITHUB_TOKEN":secret,"GH_TOKEN":secret,
            "SSH_PRIVATE_KEY":secret,"AWS_SECRET_ACCESS_KEY":secret,
            "HOME":"/home/private-user/" + secret,
            "HOSTNAME":"private-laptop-"+secret,
            "RMW_IMPLEMENTATION":"rmw_untrusted_"+secret,
            "ROS_AUTOMATIC_DISCOVERY_RANGE":"SUBNET;"+secret,
            "ROS_DOMAIN_ID":"66;"+secret,
            "GZ_SIM_RESOURCE_PATH":"/mnt/d/private-"+secret,
            "GZ_PARTITION":"axia_p2_private_"+secret,
            "ROS_DISTRO":"jazzy",
            "ROS_VERSION":"2",
            "AXIA_P2_OWNER_PINNED_SHA":secret,
        }
        with mock.patch.object(c, "package_versions", return_value={}), \
             mock.patch.object(c, "package_holds", return_value=[]), \
             mock.patch.object(c, "official_hashes", return_value={}), \
             mock.patch.object(c, "safe_version", return_value=""):
            result=c.create_profile(env,mode="owner")
        out=json.dumps(result)
        self.assertNotIn(secret,out)
        self.assertNotIn("/home/private-user",out)
        self.assertNotIn("/mnt/d/private",out)
        self.assertNotIn("GITHUB_TOKEN",out)
        self.assertIsNone(result["runtime_details"]["source_commit_sha_if_explicitly_set"])
        self.assertEqual(result["env_allowlist"]["rmw_implementation"],"CUSTOM_REDACTED")
        self.assertEqual(result["env_allowlist"]["discovery_range"],"CUSTOM_REDACTED")
        self.assertIsNone(result["env_allowlist"]["domain_id"])

    def test_dpkg_filter_ignores_uninstalled_injected_bad_names(self):
        sample=(
          "ros-jazzy-navigation2\t1.3.13-1noble\tii \n"
          "ros-jazzy-nav2-bringup\t1.3.13-1noble\trc \n"
          "curl\t1.0\tii \n"
          "ros-jazzy-unsafe/name\tbad-version\tii \n"
          "libgz-sim8\t8.15.0-1~noble\tii \n"
        )
        with mock.patch.object(c,"command",return_value=sample):
            self.assertEqual(c.package_versions(),{
                "libgz-sim8":"8.15.0-1~noble",
                "ros-jazzy-navigation2":"1.3.13-1noble",
            })

    def test_summary_distinguishes_runner_localhost_from_shell_subnet(self):
        s=c.summary(fixture())
        self.assertEqual(s["status"],"COLLECTED_READY_FOR_CI_COMPARISON")
        self.assertEqual(s["discovery_range_at_capture"],"SUBNET")
        self.assertEqual(s["expected_owner_g07_runner_discovery"],"LOCALHOST")
        self.assertFalse(s["ci_sync_applied"])
        self.assertFalse(s["formal_g07_accepted"])

    def test_private_output_sha256_and_0600_and_no_goal(self):
        with tempfile.TemporaryDirectory() as temp:
            d=Path(temp)/"restricted"
            d.mkdir(mode=0o700)
            with mock.patch.object(c, "create_profile", return_value=fixture()), \
                 mock.patch.object(Path, "home", return_value=Path(temp)):
                rc=c.main(["--out-dir",str(d),"--mode","owner"])
            self.assertEqual(rc,0)
            for name in ("owner_profile.json","owner_summary.json","SHA256SUMS"):
                self.assertTrue((d/name).is_file())
                self.assertEqual(stat.S_IMODE((d/name).stat().st_mode),0o600)
            text=(d/"SHA256SUMS").read_text()
            for row in text.splitlines():
                digest,name=row.split("  ",1)
                self.assertEqual(hashlib.sha256((d/name).read_bytes()).hexdigest(),digest)
            brief=json.loads((d/"owner_summary.json").read_text())
            self.assertFalse(brief["goal_sent"])
            self.assertFalse(brief["gazebo_started_by_collector"])

    def test_owner_rejects_nonwsl_and_insecure_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            d=Path(temp)/"restricted"
            d.mkdir(mode=0o700)
            with mock.patch.object(c, "create_profile", return_value=fixture(wsl=False)), \
                 mock.patch.object(Path, "home", return_value=Path(temp)):
                self.assertEqual(c.main(["--out-dir",str(d),"--mode","owner"]),2)
            self.assertFalse((d/"owner_profile.json").exists())
            d.chmod(0o755)
            with mock.patch.object(c, "create_profile", return_value=fixture()):
                self.assertEqual(c.main(["--out-dir",str(d),"--mode","ci"]),2)

    def test_no_destructive_commands_or_external_upload(self):
        source=(ROOT/"tools/axia_wsl2_ci_sync_collect.py").read_text()
        wrapper=(ROOT/"scripts/axia_wsl2_ci_sync_collect_once.sh").read_text()
        for forbidden in ("sudo ", "apt-get install", "ros2 topic pub", "ros2 action send_goal",
                          "gz service -s", "curl -X POST", "gh api --method POST",
                          "gh repo clone", "git push"):
            self.assertNotIn(forbidden,source)
            self.assertNotIn(forbidden,wrapper)
        self.assertIn("COLLECTOR_REF",wrapper)
        self.assertIn("AXIA_WSL2_CI_SYNC_NO_UPLOAD_NO_GOAL_NO_FAULT",wrapper)


if __name__ == "__main__":
    unittest.main()
