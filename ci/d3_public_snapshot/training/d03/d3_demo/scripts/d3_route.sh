#!/usr/bin/env bash
# Persist instructor-verified Gazebo world coordinates ONCE for D3 preview and live.
set -Eeuo pipefail
[[ $# -eq 5 ]] || { echo 'Usage: bash d3_route.sh WORLD START_X START_Y END_X END_Y' >&2; exit 64; }
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
[[ -f "$ROOT/install/setup.bash" ]] || { echo '[BLOCKED] Build+source D3 first' >&2; exit 2; }
set +u
source /opt/ros/jazzy/setup.bash
source "$ROOT/install/setup.bash"
set -u
python3 - "$@" <<'PY'
from axia_d3_demo.scenario import validate_path
import sys
validate_path(sys.argv[1], (sys.argv[2],sys.argv[3]), (sys.argv[4],sys.argv[5]))
print('[PASS] Gazebo proxy path validated for format, 0.3..3.0m')
PY
OUT="$HOME/axia_d3_classroom/d3_route.env"
mkdir -p "$(dirname "$OUT")"
umask 077
{
  printf 'export D3_WORLD=%q\n' "$1"
  printf 'export D3_START_X=%q\n' "$2"
  printf 'export D3_START_Y=%q\n' "$3"
  printf 'export D3_END_X=%q\n' "$4"
  printf 'export D3_END_Y=%q\n' "$5"
} > "$OUT"
echo "[SAVED] $OUT"
echo '[NOTE] Coordinates must be inspected visually against YOUR Gazebo world; format check does not establish a collision-free route.'