# AXIA D07-H01 — Owner L3 lQkNadLW 증거 검수·RED→GREEN 보고

- 검수일: 2026-11-17 KST
- 원본: Owner `session-20261117-lQkNadLW.tar.gz` 및 `.sha256` (원본 실측 아카이브는 개인 저장소에서 유지하고 공개 CI로 업로드하지 않음)
- 사용한 고정 Student main: `6a3047b5aa219687f5fc918e467cea5115d3d482`
- 기존 공개 CI main: `62e366b51c64da25ad0216328fe1e019b78e0bef`
- 개발 저장소: `silverbjin/axia-robot-safety-ci-public`
- 브랜치: `fix/d07-h01-l3-native-teardown-verifier-20261117`, Draft PR [#164](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/164)
- **교육용 L3 최종 HOLD / 전체 AXIA 안전 MVP HOLD**; 데이터 반복/기존 Structural L3 evidence gate는 PASS

## 1. 원본 무결성 및 기존 시연 범위

- tar.gz SHA256: `672f46e153bb293ff3e1b4e9d027afde3b1e0aa289cc1cc5162644df06aa5d9d` = 업로드된 sidecar SHA256, **PASS**
- 외부 `SHA256SUMS` 72/72 일치; `native/evidence/SHA256SUMS` 61/61 일치
- `native/evidence/d07_h01_geometry/teaching_cycle_evidence.jsonl`: 총 22행; **5개 완전한 4단계 사이클 + 6회차 Free/Intrusion 2행**.
- 각 완전한 사이클 Path pose 개수 **Free 52 → Intrusion 52 → Lateral 49 → Restored 52** (5회 동일). 포즈 개수만으로 좌표 편차를 입증하지 않음. 기존 물리 3단계 원본은 `path_delta_m=0.3659`, costmap 신규 lethal cell 92개→복원 0개.
- 모든 JSONL 행: `real_native_gazebo_pose_ack=true`, `official_action=ComputePathToPose`, `path_frame=map`, `rviz_path_subscribers=1`; `goal_sent=false`, `cmd_vel_sent=false`, `robot_moved=false`는 런타임이 기록한 플래그. 실제 주행 안전성 및 TTL 전체 검증 아님.
- `exit_status.txt`: `phase=POST_RUNTIME_EVIDENCE`, `entry_rc=0`, `runner_rc=130`, `operator_signal=INT`, `verifier_rc=0`.
- `l3_structural_verdict.txt`: `D07_H01_L3_COMPLETE_PHYSICAL_CYCLES=5` 및 `AXIA_D07_H01_L3_DATA_VERDICT=READY_FOR_OWNER_PIXEL_REVIEW`. 예전 판정기에는 개별 프로세스 종료 실패를 차단하는 검사가 없었다.
- `teardown.txt`: `P2_L2_GRACEFUL_TEARDOWN` 기록. **이 요약 마커만으로 모든 자식 정상 종료 증명 불가능**.

## 2. 첫 실패 경계와 후속 증상 분리

- `launch.log` 에서 SIGINT/SIGTERM 신호 처리가 ROS 노드에 전파된 시각 **1794926571.746초**.
- 후속 CM cleanup 도중 `getTransform`에서 frame extrapolation 오류 **1794926571.862735초**. 이것과 CM SIGSEGV가 동일 원인이라고 단정하지 않음.
- Base Guard Python `rclpy.spin(node)` → `RCLError: failed to initialize wait set: the given context is not valid`; `exit code 1` (`launch.log`의 process death).
- 공식 Nav2 Collision Monitor `exit code -11` (SIGSEGV)로 종료. 원인 **ROOT_CAUSE_UNCONFIRMED**. `P2_L2_GRACEFUL_TEARDOWN`은 이 충돌을 숨긴 상위 요약 문자열임.
- **시연 중 최초 안전 TTL 위반이 발생했음을 증명하는 원본 시계열은 확보되지 않음.** `p2_graph_diagnostics.json`은 `NO_GOAL` 읽기 전용 readiness snapshot이고 `cross_node_ttl_proven` 전체 보증 아님.
- Gazebo/RViz 창 생성은 확인. `window_Gazebo.xwd` (1200×1000) 및 `window_RViz.xwd` (400×287)은 픽셀 RGB 전부 검정; WSLg XWD 캡처 한계와 실제 화면 오류는 구별 불가. `gpu_glxinfo.txt`는 D3D12 Intel Iris Xe accelerated=yes. RViz watcher shader `active samplers with a different type refer to the same texture image unit` 기록. 실제 Waffle·장애물·Costmap·Path Owner 픽셀 확인 **NOT_VERIFIED**.
- B 터미널 `rqt_graph` 독립 실행·3계층 필터·A 종료 후 생존의 증거는 이 아카이브에 없으며 **NOT_VERIFIED**.
- 두 개 이상의 4단계 물리 반복은 PASS. 하지만 **정상 종료 조건 미충족(실제 child exit failures)** + GUI/rqt 미검증으로 최종 L3 HOLD.

## 3. 공식 근거 및 범위

- [ros2/rclpy #1731](https://github.com/ros2/rclpy/issues/1731): 2026-09-25 생성, 2026-10-28 마지막 업데이트, **OPEN**, ROS Lyrical `spin_once`가 shutdown 경쟁 조건에서 `ExternalShutdownException` 대신 `RCLError`를 내는 재현 사례. **Jazzy의 동일 원인 확인 아님**.
- [ROS 2 Jazzy rcl wait.c](https://api.nav2.org/jazzy/html/wait_8c_source.html): `rcl_shutdown` 이후 context invalid 시 wait set 생성 실패 설명.
- [Nav2 Jazzy Collision Monitor source](https://api.nav2.org/nav2-jazzy/html/collision__monitor__node_8cpp_source.html): 공식 Lifecycle cleanup 경로와 코드 대조가 필요하며 upstream 수정/안전정책 임의 변경 금지.
- 검토한 공개 Student 소스 `block_B/day07/h01_runtime/ros2_ws/src/axia_safety_supervisor/axia_safety_supervisor/p2_base_guard_node.py`: main에서 `KeyboardInterrupt`·`ExternalShutdownException`만 처리. 종료 시 발생한 `RCLError`에 대한 한정 catch가 없는 것은 **Guard 종료 예외 후보 원인**. 구체 패치/통합 L2 검증 전까지 원인 확정 금지.

## 4. 최소 회귀 — RED→GREEN→REFACTOR→REVIEW→COMMIT

### RED
- 커밋 `8d1eb9d8dec061e38c39541da0d1e2ad6e076ea9`; `tests/test_d07_h01_instructor_l3_field.py`
- Fixture에 native `launch.log` 추가, 두 재현: **GRACEFUL 요약이 있지만 실제 child exit -11/1** 및 **원본 launch.log 누락**은 `--verify` returncode 3을 요구.
- 공개 CI [Run 44107823899](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44107823899): `Ran 12 tests`, 두 신규 테스트 `FAIL`; 실제 반환값 `0 != 3`. 의도된 **RED**.

### GREEN
- 커밋 `8ef8c904f0f3c0d013a2060ec0fe3411a6ecd30d`; `scripts/axia_d07_h01_instructor_l3_wsl2_once.sh`
- 실제 native launch log 필수, child `process has died` 또는 `Traceback (most recent call last)` 검출 시 fail closed.
- 공개 CI [L3 전용 L0 Run 44108024927](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44108024927): **12 tests PASS**, `AXIA_D07_H01_INSTRUCTOR_L3_FIELD_L0_PASS_NO_ROS_NO_GAZEBO_NO_WSLG`.
- 공개 전체 Python [Run 44108024899](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44108024899): **185 passed, 3 skipped**. 기존 sealed Instructor 2개 및 D04 의존성 테스트 1개 SKIP.
- Public runner canary [Run 44108025139](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44108025139): **success**.
- **실제 ROS/Gazebo/WSLg를 이 GREEN 커밋에서 실행하지 않음.** 새 시험은 L0 외부 증거 판정기 계약에 한정.

### REFACTOR / REVIEW
- 불필요한 코드 이동·런타임 기능 추가 없이 판정기에만 기존 2개 조건 및 Python traceback 검사를 삽입.
- Nav2, 이동 Goal, Safety Supervisor, Collision Monitor, Base Guard, TTL 정책, 인증 E-Stop 무변경.
- 요약 `P2_L2_GRACEFUL_TEARDOWN`를 개별 노드 정상 종료 증거로 자동 승격하지 않도록 보수적 처리. 실제 프로세스 오류 없는 정상 시나리오는 기존 fixture 테스트로 보존.
- Draft PR #164는 **main 병합 승인 대기**. 학생 main 및 Instructor main 변경 없음.

## 5. 남은 단일 경계

1. **FIRST_UNVERIFIED_FAILURE_BOUNDARY:** Ctrl+C 처리 중 Collision Monitor SIGSEGV(-11) 원인 확인. 동일 현장 재실행 대신 공식 upstream + 현 소스 버전 확인, 가장 낮은 비용의 공개 CI L2 종료 회귀 후보를 먼저 정의한다. Guard의 rclpy shutdown wait-set 오류는 별도 독립 결함으로 분리한다.
2. 시연 중 Safety Supervisor→CM/Guard 전달 주기·TTL 검증은 교육용 H01로 승인하지 않는다. 최초 시각 위반 정보가 없으면 `ROOT_CAUSE_UNCONFIRMED`.
3. Owner 직접 GUI 픽셀 및 별도 rqt_graph 3계층/종료 독립성 증거 확보. XWD 검정 화면은 pixel PASS가 아니다.
4. GREEN L0 이후 본 사용자 WSL2 **새 코드 재실행은 미실시**, 사용자에게 같은 old SHA 재실행 요구 금지.
5. 교육용 H01 L3 `AXIA_D07_H01_EDUCATIONAL_L3_ACCEPTED=HOLD`, 전체 안전 MVP `AXIA_MVP_DEMO_ACCEPTED=HOLD`.
