#!/usr/bin/env bash
# Inspect exactly ONE pre-existing failed Owner WSL2 G07 run, never drive.
# No ROS, Gazebo, Goal, cmd_vel, private upload or lock modification.
set -Eeuo pipefail
umask 077
readonly PUBLIC_SHA="3b9ff7cb06805b297a204d7bd8ebe22d4d025508"
readonly ORIGINAL_SHA="c2557e3269c5cb3f56d1842f8d39bcdc5d6ab0055180911fc492a5bc84a1f672"
readonly OWNER_RUN="p2-l3-owner-A9IwJNZJ"
readonly REPO="silverbjin/axia-robot-safety-ci-public"
if [[ "${1:-}" == --self-check && $# -eq 1 ]];then
  bash -n "$0"
  [[ "$PUBLIC_SHA" =~ ^[a-f0-9]{40}$ &&
     "$ORIGINAL_SHA" =~ ^[a-f0-9]{64}$ ]] || exit 3
  echo AXIA_G07_CYCLE19_OWNER_READONLY_STATIC_PASS_NO_ROS_NO_GOAL
  exit 0
fi
[[ $# -eq 0 ]] || {
  echo AXIA_G07_CYCLE19_UNSUPPORTED_ARGS_NO_ROS_NO_GOAL >&2;exit 3;
}
for program in python3 curl sha256sum mktemp;do
  command -v "$program" >/dev/null || {
    echo "AXIA_G07_CYCLE19_MISSING_COMMAND=$program NO_ROS_NO_GOAL" >&2;exit 3;
  }
done
[[ -d "$HOME" && "$HOME" != / && ! -L "$HOME" ]] || {
  echo AXIA_G07_CYCLE19_OWNER_HOME_UNTRUSTED_NO_ROS_NO_GOAL >&2;exit 3;
}
ORIGINAL="$HOME/axia_p2_private_evidence/${OWNER_RUN}.tar.gz"
CUSTODY="$HOME/.axia_p4_g11_session_custody/objects/c2/$ORIGINAL_SHA"
# Original TAR and byte-identical G11 object are the only two candidate
# sources; no search of another Goal, no mutable branch, no raw upload.
if [[ -f "$ORIGINAL" && ! -L "$ORIGINAL" ]];then
  ARCHIVE="$ORIGINAL"
elif [[ -f "$CUSTODY" && ! -L "$CUSTODY" ]];then
  ARCHIVE="$CUSTODY"
else
  echo AXIA_G07_CYCLE19_ORIGINAL_OWNER_ARCHIVE_NOT_PRESENT_NO_ROS_NO_GOAL >&2
  echo "Expected first path: $ORIGINAL" >&2
  echo "Expected retained copy: $CUSTODY" >&2
  echo AXIA_MVP_DEMO_ACCEPTED=HOLD
  exit 3
fi
ACTUAL="$(sha256sum -- "$ARCHIVE" | cut -d' ' -f1)"
[[ "$ACTUAL" == "$ORIGINAL_SHA" ]] || {
  echo AXIA_G07_CYCLE19_ORIGINAL_ARCHIVE_SHA256_MISMATCH_NO_ROS_NO_GOAL >&2
  echo AXIA_MVP_DEMO_ACCEPTED=HOLD
  exit 3
}
echo AXIA_G07_CYCLE19_ORIGINAL_SHA256_VERIFIED_EXISTING_RUN_NO_ROS_NO_GOAL
TEMP="$(mktemp)"
cleanup(){
  rc=$?
  trap - EXIT INT TERM
  if [[ -f "$TEMP" ]];then rm -f -- "$TEMP";fi
  exit "$rc"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
curl -fL --retry 3 -sS \
  "https://raw.githubusercontent.com/$REPO/$PUBLIC_SHA/d06/live/g07_cycle19_first_cm_archive_readonly.py" \
  -o "$TEMP"
python3 -m py_compile "$TEMP" 2>/dev/null || {
  # py_compile can reject temporary filenames without .py extension; use
  # syntax checking through Python ast in a process not importing ROS.
  python3 - "$TEMP" <<'PY'
import ast,sys
with open(sys.argv[1],encoding="utf-8") as f: ast.parse(f.read())
PY
}
DIAG_DIR="$HOME/.axia_g07_first_gap_readonly"
[[ ! -L "$DIAG_DIR" && ( ! -e "$DIAG_DIR" || -d "$DIAG_DIR" ) ]] || {
  echo AXIA_G07_CYCLE19_DIAGNOSTIC_DIRECTORY_UNTRUSTED_NO_ROS_NO_GOAL >&2
  exit 3
}
mkdir -p -m 700 -- "$DIAG_DIR"
chmod 700 "$DIAG_DIR"
OUT="$(mktemp "$DIAG_DIR/g07-first-cm-gap-XXXXXXXX.json")"
# The Python inspector uses open(mode='x') to prohibit file overwrite.
# Reserve a unique path and immediately remove ONLY that empty output file.
rm -f -- "$OUT"
python3 "$TEMP" --archive "$ARCHIVE" --expected-sha256 "$ORIGINAL_SHA" --output "$OUT"
[[ -s "$OUT" ]] || {
  echo AXIA_G07_CYCLE19_SANITIZED_OUTPUT_MISSING_HOLD >&2;exit 3;
}
echo "AXIA_G07_CYCLE19_OWNER_UPLOAD_ONLY_THIS_SANITIZED_JSON=$OUT"
echo "AXIA_G07_CYCLE19_NO_NEW_GOAL_RUN: archive and all prior locks unchanged"
echo AXIA_MVP_DEMO_ACCEPTED=HOLD
