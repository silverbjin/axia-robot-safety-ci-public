#!/usr/bin/env bash
# AXIA G07 Cycle37 WSLg visual pre-acceptance. GUI ONLY, NO GOAL.
# Approved visual parity: official Gazebo Harmonic World + Waffle,
# scoped SceneBroadcaster 25Hz, separate gz sim -g and RViz2.
# No Nav2 Goal, fixture relocation, cmd_vel publisher, CM timing admission,
# or certified E-Stop claim. Does NOT replace final Owner L3 safety review.
set -Eeuo pipefail
umask 077

readonly PRIVATE_SHA=966886c4627deb2bb3b37111fe336eeee6b9ebb4
readonly GUI_SHA=c4dca31b210d28037116e49fe39d8d0b5aebdc34
readonly RVIZ_SHA=0f66059d9110f8e667200bbca22396bd0c78c02e
readonly CI_L2_RUN=43905300294
readonly CI_L2_HEAD=91cb68471809bd661f7b861f2b9c4cc8b54b4373
readonly PUBLIC_REPO=silverbjin/axia-robot-safety-ci-public
readonly PRIVATE_REPO=silverbjin/axia-robot-safety-instructor

hold() {
  echo "AXIA_G07_C38_GUI_ONLY_HOLD_NO_GOAL $*" >&2
  echo 'AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false' >&2
  exit 3
}
static_check() {
  for sha in "$PRIVATE_SHA" "$GUI_SHA" "$RVIZ_SHA" "$CI_L2_HEAD";do
    [[ "$sha" =~ ^[0-9a-f]{40}$ ]] || return 3
  done
  [[ "$CI_L2_RUN" =~ ^[0-9]+$ ]] || return 3
  bash -n "$0" || return 3
  echo "AXIA_G07_C38_GUI_ONLY_STATIC_PASS_NO_ROS_NO_GOAL private=$PRIVATE_SHA display=$GUI_SHA"
}
ci_admission() {
  command -v gh >/dev/null || hold GH_CLI_REQUIRED
  gh auth status >/dev/null 2>&1 || hold GH_AUTH_REQUIRED_FOR_PRIVATE_INSTRUCTOR
  local actual
  actual="$(gh api "repos/$PUBLIC_REPO/actions/runs/$CI_L2_RUN" \
    --jq '(.head_sha // "")+" "+(.status // "")+" "+(.conclusion // "")')" ||
      hold GUI_ONLY_L2_PROVENANCE_UNAVAILABLE
  [[ "$actual" == "$CI_L2_HEAD completed success" ]] ||
    hold "GUI_ONLY_L2_NOT_GREEN_OR_SOURCE_DRIFT $actual"
  echo "AXIA_G07_C38_GUI_ONLY_REAL_GAZEBO_L2_PROVENANCE_PASS run=$CI_L2_RUN NO_GOAL WSLG_PIXELS_NOT_YET_VERIFIED"
}
case "$#" in
  0) ;;
  1)
    case "$1" in
      --self-check) static_check;exit $?;;
      --admission-check) static_check;ci_admission;exit 0;;
      *) hold UNSUPPORTED_ARGUMENT;;
    esac;;
  *) hold UNSUPPORTED_ARGUMENTS;;
esac

[[ "${GITHUB_ACTIONS:-}" != true ]] || hold NO_OWNER_GUI_IN_GITHUB_CI
[[ -t 0 && -r /dev/tty ]] || hold OWNER_TERMINAL_REQUIRED_FOR_VISUAL_REVIEW
source /etc/os-release
[[ "$ID" == ubuntu && "$VERSION_ID" == 24.04 ]] || hold UBUNTU_24_04_REQUIRED
grep -qiE '(microsoft|wsl)' /proc/sys/kernel/osrelease || hold OWNER_WSL2_REQUIRED
[[ -n "${DISPLAY:-}" && -r /opt/ros/jazzy/setup.bash ]] || hold WSLG_AND_ROS2_JAZZY_REQUIRED
for command_name in bash git gh python3 ros2 colcon gz rviz2 xacro taskset nice setsid timeout sha256sum mktemp glxinfo xwininfo xwd tar;do
  command -v "$command_name" >/dev/null || hold "MISSING_COMMAND_$command_name"
