#!/usr/bin/env bash
# C22: test WSL2 systemd-coredump pipeline using ONE isolated Bash SIGSEGV.
# This is only a preflight and never starts any simulator or ROS process.
set -Eeuo pipefail
umask 077
MODE="${1:---self-check}"
[[ $# -eq 1 && ( "$MODE" == --self-check || "$MODE" == --probe-once ) ]] || {
  echo 'D06_C22_USAGE=--self-check|--probe-once' >&2
  exit 2
}
if [[ "$MODE" == --self-check ]];then
  echo 'D06_C22_STATIC_PASS_NO_ROS_NO_GAZEBO_NO_CRASH'
  echo 'D06_C22_REAL_WSL2_PIPELINE_NOT_TESTED'
  echo 'AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false'
  exit 0
fi
[[ "${GITHUB_ACTIONS:-false}" != true ]] || {
  echo 'D06_C22_NOT_OWNER_WSL2_NO_CRASH' >&2
  exit 3
}
if ! grep -qiE 'microsoft|wsl' /proc/sys/kernel/osrelease;then
  echo 'D06_C22_NOT_OWNER_WSL2_NO_CRASH' >&2
  exit 3
fi
. /etc/os-release
[[ "${ID:-}" == ubuntu && "${VERSION_ID:-}" == 24.04 ]] || {
  echo 'D06_C22_UNSUPPORTED_UBUNTU_NO_CRASH' >&2
  exit 3
}
for exe in bash coredumpctl gdb grep sed head ps tar sha256sum timeout mktemp stat sleep rm;do
  command -v "$exe" >/dev/null || {
    echo "D06_C22_MISSING_EXECUTABLE=$exe NO_CRASH" >&2
    exit 3
  }
done
pattern="$(cat /proc/sys/kernel/core_pattern 2>/dev/null || true)"
[[ "$pattern" == \|*systemd-coredump* ]] || {
  echo 'D06_C22_NO_SYSTEMD_CORE_PIPE_NO_CRASH' >&2
  exit 3
}
echo 'D06_C22_SYNTHETIC_BASH_CHILD_SINGLE_SIGSEGV_ONLY'
ROOT="$HOME/axia_d06_c22_core_pipeline"
mkdir -p "$ROOT"
chmod 700 "$ROOT"
RUN="$(mktemp -d -p "$ROOT" 'probe-XXXXXXXX')"
STAGE=INIT
PROBE_RC=NOT_RUN
: > "$RUN/summary.txt"
: > "$RUN/preflight.txt"
: > "$RUN/probe_result.txt"
: > "$RUN/gdb_excerpt.txt"
finish() {
  local rc=$?
  trap - EXIT
  set +e
  rm -f -- "$RUN/private.core"
  echo "stage=$STAGE synthetic_child_rc=$PROBE_RC core_not_archived=true" >> "$RUN/summary.txt"
  local archive="$ROOT/$(basename "$RUN").tar.gz"
  (cd "$RUN" && tar -czf "$archive" summary.txt preflight.txt probe_result.txt gdb_excerpt.txt)
  sha256sum "$archive" > "$archive.sha256"
  echo "D06_C22_FORENSIC_ARCHIVE=$archive"
  echo "D06_C22_FORENSIC_SHA256=$archive.sha256"
  echo 'D06_C22_NO_GOAL_ACCEPTANCE_NOT_RUN'
  echo 'AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false'
  exit "$rc"
}
trap finish EXIT
{
  echo "kernel_core_pattern=$pattern"
  echo "parent_core_soft_limit=$(ulimit -Sc)"
  echo "parent_core_hard_limit=$(ulimit -Hc)"
  echo "init_process=$(ps -p 1 -o comm= 2>/dev/null || true)"
  echo 'process_under_test=isolated_bash_subprocess'
  echo 'system_config_changed=false'
} > "$RUN/preflight.txt"
# Changing the core soft limit is local ONLY to the isolated child.
# Shell exit 139 means this intentional SIGSEGV happened; it is not
# a Gazebo crash and does not exercise Gazebo GPU teardown.
STAGE=SYNTHETIC_CHILD
PROBE_RC=0
(
  ulimit -c 65536 || exit 46
  bash -c 'printf "%s\n" "$BASHPID" > "$1"; kill -s SEGV "$BASHPID"' _ "$RUN/probe.pid"
) > "$RUN/child.private.stderr" 2>&1 || PROBE_RC=$?
echo "synthetic_child_rc=$PROBE_RC" >> "$RUN/probe_result.txt"
if [[ "$PROBE_RC" != 139 || ! -s "$RUN/probe.pid" ]];then
  echo 'D06_C22_SYNTHETIC_CRASH_NOT_CONFIRMED_HOLD_NO_GAZEBO' | tee -a "$RUN/summary.txt"
  exit 3
fi
PID="$(cat "$RUN/probe.pid")"
[[ "$PID" =~ ^[1-9][0-9]*$ ]] || {
  echo 'D06_C22_SYNTHETIC_PID_INVALID_HOLD_NO_GAZEBO' | tee -a "$RUN/summary.txt"
  exit 3
}
echo "synthetic_pid=$PID" >> "$RUN/probe_result.txt"
STAGE=CORE_INDEX
found=0
for attempt in 1 2 3 4 5 6 7 8;do
  if coredumpctl --no-pager info "$PID" > "$RUN/core_info.private" 2>&1 &&
     grep -Eq '^[[:space:]]*Signal:[[:space:]]*11' "$RUN/core_info.private" &&
     grep -Eq '^[[:space:]]*Executable:[[:space:]]*/(usr/)?bin/bash' "$RUN/core_info.private";then
    found=1
    break
  fi
  sleep 1
done
if [[ "$found" != 1 ]];then
  echo 'D06_C22_SYSTEMD_CORE_RETRIEVAL_NOT_PROVEN_HOLD_NO_GAZEBO' | tee -a "$RUN/summary.txt"
  exit 3
fi
{
  echo 'synthetic_record=found_signal11_bash'
  grep -E '^[[:space:]]*(Signal|Executable|Storage):' "$RUN/core_info.private" | head -n 5 || true
} >> "$RUN/probe_result.txt"
STAGE=CORE_DUMP
if ! timeout 25s coredumpctl dump "$PID" --output="$RUN/private.core" \
      > "$RUN/dump.private.log" 2>&1;then
  echo 'D06_C22_SYSTEMD_CORE_RETRIEVAL_NOT_PROVEN_HOLD_NO_GAZEBO' | tee -a "$RUN/summary.txt"
  exit 3
fi
corebytes="$(stat -c '%s' "$RUN/private.core" 2>/dev/null || echo 0)"
if [[ ! "$corebytes" =~ ^[1-9][0-9]*$ || "$corebytes" -gt 67108864 ]];then
  echo 'D06_C22_SYSTEMD_CORE_INVALID_SIZE_HOLD_NO_GAZEBO' | tee -a "$RUN/summary.txt"
  exit 3
fi
echo 'systemd_core_export=available_private_only' >> "$RUN/probe_result.txt"
STAGE=GDB_FIRST_FRAME
timeout 30s gdb -nx -q -batch \
  -ex 'set pagination off' -ex 'bt 8' \
  -- "$(command -v bash)" "$RUN/private.core" \
  > "$RUN/gdb.private.log" 2>&1 || true
head -c 32768 "$RUN/gdb.private.log" > "$RUN/gdb_excerpt.txt"
if ! grep -Eq 'SIGSEGV|Segmentation fault' "$RUN/gdb_excerpt.txt" ||
   ! grep -Eq '^#0[[:space:]]' "$RUN/gdb_excerpt.txt";then
  echo 'D06_C22_SYNTHETIC_CORE_FIRST_FRAME_MISSING_HOLD_NO_GAZEBO' | tee -a "$RUN/summary.txt"
  exit 3
fi
echo 'D06_C22_SYNTHETIC_COREDUMP_PIPELINE_PASS_NOT_GAZEBO' | tee -a "$RUN/summary.txt"
STAGE=CORE_TRANSPORT_PROVEN
exit 0
