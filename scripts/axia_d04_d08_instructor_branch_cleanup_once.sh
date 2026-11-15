#!/usr/bin/env bash
# AXIA D04–D08 Instructor private branch Owner cleanup.
# No ROS, no Goal, no private GitHub Actions. One noninteractive sweep.
set -Eeuo pipefail
PUBLIC_REPO="silverbjin/axia-robot-safety-ci-public"
SOURCE_SHA="4c5cae16f11a2d7ef952e6ced028d58328417453"
BASE="https://raw.githubusercontent.com/$PUBLIC_REPO/$SOURCE_SHA/scripts"
TMP="$(mktemp -d)"
trap 'rm -rf -- "$TMP"' EXIT
mkdir -p "$HOME/.axia_branch_cleanup"
RUN="$HOME/.axia_branch_cleanup/$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$RUN"
command -v gh >/dev/null || { echo "AXIA_GH_CLI_MISSING: install GitHub CLI first" >&2; exit 2; }
gh auth status >/dev/null 2>&1 || { echo "AXIA_GH_AUTH_REQUIRED: run gh auth login once" >&2; exit 2; }
command -v python3 >/dev/null
command -v git >/dev/null
for f in axia_d04_d08_safe_prune.py axia_d04_d08_instructor_superseded_prune.py; do
  curl -fLsS --retry 3 --connect-timeout 15 "$BASE/$f" -o "$TMP/$f"
done
# Exact immutable Git blobs from the PUBLIC source commit.
test "$(git hash-object "$TMP/axia_d04_d08_safe_prune.py")" = \
  "f4523059d8700832c0d6d4a5527821355a5430b8"
test "$(git hash-object "$TMP/axia_d04_d08_instructor_superseded_prune.py")" = \
  "c0fb29bb285f1ad90906350cd811fc5aadd18f69"
python3 -m py_compile "$TMP/axia_d04_d08_safe_prune.py" \
  "$TMP/axia_d04_d08_instructor_superseded_prune.py"
echo "AXIA_INSTRUCTOR_BRANCH_PRUNE_PINNED_SOURCE_VERIFIED sha=$SOURCE_SHA"
python3 "$TMP/axia_d04_d08_safe_prune.py" \
  --repo silverbjin/axia-robot-safety-instructor --apply \
  --out "$RUN/main_ancestor_cleanup.json" | tee "$RUN/main_ancestor_cleanup.log"
python3 "$TMP/axia_d04_d08_instructor_superseded_prune.py" \
  --apply --out "$RUN/superseded_cleanup.json" | tee "$RUN/superseded_cleanup.log"
# One D06/G07 sub-branch has been fully incorporated into the newer CM
# core-affinity branch. Preserve latest branch and all open PRs.
python3 - <<'PY'
import json,subprocess
R="silverbjin/axia-robot-safety-instructor"
A="fix/d06-g07-observer-cpu-isolation-20261115"
B="fix/d06-g07-official-cm-core-affinity-20261115"
def api(path,method="GET"):
    r=subprocess.run(["gh","api","-X",method,path],capture_output=True,text=True,timeout=50)
    if r.returncode:raise RuntimeError(path+": "+r.stderr[:240])
    return json.loads(r.stdout) if r.stdout.strip() else None
a=api(f"repos/{R}/branches/{A}")
b=api(f"repos/{R}/branches/{B}")
assert a["commit"]["sha"]=="3593125fdfe489aead3e892daf39563df0c0d4a0"
assert b["commit"]["sha"]=="6e402e30f5036285f067b5dffed085eff41af599"
assert a.get("protected") is False
c=api(f"repos/{R}/compare/{A}...{B}")
assert c["behind_by"]==0 and c["ahead_by"]>=1
for page in range(1,21):
    pulls=api(f"repos/{R}/pulls?state=open&per_page=100&page={page}")
    assert not any(p[part]["ref"]==A and (p[part].get("repo") or {}).get("full_name")==R
                   for p in pulls for part in ("head","base"))
    if len(pulls)<100:break
api(f"repos/{R}/git/refs/heads/{A}",method="DELETE")
print("AXIA_INSTRUCTOR_D06_OBSERVER_CPU_ANCESTOR_DELETED",a["commit"]["sha"])
PY
echo "AXIA_INSTRUCTOR_D04_D08_BRANCH_PRUNE_OWNER_DONE evidence=$RUN"
echo "NO_ROS_NO_GOAL_PRIVATE_ACTIONS_NOT_USED"
