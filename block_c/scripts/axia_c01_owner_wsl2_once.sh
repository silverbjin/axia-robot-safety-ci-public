#!/usr/bin/env bash
# AXIA C-01 student-only Owner WSL2 single-entry, Python L0 / no ROS / no motor.
# Download this file from a fixed, reviewed public CI git SHA.
set -Eeuo pipefail
umask 077
MODE="${1:---run}"
[[ "$#" -le 1 ]] || { echo C01_BOOTSTRAP_USAGE_ERROR >&2; exit 2; }
case "$MODE" in --self-check|--run) ;; *) echo C01_BOOTSTRAP_USAGE_ERROR >&2; exit 2 ;; esac
PINNED_STUDENT_SHA=766ef987fc0357fdf171fa0926dbef65c6aae972
STUDENT_BRANCH=feat/block-c-c01-synthetic-20261115
STUDENT_URL=https://github.com/silverbjin/axia-robot-safety-student.git
if [[ "$MODE" == --self-check ]]; then
  bash -n "${BASH_SOURCE[0]}"
  echo "C01_BOOTSTRAP_SELF_CHECK_PASS pinned_student=$PINNED_STUDENT_SHA NO_ROS_NO_GOAL"
  exit 0
fi
for cmd in python3 git; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "C01_ENV_BLOCKED_MISSING_COMMAND=$cmd" >&2; exit 2
  fi
done
PY_VERSION="$(python3 -c 'import sys;print(".".join(str(x) for x in sys.version_info[:3]))')"
if ! python3 -c 'import sys;sys.exit(0 if sys.version_info[:2] == (3,12) else 2)'; then
  echo "C01_ENV_DIFF_BLOCKED expected_python=3.12 actual=$PY_VERSION" >&2; exit 2
fi
BASE="${AXIA_C01_OWNER_ROOT:-${HOME:?}/axia_c01_owner_evidence}"
if [[ -L "$BASE" ]]; then echo C01_ENV_BLOCKED_SYMLINK_WORKROOT >&2; exit 2; fi
mkdir -p -- "$BASE"
RUN="$(mktemp -d "$BASE/run-XXXXXXXX")"
mkdir -p "$RUN/evidence"
printf 'C01_OWNER_RUN_DIR=%s\nC01_EXPECTED_SOURCE_SHA=%s\n' "$RUN" "$PINNED_STUDENT_SHA"
if [[ -n "${AXIA_C01_SOURCE_DIR:-}" ]]; then
  SOURCE="${AXIA_C01_SOURCE_DIR}"
  [[ -d "$SOURCE/.git" ]] || { echo C01_SOURCE_NOT_GIT >&2; exit 2; }
else
  SOURCE="$RUN/student"
  if ! GIT_TERMINAL_PROMPT=0 git clone --quiet --depth 1 --branch "$STUDENT_BRANCH" "$STUDENT_URL" "$SOURCE" >"$RUN/git.stdout.log" 2>"$RUN/git.stderr.log"; then
    echo C01_GIT_CLONE_BLOCKED >&2; cat "$RUN/git.stderr.log" >&2; exit 2
  fi
  # A teaching branch may advance to C-06. Rehydrate the immutable C-01
  # reviewed commit instead of expecting its SHA to equal the moving branch HEAD.
  if ! GIT_TERMINAL_PROMPT=0 git -C "$SOURCE" fetch --quiet --depth 1 origin "$PINNED_STUDENT_SHA"        >"$RUN/pinned_git.stdout.log" 2>"$RUN/pinned_git.stderr.log"; then
    echo C01_PINNED_COMMIT_FETCH_BLOCKED >&2; cat "$RUN/pinned_git.stderr.log" >&2; exit 2
  fi
  if ! git -C "$SOURCE" checkout --quiet --detach "$PINNED_STUDENT_SHA"        >"$RUN/pinned_checkout.stdout.log" 2>"$RUN/pinned_checkout.stderr.log"; then
    echo C01_PINNED_COMMIT_CHECKOUT_BLOCKED >&2; cat "$RUN/pinned_checkout.stderr.log" >&2; exit 2
  fi
fi
ACTUAL="$(git -C "$SOURCE" rev-parse HEAD 2>/dev/null || true)"
if [[ "$ACTUAL" != "$PINNED_STUDENT_SHA" ]]; then
  echo "C01_SOURCE_SHA_MISMATCH expected=$PINNED_STUDENT_SHA actual=$ACTUAL" >&2; exit 2
fi
[[ -s "$SOURCE/block_C/scripts/c01_fixture_once.sh" ]] || { echo C01_SOURCE_RUNNER_MISSING >&2; exit 2; }
# Use a matching existing pytest; otherwise isolate Python dependencies in this run only.
if ! python3 -c 'import importlib.metadata as m;sys_ok=(m.version("pytest")=="8.3.5");raise SystemExit(0 if sys_ok else 1)' 2>/dev/null; then
  if ! python3 -m venv "$RUN/venv" >"$RUN/venv.stdout.log" 2>"$RUN/venv.stderr.log"; then
    echo C01_ENV_BLOCKED_VENV_MISSING >&2; cat "$RUN/venv.stderr.log" >&2; exit 2
  fi
  if ! "$RUN/venv/bin/python3" -m pip install --disable-pip-version-check --quiet pytest==8.3.5 >"$RUN/pip.stdout.log" 2>"$RUN/pip.stderr.log"; then
    echo C01_ENV_BLOCKED_PYTEST_INSTALL >&2; cat "$RUN/pip.stderr.log" >&2; exit 2
  fi
  export PATH="$RUN/venv/bin:$PATH"
fi
export AXIA_C01_EVIDENCE_DIR="$RUN/evidence"
if ! bash "$SOURCE/block_C/scripts/c01_fixture_once.sh" --check >"$RUN/runner.stdout.log" 2>"$RUN/runner.stderr.log"; then
  echo C01_OWNER_PYTHON_L0_FAIL >&2
  cat "$RUN/runner.stdout.log" >&2; cat "$RUN/runner.stderr.log" >&2
  exit 1
fi
if ! python3 - "$RUN/evidence/verdict.json" "$PINNED_STUDENT_SHA" <<'PY'
import json, sys
from pathlib import Path
report = json.loads(Path(sys.argv[1]).read_text())
assert report['status'] == 'PASS' and report['level'] == 'PYTHON_L0'
assert report['source_sha'] == sys.argv[2]
assert report['rows'] == 4599 and report['traces'] == 46
assert report['gazebo_actual'] is False and report['ros_actual'] is False
assert report['owner_wsl2_verified'] is False  # CI must not fabricate Owner result
PY
then
  echo C01_OWNER_VERDICT_CONTRACT_FAIL >&2; exit 1
fi
cat "$RUN/runner.stdout.log"
printf 'C01_OWNER_PYTHON_L0_PASS source_sha=%s evidence=%s\n' "$PINNED_STUDENT_SHA" "$RUN/evidence"
printf 'C01_OWNER_ROS_NOT_RUN_GAZEBO_NOT_RUN_SW_STOP_NOT_TESTED\n'
