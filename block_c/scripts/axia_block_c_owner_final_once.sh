#!/usr/bin/env bash
# AXIA Block C D09-D12 educational-MVP Owner WSL2 acceptance (pinned, read-only).
# NO Gazebo; NO production Safety Guard; NO robot motion; NO automatic release/merge.
set -Eeuo pipefail
umask 077
MODE="${1:---run}"
if [[ "$#" -gt 1 ]] || [[ "$MODE" != --run && "$MODE" != --self-check ]]; then
  echo 'BLOCK_C_OWNER_USAGE_ERROR expected=--run|--self-check' >&2
  exit 2
fi
INSTRUCTOR_SHA=961b574e7623eede6ae94bf7b9cf06e62dc3674a
STUDENT_SHA=dff7b4a2710525a72287f5416b7b613a9d979f1e
PUBLIC_CI_SHA=18631cf070b4c2afb994aa49013fee69224d2aa1
INSTRUCTOR_BRANCH=plan/block-c-d09-d12-freeze-20261115
STUDENT_BRANCH=feat/block-c-c01-synthetic-20261115
PUBLIC_C01_RUN=43716783675
PUBLIC_C05_RUN=43720178979
PUBLIC_C06_RUN=43725720019
if [[ "$MODE" == --self-check ]]; then
  bash -n "${BASH_SOURCE[0]}"
  printf 'BLOCK_C_OWNER_BOOTSTRAP_SELF_CHECK_PASS OWNER_WSL2_NOT_RUN\n'
  printf 'BLOCK_C_RELEASE_APPROVED=false\n'
  exit 0
fi

BASE="${AXIA_BLOCK_C_OWNER_ROOT:-${HOME:?}/axia_block_c_owner_acceptance}"
if [[ -L "$BASE" ]]; then echo 'BLOCK_C_OWNER_WORKROOT_SYMLINK_BLOCKED' >&2; exit 2; fi
mkdir -p -- "$BASE"
RUN="$(mktemp -d "$BASE/run-XXXXXXXX")"
mkdir -p -- "$RUN/evidence" "$RUN/lab"
STATUS_FILE="$RUN/evidence/stage_status.tsv"
printf 'stage\tresult\n' > "$STATUS_FILE"
READY=0
LAST_STAGE=BOOTSTRAP
INSTRUCTOR="$RUN/instructor"
STUDENT="$INSTRUCTOR/student"
TEACHER="$INSTRUCTOR/training/block_C"
STUDENT_BLOCK="$STUDENT/block_C"

