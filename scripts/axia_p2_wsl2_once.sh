#!/usr/bin/env bash
# AXIA P2: Owner WSL2 L2 no-Goal preflight only. NOT G05/G06/G07 acceptance.
set -Eeuo pipefail
umask 077
REPO='silverbjin/axia-robot-safety-instructor'
BRANCH='feat/p2-g05-g07-base-timeout-contract-20261108'
SHA='1728b8708c6672ca8bb059fd25aab86ec9fa2c46'
if [[ $# == 1 && "$1" == --self-check ]]; then
  [[ "$SHA" =~ ^[0-9a-f]{40}$ ]] || exit 2
  echo "AXIA_P2_OWNER_PUBLIC_CONTRACT_OK private_sha=$SHA L3_NOT_RUN"
  exit 0
fi
[[ $# == 0 ]] || { echo 'BLOCKED: invalid argument' >&2; exit 2; }
[[ -t 0 && -t 1 && -r /dev/tty ]] || { echo 'BLOCKED: controlling TTY required' >&2; exit 2; }
[[ "$(uname -s)" == Linux ]] || exit 2
# shellcheck disable=SC1091
source /etc/os-release
[[ "$ID" == ubuntu && "$VERSION_ID" == '24.04' ]] || { echo 'BLOCKED: Ubuntu 24.04 required'; exit 2; }
grep -qiE 'microsoft|wsl' /proc/sys/kernel/osrelease || { echo 'BLOCKED: WSL2 required'; exit 2; }
[[ -f /opt/ros/jazzy/setup.bash ]] || { echo 'BLOCKED: ROS Jazzy missing'; exit 2; }
set +u
# shellcheck disable=SC1091
source /opt/ros/jazzy/setup.bash
set -u
for cmd in gh git python3 colcon ros2 gz setsid timeout sha256sum tar; do
  command -v "$cmd" >/dev/null || { echo "BLOCKED: missing $cmd"; exit 2; }
done
gh auth status >/dev/null 2>&1 || { echo 'BLOCKED: private GitHub authentication required'; exit 2; }
BASE="$HOME/axia_p2_private_evidence"
mkdir -p "$BASE"; chmod 700 "$BASE"
OUT="$(mktemp -d "$BASE/p2-owner-prelocal-XXXXXXXX")"
SRC="$(mktemp -d "$HOME/.axia_p2_src_XXXXXXXX")"
STATE=BLOCKED
RC_L2=125
finish() {
  rc=$?
  trap - EXIT INT TERM
  set +e
  if [[ -d "$SRC" && "$SRC" == "$HOME"/.axia_p2_src_* ]]; then rm -rf -- "$SRC"; fi
  python3 - "$OUT/summary.json" "$SHA" "$STATE" "$RC_L2" "$rc" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1]);p.write_text(json.dumps({
  'private_sha':sys.argv[2], 'state':sys.argv[3],
  'l2_exit':int(sys.argv[4]), 'wrapper_exit':int(sys.argv[5]),
  'G05':'NOT_RUN', 'G06':'NOT_RUN', 'G07':'NOT_RUN',
  'gate_accepted':False, 'certified_estop':False,
  'goal_sent':False, 'fault_injected':False
},indent=2,sort_keys=True)+'\n')
PY
  (cd "$OUT" && find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 -r sha256sum > SHA256SUMS)
  tar -czf "$OUT.tar.gz" -C "$BASE" "$(basename "$OUT")"
  sha256sum "$OUT.tar.gz" > "$OUT.tar.gz.sha256"
  printf '\nP2_OWNER_STATUS=%s\nEVIDENCE=%s\nARCHIVE=%s\n' "$STATE" "$OUT" "$OUT.tar.gz"
  echo 'G05=NOT_RUN G06=NOT_RUN G07=NOT_RUN CERTIFIED_ESTOP=false'
  exit "$rc"
}
trap finish EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
export ROS_DOMAIN_ID="$((20 + $$ % 40))"
export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
export GZ_PARTITION="axia_p2_owner_$$_$(date -u +%s)"
export AXIA_P0_SIM_ONLY=1
printf 'AXIA P2 Owner WSL2 prelocal; exact private SHA=%s\n' "$SHA"
printf 'Evidence: %s\n' "$OUT"
gh repo clone "$REPO" "$SRC/instructor" -- --single-branch --branch "$BRANCH" --depth 1 > "$OUT/checkout.log" 2>&1 || {
  echo 'BLOCKED: private clone failed'; exit 2; }
[[ "$(git -C "$SRC/instructor" rev-parse HEAD)" == "$SHA" ]] || {
  echo 'BLOCKED: private SHA mismatch'; exit 2; }
[[ -z "$(git -C "$SRC/instructor" status --porcelain)" ]] || { echo 'BLOCKED: dirty checkout'; exit 2; }
printf '%s\n' "$SHA" > "$OUT/source.sha"
cd "$SRC/instructor"
for pkg in nav2_bringup nav2_minimal_tb3_sim ros_gz_sim; do
  ros2 pkg prefix "$pkg" >/dev/null || { echo "BLOCKED: ROS package $pkg"; exit 2; }
done
export AXIA_P2_SMOKE_RESULTS="$OUT/no_goal"
echo 'Running official Waffle / Nav2 / Harmonic L2 no-Goal smoke...'
if timeout --signal=TERM --kill-after=25s 900s bash scripts/p2_no_goal_smoke_ci.sh > "$OUT/l2.log" 2>&1; then
  RC_L2=0
else
  RC_L2=$?
  echo "BLOCKED: L2 exit=$RC_L2; log=$OUT/l2.log" >&2
  tail -n 30 "$OUT/l2.log" >&2 || true
  exit 2
fi
python3 - "$OUT/no_goal/startup_verdict.json" "$OUT/no_goal/source_sha.txt" "$SHA" <<'PY'
import json,sys
from pathlib import Path
j=json.loads(Path(sys.argv[1]).read_text())
assert j.get('status')=='SMOKE_READY'
assert j.get('gate_accepted') is False
assert j.get('goal_sent') is False and j.get('fault_injected') is False
assert Path(sys.argv[2]).read_text().strip()==sys.argv[3]
print('P2_OWNER_L2_NO_GOAL_PASS G05_G06_G07_ACCEPTED=false')
PY
STATE=PRELOCAL_PASS_L3_HOLD
echo 'G05/G06/G07 moving-Goal, crash and physical obstacle acceptance still NOT_RUN.'
