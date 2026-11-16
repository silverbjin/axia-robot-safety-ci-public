#!/usr/bin/env bash
# AXIA G07 field first-failure proof — NO ROS, NO Goal, never clears attempts.
# This is a checked-in read-only subcommand. Fetch only pinned public SHA.
set -Eeuo pipefail
umask 077
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
CHECK="$ROOT/d06/live/g07_cycle18_field_owner_admission_v5.py"
GATE="$ROOT/d06/acceptance/g07_cycle16_owner_ci_gate_v3.json"
FIRST="$ROOT/d06/tests/fixtures/g07_cycle17_wsl2_guard_174ms_rmw_186ms_sanitized.json"
if [[ "${1:-}" == --self-check && $# == 1 ]];then
  [[ -s "$CHECK" && -s "$GATE" && -s "$FIRST" ]] || exit 3
  bash -n "$0"
  python3 - "$CHECK" <<'PY'
import ast,pathlib,sys
ast.parse(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
PY
  echo AXIA_G07_CYCLE18_FIELD_READONLY_STATIC_PASS_NO_ROS_NO_GOAL
  exit 0
fi
[[ $# == 0 ]] || {
  echo AXIA_G07_CYCLE18_FIELD_READONLY_INVALID_ARGS_NO_ROS_NO_GOAL >&2
  exit 3
}
[[ -d "$HOME" && ! -L "$HOME" ]] || {
  echo AXIA_G07_CYCLE18_FIELD_HOME_UNTRUSTED_NO_ROS_NO_GOAL >&2
  exit 3
}
[[ -s "$CHECK" && -s "$GATE" && -s "$FIRST" ]] || {
  echo AXIA_G07_CYCLE18_FIELD_READONLY_SOURCE_MISSING_NO_ROS_NO_GOAL >&2
  exit 3
}
echo AXIA_G07_CYCLE18_FIELD_READONLY_BEFORE_GUI_ROS_GOAL
exec python3 "$CHECK" --home "$HOME" --ci-gate "$GATE" --field-evidence "$FIRST"