done
static_check || hold STATIC_CHECK_FAILED
ci_admission

[[ -d "$HOME" && "$HOME" != / && ! -L "$HOME" ]] || hold HOME_NOT_TRUSTED
readonly WORK="$(mktemp -d "$HOME/.axia_g07_c38_gui_source_XXXXXXXX")"
readonly OUT="$(mktemp -d "$HOME/axia_g07_c38_gui_evidence_XXXXXXXX")"
readonly PRIVATE="$WORK/instructor"
readonly PUBLIC="$WORK/gui_public"
readonly VISUAL="$WORK/rviz_public"
mkdir -m 700 "$OUT/G07" "$OUT/visual"
LAUNCH_PID=''
GUI_PID=''
finish() {
  local rc=$?
  trap - EXIT INT TERM
  set +e
  if [[ "$GUI_PID" =~ ^[0-9]+$ ]];then
    kill -TERM "$GUI_PID" 2>/dev/null || true
    wait "$GUI_PID" 2>/dev/null || true
  fi
  if [[ "$LAUNCH_PID" =~ ^[0-9]+$ ]];then
    kill -INT -- "-$LAUNCH_PID" 2>/dev/null || true
    for _ in {1..50};do
      kill -0 "$LAUNCH_PID" 2>/dev/null || break
      sleep 0.2
    done
    if kill -0 "$LAUNCH_PID" 2>/dev/null;then
      kill -TERM -- "-$LAUNCH_PID" 2>/dev/null || true
    fi
    wait "$LAUNCH_PID" 2>/dev/null || true
  fi
  cd "$HOME" 2>/dev/null || cd /
  # Preserve the first Ogre2 rendering fault, not just later exit rc=-11.
  if [[ -r "$HOME/.gz/rendering/ogre2.log" ]];then
    cp -- "$HOME/.gz/rendering/ogre2.log" "$OUT/visual/ogre2_owner_log.txt" 2>/dev/null || true
  fi
  ( cd "$OUT" && find . -type f ! -name SHA256SUMS -print0 |
    sort -z | xargs -0 -r sha256sum > SHA256SUMS ) || true
  # One evidence archive for agent-side FIRST-failure CI regression.
  tar -czf "$OUT.tar.gz" -C "$(dirname "$OUT")" "$(basename "$OUT")" 2>/dev/null || true
  [[ -s "$OUT.tar.gz" ]] && sha256sum "$OUT.tar.gz" > "$OUT.tar.gz.sha256" || true
  echo "AXIA_G07_C38_GUI_ONLY_ARCHIVE=$OUT.tar.gz"
  if [[ "$WORK" == "$HOME"/.axia_g07_c38_gui_source_* ]];then
    rm -rf -- "$WORK"
  fi
  echo "AXIA_G07_C38_GUI_ONLY_EVIDENCE=$OUT"
  echo "AXIA_G07_C38_GUI_ONLY_EXIT_RC=$rc"
  echo 'AXIA_G07_OWNER_FINAL_MOVING_L3=NOT_RUN CM_120MS=NOT_TESTED'
  echo 'AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false'
  exit "$rc"
}
trap finish EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

# Fetch immutable SHAs; main branches and unpinned scripts are not executed.
for item in "$GUI_SHA:$PUBLIC" "$RVIZ_SHA:$VISUAL";do
  sha="${item%%:*}"; checkout_dir="${item#*:}"
  git init -q "$checkout_dir"
  git -C "$checkout_dir" remote add origin "https://github.com/$PUBLIC_REPO.git"
  git -C "$checkout_dir" fetch -q --depth 1 origin "$sha" ||
    hold PUBLIC_IMMUTABLE_FETCH_FAILED
  git -C "$checkout_dir" checkout -q --detach FETCH_HEAD
  [[ "$(git -C "$checkout_dir" rev-parse HEAD)" == "$sha" ]] ||
    hold PUBLIC_IMMUTABLE_SHA_NOT_MATCHED