finalize() {
  local rc=$?
  trap - EXIT
  local verdict=HOLD
  if [[ $rc -eq 0 && "$READY" == 1 ]]; then verdict=READY_FOR_OWNER_APPROVAL; fi
  local custody_ok=1
  if command -v python3 >/dev/null 2>&1; then
    python3 - "$RUN" "$STATUS_FILE" "$verdict" "$rc" "$LAST_STAGE" "$INSTRUCTOR_SHA" "$STUDENT_SHA" "$PUBLIC_CI_SHA" <<'PY' || custody_ok=0
import json,sys
from pathlib import Path
run,stages,status,rc,last,inst,student,public=sys.argv[1:]
lines=Path(stages).read_text().splitlines()[1:]
results={}
for line in lines:
    if '\t' in line:
        k,v=line.split('\t',1);results[k]=v
report={'schema_version':1,'profile':'BLOCK_C_EDUCATION_MVP_D09_D12',
        'status':status,'last_stage':last,'exit_code':int(rc),
        'instructor_source_sha':inst,'student_source_sha':student,'public_ci_source_sha':public,
        'stage_results':results,'owner_wsl2_verified':status=='READY_FOR_OWNER_APPROVAL',
        'release_approved': False,'main_merged':False,'safety_control_authority':False,
        'certified_estop':False,'production_guard_ttl_verified':False,'gazebo_actual':False,
        'release_decision':'OWNER_APPROVAL_REQUIRED' if status=='READY_FOR_OWNER_APPROVAL' else 'HOLD',
        'scope':'Synthetic-data education only; real WSL2 Python L0 plus ROS Jazzy educational L1 and ROS package build',
        'unverified':['Gazebo navigation','production Safety Guard and CM TTL','certified E-Stop',
                      'four 3-hour classroom rehearsals']}
Path(run,'verdict.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
PY
  else
    custody_ok=0
  fi
  if [[ "$custody_ok" == 1 && -s "$RUN/verdict.json" ]] && \
      tar -C "$RUN" -czf "$RUN/AXIA_BLOCK_C_OWNER_EVIDENCE.tar.gz" evidence verdict.json lab && \
      (cd "$RUN" && sha256sum AXIA_BLOCK_C_OWNER_EVIDENCE.tar.gz > AXIA_BLOCK_C_OWNER_EVIDENCE.tar.gz.sha256); then
    : # Evidence archive and SHA256 exist, so the declared verdict may be emitted.
  else
    custody_ok=0
  fi
  if [[ "$custody_ok" != 1 ]]; then
    echo BLOCK_C_EVIDENCE_CUSTODY_BLOCKED >&2
    verdict=HOLD
    rc=1
    printf '{"status":"HOLD","release_approved":false,"owner_wsl2_verified":false,"last_stage":"EVIDENCE_CUSTODY","release_decision":"HOLD"}\n' > "$RUN/verdict.json" || true
    tar -C "$RUN" -czf "$RUN/AXIA_BLOCK_C_OWNER_EVIDENCE.tar.gz" evidence verdict.json lab 2>/dev/null || true
    if [[ -f "$RUN/AXIA_BLOCK_C_OWNER_EVIDENCE.tar.gz" ]]; then
      (cd "$RUN" && sha256sum AXIA_BLOCK_C_OWNER_EVIDENCE.tar.gz > AXIA_BLOCK_C_OWNER_EVIDENCE.tar.gz.sha256) || true
    fi
  fi
  if [[ "$verdict" == HOLD ]]; then
    printf 'BLOCK_C_OWNER_ACCEPTED=HOLD\n'
  else
    printf 'BLOCK_C_OWNER_ACCEPTED=READY_FOR_OWNER_APPROVAL\n'
  fi
  printf 'BLOCK_C_RELEASE_APPROVED=false\n'
  printf 'BLOCK_C_PRODUCTION_GUARD_TTL_NOT_VERIFIED CERTIFIED_ESTOP_NOT_TESTED\n'
  printf 'BLOCK_C_OWNER_VERDICT=%s/verdict.json\n' "$RUN"
  printf 'BLOCK_C_OWNER_EVIDENCE=%s/AXIA_BLOCK_C_OWNER_EVIDENCE.tar.gz\n' "$RUN"
  exit "$rc"
}
trap finalize EXIT

echo "BLOCK_C_OWNER_SOURCE_PIN instructor=$INSTRUCTOR_SHA student=$STUDENT_SHA ci=$PUBLIC_CI_SHA"
echo "BLOCK_C_OWNER_RUN_DIR=$RUN"

run_step() {
  local name="$1"; shift
  LAST_STAGE="$name"
  echo "BLOCK_C_STAGE_START=$name"
  local rc=0
  "$@" >"$RUN/evidence/$name.log" 2>&1 || rc=$?
  if [[ "$rc" -ne 0 ]]; then
    printf '%s\tHOLD_RC_%s\n' "$name" "$rc" >> "$STATUS_FILE"
    cat "$RUN/evidence/$name.log" >&2
    echo "BLOCK_C_STAGE_HOLD=$name rc=$rc" >&2
    return "$rc"
  fi
  printf '%s\tPASS\n' "$name" >> "$STATUS_FILE"
  tail -n 4 "$RUN/evidence/$name.log" || true
  echo "BLOCK_C_STAGE_PASS=$name"
}

check_wsl2() {
  local kernel
  kernel="$(cat /proc/sys/kernel/osrelease 2>/dev/null || true)"
  if [[ ! "$kernel" =~ [Mm]icrosoft ]] && [[ ! "$kernel" =~ [Ww][Ss][Ll] ]]; then
    echo "BLOCK_C_WSL2_REQUIRED kernel=$kernel" >&2
    return 2
  fi
  [[ "$kernel" == *WSL2* || "$kernel" == *wsl2* ]] || {
    echo "BLOCK_C_WSL2_REQUIRED actual_kernel=$kernel" >&2; return 2;
  }
  echo "BLOCK_C_NATIVE_WSL2_CONFIRMED kernel=$kernel"
}
check_preflight() {
  local tool
  for tool in python3 git curl tar sha256sum cmp; do
    command -v "$tool" >/dev/null 2>&1 || { echo "BLOCK_C_ENV_MISSING_TOOL=$tool" >&2; return 2; }
  done
  python3 - <<'PY'
import sys
if sys.version_info[:2]!=(3,12):
    print(f'BLOCK_C_ENV_DIFF_BLOCKED expected_python=3.12 actual={sys.version.split()[0]}')
    raise SystemExit(2)
print('BLOCK_C_PYTHON312_CONFIRMED',sys.version.split()[0])
PY
  [[ -f /opt/ros/jazzy/setup.bash ]] || { echo 'BLOCK_C_ROS_JAZZY_MISSING' >&2; return 2; }
  command -v colcon >/dev/null 2>&1 || { echo 'BLOCK_C_ROS_COLCON_MISSING' >&2; return 2; }
  command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1 || {
    echo 'BLOCK_C_GH_AUTH_UNAVAILABLE: using configured git credentials for instructor clone'
  }
}
check_public_ci() {
  python3 - "$PUBLIC_C01_RUN" "$PUBLIC_C05_RUN" "$PUBLIC_C06_RUN" "$PUBLIC_CI_SHA" <<'PY'
import json,sys,urllib.request
c01,c05,c06,current=sys.argv[1:]
cases=[('C01',c01,'fd4019420f0552f4a08f531ea3e1336d7369e88e'),
       ('C05',c05,'968b1eb4296710860c02199f9b540c4f06098dbc'),
       ('C06',c06,current)]
for name,run,sha in cases:
    req=urllib.request.Request(
        f'https://api.github.com/repos/silverbjin/axia-robot-safety-ci-public/actions/runs/{run}',
        headers={'User-Agent':'AXIA-Block-C-Owner-WSL2','Accept':'application/vnd.github+json'})
    with urllib.request.urlopen(req,timeout=20) as response:
        data=json.load(response)
    if data.get('conclusion')!='success' or data.get('head_sha')!=sha:
        raise SystemExit(f'BLOCK_C_PUBLIC_CI_HOLD stage={name} run={run} status={data.get("conclusion")} head={data.get("head_sha")}')
    print(f'BLOCK_C_PUBLIC_CI_EVIDENCE_PASS stage={name} run={run} sha={sha}')
PY
}
clone_repos() {
  local teacher_url='https://github.com/silverbjin/axia-robot-safety-instructor.git'
  if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
    GIT_TERMINAL_PROMPT=0 gh repo clone silverbjin/axia-robot-safety-instructor "$INSTRUCTOR" -- \
      --depth 1 --branch "$INSTRUCTOR_BRANCH" --single-branch --quiet || return 2
  else
    GIT_TERMINAL_PROMPT=0 GIT_ASKPASS=/bin/false git clone --depth 1 --branch "$INSTRUCTOR_BRANCH" \
      --single-branch --quiet "$teacher_url" "$INSTRUCTOR" || {
       echo 'BLOCK_C_PRIVATE_SOURCE_AUTH_BLOCKED: configure gh auth or git credential helper' >&2; return 2;
      }
  fi
  GIT_TERMINAL_PROMPT=0 git clone --depth 1 --branch "$STUDENT_BRANCH" --single-branch --quiet \
    https://github.com/silverbjin/axia-robot-safety-student.git "$STUDENT" || return 2
  local actual_teacher actual_student
  actual_teacher="$(git -C "$INSTRUCTOR" rev-parse HEAD)"
  actual_student="$(git -C "$STUDENT" rev-parse HEAD)"
  [[ "$actual_teacher" == "$INSTRUCTOR_SHA" ]] || {
    echo "BLOCK_C_TEACHER_PIN_MISMATCH actual=$actual_teacher expected=$INSTRUCTOR_SHA" >&2; return 1; }
  [[ "$actual_student" == "$STUDENT_SHA" ]] || {
    echo "BLOCK_C_STUDENT_PIN_MISMATCH actual=$actual_student expected=$STUDENT_SHA" >&2; return 1; }
  echo "BLOCK_C_REPO_PINS_PASS instructor=$actual_teacher student=$actual_student"
}

check_manifests_and_source_parity() {
  python3 - "$TEACHER" "$STUDENT_BLOCK" <<'PY'
import hashlib,hmac,json,re,sys
from pathlib import Path
teacher,student=map(Path,sys.argv[1:])
for role,root,manifest in [('instructor',teacher,teacher/'release/RELEASE_MANIFEST.json'),
                           ('student',student,student/'release/PUBLIC_STUDENT_MANIFEST.json')]:
    m=json.loads(manifest.read_text())
    assert m['release_approved'] is False and m['owner_wsl2_verified'] is False
    assert m['control_authority'] is False and m['certified_estop'] is False
    assert m['data_source']=='SYNTHETIC_COURSE_FIXTURE'
    inventory=m['file_sha256'];assert len(inventory)>=10
    for rel,sha in inventory.items():
        p=Path(rel)
        assert not p.is_absolute() and '..' not in p.parts and re.fullmatch('[a-f0-9]{64}',sha),rel
        full=root/p
        assert full.is_file() and not full.is_symlink(),f'MISSING_OR_LINK_{role}:{rel}'
        assert hmac.compare_digest(hashlib.sha256(full.read_bytes()).hexdigest(),sha),f'SHA256_MISMATCH_{role}:{rel}'
    print(f'BLOCK_C_{role.upper()}_MANIFEST_SHA256_PASS files={len(inventory)}')
PY
  local path
  for path in generator.py normal_train.csv normal_valid.csv test_mixed.csv schema.json scenario_manifest.json PROVENANCE.md SHA256SUMS; do
    cmp -s "$TEACHER/fixtures/$path" "$STUDENT_BLOCK/fixtures/$path" || {
      echo "BLOCK_C_C01_INSTRUCTOR_STUDENT_MISMATCH=$path" >&2; return 1; }
  done
  for path in event_contract.py ros_diagnostic_bridge.py ros_l1_probe.py sample_events.jsonl; do
    cmp -s "$TEACHER/day12/shared/$path" "$STUDENT_BLOCK/day12/ros_transport/$path" || {
      echo "BLOCK_C_C05_SHARED_TRANSPORT_MISMATCH=$path" >&2; return 1; }
  done
  echo 'BLOCK_C_SHARED_C01_C05_BYTES_IDENTICAL'
}

install_python_venv() {
  python3 -m venv --system-site-packages "$RUN/venv" || {
    echo 'BLOCK_C_VENV_BLOCKED: install python3-venv via Ubuntu package manager' >&2; return 2; }
  export PATH="$RUN/venv/bin:$PATH"
  export PYTHONDONTWRITEBYTECODE=1
  local py="$RUN/venv/bin/python3"
  "$py" -m pip install --disable-pip-version-check --no-input --timeout 30 --retries 2 \
    'pytest==8.3.5' 'numpy==2.2.6' 'scikit-learn==1.8.0' 'python-pptx==1.0.2'
  if ! "$py" - <<'PY'
import torch
assert torch.__version__=='2.10.0+cpu',torch.__version__
PY
  then
    "$py" -m pip install --disable-pip-version-check --no-input --timeout 45 --retries 2 \
      --extra-index-url https://download.pytorch.org/whl/cpu 'torch==2.10.0+cpu' || {
        echo 'BLOCK_C_TORCH_CPU_INSTALL_BLOCKED' >&2; return 2; }
  fi
  "$py" - <<'PY'
import json,sys,torch,numpy,sklearn,pptx,pytest
if sys.version_info[:2]!=(3,12) or torch.__version__!='2.10.0+cpu' or sklearn.__version__!='1.8.0':
    raise SystemExit('BLOCK_C_VERSION_MISMATCH')
print('BLOCK_C_DEPENDENCY_PINS_PASS '+json.dumps({
    'python':sys.version.split()[0], 'numpy':numpy.__version__,
    'scikit_learn':sklearn.__version__, 'torch':torch.__version__,
    'python_pptx':pptx.__version__, 'pytest':pytest.__version__,
    'torch_cuda_available':torch.cuda.is_available()},sort_keys=True))
PY
}

