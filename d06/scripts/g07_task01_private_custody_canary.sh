#!/usr/bin/env bash
# CI-only pre-Goal private-custody remote round-trip gate.
# NO ROS, NO Goal, NO private/raw evidence printed to public logs.
set -Eeuo pipefail
umask 077

: "${AXIA_G07_TASK01_PRIVATE_CUSTODY_DIR:?private Instructor checkout required}"
: "${AXIA_G07_EVIDENCE_WRITE_TOKEN:?narrow private evidence write token required}"
: "${GITHUB_RUN_ID:?GitHub run id required}"
: "${GITHUB_SHA:?immutable public commit required}"

if [[ "${GITHUB_ACTIONS:-}" != true || "${AXIA_P0_SIM_ONLY:-0}" != 1 ||
      "${AXIA_G07_TASK01_GOAL_ALLOWED:-0}" != 0 ]]; then
  echo AXIA_G07_TASK01_PRIVATE_CUSTODY_SCOPE_UNAUTHORIZED_NO_GOAL >&2
  exit 3
fi

if [[ ! "$GITHUB_RUN_ID" =~ ^[0-9]+$ ||
      ! "$GITHUB_SHA" =~ ^[0-9a-f]{40}$ ]]; then
  echo AXIA_G07_TASK01_PRIVATE_CUSTODY_SHA_OR_RUN_INVALID >&2
  exit 3
fi

CUSTODY_BRANCH=evidence/g07-cm120-task01-20261117
PRIVATE_REPO=silverbjin/axia-robot-safety-instructor
D="$AXIA_G07_TASK01_PRIVATE_CUSTODY_DIR"
test -d "$D/.git"
test "$(git -C "$D" branch --show-current)" = "$CUSTODY_BRANCH"
ORIGIN="$(git -C "$D" remote get-url origin)"
if [[ "$ORIGIN" != "https://github.com/$PRIVATE_REPO" &&
      "$ORIGIN" != "https://github.com/$PRIVATE_REPO.git" ]]; then
  echo AXIA_G07_TASK01_PRIVATE_CUSTODY_ORIGIN_MISMATCH >&2
  exit 3
fi

# No bearer credential in source, repository config, or public log.
AUTH="$(printf 'x-access-token:%s' "$AXIA_G07_EVIDENCE_WRITE_TOKEN" | base64 -w0)"
REL="diagnostic_evidence/g07_cm120_task01/canary_${GITHUB_RUN_ID}.txt"
mkdir -p "$D/$(dirname "$REL")"
printf 'AXIA_G07_TASK01_PREGOAL_PRIVATE_CANARY_V1\nrun_id=%s\nsource_sha=%s\ngoal_sent=false\n' \
  "$GITHUB_RUN_ID" "$GITHUB_SHA" >"$D/$REL"
LOCAL_SHA="$(sha256sum "$D/$REL" | awk '{print $1}')"
git -C "$D" config user.name "AXIA CI Evidence"
git -C "$D" config user.email "axia-ci-evidence@users.noreply.github.com"
git -C "$D" add -- "$REL"
git -C "$D" commit -m "evidence(g07 task01): pregoal private SHA256 canary run $GITHUB_RUN_ID" >/dev/null

# A missing write permission, wrong branch, or remote round-trip blocks Goal.
PUSH_ERR="$(mktemp)"
if ! git -C "$D" -c "http.extraheader=AUTHORIZATION: basic $AUTH" \
  push origin "HEAD:refs/heads/$CUSTODY_BRANCH" >/dev/null 2>"$PUSH_ERR"; then
  # Never expose a Git transport stderr that could contain a credential URL.
  DIAG=UNCLASSIFIED_REMOTE_REJECTION
  if grep -Eqi 'write access to repository not granted|permission.*denied|403|authentication failed' "$PUSH_ERR"; then
    DIAG=AUTH_OR_CONTENT_WRITE_DENIED
  elif grep -Eqi 'protected branch|GH006|GH013|repository rule' "$PUSH_ERR"; then
    DIAG=BRANCH_PROTECTION_REJECTED
  elif grep -Eqi 'non-fast-forward|fetch first|stale info' "$PUSH_ERR"; then
    DIAG=REMOTE_HEAD_CONFLICT
  fi
  rm -f -- "$PUSH_ERR"
  echo "AXIA_G07_TASK01_PRIVATE_REMOTE_PUSH_FAILED_NO_GOAL class=$DIAG" >&2
  exit 3
fi
rm -f -- "$PUSH_ERR"
git -C "$D" -c "http.extraheader=AUTHORIZATION: basic $AUTH" \
  fetch --no-tags --depth=1 origin "refs/heads/$CUSTODY_BRANCH" >/dev/null 2>&1 || {
  echo AXIA_G07_TASK01_PRIVATE_REMOTE_READBACK_FAILED_NO_GOAL >&2
  exit 3
}
REMOTE_SHA="$(git -C "$D" show "FETCH_HEAD:$REL" | sha256sum | awk '{print $1}')" || {
  echo AXIA_G07_TASK01_PRIVATE_REMOTE_SHA_READBACK_FAILED_NO_GOAL >&2
  exit 3
}
unset AUTH
if [[ "$REMOTE_SHA" != "$LOCAL_SHA" ]]; then
  echo AXIA_G07_TASK01_PRIVATE_REMOTE_SHA_MISMATCH_NO_GOAL >&2
  exit 3
fi

echo "AXIA_G07_TASK01_PRIVATE_SHA256_CANARY_PASS run_id=$GITHUB_RUN_ID sha256=$LOCAL_SHA"
echo AXIA_G07_TASK01_CUSTODY_PREFLIGHT_ONLY_NO_ROS_NO_GOAL
