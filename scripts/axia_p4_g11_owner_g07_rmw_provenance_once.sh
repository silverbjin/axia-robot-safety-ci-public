#!/usr/bin/env bash
# AXIA P4 G11: one manually consented G07 GUI Goal, archived raw + RMW provenance.
# No simulated Goal in CI, no implicit consent, no public RAW upload.
set -Eeuo pipefail
umask 077
PRIVATE_SHA="c44414f8e3bad37a349565f211d554540cccb062"
PRIVATE_TREE="d2e3044689a5873cd61d6bc5f84a40b20a81f84e"
[[ -t 0 && -t 1 && -r /dev/tty ]] || {
  echo 'AXIA_G11_G07_BLOCKED_INTERACTIVE_OWNER_TTY_REQUIRED' >&2; exit 2;
}
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
echo "AXIA_G11_G07_PRIVATE_SOURCE_AND_TREE_VERIFIED sha=$PRIVATE_SHA"
echo 'SIMULATION ONLY: Exactly one existing P2 G07 Goal after manual Owner TTY consent.'
echo 'The existing Owner runner will require YES-P2-G07-GOAL; it is NEVER entered by this script.'
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
RMW_OUT="$HOME/.axia_p4_g11_session_custody/reviews/g07-rmw-$(date -u +%Y%m%dT%H%M%SZ)-$.json"
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
        "no_ros_no_goal_no_upload":True
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
except (OSError,ValueError,TypeError,KeyError) as exc:
    print("AXIA_G11_G07_RMW_READONLY_BLOCKED "+type(exc).__name__+":"+str(exc),
          file=sys.stderr)
    sys.exit(3)
PY
echo "AXIA_G11_G07_RMW_REVIEW_EXIT_CODE=$RMW_RC"
echo "AXIA_G11_G07_PRIVATE_ORIGINAL=$RUN_ROOT.tar.gz"
echo "AXIA_G11_G07_FORMAL_0_OF_15_OWNER_ACCEPTANCE_HOLD CERTIFIED_ESTOP=false"
if (( OWNER_RC != 0 ));then exit "$OWNER_RC";fi
if (( REVIEW_RC != 0 || RMW_RC != 0 ));then exit 3;fi
exit 0
