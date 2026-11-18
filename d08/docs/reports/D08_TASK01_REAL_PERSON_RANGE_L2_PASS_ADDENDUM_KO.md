# AXIA D08 Task01 — 실제 같은 World YOLO/Depth 두 VALID+UNKNOWN L2 성공 보고

## 기준·재사용
- Repo silverbjin/axia-robot-safety-ci-public, PR #166, integration branch feat/d08-unified-sensor-cm-path-20261118, main base 62e366b51c64da25ad0216328fe1e019b78e0bef.
- 실제 공개 [Run #44236129868](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44236129868), feature HEAD `16c1bdadf2312f31e639125b75a3b7b0ab634e18`, actual checkout source SHA `b632d787bbaf062f6327d5e2dc53f1ae354586d4`. Workflow all jobs SUCCESS, L0 **88 passed in 0.42s**.
- pinned official Microsoft ONNX Runtime 1.20.0 NuGet SHA256 36dbafacb1bc532e92d02371bd70582a61105872561fc9982314854d1c7ebf72, pinned upstream mgonzs13/yolo_ros 94d2dd500cb26027ee9c019f4d3a02029ac615cc, official ROS Jazzy/Gazebo Harmonic/Waffle and Nav2 unmodified.
- Raw artifact `d08-same-world-live-person-range-cm-nav2-evidence` #14397906766, retained by public workflow 7d. Same world default, single physical person axia_p2_g07_obstacle, robot axia_d08_ci_waffle, ROS_DOMAIN_ID 69/GZ_PARTITION axia_d08_ci_12493, SDF SHA256 d70a7773cf13c5ea5678279e36ef719603010fefe9cce90761ddd06b8131a461.

## PLAN → RED → GREEN → REFACTOR → REVIEW → COMMIT
- Original actual RED #44229304083: same-world RGBD/YOLO/Depth 2 VALID .475343/.534589m, closer person had larger median and only 80px-high top bbox. First boundary `D08_TWO_ACTUAL_PERSON_DISTANCES_NOT_DISTINCT`; NOT an inference engine or DDS missing-message error. Original RGB/Depth/Detection timestamps and confidence retained, untouched.
- PLAN v1.8 `659144df98717c16d0795fa09a506e6da949ceb8`; physical farther candidate world x=-1.20, keep StopZone x=-1.63 and side Unknown. New actual frame+16 Depth ROI samples copied read-only, original 50ms stamp skew and <=0.5s input age rules untouched.
- RED #44231082387 at `b9a3947d35aaeb9f7e1525e08cec49c31170e8c4`: failed import of raw ROI capture and reversed distance contract; minimum GREEN `8e0c3c2340319ac7b374c345ea42d2b525598453` L0 79 tests passed but actual AMCL static Pose/TF stale first boundary, later isolated.
- AMCL official one-shot Pose→live TF fix: PLAN `6b2f8a0477a4c44f3a45dd7bd60ff6bf4a336e9c`, RED CI #44235514176 `8c9b217e4b7b87e4785346546ef4d14ed6db19a7`; source `44f19efdd8598cbf84bec021acd6c5d0206df34f` with obsolete test alignment `16c1bdadf2312f31e639125b75a3b7b0ab634e18`. Actual public L2 SUCCESS #44236129868. No AMCL reissue or safety TTL extension.
- Code paths `d08/harness/{d08_live_person_range,d08_live_person_range_session,d08_amcl_initial_pose,d08_same_world_replan}.py`, shared public runner `d08/scripts/d08_public_gazebo_l2.py`, workflow `.github/workflows/d08-main-no-goal-real-gazebo-l2.yml`.
- Commands:
  `python -m pytest -q d08/tests/test_d08_roi_physical_trace.py d08/tests/test_d08_live_person_range.py d08/tests/test_d08_live_person_range_session.py d08/tests/test_d08_static_amcl_witness.py`
  `python3 -u d08/scripts/d08_public_gazebo_l2.py --actor /tmp/axia-d08-live-assets/walk.dae --out results/d08-live-person-nav2-e2e --official-nav2 --official-path-phases --live-person-range`.
- REFACTOR/REVIEW: only existing read-only ROI and original official Action Path, no student hidden tests/private Instructor reference, new YOLO model or Planner, no ROS cmd_vel publisher, no robot Moving Goal, no certified E-Stop claim.

## 원본 실제 ROS 증거
| Stage | 실제 Gazebo 사람 World(x,y,z) m | 실제 /scan (m) | YOLO bbox (px) | Raw ROI valid | D05 median (m) | RGB/Depth/YOLO stamp (s) | callback age max (s) |
|---|---|---:|---|---:|---:|---:|---:|
| farther | -1.20,-0.50,.24 | .787593 | [195,138,428,354] | 10/16 | **.704022 VALID** | 19.200 | .089602 |
| stop | -1.63,-0.50,.24 | .360354 | [116,25,499,105] | 10/16 | **.534589 VALID** | 25.002 | .079719 |
| unknown | -1.979119,.171291,.24 | moving off camera axis | no person detected | — | **UNKNOWN** | 29.601 | .064665 |

- Distance direction is correct and raw median delta **.169433m ≥.12m**. UNKNOWN reason `NO_PERSON_CLASS_IN_ACTUAL_YOLO`, from real 6 DetectionArray callbacks, not CLEAR/movement authorization.
- Valid Depth source image hashes and exact 16 real float32 pixels are recorded in `live_person_range/{farther,stop}_live_d05.json`, real RGB PPM and SHA in same artifact. Same generated registered RGBD sensor optical frame; class/bbox and physics Proxy identity association beyond same scene is NOT independently solved.
- Live official Nav2 three-stage Path also succeeded in same World; integration of actual camera data with CM control chain/actual safety action is NOT claimed.
- Moving G07 strict HOLD, Owner WSLg actual displayed pixels NOT_RUN, no certified physical E-Stop.

## 판정·다음
- **D08 Task01 actual same-world RGBD+YOLO+D05 2 VALID+1 UNKNOWN: real Gazebo L2 PASS** for exact evidence run. New Task04 GUI runner commit must independently preserve headless L2 and pass L0 before release.
- Task02 actual CM subscription discovered but internal CM receive period/state and Guard age NOT_VERIFIED, actual slowdown NOT_RUN. Owner GUI/merge remain unapproved.
