#!/usr/bin/env bash
# Owner-only GitHub administration: no Instructor Actions/ROS/Gazebo or stored tokens.
set -Eeuo pipefail
MODE="\${1:---self-check}"
if [[ $# -gt 1 || ( "$MODE" != --self-check && "$MODE" != --run ) ]]; then
  echo 'AXIA_INSTRUCTOR_ADMIN_USAGE=--self-check|--run' >&2
  exit 2
fi

REPO="silverbjin/axia-robot-safety-instructor"
BRANCH="plan/block-c-d09-d12-freeze-20261115"
MERGE="d1f10b220143b4138c260768a59c35b6166abfe1"
EXPECTED_PARENT="e2b97089239f6a444056d142e752de5591c93757"

if [[ "$MODE" == --self-check ]]; then
  echo AXIA_INSTRUCTOR_ADMIN_SELF_CHECK_PASS_NO_MUTATION
  exit 0
fi

export GH_PROMPT_DISABLED=1
command -v gh >/dev/null || {
  echo 'AXIA_INSTRUCTOR_ADMIN_HOLD_GH_CLI_MISSING' >&2; exit 2;
}
gh auth status --hostname github.com >/dev/null 2>&1 || {
  echo 'AXIA_INSTRUCTOR_ADMIN_HOLD_GH_AUTH_REQUIRED' >&2; exit 2;
}

# All preconditions MUST succeed before either administrative write.
private="$(gh api "repos/$REPO" --jq '.private')" || exit 2
if [[ "$private" != true ]]; then
  echo 'AXIA_INSTRUCTOR_ADMIN_HOLD_WRONG_REPO_VISIBILITY' >&2; exit 2;
fi
merged="$(gh api "repos/$REPO/pulls/184" --jq '.merged')" || exit 2
if [[ "$merged" != true ]]; then
  echo 'AXIA_INSTRUCTOR_ADMIN_HOLD_PR_184_NOT_MERGED' >&2; exit 2;
fi
parent="$(gh api "repos/$REPO/git/commits/$MERGE" --jq '.parents[1].sha')" || exit 2
if [[ "$parent" != "$EXPECTED_PARENT" ]]; then
  echo "AXIA_INSTRUCTOR_ADMIN_HOLD_MERGE_PARENT_CHANGED=$parent" >&2; exit 2;
fi
current="$(gh api "repos/$REPO/branches/$BRANCH" --jq '.commit.sha')" || {
  echo 'AXIA_INSTRUCTOR_ADMIN_HOLD_BRANCH_READ_FAILED_OR_ALREADY_ABSENT' >&2; exit 2;
}
if [[ "$current" != "$parent" ]]; then
  echo "AXIA_INSTRUCTOR_ADMIN_HOLD_BRANCH_SHA_CHANGED actual=$current" >&2; exit 2;
fi
enabled="$(gh api "repos/$REPO/actions/permissions" --jq '.enabled')" || {
  echo 'AXIA_INSTRUCTOR_ADMIN_HOLD_ACTIONS_READ_FORBIDDEN' >&2; exit 2;
}
if [[ "$enabled" != true && "$enabled" != false ]]; then
  echo "AXIA_INSTRUCTOR_ADMIN_HOLD_BAD_ACTIONS_STATUS=$enabled" >&2; exit 2;
fi

if [[ "$enabled" == true ]]; then
  gh api --method PUT -F enabled=false "repos/$REPO/actions/permissions" >/dev/null || {
    echo 'AXIA_INSTRUCTOR_ADMIN_HOLD_ACTIONS_DISABLE_FAILED' >&2; exit 2;
  }
fi
confirmed="$(gh api "repos/$REPO/actions/permissions" --jq '.enabled')" || exit 2
if [[ "$confirmed" != false ]]; then
  echo "AXIA_INSTRUCTOR_ADMIN_HOLD_ACTIONS_STILL_ENABLED=$confirmed" >&2; exit 2;
fi
echo 'AXIA_INSTRUCTOR_ACTIONS_DISABLED_VERIFIED enabled=false'

# Delete ONLY the reviewed merged Block C ref, never main or other branches.
gh api --method DELETE "repos/$REPO/git/refs/heads/$BRANCH" >/dev/null || {
  echo 'AXIA_INSTRUCTOR_ADMIN_HOLD_BRANCH_DELETE_FAILED' >&2; exit 2;
}
echo "AXIA_INSTRUCTOR_MERGED_BRANCH_DELETED=$BRANCH"
echo 'AXIA_INSTRUCTOR_ADMIN_COMPLETE enabled=false deleted=1'
