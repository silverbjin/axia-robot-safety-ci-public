#!/usr/bin/env bash
# AXIA G07 CV2U3T4v — one read-only CPU scheduling probe + exactly one
# ORIGINAL pinned Owner WSL2 Gazebo Moving Goal attempt.
# Never changes ROS safety TTL, renderer, WSL settings, CPU priority, or Goal.
set -Eeuo pipefail
umask 077

readonly OWNER_SHA='cd8c23c52588f5efd6295b6904e15b1aa54496e7'
readonly OWNER_PATH='scripts/axia_g07_task04_owner_moving_l3_once.sh'
readonly PUBLIC='https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public'
readonly PROBE_REF="${AXIA_G07_CV2_PROBE_REF:-}"
MODE="${1:---self-check}"
if [[ ! "$PROBE_REF" =~ ^[0-9a-f]{40}$ ]];then
  echo 'AXIA_G07_CV2_DIAGNOSTIC_PIN_SHA_REQUIRED' >&2;exit 2
fi
case "$MODE" in --run|--self-check) ;; *)
  echo 'AXIA_G07_CV2_BAD_ARGUMENT' >&2;exit 2 ;;
esac
for cmd in curl bash python3 sha256sum mktemp;do
  command -v "$cmd" >/dev/null || {
    echo "AXIA_G07_CV2_MISSING_COMMAND_$cmd" >&2;exit 2;
  }
done
TMP="$(mktemp -d)"
GUEST_PID=''
HOST_PID=''
STOP=''
cleanup(){
  if [[ -n "$STOP" ]];then touch "$STOP" 2>/dev/null || true;fi
  if [[ -n "$GUEST_PID" ]];then
    if kill -0 "$GUEST_PID" 2>/dev/null;then
      sleep .25;kill -TERM "$GUEST_PID" 2>/dev/null || true
    fi
    wait "$GUEST_PID" 2>/dev/null || true
  fi
  if [[ -n "$HOST_PID" ]];then
    if kill -0 "$HOST_PID" 2>/dev/null;then
      sleep .25;kill -TERM "$HOST_PID" 2>/dev/null || true
    fi
    wait "$HOST_PID" 2>/dev/null || true
  fi
  rm -rf -- "$TMP"
}
trap cleanup EXIT
fetch_exact(){
  local ref="$1" rel="$2" dst="$3"
  curl -fLsS --retry 3 --max-time 90 \
     "$PUBLIC/$ref/$rel" -o "$dst"
  test -s "$dst"
}
fetch_exact "$PROBE_REF" scripts/axia_g07_wsl2_sched_probe.py "$TMP/guest_probe.py"
fetch_exact "$PROBE_REF" scripts/axia_g07_windows_host_cpu_probe.ps1 "$TMP/windows_probe.ps1"
fetch_exact "$OWNER_SHA" "$OWNER_PATH" "$TMP/owner_once.sh"
python3 "$TMP/guest_probe.py" selftest
bash -n "$TMP/owner_once.sh"
bash "$TMP/owner_once.sh" --self-check
if [[ "$MODE" == --self-check ]];then
  echo "AXIA_G07_CV2_PROBE_L0_PASS_NO_ROS_NO_GAZEBO_NO_GOAL probe=$PROBE_REF owner=$OWNER_SHA"
  exit 0
fi

# Same original Owner scenario; nothing bypasses its physical TTY approval.
if [[ ! -t 0 || ! -r /dev/tty ]];then
  echo 'AXIA_G07_CV2_OWNER_CONTROLLING_TTY_REQUIRED' >&2;exit 2
fi
if ! grep -Eiq 'microsoft|wsl' /proc/sys/kernel/osrelease;then
  echo 'AXIA_G07_CV2_WSL2_REQUIRED' >&2;exit 2
fi
BASE="$HOME/axia_g07_task04_owner_moving"
mkdir -p "$BASE"
chmod 700 "$BASE"
OUT="$(mktemp -d "$BASE/probe-CV2-XXXXXXXX")"
chmod 700 "$OUT"
STOP="$OUT/probe.stop"
printf 'probe_ref=%s\nowner_sha=%s\nmonitor_interval_ms=40\n' \
  "$PROBE_REF" "$OWNER_SHA" > "$OUT/probe_manifest.txt"
{
  date --iso-8601=seconds || true
  uname -a || true
  cat /proc/sys/kernel/osrelease || true
  nproc || true
  grep -E '^MemTotal:|^SwapTotal:|^MemAvailable:' /proc/meminfo || true
  head -n 1 /proc/stat || true
  cat /proc/pressure/cpu /proc/pressure/memory 2>/dev/null || true
  cat /proc/sys/kernel/sched_schedstats 2>/dev/null || true
  cat /proc/sys/kernel/sched_autogroup_enabled 2>/dev/null || true
} > "$OUT/environment_guest.txt"
echo "AXIA_G07_CV2_DIAGNOSTIC_OUT=$OUT"
echo 'AXIA_G07_CV2_SAFETY_TTLS_UNCHANGED=true'
echo 'AXIA_G07_CV2_ORIGINAL_OWNER_SAME_SCENARIO_SINGLE_ATTEMPT=true'
echo 'AXIA_G07_CV2_WINDOWS_CPU_MONITOR_STARTING_IF_WSL_INTEROP_AVAILABLE'

