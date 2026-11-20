"""Offline tests for one-shot's public strict native CI gate; no ROS or Goal."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/axia_g07_stabilization_wsl2_final_once.sh"
STUDENT="148635b40c69a40feb8174306cacba6755c88c92"
HEAD="310c8932bde167a1a63ad6305a72057d070d4fb1"
RUN=44683741133
NAME="AXIA G07 FV17 Independent 2-cycle Real Moving Goal Guard TTL L2"


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

    def test_bad_command_refused(self):
        r=subprocess.run(["bash",str(SCRIPT),"--force-run"],
                         capture_output=True,text=True,timeout=8)
        self.assertNotEqual(r.returncode,0)


if __name__=="__main__":
    unittest.main()
