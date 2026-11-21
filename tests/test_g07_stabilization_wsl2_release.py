"""Offline tests for one-shot's public strict native CI gate; no ROS or Goal."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/axia_g07_stabilization_wsl2_final_once.sh"
STUDENT="fb1aae6cbde54ff0ed4e78317f403aa5cef4d550"
HEAD="0711e583f3c0c546a64c687edd8e280c2ae8e776"
RUN=44878063103
NAME="AXIA G07 Original Multi First Scan RMW Exact Pair Diagnostic Native L2"


def inputs(conclusion="success", second="success", sha=HEAD):
    run={"id":RUN,"head_sha":sha,"event":"push","status":"completed",
         "conclusion":conclusion,"name":NAME}
    jobs={"jobs":[{"name":"one-real-gazebo-moving-gui (1)","status":"completed",
                   "conclusion":"success"},
                  {"name":"one-real-gazebo-moving-gui (2)","status":"completed",
                   "conclusion":second}]}
    return run,jobs


class SafeOwnerRelease(unittest.TestCase):
    def test_static_bootstrap_no_ros(self):
        r=subprocess.run(["bash",str(SCRIPT),"--self-check"],
                         capture_output=True,text=True,timeout=8)
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)
        self.assertIn("AXIA_G07_STABILIZATION_WSL2_BOOTSTRAP_L0_PASS",r.stdout)
        self.assertIn(STUDENT,r.stdout)
        self.assertIn("l2_run="+str(RUN),r.stdout)
        self.assertIn("AXIA_G07_TASK04_OWNER_MOVING_L3=NOT_RUN",r.stdout)
        self.assertIn("CERTIFIED_ESTOP=false",r.stdout)

    def test_bash_syntax_and_original_real_owner_guardrails(self):
        subprocess.run(["bash","-n",str(SCRIPT)],check=True)
        text=SCRIPT.read_text()
        self.assertIn("AXIA_G07_CI_SIM_GOAL_ALLOWED=0",text)
        self.assertIn("OWNER_CONTROLLING_TTY_REQUIRED",text)
        self.assertIn("timeout --foreground --signal=TERM",text)
        self.assertIn("AXIA_G07_TASK04_DIAGNOSTIC_ZIP=",text)
        self.assertIn("AXIA_G07_TASK04_OWNER_MOVING_L3=HOLD",text)
        self.assertNotIn("pkill -f",text)
        self.assertNotIn("killall",text)

    def test_fastdds_udpv4_mode_matches_strict_native_l2(self):
        text=SCRIPT.read_text()
        self.assertIn("export FASTDDS_BUILTIN_TRANSPORTS=UDPv4",text)
        self.assertIn("AXIA_G07_FASTDDS_BUILTIN_TRANSPORTS=UDPv4",text)
        self.assertIn("FASTDDS_XML_OVERRIDE_UNVERIFIED_HOLD",text)
        # Applies to the entire run, before Jazzy nodes or any Goal launch.
        self.assertLess(text.index("export FASTDDS_BUILTIN_TRANSPORTS=UDPv4"),
                        text.index("source /opt/ros/jazzy/setup.bash",text.index("OUT=''")))

    def test_wsl2_owner_nav_warm_participant_does_not_spoof_public_ci(self):
        text=SCRIPT.read_text()
        self.assertIn("export AXIA_G07_NAV_WARM_PARTICIPANT_OWNER=1",text)
        self.assertIn("unset AXIA_G07_NAV_WARM_PARTICIPANT_CI_AB",text)
        self.assertIn("export AXIA_G07_CI_SIM_GOAL_ALLOWED=0",text)
        self.assertIn("OWNER_CONTROLLING_TTY_REQUIRED",text)
        self.assertLess(
            text.index("export AXIA_G07_NAV_WARM_PARTICIPANT_OWNER=1"),
            text.index("source /opt/ros/jazzy/setup.bash",text.index("OUT=''")))

    def _gate(self,run,jobs):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            (p/"run.json").write_text(json.dumps(run))
            (p/"jobs.json").write_text(json.dumps(jobs))
            curl=p/"curl"
            curl.write_text("""#!/bin/bash
