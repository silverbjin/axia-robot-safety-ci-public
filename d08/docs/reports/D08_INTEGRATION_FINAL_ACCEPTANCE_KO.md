# AXIA D08 — 통합 최종 인수 현황 / 출고 보류 보고서 (2026-11-18 KST)

**현재 결과: PARTIAL / RELEASE HOLD; 교육용 NO_GOAL 아직 인수 불가.** This report is not a declaration of all tasks complete.

## 코드 및 Git 출처
| Repo | Development branch / PR | base main SHA | Latest evidence |
|---|---|---|---|
| Public CI | feat/d08-unified-sensor-cm-path-20261118 / PR #166 | 62e366b51c64da25ad0216328fe1e019b78e0bef | previous head dfd4ba290807a933ac911dbc8e832f670386b77c |
| Student | feat/d08-integrated-no-goal-live-20261118 / PR #43 | 6a3047b5aa219687f5fc918e467cea5115d3d482 | guide e8f1de9911a90c0f77e085ff8bd13594d55987a4 |
| Instructor | docs/d08-unified-teacher-guide-20261118 / PR #212 | f46874470a814be8f6976b6adbcaa1e43a1fe681 | guide 839da3c3daa3d62bec4e1a9a7b47acf5a026a399 |

All main merges NO; owner approval required. Private instructor answer and hidden tests retained in private repo.

## 실행·기술 판정
| Contract | Actual evidence | Level | Status |
|---|---|---|---|
| Task00 world provenance and actual Waffle/Proxy | real world generated, physical human, stamp/hash/domain/partition check; actual Gazebo first job #44201775704 PASS | L0 + native Gazebo partial L2 | PARTIAL; full integrated world with Nav2/CM not yet |
| Task01 two real distances + UNKNOWN | public ROI strict L0 fixtures, no simultaneous actual YOLO/depth registration/2 VALID | L0 only | HOLD |
| Task02 native /scan→official CM and same-world official Nav2 Path before/near/restore | isolated native CM with **synthetic scan**, actual /scan elsewhere; official Planner path NOT in this D08 world | independent ROS tests | HOLD |
| Task03 moving tracer-OFF | Latest referenced G07 Task02 #44120024711 fails, no strict moving source/observer/Guard/Goal/odom shutdown green | none | HOLD dependency |
| Task04 student/teacher guides and common WSL2 one-shot | guides in separate draft PRs; no new exact SHA public integrated one-shot | docs draft | HOLD |
| Owner WSLg physical GUI | no Owner field execution | L3 NOT_RUN | NOT_VERIFIED |

## Real CI output and first failure boundaries
1. SHA 52b104... Public CI #44199555533 L0: "22 passed in 0.12s".
2. SHA 9800cd... L2 #44199786210: "D08_REAL_GAZEBO_L2_BLOCKED RuntimeError:D08_GIT_SOURCE_SHA_NOT_AVAILABLE" exit2 before Gazebo. Fixed scoped Git checkout trust, no wildcard.
3. SHA 25d3ed... L0 #44200740416: "26 passed in 0.14s"; Gazebo world sensor L2 showed actual scan near 0.558158m, STOP 0.363060m, restored 1.414728m, then max real /scan wall receive gap 0.519095s > unchanged 0.5s -> L2 failure exit1. Isolated CM callback max 0.063337s did not prove real CM /scan.
4. SHA dfd4ba... L0 #44201775704: "28 passed in 0.16s"; Gazebo native job PASS for that run (observed near 0.569907m, restored 1.411924m), **separate** YOLO upstream build job failed ONNX Runtime archive "Unrecognized archive format", exit2. Intermittent scan gap from earlier run not closed; no full-workflow success.
5. Newly proposed official ONNX archive preflight/verification in this report commit: exact SHA/new CI outcome pending. Could be infra blocked. No actual new success asserted.

## Minimal actual CI command and evidence
- Public source workflow: .github/workflows/d08-main-no-goal-real-gazebo-l2.yml
- L0: python -m pytest -q d08/tests/test_d08_unified_runtime_provenance.py d08/tests/test_d08_public_person_range.py d08/tests/test_d08_scan_gap_trace.py d08/tests/test_d08_yolo_archive_gate.py
- Real L2: python3 -u d08/scripts/d08_public_gazebo_l2.py --actor /tmp/axia-d08-assets/walk.dae --out results/d08-human-contact-calibration --lidar-pre-goal --cm-cadence-l1
- Evidence artifacts: https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44201775704 ; outputs results/d08-human-contact-calibration/verdict.json, runtime_provenance.json, SHA256SUMS, native logs and first scan gap in verdict. Retention 7 days according to workflow.
- Real installed ROS topic QoS/first CM native input gap/TF/actual registered person ROI, final publisher count, Contact safety, odom dwell, WSLg pixel: NOT_VERIFIED for unified run.
- Neither an L0 fixture nor replayed YOLO ROS L1 is end-to-end connected actual RGB-D human distance.

## Final mandatory flags (truthful)
D08_UNIFIED_PLAN_COMMITTED=YES
D08_TASK00_BASELINE_VERIFIED=HOLD
D08_TASK01_PERSON_RANGE=HOLD
D08_TASK02_NO_GOAL_SAME_WORLD=HOLD
D08_LIVE_NO_GOAL_ACCEPTED=NO
D08_MOVING_E2E_ACCEPTED=HOLD
D08_OWNER_WSLG_VISUAL=NOT_RUN
D08_STUDENT_MAIN_MERGED=NO
D08_INSTRUCTOR_MAIN_MERGED=NO
D08_PUBLIC_CI_MAIN_MERGED=NO

## Next exact boundary
1. Fix provenance of upstream ONNX download as infra vs valid archive; no inappropriate ROS code workaround.
2. Investigate 519ms receiver gap with actual Gazebo publisher/RMW, bridge receiver and /clock across same run; do not raise TTL. Test prior failure in public CI first.
3. Link existing D08 real sensor/YOLO and D05 measure with existing D07-H01 official Nav2+physical loop and D06 official CM on **one identical world SHA**. Obtain actual 2 VALID+UNKNOWN, Costmap+Path three stages, actual real Scan-to-CM first-gaps.
4. Exact same public runner CI/WSL2 3-layer teaching smoke, one Owner field run after CI. Do not send Moving Goal until G07 strict separately green.
5. Request **explicit** merge approval for Public #166, Student #43, Instructor #212 only when all required NO_GOAL gates are met.