done
gh repo clone "$PRIVATE_REPO" "$PRIVATE" \
  -- --quiet --no-checkout --filter=blob:none >/dev/null ||
    hold PRIVATE_INSTRUCTOR_CLONE_FAILED
git -C "$PRIVATE" fetch -q --depth 1 origin "$PRIVATE_SHA" ||
  hold PRIVATE_INSTRUCTOR_PIN_FETCH_FAILED
git -C "$PRIVATE" -c advice.detachedHead=false checkout -q --detach FETCH_HEAD
[[ "$(git -C "$PRIVATE" rev-parse HEAD)" == "$PRIVATE_SHA" ]] ||
  hold PRIVATE_INSTRUCTOR_SHA_NOT_MATCHED
for f in "$PRIVATE/scripts/p4_g07_shared_runtime.sh" \
         "$PRIVATE/tools/p4_g07_scene_broadcaster_overlay.py" \
         "$PRIVATE/tools/p2_l3_world_overlay.py" \
         "$PRIVATE/tools/p2_g07_demo_lidar_overlay.py" \
         "$PUBLIC/d06/scripts/g07_shared_gui_clients.sh" \
         "$PUBLIC/d06/live/d06_gui_cpu_plan.py" \
         "$PUBLIC/d06/live/g07_cycle38_gui_window_evidence.py" \
         "$VISUAL/d06/live/d06_readonly_monitor.py" \
         "$VISUAL/d06/rviz/d06_safety_bubble.rviz";do
  [[ -s "$f" ]] || hold GUI_SOURCE_INCOMPLETE
done

set +u
source /opt/ros/jazzy/setup.bash
set -u
export ROS_DOMAIN_ID="$((50 + RANDOM % 100))"
export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
export GZ_PARTITION="axia_p2_c38_gui_$_$RANDOM"
export AXIA_P0_SIM_ONLY=1
export AXIA_G07_UNIFIED_GUI_SIDECAR=1
export AXIA_G07_CYCLE36_INTEGRATED_GUI=0
export AXIA_G07_GUI_SCENE_OVERLAY=1
export AXIA_G07_C37_SCENE_RATE_HZ=25
export AXIA_G07_CI_SIM_GOAL_ALLOWED=0
export AXIA_P2_MVP_ONE_GOAL=0
export AXIA_P2_G07_RELOCATED_OBSTACLE=0
unset LIBGL_ALWAYS_SOFTWARE GALLIUM_DRIVER MESA_LOADER_DRIVER_OVERRIDE QT_QPA_PLATFORM || true
# D07 Cycle19 actually showed 3D/Entity Tree in WSLg when the GUI
# subprocesses selected D3D12 NVIDIA and Qt xcb. Our uploaded Owner ZIP
# selected Intel Xe, OpenGL 4.1, and had only Qt Selection Owner windows.
# Preflight NVIDIA BEFORE starting the expensive Gazebo/Nav2 backend.
if ! timeout 12s env -u LIBGL_ALWAYS_SOFTWARE -u MESA_LOADER_DRIVER_OVERRIDE \
    QT_QPA_PLATFORM=xcb QT_X11_NO_MITSHM=1 \
    GALLIUM_DRIVER=d3d12 MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA \
    glxinfo -B > "$OUT/visual/d07_nvidia_glx_before_launch.txt" 2>&1;then
  hold D07_NVIDIA_D3D12_PRELAUNCH_GPU_PROBE_FAILED
