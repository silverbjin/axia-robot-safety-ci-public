#!/usr/bin/env bash
# AXIA D08 instructor offline Python L0; no ROS/Gazebo startup or robot actuation.
# Isolates pytest from ROS Jazzy's ambient pytest11 launch_testing entrypoint.
set -Eeuo pipefail
umask 077

PRIVATE_REPO='silverbjin/axia-robot-safety-instructor'
PRIVATE_BRANCH='feature/d08-online-integration-20261110'
PRIVATE_SHA='79a201ca6f7c5f02beee26f225706c76a23f7ae1'

if [[ "$#" -eq 1 && "$1" == '--self-check' ]]; then
  [[ "$PRIVATE_SHA" =~ ^[a-f0-9]{40}$ ]]
  echo 'D08_OWNER_WRAPPER_STATIC_PASS; ROS_AND_GAZEBO_NOT_RUN'
  exit 0
fi
[[ "$#" -eq 0 ]] || { echo 'BLOCKED: unexpected arguments' >&2; exit 2; }

source /etc/os-release
[[ "$ID" == 'ubuntu' && "$VERSION_ID" == '24.04' ]] || {
  echo 'BLOCKED: Ubuntu 24.04 required' >&2; exit 2;
}
grep -qiE 'microsoft|wsl' /proc/sys/kernel/osrelease || {
  echo 'BLOCKED: WSL2 required for owner wrapper' >&2; exit 2;
}
for tool in git gh tar sha256sum /usr/bin/python3; do
  command -v "$tool" >/dev/null || {
    echo "BLOCKED: missing prerequisite $tool" >&2; exit 2;
  }
done
[[ "$(/usr/bin/python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')" == '3.12' ]] || {
  echo 'BLOCKED: Ubuntu 24.04 system Python 3.12 required' >&2; exit 2;
}
gh auth status >/dev/null 2>&1 || {
  echo 'BLOCKED: gh auth login with instructor repo read access required' >&2; exit 2;
}

BASE="$HOME/axia_d08_evidence"
mkdir -p "$BASE"
chmod 700 "$BASE"
OUT="$(mktemp -d "$BASE/d08-owner-XXXXXXXX")"
SRC="$(mktemp -d "$HOME/axia_d08_instructor_XXXXXXXX")"
STATUS='BLOCKED'
GATE_RC=125

finish() {
  local wrapper_rc="$?"
  trap - EXIT INT TERM
  set +e
  cd "$HOME" || cd /
  /usr/bin/python3 - "$OUT/owner_summary.json" "$STATUS" "$GATE_RC" "$wrapper_rc" "$PRIVATE_SHA" <<'PY'
import json,sys
from pathlib import Path
path,status,gate_rc,wrapper_rc,private_sha=sys.argv[1:]
Path(path).write_text(json.dumps({
    'status':status, 'gate_rc':int(gate_rc), 'wrapper_rc':int(wrapper_rc),
    'teacher_source_sha':private_sha, 'verified_level':'PYTHON_ONLY',
    'ros_actual':False,'gazebo_actual':False,'robot_moved':False,
    'control_published':False,'collision_free_verified':False,
    'safety_certified':False
},indent=2)+"\n",encoding='utf-8')
PY
  # Never retain private instructor source or virtualenv as public artifacts.
  if [[ "$SRC" == "$HOME"/axia_d08_instructor_* ]]; then
    rm -rf -- "$SRC"
  fi
  (cd "$OUT" && find . -type f ! -name SHA256SUMS -print0 | sort -z |
    xargs -0 -r sha256sum > SHA256SUMS)
  tar -czf "$OUT.tar.gz" -C "$BASE" "$(basename "$OUT")"
  sha256sum "$OUT.tar.gz" > "$OUT.tar.gz.sha256"
  echo '========================================'
  echo "D08_OWNER_STATUS=$STATUS"
  echo "GATE_RC=$GATE_RC WRAPPER_RC=$wrapper_rc"
  echo "D08_OWNER_EVIDENCE=$OUT"
  echo "D08_OWNER_ARCHIVE=$OUT.tar.gz"
  echo 'ROS_GAZEBO_NOT_RUN=true CERTIFIED_ESTOP=false'
  echo '========================================'
  exit "$wrapper_rc"
}
trap finish EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