set -Eeuo pipefail
args="$*"
out=""
while (( $# ));do
  if [[ "$1" == '-o' ]];then out="$2";shift 2;continue;fi
  shift
done
[[ -n "$out" ]]
if [[ "$args" == *'/jobs?per_page=100'* ]];then
  cp "$AXIA_MOCK_JOBS" "$out"
else
  cp "$AXIA_MOCK_RUN" "$out"
fi
""")
            curl.chmod(0o755)
            env=dict(os.environ,PATH=str(p)+os.pathsep+os.environ.get("PATH",""),
                     AXIA_MOCK_RUN=str(p/"run.json"),AXIA_MOCK_JOBS=str(p/"jobs.json"))
            return subprocess.run(["bash",str(SCRIPT),"--ci-check"],
                                  capture_output=True,text=True,env=env,timeout=8)

    def test_two_exact_real_native_jobs_success_admit_only_execution_not_acceptance(self):
        r=self._gate(*inputs())
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)
        self.assertIn("PASS_TWO_STRICT_REAL_GAZEBO_GOALS_OWNER_WSL2_NOT_RUN",r.stdout)
        self.assertNotIn("OWNER_MOVING_L3=PASS",r.stdout)

    def test_any_failed_job_entire_l2_failure_or_wrong_sha_blocks(self):
        for payload in (inputs(second="failure"),
                        inputs(conclusion="failure"),
                        inputs(sha="a"*40)):
            with self.subTest(payload=payload):
                r=self._gate(*payload)
                self.assertNotEqual(r.returncode,0,r.stdout+r.stderr)
                self.assertIn("HOLD_NO_NEW_WSL2_MOVING_RELEASE",r.stdout)

    def test_strict_native_run_and_owner_source_share_exact_committed_sha(self):
        flow=(ROOT/".github/workflows/axia-g07-original-multi-first-scan-rmw-native-l2.yml").read_text()
        script=SCRIPT.read_text()
        self.assertIn("ref: "+STUDENT,flow)
        self.assertIn("readonly STUDENT_SHA='"+STUDENT+"'",script)
        self.assertIn("readonly CI_L2_RUN="+str(RUN),script)
        self.assertIn("readonly CI_L2_HEAD='"+HEAD+"'",script)
        self.assertIn("FASTDDS_BUILTIN_TRANSPORTS: UDPv4",flow)
        self.assertIn("AXIA_G07_NAV_WARM_PARTICIPANT_CI_AB: '1'",flow)

    def test_actual_two_cycle_one_failed_response_is_denied_offline(self):
        # Synthetic regression for historic missing Navigation ACK boundary;
        # reject one failed job despite the pinned real run being 2/2 PASS.
        # unauthenticated GitHub API network access in the CI runner.
        run,jobs=inputs(conclusion="failure",second="success")
        jobs["jobs"][0]["conclusion"]="failure"
        r=self._gate(run,jobs)
        self.assertEqual(r.returncode,3,r.stdout+r.stderr)
        self.assertIn("HOLD_NO_NEW_WSL2_MOVING_RELEASE",r.stdout)
        self.assertNotIn("OWNER_MOVING_L3=PASS",r.stdout)

    def test_bad_command_refused(self):
        r=subprocess.run(["bash",str(SCRIPT),"--force-run"],
                         capture_output=True,text=True,timeout=8)
        self.assertNotEqual(r.returncode,0)



    def test_formal_shutdown_or_rmw_failed_candidate_must_exit_nonzero(self):
        # A complete physical educational demo is NOT the accepted final L3
        # if Localization ACK or formal CM/RMW timing remained HOLD.
        src=SCRIPT.read_text()
        assert "FIRST_FAILURE='FORMAL_LOCALIZATION_SHUTDOWN_TIMEOUT_AFTER_DEMO'" in src
        assert "FIRST_FAILURE='FORMAL_RMW_TIMEBASE_HOLD_ONLY'" in src
        a=src.index("FIRST_FAILURE='FORMAL_LOCALIZATION_SHUTDOWN_TIMEOUT_AFTER_DEMO'")
        b=src.index("FIRST_FAILURE='FORMAL_RMW_TIMEBASE_HOLD_ONLY'")
        self.assertIn("exit 3",src[a:a+650])
        self.assertIn("exit 3",src[b:b+220])
        self.assertIn("AXIA_G07_TASK04_OWNER_MOVING_L3=HOLD",src)

    def test_original_multi2_release_must_not_enable_failed_executor_candidates(self):
        src=SCRIPT.read_text()
        self.assertIn("unset AXIA_G07_CI_EXECUTOR_GUARD_WAKE_AB",src)
        self.assertRegex(src,r"unset [^\n]*AXIA_G07_CI_EXECUTOR_WAIT_BOUNDED_AB")
        self.assertNotIn("export AXIA_G07_OBSERVER_EXECUTOR_AB=single",src)
        self.assertIn("AXIA_G07_CI_SIM_GOAL_ALLOWED=0",src)

if __name__=="__main__":
    unittest.main()
