#!/usr/bin/env bash
# AXIA G13: ONE external instructor-authorized WSL2 PC, real ROS/Gazebo,
# official Nav2 lifecycle + Collision Monitor NO-GOAL smoke.
# Safety: NO automatic Goal, Crash, Fault, E-Stop, or student release.
set -Eeuo pipefail
umask 077

# Read-only triage of PREVIOUS failed G13 attempt. Must run before
# WSL2, gh, ROS, or clone preflights, and must never start another Goal.
g13_first_failure_readonly() {
  python3 - "$1" <<'PY'
from pathlib import Path
import hashlib,json,re,sys
raw=Path(sys.argv[1]).expanduser()
allowed=Path.home()/".axia_g13_external_pc_evidence"
try:
    root=raw.resolve(strict=True)
    home=allowed.resolve(strict=True)
    if (not root.is_dir() or root.parent!=home
        or not re.fullmatch(r"g13-PC[12]-[A-Za-z0-9_-]+",root.name)
        or raw.is_symlink()):
        raise ValueError("G13_EVIDENCE_PATH_NOT_CANONICAL")
except (OSError,ValueError) as e:
    print("AXIA_G13_PREVIOUS_RUN_BLOCKED_INVALID_EVIDENCE_DIRECTORY",file=sys.stderr)
    sys.exit(2)
print("AXIA_G13_PREVIOUS_RUN_READONLY_EVIDENCE="+str(root))
receipt=root/"g13_no_goal_receipt.json"
try:
    data=json.loads(receipt.read_text(encoding="utf-8"))
    print("AXIA_G13_PREVIOUS_RUN_EXIT_CODE="+str(data.get("run_exit_code","UNKNOWN")))
    print("AXIA_G13_PREVIOUS_RUN_NO_GOAL_PASS="+str(data.get("no_goal_smoke_pass","UNKNOWN")))
except (ValueError,OSError):
    print("AXIA_G13_PREVIOUS_RUN_RECEIPT_MISSING_OR_INVALID")
# Start/lifecycle failure is observed BEFORE shutdown or wrapper final rc.
# Report the first available specific failure witness, not the last
# RuntimeError nor success from any unrelated previous CI run.
paths=[
  "actual/staged_startup.log",
  "actual/g07_ordered_shutdown.log",
  "actual/g07_shutdown_audit.json",
  "actual/launch.log",
  "smoke.log",
]
markers=[
 ("LOCALIZATION_START",re.compile(r"(?:P2_STAGED_NO_GOAL_BLOCKED|BLOCKED|ERROR).{0,240}LOCALIZATION_START|LOCALIZATION_START.{0,240}(?:BLOCKED|TIMEOUT|ERROR|FAILED)|lifecycle_manager_localization.*(?:timed out|failed|ERROR)",re.I)),
 ("NAVIGATION_START",re.compile(r"(?:P2_STAGED_NO_GOAL_BLOCKED|BLOCKED|ERROR).{0,240}NAVIGATION_START|NAVIGATION_START.{0,240}(?:BLOCKED|TIMEOUT|ERROR|FAILED)|lifecycle_manager_navigation.*(?:timed out|failed|ERROR)",re.I)),
 ("STARTUP_BLOCKED",re.compile(r"P2_STAGED_NO_GOAL_BLOCKED|G07_NATIVE_LIFECYCLE_STARTUP_SERVICE_TIMEOUT")),
 ("LIFECYCLE_SHUTDOWN",re.compile(r"SHUTDOWN_BLOCKED|SHUTDOWN.*(?:TIMEOUT|ERROR|BLOCKED)|NAVIGATION_ACK.*false|LOCALIZATION_ACK.*false",re.I)),
 ("CM_SHUTDOWN",re.compile(r"G07_REAL_SHUTDOWN_L2_CM_PROCESS_NONCLEAN|CM_PROCESS_NONCLEAN|CM.*(?:SIGABRT|SIGKILL)",re.I)),
 ("FORCED_TEARDOWN",re.compile(r"P2_L2_FORCED_TEARDOWN|P2_L2_FORCED_SIGKILL")),
 ("OTHER_RUNTIME_ERROR",re.compile(r"(?:^|\\s)(?:ERROR|BLOCKED|Traceback|RuntimeError):?",re.I)),
]
witnesses=[]
for name in paths:
    p=root/name
    if p.is_symlink() or not p.is_file():
        continue
    sha=hashlib.sha256()
    with p.open("rb") as stream:
        for buf in iter(lambda:stream.read(1048576),b""):
            sha.update(buf)
    print("AXIA_G13_PREVIOUS_RUN_LOG_HASH="+name+":"+sha.hexdigest())
    # Bounded review; never echo the complete (possibly private) logs.
    with p.open("r",encoding="utf-8",errors="replace") as stream:
        for line_number,line in enumerate(stream,1):
            if line_number>150000:
                print("AXIA_G13_PREVIOUS_RUN_LOG_REVIEW_BOUNDED="+name)
                break
            for label,pattern in markers:
                if pattern.search(line):
                    witnesses.append((paths.index(name),line_number,label,name))
                    break
if witnesses:
    # Staged startup is earliest stage. Shutdown failure cannot outrank it;
    # within one source preserve original line order.
    first=min(witnesses,key=lambda row:(row[0],row[1]))
    print("AXIA_G13_PREVIOUS_RUN_FIRST_FAILURE="+first[2])
    print("AXIA_G13_PREVIOUS_RUN_FIRST_FAILURE_SOURCE="+first[3]+":"+str(first[1]))
    print("AXIA_G13_PREVIOUS_RUN_FIRST_FAILURE_PROVENANCE=FIRST_AVAILABLE_STAGE_LOG_NOT_GLOBAL_CAUSAL_PROOF")
else:
    print("AXIA_G13_PREVIOUS_RUN_FIRST_FAILURE=UNDETERMINED_FROM_AVAILABLE_LOGS")
print("AXIA_G13_PREVIOUS_RUN_DIAGNOSTIC_ONLY_NO_GOAL_NO_RETRY")
PY
}
if [[ "${1:-}" == "--inspect" ]]; then
  [[ "$#" == 2 ]] || {
    echo 'AXIA_G13_USAGE_INSPECT=--inspect_OLD_G13_EVIDENCE_DIRECTORY' >&2; exit 2;
  }
  g13_first_failure_readonly "$2"
  exit $?