instructor_unit() {
  AXIA_BLOCK_C_EVIDENCE_DIR="$RUN/evidence/instructor_unit" \
    bash "$TEACHER/scripts/block_c_once.sh" --unit
}
student_unit() {
  AXIA_BLOCK_C_EVIDENCE_DIR="$RUN/evidence/student_unit" \
    bash "$STUDENT_BLOCK/scripts/block_c_once.sh" --unit
}
assert_student_expected_red() {
  local rc=0
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q \
    "$STUDENT_BLOCK/tests/test_student_task_expected_red.py" >"$RUN/evidence/student_todo_expected_red.log" 2>&1 || rc=$?
  [[ "$rc" == 1 ]] && grep -q '4 failed' "$RUN/evidence/student_todo_expected_red.log" || {
    echo "BLOCK_C_TODO_RED_BOUNDARY_CHANGED rc=$rc" >&2
    cat "$RUN/evidence/student_todo_expected_red.log" >&2
    return 1
  }
  echo 'BLOCK_C_STUDENT_TODO_EXPECTED_RED_4_CONFIRMED'
}
model_pipeline() {
  mkdir -p "$RUN/lab"/{c02,c03,c04,c05}
  python3 "$TEACHER/day09/eda_pipeline.py" --fixtures "$TEACHER/fixtures" --out "$RUN/lab/c02"
  python3 "$TEACHER/day10/isolation_forest_pipeline.py" --features "$RUN/lab/c02" --out "$RUN/lab/c03"
  python3 "$TEACHER/day11/autoencoder_pipeline.py" --features "$RUN/lab/c02" \
     --if-metrics "$RUN/lab/c03" --checkpoint "$TEACHER/day11/reference_outputs/ae_checkpoint.pt" \
     --out "$RUN/lab/c04"
  python3 "$TEACHER/day12/events.py" --scores "$RUN/lab/c04/ae_scores_test.csv" --out "$RUN/lab/c05"
  python3 - "$RUN/lab" <<'PY'
import csv,json,sys
from pathlib import Path
base=Path(sys.argv[1]); features=base/'c02';c03=base/'c03';c04=base/'c04';c05=base/'c05'
counts={}
for split,n in [('train',240),('valid',80),('test',104)]:
    with (features/f'features_{split}.csv').open(newline='') as f: rows=list(csv.DictReader(f))
    assert len(rows)==n,(split,len(rows))
    counts[split]=n
m_if=json.loads((c03/'if_metrics.json').read_text())
m_ae=json.loads((c04/'ae_metrics.json').read_text())
for name,m in [('IF',m_if),('AE',m_ae)]:
    assert m['fit_on_test'] is False and m['test_threshold_tuned'] is False,name
    assert m['test_invalid_count']==4 and m['test_valid_count']==100,name
    assert m['threshold_source']=='normal_valid_only',name
    assert sum(m['confusion'].values())==100,name
    print(f'BLOCK_C_{name}_EDUCATIONAL_METRICS '+json.dumps(m['confusion'],sort_keys=True))
events=[json.loads(line) for line in (c05/'anomaly_events.jsonl').read_text().splitlines() if line]
assert len(events)==104,len(events)
assert sum(e['level']=='INSUFFICIENT_DATA' for e in events)==4
assert {e['level'] for e in events}=={'NORMAL','CAUTION','WARNING','INSUFFICIENT_DATA'}
assert all(e['control_authority'] is False and e['certified_estop'] is False for e in events)
print('BLOCK_C_PIPELINE_L0_PASS windows=424 valid_test=100 invalid_test=4 events=104')
PY
}

