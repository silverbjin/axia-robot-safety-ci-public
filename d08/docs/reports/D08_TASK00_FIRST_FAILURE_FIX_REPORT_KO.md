# AXIA D08 Task00 — First actual Gazebo L2 failure / minimal fix

## Source and evidence
Public repository silverbjin/axia-robot-safety-ci-public; branch feat/d08-unified-sensor-cm-path-20261118; base main 62e366b51c64da25ad0216328fe1e019b78e0bef; PR #166. Failed source HEAD 9800cd2f6d414c667a8fc2a607a06c435870616a at https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44199786210 , job #134450854488.

## PLAN → RED → GREEN → REFACTOR → REVIEW → COMMIT
- Actual RED stdout: D08_REAL_GAZEBO_L2_BLOCKED RuntimeError:D08_GIT_SOURCE_SHA_NOT_AVAILABLE; process exited 2 BEFORE Gazebo start. Source and generated World were not admitted. This is not a sensor/physics failure.
- Single unconfirmed hypothesis: Docker GitHub checkout file ownership triggers git safe.directory check. The previous runner hid stderr; cannot assert root cause yet.
- Minimal GREEN change: Git invoked with safe.directory set to exactly ROOT, never wildcard; GitHub event GITHUB_SHA must equal checkout SHA. If the error repeats, include original stderr in first-failure evidence.
- L0 regression: test_github_checkout_owner_mismatch_regression_is_scoped; command python -m pytest -q d08/tests/test_d08_unified_runtime_provenance.py.
- New exact SHA L0 and L2 are not yet evaluated. Prior candidate L0: 22 passed in 0.12s at 52b10486649b4e0070c67ca67b29be7cd82a3165.
- REFACTOR/REVIEW: no upstream ROS/Nav2/CM changes, no safety TTL changes, no new publisher, no new scene, no private code.
- New commit SHA is referenced by GitHub PR comment after the commit.

## Verdict
L0 new: NOT_RUN; ROS L1: NOT_RUN; actual Gazebo L2: prior FAILURE / new NOT_RUN; Owner WSL2 L3: NOT_RUN.
Single World and real source, person distance, scan, CM first gap, official Path, odom, contact and WSLg visible pixels remain NOT_VERIFIED.
NO_GOAL educational release HOLD; MOVING separate G07 HOLD.
Next: exact-HEAD public CI, inspect earliest failure. Never retry Owner before CI. No main merge.
