#!/usr/bin/env bash
# AXIA C29 — Instructor Windows WSL2 Ubuntu24.04 WSLg NVIDIA D3D12:
# single final NO_GOAL acceptance. Never drive/send Goal/fault/real E-stop.
# Trigger ONLY after C29 CycloneDDS full real Linux L2 2/2 PASS.
set -Eeuo pipefail
umask 077
MODE="${1:---self-check}"
if [[ "$MODE" == --self-check && $# == 1 ]];then
  echo 'C29_OWNER_SELF_CHECK_L0_PASS_NO_ROS_NO_GAZEBO_NO_GOAL'
  echo 'C29_CI_CYCLONE_NATIVE_L2_TWO_COLD=PASS_2_OF_2_RUN_44876761417'
  echo 'C29_OWNER_WSL2_L3_NOT_RUN CERTIFIED_ESTOP=false'
  exit 0
fi
[[ "$MODE" == --run && $# == 1 ]] || { echo 'C29_USAGE=--self-check|--run' >&2;exit 2; }
if [[ "${GITHUB_ACTIONS:-}" == true ]];then
  echo 'C29_OWNER_WSL2_ONLY_NO_SIMULATION' >&2;exit 3
fi
grep -Eqi 'microsoft|wsl' /proc/sys/kernel/osrelease || {
  echo 'C29_OWNER_WSL2_ONLY_NO_SIMULATION' >&2;exit 3;
}
. /etc/os-release
if [[ "${ID:-}" != ubuntu || "${VERSION_ID:-}" != 24.04 ]];then
  echo 'C29_OWNER_WSL2_UBUNTU2404_REQUIRED_NO_SIMULATION' >&2;exit 3
fi
[[ -n "${DISPLAY:-}" && -r /opt/ros/jazzy/setup.bash ]] || {
  echo 'C29_OWNER_WSLG_GUI_OR_ROS_JAZZY_MISSING_NO_SIM' >&2;exit 3
}
for bin in curl git sha256sum python3 bash tar glxinfo timeout;do
  command -v "$bin" >/dev/null || {
    echo "C29_OWNER_MISSING_PRECONDITION=$bin NO_SIM";exit 3;
  }
done
# Local process environment only. Does not modify GPU driver/Mesa config.
export MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA
if ! glxinfo -B 2>/dev/null | grep -Eiq 'OpenGL renderer string:.*D3D12.*NVIDIA';then
  echo 'C29_OWNER_NVIDIA_D3D12_REQUIRED_NO_SIMULATION' >&2;exit 3
fi
set +u
source /opt/ros/jazzy/setup.bash
set -u
[[ "${ROS_DISTRO:-}" == jazzy ]] || {
  echo 'C29_OWNER_ROS_JAZZY_REQUIRED_NO_SIMULATION' >&2;exit 3
}
# RMW selection is explicit and limited to this ONE process tree, never a
# global WSL2 configuration change. Install only the missing ROS package.
if ! test -f /opt/ros/jazzy/lib/librmw_cyclonedds_cpp.so;then
  echo 'C29_OWNER_CYCLONEDDS_PACKAGE_MISSING_INSTALLING_OFFICIAL_ROS_PACKAGE'
  command -v sudo >/dev/null || {
    echo 'C29_OWNER_CYCLONEDDS_PACKAGE_MISSING_NO_SUDO_NO_SIM';exit 3
  }
  sudo apt-get update -qq -o Acquire::Retries=2
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends ros-jazzy-rmw-cyclonedds-cpp
fi
test -f /opt/ros/jazzy/lib/librmw_cyclonedds_cpp.so || {
  echo 'C29_OWNER_CYCLONEDDS_RUNTIME_UNAVAILABLE_NO_SIM';exit 3
}
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
for flag in AXIA_G07_CI_SIM_GOAL_ALLOWED AXIA_G07_TASK04_OWNER_MOVING_L3 \
  AXIA_G07_TASK04_CI_GUI_MOVING AXIA_FAULT_INJECTION_ENABLED;do
  [[ "${!flag:-0}" != 1 ]] || {
    echo "C29_OWNER_MOVING_OR_FAULT_AUTHORITY_DENIED=$flag";exit 3;
  }
done
TMP="$(mktemp -d)"
trap 'rm -rf -- "$TMP"' EXIT
readonly PUBLIC_C28_SHA='ffe0d467e159efcf1b60da6263203d3cee86f9d5'
readonly PUBLIC_C28_BLOB='cefe00b6304c7bab0265b7b5d660cfb9a909a3a3'
readonly PUBLIC_GATE_SHA='681cab1b8f7980e25f0cae98d318116d822289a4'
readonly PUBLIC_GATE_BLOB='7221c596f002b03c9e5b36f6150364b490919ebd'
C28="$TMP/c28_owner.sh"
GATE="$TMP/c29_gate.py"
curl -fLsS --retry 3 --max-time 90 \
  "https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public/$PUBLIC_C28_SHA/d06/scripts/axia_d06_c27_owner_wsl2_nogoal_once.sh" -o "$C28"
curl -fLsS --retry 3 --max-time 90 \
  "https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public/$PUBLIC_GATE_SHA/d06/tools/d06_c29_no_goal_compact_gate.py" -o "$GATE"
[[ "$(git hash-object "$C28")" == "$PUBLIC_C28_BLOB" ]] || {
  echo 'C29_OWNER_C28_EXACT_BLOB_MISMATCH_NO_SIM';exit 3;
}
[[ "$(git hash-object "$GATE")" == "$PUBLIC_GATE_BLOB" ]] || {
  echo 'C29_OWNER_GATE_EXACT_BLOB_MISMATCH_NO_SIM';exit 3;
}
bash -n "$C28"
python3 -m py_compile "$GATE"
bash "$C28" --self-check | grep -Fq 'D06_C27_OWNER_L0_PASS_NO_ROS_NO_GAZEBO_NO_GOAL'
ROOT="$HOME/axia_c29_owner_final"
mkdir -p "$ROOT"; chmod 700 "$ROOT"
RUN="$(mktemp -d -p "$ROOT" c29-owner-XXXXXXXX)"
chmod 700 "$RUN"
echo "C29_OWNER_RMW_SELECTED=$RMW_IMPLEMENTATION"
echo "C29_OWNER_STUDENT_SHA=6c79c09d91f13c81961492eb30e66d99d307831c"
echo "C29_OWNER_CI_TWO_COLD_RUN=https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44876761417"
echo "C29_OWNER_EVIDENCE_ROOT=$RUN"

# Recover existing evidence EOF only if already present. Never replay it.
OLD_BASE="$HOME/axia_d06_c27_owner_evidence"
if [[ -d "$OLD_BASE" ]];then
  OLD_RAW="$(find "$OLD_BASE" -type f -name 'd06-wslg-sensor-*.tar.gz' \
               -printf '%T@ %p\n' | sort -nr | sed -n '1s/^[^ ]* //p')"
  if [[ -n "$OLD_RAW" && -s "$OLD_RAW.sha256" ]];then
    echo "C29_OWNER_PREVIOUS_RAW_RECOMPACT_READONLY=$OLD_RAW"
    bash "$C28" --compact-only "$OLD_RAW" \
      > "$RUN/previous_readonly_recompact.log" 2>&1 || {
      echo 'C29_OWNER_PREVIOUS_RAW_EOF_HOLD_NO_REPLAY'
    }
  else
    echo 'C29_OWNER_PREVIOUS_RAW_MISSING_KEEP_PRIOR_HOLD'
  fi
fi

# Exactly one controlled WSL2 NO_GOAL run; C27 delegates to its own
# pinned Student source and compact custody. No moving goals or faults.
OWNER_RC=0
bash "$C28" --run > "$RUN/owner_no_goal.log" 2>&1 || OWNER_RC=$?
echo "C29_OWNER_RAW_ONCE_RC=$OWNER_RC"
COMPACT="$(sed -n 's/^D06_C27_COMPACT_ARCHIVE=//p' "$RUN/owner_no_goal.log" | tail -1)"
SHA_FILE="$(sed -n 's/^D06_C27_COMPACT_SHA256=//p' "$RUN/owner_no_goal.log" | tail -1)"
[[ -z "$COMPACT" ]] || echo "C29_OWNER_FINAL_COMPACT_ARCHIVE=$COMPACT"
[[ -z "$SHA_FILE" ]] || echo "C29_OWNER_FINAL_COMPACT_SHA256=$SHA_FILE"
if [[ "$OWNER_RC" != 0 || -z "$COMPACT" || ! -s "$COMPACT" ||
      ! -s "$COMPACT.sha256" ]];then
  grep -E 'FIRST_|HOLD|NATIVE|SCAN|SHUTDOWN|OWNER_RC' \
    "$RUN/owner_no_goal.log" | tail -n 40 || true
  echo "C29_OWNER_L3_HOLD_FIRST_NATIVE_OR_SCAN_FAILURE RAW_RC=$OWNER_RC"
  echo 'AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false'
  exit 3
fi
python3 "$GATE" --verify-compact "$COMPACT" \
  > "$RUN/evidence_gate.log" 2>&1 || {
  cat "$RUN/evidence_gate.log"
  echo 'C29_OWNER_WSL2_L3_HOLD_EVIDENCE_GATE'
  echo 'AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false'
  exit 3
}
cat "$RUN/evidence_gate.log"
grep -Fq 'D06_C27_OWNER_NO_GOAL_NATIVE_CANDIDATE=true' "$RUN/owner_no_goal.log" || {
  echo 'C29_OWNER_NATIVE_CANDIDATE_MARKER_MISSING_HOLD';exit 3;
}
echo 'C29_OWNER_WSL2_NO_GOAL_L3_CANDIDATE_PASS'
echo 'C29_OWNER_REQUIRED_SAFETY_CM120_GUARD150_MOVING_NOT_VERIFIED'
echo 'AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false'
exit 0
