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
readonly OWNER_SHA='3e2e9f2abc694a1183634c06b558efe85e976474'
readonly OWNER_BLOB='8fa030fd2e87907b758075c7a88b61caa8b9bb42'
readonly ANALYZER_SHA='615bcd81b8f74a478daa2baeaf9f27ca02c94f11'
readonly ANALYZER_BLOB='171aad7ce8abe97c93a42f19787042619c06b65e'
readonly STUDENT_SHA='8e19742fd7bd80db73a37dc7b1d798768dc33e2a'
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
 "first_scan_host_receipt_trace_available":any(
     bool(report.get("scan_receipts_compact",{}).get(topic)) for topic in ("raw","safety"))
}
# The safety gate now observes an unmodified Scan300 for the FULL window
# AFTER both topics are active; preserve every earlier warmup breach distinctly.
warmup=report.get("startup_pre_both_scan_diagnostics",{})
if not isinstance(warmup,dict):warmup={}
summary["dual_topic_both_topics_ready"]=warmup.get("both_topics_ready",False)
summary["pre_ready_raw_gap_sec"]=warmup.get("pre_ready_raw_first_gap_sec")
summary["pre_ready_breach_evidence_retained"]=warmup.get("pre_ready_breach_evidence_retained",False)
summary["dual_topic_required_observation_sec"]=report.get("dual_topic_required_observation_sec")
summary["dual_topic_observed_wall_sec"]=report.get("dual_topic_actual_wall_observation_sec")
if warmup:
    (out/"startup_pre_both_scan_diagnostics.json").write_text(
        json.dumps(warmup,indent=2,sort_keys=True)+"\\n",encoding="utf-8")

(out/"summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")
if report.get("scan_receipts_compact"):
    (out/"scan_receipts_compact.json").write_text(json.dumps(report["scan_receipts_compact"])+"\n",encoding="utf-8")
owner=read("nvidia.run.log")
# Preserve actual first failure, not a guessed root cause from the absence of ROS logs.
state={}
for row in read("attempt_state.txt")[:30]:
    if "=" in row:
        key,value=row.split("=",1)
        state[key.strip()]=value.strip()
summary["first_failure_stage"]=state.get("phase","UNKNOWN_ORIGINAL_STAGE")
summary["outer_exit_code"]=(int(state["outer_rc"])
    if state.get("outer_rc","").isdigit() else None)
summary["owner_exit_code"]=(int(state["owner_rc"])
    if state.get("owner_rc","").isdigit() else None)
failure_pattern=re.compile(
    r"(_MISSING|_BLOCKED|_FAILED|_UNAVAILABLE|_MISMATCH|_DENIED|"
    r"_INVALID|_HOLD|_ERROR|_FAILURE|_NOT_READY|_NOT_FOUND|"
    r"Traceback|ModuleNotFoundError|ImportError|Exception|"
    r"Error:|fatal:|no such file|command not found|Permission denied)",re.I)
issues=[(i,row) for i,row in enumerate(owner) if failure_pattern.search(row)]
first_marker=("ORIGINAL_OWNER_LOG_UNAVAILABLE" if not owner else
    issues[0][1].strip()[:300] if issues else "OWNER_FIRST_FAILURE_UNIDENTIFIED")
summary["first_owner_failure_marker"]=first_marker
summary["original_owner_log_present"]=bool(owner)
summary["original_owner_log_line_count"]=len(owner)
indices=set(range(min(4,len(owner))))
for i,_ in issues[:12]:
    indices.update(range(max(0,i-2),min(len(owner),i+3)))
indices.update(range(max(0,len(owner)-16),len(owner)))
def sanitize(v):
    v=re.sub(r"(gh[pousr]_[A-Za-z0-9_]{12,}|github_pat_[A-Za-z0-9_]{10,})",
             "[REDACTED_TOKEN]",v)
    v=re.sub(r"(?i)(authorization[:=]\s*bearer\s+)\S+",
             r"\1[REDACTED]",v)
    return v[:360]
detail=["FIRST_OWNER_FAILURE_MARKER="+sanitize(first_marker),
        "FIRST_FAILURE_STAGE="+summary["first_failure_stage"],
        "ORIGINAL_OWNER_LOG_LINE_COUNT="+str(len(owner)),
        "OWNER_ORIGINAL_RC="+str(summary["owner_exit_code"]),
        "NOTE: no native sensor verdict means NO_GOAL acceptance is HOLD.",
        "Original local nvidia.run.log is NOT embedded in this compact TAR."]