fi
[[ "$#" == 1 && ( "$1" == "PC1" || "$1" == "PC2" ) ]] || {
  echo 'AXIA_G13_USAGE=--LABEL_PC1_OR_PC2_AS_FIRST_ARGUMENT' >&2; exit 2;
}
LABEL="$1"
PRIVATE_SHA='afe4e9ae3f6542ef7b2bd3097ce5c15ae5a5ddcc'
PRIVATE_TREE='580dec5be1988b26d5189616b1b01559a0f1f9a5'
if [[ ! -r /proc/sys/kernel/osrelease ]] ||
   ! grep -Eqi '(microsoft|wsl2)' /proc/sys/kernel/osrelease ||
   ! grep -q '24.04' /etc/os-release ||
   [[ "$(uname -m)" != "x86_64" ]]; then
  echo 'AXIA_G13_BLOCKED_WSL2_UBUNTU2404_X86_64_REQUIRED' >&2; exit 2
fi
for c in gh git python3 bash timeout sha256sum ros2 gz; do
  if ! command -v "$c" >/dev/null 2>&1 && [[ "$c" != ros2 && "$c" != gz ]]; then
    echo "AXIA_G13_BLOCKED_TOOL_MISSING=$c" >&2; exit 2
  fi
done
[[ -r /opt/ros/jazzy/setup.bash ]] || {
  echo 'AXIA_G13_BLOCKED_OFFICIAL_ROS_JAZZY_SETUP_MISSING' >&2; exit 2;
}
# ROS setup may be unset in the user's login shell.
set +u
source /opt/ros/jazzy/setup.bash
set -u
for c in ros2 gz; do
  command -v "$c" >/dev/null || {
    echo "AXIA_G13_BLOCKED_ROS_GAZEBO_MISSING=$c" >&2; exit 2;
  }
