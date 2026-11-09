#!/usr/bin/env bash
# P2 G06 only. Owner runs locally; no automatic YES, no uncertified E-Stop claims.
set -Eeuo pipefail
umask 077
REPO='silverbjin/axia-robot-safety-ci-public'
ENVIRONMENT='axia-instructor-sealed'
BRANCH='release/p2-g06-cm-ttl-20261110'
RUN='42655414492'
CI_SHA='c14819c7109fc143de14cc7935880b922c2d0074'
PRIVATE_SHA='276c13d4d046df0f0ee73e7953d7639f312e0029'
WRAPPER_BLOB='441e40a5c1d8dfb65dfb2d1c358f77d652debe73'
if [[ "${1:-}" == "--self-check" ]]; then
  echo "P2_G06_CI_RECOVER_STATIC_OK $PRIVATE_SHA L3_NOT_RUN"; exit 0
fi
[[ $# == 0 && -t 0 && -t 1 && -r /dev/tty ]] || {
  echo 'BLOCKED: interactive Owner TTY required; no action performed' >&2;exit 2;
}
for cmd in gh python3 curl git bash timeout;do
  command -v "$cmd" >/dev/null || { echo "BLOCKED: missing $cmd" >&2;exit 2; }
done
gh auth status >/dev/null || exit 2
run_info="$(gh api "repos/$REPO/actions/runs/$RUN")"
printf '%s' "$run_info" | python3 -c '
import json,sys
r=json.load(sys.stdin)
assert r.get("head_branch")=="release/p2-g06-cm-ttl-20261110"
assert r.get("head_sha")=="c14819c7109fc143de14cc7935880b922c2d0074"
assert r.get("event")=="push"
print("PINNED_CI_RUN_VERIFIED")
' || exit 2
meta="$(gh api "repos/$REPO/environments/$ENVIRONMENT")" || {
  echo 'BLOCKED: no Environment settings read permission' >&2;exit 2;
}
mode="$(printf '%s' "$meta" | python3 -c '
import json,sys
p=json.load(sys.stdin).get("deployment_branch_policy")
print("any" if p is None else "custom" if p.get("custom_branch_policies") else "protected" if p.get("protected_branches") else "unknown")
')"
case "$mode" in
  custom)
    patterns="$(gh api "repos/$REPO/environments/$ENVIRONMENT/deployment-branch-policies?per_page=100" \
       --jq '.branch_policies[].name')" || exit 2
    if printf '%s\n' "$patterns" | grep -Fxq "$BRANCH";then
      echo "G06_CI_ENV_ALREADY_ALLOWED=$BRANCH"
    else
      echo "G06_CI_ENV_ADD_EXACT_BRANCH=$BRANCH"
      gh api -X POST "repos/$REPO/environments/$ENVIRONMENT/deployment-branch-policies" \
        -f "name=$BRANCH" -f 'type=branch' >/dev/null || exit 2
    fi;;
  any) echo 'G06_CI_ENV_UNRESTRICTED';;
  protected)
    echo "BLOCKED: protected-branches-only. No weakening of policy attempted." >&2
    exit 2;;
  *) echo 'BLOCKED: unknown Environment deployment policy' >&2;exit 2;;
esac
gh run view "$RUN" -R "$REPO" --json jobs | python3 -c '
import json,sys
j={a["name"]:a["conclusion"] for a in json.load(sys.stdin)["jobs"]}
assert j.get("public-contract")=="success", "Original public contract not PASS"
print("PUBLIC_CONTRACT_PREVIOUSLY_PASS")
' || exit 2
echo 'RETRY_ONLY_FAILED_JOBS_ONCE'
gh run rerun "$RUN" -R "$REPO" --failed || exit 2
set +e
timeout --signal=TERM --kill-after=5s 1200 gh run watch "$RUN" -R "$REPO" --exit-status --interval 10
RC=$?
set -e
if [[ $RC != 0 ]];then
  echo "BLOCKED: CI did not pass, G06 NOT RUN, watch_rc=$RC" >&2
  gh run view "$RUN" -R "$REPO" --json status,conclusion,jobs || true
  exit 2
fi
gh run view "$RUN" -R "$REPO" --json conclusion,jobs | python3 -c '
import json,sys
v=json.load(sys.stdin)
j={a["name"]:a["conclusion"] for a in v["jobs"]}
for n in ("private-l0","private-l1-cm-loss"):print(n,j.get(n))
assert v.get("conclusion")=="success"
assert all(j.get(n)=="success" for n in ("private-l0","private-l1-cm-loss"))
print("P2_G06_TARGETED_CI_PASS")
' || { echo 'BLOCKED: protected tests incomplete' >&2;exit 2; }
FILE="$(mktemp --suffix=.sh)"
trap 'rm -f -- "$FILE"' EXIT
curl -fL --retry 3 -sS \
  "https://raw.githubusercontent.com/$REPO/$CI_SHA/scripts/axia_p2_owner_l3_once.sh" -o "$FILE"
bash -n "$FILE"
[[ "$(git hash-object "$FILE")" == "$WRAPPER_BLOB" ]] || {
  echo 'BLOCKED: Owner wrapper blob mismatch' >&2;exit 2;
}
bash "$FILE" --self-check
echo "G06_SINGLE_RUN_PRIVATE_SHA=$PRIVATE_SHA"
echo 'Manual YES-P2-G06-GOAL and YES-P2-G06-CRASH approvals will be required.'
bash "$FILE" --case G06