for i in sorted(indices)[:65]:
    detail.append(str(i+1)+": "+sanitize(owner[i]))
for file in ("nvidia.preflight.stderr.txt","bootstrap_fetch_errors.txt"):
    rows=read(file)
    if rows:
        detail.append("## "+file)
        detail.extend(sanitize(v) for v in rows[:12])
(out/"first_preflight_or_owner_failure.txt").write_text(
    "\n".join(detail)[:17000]+"\n",encoding="utf-8")
if (base/"attempt_state.txt").is_file():
    (out/"attempt_state.txt").write_text(
        "\n".join(read("attempt_state.txt")[:30])+"\n",encoding="utf-8")

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
                "g07_ordered_shutdown.json":("native_nav2_ordered_shutdown.json",16000),
                "g07_shutdown_audit.json":("native_cm_shutdown_audit.json",16000),
                "g07_ordered_shutdown.log":("native_nav2_ordered_shutdown.log",22000),
                "g07_witness_probe_complete.signal":("native_witness_probe_completed.txt",256),
                "g07_witness_stopped.ack":("native_witness_handoff_ack.txt",256),
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
# Full-run first callback delay is NOT the same as the post-READY proxy.
# Preserve both, while making it explicit the Student's exact source pairs
# were not captured by that Student process in this run.
post_ready=causal.get("post_ready_proxy",{})
summary["whole_session_first_gap_scope"]=causal.get("scope","WHOLE_SESSION_UNVERIFIED")
summary["post_ready_proxy_candidate"]=post_ready.get("candidate","NOT_MEASURED")
summary["post_ready_proxy_native_gap_sec"]=post_ready.get("native_gap_sec")
summary["post_ready_proxy_clock_rtf"]=post_ready.get("native_clock_window_rtf")
summary["post_ready_proxy_student_pair_proven"]=False
student_first=causal.get("student_first_ttl",{})
summary["student_first_actual_pair_candidate"]=student_first.get("student_first_candidate","NOT_MEASURED")
summary["student_first_actual_stamp_pair_verified"]=bool(student_first.get("student_first_stamp_pair_verified",False))
summary["student_first_actual_native_gap_sec"]=student_first.get("student_first_native_gap_sec")
summary["student_first_actual_host_gap_sec"]=student_first.get("student_first_host_gap_sec")
summary["student_first_topic"]=student_first.get("student_first_topic")


summary["source_pair_causality_proven"]=False
summary["native_transport_rx_observed"]=bool(causal.get("native_count",0)>0)
summary["ros_rx_observed"]=bool(causal.get("observer_raw_count",0)>0)
summary["no_goal_acceptance"]=False
# A parent shutdown marker never overrides actual CM abnormal exit.
# These fields make independent Nav2 ACK and process exit checks self-contained
# in the same compact ZIP, even if the original Scan300 gate returns rc3.
nav={}
audit={}
if native_verified:
    try: nav=json.loads((out/"native_nav2_ordered_shutdown.json").read_text(encoding="utf-8"))
    except (OSError,ValueError): pass
    try: audit=json.loads((out/"native_cm_shutdown_audit.json").read_text(encoding="utf-8"))
    except (OSError,ValueError): pass
summary["native_no_goal_navigation_ack"]=nav.get("navigation_ack")
summary["native_no_goal_localization_ack"]=nav.get("localization_ack")
handoff_probe=out/"native_witness_probe_completed.txt"
handoff_ack=out/"native_witness_handoff_ack.txt"
summary["native_readonly_witness_handoff_ack"]=bool(
    native_verified
    and handoff_probe.is_file()
    and handoff_ack.is_file()
    and handoff_probe.read_text(encoding="utf-8").strip()=="G07_READONLY_SENSOR_PROBE_FINISHED"
    and handoff_ack.read_text(encoding="utf-8").strip()=="G07_READONLY_WITNESSES_STOPPED"
)

