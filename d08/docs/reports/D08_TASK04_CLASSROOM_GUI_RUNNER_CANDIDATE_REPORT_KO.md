# AXIA D08 Task04 — 공개 동일 실행기 WSL2/WSLg NO_GOAL 원샷 후보·수업 가이드

## 작업 기준
- Public CI repo silverbjin/axia-robot-safety-ci-public / branch feat/d08-unified-sensor-cm-path-20261118 / base main 62e366b51c64da25ad0216328fe1e019b78e0bef / PR #166.
- Prior successful same-world integration source `16c1bdadf2312f31e639125b75a3b7b0ab634e18`; real public Run https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44236129868, all SUCCESS, exact runtime Actions checkout b632d787bbaf062f6327d5e2dc53f1ae354586d4. Actual D05 range 0.704022 / 0.534589m + true no-person UNKNOWN, official Nav2 3 Path + native Costmap lethal 0→66→0 in same run. Owner WSLg NOT_RUN.
- Plan v1.10 commit `dc2aabfca92636b8ebcebb4da361eb850f818299` — only GUI/Path display and immutable bootstrap; official Navigator/CM/YOLO engine unchanged. Student/Instructor draft docs in separate repos remain HOLD until source-pinned CI.

## PLAN → RED → GREEN → REFACTOR → REVIEW → COMMIT
- Actual RED public #44238004993 commit `31d116d73abc280dbfcc936bcae48d1306c3891e`: `4 failed, 88 passed in 0.43s` in `test_d08_owner_gui_runner_contract.py`, from missing opt-in GUI flags, original Path read-only RViz publisher, bootstrap script; actual Gazebo L2 SKIPPED in this RED. Prior real same-world integrated success preserved at own SHA.
- Minimal GREEN candidate: original `d08/scripts/d08_public_gazebo_l2.py` gains only `--owner-gui` opt-in, reuses same actual World/robot/person/ROS Action tests as public CI. On WSLg it removes forced CI llvmpipe/Xvfb, passes `headless:=False use_rviz:=True` to unmodified official `nav2_bringup/tb3_simulation_launch.py`, runs one NO_GOAL integrated D04/D05+D07 proof, then **reuses existing** three Path observer in a repeated physical person-only read-only loop until Ctrl+C. The existing CI command/flags continue to run headless and unchanged. No new GZ or Nav2 server.
- `d08/harness/d08_same_world_replan.py` publishes the exact official `ComputePathToPose.Result.path` (unchanged source header/frame) to one read-only `/axia/d08/official_path_readonly` nav_msgs/Path for RViz. It does not generate/control/alter Planner/Controller, no NavigateToPose, no cmd_vel.
- `d08/harness/d08_one_world_official_nav2_launch.py` has owner_gui flag with default False; ROS Jazzy official parameters are source of truth for launch and render, no package patch.
- `d08/scripts/d08_owner_no_goal_bootstrap.sh` implements `--self-check|--doctor|--run`. User exports pinned SHA, script fetches same public exact PR HEAD SHA, checks detached HEAD, downloads original pinned physical human DAE, official Microsoft 1.20.0 NuGet/SONAME, pinned ONNX model SHA, pinned upstream yolo_ros C++ SHA, compiles into unique evidence root, launches ROS/Gazebo/RViz using the *same* CI runner. ROS setup nounset-safe. No `reset --hard`, `pkill`, `rm -rf` or deletion of prior logs, cleanup only of children it creates, Owner Ctrl+C is expected. Local package installation only for missing official apt deps (one sudo authorisation). Actual local WSLg GUI/pixel result NOT verified by L0.
- L0 new tests `d08/tests/test_d08_owner_gui_runner_contract.py`, plus existing 88 regressions; workflow adds Python compile, bash -n and self-check. RED→GREEN exact-head CI run and real Gazebo L2 **PENDING**; no PASS until completed.
- REVIEW: the NO_GOAL path does not issue any robot motion command, synthetic /scan, fake RGB-D, safety TTL change or certified E-Stop. Both Student public TODO and Instructor sealed answer stay in separate repositories. If GUI renderer or TTL fails locally, Owner original logs/first boundary are inspected then reproducible portion enters public regression RED before retry.

## 검증 수준·증거·다음
- L0 / actual ROS L1 / actual Gazebo L2 for new Task04 HEAD: NOT_RUN (post-commit CI). Existing real L2 `16c1bd...` PASS for original one World NO_GOAL, but new GUI flag pixels cannot be inferred.
- Owner WSL2/WSLg L3: NOT_RUN. Xvfb window creation is not a rendered GUI pixel admission. Actual User one-shot to be issued ONCE only after new source SHA public CI success, and owner result bundle reviewed before release.
- Task03 strict Moving G07: HOLD (separate scoped public G07 timing numbers do NOT constitute D08 same-world moving proof).
- Public/Student/Instructor PR main merge: user approval NOT GIVEN, all remain unmerged.

## 원본과 기대 문자열 (후속 exact SHA를 PR에 기재)
- Public L0: `D08_OWNER_BOOTSTRAP_L0_PASS_ROS_GAZEBO_WSLG_NOT_RUN_NO_GOAL`
- Public same-world L2: `D08_REAL_LIVE_RGBD_YOLO_D05_NAV2_THREE_PATHS_L2_PASS_NO_GOAL`
- Owner console after actual GUI launch: `D08_OWNER_WSLG_REAL_GUI_REQUESTED`; after actual live phase: `D08_OWNER_GUI_REPLAN_LOOP_READY Ctrl+C TO_STOP`; on Ctrl+C: `D08_OWNER_GUI_CTRLC_ACK`. These are control-flow indicators, not proof of pixel rendering.
- Owner screen/report: expected actual Gazebo human mesh physical collision, Waffle, RViz official Path read-only display. User must view and attach actual screenshot/log bundle for L3 pixel acceptance. Moving E2E and E-Stop not included.
