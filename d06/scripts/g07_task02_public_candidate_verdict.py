"""Public-only G07 Task02 real Gazebo candidate verdict; never final release."""
import argparse
import json
import sys
from pathlib import Path
from d06.diagnostic.g07_task02_strict_gate import assess


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--report",type=Path,required=True)
    parser.add_argument("--events",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--runner-rc",type=int,required=True)
    args=parser.parse_args()
    try:
        if args.report.stat().st_size>1000000 or args.events.stat().st_size>20000000:
            raise ValueError("INPUT_UNBOUNDED")
        report=json.loads(args.report.read_text(encoding="utf-8"))
        rows=[json.loads(line) for line in args.events.read_text(encoding="utf-8").splitlines()]
        verdict=assess(report,rows)
    except (OSError,ValueError,TypeError):
        verdict=dict(schema="axia.g07.task02.strict_actual_cm_period_v1",
                     status="TASK02_REAL_EVIDENCE_UNAVAILABLE_HOLD",
                     tracer_off_release_pass=False,owner_wsl2_accepted=False,
                     certified_estop=False)
    if args.runner_rc!=0:
        verdict["status"]="TASK02_ACTUAL_GAZEBO_OR_GUARD_GOAL_BLOCKED_HOLD"
    verdict.update(actual_runner_rc=args.runner_rc,
        student_source_sha="7292659a7ea92f25076f4ef605d0dc1e0d1f3c5a",
        real_gazebo_l2_numeric_accepted=(
            args.runner_rc==0 and verdict["status"]=="TASK02_PUBLIC_L2_NUMERICAL_CANDIDATE"),
        task03_tracer_off_release_pass=False,
        owner_wsl2_l3_accepted=False)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(verdict,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("AXIA_G07_TASK02_PUBLIC_SAFETY_VERDICT "+
          json.dumps(verdict,sort_keys=True),flush=True)
    print("CM120_TRACER_OFF_RELEASE=HOLD\nAXIA_MVP_DEMO_ACCEPTED=HOLD",flush=True)
    return 0 if verdict["real_gazebo_l2_numeric_accepted"] else 3


if __name__=="__main__":
    sys.exit(main())