done
[[ "${ROS_DISTRO:-}" == jazzy ]] || {
  echo 'AXIA_G13_BLOCKED_WRONG_ROS_DISTRO' >&2; exit 2;
}
gh auth status >/dev/null 2>&1 || {
  echo 'AXIA_G13_BLOCKED_OWNER_AUTH_FOR_SEALED_INSTRUCTOR_REQUIRED' >&2; exit 2;
}
BASE="$HOME/.axia_g13_external_pc_evidence"
mkdir -p -m 700 "$BASE"
OUT="$(mktemp -d "$BASE/g13-$LABEL-XXXXXXXX")"
WORK="$(mktemp -d)"
cleanup() { rm -rf -- "$WORK"; }
trap cleanup EXIT
echo "AXIA_G13_EVIDENCE_ROOT=$OUT"
echo "AXIA_G13_PC_LABEL=$LABEL SIMULATION_ONLY NO_NAV2_GOAL NO_FAULT"
# Clone a sealed instructor SHA. The source never enters a student repo.
gh repo clone silverbjin/axia-robot-safety-instructor "$WORK/instructor" \
  -- --quiet --no-checkout --filter=blob:none >/dev/null
git -C "$WORK/instructor" fetch --quiet --depth 1 origin "$PRIVATE_SHA"
git -C "$WORK/instructor" -c advice.detachedHead=false checkout --quiet --detach FETCH_HEAD
[[ "$(git -C "$WORK/instructor" rev-parse HEAD)" == "$PRIVATE_SHA" &&
   "$(git -C "$WORK/instructor" rev-parse 'HEAD^{tree}')" == "$PRIVATE_TREE" ]] || {
  echo 'AXIA_G13_BLOCKED_PRIVATE_SHA_OR_TREE_MISMATCH' >&2; exit 2;
}
echo "AXIA_G13_PRIVATE_PINNED_SOURCE_VERIFIED=$PRIVATE_SHA"
# Exact owner-locked 25 package/5 official file parity; no apt install.
export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
if [[ "$LABEL" == PC1 ]]; then export ROS_DOMAIN_ID=74; else export ROS_DOMAIN_ID=75; fi
export GZ_PARTITION="axia_p2_g13_${LABEL}_$$_$ROS_DOMAIN_ID"
export AXIA_P0_SIM_ONLY=1
export AXIA_P2_G07_PHYSICAL_PREFLIGHT=1
export AXIA_P2_G07_OWNER_PARITY_CHECK=1
export AXIA_G07_OWNER_STARTUP_PARITY=1
export AXIA_G07_SHUTDOWN_L2_ONLY=1
export AXIA_G07_CI_SIM_GOAL_ALLOWED=0
export AXIA_G07_CI_OWNER_BAG_PARITY=0
export AXIA_G13_NO_GOAL=1
export AXIA_P2_SMOKE_RESULTS="$OUT/actual"
cd "$WORK/instructor"
bash -n scripts/p2_no_goal_smoke_ci.sh
PARITY_RC=0
python3 tools/p2_g07_owner_env_parity.py --mode owner \
  --output "$OUT/runtime_parity.json" >"$OUT/runtime_parity.log" 2>&1 || PARITY_RC=$?
if (( PARITY_RC != 0 )); then
  echo 'AXIA_G13_BLOCKED_REAL_PC_RUNTIME_PARITY' >&2
  tail -n 15 "$OUT/runtime_parity.log" >&2
  echo 'AXIA_G13_GOAL_NOT_SENT_FORMAL_0_OF_2'
  exit 3
fi
echo 'AXIA_G13_REAL_PC_EXACT_25_PACKAGES_5_FILES_PARITY_PASS'
SMOKE_RC=0
timeout --signal=TERM --kill-after=10s 540s \
  bash scripts/p2_no_goal_smoke_ci.sh >"$OUT/smoke.log" 2>&1 || SMOKE_RC=$?
# On failure, preserve first error and original logs. NEVER auto-retry.
if (( SMOKE_RC != 0 )); then
  echo "AXIA_G13_L2_SMOKE_FAILED_RC=$SMOKE_RC; PRESERVE_FIRST_FAILURE_NO_RETRY"
  g13_first_failure_readonly "$OUT" || true
