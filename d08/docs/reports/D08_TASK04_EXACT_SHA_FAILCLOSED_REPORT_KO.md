# AXIA D08 Task04 — CI synthetic PR merge SHA vs Owner Head 및 GUI 오류 fail-closed 중간보고

## 기준
- Public repo silverbjin/axia-robot-safety-ci-public, PR #166, branch feat/d08-unified-sensor-cm-path-20261118, original main base 62e366b51c64da25ad0216328fe1e019b78e0bef.
- Existing same-world actual GUI code HEAD 183b75e7dd612f36d07c4549750046a87c1cc0df; full public [Run #44243971341](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44243971341) **SUCCESS**. L0 95 passed; physical Gazebo scan+RGBD, pinned original C++ YOLO and original official Nav2 3 Path in same World PASS. D05 0.704022/0.534589m, true UNKNOWN. This does NOT verify Owner WSLg GUI pixel, actual CM internal state/Guard or robot Moving.
- Output paths: .github/workflows/d08-main-no-goal-real-gazebo-l2.yml, d08/scripts/d08_public_gazebo_l2.py, d08/scripts/d08_owner_no_goal_bootstrap.sh, d08/tests/test_d08_task04_exact_sha_and_failclosed.py.

## PLAN → RED → GREEN → REFACTOR → REVIEW → COMMIT
- PLAN v1.12 committed in first RED commit 404f4e62520b310b0afc3e1f480522a9bee09626.
- One first provenance failure: previous PR CI defaults to merge SHA from actions/checkout, but Owner public bootstrap fetches PR HEAD SHA. Earlier #44243971341 result source is a synthetic merge checkout; cannot claim identical Owner source until checkout policy is fixed.
- Second first unsafe verdict condition: when the Owner GUI repeat loop raises Exception after setting `D08_REAL_GAZEBO_WAFFLE_RGBD_NO_GOAL_PASS`, previous outer exception would set only `blocker` without resetting status, and exit0 could be emitted. No additional fake moving/velocity gate is required; only error-branch fail closed.
- Actual CI RED Run https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44245418250 at source 404f4e62520b310b0afc3e1f480522a9bee09626, **2 failed, 95 passed in 0.43s**, tests `test_same_exact_source_sha_in_public_pr_ci_and_owner_checkout` and `test_owner_gui_cycle_failure_after_before_pass_cannot_return_success`. Native Gazebo L2 skipped (RED).
- Minimal GREEN: four original public checkout steps explicitly `ref: ${{ github.event.pull_request.head.sha || github.sha }}`, shared `AXIA_D08_EXACT_SOURCE_SHA` env; unchanged `git rev-parse HEAD` verifies exact checkout (fallback to default event SHA only outside these explicit calls). Public Owner bootstrap passes its downloaded `AXIA_D08_PUBLIC_SHA` as expected, no branch/main reset. Existing GitHub source mismatch exception preserved. Outer runtime exception explicitly sets BLOCKED before logging first exception. GUI Ctrl+C success remains separately recorded; no source TTL/Planner changes.
- L0 command: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q d08/tests/test_d08_task04_exact_sha_and_failclosed.py d08/tests/test_d08_task04_native_path_and_rviz.py`.
- Actual public ROS/Gazebo L2: pinned one-world original `d08/scripts/d08_public_gazebo_l2.py --official-nav2 --official-path-phases --live-person-range` job. Expected exact-head CI SUCCESS still NOT_RUN at this report commit; no fabricated PASS.
- REFACTOR/REVIEW: 4 identical checksum-protected checkout files, no private Instructor answers, no extra Planner, no new command publishers, no CM/Guard TTL relaxation or ROS/world changes. Native official Gazebo real scan max 0.5s bound preserved. Owner WSLg pixels NOT_RUN.

## 판단 및 후속
- Existing 183b75 head same-world actual L2 PASS, new head exact-SHA same-run L2 PENDING; CLI/CI no owner field test yet. Task03 G07 strict moving HOLD. Three main branches NO merges.
- After new exact-head public workflow SUCCESS, update Student/Instructor integrated classroom guides to single pinned public SHA and original Path display, then provide a single Owner WSL2 final GUI command. Main merges require user explicit approval.