fi
if ! python3 "$PUBLIC/d06/live/g07_cycle38_gui_window_evidence.py" \
     --gpu "$OUT/visual/d07_nvidia_glx_before_launch.txt" --adapter NVIDIA;then
  hold D07_NVIDIA_D3D12_NOT_SELECTED_OWNER_GPU_HOLD
fi
echo AXIA_G07_C38_OWNER_D07_NVIDIA_D3D12_XCB_PREFLIGHT_PASS_NO_ROS_NO_GOAL
printf 'PRIVATE_SHA=%s\nGUI_SHA=%s\nRVIZ_SHA=%s\nROS_DOMAIN_ID=%s\nGZ_PARTITION=%s\nGUI_ONLY_NO_GOAL=true\n' \
  "$PRIVATE_SHA" "$GUI_SHA" "$RVIZ_SHA" "$ROS_DOMAIN_ID" "$GZ_PARTITION" > "$OUT/G07/session_source.txt"
echo "AXIA_G07_C38_GUI_ONLY_WSLG_START domain=$ROS_DOMAIN_ID NO_GOAL CM_120MS_NOT_REQUIRED"

cd "$PRIVATE"
colcon build --base-paths ros2_ws/src --packages-select \
  axia_safety_supervisor axia_fault_injector axia_scenario_verifier \
  --event-handlers console_direct+ > "$OUT/G07/build.log" 2>&1 ||
    hold ROS2_COLCON_BUILD_FAILED
set +u
source install/setup.bash
set -u
for pkg in nav2_bringup nav2_minimal_tb3_sim ros_gz_sim;do
  ros2 pkg prefix "$pkg" >/dev/null || hold "OFFICIAL_PACKAGE_MISSING_$pkg"
done

WORLD="$(ros2 pkg prefix nav2_minimal_tb3_sim)/share/nav2_minimal_tb3_sim/worlds/tb3_sandbox.sdf.xacro"
WAFFLE="$(ros2 pkg prefix nav2_minimal_tb3_sim)/share/nav2_minimal_tb3_sim/urdf/gz_waffle.sdf.xacro"
python3 tools/p2_l3_world_overlay.py --source "$WORLD" \
  --output "$OUT/G07/g07_world.sdf.xacro" \
  --manifest "$OUT/G07/g07_world_manifest.json" > "$OUT/G07/world_overlay.log" 2>&1 ||
    hold WORLD_CONTACT_OVERLAY_FAILED
python3 tools/p2_g07_demo_lidar_overlay.py --source "$WAFFLE" \
  --output "$OUT/G07/g07_waffle.sdf.xacro" \
  --manifest "$OUT/G07/g07_waffle_manifest.json" > "$OUT/G07/waffle_overlay.log" 2>&1 ||
    hold OFFICIAL_WAFFLE_OVERLAY_FAILED

source scripts/p4_g07_shared_runtime.sh
axia_g07_shared_launch owner-gui \
  "$PRIVATE/ros2_ws/src/axia_safety_bringup/launch/axia_tb3_p2.launch.py" \
  "$OUT/G07/g07_world.sdf.xacro" "$OUT/G07/g07_waffle.sdf.xacro" \
  "$OUT/G07/launch.log" || hold GAZEBO_WORLD_LAUNCH_FAILED
LAUNCH_PID="$AXIA_G07_SHARED_LAUNCH_PID"
[[ "$(axia_g07_shared_headless_mode owner-gui)" == True ]] ||
  hold HEADLESS_SCENE_PROFILE_NOT_SELECTED

