#!/usr/bin/env bash
# AXIA D06: read an EXISTING Gazebo server crash core only.
# No simulation, motion, renderer override, installation, or retry.
set -Eeuo pipefail
umask 077
usage() {
  echo "usage: $0 --self-check | --core ABSOLUTE_CORE --exe ABSOLUTE_EXECUTABLE | --pid POSITIVE_COREDUMP_PID" >&2
}
if [[ "${1:-}" == --self-check && $# == 1 ]];then
  echo 'D06_WSLG_CORE_TRIAGE_L0_PASS_NO_GAZEBO_RUN'
  echo 'D06_GAZEBO_LIVE_RELEASE=HOLD CERTIFIED_ESTOP=false'
  exit 0
fi
mode="${1:-}"
core=''
exe=''
pid=''
case "$mode" in
  --core)
    [[ $# == 4 && "${3:-}" == --exe ]] || { usage;exit 2; }
    core="$2"; exe="$4"
    ;;
  --pid)
    [[ $# == 2 && "$2" =~ ^[0-9]+$ && "$2" != 0 ]] || { usage;exit 2; }
    pid="$2"
    ;;
  *) usage;exit 2;;
esac
echo 'D06_WSLG_CORE_TRIAGE_START EXISTING_CORE_ONLY NO_GAZEBO_RUN'
echo 'D06_GAZEBO_LIVE_RELEASE=HOLD CERTIFIED_ESTOP=false'
ROOT="${HOME:?}/axia_d06_g07_core_triage"
mkdir -p "$ROOT"
RUN="$(mktemp -d -p "$ROOT" 'core-XXXXXXXX')"
CORE_TEMP=''
finish(){
  local prior=$?
  trap - EXIT
  set +e
  [[ -z "$CORE_TEMP" ]] || rm -f -- "$CORE_TEMP"
  # core_not_archived: never place crash memory inside the compact evidence.
  printf 'core_not_archived=true\n' >> "$RUN/summary.txt"
  local archive="$ROOT/$(basename "$RUN").tar.gz"
  (cd "$RUN" && tar -czf "$archive" summary.txt preflight.txt gdb_backtrace.log)
  sha256sum "$archive" > "$archive.sha256"
  echo "D06_WSLG_CORE_TRIAGE_ARCHIVE=$archive"
  echo "D06_WSLG_CORE_TRIAGE_SHA256=$archive.sha256"
  echo 'D06_GAZEBO_SIGSEGV_ROOT_CAUSE=UNCONFIRMED'
  echo 'D06_GAZEBO_LIVE_RELEASE=HOLD CERTIFIED_ESTOP=false'
  exit "$prior"
}
: > "$RUN/summary.txt"
: > "$RUN/preflight.txt"
: > "$RUN/gdb_backtrace.log"
trap finish EXIT
{
  echo "core_pattern=$(cat /proc/sys/kernel/core_pattern 2>/dev/null || echo unavailable)"
  echo "ulimit_core=$(ulimit -c)"
  command -v gdb || true
  command -v coredumpctl || true
} > "$RUN/preflight.txt"
if [[ "$mode" == --pid ]];then
  if ! command -v coredumpctl >/dev/null 2>&1;then
    echo 'D06_WSLG_CORE_TRIAGE_HOLD COREDUMPCTL_UNAVAILABLE';exit 3
  fi
  coredumpctl --no-pager info "$pid" > "$RUN/coredump_info_private.tmp" 2>&1 || {
    echo 'D06_WSLG_CORE_TRIAGE_HOLD MATCHING_COREDUMP_UNAVAILABLE';exit 3;
  }
  # Derive the real executable from the existing core record, never guess
  # that the gz CLI wrapper is the same binary as the crashed server process.
  exe="$(sed -n 's/^[[:space:]]*Executable:[[:space:]]*//p' "$RUN/coredump_info_private.tmp" | head -1)"
  if [[ "$exe" != /* || ! -f "$exe" ]];then
    rm -f "$RUN/coredump_info_private.tmp"
    echo 'D06_WSLG_CORE_TRIAGE_HOLD CORE_EXECUTABLE_UNAVAILABLE';exit 3
  fi
  CORE_TEMP="$RUN/private.core"
  if ! timeout 30s coredumpctl dump "$pid" --output="$CORE_TEMP" >/dev/null 2>&1;then
    rm -f "$RUN/coredump_info_private.tmp"
    echo 'D06_WSLG_CORE_TRIAGE_HOLD COREDUMP_EXPORT_FAILED';exit 3
  fi
  core="$CORE_TEMP"
  rm -f "$RUN/coredump_info_private.tmp"
fi
if [[ "$core" != /* || "$exe" != /* || ! -f "$core" || ! -f "$exe" ]];then
  echo 'D06_WSLG_CORE_TRIAGE_HOLD VALID_EXISTING_CORE_AND_EXECUTABLE_REQUIRED'
  exit 3
fi
if ! command -v gdb >/dev/null 2>&1;then
  echo 'D06_WSLG_CORE_TRIAGE_HOLD GDB_NOT_INSTALLED_NO_AUTO_INSTALL'
  exit 3
fi
# GDB runs in batch only on the existing core; it starts no target process.
# SIGSEGV is the *first fatal signal* in the core, not an inferred driver cause.
timeout 45s gdb -nx -q -batch \
  -ex 'set pagination off' -ex 'set confirm off' \
  -ex 'info threads' -ex 'thread apply all bt 15' \
  -ex 'info sharedlibrary' -ex 'info proc mappings' \
  -- "$exe" "$core" > "$RUN/gdb_backtrace.log" 2>&1 || true
# Keep at most the first 160 KiB of text. The full core stays at its owner path
# (or is removed if temporarily exported from coredumpctl).
head -c 163840 "$RUN/gdb_backtrace.log" > "$RUN/gdb_truncated.tmp"
mv "$RUN/gdb_truncated.tmp" "$RUN/gdb_backtrace.log"
if grep -Eq 'SIGSEGV|Segmentation fault' "$RUN/gdb_backtrace.log" &&
   grep -Eq '#0[[:space:]]' "$RUN/gdb_backtrace.log";then
  echo 'D06_WSLG_CORE_TRIAGE_STACK=CAPTURED' | tee -a "$RUN/summary.txt"
  if grep -Eq '__nptl_deallocate_tsd' "$RUN/gdb_backtrace.log" &&
     grep -Eq 'libd3d12core[.]so' "$RUN/gdb_backtrace.log";then
    echo 'D06_WSLG_CORE_TRIAGE_CANDIDATE=D3D12_TLS_DESTRUCTOR_STACK_NEEDS_REVIEW' | tee -a "$RUN/summary.txt"
  elif grep -Eq 'GpuLidarSensor|RenderThread|Ogre' "$RUN/gdb_backtrace.log";then
    echo 'D06_WSLG_CORE_TRIAGE_CANDIDATE=GAZEBO_RENDER_THREAD_STACK_NEEDS_REVIEW' | tee -a "$RUN/summary.txt"
  else
    echo 'D06_WSLG_CORE_TRIAGE_CANDIDATE=UNCLASSIFIED_STACK_NEEDS_REVIEW' | tee -a "$RUN/summary.txt"
  fi
else
  echo 'D06_WSLG_CORE_TRIAGE_HOLD SIGSEGV_FIRST_FRAME_NOT_CAPTURED' | tee -a "$RUN/summary.txt"
  exit 3
fi
echo 'D06_WSLG_CORE_TRIAGE_HOLD CORE_STACK_REVIEW_REQUIRED ROOT_CAUSE=UNCONFIRMED'
exit 0