# The entire shutdown is clean ONLY if each native child has positive
# exit0 evidence. A ros2 launch group exit marker never proves Gazebo clean.
gz_clean=any("[gz-" in row and "process has finished cleanly" in row for row in log)
gz_negative=any("[gz-" in row and "process has died" in row for row in log)
summary["native_no_goal_gazebo_server_exit_code"]=(
    -11 if "gazebo_server" in crashes else 0 if gz_clean and not gz_negative else None
)
summary["native_no_goal_gazebo_server_clean"]=(
    gz_clean and not gz_negative and "gazebo_server" not in crashes
)
summary["first_native_crash_layer"]=(
    "GAZEBO_OR_CM_SHUTDOWN" if len(crashes)>1
    else "GAZEBO_SERVER" if "gazebo_server" in crashes
    else "COLLISION_MONITOR" if "collision_monitor" in crashes
    else "NONE_OBSERVED"
)

summary["native_no_goal_cm_exit_code"]=audit.get("cm_exit_code")
summary["native_no_goal_cm_clean_candidate"]=(
    nav.get("status")=="NAV2_LIFECYCLE_SHUTDOWN_ACK"
    and nav.get("navigation_ack") is True
    and nav.get("localization_ack") is True
    and nav.get("cm_managed_by_navigation") is True
    and audit.get("status")=="SHUTDOWN_CLEAN_CANDIDATE"
    and audit.get("cm_exit_code")==0
    and not any(crash=="collision_monitor" for crash in crashes)
    and "FORCED" not in "\\n".join(read("nvidia.run.log"))
)
summary["native_no_goal_whole_teardown_clean"]=(
    summary["native_no_goal_cm_clean_candidate"]
    and summary["native_no_goal_gazebo_server_clean"]
    and not crashes
    and "P2_L2_GRACEFUL_TEARDOWN" in (out/"native_teardown_marker.txt").read_text(encoding="utf-8")
    if (out/"native_teardown_marker.txt").exists() else False
)


