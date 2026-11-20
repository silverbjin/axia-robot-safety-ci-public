#!/usr/bin/env bash
# AXIA D10: cwd-independent instructor offline C01 -> C02 -> C03 one-shot.
# Public transport only. Private instructor implementation stays in private repo.
# Invoke with `bash script --run` (never `source script`).
if [[ "${BASH_SOURCE[0]}" != "$0" ]]; then
  printf '%s\n' 'D10_DO_NOT_SOURCE_USE_BASH_SCRIPT' >&2
  return 2
fi
set -Eeuo pipefail
MODE="${1:---run}"
if [[ $# -gt 1 ]] || [[ "$MODE" != --run && "$MODE" != --doctor && "$MODE" != --help ]]; then
  printf '%s\n' 'usage: bash d10_instructor_offline_once.sh [--run|--doctor|--help]' >&2
  exit 2
fi
if [[ "$MODE" == --help ]]; then
  printf '%s\n' 'D10 offline C01 fixture -> C02 feature -> C03 isolation forest. Does not launch ROS/Gazebo.' \
    'Environment: AXIA_D10_INSTRUCTOR_ROOT=<checkout root or training/block_C> (optional)' \
    'AXIA_D10_WORK_DIR=<local work dir> AXIA_D10_PYTHON=<python executable> (optional)'
  exit 0
fi
WORK="${AXIA_D10_WORK_DIR:-${HOME:?}/axia_d10_course}"
if ! mkdir -p -- "$WORK/evidence"; then
  printf 'D10_WORK_DIR_BLOCKED path=%s\n' "$WORK" >&2; exit 2
fi
RUN="$(mktemp -d "$WORK/evidence/run-$(date -u +%Y%m%dT%H%M%SZ)-XXXXXX")"
LOG="$RUN/session.log"
STAGE=INIT
fail() { printf 'D10_BLOCKED stage=%s reason=%s\n' "$STAGE" "$1" >&2; return 2; }
find_block() {
  local candidate="${1:-}"
  [[ -n "$candidate" && -d "$candidate" ]] || return 1
  if [[ -f "$candidate/training/block_C/day10/isolation_forest_pipeline.py" ]]; then
    printf '%s\n' "$(cd "$candidate/training/block_C" && pwd -P)"; return 0
  fi
  if [[ -f "$candidate/day10/isolation_forest_pipeline.py" && -f "$candidate/fixtures/generator.py" ]]; then
    printf '%s\n' "$(cd "$candidate" && pwd -P)"; return 0
  fi
  return 1
}
resolve_block() {
  STAGE=SOURCE_DISCOVERY
  local cwd="$PWD" found='' candidate=''
  for candidate in "${AXIA_D10_INSTRUCTOR_ROOT:-}" "$cwd" "$WORK/axia-robot-safety-instructor" \
      "${HOME}/axia-robot-safety-instructor" "${HOME}/axia_d09_course/axia-robot-safety-instructor"; do
    if found="$(find_block "$candidate")"; then printf '%s\n' "$found"; return 0; fi
  done
  while [[ "$cwd" != / ]]; do
    cwd="$(dirname "$cwd")"
    if found="$(find_block "$cwd")"; then printf '%s\n' "$found"; return 0; fi
  done
  if [[ -n "${AXIA_D10_INSTRUCTOR_ROOT:-}" ]]; then
    printf '%s\n' 'D10_SOURCE_BLOCKED specified_AXIA_D10_INSTRUCTOR_ROOT_invalid' >&2
    return 2
  fi
  if [[ "${AXIA_D10_DISABLE_CLONE:-0}" == 1 ]]; then
    printf '%s\n' 'D10_SOURCE_BLOCKED local_instructor_checkout_not_found clone_disabled' >&2
    return 2
  fi
  local dest="$WORK/axia-robot-safety-instructor"
  if [[ -e "$dest" ]]; then
    printf 'D10_SOURCE_BLOCKED existing_path_not_valid=%s\n' "$dest" >&2
    return 2
  fi
  printf 'D10_SOURCE_AUTO_CLONE private_repo=%s\n' 'silverbjin/axia-robot-safety-instructor' >&2
  if ! GIT_TERMINAL_PROMPT=0 git clone --quiet \
      https://github.com/silverbjin/axia-robot-safety-instructor.git "$dest"; then
    printf '%s\n' 'D10_SOURCE_BLOCKED private_clone_failed; authorize GitHub (gh auth login / gh auth setup-git)' >&2
    return 2
  fi
  find_block "$dest" || { printf '%s\n' 'D10_SOURCE_BLOCKED cloned_repo_missing_D10' >&2; return 2; }
}
main() {
  printf 'D10_OWNER_START mode=%s work=%s cwd=%s evidence=%s\n' "$MODE" "$WORK" "$PWD" "$RUN"
  local root='' py="${AXIA_D10_PYTHON:-python3}" sha='' vers=''
  STAGE=SOURCE_DISCOVERY
  printf 'D10_STAGE=%s\n' "$STAGE"
  root="$(resolve_block)" || fail 'instructor_checkout_not_available'
  printf 'D10_BLOCK_C_ROOT=%s\n' "$root"
  STAGE=SOURCE_VERSION
  printf 'D10_STAGE=%s\n' "$STAGE"
  if ! command -v git >/dev/null 2>&1; then fail 'git_missing'; fi
  sha="$(git -C "$root" rev-parse HEAD)" || fail 'git_repo_invalid'
  printf '%s\n' "$sha" >"$RUN/instructor_sha.txt"
  printf 'D10_INSTRUCTOR_SOURCE_SHA=%s\n' "$sha"
  if [[ -n "$(git -C "$root" status --porcelain --untracked-files=no)" ]]; then
    printf '%s\n' 'D10_SOURCE_WORKTREE_MODIFIED local_tracked_changes_present'
  fi
  STAGE=PYTHON_DEPENDENCIES
  printf 'D10_STAGE=%s\n' "$STAGE"
  # Never install into system Python or ROS 2. Prefer course-owned virtualenv.
  local owned_venv="$WORK/.venv-d10" base_py='' explicit_py=0
  if [[ -n "${AXIA_D10_PYTHON:-}" ]]; then
    py="$AXIA_D10_PYTHON"; explicit_py=1
  elif [[ -x "$owned_venv/bin/python" ]]; then
    py="$owned_venv/bin/python"
  elif [[ -x "$WORK/.venv/bin/python" ]]; then
    py="$WORK/.venv/bin/python"
  elif command -v python3.12 >/dev/null 2>&1; then
    py="$(command -v python3.12)"
  else
    py="$(command -v python3 || true)"
  fi
  [[ -n "$py" ]] && command -v "$py" >/dev/null 2>&1 || fail 'python_missing; install Ubuntu 24.04 Python 3.12'
  if ! "$py" -c 'import sys;raise SystemExit(0 if sys.version_info[:2]==(3,12) else 2)' >"$RUN/python_version_probe.log" 2>&1; then
    "$py" --version >"$RUN/python_version_actual.log" 2>&1 || true
    cat "$RUN/python_version_actual.log"
    fail 'python_3_12_required; use Ubuntu 24.04 Python 3.12 (do not replace system Python)'
  fi
  if ! "$py" -c 'import sys,numpy,sklearn;print("python="+sys.version.split()[0]+" numpy="+numpy.__version__+" sklearn="+sklearn.__version__)' >"$RUN/versions.log" 2>&1; then
    cp "$RUN/versions.log" "$RUN/initial_dependency_error.log"
    printf 'D10_PYTHON_DEPENDENCY_MISSING py=%s; numpy/scikit-learn unavailable\n' "$py"
    if [[ "$MODE" == --doctor ]]; then
      fail 'doctor_only_missing_dependencies; --run can prepare course venv without sudo'
    fi
    if [[ "${AXIA_D10_AUTO_INSTALL:-1}" != 1 ]]; then
      fail 'auto_install_disabled; provide a venv using AXIA_D10_PYTHON or enable AXIA_D10_AUTO_INSTALL=1'
    fi
    if (( explicit_py )) && [[ "$py" != "$owned_venv/bin/python" && "$py" != "$WORK/.venv/bin/python" ]]; then
      fail 'explicit_python_missing_dependencies; install into your selected venv or omit AXIA_D10_PYTHON for automatic course venv'
    fi
    STAGE=PYTHON_BOOTSTRAP
    printf 'D10_STAGE=%s\n' "$STAGE"
    if [[ -x "$WORK/.venv/bin/python" && "$py" == "$WORK/.venv/bin/python" ]]; then
      printf 'D10_VENV_REUSE path=%s\n' "$WORK/.venv"
    else
      if [[ ! -x "$owned_venv/bin/python" ]]; then
        if [[ -e "$owned_venv" ]]; then
          fail 'course_venv_path_exists_but_invalid; rename it manually after preserving evidence'
        fi
        if command -v python3.12 >/dev/null 2>&1; then
          base_py="$(command -v python3.12)"
        else
          base_py="$py"
        fi
        printf 'D10_VENV_CREATE path=%s python=%s\n' "$owned_venv" "$base_py"
        if ! "$base_py" -m venv "$owned_venv" >"$RUN/venv_create.log" 2>&1; then
          cat "$RUN/venv_create.log"
          fail 'venv_creation_failed; install python3.12-venv using apt and retry'
        fi
      fi
      py="$owned_venv/bin/python"
      printf 'D10_VENV_REUSE path=%s\n' "$owned_venv"
    fi
    printf 'D10_PIP_INSTALL_BEGIN python=%s requirements=numpy>=1.26,<3;scikit-learn==1.8.0\n' "$py"
    if ! "$py" -m pip install --disable-pip-version-check --no-input --only-binary=:all: \
        --retries 2 --timeout 30 'numpy>=1.26,<3' 'scikit-learn==1.8.0' >"$RUN/python_install.log" 2>&1; then
      tail -n 55 "$RUN/python_install.log"
      fail 'pip_install_failed; inspect python_install.log and network/proxy; no system Python changed'
    fi
    printf 'D10_PIP_INSTALL_PASS evidence=%s\n' "$RUN/python_install.log"
    if ! "$py" -c 'import sys,numpy,sklearn;print("python="+sys.version.split()[0]+" numpy="+numpy.__version__+" sklearn="+sklearn.__version__)' >"$RUN/versions.log" 2>&1; then
      cat "$RUN/versions.log"
      fail 'post_install_import_failed; inspect versions.log'
    fi
  fi
  vers="$(cat "$RUN/versions.log")"; printf 'D10_RUNTIME=%s py=%s\n' "$vers" "$py"
  if [[ "$vers" != *"sklearn=1.8.0"* ]]; then
    printf '%s\n' 'D10_SKLEARN_VERSION_NOTE expected_reference=1.8.0; C03 reference check remains authoritative'
  fi
  [[ -f "$root/fixtures/generator.py" && -f "$root/day09/eda_pipeline.py" && \
    -f "$root/day10/isolation_forest_pipeline.py" ]] || fail 'required_instructor_files_missing'
  if [[ "$MODE" == --doctor ]]; then
    printf '%s\n' 'D10_OWNER_DOCTOR_PASS ros_actual=false gazebo_actual=false model_not_run=true'
    return 0
  fi
  STAGE=C01_FIXTURE
  printf 'D10_STAGE=%s\n' "$STAGE"
  "$py" "$root/fixtures/generator.py" --check --fixture-dir "$root/fixtures" | tee "$RUN/fixture.log"
  STAGE=C02_FEATURES
  printf 'D10_STAGE=%s\n' "$STAGE"
  "$py" "$root/day09/eda_pipeline.py" --fixtures "$root/fixtures" --out "$RUN/c02" | tee "$RUN/eda.log"
  STAGE=C03_ISOLATION_FOREST
  printf 'D10_STAGE=%s\n' "$STAGE"
  "$py" "$root/day10/isolation_forest_pipeline.py" --features "$RUN/c02" --out "$RUN/c03" | tee "$RUN/if.log"
  STAGE=C03_RESULT_CONTRACT
  printf 'D10_STAGE=%s\n' "$STAGE"
  "$py" - "$RUN/c03/if_metrics.json" "$RUN/c03/if_scores_test.csv" <<'PY' | tee "$RUN/check.log"
import csv,json,sys
from pathlib import Path
m=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
with Path(sys.argv[2]).open(newline='',encoding='utf-8') as f:
    rows=list(csv.DictReader(f))
assert m['source']=='SYNTHETIC_COURSE_FIXTURE'
assert (m['train_count'],m['valid_count'],m['test_valid_count'],m['test_invalid_count'])==(240,80,100,4)
assert m['threshold_source']=='normal_valid_only'
assert m['risk_score_direction']=='higher_is_more_anomalous'
assert m['fit_on_test'] is False and m['test_threshold_tuned'] is False
assert m['ros_actual'] is False and m['gazebo_actual'] is False
assert m['safety_control_authority'] is False
assert len(rows)==104 and sum(m['confusion'].values())==100
bad=[r for r in rows if r['status']=='INSUFFICIENT_DATA']
assert len(bad)==4 and all(r['prediction']=='INSUFFICIENT_DATA' and r['risk_score']=='' and r['threshold']=='' for r in bad)
if m['confusion']!={'TP':1,'FP':2,'FN':17,'TN':80}:
    raise AssertionError('baseline numeric mismatch, inspect Python/sklearn versions; test threshold must NOT be retuned')
assert abs(m['threshold']-0.10199750)<1e-7
hits=[r for r in rows if r['trace_id']=='TST_A_00' and r['truth_label']=='1' and r['prediction']=='WARNING']
assert len(hits)==1 and hits[0]['window_id']=='5' and int(hits[0]['timestamp_ns'])==5900000000
fps={(r['trace_id'],r['window_id']) for r in rows if r['truth_label']=='0' and r['prediction']=='WARNING'}
assert fps=={('TST_A_03','9'),('TST_A_04','8')}
print('D10_C03_REFERENCE_CONTRACT_PASS threshold=0.10199750 tp=1 fp=2 fn=17 tn=80 quality=4 synthetic_delay_s=1.9')
PY
  STAGE=DONE
  printf 'D10_OWNER_OFFLINE_L0_PASS evidence=%s ros_actual=false gazebo_actual=false safety_control_authority=false\n' "$RUN"
}
# Run in a dedicated process with one consolidated evidence log. Never set -e in the caller shell.
set +e
( set -Eeuo pipefail; main ) 2>&1 | tee "$LOG"
rc=${PIPESTATUS[0]}
set -e
if (( rc != 0 )); then
  printf 'D10_OWNER_HOLD rc=%d first_failed_stage_in_log=%s evidence=%s\n' "$rc" "$LOG" "$RUN" | tee -a "$LOG" >&2
fi
exit "$rc"
