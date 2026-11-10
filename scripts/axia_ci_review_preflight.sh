#!/usr/bin/env bash
# AXIA P2 G07 review: CI SYNC FIRST -> source delta -> regression -> Owner candidate.
# Runs ONLY on trusted GitHub protected runner; never issues a Nav2 Goal/Fault.
set -Eeuo pipefail
umask 077
for var in GITHUB_WORKSPACE GITHUB_TOKEN AXIA_REVIEW_PUBLIC_TOOL_ROOT AXIA_REVIEW_PRIVATE_SOURCE AXIA_REVIEW_OWNER_PROFILE; do
  [[ -n "$(printenv "$var" 2>/dev/null || true)" ]] || {
    echo "AXIA_CI_SYNC_FIRST=BLOCKED_MISSING_VARIABLE:$var" >&2
    exit 2
  }
done

toolroot="$AXIA_REVIEW_PUBLIC_TOOL_ROOT"
checkout="$AXIA_REVIEW_PRIVATE_SOURCE"
owner="$AXIA_REVIEW_OWNER_PROFILE"
repo='silverbjin/axia-robot-safety-ci-public'
run_id=42777095584

[[ -f "$toolroot/tools/axia_review_gate.py" && -s "$owner" ]] || {
  echo 'AXIA_CI_SYNC_FIRST=BLOCKED_MISSING_OWNER_PROFILE_OR_VERIFIER' >&2
  exit 2
}
[[ "$(git -C "$checkout" rev-parse HEAD)" == 'a9a33cc32586e4a30843efcf9172bdaade85d8ea' ]] || {
  echo 'AXIA_CI_SYNC_FIRST=BLOCKED_PRIVATE_SHA' >&2
  exit 2
}
[[ -z "$(git -C "$checkout" status --porcelain)" ]] || {
  echo 'AXIA_CI_SYNC_FIRST=BLOCKED_DIRTY_CHECKOUT' >&2
  exit 2
}

tempdir="$(mktemp -d)"
trap 'rm -rf -- "$tempdir"' EXIT
curl -fsS --retry 3 --connect-timeout 10 --max-time 30 \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/$repo/actions/runs/$run_id" \
  -o "$tempdir/live_run.json"
curl -fsS --retry 3 --connect-timeout 10 --max-time 30 \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/$repo/actions/runs/$run_id/jobs?per_page=100" \
  -o "$tempdir/live_jobs.json"

# Mandatory policy check before even collecting test counts.
python3 "$toolroot/tools/axia_review_gate.py" \
  --owner "$owner" \
  --run "$tempdir/live_run.json" \
  --jobs "$tempdir/live_jobs.json" \
  --private-checkout "$checkout" \
  --report "$tempdir/review_verdict.json"

# G07 physical model and fault policy must have a satisfiable
# positive/negative scenario. Do not substitute no-Goal L2 for Goal L3.
cd "$checkout"
python3 -m pytest -q -ra \
  tests/unit/test_p2_g07_mvp_motion_gate.py \
  tests/unit/test_p2_mvp_one_goal_timing.py \
  tests/unit/test_p2_mvp_one_goal_readiness.py \
  tests/unit/test_p2_g07_live_phase.py \
  tests/unit/test_p2_g07_demo_evidence.py \
  tests/unit/test_p2_evidence_oracles.py \
  tests/unit/test_p2_base_guard_policy.py \
  tests/unit/test_p2_t07_owner_contract.py
python3 -m py_compile tools/p2_l3_acceptance_contract.py tools/p2_l3_live_session.py
echo 'G07_MVP_PRE_OWNER_GATE_OK SYNC_VERIFIED REAL_NO_GOAL_L2_PROVEN MOVING_GOAL_NOT_RUN'
