#!/usr/bin/env bash
# One bounded GPU A/B experiment, exactly 1 NO_GOAL session per adapter.
set -Eeuo pipefail
umask 077
MODE=--compare
if [[ $# -gt 0 ]]; then MODE="$1";fi
[[ $# -le 1 && ( "$MODE" == --compare || "$MODE" == --nvidia-only || "$MODE" == --nvidia-causal || "$MODE" == --analyze-existing || "$MODE" == --self-check ) ]] || exit 2
# Reuse the D08 Owner-proven NVIDIA WSLg profile as one isolated
# NO_GOAL diagnostic; do not repeat the historically failed Intel run.
adapters=(NVIDIA Intel)
if [[ "$MODE" == --nvidia-only || "$MODE" == --nvidia-causal ]];then
  adapters=(NVIDIA)
  echo 'D06_GPU_RTF_NVIDIA_ONLY_NO_GOAL OWNER_L3_NOT_ACCEPTED'
fi
readonly OWNER_SHA='6033d7d68efb6324699780fe9de68b9fcefee78f'
readonly OWNER_BLOB='18f6b3d73951fbd95a05eb4f59dbc1a19e2a5fa3'
readonly ANALYZER_SHA='615bcd81b8f74a478daa2baeaf9f27ca02c94f11'
readonly ANALYZER_BLOB='171aad7ce8abe97c93a42f19787042619c06b65e'
readonly STUDENT_SHA='e4c2007064bec2103bb743bd27cdbdf0955961b7'
echo "AXIA_D06_GPU_RTF_PINNED_STUDENT=$STUDENT_SHA NO_GOAL_ONLY"
if [[ "$MODE" == --self-check ]];then
  echo 'D06_GPU_RTF_STATIC_PASS NO_ROS_NO_GAZEBO_NO_GOAL'
  echo 'D06_GAZEBO_LIVE_RELEASE=HOLD CERTIFIED_ESTOP=false'
  exit 0
fi
# Both --analyze-existing and future run failures produce ONE small archive.
# No ROS/Gazebo launched in --analyze-existing.
ROOT="${HOME:-/nonexistent}/axia_d06_g07_gpu_rtf_evidence"
collect_and_package() {
  local d="$1" origin="${2:-FUTURE_RUN_SAME_SESSION}" archive
  [[ -d "$d" ]] || return 3
  mkdir -p "$d/forensic"
  python3 - "$d" "$origin" "$STUDENT_SHA" <<'PY'
import hashlib
import json
import re
import sys
from pathlib import Path

base=Path(sys.argv[1]); origin=sys.argv[2]; sha=sys.argv[3]
out=base/"forensic";out.mkdir(parents=True,exist_ok=True)
def read(name):
    file=base/name
    return file.read_text(encoding="utf-8",errors="replace").splitlines() if file.is_file() else []
def excerpt(rows,points,before=5,after=8):
    ids=set()
    for i in points[:12]:
        ids.update(range(max(0,i-before),min(len(rows),i+after+1)))
    return "\n".join(f"{i+1}: {rows[i][:1400]}" for i in sorted(ids)[:170])+"\n"
try:
    report=json.loads((base/"nvidia.g07_wslg_sensor_truth.json").read_text(encoding="utf-8"))
except (OSError,ValueError):
    report={}
reasons=report.get("reasons",[])
if not isinstance(reasons,list):reasons=[]
first=next((v for v in reasons if isinstance(v,str)),"EVIDENCE_INCOMPLETE")
log=read("nvidia.launch.log")
stop=next((i for i,row in enumerate(log) if "Robot to stop due to" in row or "AXIA_StopFront polygon" in row),None)
timing=next((i for i,row in enumerate(log) if "SCAN_TIMEOUT" in row or "HEALTH_BAD_DIAGNOSTIC" in row),None)
crash=[i for i,row in enumerate(log) if re.search(r"exit code -11|SIGSEGV|Segmentation fault",row,re.I)]
signals=[i for i,row in enumerate(log) if re.search(r"SIGINT|SIGTERM|Sending signal",row,re.I)]
crashes=[]
if any(re.search(r"\[collision_monitor-\d+\].*exit code -11",log[i]) for i in crash):crashes.append("collision_monitor")
if any(re.search(r"\[gz-\d+\].*exit code -11",log[i]) for i in crash):crashes.append("gazebo_server")
(out/"first_stop_and_timing.txt").write_text("First safety STOP and first timing warning (log line numbers)\n"+
    excerpt(log,([stop] if stop is not None else [])+([timing] if timing is not None else [])),encoding="utf-8")
(out/"shutdown_context.txt").write_text("Signals and actual native child exits (log line numbers)\n"+
    excerpt(log,signals[:2]+crash[:8],before=8,after=12),encoding="utf-8")
summary={
 "schema":"axia.d06.g07.compact_forensics.v1",
 "source":origin,"student_sha":sha,"first_sensor_failure":first,
 "all_sensor_reasons":reasons,"sensor_status":report.get("status","UNMEASURED"),
 "rtf_diagnostics":report.get("rtf_diagnostics",{}),
 "raw":report.get("metrics",{}).get("raw",{}),
 "safety":report.get("metrics",{}).get("safety",{}),
 "raw_first_gap_diagnostics":report.get("raw_first_gap_diagnostics",{}),
 "first_stop_log_line":None if stop is None else stop+1,
 "first_timeout_log_line":None if timing is None else timing+1,
 "first_native_crash_log_line":None if not crash else crash[0]+1,
 "process_crashes":crashes,
 "goal_sent":report.get("goal_sent","UNVERIFIED"),
 "fixture_moved":report.get("fixture_moved","UNVERIFIED"),
 "certified_estop":False,"moving_l3_accepted":False,
 "raw_archive_embedded":False,
 "first_scan_host_receipt_trace_available":bool(report.get("scan_receipts_compact"))
}
(out/"summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")
if report.get("scan_receipts_compact"):
    (out/"scan_receipts_compact.json").write_text(json.dumps(report["scan_receipts_compact"])+"\n",encoding="utf-8")
owner=read("nvidia.run.log")
# Reuse original immutable Owner TAR: only small proven-relevant native
# clock, graph, GUI and teardown files, never a second Gazebo execution.
import tarfile
source_archive=next((row.partition("=")[2] for row in reversed(owner)
                     if row.startswith("D06_WSLG_NO_GOAL_RAW_ARCHIVE=")),None)
native_verified=False
if source_archive:
    src=Path(source_archive)
    digest_file=Path(source_archive+".sha256")
    try:
        digest=digest_file.read_text(encoding="utf-8").split()[0]
        if (re.fullmatch(r"[0-9a-fA-F]{64}",digest)
            and src.is_file() and src.stat().st_size <= 8*1024*1024
            and hashlib.sha256(src.read_bytes()).hexdigest().lower()==digest.lower()):
            native_verified=True
            desired={
                "clock_diagnostics.json":("native_clock_diagnostics.json",12000),
                "p2_graph_diagnostics.json":("native_p2_graph_diagnostics.json",20000),
                "startup_verdict.json":("native_startup_verdict.json",25000),
                "task04_rviz.log":("rviz",30000),
                "task04_gazebo_gui.log":("gazebo_gui",30000),
                "teardown.txt":("native_teardown_marker.txt",5000),
                # Exactly the D08 native/ROS receiver stamps for same-session
                # correlation; bounded traces, no giant ROS logs or SDF.
                "d06_g07_scan_delivery_layer.json":("d06_g07_scan_delivery_layer.json",25000),
                "d06_gz_scan_receipts.jsonl":("d06_gz_scan_receipts.jsonl",400000),
                "d06_ros_scan_receipts.jsonl":("d06_ros_scan_receipts.jsonl",800000),
                "d06_gz_clock_receipts.jsonl":("d06_gz_clock_receipts.jsonl",400000),
                "d06_gz_scan_rx.log":("gz_scan",12000),
                "d06_ros_scan_rx.log":("ros_scan",12000),
            }
            render_errors=[]
            with tarfile.open(src,"r:gz") as tg:
                for member in tg.getmembers():
                    if not member.isfile() or "/native/" not in member.name:continue
                    name=member.name.rsplit("/",1)[-1]
                    if name not in desired or member.size>desired[name][1]:continue
                    fileobj=tg.extractfile(member)
                    if not fileobj:continue
                    payload=fileobj.read(member.size+1)
                    if len(payload)>desired[name][1]:continue
                    value=payload.decode("utf-8",errors="replace")
                    dest=desired[name][0]
                    if dest in ("rviz","gazebo_gui","gz_scan","ros_scan"):
                        selected=[x[:700] for x in value.splitlines()
                                  if re.search(r"error|exception|shader|GLSL|render|OpenGL|D3D12|"
                                               r"message filter|queue is full|ogre|EGL",x,re.I)]
                        render_errors.extend(["## "+name]+selected[:30])
                    elif name=="teardown.txt":
                        (out/dest).write_text(
                            value+"\nNOTE: marker does not prove child exit 0;"
                            " launch.log native -11 overrides it\n",encoding="utf-8")
                    else:
                        (out/dest).write_text(value,encoding="utf-8")
            (out/"native_render_errors_excerpt.txt").write_text(
                "\n".join(render_errors)+"\n",encoding="utf-8")
    except (OSError,ValueError,tarfile.TarError,IndexError):
        native_verified=False
summary["source_archive_sha256_verified"]=native_verified
layer_file=out/"d06_g07_scan_delivery_layer.json"
try:
    causal=json.loads(layer_file.read_text(encoding="utf-8")) if layer_file.exists() else {}
except (OSError,ValueError):
    causal={}
summary["same_session_native_ros_candidate"]=causal.get("candidate","NOT_MEASURED")
summary["source_pair_causality_proven"]=False
summary["native_transport_rx_observed"]=bool(causal.get("native_count",0)>0)
summary["ros_rx_observed"]=bool(causal.get("observer_raw_count",0)>0)
summary["no_goal_acceptance"]=False
(out/"summary.json").write_text(
    json.dumps(summary,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")
markers=re.compile("G07_WSLG_NO_GOAL_SENSOR_|AXIA_G07_WSLG_NO_GOAL_SENSOR_TRUTH|D06_WSLG_NO_GOAL_SENSOR_|D06_GAZEBO_LIVE_RELEASE|D06_WSLG_NO_GOAL_RAW_ARCHIVE|D06_G07_NATIVE|D06_G07_RX_WITNESS|D06_G07_FIRST_SCAN_TTL_HOLD")
(out/"owner_verdict_excerpt.txt").write_text("\n".join(
    f"{i+1}: {row[:3500]}" for i,row in enumerate(owner) if markers.search(row))[-30000:]+"\n",encoding="utf-8")
renderer=[]
for file in ("nvidia.preflight.txt","nvidia.renderer.txt","nvidia.ogre2_gl_evidence.txt"):
    relevant=[row[:500] for row in read(file) if re.search("GL_RENDERER|OpenGL renderer|GL_VENDOR|D3D12|llvmpipe|NVIDIA|Intel",row,re.I)]
    renderer.append("## "+file+"\n"+"\n".join(relevant[-12:]))
(out/"renderer_excerpt.txt").write_text("\n".join(renderer)+"\n",encoding="utf-8")
hashed=[]
for fn in ("nvidia.g07_wslg_sensor_truth.json","nvidia.launch.log","nvidia.run.log",
           "nvidia.g07_world.sdf.xacro","nvidia.g07_demo_waffle.sdf.xacro","nvidia.initialpose.json"):
    file=base/fn
    if file.is_file():hashed.append(hashlib.sha256(file.read_bytes()).hexdigest()+"  "+fn)
(out/"source_hashes.txt").write_text("SHA256 of original local evidence (not embedded)\n"+"\n".join(hashed)+"\n",encoding="utf-8")
print("D06_FORENSIC_FIRST_SENSOR_FAILURE="+first,flush=True)
print("D06_FORENSIC_PROCESS_CRASH="+(",".join(crashes) if crashes else "NONE_OBSERVED"),flush=True)
print("D06_FORENSIC_RTF="+str(report.get("rtf_diagnostics",{}).get("ros_clock_rtf","UNMEASURED")),flush=True)
print("D06_FORENSIC_SCOPE=NO_GOAL_MOVING_L3_HOLD",flush=True)
PY
  archive="$ROOT/d06-forensic-$(basename "$d").tar.gz"
  tar -C "$d" -czf "$archive" forensic
  sha256sum "$archive" > "$archive.sha256"
  echo "D06_FORENSIC_ARCHIVE=$archive"
  echo "D06_FORENSIC_SHA256=$archive.sha256"
}

if [[ "$MODE" == --analyze-existing ]];then
  for cmd in python3 tar sha256sum;do
    command -v "$cmd" >/dev/null || { echo D06_FORENSIC_TOOLS_MISSING >&2;exit 3; }
  done
  [[ -d "$ROOT" ]] || {
    echo D06_FORENSIC_EXISTING_EVIDENCE_MISSING_NO_GOAL >&2;exit 3;
  }
  RUN_DIR="$(python3 - "$ROOT" <<'PY'
import sys
from pathlib import Path
root=Path(sys.argv[1])
found=[p for p in root.glob("ab-no-goal-*") if p.is_dir()
       and (p/"nvidia.g07_wslg_sensor_truth.json").is_file()]
if found:print(max(found,key=lambda p:(p/"nvidia.g07_wslg_sensor_truth.json").stat().st_mtime))
PY
)"
  [[ -n "$RUN_DIR" ]] || {
    echo D06_FORENSIC_EXISTING_EVIDENCE_MISSING_NO_GOAL >&2;exit 3;
  }
  ROOT="$(cd "$ROOT" && pwd -P)"
  echo "D06_FORENSIC_EXISTING_NO_SIM_REPLAY=$RUN_DIR"
  collect_and_package "$RUN_DIR" EXISTING_LOCAL_EVIDENCE
  echo 'D06_GAZEBO_LIVE_RELEASE=HOLD CERTIFIED_ESTOP=false'
  exit 0
fi

[[ -n "$(printenv DISPLAY || :)" && "$(printenv GITHUB_ACTIONS || :)" != true ]] || {
  echo D06_GPU_RTF_REAL_WSLG_REQUIRED >&2;exit 3;
}
grep -qiE 'microsoft|wsl' /proc/sys/kernel/osrelease || exit 3
for cmd in curl git python3 glxinfo tar sha256sum cmp;do
  command -v "$cmd" >/dev/null || { echo "MISSING_EXECUTABLE=$cmd" >&2;exit 3; }
done
mkdir -p "$ROOT";chmod 700 "$ROOT"
ROOT="$(cd "$ROOT" && pwd -P)"
RUN_DIR="$(mktemp -d -p "$ROOT" ab-no-goal-XXXXXXXX)"
TMP="$(mktemp -d)"
cleanup() {
  local saved_rc=$?
  trap - EXIT
  # Never turn a failed sensor/teardown process into a success.
  collect_and_package "$RUN_DIR" FUTURE_RUN_SAME_SESSION ||
    echo 'D06_FORENSIC_BUNDLE_FAILED_OR_INCOMPLETE_NO_GOAL' >&2
  rm -rf -- "$TMP"
  exit "$saved_rc"
}
trap cleanup EXIT
# Preflight *actual* GPU selection before ever launching a robot.
for gpu in "${adapters[@]}";do
  MESA_D3D12_DEFAULT_ADAPTER_NAME="$gpu" glxinfo -B > "$RUN_DIR/$gpu.preflight.txt"
  grep -Ei "OpenGL renderer string:.*D3D12.*$gpu" "$RUN_DIR/$gpu.preflight.txt" >/dev/null || {
    echo "D06_GPU_RTF_D3D12_$gpu_UNAVAILABLE_NO_GOAL" >&2;exit 3;
  }
done
URL="https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public"
curl -fLsS --retry 3 --max-time 90 "$URL/$OWNER_SHA/d06/scripts/axia_d06_g07_wslg_sensor_no_goal_once.sh" -o "$TMP/owner.sh"
curl -fLsS --retry 3 --max-time 90 "$URL/$ANALYZER_SHA/d06/tools/axia_d06_lidar_rtf_compare.py" -o "$TMP/compare.py"
[[ "$(git hash-object "$TMP/owner.sh")" == "$OWNER_BLOB" && "$(git hash-object "$TMP/compare.py")" == "$ANALYZER_BLOB" ]] || {
  echo 'D06_GPU_RTF_SOURCE_BLOB_MISMATCH_NO_GOAL' >&2;exit 3;
}
bash -n "$TMP/owner.sh"
# New NVIDIA first; the historically unsafe Intel is the last session.
for gpu in "${adapters[@]}";do
  if [[ "$gpu" == NVIDIA ]];then lc=nvidia; domain=86;else lc=intel;domain=87;fi
  echo "D06_GPU_RTF_AB_CASE_START=$gpu DOMAIN=$domain GOAL_NOT_SENT"
  rc=0
  AXIA_D06_G07_RX_WITNESS="$([[ "$MODE" == --nvidia-causal ]] && echo 1 || echo 0)" MESA_D3D12_DEFAULT_ADAPTER_NAME="$gpu" ROS_DOMAIN_ID="$domain" \
    bash "$TMP/owner.sh" --run > "$RUN_DIR/$lc.run.log" 2>&1 || rc=$?
  [[ "$rc" == 0 || "$rc" == 3 ]] || {
    echo "D06_GPU_RTF_INFRA_FAILURE=$gpu:$rc" >&2;exit 3;
  }
  archive="$(sed -n 's/^D06_WSLG_NO_GOAL_RAW_ARCHIVE=//p' "$RUN_DIR/$lc.run.log" | tail -1)"
  [[ -n "$archive" && -s "$archive" && -s "$archive.sha256" ]] || {
    echo "D06_GPU_RTF_MISSING_SENSOR_EVIDENCE=$gpu" >&2;exit 3;
  }
  sha256sum -c --status "$archive.sha256" || exit 3
  sub="$(basename "$archive" .tar.gz)"
  for item in native/g07_wslg_sensor_truth.json renderer.txt native/g07_world.sdf.xacro native/g07_demo_waffle.sdf.xacro native/initialpose.json native/launch.log;do
    tar -xOf "$archive" "$sub/$item" > "$RUN_DIR/$lc.$(basename "$item")" || exit 3
  done
  grep -Ei "OpenGL renderer string:.*D3D12.*$gpu" "$RUN_DIR/$lc.renderer.txt" >/dev/null || {
    echo "D06_GPU_RTF_ACTUAL_RENDERER_MISMATCH=$gpu" >&2;exit 3;
  }
  python3 - "$RUN_DIR/$lc.g07_wslg_sensor_truth.json" <<'PY'
import json,sys
d=json.load(open(sys.argv[1]));m=d.get("rtf_diagnostics",{})
assert d["goal_sent"] is False and d["fixture_moved"] is False
assert m.get("ros_clock_rtf") is not None and m["ros_clock_rtf"]>0
print("D06_GPU_RTF_CLOCK_MEASURED",m["ros_clock_rtf"],m["timing_pattern"])
PY
  # Record the actual Gazebo/Ogre2 GL renderer separately from glxinfo:
  # glxinfo describes the WSLg client, NOT conclusive sensor-server GPU use.
  # Filter to minimal render evidence; never assert GPU causation from it.
  if [[ -r "$HOME/.gz/rendering/ogre2.log" ]];then
    grep -Ei 'GL_RENDERER|GL_VENDOR|OpenGL|D3D12' "$HOME/.gz/rendering/ogre2.log" \
      | tail -n 12 > "$RUN_DIR/$lc.ogre2_gl_evidence.txt" || true
  fi
  # Surface the first sensor failure BEFORE native shutdown crash check.
  python3 - "$RUN_DIR/$lc.g07_wslg_sensor_truth.json" <<'PY'
import json,sys
r=json.load(open(sys.argv[1],encoding="utf-8"))
reasons=r.get("reasons",[])
m=r.get("metrics",{})
print("D06_GPU_RTF_FIRST_SENSOR_FAILURE="+(reasons[0] if reasons else "NONE"))
print("D06_GPU_RTF_SENSOR_REASONS="+",".join(reasons))
for key in ("raw","safety"):
    a=m.get(key,{})
    print("D06_GPU_RTF_"+key.upper()+"_MAX_HOST_GAP_SEC="+str(a.get("max_receipt_gap_sec")))
    print("D06_GPU_RTF_"+key.upper()+"_FIRST_TTL_INDEX="+str(a.get("first_receipt_ttl_breach_at_index")))
safe=m.get("safety",{})
print("D06_GPU_RTF_CLEAR_COUNT="+str(safe.get("clear_count"))+"/"+str(safe.get("count")))
print("D06_GPU_RTF_FRONT_SIDE_MEDIAN_M="+str(safe.get("front_median_m"))+"/"+str(safe.get("side_median_m")))
PY
  echo "D06_GPU_RTF_AB_CASE_FINISHED=$gpu SENSOR_EXIT=$rc NO_GOAL"
  # D08 unchanged native receiver and independent ROS scan witness from
  # this EXACT SAME Gazebo simulation; no second run and no Goal.
  if [[ "$MODE" == --nvidia-causal ]];then
    if ! tar -xOf "$archive" "$sub/native/d06_g07_scan_delivery_layer.json" \
        > "$RUN_DIR/$lc.d06_g07_scan_delivery_layer.json";then
      echo D06_G07_NATIVE_RX_NO_LAYER_REPORT_NO_GOAL >&2;exit 3
    fi
    python3 - "$RUN_DIR/$lc.d06_g07_scan_delivery_layer.json" <<'PY'
import json,sys
v=json.load(open(sys.argv[1],encoding="utf-8"))
print("D06_G07_FIRST_SCAN_TTL_HOLD candidate="+str(v.get("candidate","UNMEASURED"))+
      " native_gap_sec="+str(v.get("native_gap_sec"))+
      " raw_gap_sec="+str(v.get("raw_gap_sec"))+
      " safety_gap_sec="+str(v.get("safety_gap_sec"))+
      " GOAL_NOT_SENT")
assert v.get("release")=="HOLD" and v.get("goal_allowed") is False
assert v.get("observer_raw_count",0)>=20 and v.get("observer_safety_count",0)>=20
assert v.get("native_count",0)>=20
PY
  fi
  # A fatal shutdown after NVIDIA must not be followed by another session.
  if grep -Eiq 'exit code -11|SIGSEGV|Segmentation fault' "$RUN_DIR/$lc.launch.log";then
    echo "D06_GPU_RTF_NATIVE_SHUTDOWN_SEGV_HOLD=$gpu" >&2
    if [[ "$gpu" == NVIDIA ]];then
      echo D06_GPU_RTF_NVIDIA_SHUTDOWN_CRASH_ABORT_SECOND_RUN >&2
    fi
    exit 3
  elif grep -Eiq 'Traceback' "$RUN_DIR/$lc.launch.log";then
    echo "D06_GPU_RTF_NATIVE_PYTHON_TRACEBACK_HOLD=$gpu" >&2
    exit 3
  fi
  if [[ "$rc" -ne 0 ]];then
    echo "D06_GPU_RTF_SENSOR_EXIT_HOLD=$gpu:$rc" >&2
    exit 3
  fi
done
# A single NVIDIA session tests only the D08-proven adapter choice.
# It does NOT prove Intel-vs-NVIDIA causality, CM120/Guard150 or Moving L3.
if [[ "$MODE" == --nvidia-only || "$MODE" == --nvidia-causal ]];then
  python3 - "$RUN_DIR/nvidia.g07_wslg_sensor_truth.json" <<'PY'
import json,sys
r=json.load(open(sys.argv[1],encoding='utf-8'))
m=r.get('metrics',{})
raw=m.get('raw',{})
safety=m.get('safety',{})
rtf=r.get('rtf_diagnostics',{})
checks={
 'no_goal':r.get('goal_sent') is False and r.get('fixture_moved') is False,
 'source_clock_rtf_measured':isinstance(rtf.get('ros_clock_rtf'),(float,int)) and rtf['ros_clock_rtf']>0,
 'raw_300ms':0 < raw.get('max_receipt_gap_sec',999) <= .3,
 'safety_300ms':0 < safety.get('max_receipt_gap_sec',999) <= .3,
 'front_clear':safety.get('front_median_m',0)>.75,
 'side_clear':safety.get('side_median_m',0)>1.20,
 'every_safety_scan_clear':safety.get('count',0)>=20 and safety.get('count')==safety.get('clear_count'),
 'native_report_candidate':r.get('status')=='NO_GOAL_SENSOR_WINDOW_CLEAR_CANDIDATE',
}
print('D06_GPU_RTF_NVIDIA_ONLY_FIRST_BLOCK='+next((k for k,v in checks.items() if not v),'NONE'))
print('D06_GPU_RTF_NVIDIA_ONLY_NO_GOAL_CHECKS='+json.dumps(checks,sort_keys=True))
print('D06_GPU_RTF_NVIDIA_SENSOR_CANDIDATE_NOT_ACCEPTED')
if not all(checks.values()):raise SystemExit(3)
PY
  echo "D06_GPU_RTF_NVIDIA_NO_GOAL_EVIDENCE=$RUN_DIR"
  echo 'D06_GAZEBO_LIVE_RELEASE=HOLD CERTIFIED_ESTOP=false'
  exit 0
fi
for stem in g07_world.sdf.xacro g07_demo_waffle.sdf.xacro;do
  cmp -s "$RUN_DIR/intel.$stem" "$RUN_DIR/nvidia.$stem" || {
    echo "D06_GPU_RTF_WORLD_OR_WAFFLE_NOT_IDENTICAL=$stem" >&2;exit 3;
  }
done
# Same frozen initial pose and static occupancy map are required to
# attribute LiDAR geometry changes to renderer condition rather than scene.
python3 - "$RUN_DIR/intel.initialpose.json" "$RUN_DIR/nvidia.initialpose.json" <<'PY'
import json,sys
a,b=[json.load(open(p)) for p in sys.argv[1:]]
assert a["result"]=="POSE_DELIVERY_ACKNOWLEDGED"
assert b["result"]=="POSE_DELIVERY_ACKNOWLEDGED"
assert a["position"]==b["position"]==[-2.0,-0.5,0.0]
assert a["map_meta"]["data_sha256"]==b["map_meta"]["data_sha256"]
print("D06_GPU_RTF_AB_SAME_GAZEBO_WORLD_WAFFLE_INITIALPOSE_AND_MAP_PROVEN_NO_GOAL")
PY
python3 "$TMP/compare.py" \
  --intel-json "$RUN_DIR/intel.g07_wslg_sensor_truth.json" \
  --nvidia-json "$RUN_DIR/nvidia.g07_wslg_sensor_truth.json" \
  --intel-renderer "$RUN_DIR/intel.renderer.txt" \
  --nvidia-renderer "$RUN_DIR/nvidia.renderer.txt" \
  --output "$RUN_DIR/independent_axes_ab.json"
echo "D06_GPU_RTF_AB_REPORT=$RUN_DIR/independent_axes_ab.json"
echo "D06_GPU_RTF_PRIVATE_EVIDENCE=$RUN_DIR"
echo 'D06_GAZEBO_LIVE_RELEASE=HOLD CERTIFIED_ESTOP=false'