(out/"summary.json").write_text(
    json.dumps(summary,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")
markers=re.compile("G07_WSLG_NO_GOAL_SENSOR_|AXIA_G07_WSLG_NO_GOAL_SENSOR_TRUTH|D06_WSLG_NO_GOAL_SENSOR_|D06_GAZEBO_LIVE_RELEASE|D06_WSLG_NO_GOAL_RAW_ARCHIVE|D06_G07_NATIVE|D06_G07_RX_WITNESS|D06_G07_FIRST_SCAN_TTL_HOLD|D06_G07_POST_READY_PROXY|D06_G07_STUDENT_FIRST_TTL|G07_NO_GOAL_GAZEBO_PAUSE")
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
print("D06_FORENSIC_READONLY_WITNESS_HANDOFF="+str(summary["native_readonly_witness_handoff_ack"])+
      " BEFORE_NAV2_SHUTDOWN_EVIDENCE_ONLY",flush=True)
print("D06_FORENSIC_NO_GOAL_NAV2_ACK="+str(
    summary.get("native_no_goal_navigation_ack"))+"/"+str(
    summary.get("native_no_goal_localization_ack"))+
    " CM_NATIVE_EXIT_CODE="+str(summary.get("native_no_goal_cm_exit_code"))+
    " CLEAN_CANDIDATE="+str(summary.get("native_no_goal_cm_clean_candidate"))+
    " SENSOR_TTL_GATE_UNCHANGED",flush=True)
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
  # Failure provenance also on early preflight/checkout/import error.
  printf "phase=%s\nowner_rc=%s\nouter_rc=%s\nmode=%s\n" \
    "${D06_STAGE:-UNKNOWN}" "${D06_OWNER_RC:-NOT_STARTED}" "$saved_rc" "$MODE" \
    > "$RUN_DIR/attempt_state.txt" || true
  # Never turn a failed sensor/teardown process into a success.
  collect_and_package "$RUN_DIR" FUTURE_RUN_SAME_SESSION ||
    echo 'D06_FORENSIC_BUNDLE_FAILED_OR_INCOMPLETE_NO_GOAL' >&2
  rm -rf -- "$TMP"
  exit "$saved_rc"
}
trap cleanup EXIT
D06_STAGE=GPU_PREFLIGHT
D06_OWNER_RC=NOT_STARTED
# Preflight *actual* GPU selection before ever launching a robot.
for gpu in "${adapters[@]}";do
  MESA_D3D12_DEFAULT_ADAPTER_NAME="$gpu" glxinfo -B > "$RUN_DIR/$gpu.preflight.txt" 2> "$RUN_DIR/$gpu.preflight.stderr.txt"
  grep -Ei "OpenGL renderer string:.*D3D12.*$gpu" "$RUN_DIR/$gpu.preflight.txt" >/dev/null || {
    echo "D06_GPU_RTF_D3D12_$gpu_UNAVAILABLE_NO_GOAL" >&2;exit 3;
  }
done
D06_STAGE=SOURCE_FETCH
URL="https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public"
curl -fLsS --retry 3 --max-time 90 "$URL/$OWNER_SHA/d06/scripts/axia_d06_g07_wslg_sensor_no_goal_once.sh" -o "$TMP/owner.sh"
curl -fLsS --retry 3 --max-time 90 "$URL/$ANALYZER_SHA/d06/tools/axia_d06_lidar_rtf_compare.py" -o "$TMP/compare.py"
[[ "$(git hash-object "$TMP/owner.sh")" == "$OWNER_BLOB" && "$(git hash-object "$TMP/compare.py")" == "$ANALYZER_BLOB" ]] || {
  echo 'D06_GPU_RTF_SOURCE_BLOB_MISMATCH_NO_GOAL' >&2;exit 3;
}
bash -n "$TMP/owner.sh"
# New NVIDIA first; the historically unsafe Intel is the last session.
for gpu in "${adapters[@]}";do
  D06_STAGE=OWNER_RUNNING
  if [[ "$gpu" == NVIDIA ]];then lc=nvidia; domain=86;else lc=intel;domain=87;fi
  echo "D06_GPU_RTF_AB_CASE_START=$gpu DOMAIN=$domain GOAL_NOT_SENT"
  rc=0
  AXIA_D06_G07_RX_WITNESS="$([[ "$MODE" == --nvidia-causal ]] && echo 1 || echo 0)" MESA_D3D12_DEFAULT_ADAPTER_NAME="$gpu" ROS_DOMAIN_ID="$domain" \
    bash "$TMP/owner.sh" --run > "$RUN_DIR/$lc.run.log" 2>&1 || rc=$?
  D06_OWNER_RC="$rc"
  D06_STAGE=OWNER_FINISHED
  [[ "$rc" == 0 || "$rc" == 3 ]] || {
    echo "D06_GPU_RTF_INFRA_FAILURE=$gpu:$rc" >&2;exit 3;
  }
  D06_STAGE=NATIVE_ARCHIVE_VALIDATION
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
actual=v.get("student_first_ttl",{})
print("D06_G07_STUDENT_FIRST_TTL candidate="+str(actual.get("student_first_candidate","NOT_MEASURED"))+
      " matched="+str(actual.get("student_first_stamp_pair_verified",False))+
      " native_gap="+str(actual.get("student_first_native_gap_sec"))+
      " topic="+str(actual.get("student_first_topic"))+
      " GOAL_NOT_SENT")
assert v.get("release")=="HOLD" and v.get("goal_allowed") is False
assert v.get("observer_raw_count",0)>=20 and v.get("observer_safety_count",0)>=20
assert v.get("native_count",0)>=20
PY
  fi
  # D06_OWNER_NO_GOAL_NATIVE_GATE_START
  # Full native shutdown is not established by a successful sensor candidate,
  # no SIGSEGV substring, or parent P2_L2_GRACEFUL_TEARDOWN alone.
  # This is read-only verification of the existing immutable Owner evidence.
  python3 - "$archive" "$MODE" "$rc" "$sub" <<'PY'
import json, math, re, sys, tarfile
archive, mode, owner_rc, root = sys.argv[1:]
def block(reason):
    print("D06_OWNER_NO_GOAL_NATIVE_GATE_BLOCKED="+reason,flush=True)
    raise SystemExit(3)
try:
    with tarfile.open(archive,"r:gz") as bundle:
        def read(name,limit=1500000):
            info=bundle.getmember(root+"/native/"+name)
            if not info.isfile() or info.size>limit:
                block("MISSING_OR_OVERSIZED_"+name.replace("/","_"))
            with bundle.extractfile(info) as stream:
                return stream.read().decode("utf-8",errors="replace")
        sensor=json.loads(read("g07_wslg_sensor_truth.json"))
        nav=json.loads(read("g07_ordered_shutdown.json"))
        audit=json.loads(read("g07_shutdown_audit.json"))
        launch=read("launch.log",limit=3000000)
        teardown=read("teardown.txt",limit=12000)
        pause=read("g07_gz_world_pause.log",limit=12000)
        handoff=False
        if mode=="--nvidia-causal":
            signal=read("g07_witness_probe_complete.signal",limit=256)
            ack=read("g07_witness_stopped.ack",limit=256)
            handoff=(signal.strip()=="G07_READONLY_SENSOR_PROBE_FINISHED"
                     and ack.strip()=="G07_READONLY_WITNESSES_STOPPED")
            if not handoff:block("WITNESS_HANDOFF_MISSING_BEFORE_NAV2")
except (OSError,KeyError,ValueError,UnicodeError,tarfile.TarError) as exc:
    block("MISSING_OR_INVALID_NATIVE_EVIDENCE_"+type(exc).__name__)
if owner_rc!="0":block("ORIGINAL_OWNER_RC_"+owner_rc)
if (sensor.get("status")!="NO_GOAL_SENSOR_WINDOW_CLEAR_CANDIDATE"
    or sensor.get("reasons")
    or sensor.get("goal_sent") is not False
    or sensor.get("fixture_moved") is not False):
    block("SENSOR_NOT_CLEAR_OR_GOAL_AUTHORITY")
warmup=sensor.get("startup_pre_both_scan_diagnostics",{})
if (not isinstance(warmup,dict)
    or warmup.get("both_topics_ready") is not True
    or warmup.get("pre_ready_observations_not_motion_authority") is not True
    or sensor.get("dual_topic_required_observation_sec")!=20
    or not isinstance(sensor.get("dual_topic_actual_wall_observation_sec"),(int,float))
    or sensor["dual_topic_actual_wall_observation_sec"]<20):
    block("BOTH_TOPIC_FULL_20S_NOT_PROVEN")
metrics=sensor.get("metrics",{})
for topic in ("raw","safety"):
    m=metrics.get(topic,{})
    gap=m.get("max_receipt_gap_sec")
    if (not isinstance(gap,(int,float)) or not math.isfinite(gap)
        or not 0<gap<=.300 or m.get("count",0)<20
        or m.get("first_receipt_ttl_breach_at_index") is not None):
        block("SCAN_300MS_"+topic.upper()+"_BLOCKED")
safe=metrics["safety"]
if (safe.get("clear_count")!=safe["count"]
    or not isinstance(safe.get("front_median_m"),(float,int))
    or not isinstance(safe.get("side_median_m"),(float,int))
    or not safe["front_median_m"]>.75
    or not safe["side_median_m"]>1.20):
    block("SCAN_GEOMETRY_NOT_ALL_CLEAR")
if (nav.get("status")!="NAV2_LIFECYCLE_SHUTDOWN_ACK"
    or nav.get("navigation_ack") is not True
    or nav.get("localization_ack") is not True
    or nav.get("cm_managed_by_navigation") is not True):
    block("NAV2_LIFECYCLE_SHUTDOWN_ACK_MISSING")
if audit.get("status")!="SHUTDOWN_CLEAN_CANDIDATE" or audit.get("cm_exit_code")!=0:
    block("COLLISION_MONITOR_CHILD_EXIT0_NOT_PROVEN")
if "P2_L2_GRACEFUL_TEARDOWN" not in teardown or "data: true" not in pause:
    block("PARENT_TEARDOWN_OR_GAZEBO_PAUSE_MISSING")
def exited_clean(process):
    return bool(re.search(
       r"(?m)^\[INFO\]\s+\["+process+r"-\d+\]: process has finished cleanly",
       launch))
def died(process):
    return bool(re.search(
       r"(?m)^\[ERROR\]\s+\["+process+r"-\d+\]: process has died",
       launch))
if not exited_clean("collision_monitor") or died("collision_monitor"):
    block("COLLISION_MONITOR_LAUNCH_EXIT0_NOT_PROVEN")
if not exited_clean("gz") or died("gz"):
    block("GAZEBO_SERVER_LAUNCH_EXIT0_NOT_PROVEN")
print("D06_OWNER_NO_GOAL_NATIVE_COMPLETE_CANDIDATE"+
      " SCAN300_DUAL_20S_PASS NAV2_ACK_PASS CM_CHILD_EXIT0 GZ_CHILD_EXIT0"+
      " WITNESS_HANDOFF="+str(handoff)+" NO_MOVING_L3 CERTIFIED_ESTOP=false",
      flush=True)
PY
  # D06_OWNER_NO_GOAL_NATIVE_GATE_END
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
