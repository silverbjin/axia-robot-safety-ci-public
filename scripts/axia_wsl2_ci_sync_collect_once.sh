#!/usr/bin/env bash
# AXIA WSL2/Jazzy/Harmonic environment inventory: READ ONLY, NO ROS GOAL.
# One shot; results remain under private $HOME. No GitHub upload, no sudo.
set -Eeuo pipefail
umask 077

readonly COLLECTOR_REF="b27df09529daab4e67d6c3486f8b7e0cf2c6b123"
readonly REPO="silverbjin/axia-robot-safety-ci-public"

if [[ "${1:-}" == "--self-check" ]]; then
  [[ $# -eq 1 && "$COLLECTOR_REF" =~ ^[a-f0-9]{40}$ ]] || exit 2
  echo "AXIA_WSL2_CI_SYNC_WRAPPER_STATIC_OK NO_NETWORK_NO_GOAL"
  exit 0
fi
[[ $# -eq 0 ]] || { echo "AXIA_WSL2_CI_SYNC_BLOCKED_UNEXPECTED_ARGS" >&2; exit 2; }
for command_name in curl python3 mktemp sha256sum; do
  command -v "$command_name" >/dev/null || {
    echo "AXIA_WSL2_CI_SYNC_BLOCKED_MISSING_$command_name" >&2
    exit 2
  }
done
[[ -f /opt/ros/jazzy/setup.bash ]] || {
  echo "AXIA_WSL2_CI_SYNC_BLOCKED_ROS_JAZZY_MISSING" >&2
  exit 2
}
# Read-only ROS environment activation in THIS subshell; no system mutation.
set +u
source /opt/ros/jazzy/setup.bash
set -u

readonly BASE="$HOME/.axia_ci_sync_private"
[[ ! -L "$BASE" ]] || {
  echo "AXIA_WSL2_CI_SYNC_BLOCKED_SYMLINK_BASE" >&2
  exit 2
}
mkdir -p -m 700 -- "$BASE"
chmod 700 -- "$BASE"
readonly RUN_DIR="$(mktemp -d "$BASE/wsl2-env-$(date -u +%Y%m%dT%H%M%SZ)-XXXXXXXX")"
readonly COLLECTOR="$(mktemp)"
cleanup() { rm -f -- "$COLLECTOR"; }
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

curl --fail --location --silent --show-error --retry 3 \
  "https://raw.githubusercontent.com/$REPO/$COLLECTOR_REF/tools/axia_wsl2_ci_sync_collect.py" \
  --output "$COLLECTOR"
[[ -s "$COLLECTOR" ]] || {
  echo "AXIA_WSL2_CI_SYNC_BLOCKED_EMPTY_COLLECTOR" >&2
  exit 2
}
python3 "$COLLECTOR" --mode owner --out-dir "$RUN_DIR"
(
  cd "$RUN_DIR"
  sha256sum -c SHA256SUMS
)
echo "AXIA_WSL2_CI_SYNC_READ_ONLY_COMPLETE"
echo "REPORT=$RUN_DIR/owner_summary.json"
echo "FULL_PROFILE_PRIVATE=$RUN_DIR/owner_profile.json"
echo "SHA256SUMS=$RUN_DIR/SHA256SUMS"
echo "AXIA_WSL2_CI_SYNC_NO_UPLOAD_NO_GOAL_NO_FAULT"
