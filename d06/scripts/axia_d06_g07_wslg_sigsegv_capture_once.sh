#!/usr/bin/env bash
# AXIA D06 C11 — first WSLg Gazebo SIGSEGV core stack, one bounded NO_GOAL trial.
# No Goal/velocity/fault, no RMW/GPU overrides, no system-global configuration.
set -Eeuo pipefail
umask 077
MODE="${1:---self-check}"
[[ $# -le 1 && ( "$MODE" == --self-check || "$MODE" == --run-once ) ]] || {
  echo 'D06_WSLG_CORE_ONCE_USAGE=--self-check|--run-once' >&2;exit 2;
}
if [[ "$MODE" == --self-check ]];then
  echo 'D06_WSLG_CORE_ONCE_L0_PASS_NO_ROS_NO_GAZEBO'
  echo 'AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false'
  exit 0
fi
# WSL2-only, explicit NO_GOAL; no local settings/apt/driver modifications.
[[ "${GITHUB_ACTIONS:-false}" != true && -n "${DISPLAY:-}" ]] || {
  echo 'D06_WSLG_CORE_ONCE_HOLD_WSL2_DISPLAY_REQUIRED' >&2;exit 3;
}
grep -qiE 'microsoft|wsl' /proc/sys/kernel/osrelease || {
  echo 'D06_WSLG_CORE_ONCE_HOLD_WSL2_KERNEL_REQUIRED' >&2;exit 3;
}
for exe in python3 curl sha256sum git bash gdb coredumpctl timeout tar glxinfo;do
  command -v "$exe" >/dev/null 2>&1 || {
    echo "D06_WSLG_CORE_ONCE_HOLD_MISSING_TOOL=$exe" >&2;exit 3;
  }
done
# This is a diagnosis, NOT the approved Owner WSL2 L3 acceptance run.
echo 'D06_WSLG_CORE_ONCE_DIAGNOSTIC_NO_GOAL_OWNER_L3_NOT_RUN'
echo 'AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false'
ROOT="${HOME:?}/axia_d06_g07_wslg_core_once"
mkdir -p "$ROOT";chmod 700 "$ROOT"
RUN="$(mktemp -d -p "$ROOT" 'trace-XXXXXXXX')"
chmod 700 "$RUN"
STAGE=PREFLIGHT
OWNER_RC=NOT_RUN
TMP=''
finish() {
  local rc=$?
  trap - EXIT
  set +e
  echo "stage=$STAGE owner_rc=$OWNER_RC root_cause=UNCONFIRMED core_not_archived=true" >> "$RUN/summary.txt"
  if [[ -f "$RUN/owner_full.log" ]];then
    tail -n 220 "$RUN/owner_full.log" > "$RUN/owner_tail.log"
    rm -f "$RUN/owner_full.log"
  fi
  # Never archive raw process memory, coredump index or local auth tokens.
  local archive="$ROOT/$(basename "$RUN").tar.gz"
  (cd "$RUN" && tar -czf "$archive" summary.txt preflight.txt triage.log owner_tail.log)
  sha256sum "$archive" > "$archive.sha256"
  [[ -z "$TMP" ]] || rm -rf -- "$TMP"
  echo "D06_WSLG_CORE_ONCE_FORENSIC_ARCHIVE=$archive"
  echo "D06_WSLG_CORE_ONCE_SHA256=$archive.sha256"
  echo 'D06_GAZEBO_LIVE_RELEASE=HOLD AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false'
  exit "$rc"
}
: > "$RUN/summary.txt"
: > "$RUN/preflight.txt"
: > "$RUN/triage.log"
: > "$RUN/owner_tail.log"
trap finish EXIT
PATTERN="$(cat /proc/sys/kernel/core_pattern 2>/dev/null || true)"
printf 'kernel_core_pattern=%s\ncurrent_core_soft_limit=%s\n' "$PATTERN" "$(ulimit -c)" > "$RUN/preflight.txt"
# Reuse only exact pinned, public, L0-tested files. No arbitrary remote shell.
PINNED_PUBLIC_SHA='d66e6052d777696c390ddbb791b346f7abb96711'
OWNER_BLOB='0592044ade101dfdff7682e127953c976778e6fc'
TRIAGE_BLOB='08d66ff3cac2dac4564b744a02f5a8e50faf7b61'
FINDER_SHA='801e6b7be271da55a86101d25924edcafc98deb6'
FINDER_BLOB='04cc7cab351f4542dba754262912900cd258ec25'
RAW='https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public'
TMP="$(mktemp -d)"
for ent in \
  "owner:$PINNED_PUBLIC_SHA:d06/scripts/axia_d06_g07_wslg_gpu_rtf_compare_once.sh:$OWNER_BLOB" \
  "triage:$PINNED_PUBLIC_SHA:d06/scripts/axia_d06_g07_wslg_existing_core_once.sh:$TRIAGE_BLOB" \
  "finder:$FINDER_SHA:d06/tools/d06_wslg_latest_gz_sigsegv_core.py:$FINDER_BLOB";do
  IFS=: read -r key commit path expected <<< "$ent"
  curl -fLsS --retry 2 --max-time 90 "$RAW/$commit/$path" -o "$TMP/$key"
  [[ "$(git hash-object "$TMP/$key")" == "$expected" ]] || {
    echo "D06_WSLG_CORE_ONCE_HOLD_SOURCE_BLOB_MISMATCH=$key" >&2;exit 3;
  }
done
bash -n "$TMP/owner" "$TMP/triage"
python3 -m py_compile "$TMP/finder"
listing() {
  local dest="$1"
  if ! coredumpctl --no-pager --json=short list > "$dest" 2> "$RUN/coredump_error_private.tmp";then
    # No stored cores may return status 1 with empty stdout; that is
    # distinct from JSON mode unsupported, which prints an error.
    if [[ ! -s "$dest" ]];then
      if grep -Eiq 'unrecognized|unknown|invalid option' "$RUN/coredump_error_private.tmp";then
        echo 'D06_WSLG_CORE_ONCE_HOLD_JSON_COREDUMPCTL_UNSUPPORTED' >&2
        return 3
      fi
      printf '[]\n' > "$dest"
    fi
  fi
  python3 - "$dest" <<'PY'
import json,sys
s=open(sys.argv[1]).read().strip()
try:
    json.loads(s)
except (ValueError,TypeError):
    # newline-delimited coredump records also supported by finder
    try:
        for x in s.splitlines():json.loads(x)
    except (ValueError,TypeError):
        sys.exit(3)
PY
}
core_pid() {
  local file="$1" pid=''
  pid="$(python3 "$TMP/finder" --json-file "$file" 2>/dev/null || true)"
  [[ "$pid" =~ ^[1-9][0-9]*$ ]] && printf '%s' "$pid"
}
listing "$RUN/before_cores.json" || {
  echo 'D06_WSLG_CORE_ONCE_HOLD_COREDUMP_INDEX_UNREADABLE' >&2;exit 3;
}
before="$(core_pid "$RUN/before_cores.json" || true)"
STAGE=FIRST_CORE_CHECK
if [[ -n "$before" ]];then
  echo "D06_WSLG_CORE_ONCE_EXISTING_GZ_SIGSEGV_PID=$before NO_REPLAY" | tee -a "$RUN/summary.txt"
  after="$before"
else
  # A new Gazebo trial is allowed only if systemd actually receives new
  # cores, otherwise it would be a useless physical repeat without a stack.
  [[ "$PATTERN" == *systemd-coredump* ]] || {
    echo 'D06_WSLG_CORE_ONCE_HOLD_NO_SYSTEMD_COREDUMP_HANDLER_NO_REPLAY' | tee -a "$RUN/summary.txt"
    exit 3
  }
  # Do not contend with another already running simulation.
  if ps -eo args | grep -Eq '[g]z sim .* -s';then
    echo 'D06_WSLG_CORE_ONCE_HOLD_OTHER_GAZEBO_SIM_RUNNING' >&2;exit 3
  fi
  ulimit -c 524288 || {
    echo 'D06_WSLG_CORE_ONCE_HOLD_CORE_RLIMIT_NOT_SETTABLE' >&2;exit 3;
  }
  echo 'D06_WSLG_CORE_ONCE_SINGLE_NVIDIA_NO_GOAL_FORENSIC_START' | tee -a "$RUN/summary.txt"
  STAGE=ONE_NVIDIA_NO_GOAL_TRIAL
  OWNER_RC=0
  # This existing owner is SHA-and-blob pinned, starts exactly ONE NVIDIA
  # NO_GOAL causal session, and packages its own complete raw evidence.
  timeout --signal=TERM --kill-after=5s 900s \
    bash "$TMP/owner" --nvidia-causal > "$RUN/owner_full.log" 2>&1 || OWNER_RC=$?
  printf 'owner_rc=%s\n' "$OWNER_RC" >> "$RUN/summary.txt"
  STAGE=AFTER_SINGLE_TRIAL
  # Let coredump collection finish; do not replay the simulation.
  after=''
  for n in 1 2 3 4 5;do
    listing "$RUN/after_cores.json" || break
    after="$(core_pid "$RUN/after_cores.json" || true)"
    [[ -n "$after" && "$after" != "$before" ]] && break
    sleep 1
  done
  [[ -n "$after" && "$after" != "$before" ]] || {
    echo 'D06_WSLG_CORE_ONCE_HOLD_FIRST_SIGSEGV_CORE_NOT_CAPTURED_AFTER_ONE_TRIAL' | tee -a "$RUN/summary.txt"
    exit 3
  }
fi
STAGE=GDB_EXISTING_CORE
echo "D06_WSLG_CORE_ONCE_CANDIDATE_PID=$after" >> "$RUN/summary.txt"
if bash "$TMP/triage" --pid "$after" > "$RUN/triage.log" 2>&1 &&
   grep -Fq 'D06_WSLG_CORE_TRIAGE_STACK=CAPTURED' "$RUN/triage.log";then
  echo 'D06_WSLG_CORE_STACK_CAPTURED_NOT_RESOLVED' | tee -a "$RUN/summary.txt"
else
  echo 'D06_WSLG_CORE_ONCE_HOLD_FIRST_STACK_NOT_RECOVERABLE' | tee -a "$RUN/summary.txt"
fi
# Never promote a diagnostic stack to an accepted release.
exit 3
