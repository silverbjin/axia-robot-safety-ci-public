#!/usr/bin/env bash
# C17: trusted independent NVIDIA WSLg host -> existing NO_GOAL core-or-clean trial.
# Reuses immutable C16 capability and C11 diagnosis. Never sends Goal/velocity/fault.
set -Eeuo pipefail
umask 077
MODE=--self-check
if [[ $# -gt 0 ]];then MODE="$1";fi
if [[ "$MODE" == --classify-bundle ]];then
  [[ $# == 2 ]] || exit 2
elif [[ $# == 1 && ( "$MODE" == --self-check || "$MODE" == --run-once ) ]];then
  :
else
  echo 'D06_G3_USAGE=--self-check|--run-once|--classify-bundle ARCHIVE' >&2
  exit 2
fi
if [[ "$MODE" == --self-check ]];then
  echo 'D06_G3_C17_L0_STATIC_PASS NO_ROS_NO_GAZEBO_NO_GOAL'
  echo 'AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false'
  exit 0
fi

classify_bundle() {
  local archive="$1" declared
  declared="$(sed -n 's/^[0-9a-fA-F]\{64\}  //p' "$archive.sha256" 2>/dev/null || true)"
  if [[ ! -s "$archive" || ! -s "$archive.sha256" || "$declared" != "$archive" ]] ||
     ! sha256sum -c --status "$archive.sha256";then
    echo 'D06_G3_ARCHIVE_SHA256_MISMATCH_HOLD'
    return 3
  fi
  python3 - "$archive" <<'PY'
import re,sys,tarfile
archive=sys.argv[1]
def block(marker):
    print(marker)
    print('AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false')
    raise SystemExit(3)
try:
    with tarfile.open(archive,'r:gz') as tar:
        def read(name):
            item=tar.getmember(name)
            if not item.isfile() or item.size>240000:
                block('D06_G3_BUNDLE_INVALID_SIZE_HOLD')
            src=tar.extractfile(item)
            return src.read().decode('utf-8','replace') if src else ''
        summary=read('summary.txt')
        owner=read('owner_tail.log')
        stack=read('gdb_backtrace.log')
except (OSError,tarfile.TarError,KeyError,ValueError):
    block('D06_G3_BUNDLE_INVALID_OR_MISSING_HOLD')
if 'D06_WSLG_CORE_STACK_CAPTURED_NOT_RESOLVED' in summary:
    if ('SIGSEGV' in stack or 'Segmentation fault' in stack) and re.search(r'(?m)^#0\s',stack):
        block('D06_G3_FIRST_SERVER_SIGSEGV_STACK_CAPTURED_HOLD')
    block('D06_G3_FIRST_SERVER_STACK_PROOF_INCOMPLETE_HOLD')
# Do not confuse a fixture/old archive with physical hardware acceptance.
# Even exit0 alone is insufficient without positive native+sensor+shutdown evidence.
clean=(re.search(r'(?m)^owner_rc=0$',summary) is not None
       and 'D06_WSLG_CORE_ONCE_SINGLE_NVIDIA_NO_GOAL_FORENSIC_START' in summary
       and 'D06_OWNER_NO_GOAL_NATIVE_COMPLETE_CANDIDATE' in owner
       and 'SCAN300_DUAL_20S_PASS NAV2_ACK_PASS CM_CHILD_EXIT0 GZ_CHILD_EXIT0' in owner
       and 'D06_GPU_RTF_NVIDIA_ONLY_FIRST_BLOCK=NONE' in owner
       and not re.search(r'(?i)exit code -11|segmentation fault|sigsegv',owner+summary))
if not clean:
    block('D06_G3_NO_GOAL_NATIVE_PROOF_MISSING_HOLD')
print('D06_G3_OFFLINE_BUNDLE_CLEAN_CONTRACT_HARDWARE_NOT_PROVEN')
print('AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false')
PY
}
if [[ "$MODE" == --classify-bundle ]];then
  classify_bundle "$2"
  exit $?
fi

# The explicit ACK prevents accidental use on the instructor's final-acceptance
# WSL2. It is self-attestation, not independent proof of host identity.
[[ "$(printenv AXIA_G3_ISOLATED_HOST_ACK || :)" == YES-INDEPENDENT-G3 ]] || {
  echo 'D06_G3_ISOLATED_HOST_ATTESTATION_MISSING_NO_GAZEBO' >&2;exit 3;
}
[[ "$(printenv GITHUB_ACTIONS || :)" != true ]] || {
  echo 'D06_G3_PUBLIC_ACTIONS_GPU_HOST_DENIED' >&2;exit 3;
}
for exe in curl git python3 sha256sum bash mktemp sed grep;do
  command -v "$exe" >/dev/null || {
    echo "D06_G3_MISSING_TOOL=$exe" >&2;exit 3;
  }
done
TMP="$(mktemp -d)"
trap 'rm -rf -- "$TMP"' EXIT
BASE='https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public'
CAP_SHA='32c9448b92eb7b50427d9c47b41aa2e07b17588c'
CAP_BLOB='eea3f6582eb184d9b61d0ac525d368793d11d271'
CORE_SHA='ac07c811cfa00659c296e30709f36387014cf2d6'
CORE_BLOB='c7b3e9f5372a78e6373fce086cb7ab5a65475657'
for ent in \
  "cap:$CAP_SHA:d06/tools/d06_g3_wslg_gpu_capability.py:$CAP_BLOB" \
  "core:$CORE_SHA:d06/scripts/axia_d06_g07_wslg_sigsegv_capture_once.sh:$CORE_BLOB";do
  IFS=: read -r key sha fpath expected <<< "$ent"
  curl -fLsS --retry 3 --max-time 90 "$BASE/$sha/$fpath" -o "$TMP/$key" || exit 3
  [[ "$(git hash-object "$TMP/$key")" == "$expected" ]] || {
    echo "D06_G3_PIN_BLOB_MISMATCH_HOLD=$key" >&2;exit 3;
  }
done
bash -n "$TMP/core"
if ! python3 "$TMP/cap" > "$TMP/capability.log" 2>&1 ||
   ! grep -q '^D06_G3_HOST_CANDIDATE_NOT_ACCEPTED$' "$TMP/capability.log";then
  cat "$TMP/capability.log"
  echo 'D06_G3_INDEPENDENT_WSLG_GPU_ADMISSION_HOLD_NO_GAZEBO' >&2
  exit 3
fi
# Existing first server core is analyzed WITHOUT another sim run. Otherwise
# C11 performs ONE pinned NVIDIA NO_GOAL trial and captures its first core.
echo 'D06_G3_INDEPENDENT_GPU_ADMITTED_NO_GOAL_TRIAL_ONLY'
rc=0
bash "$TMP/core" --run-once > "$TMP/core_run.log" 2>&1 || rc=$?
archive="$(sed -n 's/^D06_WSLG_CORE_ONCE_FORENSIC_ARCHIVE=//p' "$TMP/core_run.log" | tail -1)"
[[ "$archive" == "$HOME/axia_d06_g07_wslg_core_once/"trace-*.tar.gz ]] || {
  echo 'D06_G3_FIRST_RUN_ARCHIVE_MISSING_HOLD' >&2;exit 3;
}
echo "D06_G3_FIRST_RUN_ARCHIVE=$archive"
echo "D06_G3_FIRST_RUN_SHA256=$archive.sha256"
echo "D06_G3_C11_DIAGNOSTIC_RC=$rc"
if classify_bundle "$archive";then
  echo 'D06_G3_NATIVE_NO_GOAL_CLEAN_CANDIDATE_NOT_MOVING_L3'
  echo 'D06_G3_ACTUAL_HOST_TRIAL_CANDIDATE_NOT_GLOBAL_RELIABILITY'
  echo 'AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false'
else
  exit 3
fi
