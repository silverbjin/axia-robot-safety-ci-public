#!/usr/bin/env bash
# AXIA P4 G11: exactly one consented G07 GUI Goal, then original archive join.
# No simulated Goal in CI, no implicit consent, no public RAW upload.
set -Eeuo pipefail
umask 077
PRIVATE_SHA="8275ecd163320aad7a3ea8b02411242cdaee50fa"
PRIVATE_TREE="1897bde19382016ae60013629d34b84901e16174"
[[ -t 0 && -t 1 && -r /dev/tty ]] || {
  echo 'AXIA_G11_G07_BLOCKED_INTERACTIVE_OWNER_TTY_REQUIRED' >&2; exit 2;
}
grep -qiE '(microsoft|wsl2)' /proc/sys/kernel/osrelease || {
  echo 'AXIA_G11_G07_BLOCKED_WSL2_REQUIRED' >&2; exit 2;
}
for c in gh git bash python3 find mktemp sha256sum; do
  command -v "$c" >/dev/null || {
    echo "AXIA_G11_G07_BLOCKED_MISSING_${c}" >&2;exit 2;
  }
done
gh auth status >/dev/null 2>&1 || {
  echo 'AXIA_G11_G07_BLOCKED_PRIVATE_GH_AUTH_REQUIRED' >&2; exit 2;
}
WORK="$(mktemp -d)"
MARKER=''
cleanup() {
  [[ -z "$MARKER" ]] || rm -f -- "$MARKER"
  rm -rf -- "$WORK"
}
trap cleanup EXIT
gh repo clone silverbjin/axia-robot-safety-instructor "$WORK/instructor" \
  -- --quiet --no-checkout --filter=blob:none >/dev/null
git -C "$WORK/instructor" fetch --quiet --depth 1 origin "$PRIVATE_SHA"
git -C "$WORK/instructor" -c advice.detachedHead=false checkout --quiet --detach FETCH_HEAD
[[ "$(git -C "$WORK/instructor" rev-parse HEAD)" == "$PRIVATE_SHA" &&
   "$(git -C "$WORK/instructor" rev-parse 'HEAD^{tree}')" == "$PRIVATE_TREE" ]] || {
  echo 'AXIA_G11_G07_BLOCKED_PRIVATE_SOURCE_OR_TREE_MISMATCH' >&2;exit 2;
}
test -f "$WORK/instructor/tools/p4_g11_g07_joined_raw_review.py"
echo "AXIA_G11_G07_PRIVATE_SOURCE_AND_TREE_VERIFIED sha=$PRIVATE_SHA"
echo 'SIMULATION ONLY: Exactly one existing P2 G07 Goal after manual Owner TTY consent.'
echo 'The existing Owner runner will require YES-P2-G07-GOAL; it is NEVER entered by this script.'
BASE="$HOME/axia_p2_private_evidence"
mkdir -p "$BASE"; chmod 700 "$BASE"
MARKER="$(mktemp "$BASE/.g11-start-XXXXXXXX")"
OWNER_RC=0
AXIA_P2_OWNER_PINNED_SHA="$PRIVATE_SHA" \
AXIA_G11_RUN_CUSTODY_REQUIRED=1 \
  bash "$WORK/instructor/scripts/p2_owner_l3_wsl2.sh" \
  --case G07 --mvp-relocated-obstacle || OWNER_RC=$?
echo "AXIA_G11_G07_OWNER_RUNNER_EXIT_CODE=$OWNER_RC"
RUN_ROOTS=()
while IFS= read -r -d '' summary; do
  RUN_ROOTS+=("${summary%/summary.json}")
done < <(find "$BASE" -mindepth 2 -maxdepth 2 -name summary.json -type f \
           -newer "$MARKER" -print0)
if (( ${#RUN_ROOTS[@]} != 1 ));then
  echo "AXIA_G11_G07_BLOCKED_NEW_RUN_ROOT_AMBIGUOUS count=${#RUN_ROOTS[@]}" >&2
  exit 3
fi
RUN_ROOT="${RUN_ROOTS[0]}"
MANIFEST="$(
python3 - "$HOME" "$RUN_ROOT" <<'PY'
from pathlib import Path
import json,sys
home=Path(sys.argv[1]).resolve()
run=Path(sys.argv[2]).resolve()
archive=run.with_suffix(".tar.gz")
side=archive.with_name(archive.name+".sha256")
try:
    checksum=side.read_text(encoding="utf-8").split()[0]
    source=(run/"source.sha").read_text(encoding="utf-8").strip()
    matches=[]
    for candidate in (home/".axia_p4_g11_session_custody"/"manifests").glob("*.json"):
        if candidate.is_symlink():continue
        try:
            j=json.loads(candidate.read_text(encoding="utf-8"))
        except (ValueError,OSError):continue
        if (j.get("archive_sha256")==checksum
                and j.get("owner_source_sha")==source
                and j.get("archive_original_relative_to_owner")==
                str(archive.relative_to(home))):
            matches.append(candidate)
    if len(matches)!=1:
        raise ValueError("G11_MANIFEST_AMBIGUOUS_OR_MISSING")
    print(matches[0])
except (OSError,ValueError,IndexError) as exc:
    print("AXIA_G11_G07_BLOCKED_MANIFEST_LOOKUP "+str(exc),file=sys.stderr)
    sys.exit(3)
PY
)" || exit 3
REVIEW_OUT="$HOME/.axia_p4_g11_session_custody/reviews/g07-$(date -u +%Y%m%dT%H%M%SZ)-$$.json"
REVIEW_RC=0
python3 "$WORK/instructor/tools/p4_g11_g07_joined_raw_review.py" \
  --owner-home "$HOME" --run-root "$RUN_ROOT" \
  --custody-manifest "$MANIFEST" --output "$REVIEW_OUT" || REVIEW_RC=$?
echo "AXIA_G11_G07_JOINED_REVIEW_EXIT_CODE=$REVIEW_RC"
echo "AXIA_G11_G07_PRIVATE_ORIGINAL=$RUN_ROOT.tar.gz"
echo "AXIA_G11_G07_FORMAL_0_OF_15_OWNER_ACCEPTANCE_HOLD CERTIFIED_ESTOP=false"
if (( OWNER_RC != 0 ));then exit "$OWNER_RC";fi
if (( REVIEW_RC != 0 ));then exit 3;fi
exit 0
