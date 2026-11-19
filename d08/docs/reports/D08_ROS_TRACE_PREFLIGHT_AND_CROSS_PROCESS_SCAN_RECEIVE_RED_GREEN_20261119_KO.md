# AXIA D08 — ROS Trace 사전검사와 최초 수신 경계 증거 수정 보고서 (2026-11-19 KST)

## 0. 인수 범위와 보존해야 할 증거

- 원본 시연: ROS 2 Jazzy, Gazebo Harmonic, 공식 Nav2, TurtleBot3 Waffle, **NO_GOAL**.
- 공개 저장소: `silverbjin/axia-robot-safety-ci-public`, Draft PR [#184](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/184).
- 진단 개발 브랜치: `diag/d08-ros-trace-preflight-20261119`; **검증 HEAD `0d912f9718496baa92aa52630a69d6d9a754c544`**.
- 수정 이전 독립 GREEN 코드 `d7cf8dc742481e57bd92a0087263e6c761a9855d`: [공개 CI #44437921180](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44437921180), L0 `189 passed`, 공식 Gazebo 첫 3상 + 실제 8사이클 L2 성공, 원본 아티팩트 SHA256 `7e5a56c71bf8570b0d9b0be8b318a3be62ec45a8f7281c1adb6af6715b0bf714`. **원본 유지**.
- 과거 Owner WSL2 `518.394ms`, 실제 공개 CI `505.365ms`, `512.136ms`, `667.085ms` 최초 Scan >500ms 위반들은 FAIL-CLOSED 유지. 이번 작업에서 SW Stop을 실제 인증 E-Stop으로 보고하거나 500ms/120ms/150ms 안전 TTL을 수정하지 않음.
- AMCL 교정 파일 `d08/harness/d08_amcl_initial_pose.py` blob `f44ffe3aa67bbbde03a28319d0db3587742b6f52` 그대로.

## 1. 기존 성공 아티팩트에서 확인한 미해결 원인 경계

성공된 동일 SHA 실 Gazebo L2 `#44437921180`의 8개 `cycle_XXXX/verdict.json`과 첫 `official_path_phases/verdict.json`을 모두 검수했다.

- `cycle_0004` 동일 LaserScan source-stamp pair: Gazebo native subscriber **140.871ms**, 별도 Python 프로세스 ROS subscriber **341.956ms**, 원래 Observer **346.500ms**, 같은 프로세스 다른 ROS Executor **347.729ms**. Python heartbeat 최대 **23.529ms**, 두 spin_once wall 최대 **58.294/53.906ms**. `ROS_BRIDGE_DDS_OR_SHARED_HOST_DELAY_CANDIDATE`이지만 Bridge RCL publish / RMW queue / 호스트 스케줄러 중 확정 불가.
- 첫 `official_path_phases`: native **302.741ms**, 별도 ROS **148.779ms**, Observer **321.348ms**, 같은 Python ROS **319.449ms**, Python heartbeat 최대 **195.863ms**, 두 spin_once 최대 **206.315/214.310ms**. 이는 별도 Python/GIL/스케줄링 지연형이 공존함을 시사한다. 두 지연을 한 가지 오류로 합치면 안 됨.
- `spin_once(timeout_sec=.05)`는 각 rclpy wait 호출의 설정 timeout이지 callback 전달의 50ms 보장이나 DDS 내부 타이밍 측정이 아니다.
- 공식 근거: [Jazzy tracing 안내](https://repo.test.ros2.org/en/jazzy/How-To-Guides/Building-ROS-2-with-Tracing.html), [ros2_tracing](https://github.com/ros2/ros2_tracing). Jazzy userspace tracepoint는 ROS 설치에 포함되지만 `ros2trace` 실행 CLI 기능은 배포된 버전에 따라 다름.

## 2. RED → GREEN → REFACTOR → REVIEW → COMMIT 실행 기록

### 사이클 A — 공식 Jazzy tracing 사전검사

1. `d08/tests/test_d08_ros_trace_preflight.py` (신규) RED: CI-only script/opt-in workflow 부재, [Run #44440132890](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44440132890) `2 failed, 189 passed`.
2. `d08/scripts/d08_ros_trace_preflight.sh`를 공식 `ros2 run tracetools status`, `ros2 trace start/stop` 사용으로 구현. `.github/workflows/d08-main-no-goal-real-gazebo-l2.yml` 대상 진단 브랜치에서만 `ros-jazzy-ros2trace`, `lttng-tools`, `babeltrace` 패키지를 설치하고, 로그를 별도 bounded artifact로 업로드.
3. [Run #44440375258](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44440375258) L0 `191 passed`, L2 진단 사전검사 **BLOCKED**: `Tracing enabled`이지만 배포된 Jazzy `ros2trace 8.2.6` CLI가 `--snapshot-mode`를 `unrecognized arguments`로 거부. Snapshot mode는 사용자가 보는 최신 README에서 확인되더라도 설치 Jazzy 8.2.6의 CLI 기능으로 간주 불가. 공개 artifact #14489644312 CRC PASS.
4. 잘못된 CLI 옵션을 L0 회귀 RED로 고정: [Run #44441050878](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44441050878), `1 failed, 190 passed`. 수정을 `ros2 trace start NAME` / `ros2 trace stop NAME` 기본 세션으로 제한, 사전검사 중 일회용 read-only ROS node 생성.
5. GREEN [Run #44441214032](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44441214032): L0 `191 passed`; 실제 `D08_ROS_TRACE_PREFLIGHT_L2_PASS_NOT_BRIDGE_CAUSALITY`; trace artifact #14491357859(13 entries, ZIP CRC PASS): `Tracing enabled`, `UST tracing enabled (35 events)`, 커널 tracing 비활성, LTTng metadata 및 trace files 실제 생성. **Bridge publish-to-subscribe causality를 측정한 것은 아님**.

### 사이클 B — L2 마지막 사이클 초기 입력 준비 실패

- #44441214032에서 실제 Gazebo 첫 3상과 `cycle_0000~0006` PASS 후 `cycle_0007`: `D08_SCAN_COSTMAP_ODOM_MISSING_FIRST_REAL_BOUNDARY` HOLD. 그때 실제 native Gazebo Scan **259개**, 별도 ROS 프로세스 Scan **248개**, native Clock **623개**가 수집됐으며, 최초 실패 후각기 Scan·Costmap·Odom 중 원래 Observer 어떤 입력이 빠졌는지는 최초 아티팩트가 기록하지 못했음. 원인을 Gazebo 정지나 Scan 500ms 위반으로 허위 보고하지 않음.
- `d08/tests/test_d08_first_ros_input_gate_custody.py` RED [Run #44442258038](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44442258038): `ImportError diagnose_initial_ros_gate`.
- GREEN `d08/harness/d08_same_world_replan.py`: 준비 게이트 **기존 25초 그대로**, 원래 Observer Scan·Costmap·Odom raw callback 횟수와 유효 accepted count, 독립 Scan/Odom/Clock/TF callback count, 각 마지막 수신 age 및 Executor thread 상태를 실패 시에만 bounded JSON으로 기록. [Run #44442429149](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44442429149) L0 `194 passed`, 실제 L2는 마지막 `cycle_0007`에서 새로운 **분석 코드 판정** `D08_EXECUTOR_SPIN_ONCE_FIRST_GAP_PAIR_UNVERIFIED` (아티팩트 #14491433422), Scan 준비 자체는 통과. 인수 PASS로 승격 금지.

### 사이클 C — 교차 프로세스 Scan 도착 순서 오류

- #44442429149 `cycle_0007` 실제 원본 JSONL: 같은 source-stamp pair `96.900s→97.002s`.
  - 원래 Observer host `558.730791→558.969290` = **238.499ms**.
  - Native Gazebo `558.727407→558.966566` = **239.159ms**.
  - 별도 ROS subscriber `558.919806→558.966553` = **46.747ms**.
  - **두 메시지 모두 native/독립 ROS에 존재했다**. 하지만 이전 `compare_worst_scan_pair_receivers` 함수가 독립 subscriber의 이전 메시지가 원래 Observer보다 50ms 이상 늦게 도착했다는 이유로 `SOURCE_PAIR_INCOMPLETE`를 반환. **독립 프로세스 간 호스트 수신 시각이 항상 동일 순서여야 한다는 잘못된 검사**가 원인이었음.
- 새 `d08/tests/test_d08_ros_cross_process_arrival_order.py` RED [Run #44443490889](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44443490889): `2 failed, 195 passed`, 실제 원본 시각을 고정.
- GREEN `d08/harness/d08_scan_gap_trace.py`: 같은 각 subscriber *자기 내부*의 두 source-stamp 수신 시각이 진행하는지만 요구. **서로 다른 프로세스 간 arrival order가 다르면** `cross_receiver_order_consistent=false`, `candidate=CROSS_RECEIVER_ORDER_UNCERTAIN`, `cause=UNDETERMINED`로 별도 보존. 실제 센서 안전 기준이나 첫 실제 위반 판정은 변경하지 않음.

## 3. 최종 동일 소스 CI 실증과 남는 지연

**소스 SHA `0d912f9718496baa92aa52630a69d6d9a754c544`**, [최종 공개 CI #44443654845](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44443654845).

```text
197 passed in 1.33s
D08_PUBLIC_MAIN_NO_GOAL_L0_PASS
D08_ROS_TRACE_PREFLIGHT_L2_PASS_NOT_BRIDGE_CAUSALITY
D08_OFFICIAL_SAME_WORLD_THREE_PHASE_PATHS_L2_PASS_NO_GOAL
D08_CI_REAL_GUI_EIGHT_REPEAT_PATHS_L2_PASS
D08_REAL_SAME_RUN_EIGHT_CYCLES_SCAN_ODOM_CLOCK_CADENCE_L2_PASS_NOT_CM
```

- 공식 Jazzy·Gazebo Harmonic ONE WORLD·Nav2 **초기 3상+반복 8사이클 실제 L2 SUCCESS**. 9개 `verdict.json` 모두 코드 SHA 일치 및 `D08_REAL_THREE_OFFICIAL_NAV2_PATH_PHASES_L2_PASS_NO_GOAL`. 최초 >500ms Scan 위반 **0건**. Contact/YOLO 별도 Job들은 기존 통합 성공 증거를 보존하기 위해 SKIPPED.
- 원본 아티팩트 [#14493010814](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44443654845/artifacts/14493010814) SHA256 `b54a7cb1c8b8c1f16090f970b90c43724004474a806ebe8a628c27036811ae55`, 113 entries, ZIP CRC PASS. 공개 tracing 사전검사 아티팩트 [#14492945874](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44443654845/artifacts/14492945874) 별도 관리.
- `cycle_0000`: native **144.818ms**, 독립 ROS **296.365ms**, 원래 Observer **376.359ms**; `ROS_BRIDGE_DDS_OR_SHARED_HOST_DELAY_CANDIDATE`.
- `cycle_0001`: native **54.202ms**, 독립 ROS **53.896ms**, 원래 Observer **364.754ms**; `SAME_PYTHON_PROCESS_DELAY_CANDIDATE`.
- `cycle_0006`: native **145.966ms**, 독립 ROS **425.128ms**, Observer **444.784ms**; `ROS_BRIDGE_DDS_OR_SHARED_HOST_DELAY_CANDIDATE`.
- 즉, **본 시연 실행은 PASS이나 두 개의 지연 패턴이 남아 있다**. `ros2trace` 사전검사는 실제 주행 세션을 감싸지 않았고 bridge publisher→rcl_take 인과 관계를 재구성하지 않았다. 과거 최초 518.394ms WSL2 원인 확정·시연 안정성 확정 불가.

## 4. REVIEW 및 최종 검증 수준

```text
D08_TRACE_CLI_JAZZY_VERSION_COMPAT_L0=PASS
D08_ROS_TRACE_PREFLIGHT_REAL_L2=PASS_NOT_BRIDGE_CAUSALITY
D08_INITIAL_ROS_GATE_EVIDENCE_L0=PASS
D08_CROSS_PROCESS_SAME_STAMP_L0=PASS
D08_OFFICIAL_NO_GOAL_GAZEBO_EIGHT_CYCLE_L2=PASS
D08_HISTORICAL_FIRST_518394MS_CAUSE=UNDETERMINED
D08_BRIDGE_RCL_PUBLISH_TO_RCL_TAKE=NOT_MEASURED
D08_CM_INTERNAL_RX_GUARD_TTL=NOT_VERIFIED
D08_OWNER_WSL2_L3=NOT_RUN
D08_MOVING_GOAL_E2E=HOLD
D08_MAIN_MERGED=NO
```

**다음 최소 원인 검증:** 공식 Jazzy `ros2_tracing` userspace 세션을 실제 `ros_gz_bridge` ROS publisher와 독립 ROS subscriber 실행 전에 시작하고, 최초 지연 구간의 `rcl_publish`·`rcl_take` tracepoint와 같은 LaserScan source-stamp를 연결하는 bounded capture를 한다. 이 metadata가 없으면 DDS 원인으로 단정하지 않는다. 원천 재현 실패를 일부러 만들거나 500ms TTL을 완화하지 않고, 공개 CI 검증 후에만 Owner WSL2 원샷을 다시 인수한다. 실제 인증 E-Stop과 SW Stop을 구분한다.

**브랜치/커밋:** 코드 `diag/d08-ros-trace-preflight-20261119` SHA `0d912f9718496baa92aa52630a69d6d9a754c544`; 교육용 보고서만 별도 `docs/d08-ros-trace-root-gate-20261119` 브랜치 커밋. `main` 병합 NO.
