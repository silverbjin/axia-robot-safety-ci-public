#!/usr/bin/env bash
# C20: Ubuntu24.04 WSL2 missing coredumpctl recovery, exact old Gazebo core only.
# NO new Gazebo, ROS, Goal, fault, RMW or renderer changes.
set -Eeuo pipefail
umask 077
MODE="${1:---self-check}"
[[ $# -le 1 && ( "$MODE" == --self-check || "$MODE" == --run ) ]] || {
  echo 'D06_C20_USAGE=--self-check|--run' >&2
  exit 2
}
if [[ "$MODE" == --self-check ]];then
  echo 'D06_C20_STATIC_L0_PASS_NO_ROS_NO_GAZEBO'
  echo 'D06_C20_HOST_DEPENDENCIES_NOT_TESTED'
  echo 'AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false'
  exit 0
fi
[[ "${GITHUB_ACTIONS:-false}" != true ]] || {
  echo 'D06_C20_HOLD_PUBLIC_RUNNER_IS_NOT_FIELD_WSL2' >&2
  exit 3
}
grep -qiE 'microsoft|wsl' /proc/sys/kernel/osrelease || {
  echo 'D06_C20_HOLD_WSL2_HOST_REQUIRED' >&2
  exit 3
}
# Only clean Ubuntu 24.04 is in the C12/C13 package-regression scope.
# Do not use a package guessed for a different OS.
. /etc/os-release
[[ "${ID:-}" == ubuntu && "${VERSION_ID:-}" == 24.04 ]] || {
  echo 'D06_C20_HOLD_UBUNTU2404_REQUIRED' >&2
  exit 3
}
for exe in git curl bash sha256sum python3;do
  command -v "$exe" >/dev/null || {
    echo "D06_C20_HOLD_MISSING_TOOL=$exe" >&2
    exit 3
  }
done
echo 'D06_C20_NO_NEW_SIMULATION_ONLY_EXISTING_CORE_PID_19280'
echo 'D06_C20_POSTCRASH_INSTALL_CANNOT_RECREATE_OLD_CORE'
echo "D06_C20_CORE_PATTERN_BEFORE=$(cat /proc/sys/kernel/core_pattern 2>/dev/null || true)"
echo "D06_C20_INIT1=$(ps -p 1 -o comm= 2>/dev/null || true)"
if ! command -v coredumpctl >/dev/null 2>&1;then
  echo 'D06_C20_SYSTEMD_COREDUMP_INSTALL_REQUIRED'
  command -v sudo >/dev/null || {
    echo 'D06_C20_HOLD_SUDO_NOT_AVAILABLE_NO_GAZEBO' >&2
    exit 3
  }
  # Only installs the official package verified by public Ubuntu24 CI;
  # no driver, ROS, Mesa, RMW or kernel override.
  if ! sudo apt-get update -qq -o Acquire::Retries=2;then
    echo 'D06_C20_HOLD_APT_INDEX_FAILED_NO_GAZEBO' >&2
    exit 3
  fi
  if ! sudo env DEBIAN_FRONTEND=noninteractive apt-get install -y \
    --no-install-recommends systemd-coredump;then
    echo 'D06_C20_HOLD_APT_PACKAGE_INSTALL_FAILED_NO_GAZEBO' >&2
    exit 3
  fi
fi
if ! command -v coredumpctl >/dev/null 2>&1;then
  echo 'D06_C20_HOLD_COREDUMPCTL_STILL_MISSING_NO_GAZEBO' >&2
  exit 3
fi
help_text="$(coredumpctl --help 2>&1)" || {
  echo 'D06_C20_HOLD_COREDUMPCTL_NOT_EXECUTABLE_NO_GAZEBO' >&2
  exit 3
}
[[ "$help_text" == *--json* ]] || {
  echo 'D06_C20_HOLD_COREDUMPCTL_JSON_UNSUPPORTED_NO_GAZEBO' >&2
  exit 3
}
echo 'D06_C20_COREDUMPCTL_CLI_PRESENT_BACKEND_NOT_PROVEN'
echo "D06_C20_CORE_PATTERN_AFTER=$(cat /proc/sys/kernel/core_pattern 2>/dev/null || true)"
# Reuse the public-CI GREEN C19 tool unchanged; exact blob verification.
SHA='1f0c5e9fffd0d40d151129dd72b6eb840266655a'
BLOB='3ba68b695c91d058604b9cfc9c37e4a3cd0d257d'
TMP="$(mktemp --suffix=.sh)"
trap 'rm -f "$TMP"' EXIT
curl -fLsS --retry 3 --max-time 90 \
  "https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public/$SHA/d06/scripts/axia_d06_g07_wslg_sigsegv_capture_once.sh" \
  -o "$TMP"
[[ "$(git hash-object "$TMP")" == "$BLOB" ]] || {
  echo 'D06_C20_HOLD_C19_BLOB_MISMATCH_NO_GAZEBO' >&2
  exit 3
}
bash -n "$TMP"
echo 'D06_C20_EXACT_PRIOR_PID_CORE_INSPECTION_START_NO_GAZEBO'
AXIA_D06_EXPECTED_GAZEBO_PID=19280 bash "$TMP" --existing-only