fi
python3 - "$OUT" "$LABEL" "$PRIVATE_SHA" "$SMOKE_RC" <<'PY'
import hashlib,json,os,sys
from pathlib import Path
from datetime import datetime,timezone
root=Path(sys.argv[1]);label=sys.argv[2];source=sys.argv[3];rc=int(sys.argv[4])
files=["actual/startup_verdict.json","actual/startup_verdict.localization_start.native.json",
       "actual/startup_verdict.navigation_start.native.json",
       "actual/g07_ordered_shutdown.json","actual/g07_shutdown_audit.json",
       "actual/teardown.txt","smoke.log"]
hashes={}
for name in files:
    p=root/name
    if p.is_file():
        hashes[name]=hashlib.sha256(p.read_bytes()).hexdigest()
def load(name):
    try:return json.loads((root/name).read_text(encoding="utf-8"))
    except (OSError,ValueError):return {}
startup=load("actual/startup_verdict.json")
loc=load("actual/startup_verdict.localization_start.native.json")
nav=load("actual/startup_verdict.navigation_start.native.json")
down=load("actual/g07_ordered_shutdown.json")
teardown=(root/"actual/teardown.txt").read_text() if (root/"actual/teardown.txt").is_file() else ""
log=(root/"smoke.log").read_text() if (root/"smoke.log").is_file() else ""
machine_id=Path("/etc/machine-id").read_text().strip()
fingerprint=hashlib.sha256(("AXIA_G13_PC_VERSION1:"+machine_id).encode()).hexdigest()
passed=all((
 rc==0,
 startup.get("status")=="SMOKE_READY",
 startup.get("goal_sent") is False,
 loc.get("status")=="ACK",loc.get("success") is True,
 nav.get("status")=="ACK",nav.get("success") is True,
 down.get("status")=="NAV2_LIFECYCLE_SHUTDOWN_ACK",
 down.get("navigation_ack") is True,
 down.get("localization_ack") is True,
 "G07_REAL_SHUTDOWN_L2_CM_CLEAN_EXIT_AFTER_NAV2_ACK_PASS" in log,
 "P2_L2_GRACEFUL_TEARDOWN" in teardown,
 "P2_NO_GOAL_STATIC_AND_RUNTIME_READINESS_OBSERVED" in log,
))
report={
 "schema":"axia_g13_external_pc_no_goal_receipt_v1",
 "created_utc":datetime.now(timezone.utc).isoformat(),
 "label":label,"machine_fingerprint_sha256":fingerprint,
 "instructor_private_source_sha":source,
 "goal_sent":False,"fault_injected":False,"certified_estop":False,
 "runtime_parity_passed":True,
 "lifecycle_localization_ack":loc.get("status")=="ACK",
 "lifecycle_navigation_ack":nav.get("status")=="ACK",
 "cm_clean_exit_after_ack":"G07_REAL_SHUTDOWN_L2_CM_CLEAN_EXIT_AFTER_NAV2_ACK_PASS" in log,
 "no_goal_smoke_pass":passed,"run_exit_code":rc,
 "file_sha256":hashes,
 "g13_two_distinct_pcs_formally_accepted":False,
 "instructor_main_merged":False,
}
output=root/"g13_no_goal_receipt.json"
fd=os.open(output,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
with os.fdopen(fd,"w",encoding="utf-8") as f:
    json.dump(report,f,sort_keys=True,indent=2)
    f.write("\n")
print("AXIA_G13_MACHINE_FINGERPRINT_SHA256="+fingerprint)
print("AXIA_G13_RECEIPT="+str(output))
if not passed:
    print("AXIA_G13_"+label+"_ACTUAL_NO_GOAL_BLOCKED_FIRST_LOG_REQUIRED")
    sys.exit(3)
print("AXIA_G13_"+label+"_REAL_JAZZY_HARMONIC_NO_GOAL_L2_PASS_CANDIDATE")
print("AXIA_G13_TWO_DISTINCT_EXTERNAL_PC_RECEIPTS_REQUIRED_FORMAL_0_OF_2")
PY