python3 - "$OUT/G07" <<'PY' || hold SCENE_BROADCASTER_MANIFEST_OR_SDF_INVALID
import hashlib,json,subprocess,sys,xml.etree.ElementTree as ET
from pathlib import Path
p=Path(sys.argv[1])
orig=p/"g07_world.sdf.xacro"
scene=p/"g07_gui_scene_world.sdf.xacro"
manifest=p/"g07_gui_scene_world_manifest.json"
m=json.loads(manifest.read_text(encoding="utf-8"))
assert m["schema"]=="axia_g07_cycle37_headless_scene_broadcaster_v1"
assert m["original_sha256"]==hashlib.sha256(orig.read_bytes()).hexdigest()
assert m["overlay_sha256"]==hashlib.sha256(scene.read_bytes()).hexdigest()
assert m["scene_broadcaster_count"]==1 and m["scene_broadcaster_unconditional"]
assert m["state_hertz"]==25 and not m["official_source_mutated"]
d=subprocess.run(["xacro",str(scene),"headless:=True"],
                 text=True,capture_output=True,timeout=30)
assert d.returncode==0,d.stderr[:300]
w=ET.fromstring(d.stdout).find("world")
assert w is not None
assert sum(x.get("name")=="gz::sim::systems::Contact" for x in w.findall("plugin"))==1
assert len(w.findall("./model[@name='axia_p2_g07_obstacle']"))==1
plugin=[x for x in w.findall("plugin") if x.get("name")=="gz::sim::systems::SceneBroadcaster"]
assert len(plugin)==1 and plugin[0].findtext("state_hertz")=="25"
print("AXIA_G07_C37_GUI_SCENE25_WORLD_SHA256_SDF_PASS_NO_GOAL",flush=True)
PY

# Do not treat a gz model --list state RPC timeout as absence of World.
world_seen=0
for _ in {1..75};do
  (timeout 6s gz service -l > "$OUT/G07/gz_services.txt" 2>&1) || true
  if grep -Fq '/world/default/control' "$OUT/G07/gz_services.txt" &&
     grep -Fq '/world/default/model/turtlebot3_waffle/' "$OUT/G07/gz_services.txt";then
    world_seen=1;break
  fi
  kill -0 "$LAUNCH_PID" 2>/dev/null || hold GAZEBO_SERVER_EXITED_EARLY
  sleep .5
done
[[ "$world_seen" == 1 ]] || hold REAL_WORLD_OR_WAFFLE_SERVICE_MISSING
echo AXIA_G07_C37_GUI_REAL_GAZEBO_WORLD_WAFFLE_PASS_NO_GOAL

# Exact Cycle37 shared read-only Scene/Pose pre-goal contract.
axia_g07_shared_scene_ready "$OUT/G07" "$OUT/G07/c37_scene_topics_pregoal.txt" ||
  hold SCENE_POSE_LIVE_TRANSPORT_NOT_READY
echo AXIA_G07_C37_GUI_LIVE_SCENE_POSE_PASS_NO_GOAL

bash "$PUBLIC/d06/scripts/g07_shared_gui_clients.sh" owner \
  "$OUT/visual" "$VISUAL" "$PUBLIC" > "$OUT/visual/sidecar.log" 2>&1 &
GUI_PID=$!
for _ in {1..100};do
  [[ -s "$OUT/visual/display_attestation.json" ]] && break
  kill -0 "$GUI_PID" 2>/dev/null || {
    tail -n 50 "$OUT/visual/sidecar.log" >&2 || true
    hold FIRST_D07_XCB_NVIDIA_GUI_CHILD_OR_WINDOW_FAILURE_NO_GOAL
  }
  sleep .5
