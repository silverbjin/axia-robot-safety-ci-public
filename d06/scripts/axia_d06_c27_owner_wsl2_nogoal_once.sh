#!/usr/bin/env bash
# C27: one immutable student NO_GOAL Gazebo native-exit drain trial on WSL2.
# --compact-only never starts ROS/Gazebo; preserve originals locally.
set -Eeuo pipefail
umask 077
MODE="${1:---self-check}"
if [[ "$MODE" == --self-check && $# == 1 ]];then
  echo 'D06_C27_OWNER_L0_PASS_NO_ROS_NO_GAZEBO_NO_GOAL'
  echo 'D06_C27_REAL_WSL2_NOT_TESTED'
  echo 'AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false'
  exit 0
fi
[[ ( "$MODE" == --compact-only && $# == 2 ) ||
   ( "$MODE" == --run && $# == 1 ) ]] || {
  echo 'D06_C27_USAGE=--self-check|--compact-only ABS_RAW_TAR_GZ|--run' >&2
  exit 2
}
COMPACT_ROOT="$HOME/axia_d06_c27_compact"
if [[ "$MODE" == --compact-only ]];then
  ARCHIVE="$2"
  [[ "$ARCHIVE" == /* && -s "$ARCHIVE" && -s "$ARCHIVE.sha256" ]] || {
    echo 'D06_C27_COMPACT_MISSING_RAW_AND_SHA256' >&2;exit 3;
  }
  sha256sum -c --status "$ARCHIVE.sha256" || {
    echo 'D06_C27_COMPACT_RAW_SHA256_MISMATCH' >&2;exit 3;
  }
  mkdir -p "$COMPACT_ROOT"; chmod 700 "$COMPACT_ROOT"
  DEST="$COMPACT_ROOT/compact-$(date -u +%Y%m%dT%H%M%SZ)-$$.tar.gz"
  python3 - "$ARCHIVE" "$DEST" <<'PY'
import io,json,re,sys,tarfile
from pathlib import Path
source,dest=map(Path,sys.argv[1:])
# Only small bounded text files. Exclude full bag, core, credentials and raw sensor data.
wanted = {
  "launch.log":("launch_tail.log",100000),
  "owner_no_goal.log":("owner_log_tail.log",16000),
  "g07_ordered_shutdown.log":("ordered_shutdown_log_tail.log",16000),
  "g07_ordered_shutdown.json":("ordered_shutdown.json",18000),
  "g07_shutdown_audit.json":("cm_shutdown_audit.json",18000),
  "g07_gz_server_stop.log":("gz_server_stop.log",8000),
  "g07_gz_world_pause.log":("gz_world_pause.log",8000),
  "g07_wslg_sensor_truth.json":("sensor_truth.json",30000),
  "d06_g07_scan_delivery_layer.json":("scan_delivery.json",30000),
  "teardown.txt":("teardown.txt",6000),
  "renderer.txt":("renderer.txt",6000),
}
selected={}
with tarfile.open(source,"r:gz") as src:
  for m in src:
    if not m.isfile() or m.size<0:continue
    parts=Path(m.name).parts
    if len(parts)<2:continue
    key=parts[-1]
    if key not in wanted:continue
    # Only launch.log may be larger than the small-text limit. Read the
    # ENTIRE bounded native log before selecting EOF. Prior C27 selected
    # the tail of its FIRST 100KB, truncating the actual process exit.
    if m.size>(32000000 if key=="launch.log" else 5000000):continue
    # Do not follow symbolic links, no extraction to filesystem.
    fh=src.extractfile(m)
    if fh is None:continue
    if key=="launch.log":
      text=fh.read(m.size).decode("utf-8","replace")
      lines=text.splitlines()
      data="\n".join(lines[-400:]).encode("utf-8")[-wanted[key][1]:]
      # Include bounded child-exit proof even if more log lines follow.
      exits=[l for l in lines if re.search(
          r"^\[(?:INFO|ERROR)\]\s+\[gz-\d+\]: process has "
          r"(?:died|finished cleanly)",l)]
      selected["native_gazebo_exit_events.log"]=(
          "\n".join(exits[-12:])+"\n").encode("utf-8")[-6000:]
    elif key in ("owner_no_goal.log","g07_ordered_shutdown.log"):
      data=fh.read(m.size)[-wanted[key][1]:]
    else:data=fh.read(min(m.size,wanted[key][1]))
    selected[wanted[key][0]]=data
if "launch_tail.log" not in selected:
  raise SystemExit("D06_C28_COMPACT_LAUNCH_EOF_NOT_RECOVERABLE_HOLD")
exit_evidence=selected.get("native_gazebo_exit_events.log",b"")
has_clean=bool(re.search(rb"(?m)^\[INFO\]\s+\[gz-\d+\]: process has finished cleanly",exit_evidence))
has_died=bool(re.search(rb"(?m)^\[ERROR\]\s+\[gz-\d+\]: process has died",exit_evidence))
def data_obj(name):
  try:return json.loads(selected.get(name,b"{}").decode("utf-8"))
  except (ValueError,UnicodeError):return {}
sensor=data_obj("sensor_truth.json")
nav=data_obj("ordered_shutdown.json")
cm=data_obj("cm_shutdown_audit.json")
# Cross-topic indices cannot be compared; use SAME host-monotonic clock.
first_candidates=[]
unknown_scan=False
for topic in ("raw","safety"):
  metrics=sensor.get("metrics",{}).get(topic,{})
  if metrics.get("first_receipt_ttl_breach_at_index") is None:
    continue
  witness=sensor.get("scan_receipts_compact",{}).get(topic,{})
  start=witness.get("before",{}).get("host_monotonic_sec")
  if type(start) in (int,float):
    first_candidates.append((start,topic))
  else: unknown_scan=True
first_failure=(
  min(first_candidates)[1].upper()+"_SCAN_RECEIPT_TTL_300MS"
  if first_candidates and not unknown_scan else
  "SCAN_RECEIPT_TTL_300MS_UNORDERED" if first_candidates or unknown_scan
  else "NOT_OBSERVED_IN_COMPACT")
forced_teardown=b"P2_L2_FORCED_TEARDOWN" in selected.get("teardown.txt",b"")
status={"scope":"NO_GOAL_OWNER_NATIVE_EXIT_DIAGNOSTIC",
        "native_gz_exit0_marker":has_clean,"native_gz_died_marker":has_died,
        "first_failure":first_failure,
        "navigation_service_status":nav.get("navigation_service_status","NOT_OBSERVED"),
        "navigation_ack":nav.get("navigation_ack"),
        "localization_ack":nav.get("localization_ack"),
        "cm_exit_code":cm.get("cm_exit_code"),
        "forced_teardown":forced_teardown,
        "release_authorized":False,
        "gazebo_crash_root_cause":"UNCONFIRMED",
        "core_not_archived":True,"raw_archive_retained_locally":True,
        "axia_mvp_demo_accepted":"HOLD","certified_estop":False}
selected["summary.txt"]=(json.dumps(status,sort_keys=True)+"\ncore_not_archived=true\n").encode()
with tarfile.open(dest,"w:gz") as out:
  for name,data in sorted(selected.items()):
    entry=tarfile.TarInfo(name); entry.mode=0o600;entry.size=len(data)
    out.addfile(entry,io.BytesIO(data))
print("D06_C27_COMPACT_GZ_EXIT0_MARKER="+str(has_clean).lower())
print("D06_C27_COMPACT_GZ_DIED_MARKER="+str(has_died).lower())
print("D06_C28_FIRST_FAILURE="+first_failure)
print("D06_C28_EOF_BOUNDARY_PRESERVED_NO_SIM")
if forced_teardown and "SCAN_RECEIPT_TTL_300MS" in first_failure:
  print("D06_C28_FORCED_TEARDOWN_AND_SCAN_TTL_HOLD")
PY
  sha256sum "$DEST" > "$DEST.sha256"
  echo "D06_C27_COMPACT_ARCHIVE=$DEST"
  echo "D06_C27_COMPACT_SHA256=$DEST.sha256"
  echo 'D06_C27_COMPACT_ONLY_NO_GAZEBO_RUN'
  echo 'AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false'
  exit 0
fi
[[ "$MODE" == --run && $# == 1 ]] || exit 2
[[ "${GITHUB_ACTIONS:-false}" != true && -n "${DISPLAY:-}" ]] || {
  echo 'D06_C27_OWNER_WSL2_REQUIRED_NO_SIM' >&2;exit 3;
}
grep -qiE 'microsoft|wsl' /proc/sys/kernel/osrelease || {
  echo 'D06_C27_OWNER_WSL2_KERNEL_REQUIRED_NO_SIM' >&2;exit 3;
}
. /etc/os-release
[[ "${ID:-}" == ubuntu && "${VERSION_ID:-}" == 24.04 ]] || {
  echo 'D06_C27_OWNER_UBUNTU2404_REQUIRED_NO_SIM' >&2;exit 3;
}
for exe in curl git python3 tar sha256sum glxinfo timeout;do
  command -v "$exe" >/dev/null || { echo "D06_C27_MISSING_TOOL=$exe" >&2;exit 3; }
done
export MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA
if ! glxinfo -B | grep -Eiq 'OpenGL renderer string:.*D3D12.*NVIDIA';then
  echo 'D06_C27_NVIDIA_D3D12_PREFLIGHT_FAILED_NO_SIM' >&2;exit 3;
fi
PIN='aa1dc0eae2db6903389a24bf92e9370624e3117d'
BLOB='73ed5d3965361d3230cd7df5ceafaf590d9e4e5e'
TMP="$(mktemp --suffix=.sh)"
trap 'rm -f -- "$TMP"' EXIT
curl -fLsS --retry 3 --max-time 90 \
  "https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public/$PIN/d06/scripts/axia_d06_g07_wslg_sensor_no_goal_once.sh" \
  -o "$TMP"
[[ "$(git hash-object "$TMP")" == "$BLOB" ]] || {
  echo 'D06_C27_OWNER_BLOB_MISMATCH_NO_SIM' >&2;exit 3;
}
bash -n "$TMP"
AXIA_D06_GAZEBO_C27_CANDIDATE=1 bash "$TMP" --self-check
RUN_ROOT="$HOME/axia_d06_c27_owner_evidence"
mkdir -p "$RUN_ROOT";chmod 700 "$RUN_ROOT"
RUN="$(mktemp -d -p "$RUN_ROOT" owner-XXXXXXXX)"
export AXIA_D06_SENSOR_EVIDENCE_ROOT="$RUN/raw"
mkdir -p "$AXIA_D06_SENSOR_EVIDENCE_ROOT"
OWNER_RC=0
# One bounded NO_GOAL trial only: same NVIDIA adapter, no Goal/Fault/Twist.
AXIA_D06_GAZEBO_C27_CANDIDATE=1 AXIA_D06_G07_RX_WITNESS=1 \
  timeout --signal=TERM --kill-after=10s 960s bash "$TMP" --run \
    > "$RUN/owner.log" 2>&1 || OWNER_RC=$?
echo "D06_C27_OWNER_RC=$OWNER_RC"
raw="$(sed -n 's/^D06_WSLG_NO_GOAL_RAW_ARCHIVE=//p' "$RUN/owner.log" | tail -1)"
if [[ -z "$raw" || ! -s "$raw" || ! -s "$raw.sha256" ]];then
  tail -n 55 "$RUN/owner.log" || true
  echo 'D06_C27_OWNER_RAW_EVIDENCE_MISSING_HOLD' >&2
  exit 3
fi
bash "$0" --compact-only "$raw"
# The native Gazebo exit0 marker is mandatory even if Owner returns rc0.
# Parent teardown / service ACK and scan candidate are never a substitute.
set +e
python3 - "$raw" "$OWNER_RC" <<'PY'
import json,re,sys,tarfile
raw,owner_rc=sys.argv[1:]
with tarfile.open(raw,"r:gz") as tf:
    def get(name):
      match=[m for m in tf.getmembers() if m.isfile() and m.name.endswith("/native/"+name)]
      if len(match)!=1 or match[0].size>5000000:raise ValueError(name)
      return tf.extractfile(match[0]).read().decode("utf-8","replace")
    log=get("launch.log")
    nav=json.loads(get("g07_ordered_shutdown.json"))
    audit=json.loads(get("g07_shutdown_audit.json"))
    sensor=json.loads(get("g07_wslg_sensor_truth.json"))
gazebo_exit0=bool(re.search(r"(?m)^\[INFO\]\s+\[gz-\d+\]: process has finished cleanly",log))
gazebo_died=bool(re.search(r"(?m)^\[ERROR\]\s+\[gz-\d+\]: process has died",log))
ok=(owner_rc=="0" and gazebo_exit0 and not gazebo_died
    and nav.get("navigation_ack") is True and nav.get("localization_ack") is True
    and audit.get("cm_exit_code")==0
    and sensor.get("goal_sent") is False and sensor.get("fixture_moved") is False
    and sensor.get("status")=="NO_GOAL_SENSOR_WINDOW_CLEAR_CANDIDATE")
print("D06_C27_OWNER_GZ_NATIVE_EXIT0="+str(gazebo_exit0).lower())
print("D06_C27_OWNER_GZ_NATIVE_DIED="+str(gazebo_died).lower())
print("D06_C27_OWNER_NAV2_ACK="+str(nav.get("navigation_ack") is True and nav.get("localization_ack") is True).lower())
print("D06_C27_OWNER_CM_EXIT0="+str(audit.get("cm_exit_code")==0).lower())
print("D06_C27_OWNER_NO_GOAL_NATIVE_CANDIDATE="+str(ok).lower())
sys.exit(0 if ok else 3)
PY
GATE_RC=$?
set -e
echo 'D06_C27_OWNER_WSL2_NO_GOAL_NOT_ACCEPTED'
echo 'AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false'
[[ "$GATE_RC" == 0 ]] || exit 3
exit 0
