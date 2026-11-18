# AXIA D08 Task02 — 최초 AMCL→TF 경계, 구독 준비 순서 검증 (2026-11-18)

## 기준
- Repo: silverbjin/axia-robot-safety-ci-public; branch feat/d08-unified-sensor-cm-path-20261118; main base 62e366b51c64da25ad0216328fe1e019b78e0bef; PR #166.
- 前기준 05503ecc434152ac497e3ae4b1535516a5410fc4: 공식 Jazzy 하나의 World RGBD/AMCL/TF 첫 ComputePathToPose L2 + 독립 C++ YOLO RGB replay L1, 공개 Run #44211587111 SUCCESS. 기존 성공 증거를 새 통합 경계에 자동 적용하지 않는다.
- 3상 후보 HEAD 339f92df043f0b5e22212812428555ec8ee682ba; Run #44226367924: **L0 57 passed in 0.28s**, standalone Gazebo RGBD/scan/physical Proxy L2 PASS, standalone C++ YOLO replay L1 PASS, **공식 Nav2 첫 Path P0 경계에서 FAIL**, 3상 Phase NOT_RUN.

## PLAN → RED → GREEN → REFACTOR → REVIEW → COMMIT
- PLAN revised master v1.6 commit 4ffbda05c932a2e15af2ea426ebd6b296e44317a.
- 현장 최초 실제 RED: `D08_AMCL_REAL_MAP_BASE_TF_NOT_READY:AMCL_POSE_STALE`, exit2. Raw artifact #14393167386 `d08-official-nav2-oneworld-l2-evidence`, `official_nav2_before_path.json`, native launch, generated World/SDF. 실제 /scan·RGBD+Contact topic 존재; AMCL Pose timeout 이후 Nav2 종료 로그는 결과이지 원인 아님.
- 유일한 주 가설: `d08_amcl_initial_pose.py`에서 공식 `/set_initial_pose` 서비스 응답이 돌아온 **뒤** TF2 listener를 만들면, 정지 중 AMCL 최초 map→odom 동적 변환을 놓칠 수 있다. Nav2 Jazzy 원본 AMCL은 LaserScan/pose 처리 후 TF를 publish함. 공식 링크: https://api.nav2.org/nav2-jazzy/html/amcl__node_8cpp_source.html ; https://ros-navigation.github.io/mkdocs.nav2.org/jazzy/configuration_and_development/configuration_guide/others/configuring_amcl/
- CI 실제 정적 RED: HEAD ef2a152324a54ccb71e472a297ead471d56e0b8f, Run #44227259173, `1 failed, 58 passed in 0.34s`; 실패 `test_tf_listener_is_ready_before_initial_pose_service_can_broadcast`: `D08_P0_TF_LISTENER_SUBSCRIBE_AFTER_INITIAL_POSE_RED`. 실제 ROS/Gazebo는 이 RED에서 SKIPPED.
- GREEN 최소 결선: 바로 기존 ROS node/Graph subscriptions 뒤에 `tf2_ros.TransformListener` 생성, 그 **후** /map·/scan·/odom 준비 및 공식 `SetInitialPose` 단일 전송. 기존 순서 뒤의 중복 listener 생성 삭제; ROS TF/pose 임의 publish 없음.
- **검증 기준 변경 없음**: `/scan` 및 `/odom` monotonic input age ≤0.5s, AMCL pose steady age ≤1.0s, 안전 CM/Guard TTL 원본, planner/Costmap/유효 거리/3상 경로 계약 모두 그대로. 단순 age 완화 PASS 금지.
- GREEN 실제 새 CI outcome: NOT_RUN, exact HEAD pending. 만약 다시 FAIL이면 먼저 AMCL 최초 Pose stamp/TF 구독 epoch 증거를 기록하고 그 경계만 다시 좁힌다.

## 검증 판정·미검증 항목
- L0 GREEN: NOT_RUN (새 커밋 후 공개 CI).
- 실제 ROS/Gazebo L2: previous one-world before Path PASS at 05503; new 3상 physical Path HOLD.
- Owner WSLg 3D pixel: NOT_RUN.
- Task01 real person depth 2 VALID + UNKNOWN: HOLD. Task02 native CM /scan real source gap, Costmap & 3 paths: HOLD. G07 strict Moving: HOLD. C++ YOLO pinned ROS L1 prior SUCCESS but no actual same-world simultaneous YOLO/RGBD/Depth.
- Student/Instructor/main branches unmerged. No certified E-Stop claim.

## 검증 명령·다음
- L0: `python -m pytest -q d08/tests/test_d08_amcl_tf_subscription_order.py d08/tests/test_d08_same_world_replan.py`
- L2: `python3 -u d08/scripts/d08_public_gazebo_l2.py --actor /tmp/axia-d08-nav2-assets/walk.dae --out results/d08-official-nav2-sameworld --official-nav2 --official-path-phases` in public pinned Actions workflow. Real `SetInitialPose` ACK + map→base_link, before/intrusion/restored actual Path, /scan/costmap host stamp + first gap, native Gazebo set_pose must pass. Failure raw artifact preserved; no Owner run requested.
- Git commit SHA (this report included) is recorded in PR #166 after commit.
