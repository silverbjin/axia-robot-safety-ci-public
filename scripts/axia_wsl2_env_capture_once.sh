#!/usr/bin/env bash
# AXIA Owner WSL2 environment capture. No sudo, no test Goal, no Fault.
# Captures a strict allowlist. Uploads ONLY a JSON profile to PRIVATE instructor
# evidence branch unless --local-only is specified.
set -Eeuo pipefail
umask 077
REPO='silverbjin/axia-robot-safety-instructor'
BRANCH='evidence/wsl2-jazzy-harmonic-profile-20261110'
REMOTE_FILE='docs/environment/wsl2_owner_profile.json'
PUBLIC_REPO='silverbjin/axia-robot-safety-ci-public'
PROFILE_FILE=''
UPLOAD=1

if [[ $# -eq 1 && "$1" == '--local-only' ]]; then
  UPLOAD=0
elif [[ $# -ne 0 ]]; then
  echo 'Usage: axia_wsl2_env_capture_once.sh [--local-only]' >&2
  exit 2
fi
if [[ ! "$AXIA_PUBLIC_SHA" =~ ^[0-9a-f]{40}$ ]]; then
  echo 'AXIA_ENV_BLOCKED: set exact AXIA_PUBLIC_SHA from verified public CI commit' >&2
  exit 2
fi
grep -qiE 'microsoft|wsl' /proc/sys/kernel/osrelease || {
  echo 'AXIA_ENV_BLOCKED_NOT_WSL2' >&2
  exit 2
}
[[ -f /opt/ros/jazzy/setup.bash ]] || {
  echo 'AXIA_ENV_BLOCKED_ROS_JAZZY_ABSENT' >&2
  exit 2
}
for tool in curl python3 sha256sum; do
  command -v "$tool" >/dev/null || {
    echo "AXIA_ENV_BLOCKED_MISSING_TOOL=$tool" >&2
    exit 2
  }
done
# ROS source is read-only and sets path/discovery environment for accurate
# ament package hash collection.
set +u
source /opt/ros/jazzy/setup.bash
set -u

OUT="$HOME/axia_env_evidence/owner-$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$OUT"
chmod 700 "$OUT"
PROFILE_FILE="$OUT/wsl2_owner_profile.json"
TMP="$(mktemp -d)"
trap 'rm -rf -- "$TMP"' EXIT
URL="https://raw.githubusercontent.com/$PUBLIC_REPO/$AXIA_PUBLIC_SHA/tools/axia_env_profile.py"
curl -fL --retry 3 -sS "$URL" -o "$TMP/axia_env_profile.py"
python3 -m py_compile "$TMP/axia_env_profile.py"
python3 "$TMP/axia_env_profile.py" --output "$PROFILE_FILE" --require-wsl2
python3 -m json.tool "$PROFILE_FILE" >/dev/null
sha256sum "$PROFILE_FILE" > "$PROFILE_FILE.sha256"
printf 'AXIA_WSL2_ENV_LOCAL_PROFILE=%s\n' "$PROFILE_FILE"
printf 'AXIA_WSL2_ENV_LOCAL_SHA256=%s\n' "$(sha256sum "$PROFILE_FILE" | cut -d' ' -f1)"
if [[ "$UPLOAD" -eq 0 ]]; then
  echo 'AXIA_WSL2_ENV_LOCAL_ONLY_PRIVATE_UPLOAD_NOT_RUN'
  exit 0
fi

command -v gh >/dev/null || {
  echo "AXIA_ENV_PRIVATE_UPLOAD_BLOCKED: gh missing; attach local JSON profile instead" >&2
  exit 3
}
gh auth status >/dev/null 2>&1 || {
  echo "AXIA_ENV_PRIVATE_UPLOAD_BLOCKED: gh auth status failed; attach local JSON" >&2
  exit 3
}
gh api "repos/$REPO/git/ref/heads/$BRANCH" -q '.object.sha' >/dev/null || {
  echo "AXIA_ENV_PRIVATE_UPLOAD_BLOCKED: private evidence branch not accessible" >&2
  exit 3
}
EXISTING="$(gh api "repos/$REPO/contents/$REMOTE_FILE?ref=$BRANCH" -q .sha 2>/dev/null || true)"
python3 - "$PROFILE_FILE" "$TMP/request.json" "$BRANCH" "$EXISTING" <<'PY'
import base64
import json
from pathlib import Path
import sys
source, destination, branch, old_sha = sys.argv[1:]
payload = {
    "message": "evidence(ci): sanitized WSL2 Jazzy/Harmonic owner user-space profile",
    "branch": branch,
    "content": base64.b64encode(Path(source).read_bytes()).decode("ascii"),
}
if old_sha:
    payload["sha"] = old_sha
Path(destination).write_text(json.dumps(payload), encoding="utf-8")
PY
chmod 600 "$TMP/request.json"
if gh api --method PUT "repos/$REPO/contents/$REMOTE_FILE" \
  --input "$TMP/request.json" >/dev/null; then
  echo 'AXIA_ENV_PRIVATE_UPLOAD_SUCCESS'
  printf 'AXIA_ENV_PRIVATE_REPO=%s\nAXIA_ENV_PRIVATE_BRANCH=%s\nAXIA_ENV_PRIVATE_PATH=%s\n' \
    "$REPO" "$BRANCH" "$REMOTE_FILE"
  echo 'AXIA_ENV_NEXT=CI profile comparator must verify user-space parity; no ROS/Gazebo runtime acceptance yet'
else
  echo "AXIA_ENV_PRIVATE_UPLOAD_BLOCKED: report remains on WSL2 local disk; attach JSON" >&2
  exit 3
fi
