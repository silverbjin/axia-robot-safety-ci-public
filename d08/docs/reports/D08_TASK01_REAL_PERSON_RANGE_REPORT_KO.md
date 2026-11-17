# AXIA D08 Task01 — 실제 사람 거리 통합 중간보고서 (진행 / HOLD)

## 기준
- Public CI repo / branch: silverbjin/axia-robot-safety-ci-public / feat/d08-unified-sensor-cm-path-20261118
- Base main: 62e366b51c64da25ad0216328fe1e019b78e0bef; PR https://github.com/silverbjin/axia-robot-safety-ci-public/pull/166
- Owner private D05 range_core / triad_sync remains private; existing public D08 ROI decoder reused, not copied from private answer.
- NO_GOAL only. Actual moving Goal, robot Twist, certified E-Stop excluded.

## PLAN → RED → GREEN → REFACTOR → REVIEW → COMMIT
- First demonstrated gap: public D08 live_readonly_probe.run() depends on PRIVATE block_b_reference and stops if absent; public L2 also splits actual Gazebo image acquisition and later ROS YOLO replay, so cannot claim same-run 2 VALID + UNKNOWN.
- Minimal hypothesis: a separate public read-only status function using existing public 16-pixel ROI decode/standard statistics enables strict L0 contract without exposing teacher answer; still not same-world L2.
- RED: test_d08_public_person_range.py checks stale 0.5s, triad skew >50ms, optical frame mismatch, missing registration-SDF evidence, depth NaN. These are synthetic byte L0 fixtures, NOT physical distances. Actual RED run not yet observed.
- GREEN candidate: d08/harness/d08_public_person_range.py; no ROS publisher, no Nav2 changes. Command in workflow: python -m pytest -q d08/tests/test_d08_public_person_range.py. CI outcome for new commit PENDING.
- REFACTOR/REVIEW: keep instructor D05 reference unchanged; do not use a mere matching image frame/size or hash format as registration proof. Actual same-run SDF check still required. No safety TTL modifications.
- Report commit SHA: record in PR after commit.

## 증거 기반 판정
- L0: NOT_RUN for new SHA (test newly added). ROS L1: NOT_RUN. Gazebo L2 same-world 2 VALID + UNKNOWN: HOLD. Owner WSL2 L3: NOT_RUN.
- Exact source SHA/World/ROS_DOMAIN_ID/GZ_PARTITION, registration sensor SDF hash, actual first gaps, distance_m and UNKNOWN reason from real ROS packets: NOT_VERIFIED.
- D06 CM state / D07 Path / final cmd_vel / Contact / odom / Owner pixels: not proven by Task01 fixtures.
- No PASS if VALID count zero. A one-shot replayed RGB frame is not real-time linked RGBD+YOLO distance.

## Next
- Wire this read-only status to same-world real ROS RGB+Depth+DetectionArray with SDF registration and monotonic capture evidence.
- Collect two actual different valid distance stages and one real UNKNOWN; separate L1/L2 evidence. Until then Task01 HOLD and Task02 NO_GOAL release cannot be accepted.
