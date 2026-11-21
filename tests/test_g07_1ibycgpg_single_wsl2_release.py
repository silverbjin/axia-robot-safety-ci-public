"""One Owner WSL2 L3 script is allowed ONLY after exact 2/2 native CI.

No actual ROS/Gazebo/Goal in L0; synthetic GitHub API responses validate
fail closed on any failed/missing job. Original baseline remains immutable.
"""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/axia_g07_1ibycgpg_single_observer_wsl2_l3_once.sh"
STUDENT="2218584a907d3b7082588dc40625c8156cc88486"
L2_HEAD="9b0fef8c5c1502685c5e16486408225c7930eb00"
RUN=44855963095
NAME="AXIA G07 1ibYCGPg Single Observer 2-cycle Native Moving L2"


def evidence(conclusion="success", a="success",b="success", sha=L2_HEAD):
    return ({"id":RUN,"head_sha":sha,"event":"push","status":"completed",
             "conclusion":conclusion,"name":NAME},
            {"jobs":[{"name":"one-real-gazebo-moving-gui (1)",
                       "status":"completed","conclusion":a},
                      {"name":"one-real-gazebo-moving-gui (2)",
                       "status":"completed","conclusion":b}]})


class ScopedSingleObserverRelease(unittest.TestCase):
    def test_exact_strict_public_l2_and_student_source_pinned(self):
        src=SCRIPT.read_text()
        workflow=(ROOT/".github/workflows/axia-g07-1ibycgpg-single-observer-native-l2.yml").read_text()
        self.assertIn("readonly STUDENT_SHA='"+STUDENT+"'",src)
        self.assertIn("readonly CI_L2_RUN="+str(RUN),src)
        self.assertIn("readonly CI_L2_HEAD='"+L2_HEAD+"'",src)
        self.assertIn(NAME,src)
        self.assertIn("ref: "+STUDENT,workflow)
        self.assertIn("AXIA_G07_OBSERVER_EXECUTOR_AB: 'single'",workflow)
        self.assertIn("export AXIA_G07_OBSERVER_EXECUTOR_AB=single",src)
        self.assertIn("export AXIA_G07_SCAN_PREFLIGHT_STRICT=1",src)
        self.assertIn("export FASTDDS_BUILTIN_TRANSPORTS=UDPv4",src)
        self.assertIn("AXIA_G07_CI_SIM_GOAL_ALLOWED=0",src)
        self.assertIn("OWNER_CONTROLLING_TTY_REQUIRED",src)
        self.assertIn("CERTIFIED_ESTOP=false",src)
        self.assertNotIn("pkill -f",src)
        self.assertNotIn("killall",src)
        self.assertNotIn("AXIA_G07_CM_OBSERVER_GROUPS=1",src)
        self.assertIn("CI-BLOCKED candidate",src)
        for i,line in enumerate(src.splitlines(),1):
            self.assertFalse(line.endswith(chr(92)*2),f"broken escaped shell continuation line {i}")

    def test_no_side_effects_self_check(self):
        subprocess.run(["bash","-n",str(SCRIPT)],check=True)
        r=subprocess.run(["bash",str(SCRIPT),"--self-check"],
                  capture_output=True,text=True,timeout=10)
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)
        self.assertIn("NO_ROS_NO_GAZEBO_NO_GOAL",r.stdout)
        self.assertIn("OWNER_MOVING_L3=NOT_RUN",r.stdout)
        self.assertNotIn("OWNER_MOVING_L3=PASS",r.stdout)

    def api(self,run,jobs):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/"run.json").write_text(json.dumps(run))
            (root/"jobs.json").write_text(json.dumps(jobs))
            mock=root/"curl"
            mock.write_text("""#!/bin/bash
set -Eeuo pipefail
args="$*"; output=""
while (( $# ));do
  if [[ "$1" == '-o' ]];then output="$2";shift 2;continue;fi
  shift
done
[[ -n "$output" ]]
if [[ "$args" == *'/jobs?per_page=100'* ]];then
  cp "$AXIA_MOCK_JOBS" "$output"
else
  cp "$AXIA_MOCK_RUN" "$output"
fi
""")
            mock.chmod(0o755)
            env={**os.environ,"PATH":str(root)+os.pathsep+os.environ.get("PATH",""),
                 "AXIA_MOCK_JOBS":str(root/"jobs.json"),
                 "AXIA_MOCK_RUN":str(root/"run.json")}
            return subprocess.run(["bash",str(SCRIPT),"--ci-check"],
                      capture_output=True,text=True,timeout=10,env=env)

    def test_positive_two_jobs_is_only_run_admission_not_owner_acceptance(self):
        r=self.api(*evidence())
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)
        self.assertIn("PASS_TWO_STRICT_REAL_GAZEBO_GOALS_OWNER_WSL2_NOT_RUN",r.stdout)
        self.assertNotIn("OWNER_MOVING_L3=PASS",r.stdout)

    def test_failed_missing_or_wrong_sha_deny_new_goal(self):
        for run,jobs in (evidence(conclusion="failure",a="failure"),
                         evidence(b="failure"),evidence(sha="f"*40),
                         evidence()):
            if run.get("conclusion")=="success" and all(
                    j["conclusion"]=="success" for j in jobs["jobs"]) and run["head_sha"]==L2_HEAD:
                jobs["jobs"].pop()
            with self.subTest(run=run,jobs=jobs):
                r=self.api(run,jobs)
                self.assertEqual(r.returncode,3,r.stdout+r.stderr)
                self.assertIn("HOLD_NO_NEW_WSL2_MOVING_RELEASE",r.stdout)


if __name__=="__main__":
    unittest.main()
