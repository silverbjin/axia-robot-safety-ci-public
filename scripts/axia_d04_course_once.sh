#!/usr/bin/env bash
# AXIA D04 teaching-only preflight / optional locally licensed image inference.
# Run from ANY working directory, including $HOME. No ROS, Gazebo, Goal, Fault or cmd_vel.
set -Eeuo pipefail
umask 077

usage() {
  cat <<'HELP'
Usage: bash axia_d04_course_once.sh --doctor|--image [options]

  --doctor              Check all prerequisites; exit 2 if incomplete.
  --image               Run EXISTING private instructor single-image .pt demo
                        only when all prerequisites are satisfied.
  --instructor DIR      Private instructor checkout root.
                        Default: $HOME/axia_d04_classroom/instructor
  --model FILE          Existing licensed .pt model; no auto download.
                        Default: $HOME/axia_licensed_assets/yolo_cached.pt
  --image-file FILE     Existing licensed local photograph (.jpg/.png).
                        Default: $HOME/axia_licensed_assets/person_scene.jpg
  --out DIR             New output directory; default under ~/axia_d04_results.
  --help                Print this message.

Environment: AXIA_D04_PYTHON may point to an existing Python environment with
Ultralytics installed (e.g. "$HOME/.venvs/axia-d04/bin/python").
Never treats a stub/fixture result as real YOLO inference or ROS/Gazebo success.
HELP
}

MODE=""
PYTHON="\${AXIA_D04_PYTHON:-python3}"
INSTRUCTOR="\${AXIA_D04_INSTRUCTOR_ROOT:-$HOME/axia_d04_classroom/instructor}"
MODEL="\${AXIA_D04_MODEL:-$HOME/axia_licensed_assets/yolo_cached.pt}"
PHOTO="\${AXIA_D04_IMAGE:-$HOME/axia_licensed_assets/person_scene.jpg}"
OUT="\${AXIA_D04_OUT:-$HOME/axia_d04_results/d04_single_$(date +%Y%m%d_%H%M%S)_$$}"

while (($# > 0)); do
  case "$1" in
    --doctor|--image)
      [[ -z "$MODE" ]] || { echo "D04_USAGE_ERROR: mode already selected" >&2; exit 2; }
      MODE="$1"; shift ;;
    --instructor|--model|--image-file|--out)
      (($# >= 2)) || { echo "D04_USAGE_ERROR: missing value for $1" >&2; exit 2; }
      case "$1" in
        --instructor) INSTRUCTOR="$2" ;;
        --model) MODEL="$2" ;;
        --image-file) PHOTO="$2" ;;
        --out) OUT="$2" ;;
      esac
      shift 2 ;;
    --help|-h) usage; exit 0 ;;
    *) echo "D04_USAGE_ERROR: unknown argument $1" >&2; usage >&2; exit 2 ;;
  esac
done
[[ -n "$MODE" ]] || { echo "D04_USAGE_ERROR: select --doctor or --image" >&2; usage >&2; exit 2; }

[[ "$INSTRUCTOR" == /* && "$MODEL" == /* && "$PHOTO" == /* && "$OUT" == /* ]] || {
  echo "D04_ABSOLUTE_PATH_REQUIRED: instructor/model/image/output must be absolute" >&2
  exit 2
}

INSTRUCTOR_SCRIPT="$INSTRUCTOR/training/block_B/instructor/yolo_single_image_demo.py"
bad=0
if [[ -f "$MODEL" && ! -L "$MODEL" && "$MODEL" == *.pt ]]; then
  echo "D04_MODEL_FOUND=$MODEL"
else
  echo "D04_MODEL_MISSING=$MODEL"; bad=1
fi
if [[ -f "$PHOTO" && ! -L "$PHOTO" && ( "$PHOTO" == *.jpg || "$PHOTO" == *.jpeg || "$PHOTO" == *.png ) ]]; then
  echo "D04_IMAGE_FOUND=$PHOTO"
else
  echo "D04_IMAGE_MISSING=$PHOTO"; bad=1
fi
if [[ -f "$INSTRUCTOR_SCRIPT" && ! -L "$INSTRUCTOR_SCRIPT" ]]; then
  echo "D04_INSTRUCTOR_SCRIPT_FOUND=$INSTRUCTOR_SCRIPT"
else
  echo "D04_INSTRUCTOR_SCRIPT_MISSING=$INSTRUCTOR_SCRIPT"; bad=1
fi
if command -v "$PYTHON" >/dev/null 2>&1 && "$PYTHON" -c 'import ultralytics' >/dev/null 2>&1; then
  echo "D04_ULTRALYTICS_FOUND_PYTHON=$PYTHON"
else
  echo "D04_ULTRALYTICS_MISSING_PYTHON=$PYTHON"
  bad=1
fi

if ((bad > 0)); then
  echo "D04_IMAGE_PREFLIGHT_BLOCKED: correct all reported failures before selecting --image"
  echo "D04_FIX_PATH: use --instructor /ABSOLUTE/PATH/TO/axia-robot-safety-instructor"
  echo "D04_FIX_PYTHON: make a Python venv; run python -m pip install ultralytics"
  echo "D04_FIX_ASSETS: explicitly prepare licensed local .pt weights and image; no automatic downloads"
  echo "D04_ALTERNATIVE: students run the independent public CSV/pytest lab without YOLO"
  exit 2
fi

if [[ "$MODE" == "--doctor" ]]; then
  echo "D04_IMAGE_DOCTOR_PASS: prerequisites present; actual inference NOT_RUN"
  exit 0
fi

if [[ -e "$OUT" || -L "$OUT" ]]; then
  echo "D04_OUTPUT_ALREADY_EXISTS=$OUT" >&2
  exit 2
fi
mkdir -p "$(dirname "$OUT")"

"$PYTHON" "$INSTRUCTOR_SCRIPT" --model "$MODEL" --image "$PHOTO" --out "$OUT"
if [[ ! -f "$OUT/detections.csv" || ! -f "$OUT/run_manifest.json" ]]; then
  echo "D04_IMAGE_INCOMPLETE_OUTPUT=$OUT" >&2
  exit 3
fi
echo "D04_IMAGE_SCRIPT_DISPATCH_OK"
echo "D04_IMAGE_OUTPUT=$OUT"
echo "D04_ROS_VERIFIED=false D04_GAZEBO_VERIFIED=false D04_SAFETY_CERTIFIED=false"