done
[[ -s "$OUT/visual/display_attestation.json" ]] || hold GUI_CLIENTS_DID_NOT_START
# The owner receipt proves launch/parity but not rendered WSLg pixels.
python3 - "$OUT/visual/display_attestation.json" <<'PY' || hold GUI_CLIENT_RECEIPT_INVALID
import json,sys
d=json.load(open(sys.argv[1],encoding="utf-8"))
assert d["schema"]=="axia.g07.shared_gui_display_client_v2"
assert d["headless_server_required"] is True
assert d["new_cmd_vel_publisher_authorized"] is False
assert d["display"]=="WSLg_candidate"
assert d["wslg_verified"] is False
assert d["renderer_cpu"]!=d["monitor_cpu"]
assert d["real_rviz_window"] is True
assert d["real_gazebo_gui_window"] is True
PY
kill -0 "$LAUNCH_PID" 2>/dev/null || hold GAZEBO_SERVER_EXITED_BEFORE_VIEW
kill -0 "$GUI_PID" 2>/dev/null || hold GUI_CLIENT_EXITED_BEFORE_VIEW
for file in gazebo_scene_owner.xwd rviz_scene_owner.xwd;do
  [[ -s "$OUT/visual/$file" &&
     "$(stat -c %s "$OUT/visual/$file")" -gt 65536 ]] ||
    hold "D07_REAL_X11_XWD_EVIDENCE_MISSING_$file"
done
[[ -s "$OUT/visual/owner_gui_xwd.sha256" ]] ||
  hold D07_XWD_SHA256_CUSTODY_MISSING
( cd "$OUT/visual" && sha256sum -c owner_gui_xwd.sha256 >/dev/null ) ||
  hold D07_XWD_SHA256_MISMATCH
echo AXIA_G07_C38_TWO_TRUE_X11_WINDOW_XWD_RECORDED_OWNER_PIXELS_CONTENT_NEEDS_HUMAN_REVIEW
if command -v xwininfo >/dev/null;then
  (xwininfo -root -tree > "$OUT/visual/windows_x11_optional.txt" 2>&1) || true
fi
if command -v glxinfo >/dev/null;then
  (timeout 8s glxinfo -B > "$OUT/visual/glxinfo_optional.txt" 2>&1) || true
fi
echo AXIA_G07_C38_GUI_TRANSPORT_AND_TWO_CLIENTS_READY_WSLG_PIXELS_UNVERIFIED_NO_GOAL
echo 'Check Gazebo: actual 3D World, Waffle robot, G07 obstacle and Entity Tree.'
echo 'Check RViz2: 3D robot/laser view as available without an active Nav2 Goal.'
echo 'No robot movement is expected. You may capture Windows Win+Shift+S now.'
echo 'The GUI stays open until you answer the following ONE confirmation. Original XWD files were already captured and checksummed.'
sleep 8
kill -0 "$GUI_PID" 2>/dev/null || hold GUI_CLIENT_DIED_DURING_RENDER
printf '\n3D World/Waffle/obstacle visible in Gazebo AND RViz2 window normal?\nType YES-G07-GUI-VISIBLE, or press Enter for HOLD: ' > /dev/tty
answer=''
IFS= read -r answer < /dev/tty || true
export AXIA_G07_GUI_USER_REPLY="$answer"
python3 - "$OUT/visual/gui_user_observation.json" <<'PY'
import json,os,sys,time
reply=os.environ.get("AXIA_G07_GUI_USER_REPLY","")
with open(sys.argv[1],"x",encoding="utf-8") as f:
    json.dump({"schema":"axia.g07.c38.wslg_gui_user_observation_v1",
               "user_confirmed_3d_and_rviz":reply=="YES-G07-GUI-VISIBLE",
               "automated_wslg_pixel_certification":False,
               "goal_sent":False,"cm_120ms_checked":False,
               "formal_owner_l3_accepted":False,"certified_estop":False,
               "utc_epoch":int(time.time())},f,sort_keys=True,indent=2)
    f.write("\n")
PY
if [[ "$answer" == YES-G07-GUI-VISIBLE ]];then
  kill -0 "$GUI_PID" 2>/dev/null || hold GUI_DIED_BEFORE_USER_CONFIRMATION
  echo AXIA_G07_C38_GUI_WSLG_USER_VISUAL_CONFIRMED_NO_GOAL_NOT_FORMAL_L3
  echo AXIA_G07_C38_GUI_ONLY_CHECK_COMPLETED CM_120MS_NOT_TESTED
else
  hold GUI_USER_VISUAL_NOT_CONFIRMED_NO_GOAL
fi