echo '========== D08: 강사 코드 다운로드 =========='
gh repo clone "$PRIVATE_REPO" "$SRC/instructor" -- \
  --branch "$PRIVATE_BRANCH" --single-branch >"$OUT/checkout.log" 2>&1 || {
    tail -n 15 "$OUT/checkout.log" >&2; exit 2;
  }
git -C "$SRC/instructor" checkout -q --detach "$PRIVATE_SHA" || {
  echo 'BLOCKED: verified private SHA unavailable' >&2; exit 2;
}
test "$(git -C "$SRC/instructor" rev-parse HEAD)" == "$PRIVATE_SHA"

echo '========== D08: Python 환경 =========='
# Using the OS interpreter avoids inheriting an active venv as our base.
VENV="$SRC/instructor/.venv"
if ! /usr/bin/python3 -m venv "$VENV" >"$OUT/venv.log" 2>&1; then
  echo '[D08] Installing missing Ubuntu venv support (not ROS/PyYAML)'
  sudo apt-get update -qq
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq python3.12-venv
  /usr/bin/python3 -m venv "$VENV" >>"$OUT/venv.log" 2>&1
fi
PY="$VENV/bin/python"
# Explicit interpreter and PYTHONPATH isolation: no ROS pytest11 plugins.
env -u PYTHONPATH -u PYTEST_ADDOPTS -u PYTEST_PLUGINS \
  PYTHONNOUSERSITE=1 "$PY" -m pip install --quiet --disable-pip-version-check \
  pytest==8.3.5 >"$OUT/pip.log" 2>&1 || {
    tail -n 20 "$OUT/pip.log" >&2; exit 2;
  }
env -u PYTHONPATH -u PYTEST_ADDOPTS -u PYTEST_PLUGINS \
  PYTHONNOUSERSITE=1 "$PY" -c \
  'import sys,pytest;print("D08_PYTHON_PRECHECK_PASS",sys.executable,"pytest",pytest.__version__)'

echo '========== D08: 강사 테스트 =========='
if (
  cd "$SRC/instructor"
  env -u PYTHONPATH -u PYTEST_ADDOPTS -u PYTEST_PLUGINS \
    PYTHONNOUSERSITE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
    "$PY" -m pytest -q --tb=short \
      training/block_B/tests/test_d08_integration.py \
      training/block_B/tests/test_d08_run_reference.py \
      training/block_B/instructor/hidden_tests/test_d08_integration_hidden.py
) >"$OUT/teacher_pytest.log" 2>&1; then
  tail -n 6 "$OUT/teacher_pytest.log"
else
  GATE_RC="$?"
  tail -n 40 "$OUT/teacher_pytest.log" >&2
  echo 'D08_OWNER_BLOCKED: instructor pytest failed' >&2
  exit 2
fi

echo '========== D08: 6개 합성 시나리오 재생 =========='
if (
  cd "$SRC/instructor"
  env -u PYTHONPATH -u PYTEST_ADDOPTS -u PYTEST_PLUGINS \
    PYTHONNOUSERSITE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
    "$PY" training/block_B/instructor/d08_run_reference.py \
      --out "$OUT/replay"
) >"$OUT/replay.log" 2>&1; then
  tail -n 6 "$OUT/replay.log"
else
  GATE_RC="$?"
  tail -n 30 "$OUT/replay.log" >&2
  echo 'D08_OWNER_BLOCKED: Python fixture replay failed' >&2
  exit 2
fi
/usr/bin/python3 - "$OUT/replay/summary.json" "$OUT/replay/trace.csv" <<'PY'
import csv,json,sys
from pathlib import Path
v=json.loads(Path(sys.argv[1]).read_text())
with Path(sys.argv[2]).open(newline='') as f:
    rows=list(csv.DictReader(f))
assert v['status']=='D08_EDU_PYTHON_L0_COMPLETE'
assert len(rows)==v['case_count']==6
assert [r['advice'] for r in v['results']]==[
    'REPLAN_REVIEW','SLOWDOWN_EXPECTED','STOP_EXPECTED',
    'UNKNOWN_REVIEW','UNKNOWN_REVIEW','UNKNOWN_REVIEW']
assert all(v.get(k) is False for k in (
    'ros_verified','gazebo_verified','robot_moved','control_published',
    'collision_free_verified','safety_certified'))
print('D08_OWNER_6_CASES_VERIFIED; PYTHON_ONLY')
PY
GATE_RC=0
STATUS='PASS_PYTHON_L0'
