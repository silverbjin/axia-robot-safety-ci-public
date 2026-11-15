#!/usr/bin/env bash
# Read-only owner field diagnosis; NEVER a goal or an attempt reservation.
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"
GATE="$ROOT/d06/acceptance/g07_unified_final_owner_ci_gate_v2.json"
FIXTURE="$ROOT/d06/tests/fixtures/g07_field_first_guard_158ms_sanitized_v1.json"
SOURCE="bc270e28620c1909fcb34669e6036504b5cae951"
RUN=43693480829
if [[ "$#" -eq 1 && "$1" == "--self-check" ]];then
  bash -n "$0"
  python3 - "$ROOT/d06/live/g07_owner_field_preflight_v3.py" <<'PY'
import ast, pathlib, sys
ast.parse(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
PY
  echo AXIA_G07_OWNER_FIELD_PREFLIGHT_STATIC_OK_NO_ROS_NO_GOAL
  exit 0
fi
[[ "$#" -eq 0 ]] || { echo AXIA_G07_OWNER_FIELD_PREFLIGHT_UNKNOWN_ARGS_NO_GOAL >&2;exit 3; }
exec python3 "$ROOT/d06/live/g07_owner_field_preflight_v3.py" \
  --home "$HOME" --gate "$GATE" --private-sha "$SOURCE" \
  --ci-run "$RUN" --field-fixture "$FIXTURE"
