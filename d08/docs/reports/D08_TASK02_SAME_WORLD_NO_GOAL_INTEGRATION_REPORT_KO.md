# AXIA D08 Task02 — Same-world NO_GOAL integration HOLD and first scan gap report

## 작업 기준
- Public CI repo: silverbjin/axia-robot-safety-ci-public. Branch feat/d08-unified-sensor-cm-path-20261118. Base main 62e366b51c64da25ad0216328fe1e019b78e0bef. PR #166.
- First actual L2 failure reference: https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44200740416 , source SHA 25d3ed03e72c8a633fff06a93be6f2ed3701fb03, job #134454028565.
- NO_GOAL: no NavigateToPose, FollowPath, cmd_vel; excludes Moving Goal / certified E-Stop.

## PLAN → RED → GREEN → REFACTOR → REVIEW → COMMIT
- ACTUAL RED: world+real RGBD and native /scan reached physical stages, scan before 0.787427m, SlowZone after 0.558158m, STOP 0.363060m, restored 1.414728m. Main L2 assertion then failed actual scan wall receive gap 0.519095s >= required <0.5s. First failed element was the 'before' scan capture. Run conclusion failure, exit1. RTF observed 0.8554, sim stamp median period 0.099s. No Nav2 moving acceptance implied.
- In the same L2, official CM isolated L1 callback max 0.063337s and service concurrent CM max 0.058048s, yet its scan is synthetic /axia_ci replay derived from a real measured front range. This is NOT same-world native CM /scan provenance. The 0.519095s real ROS receive gap must not be hidden by the isolated CM result.
- Root cause NOT DETERMINED: gap may be Gazebo source wall scheduling, bridge/DDS transport, or ROS callback scheduling. Original logs do not supply publisher RMW gap or /clock aligned first violation. One hypothesis: public CI under actual GPU LiDAR + RGBD load experiences intermittent ROS scan delivery delay.
- Minimal new regression/test: d08/tests/test_d08_scan_gap_trace.py with exact 0.519095s RED fixture and 0.5s boundary; new pure d08/harness/d08_scan_gap_trace.py extracts FIRST receive violation and source ROS simulation stamp before/after, without pretending to measure publisher gap. Updated actual d08_public_gazebo_l2.py to record first_rx_gap_over_500ms.
- GREEN candidate is only DIAGNOSTIC. This does NOT fix actual 500ms violation and does NOT make Task02 pass.
- Public CI commands: python -m pytest -q d08/tests/test_d08_scan_gap_trace.py (L0) then existing real Gazebo workflow. CI for new commit pending.
- REVIEW: no TTL/Guard grace relaxation, no sensor disable, no fabricated scan, no new Planner/Controller, no private answer, no false ROS/Gazebo PASS. Recorded sim header gap is not proof of actual RMW publication wall gap.
- This report's exact commit SHA to be added to PR comment after commit.

## 증거 기반 판정
- Task00 same-world evidence: actual Gazebo sensor data observed, but integrated L2 overall FAIL due scan receive gap. L0 previous HEAD 26 passed in 0.14s.
- Task01 public range L0 fixtures pass; actual 2 VALID + UNKNOWN in one world: HOLD.
- Task02 official Nav2 Costmap and before/near/restore ComputePathToPose from same D08 world: NOT_RUN. CM real Gazebo /scan source→observer first gap: NOT_RUN. Actual slowdown output: NOT_RUN.
- Owner WSLg 3D pixel/CM Guard TTL/odom stopped dwell/Contact continuous/moving: NOT_RUN or NOT_VERIFIED.
- D08_NO_GOAL_SAME_WORLD_SENSOR_CM_PLAN_L2_PASS=NOT_VERIFIED; D08_LIVE_NO_GOAL_ACCEPTED=NO; D08_MOVING_E2E_ACCEPTED=HOLD.

## 다음 단계
1. Run new instrumented exact-HEAD public CI; use first indexed wall receive gap and ROS sim stamp delta plus aligned /clock and publisher sensor timing before selecting ONE bounded fix. No mindless retries and no timeout widening.
2. Once real scan timing remains within baseline, connect official D07-H01 source and CM real /scan in same world; then actual RGBD/YOLO 2 VALID + UNKNOWN.
3. Public CI success + Student/Instructor guide PRs before final Owner one-shot; main merge explicit approval only.