build_educational_ros_package() {
  set +u
  source /opt/ros/jazzy/setup.bash
  set -u
  colcon --log-base "$RUN/colcon/log" build --base-paths "$TEACHER/day12/ros2_ws/src" \
    --packages-select axia_block_c_diagnostics --build-base "$RUN/colcon/build" \
    --install-base "$RUN/colcon/install" --event-handlers console_cohesion+
  set +u
  source "$RUN/colcon/install/local_setup.bash"
  set -u
  ros2 pkg prefix axia_block_c_diagnostics
  ros2 pkg executables axia_block_c_diagnostics | grep -F 'axia-block-c-diagnostics'
  echo 'BLOCK_C_OWNER_COLCON_JAZZY_BUILD_PASS'
}

ros_l1_scoped() {
  export ROS_DOMAIN_ID="$((110 + (($$ + RANDOM) % 90)))"
  echo "BLOCK_C_OWNER_ISOLATED_ROS_DOMAIN_ID=$ROS_DOMAIN_ID"
  AXIA_BLOCK_C_EVIDENCE_DIR="$RUN/evidence/instructor_ros_l1" \
    bash "$TEACHER/scripts/block_c_once.sh" --ros-l1
  AXIA_BLOCK_C_EVIDENCE_DIR="$RUN/evidence/student_ros_l1" \
    bash "$STUDENT_BLOCK/scripts/block_c_once.sh" --ros-l1
  python3 - "$RUN/evidence/instructor_ros_l1/ros_l1/verdict.json" \
    "$RUN/evidence/student_ros_l1/ros_l1/verdict.json" <<'PY'
import json,sys
from pathlib import Path
for p in sys.argv[1:]:
    v=json.loads(Path(p).read_text())
    assert v['status']=='PASS_REAL_ROS_L1_EDUCATION_ONLY',v
    assert v['ros_actual'] is True and v['gazebo_actual'] is False
    assert v['sample_count']==8 and set(v['levels'])=={0,1,2,3}
    assert v['cmd_vel_published'] is False and v['goal_sent'] is False
    assert all(n==0 for n in v['cmd_vel_publisher_count'].values())
    assert v['production_guard_ttl_verified'] is False
    assert 20<=v['period_min_ms']<=v['period_max_ms']<=600
    print(f'BLOCK_C_OWNER_EDUCATION_ROS_L1_PASS period_ms=[{v["period_min_ms"]},{v["period_max_ms"]}]')
PY
}

