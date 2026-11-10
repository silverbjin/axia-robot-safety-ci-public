#!/usr/bin/env bash
# D08 single-world GUI WSL2 Owner demo. SIM ONLY. Never auto-approves Goal.
set -Eeuo pipefail
umask 077
readonly PRIVATE_REPO='silverbjin/axia-robot-safety-instructor'
readonly PRIVATE_BRANCH='feature/d08-gazebo-live-one-world-20261110'
readonly PRIVATE_SHA='5f2a15ef3ea0a7866bce15b66f2ecd48d28e959e'
readonly D04_SOURCE_SHA='c775820077917c4da56c6aa60001b224071664b3'
readonly YOLO_SHA='94d2dd500cb26027ee9c019f4d3a02029ac615cc'
readonly ONNX_SHA='4f44c33cea12d4b5785e5e7c0a20c13d0c62a77de607ce96a40d6036c7d7bbcf'
readonly ACTOR_SHA='49af0df3a319d1cb8ca2cebf02dbd00f625e5d5bec820bc5e109925b18b65c6e'

if [[ "${1:-}" == '--self-check' ]];then
  [[ $# == 1 && "$PRIVATE_SHA" =~ ^[a-f0-9]{40}$ ]] || exit 2
  echo "D08_LIVE_WRAPPER_STATIC_PASS private_sha=$PRIVATE_SHA GAZEBO_NOT_RUN"
  exit 0
fi
[[ $# == 0 ]] || { echo 'D08_LIVE_BLOCKED: no arguments accepted' >&2;exit 2; }
[[ -t 0 && -t 1 && -r /dev/tty ]] || {
  echo 'D08_LIVE_BLOCKED: real Owner interactive TTY is required' >&2;exit 2;
}
[[ -n "${DISPLAY:-}" ]] || {
  echo 'D08_LIVE_BLOCKED: WSLg DISPLAY missing; cannot verify visible GUI' >&2;exit 2;
}
[[ -z "${VIRTUAL_ENV:-}" ]] || {
  echo 'D08_LIVE_BLOCKED: deactivate Python venv before ROS 2 Jazzy run' >&2;exit 2;
}
source /etc/os-release
[[ "$ID" == ubuntu && "$VERSION_ID" == '24.04' ]] || {
  echo 'D08_LIVE_BLOCKED: Ubuntu 24.04 required' >&2;exit 2;
}
grep -qiE 'wsl|microsoft' /proc/sys/kernel/osrelease || {
  echo 'D08_LIVE_BLOCKED: WSL2 required' >&2;exit 2;
}
[[ -f /opt/ros/jazzy/setup.bash ]] || {
  echo 'D08_LIVE_BLOCKED: ROS Jazzy missing' >&2;exit 2;
}
for tool in bash gh git curl sha256sum python3 gz ros2 colcon;do
  command -v "$tool" >/dev/null || {
    echo "D08_LIVE_BLOCKED: missing $tool" >&2;exit 2;
  }
done
gh auth status >/dev/null 2>&1 || {
  echo 'D08_LIVE_BLOCKED: gh auth login to read private instructor repo' >&2;exit 2;
}
# System Python is required for ROS Jazzy launch_testing/yaml; never use D08 .venv.
if ! /usr/bin/python3 -c 'import yaml' >/dev/null 2>&1;then
  sudo apt-get update -qq
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq python3-yaml
  /usr/bin/python3 -c 'import yaml'
fi

# Reuse D04 GUI asset/model/upstream YOLO cache; if missing, execute exactly
# one existing SHA-pinned D04 no-Goal verified preparation/demo once.
CACHE="$HOME/.cache/axia/d04"
ASSET="$CACHE/assets"
YOLO_INSTALL="$CACHE/yolo_ws_$YOLO_SHA/install/local_setup.bash"
READY=1
[[ -f "$YOLO_INSTALL" && -f "$ASSET/yolo26n.onnx" && -f "$ASSET/walk.dae" ]] || READY=0
if [[ "$READY" == 1 ]];then
  echo "$ONNX_SHA  $ASSET/yolo26n.onnx" | sha256sum -c - >/dev/null || READY=0
  echo "$ACTOR_SHA  $ASSET/walk.dae" | sha256sum -c - >/dev/null || READY=0
fi
if [[ "$READY" == 0 ]];then
  echo '[D08] Missing D04 cached assets or upstream YOLO; provisioning via approved D04 one-shot'
  PREP="$(mktemp --suffix=.sh)"
  curl -fL -sS --retry 3 \
    "https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public/$D04_SOURCE_SHA/scripts/axia_d04_ros_package_wsl2_once.sh" \
    -o "$PREP"
  bash -n "$PREP"
  AXIA_D04_PUBLIC_SHA="$D04_SOURCE_SHA" AXIA_D04_REPEAT=1 \
    AXIA_D04_GUI=1 AXIA_D04_DEMO_HOLD_S=5 \
    env -u AMENT_PREFIX_PATH -u COLCON_PREFIX_PATH -u CMAKE_PREFIX_PATH \
      -u PYTHONPATH -u LD_LIBRARY_PATH -u ROS_DISTRO -u ROS_VERSION \
      -u ROS_PYTHON_VERSION -u ROS_PACKAGE_PATH -u BASH_ENV \
      bash --noprofile --norc "$PREP"
  rm -f -- "$PREP"
fi
[[ -f "$YOLO_INSTALL" ]] || { echo 'D08_LIVE_BLOCKED: yolo_ros not available after D04' >&2;exit 2; }
echo "$ONNX_SHA  $ASSET/yolo26n.onnx" | sha256sum -c -
echo "$ACTOR_SHA  $ASSET/walk.dae" | sha256sum -c -

SRC="$(mktemp -d "$HOME/.axia_d08_gazebo_owner_XXXXXXXX")"
finish() {
  rc=$?
  trap - EXIT INT TERM
  cd "$HOME" || cd /
  if [[ -d "$SRC" && "$SRC" == "$HOME"/.axia_d08_gazebo_owner_* ]];then
    rm -rf -- "$SRC"
  fi
  exit "$rc"
}
trap finish EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
gh repo clone "$PRIVATE_REPO" "$SRC/instructor" -- \
  --single-branch --branch "$PRIVATE_BRANCH" --depth 1
[[ "$(git -C "$SRC/instructor" rev-parse HEAD)" == "$PRIVATE_SHA" ]] || {
  echo 'D08_LIVE_BLOCKED: private source SHA changed; stop instead of silently using untested code' >&2;exit 2;
}
[[ -z "$(git -C "$SRC/instructor" status --porcelain)" ]] || {
  echo 'D08_LIVE_BLOCKED: private checkout has changes' >&2;exit 2;
}
# Validate the exact private teacher reference and pure data converters BEFORE
# starting any ROS/Gazebo or an authorized Goal. No pytest/ROS plugin autoload.
bash -n "$SRC/instructor/scripts/p2_owner_l3_wsl2.sh"
env -u PYTHONPATH -u AMENT_PREFIX_PATH -u COLCON_PREFIX_PATH \
    -u CMAKE_PREFIX_PATH -u LD_LIBRARY_PATH -u BASH_ENV \
    AXIA_D08_PRIVATE_SRC="$SRC/instructor" /usr/bin/python3 - <<'PY'
import importlib.util, os, struct, sys
from pathlib import Path
from types import SimpleNamespace
root=Path(os.environ['AXIA_D08_PRIVATE_SRC'])
targets=('d08_live_world','d08_live_readonly_probe','d08_nav2_path_preflight')
sys.path.insert(0,str(root/'tools'))
modules={}
for name in targets:
    spec=importlib.util.spec_from_file_location(name,root/'tools'/(name+'.py'))
    assert spec and spec.loader
    obj=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    modules[name]=obj
data=b''.join(struct.pack('<f',1.65) for _ in range(12*10))
img=SimpleNamespace(width=12,height=10,step=48,encoding='32FC1',
 is_bigendian=False,data=data,
 header=SimpleNamespace(stamp=SimpleNamespace(sec=11,nanosec=0)))
bbox=dict(x1=3,y1=2,x2=9,y2=8,image_width=12,image_height=10)
ref=modules['d08_live_readonly_probe'].measure_real_person(img,bbox,11_000_000_000)
assert ref is not None and abs(ref['distance_m']-1.65)<1e-5
assert modules['d08_live_readonly_probe'].measure_real_person(
    img,bbox,10_800_000_000) is None
print('D08_PRIVATE_PREFLIGHT_STATIC_PASS D05_REFERENCE_32FC1_PASS NO_ROS_NO_GOAL',flush=True)
PY
export AXIA_D08_GAZEBO_GUI=1
export AXIA_P2_OWNER_PINNED_SHA="$PRIVATE_SHA"
echo '============================================================'
echo 'D08 Gazebo GUI: Waffle + visual Actor + physical cylinder + RGBD/YOLO'
echo 'SIMULATION ONLY: actor is NOT synchronized with LiDAR cylinder.'
echo 'Moving Goal requires your explicit manual YES-P2-G07-GOAL.'
echo 'If RGBD/YOLO/D05 is not ready, abort BEFORE moving robot.'
echo '============================================================'
# Only the child interpreter environment is sanitized; no change to
# the Owner's shell, GUI DISPLAY, files or other independent ROS workspaces.
# ROS Jazzy and cached YOLO local_setup are sourced anew in the child.
echo 'D08_CLEAN_ROS_ENV_ENABLED: dropping stale D03 underlay paths in child'
env -u AMENT_PREFIX_PATH -u COLCON_PREFIX_PATH -u CMAKE_PREFIX_PATH \
    -u PYTHONPATH -u LD_LIBRARY_PATH -u ROS_DISTRO -u ROS_VERSION \
    -u ROS_PYTHON_VERSION -u ROS_PACKAGE_PATH -u BASH_ENV \
    bash --noprofile --norc "$SRC/instructor/scripts/p2_owner_l3_wsl2.sh" --case G07 --mvp-one-goal
