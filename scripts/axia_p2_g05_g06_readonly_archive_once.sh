#!/usr/bin/env bash
# AXIA G05/G06 historical TAR audit. READ ONLY. NO Gazebo, NO ROS, NO Goal, NO Fault.
set -Eeuo pipefail

readonly PUBLIC_SOURCE_SHA='300cb4688a97a75156699f63552cc7efb1c38e04'
readonly PYTHON_BLOB_SHA='e67bec69a1138c9e6b54641c3fa62bacac8bb6c7'
readonly KNOWN_XJX_SHA256='da256a25382e78b0b4a590724e89de6c9d4242f8ac035b55157f67f7a274c51c'

if [[ "${1:-}" == '--self-check' && "$#" -eq 1 ]]; then
  [[ "$PUBLIC_SOURCE_SHA" =~ ^[0-9a-f]{40}$ && "$PYTHON_BLOB_SHA" =~ ^[0-9a-f]{40}$ ]]
  echo "AXIA_P2_READONLY_WRAPPER_STATIC_PASS NO_ROS NO_GOAL NO_FAULT NO_UPLOAD"
  exit 0
fi
if [[ "$#" -ne 0 ]]; then
  echo 'AXIA_P2_ARCHIVE_BLOCKED ARGUMENTS_UNSUPPORTED' >&2
  exit 2
fi

command -v python3 >/dev/null || { echo 'AXIA_P2_ARCHIVE_BLOCKED python3_required' >&2; exit 2; }
command -v git >/dev/null || { echo 'AXIA_P2_ARCHIVE_BLOCKED git_required' >&2; exit 2; }
command -v curl >/dev/null || { echo 'AXIA_P2_ARCHIVE_BLOCKED curl_required' >&2; exit 2; }

OWNER_HOME="$(realpath "$HOME")"
ROOT="${AXIA_P2_ARCHIVE_ROOT:-$OWNER_HOME/axia_p2_private_evidence}"
if [[ -z "${AXIA_P2_ARCHIVE_ROOT:-}" && ! -d "$ROOT" ]]; then
  ROOT="$OWNER_HOME" # targeted filenames only; fallback when historical private root moved
fi
[[ -d "$ROOT" && ! -L "$ROOT" ]] || {
  echo 'AXIA_P2_ARCHIVE_BLOCKED PRIVATE_ARCHIVE_ROOT_NOT_FOUND' >&2; exit 2;
}
ROOT="$(realpath "$ROOT")"
case "$ROOT" in
  "$OWNER_HOME"|"$OWNER_HOME"/*) ;;
  *) echo 'AXIA_P2_ARCHIVE_BLOCKED ROOT_OUTSIDE_OWNER_HOME' >&2; exit 2 ;;
esac

readonly BASE_URL="https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public/${PUBLIC_SOURCE_SHA}"
TMP="$(mktemp -d)"
trap 'rm -rf -- "$TMP"' EXIT
curl -fsSL --retry 3 --max-time 30 \
  "${BASE_URL}/tools/axia_p2_archive_integrity_audit.py" \
  -o "$TMP/axia_p2_archive_integrity_audit.py"
[[ "$(git hash-object "$TMP/axia_p2_archive_integrity_audit.py")" == "$PYTHON_BLOB_SHA" ]] || {
  echo 'AXIA_P2_ARCHIVE_BLOCKED DOWNLOADED_PYTHON_BLOB_MISMATCH' >&2; exit 2;
}

# Only three already-recorded historical runs; never scan unrelated private material.
mapfile -d '' -t ARCHIVES < <(
  find "$ROOT" -maxdepth 7 -type f \( \
    -name 'p2-l3-owner-Xjx3vO6q.tar.gz' -o \
    -name 'p2-l3-owner-kIeflSg4.tar.gz' -o \
    -name 'p2-l3-owner-ulbEs3NU.tar.gz' \
  \) -print0
)
if [[ "${#ARCHIVES[@]}" -eq 0 ]]; then
  echo 'AXIA_P2_ARCHIVE_BLOCKED HISTORICAL_TAR_NOT_FOUND_NO_RERUN_REQUIRED' >&2
  exit 2
fi
if [[ "${#ARCHIVES[@]}" -gt 3 ]]; then
  echo 'AXIA_P2_ARCHIVE_BLOCKED AMBIGUOUS_DUPLICATE_TARS' >&2
  exit 2
fi
ARGS=(--out-dir "$OWNER_HOME/.axia_p2_private_archive_audit")
for ARCHIVE in "${ARCHIVES[@]}"; do
  ARGS+=(--archive "$ARCHIVE")
  if [[ "$(basename "$ARCHIVE")" == 'p2-l3-owner-Xjx3vO6q.tar.gz' ]]; then
    ARGS+=(--expect "p2-l3-owner-Xjx3vO6q.tar.gz=${KNOWN_XJX_SHA256}")
  fi
done
python3 "$TMP/axia_p2_archive_integrity_audit.py" "${ARGS[@]}"