model_event_to_ros() {
  # Use eight events CREATED BY THE ACTUAL AE evaluation, not unrelated sample_events.
  # Keep original chronological order within each trace for EventGate replay safety.
  python3 - "$RUN/lab/c05/anomaly_events.jsonl" "$RUN/evidence/model_derived_8.jsonl" <<'PY'
import json,sys
from pathlib import Path
src,dst=map(Path,sys.argv[1:])
items=[json.loads(x) for x in src.read_text().splitlines() if x.strip()]
levels=('NORMAL','CAUTION','WARNING','INSUFFICIENT_DATA')
selected=[]
for level in levels:
    ids=[(i,x) for i,x in enumerate(items) if x['level']==level][:2]
    if len(ids)!=2:raise SystemExit(f'BLOCK_C_MODEL_ROS_EVENTS_INSUFFICIENT_{level}')
    selected.extend(ids)
selected.sort(key=lambda z:z[0])
dst.write_text(''.join(json.dumps(row,sort_keys=True)+'\n' for _,row in selected))
print('BLOCK_C_MODEL_EVENTS_TO_ROS_SELECTED count=8 levels='+','.join(levels))
PY
  set +u
  source /opt/ros/jazzy/setup.bash
  set -u
  export PYTHONPATH="$TEACHER/day12/shared${PYTHONPATH:+:$PYTHONPATH}"
  python3 "$TEACHER/day12/shared/ros_l1_probe.py" \
    --events "$RUN/evidence/model_derived_8.jsonl" --out "$RUN/evidence/model_to_ros_l1" --messages 8
  python3 - "$RUN/evidence/model_to_ros_l1/verdict.json" <<'PY'
import json,sys
from pathlib import Path
v=json.loads(Path(sys.argv[1]).read_text())
assert v['status']=='PASS_REAL_ROS_L1_EDUCATION_ONLY',v
assert v['sample_count']==8 and set(v['levels'])=={0,1,2,3}
assert all(n==0 for n in v['cmd_vel_publisher_count'].values())
assert v['goal_sent'] is False and v['cmd_vel_published'] is False
assert v['production_guard_ttl_verified'] is False
print(f'BLOCK_C_OWNER_MODEL_TO_JAZZY_DDS_L1_PASS samples=8 period_max_ms={v["period_max_ms"]}')
PY
}

