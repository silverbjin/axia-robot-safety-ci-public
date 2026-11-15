#!/usr/bin/env bash
# AXIA P4 reduced-demo: final one manually consented G07 GUI Goal, archived raw + first RMW/Guard provenance.
# Exact new shared executor/async evidence CI Goal #43674784552 PASS. Prior failures #43674054563 and Owner Brxs5kxL preserved; Owner WSL2 new attempt NOT_RUN.
# Owner has not run. This wrapper NEVER asserts AXIA_MVP_DEMO_ACCEPTED.
# No simulated Goal in CI, no implicit consent, no public RAW upload.
set -Eeuo pipefail
umask 077
PRIVATE_SHA="db1eec05e01e1db0d0d2e0c05610806ef4e499f9"
PRIVATE_TREE="005cc352d63067beb9d34397e51b51f7974ce7ef"
readonly CI_S02_G07_L2_RUN=43674784552
readonly AXIA_P4_G07_RMW_SOURCE_MAX_SEC=0.12971
readonly AXIA_G07_REAL_EXACT_NAV2_GOAL_CANCEL_ACK_BEFORE_LIFECYCLE_PASS=true
readonly AXIA_P4_SHARED_GOAL_CI_ACCEPTED=true
readonly CI_S02_G07_SCOPE="G07_SHARED_ASYNC_EVIDENCE_GUARD_40MS_FIRST_CLOCK_DOMAIN_7_TTL_S02_ZERO_CANCEL_ACK_NAV2_CM_EXIT0_OWNER_NOT_RUN"
# Actual #43674784552, exact 116144 source. Values are observed CI maxima.
# No inference that intermittent 175ms/368ms history is fully eliminated.
readonly CI_G07_PERIODS_JSON='{"source":0.073281726,"cm":0.132621561,"guard":0.04869535,"supervisor":0.074191285,"scan":0.198307533,"odom":0.128494472,"clock":0.105464129}'
# Source+tree are from exact successful CI #43674784552; WSLg/kernel/DDS parity NOT proven.
axia_p4_ci_scoped_admission() {
  [[ "$PRIVATE_SHA" == "db1eec05e01e1db0d0d2e0c05610806ef4e499f9" &&
     "$PRIVATE_TREE" == "005cc352d63067beb9d34397e51b51f7974ce7ef" &&
     "$CI_S02_G07_L2_RUN" == 43674784552 &&
     "$AXIA_P4_SHARED_GOAL_CI_ACCEPTED" == true &&
     "$AXIA_G07_REAL_EXACT_NAV2_GOAL_CANCEL_ACK_BEFORE_LIFECYCLE_PASS" == true ]] || {
    echo AXIA_P4_OWNER_CI_PIN_OR_CANCEL_PROOF_MISMATCH_NO_GOAL >&2;return 3;
  }
  python3 - "$CI_G07_PERIODS_JSON" <<'PY'
import json,os,sys
rows=json.loads(sys.argv[1])
limits={"source":.15,"cm":.15,"guard":.15,"supervisor":.15,
        "scan":.30,"odom":.30,"clock":.30}
if (set(rows)!=set(limits) or
    any(type(rows[k]) not in (float,int) or not 0<=rows[k]<limits[k]
        for k in limits)):
    raise SystemExit("AXIA_P4_OWNER_CI_SEVEN_PERIODS_UNVERIFIED")
print("AXIA_P4_OWNER_CI_SEVEN_PERIODS_BOUNDED_SCOPED_PASS")
PY
  [[ "$AXIA_P4_G07_RMW_SOURCE_MAX_SEC" == "0.12971" ]] || {
    echo AXIA_P4_OWNER_CI_CM_RMW_SOURCE_NOT_PINNED >&2;return 3;
  }
  echo "AXIA_P4_OWNER_CI_SCOPED_READY_FOR_ONE_MANUAL_TTY private_sha=$PRIVATE_SHA tree=$PRIVATE_TREE ci_run=$CI_S02_G07_L2_RUN"
  echo 'AXIA_MVP_DEMO_ACCEPTED=HOLD OWNER_WSL2_NOT_RUN'
}
if [[ "${1:-}" == '--admission-check' ]];then
  [[ $# == 1 ]] || exit 2
  axia_p4_ci_scoped_admission
  exit $?
fi
if [[ "${1:-}" == '--self-check' ]]; then
  [[ $# -eq 1 && "$PRIVATE_SHA" =~ ^[0-9a-f]{40}$ &&
     "$PRIVATE_TREE" =~ ^[0-9a-f]{40}$ ]] || exit 2
  printf 'AXIA_P4_FINAL_OWNER_STATIC_L0_PASS private_sha=%s tree=%s ci_run=%s OWNER_NOT_RUN NO_ROS_NO_GOAL\n' \
    "$PRIVATE_SHA" "$PRIVATE_TREE" "$CI_S02_G07_L2_RUN"
  exit 0
fi
[[ $# -eq 0 ]] || {
  echo 'AXIA_P4_FINAL_OWNER_BLOCKED_UNEXPECTED_ARGUMENT_NO_GOAL' >&2;exit 2;
}
[[ -t 0 && -t 1 && -r /dev/tty ]] || {
  echo 'AXIA_P4_FINAL_OWNER_BLOCKED_CONTROLLING_TTY_REQUIRED_NO_GOAL' >&2; exit 2;
}
# All actual Owner runs are blocked until the EXACT shared-runtime single-Goal
# safety regression has public CI GREEN. This check runs BEFORE private clone,
# Goal consent, ROS or Gazebo. Headless --admission-check is available for CI.
axia_p4_ci_scoped_admission || exit 3
grep -qiE '(microsoft|wsl2)' /proc/sys/kernel/osrelease || {
  echo 'AXIA_G11_G07_BLOCKED_WSL2_REQUIRED' >&2; exit 2;
}
for c in gh git bash python3 find mktemp sha256sum; do
  command -v "$c" >/dev/null || {
    echo "AXIA_G11_G07_BLOCKED_MISSING_${c}" >&2;exit 2;
  }
done
gh auth status >/dev/null 2>&1 || {
  echo 'AXIA_G11_G07_BLOCKED_PRIVATE_GH_AUTH_REQUIRED' >&2; exit 2;
}
WORK="$(mktemp -d)"
MARKER=''
cleanup() {
  [[ -z "$MARKER" ]] || rm -f -- "$MARKER"
  rm -rf -- "$WORK"
}
trap cleanup EXIT
gh repo clone silverbjin/axia-robot-safety-instructor "$WORK/instructor" \
  -- --quiet --no-checkout --filter=blob:none >/dev/null
git -C "$WORK/instructor" fetch --quiet --depth 1 origin "$PRIVATE_SHA"
git -C "$WORK/instructor" -c advice.detachedHead=false checkout --quiet --detach FETCH_HEAD
[[ "$(git -C "$WORK/instructor" rev-parse HEAD)" == "$PRIVATE_SHA" &&
   "$(git -C "$WORK/instructor" rev-parse 'HEAD^{tree}')" == "$PRIVATE_TREE" ]] || {
  echo 'AXIA_G11_G07_BLOCKED_PRIVATE_SOURCE_OR_TREE_MISMATCH' >&2;exit 2;
}
test -f "$WORK/instructor/tools/p4_g11_g07_joined_raw_review.py"
# Exact frozen Owner/CI shared first-failure remedy must exist BEFORE moving Goal.
test -f "$WORK/instructor/tools/p4_g07_evidence_pump.py"
test -f "$WORK/instructor/tools/p4_g07_rmw_clock_domain.py"
test -f "$WORK/instructor/ros2_ws/src/axia_safety_supervisor/axia_safety_supervisor/p4_g07_guard_tick_policy.py"
echo 'AXIA_P4_OWNER_SAME_CI_EXECUTOR_G07_ASYNC_EVIDENCE_GUARD_40MS_CLOCK_DOMAIN_SOURCE_PIN_VERIFIED_NO_GOAL'
echo "AXIA_G11_G07_PRIVATE_SOURCE_AND_TREE_VERIFIED sha=$PRIVATE_SHA"
echo 'SIMULATION ONLY: one final WSL2 G07 Goal after Owner manual controlling TTY consent.'
echo 'Scope: one real Goal, original 14-topic bag, first CM source/receive to Guard, ordered Nav2/CM clean exit.'
echo 'CI #43674784552 scoped success: 7-channel TTL, shared async evidence, G07-only Guard 40ms, S02 native zero, Goal Cancel and CM exit0. Earlier Owner 151.8ms/CM clock-step and other intermittent failures are NOT proven permanently eliminated.'
echo 'AXIA_MVP_DEMO_ACCEPTED=HOLD until Owner original raw and first timing boundary review.'
echo 'G11 0/15, G12 HOLD, G13 0/2 remain v1-only and do NOT block reduced demo.'
echo 'The private Owner runner requires YES-P2-G07-GOAL; this wrapper never supplies consent.'
BASE="$HOME/axia_p2_private_evidence"
mkdir -p "$BASE"; chmod 700 "$BASE"
MARKER="$(mktemp "$BASE/.g11-start-XXXXXXXX")"
OWNER_RC=0
AXIA_P2_OWNER_PINNED_SHA="$PRIVATE_SHA" \
AXIA_G11_RUN_CUSTODY_REQUIRED=1 \
  bash "$WORK/instructor/scripts/p2_owner_l3_wsl2.sh" \
  --case G07 --mvp-relocated-obstacle || OWNER_RC=$?
echo "AXIA_G11_G07_OWNER_RUNNER_EXIT_CODE=$OWNER_RC"
RUN_ROOTS=()
while IFS= read -r -d '' summary; do
  RUN_ROOTS+=("${summary%/summary.json}")
done < <(find "$BASE" -mindepth 2 -maxdepth 2 -name summary.json -type f \
           -newer "$MARKER" -print0)
if (( ${#RUN_ROOTS[@]} != 1 ));then
  echo "AXIA_G11_G07_BLOCKED_NEW_RUN_ROOT_AMBIGUOUS count=${#RUN_ROOTS[@]}" >&2
  exit 3
fi
RUN_ROOT="${RUN_ROOTS[0]}"
# Fail at the earliest pre-Goal lifecycle boundary, not at downstream missing
# action/14-topic/RMW files. This still preserves private archive/custody.
if [[ "$OWNER_RC" != 0 && -f "$RUN_ROOT/G07/first_startup_boundary.json" ]]; then
  if python3 - "$RUN_ROOT/G07/first_startup_boundary.json" \
       "$RUN_ROOT/G07/startup_verdict.json" <<'PY'
import json,sys
from pathlib import Path
try:
    first=json.loads(Path(sys.argv[1]).read_text())
    startup=json.loads(Path(sys.argv[2]).read_text())
    blocked=(startup.get("goal_sent") is False and
             first.get("first_failure_phase")=="PRE_GOAL" and
             str(first.get("first_failure","")).startswith("NAVIGATION_STARTUP_") and
             first.get("owner_accepted") is False)
    if not blocked:sys.exit(3)
    print("AXIA_P4_OWNER_FIRST_PREGOAL_BOUNDARY_LOCKED_NO_GOAL_RAW "+json.dumps({
        k:first.get(k) for k in ("first_failure",
             "navigation_request_sent","navigation_startup_callback_seen",
             "navigation_elapsed_sec","downstream_unverified")
    },sort_keys=True))
except (OSError,ValueError,KeyError,TypeError):
    sys.exit(3)
PY
  then
    echo "AXIA_P4_OWNER_FIRST_FAILURE_ORIGINAL=$RUN_ROOT/G07/first_startup_boundary.json"
    echo "AXIA_G11_G07_PRIVATE_ORIGINAL=$RUN_ROOT.tar.gz"
    echo 'AXIA_MVP_DEMO_ACCEPTED=HOLD NO_GOAL_NO_RMW_OR_CONTACT_PROOF'
    exit 3
  fi
fi
MANIFEST="$(
python3 - "$HOME" "$RUN_ROOT" <<'PY'
from pathlib import Path
import json,sys
home=Path(sys.argv[1]).resolve()
run=Path(sys.argv[2]).resolve()
archive=run.with_suffix(".tar.gz")
side=archive.with_name(archive.name+".sha256")
try:
    checksum=side.read_text(encoding="utf-8").split()[0]
    source=(run/"source.sha").read_text(encoding="utf-8").strip()
    matches=[]
    for candidate in (home/".axia_p4_g11_session_custody"/"manifests").glob("*.json"):
        if candidate.is_symlink():continue
        try:
            j=json.loads(candidate.read_text(encoding="utf-8"))
        except (ValueError,OSError):continue
        if (j.get("archive_sha256")==checksum
                and j.get("owner_source_sha")==source
                and j.get("archive_original_relative_to_owner")==
                str(archive.relative_to(home))):
            matches.append(candidate)
    if len(matches)!=1:
        raise ValueError("G11_MANIFEST_AMBIGUOUS_OR_MISSING")
    print(matches[0])
except (OSError,ValueError,IndexError) as exc:
    print("AXIA_G11_G07_BLOCKED_MANIFEST_LOOKUP "+str(exc),file=sys.stderr)
    sys.exit(3)
PY
)" || exit 3
REVIEW_OUT="$HOME/.axia_p4_g11_session_custody/reviews/g07-$(date -u +%Y%m%dT%H%M%SZ)-$$.json"
REVIEW_RC=0
python3 "$WORK/instructor/tools/p4_g11_g07_joined_raw_review.py" \
  --owner-home "$HOME" --run-root "$RUN_ROOT" \
  --custody-manifest "$MANIFEST" --output "$REVIEW_OUT" || REVIEW_RC=$?
echo "AXIA_G11_G07_JOINED_REVIEW_EXIT_CODE=$REVIEW_RC"
# G07 only: read the already-recorded original Observer ledger (NOT ROS).
# Compare CM publisher/receive times and actual Guard FIRST TTL transition
# even when the Owner Goal was stopped and the original custody is INCOMPLETE.
RMW_OUT="$HOME/.axia_p4_g11_session_custody/reviews/g07-rmw-$(date -u +%Y%m%dT%H%M%SZ)-$$.json"
RMW_RC=0
python3 - "$WORK/instructor/tools" "$RUN_ROOT/G07/live" "$RMW_OUT" <<'PY' || RMW_RC=$?
from pathlib import Path
from datetime import datetime,timezone
import json,os,sys
sys.path.insert(0,sys.argv[1])
from p2_g07_ci_moving_goal_oracle import (
    cm_rmw_provenance,first_guard_cm_delivery_boundary,cm_upstream_rmw_gap_window)
live=Path(sys.argv[2])
output=Path(sys.argv[3])
try:
    rows=[json.loads(line) for line in
          (live/"actual_ros_events.jsonl").read_text().splitlines()]
    goal_starts=[row["t"] for row in rows
                 if row.get("kind")=="owner_goal_published"]
    if len(goal_starts)!=1 or not rows:
        raise ValueError("GOAL_START_OR_ORIGINAL_LEDGER_UNAVAILABLE")
    result=json.loads((live/"ci_moving_goal_result.json").read_text())
    goal_start=goal_starts[0]
    at=max(row["t"] for row in rows if isinstance(row.get("t"),(int,float)))
    rmw=cm_rmw_provenance(rows,goal_start=goal_start,end=at)
    upstream=cm_upstream_rmw_gap_window(rows,goal_start=goal_start,end=at)
    boundary=first_guard_cm_delivery_boundary(
        rows,result.get("first_guard_latch"),goal_start=goal_start)
    cm_rows=[v for v in rows if v.get("kind")=="pre_guard"
             and isinstance(v.get("t"),(int,float))
             and goal_start<=v["t"]<=at]
    source_gaps=[]; receive_gaps=[]; observer_gaps=[]
    valid_rmw=(len(cm_rows)>=10 and all(
        type(v.get("rmw_source_ns")) is int and v["rmw_source_ns"]>0
        and type(v.get("rmw_received_ns")) is int
        and v["rmw_received_ns"]>=v["rmw_source_ns"]
        and type(v.get("rmw_publication_seq")) is int
        for v in cm_rows))
    if valid_rmw:
        for left,right in zip(cm_rows,cm_rows[1:]):
            source_gaps.append((right["rmw_source_ns"]-left["rmw_source_ns"])/1e9)
            receive_gaps.append((right["rmw_received_ns"]-left["rmw_received_ns"])/1e9)
            observer_gaps.append(right["t"]-left["t"])
            if right["rmw_publication_seq"]!=left["rmw_publication_seq"]+1:
                valid_rmw=False
    maxima={
       "cm_source_sec":max(source_gaps) if source_gaps else None,
       "cm_receive_sec":max(receive_gaps) if receive_gaps else None,
       "cm_observer_sec":max(observer_gaps) if observer_gaps else None,
    }
    # Supervisor source/receive sequence must also be proven; no CM-only
    # no-gap pass when upstream RMW metadata was absent or silently dropped.
    upstream_rows=[v for v in rows if v.get("kind")=="supervised"
        and isinstance(v.get("t"),(int,float))
        and goal_start<=v["t"]<=at]
    valid_supervisor=(len(upstream_rows)>=10 and all(
        type(v.get("rmw_source_ns")) is int and v["rmw_source_ns"]>0
        and type(v.get("rmw_received_ns")) is int
        and v["rmw_received_ns"]>=v["rmw_source_ns"]
        and type(v.get("rmw_publication_seq")) is int
        for v in upstream_rows))
    if valid_supervisor:
        valid_supervisor=all(
            right["rmw_publication_seq"]==left["rmw_publication_seq"]+1
            and 0 < (right["rmw_source_ns"]-left["rmw_source_ns"])/1e9 < 0.15
            and 0 < (right["rmw_received_ns"]-left["rmw_received_ns"])/1e9 < 0.15
            for left,right in zip(upstream_rows,upstream_rows[1:]))
    requirements={
       "max_source_interval_sec":0.15,
       "max_cm_interval_sec":0.15,
       "max_guard_interval_sec":0.15,
       "max_supervisor_fsm_interval_sec":0.15,
       "max_scan_interval_sec":0.30,
       "max_odom_interval_sec":0.30,
       "max_clock_interval_sec":0.30,
    }
    # Numeric candidate only. A first Guard latch, any missing proof, or a
    # 150ms CM publisher/receive gap blocks this Owner postrun review.
    safety_timing_candidate=(
       valid_rmw and valid_supervisor and all(x is not None and 0<=x<0.15 for x in maxima.values())
       and all(type(result.get(k)) in (int,float)
               and 0<=result[k]<=limit for k,limit in requirements.items())
       and result.get("status")=="NUMERICAL_CANDIDATE"
       and result.get("common_g07_ci_oracle_status")=="CI_GAZEBO_MOVING_GOAL_CANDIDATE"
       and result.get("shared_execution_mode")=="owner"
       and result.get("owner_authority_verified") is True
       and result.get("guard_latched") is False
       and result.get("first_timing_violation") is None
       and type(result.get("odom_stopped_dwell_sec")) in (int,float)
       and result["odom_stopped_dwell_sec"]>=1.0
       and rmw["status"]=="NO_CM_OBSERVED_GAP_IN_BOUND"
       and upstream["status"]=="NO_CM_SOURCE_GAP_OBSERVED"
       and boundary["status"]=="NO_FIRST_GUARD_LATCH_TRACE")
    report={
        "schema":"axia_p4_g07_owner_rmw_postrun_diagnostic_v1",
        "created_utc":datetime.now(timezone.utc).isoformat(),
        "rmw_cm":rmw,"guard_first_cm":boundary,
        "cm_supervisor":upstream,
        "goal_uuid":result.get("goal_uuid"),
        "source_runtime_status":result.get("status"),
        "safety_ttl_formally_assessed":False,
        "owner_l3_accepted":False,"formal_accepted":False,
        "g11_formal_count":0,"certified_estop":False,
        "read_only_reviewer_no_new_ros_goal_no_upload":True,
        "owner_safety_timing_numeric_candidate":bool(safety_timing_candidate),
        "max_cm_rmw_observed_intervals":maxima,
        "supervisor_rmw_coverage_verified":bool(valid_supervisor),
        "raw_original_review_required":True
    }
    output.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    fd=os.open(output,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    with os.fdopen(fd,"w",encoding="utf-8") as stream:
        json.dump(report,stream,sort_keys=True,indent=2)
        stream.write("\n")
    print("AXIA_G11_G07_RMW_CM_STATUS="+str(rmw["status"]))
    print("AXIA_G11_G07_RMW_CM_ATTRIBUTION="+str(rmw["attribution"]))
    print("AXIA_G11_G07_FIRST_CM_SUPERVISOR_RMW_WINDOW="+json.dumps(upstream,sort_keys=True))
    print("AXIA_G11_G07_RMW_CM_FIRST_GAP="+json.dumps(rmw["first_gap"],sort_keys=True))
    print("AXIA_G11_G07_FIRST_GUARD_CM_BOUNDARY="+json.dumps(
        boundary["first_timing_violation"],sort_keys=True))
    print("AXIA_G11_G07_RMW_PRIVATE_REVIEW="+str(output))
    print("AXIA_G11_G07_RMW_NO_AUTO_GOAL_NO_UPLOAD_FORMAL_HOLD")
    print("AXIA_P4_FINAL_OWNER_FIRST_TIMING_NUMERIC_CANDIDATE="+
          str(bool(safety_timing_candidate)).lower())
    if not safety_timing_candidate:
        raise ValueError("FIRST_CM_SOURCE_RECEIVE_GUARD_TIMING_UNVERIFIED_OR_BREACHED")
except (OSError,ValueError,TypeError,KeyError) as exc:
    print("AXIA_G11_G07_RMW_READONLY_BLOCKED "+type(exc).__name__+":"+str(exc),
          file=sys.stderr)
    sys.exit(3)
PY
echo "AXIA_G11_G07_RMW_REVIEW_EXIT_CODE=$RMW_RC"
echo "AXIA_G11_G07_PRIVATE_ORIGINAL=$RUN_ROOT.tar.gz"
echo "AXIA_G11_G07_FORMAL_0_OF_15_OWNER_ACCEPTANCE_HOLD CERTIFIED_ESTOP=false"
echo "AXIA_MVP_DEMO_ACCEPTED=HOLD FINAL_OWNER_RAW_REVIEW_REQUIRED_NO_AUTOMATIC_ACCEPTANCE"
if (( OWNER_RC != 0 ));then exit "$OWNER_RC";fi
if (( REVIEW_RC != 0 || RMW_RC != 0 ));then exit 3;fi
exit 0
