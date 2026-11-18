#!/usr/bin/env bash
# AXIA D08 WSL2/WSLg NO_GOAL acceptance launcher.
# Distribution-only wrapper: freezes the already-proven public CI source.
# CI GREEN = public #44310101993, 4 jobs success; Owner L3 is separate.
set -Eeuo pipefail
umask 077

MODE="${1:---run}"
case "$MODE" in
  --self-check|--doctor|--run) ;;
  *) echo 'D08_OWNER_USAGE=--self-check|--doctor|--run' >&2; exit 2 ;;
esac

# Immutable source with real one-world Gazebo/AMCL/Path L2 proof.
PINNED_SHA='342c6355b27af5b8b11a79b7e345820be18a581f'
BOOTSTRAP_BLOB='bad5b738e57827a102ebe56595d3b4b7dc3e6f83'
BOOTSTRAP_PATH='d08/scripts/d08_owner_no_goal_bootstrap.sh'
PUBLIC_URL="https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public/${PINNED_SHA}/${BOOTSTRAP_PATH}"

if [[ "$MODE" == --self-check ]]; then
  bash -n "$0"
  echo "D08_OWNER_PINNED_PUBLIC_SHA=${PINNED_SHA}"
  echo 'D08_OWNER_WRAPPER_L0_PASS_NO_ROS_GAZEBO_RUN'
  exit 0
fi

# Local WSL2 only; never auto-drive a moving robot or modify a main branch.
command -v curl >/dev/null 2>&1 || {
  echo D08_OWNER_CURL_REQUIRED >&2; exit 2;
}
command -v git >/dev/null 2>&1 || {
  echo D08_OWNER_GIT_REQUIRED_FOR_BLOB_VERIFICATION >&2; exit 2;
}
BASE="${AXIA_D08_ACCEPTANCE_ROOT:-$HOME/axia_d08_owner_acceptance}"
mkdir -p -- "$BASE"
RUN_DIR="$(mktemp -d "$BASE/acceptance_$(date -u +%Y%m%dT%H%M%SZ)_XXXXXX")"
SCRIPT="$RUN_DIR/d08_owner_no_goal_bootstrap.sh"
LOG="$RUN_DIR/acceptance.log"
echo "D08_OWNER_ACCEPTANCE_DIR=$RUN_DIR"
echo "D08_OWNER_PINNED_PUBLIC_SHA=$PINNED_SHA"

echo "D08_OWNER_PUBLIC_SOURCE_FETCH_BEGIN=$PUBLIC_URL"
curl --fail --show-error --silent --location --retry 3 \
     --connect-timeout 15 --max-time 120 "$PUBLIC_URL" -o "$SCRIPT" || {
  echo D08_OWNER_BOOTSTRAP_DOWNLOAD_BLOCKED >&2; exit 2;
}
ACTUAL_BLOB="$(git hash-object "$SCRIPT")"
if [[ "$ACTUAL_BLOB" != "$BOOTSTRAP_BLOB" ]]; then
  echo "D08_OWNER_BOOTSTRAP_BLOB_MISMATCH=$ACTUAL_BLOB" >&2
  echo "D08_OWNER_EXPECTED_BOOTSTRAP_BLOB=$BOOTSTRAP_BLOB" >&2
  exit 2
fi
bash -n "$SCRIPT"
echo "D08_OWNER_BOOTSTRAP_BLOB_VERIFIED=$ACTUAL_BLOB"
export AXIA_D08_PUBLIC_SHA="$PINNED_SHA"

# Always perform the immutable bootstrap's non-Gazebo local check first.
bash "$SCRIPT" --self-check | tee "$RUN_DIR/self_check.log"

if [[ "$MODE" == --doctor ]]; then
  bash "$SCRIPT" --doctor 2>&1 | tee "$RUN_DIR/doctor.log"
  echo D08_OWNER_DOCTOR=COMPLETE_NOT_RUNTIME_PASS
  echo D08_OWNER_WSLG_VISUAL=OWNER_CONFIRM_REQUIRED
  exit 0
fi

# Single run: doctor → exact-source GUI. Bootstrap itself prepares official
# dependencies, retains raw evidence and creates a bounded private ZIP.
bash "$SCRIPT" --doctor 2>&1 | tee "$RUN_DIR/doctor.log"
echo 'D08_OWNER_NO_GOAL_GUI_RUN_BEGIN'
echo 'D08_OWNER_GUI_EXIT=Ctrl+C (after visual acceptance)'
echo "D08_OWNER_ACCEPTANCE_RUN_LOG=$LOG"
if bash "$SCRIPT" --run 2>&1 | tee "$LOG"; then
  if ! grep -Fq 'D08_OWNER_GUI_NO_GOAL_RUNTIME_EXIT0' "$LOG"; then
    echo D08_OWNER_RUNTIME=BLOCKED >&2
    echo D08_OWNER_FIRST_BOUNDARY=RUNTIME_EXIT0_SENTINEL_MISSING >&2
    exit 2
  fi
  echo D08_OWNER_RUNTIME=PASS_CANDIDATE_NO_GOAL_ONLY
  echo D08_OWNER_WSLG_VISUAL=OWNER_CONFIRM_REQUIRED
  echo D08_MOVING_E2E_ACCEPTED=HOLD
  echo D08_CM_GUARD_INTERNAL_TTL=NOT_VERIFIED
  echo "D08_OWNER_ACCEPTANCE_RUN_LOG=$LOG"
  echo "D08_OWNER_ACCEPTANCE_DIR=$RUN_DIR"
else
  rc=$?
  echo D08_OWNER_RUNTIME=BLOCKED >&2
  echo "D08_OWNER_SCRIPT_EXIT_RC=$rc" >&2
  echo "D08_OWNER_ACCEPTANCE_RUN_LOG=$LOG" >&2
  echo "D08_OWNER_ACCEPTANCE_DIR=$RUN_DIR" >&2
  exit "$rc"
fi