PYTHONDONTWRITEBYTECODE=1 python3 "$TMP/guest_probe.py" monitor \
  --output "$OUT/guest_scheduler.jsonl" --stop "$STOP" --interval-ms 40 \
  > "$OUT/guest_monitor.log" 2>&1 &
GUEST_PID=$!
sleep .15
if ! kill -0 "$GUEST_PID" 2>/dev/null;then
  echo 'AXIA_G07_CV2_GUEST_MONITOR_START_FAILED' >&2;exit 3
fi
echo "AXIA_G07_CV2_GUEST_MONITOR_PID=$GUEST_PID"

if command -v powershell.exe >/dev/null 2>&1 && command -v wslpath >/dev/null 2>&1;then
  PS_WIN="$(wslpath -w "$TMP/windows_probe.ps1" 2>/dev/null || true)"
  OUT_WIN="$(wslpath -w "$OUT/windows_host.jsonl" 2>/dev/null || true)"
  STOP_WIN="$(wslpath -w "$STOP" 2>/dev/null || true)"
  if [[ -n "$PS_WIN" && -n "$OUT_WIN" && -n "$STOP_WIN" ]];then
    powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass \
      -File "$PS_WIN" -OutputPath "$OUT_WIN" -StopPath "$STOP_WIN" \
      -IntervalMs 150 > "$OUT/windows_monitor.log" 2>&1 &
    HOST_PID=$!
    echo "AXIA_G07_CV2_WINDOWS_HOST_MONITOR_ATTEMPTED_PID=$HOST_PID"
  else
    echo 'AXIA_G07_CV2_WINDOWS_HOST_MONITOR_UNAVAILABLE_WSLPATH'
  fi
else
  echo 'AXIA_G07_CV2_WINDOWS_HOST_MONITOR_UNAVAILABLE_INTEROP'
fi

# Do not spend the *single* Owner Gazebo attempt with no independent host
# metrics: Windows/WSL UNC and PowerShell interop must prove working first.
HOST_READY=0
for ((i=0;i<40;i++));do
  if [[ -s "$OUT/windows_host.jsonl" ]];then HOST_READY=1;break;fi
  if [[ -z "$HOST_PID" ]] || ! kill -0 "$HOST_PID" 2>/dev/null;then break;fi
  sleep .2
done
if [[ "$HOST_READY" != 1 ]];then
  echo 'AXIA_G07_CV2_HOST_SAMPLER_PRECHECK_FAILED_NO_OWNER_RUN' >&2
  tail -n 15 "$OUT/windows_monitor.log" 2>/dev/null || true
  echo "AXIA_G07_CV2_PRECHECK_LOGS=$OUT"
  exit 3
fi
echo 'AXIA_G07_CV2_WINDOWS_HOST_MONITOR_READY'

# Run exactly ONE unchanged pinned Owner scenario; the manual /dev/tty read
# stays in the original Owner script even while stdout is privately tee'd.
set +e
bash "$TMP/owner_once.sh" --run 2>&1 | tee "$OUT/owner_console.log"
OWNER_RC="${PIPESTATUS[0]}"
set -e

touch "$STOP"
sleep .35
if [[ -n "$GUEST_PID" ]];then wait "$GUEST_PID" 2>/dev/null || true;GUEST_PID='';fi
if [[ -n "$HOST_PID" ]];then
  if kill -0 "$HOST_PID" 2>/dev/null;then
    sleep .25;kill -TERM "$HOST_PID" 2>/dev/null || true
  fi
  wait "$HOST_PID" 2>/dev/null || true
  HOST_PID=''
fi
echo "owner_exit_code=$OWNER_RC" >> "$OUT/probe_manifest.txt"
python3 "$TMP/guest_probe.py" analyze \
  --guest "$OUT/guest_scheduler.jsonl" \
  --host "$OUT/windows_host.jsonl" \
  --owner-console "$OUT/owner_console.log" \
  --output "$OUT/cv2_sched_summary.json" \
  > "$OUT/analysis_console.log" 2>&1 || echo 'AXIA_G07_CV2_ANALYZE_FAILED_REVIEW_RAW'
cat "$OUT/analysis_console.log"
# Never auto-upload Owner evidence or host details. Probe zip is only local.
python3 - "$OUT" "$OUT.diagnostics.zip" <<'PY_ZIP'
import sys,zipfile
from pathlib import Path
root=Path(sys.argv[1]);dest=Path(sys.argv[2])
allowed=['probe_manifest.txt','environment_guest.txt','guest_scheduler.jsonl',
         'guest_monitor.log','windows_host.jsonl','windows_monitor.log',
         'owner_console.log','cv2_sched_summary.json','analysis_console.log']
with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for name in allowed:
        p=root/name
        if p.is_file():z.write(p,name)
print('AXIA_G07_CV2_DIAGNOSTICS_ZIP_CREATED',flush=True)
PY_ZIP
sha256sum "$OUT.diagnostics.zip" > "$OUT.diagnostics.zip.sha256"
echo "AXIA_G07_CV2_DIAGNOSTICS_ZIP=$OUT.diagnostics.zip"
echo "AXIA_G07_CV2_DIAGNOSTICS_SHA256=$OUT.diagnostics.zip.sha256"
echo "AXIA_G07_CV2_OWNER_EXIT_CODE=$OWNER_RC"
echo 'AXIA_G07_CV2_HYPERVISOR_CPU_PREEMPTION=UNVERIFIED_PENDING_CORRELATION'
echo 'AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false'
exit "$OWNER_RC"
