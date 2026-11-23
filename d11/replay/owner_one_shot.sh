#!/usr/bin/env bash
# AXIA D11 private-owner single run: immutable public builder, local private records ONLY.
# NO AE inference, ROS, Gazebo, cmd_vel, SW Stop or certified E-Stop.
set -Eeuo pipefail
if [[ "${1:-}" == "--self-check" ]]; then
  bash -n "$0"
  echo D11_REPLAY_PUBLIC_OWNER_SCRIPT_SELF_CHECK_PASS_ROS_GAZEBO_NOT_RUN
  exit 0
fi
if [[ $# -ne 0 ]]; then echo "Usage: bash owner_one_shot.sh [--self-check]" >&2;exit 2;fi
PIN="${AXIA_D11_REPLAY_PUBLIC_SHA:-6429a3e221c139a8010689272a0cc763c700e780}"
if [[ ! "$PIN" =~ ^[a-f0-9]{40}$ ]]; then echo D11_PUBLIC_SHA_INVALID >&2;exit 2;fi
ROOT="${AXIA_D11_INSTRUCTOR_BLOCK_C:-}"
DEFAULT_CLONE="$HOME/axia_d11_course/axia-robot-safety-instructor"
if [[ -z "$ROOT" ]]; then
  for path in \
    "$DEFAULT_CLONE/training/block_C" \
    "$HOME/axia_d10_course/axia-robot-safety-instructor/training/block_C" \
    "$HOME/axia_d09_course/axia-robot-safety-instructor/training/block_C";do
    if [[ -f "$path/day11/reference_outputs/ae_scores_test.csv" ]]; then ROOT="$path";break;fi
  done
fi
if [[ -z "$ROOT" ]];then
  mkdir -p "$(dirname "$DEFAULT_CLONE")"
  if [[ ! -e "$DEFAULT_CLONE" ]];then
    echo D11_PRIVATE_CLONE_REQUIRED_EXISTING_GITHUB_AUTH
    git clone https://github.com/silverbjin/axia-robot-safety-instructor.git "$DEFAULT_CLONE" || {
      echo D11_PRIVATE_AUTH_HOLD >&2;exit 3;
    }
  fi
  ROOT="$DEFAULT_CLONE/training/block_C"
fi
if [[ ! -d "$ROOT" ]];then echo "D11_PRIVATE_SOURCE_NOT_FOUND $ROOT" >&2;exit 3;fi
for rel in "fixtures/test_mixed.csv" "fixtures/scenario_manifest.json" \
  "day10/reference_outputs/if_scores_test.csv" \
  "day11/reference_outputs/ae_scores_test.csv" "day11/reference_outputs/ae_metrics.json";do
  if [[ ! -s "$ROOT/$rel" ]];then echo "D11_PRIVATE_SOURCE_NOT_FOUND $rel" >&2;exit 3;fi
done
OUT="${AXIA_D11_REPLAY_OUT:-$HOME/axia_d11_course/AXIA_D11_LIVE_REPLAY_INSTRUCTOR.html}"
if [[ "${OUT##*.}" != "html" ]];then echo D11_OUT_MUST_BE_HTML >&2;exit 2;fi
mkdir -p "$(dirname "$OUT")"
OUT="$(cd "$(dirname "$OUT")" && pwd -P)/$(basename "$OUT")"
LOG_DIR="$(dirname "$OUT")/d11_replay_evidence"
mkdir -p "$LOG_DIR"
WORK="$(mktemp -d)"
trap 'rm -rf -- "$WORK"' EXIT
mkdir -p "$WORK/d10/replay" "$WORK/d11/replay"
BASE="https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public/$PIN"
for file in "d10/replay/build_replay.py" "d11/replay/build_replay.py" "d11/replay/replay_template.html";do
  curl -fLsS --retry 3 --max-time 90 "$BASE/$file" -o "$WORK/$file" || {
    echo "D11_PUBLIC_DOWNLOAD_HOLD $file" >&2;exit 4;
  }
done
python3 -m py_compile "$WORK/d10/replay/build_replay.py" "$WORK/d11/replay/build_replay.py"
{
  echo D11_REPLAY_STAGE=PRIVATE_REFERENCE_VALIDATION
  echo "D11_REPLAY_PUBLIC_CODE_SHA=$PIN"
  echo "D11_REPLAY_OWNER_PYTHON=$(python3 --version)"
  echo "D11_REPLAY_INSTRUCTOR_SHA=$(git -C "$ROOT" rev-parse HEAD 2>/dev/null || echo UNKNOWN)"
  sha256sum "$ROOT/fixtures/test_mixed.csv" \
    "$ROOT/day10/reference_outputs/if_scores_test.csv" \
    "$ROOT/day11/reference_outputs/ae_scores_test.csv"
  python3 "$WORK/d11/replay/build_replay.py" \
    --raw "$ROOT/fixtures/test_mixed.csv" \
    --manifest "$ROOT/fixtures/scenario_manifest.json" \
    --if-scores "$ROOT/day10/reference_outputs/if_scores_test.csv" \
    --ae-scores "$ROOT/day11/reference_outputs/ae_scores_test.csv" \
    --ae-metrics "$ROOT/day11/reference_outputs/ae_metrics.json" \
    --if-source INSTRUCTOR_C03_REFERENCE \
    --ae-source INSTRUCTOR_C04_REFERENCE \
    --expect-baseline --out "$OUT"
  sha256sum "$OUT"
  echo D11_REPLAY_OWNER_HTML_BUILT_AND_REFERENCE_VALIDATED
  echo D11_REPLAY_OWNER_BROWSER_NOT_VERIFIED
} 2>&1 | tee "$LOG_DIR/build.log"
{
  echo "PUBLIC_SHA=$PIN"
  echo "OUT=$OUT"
  echo "SOURCE=$ROOT"
  echo ROS_ACTUAL=false
  echo GAZEBO_ACTUAL=false
  echo MODEL_INFERENCE=false
  echo WINDOW_END_TIME_ONLY_NOT_STOP_LATENCY=true
} > "$LOG_DIR/manifest.txt"
tar -czf "$LOG_DIR/d11_minimal_evidence.tar.gz" -C "$LOG_DIR" build.log manifest.txt
echo "D11_REPLAY_OWNER_GENERATED=$OUT"
echo "D11_REPLAY_OWNER_LOGS=$LOG_DIR/d11_minimal_evidence.tar.gz"
if command -v wslpath >/dev/null 2>&1 && command -v explorer.exe >/dev/null 2>&1 \
   && [[ "${AXIA_D11_AUTO_OPEN:-1}" == 1 ]];then
   explorer.exe "$(wslpath -w "$OUT")" >/dev/null 2>&1 || echo D11_BROWSER_OPEN_HOLD_OPEN_HTML_MANUALLY
else
   echo D11_BROWSER_MANUAL_OPEN_REQUIRED_OPEN_HTML_IN_WINDOWS_EDGE
fi
