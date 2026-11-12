#!/usr/bin/env bash
# D04 instructor add-on: PUBLIC student CPU YOLO one-image inference + visual report.
# Independent of P1/Gazebo; no proprietary instructor source or auto GUI respawn.
set -Eeuo pipefail
umask 077

MODE="${1:---run}"
[[ $# -le 1 ]] || { echo "D04_SINGLE_IMAGE_USAGE=--run|--doctor|--self-check"; exit 2; }
case "$MODE" in --run|--doctor|--self-check) ;; *)
  echo "D04_SINGLE_IMAGE_USAGE=--run|--doctor|--self-check"; exit 2 ;; esac

STUDENT_SHA='6012336bef42be7f9d74cc9632baea41db555ae9'
REPORT_PIN='7254cd8bd9fa505cd68faa2d933014825bb2e103'
REPORT_BLOB='REPLACE_REPORT_GIT_BLOB_AFTER_REVIEW'
STUDENT_INFER_BLOB='9eb5fb41ea3836da5bade7fcdb3bce99969fc212'
STUDENT_RUNNER_BLOB='805542535934f14295d74bcd0ff37ffe18ce3c7c'
PUBLIC_ORIGIN='silverbjin/axia-robot-safety-ci-public'
STUDENT_ORIGIN='silverbjin/axia-robot-safety-student'
CACHE="${AXIA_D04_STUDENT_CACHE:-$HOME/.cache/axia/d04_student_yolo}"
RESULTS="${AXIA_D04_INSTRUCTOR_SINGLE_IMAGE_RESULTS:-$HOME/axia_d04_instructor_single_image_results}"
VENV="${AXIA_D04_STUDENT_VENV:-$HOME/.venvs/axia-d04-student-yolo}"
PYTHON="${AXIA_D04_STUDENT_PYTHON:-$VENV/bin/python}"
CODE_DIR="$HOME/.cache/axia/d04_instructor_single_image/src_${STUDENT_SHA}"
REPORT_FILE="$HOME/.cache/axia/d04_instructor_single_image/report_${REPORT_PIN}.py"
STUDENT_DEMO="$CODE_DIR/block_B/day04/yolo_single_image_demo.py"
STUDENT_RUNNER="$CODE_DIR/block_B/day04/run_teacher_yolo_demo_once.sh"

if [[ "$MODE" == --self-check ]]; then
  echo "D04_SINGLE_IMAGE_STATIC_PASS NO_ROS NO_GAZEBO"
  echo "D04_SINGLE_IMAGE_PUBLIC_STUDENT_SHA=$STUDENT_SHA"
  echo "D04_SINGLE_IMAGE_SAVED_VISUAL=BBOX_CLASS_CONFIDENCE_PNG_HTML"
  echo "D04_SINGLE_IMAGE_NO_GUI_AUTO_REOPEN"
  exit 0
fi
for bin in python3 curl git bash sha256sum; do
  command -v "$bin" >/dev/null || { echo "D04_SINGLE_IMAGE_MISSING_TOOL=$bin"; exit 2; }
done
if [[ "$MODE" == --doctor ]]; then
  local_ready=1
  [[ -x "$PYTHON" ]] && "$PYTHON" -c "from ultralytics import YOLO; from PIL import Image" >/dev/null 2>&1 || local_ready=0
  [[ -s "$CACHE/yolo26n.pt" && -s "$CACHE/bus.jpg" ]] || local_ready=0
  if [[ "$local_ready" == 1 ]]; then
    echo "D04_SINGLE_IMAGE_DOCTOR_PASS=LOCAL_MODEL_AND_PYTHON_CACHED"
  else
    echo "D04_SINGLE_IMAGE_DOCTOR_NEEDS_RUN=OFFICIAL_PUBLIC_ASSETS_OR_CPU_ENV"
  fi
  echo "D04_SINGLE_IMAGE_GAZEBO_ROS=NOT_RUN"
  exit 0
fi

mkdir -p "$CODE_DIR/block_B/day04" "$(dirname "$REPORT_FILE")" "$RESULTS"
fetch_verified() {
  local url="$1" target="$2" blob="$3"
  if [[ -s "$target" && "$(git hash-object "$target")" == "$blob" ]]; then
    return 0
  fi
  curl -fsSL --retry 3 --connect-timeout 15 --max-time 120 \
    "$url" -o "$target.tmp"
  if [[ "$(git hash-object "$target.tmp")" != "$blob" ]]; then
    echo "D04_SINGLE_IMAGE_PUBLIC_SOURCE_HASH_BLOCKED=$target" >&2
    rm -f -- "$target.tmp"
    return 2
  fi
  mv -f -- "$target.tmp" "$target"
}
fetch_verified \
  "https://raw.githubusercontent.com/$STUDENT_ORIGIN/$STUDENT_SHA/block_B/day04/yolo_single_image_demo.py" \
  "$STUDENT_DEMO" "$STUDENT_INFER_BLOB"
fetch_verified \
  "https://raw.githubusercontent.com/$STUDENT_ORIGIN/$STUDENT_SHA/block_B/day04/run_teacher_yolo_demo_once.sh" \
  "$STUDENT_RUNNER" "$STUDENT_RUNNER_BLOB"
fetch_verified \
  "https://raw.githubusercontent.com/$PUBLIC_ORIGIN/$REPORT_PIN/scripts/d04_instructor_single_image_report.py" \
  "$REPORT_FILE" "$REPORT_BLOB"

bash -n "$STUDENT_RUNNER"
python3 -m py_compile "$STUDENT_DEMO" "$REPORT_FILE"
bash "$STUDENT_RUNNER" --self-check | grep -F 'D04_STUDENT_STATIC_PASS'

RUNLOG="$(mktemp "$RESULTS/d04-report-run-XXXXXXXX.log")"
trap 'rm -f -- "$RUNLOG"' EXIT
echo "D04_SINGLE_IMAGE_START: official public bus.jpg + yolo26n.pt CPU model"
# This exact PUBLIC student runner generates real CSV and SHA256 manifest;
# it reuses the existing student venv/model cache if present.
AXIA_D04_STUDENT_CACHE="$CACHE" \
AXIA_D04_STUDENT_RESULTS="$RESULTS" \
AXIA_D04_STUDENT_VENV="$VENV" \
bash "$STUDENT_RUNNER" --run | tee "$RUNLOG"

OUT="$(sed -n 's/^D04_STUDENT_REAL_IMAGE_OUTPUT=//p' "$RUNLOG" | tail -n 1)"
case "$OUT" in "$RESULTS"/teacher_same_code_*) ;; *)
  echo "D04_SINGLE_IMAGE_OUTPUT_NOT_FOUND_OR_NOT_OWNED=$OUT" >&2; exit 2 ;; esac
[[ -f "$OUT/detections.csv" && -f "$OUT/run_manifest.json" ]] || {
  echo "D04_SINGLE_IMAGE_EVIDENCE_INCOMPLETE=$OUT" >&2; exit 2; }

"$PYTHON" "$REPORT_FILE" \
  --image "$CACHE/bus.jpg" --model "$CACHE/yolo26n.pt" --out "$OUT"
echo "D04_SINGLE_IMAGE_VISUAL_INSPECTION=OPEN_FILE_MANUALLY"
echo "D04_SINGLE_IMAGE_RESULTS=$OUT"
echo "D04_SINGLE_IMAGE_INFERENCE_SCOPE=LOCAL_YOLO_CPU_ONLY ROS_GAZEBO_NAV2_SAFETY_NOT_RUN"