run_step WSL2_GATE check_wsl2
run_step TOOLS_AND_JAZZY check_preflight
run_step PUBLIC_CI_PROVENANCE check_public_ci
run_step EXACT_REPO_CHECKOUT clone_repos
run_step MANIFEST_SHA_AND_PARITY check_manifests_and_source_parity
run_step PYTHON312_PINNED_DEPENDENCIES install_python_venv
run_step INSTRUCTOR_PYTHON_L0 instructor_unit
run_step STUDENT_PYTHON_L0 student_unit
run_step STUDENT_EXPECTED_RED assert_student_expected_red
run_step C02_C05_MODEL_PIPELINE model_pipeline
run_step JAZZY_COLCON_PACKAGE_BUILD build_educational_ros_package
run_step INSTRUCTOR_STUDENT_JAZZY_L1 ros_l1_scoped
run_step AE_EVENT_TO_JAZZY_DDS_L1 model_event_to_ros
READY=1
printf 'BLOCK_C_OWNER_SCOPE_COMPLETE=PYTHON_L0_PLUS_EDUCATION_ROS_L1\n'
printf 'BLOCK_C_RELEASE_OWNER_SIGNOFF_REQUIRED NO_AUTO_MERGE NO_PRODUCTION_SAFETY_CLAIM\n'
