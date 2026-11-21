# AXIA G07 — EventsExecutor HEALTH/Scan 최초 타이밍 경계: S3 재개 기록

작성일 2026-11-21. 범위: 공식 ROS2 Jazzy/Gazebo Harmonic/Nav2/TB3 Waffle 시뮬레이션 안전 MVP. **인수 상태: HOLD**, SW STOP은 인증된 하드웨어 E-Stop이 아님. 기준 AXIA_Robot_Safety_MVP_Baseline_Scenario_Acceptance_v1_KO.md.

## 1. 중단 지점 검증 (기존 증거 불변)
- Jazzy 원본 `rclpy.experimental.EventsExecutor`는 ROS2/rclpy backport PR #1435. 읽기 전용 CI A/B 전용이며 Owner 기본 2-worker 동작 변경 금지.
- 실제 ROS Jazzy L1 #44861195626 PASS, 8개 timer callback, 최대 40.181ms; **실제 다중 토픽 Gazebo 안정성 증거 아님**.
- native 2-cycle #44861540326 **0/2**: cycle1 첫 preGoal `/clock` 331.672ms, `/scan` 385.643ms, safety hard-block. cycle2 strict Scan preGoal 통과 이후 `CI_MOVING_GOAL_TIMEOUT_HEALTH` before Goal, Guard/CM raw evidence 없음. Root UNDETERMINED.
- 최신 baseline public contract #44862156434 PASS; 이번 별도 branch 시작 정확 public `32cb1f6da19de4aa615b78cff3b15f12a419de01`, Student `26f4abecad2d714721ad27cebe6e5c36d7705b2c`. 이전 proven 2-worker 2/2 #44830956042는 다른 SHA의 역사적 증거로만 보존.

## 2. RED→GREEN #1: 최초 HEALTH 상태 추적
- Student 신규 `tools/p2_g07_health_first_boundary.py`: 48개로 제한된 read-only 최초/마지막 건강 상태, 최초 supervisor state transition, missing CM lifecycle, Clock, Scan, Guard latch. 외부 콜백/노드/퍼블리셔 추가 없음. `CI_MOVING_GOAL_TIMEOUT_HEALTH` 기존 strict 12초 이후에만 `first_health_boundary.json` 생성. **절대 PASS를 반환하지 않음**.
- 공개 RED #44863569711 module missing, GREEN #44863733721: 신규5 + Events4 + preGoal3 PASS.
- 실제 single native #44863792399 **FAIL**: 더 앞선 preGoal Scan/Clock 위반으로 HEALTH 런타임 코드 자체는 미실행. 출고 불가.

## 3. 동일 native #44863792399 FIRST preGoal 위반과 독립 증거
- Scan 최초 동일 header (sim 45.402→45.501sec): 원 Observer 424.373456ms, SafetyScan 424.359285ms, **헤더 간격99.0ms**. 동시 Clock 최초 337.093495ms/최대, Odom 365.711665ms 최대. Scan 수신 공백 중 동일 subscriber 노드의 Clock 콜백 33건. Goal 발행 전 차단.
- GitHub artifact #14690922305 (SHA256 `8b79d4e0a3db3076e8ec5e1436e7d335579aeb289e11051ce1a60d9b728a05c6`) `first_scan_rosbag_exact_pair.json`: 독립 raw rosbag에 **동일 헤더 쌍 정확 매칭**, **bag Scan101.297422ms**, **bag SafetyScan102.812639ms**. 이 사실은 Scan 송신이 424ms 동안 전 수신기에서 완전히 멈췄다는 가설과 양립하지 않으며, **해당 Python Observer의 DDS/take/Executor/deserialize 경계 후보**를 지지.
- 단, 동일 bag `/clock` 최대335.607688ms, `/odom`343.795109ms. 별도 안전 계층 위반이 존재해 Scan 수신만 고쳐도 전체 안정성 증거 없음. System epoch vs monotonic 절대값 혼합 금지. 이 결과만으로 OS/FastDDS/Gazebo native/Executor 확정 금지.

## 4. RED→GREEN #2: Jazzy 2-argument LaserScan RMW 정확한 쌍
- Student `tools/p2_g07_scan_rmw_first_pair.py` + `test_g07_scan_rmw_first_pair.py`: `MessageInfo` source timestamp/received timestamp/publication sequence를 각각 보존하고, 최초 위반의 **같은 sim Header Stamp + 같은 host-monotonic callback 쌍**을 독립적으로 고정. 각 소스/RMW/Observer **간격**만 비교; epoch 절대값은 빼지 않음.
- `tools/p2_g07_scan_wall_pregoal.py`에 12s 동안 Scan/SafetyScan 메타데이터만 bounded deque (최대1000)로 추가. 추가 파일 콜백 쓰기·Goal·cmd_vel·QoS 변경 없음. Scan/Clock/Odom **300ms** 및 헤더 **150ms**와 preGoal 12초 불변. 모든 상태 `release=HOLD`, `root_cause_proven=false`.
- RED #44864169957 → GREEN #44864249604: RMW 진단 신규5 및 기존 건강/Events/Scan 테스트 PASS.
- 공개 전체 #44864295405 **309 PASS, 3 SKIP**; 교육용 테스트와 수치회귀만 통과했으며 실제 ROS 개선 증거 아님.

## 5. 현재 병합/실증 상태
- 신규 public Draft PR #214, Student Draft PR #88. public branch `fix/g07-events-first-health-boundary-ci-20261121`, Student branch `fix/g07-events-first-health-boundary-20261121`.
- 최초 Scan RMW 메타데이터를 실제 native Jazzy에서 비교하도록 별도 단일 진단 CI #44864310689를 출고(결과는 해당 Actions 종료 상태로만 확정). 이는 원인 분리 실험이며 **2-cycle L2 인수가 아님**.
- 다음은 #44864310689의 실제 `first_scan_rmw_pair`에서 출처 간격, subscriber-received 간격, Observer callback 간격을 대조. 최초 상태 전이/최초 TTL 위반 먼저 분석 후에만 minimal candidate 선택. 이미 실패한 EventsExecutor나 SingleThreadedExecutor를 GREEN으로 승격 금지.
- 새로운 실제 runtime 수정은 공개 CI 회귀 RED→GREEN 후 independent Gazebo 2/2를 완료해야 함. 어느 채널에서든 CM120/Guard150/Scan/Clock/Odom300 위반 또는 Guard internal age 미측정 → **전체 L2 HOLD**. WSL2 최종 한 번의 Owner L3 전까지 SHA-pinned release 금지.
- 강사용 정답 private, 학생 TODO 독립 repo. `main` 병합하지 않음.

## 6. 최종 추가 실증 — 공식 EventsExecutor 후보 REJECT/HOLD

### 실제 Jazzy + Gazebo #44864310689 (단일 진단, L2 FAIL)
- 같은 정확 Student SHA `8bc6826eed88726c166118dfb2b8d7425bafc574`. Scan 12초 사전검사는 PASS였으나 Goal **발행 전** 기존 `p2_g07_ci_moving_goal.py` Observer의 worker `Thread-1 (spin)`이 `SystemError: null argument to internal routine`로 종료.
- **최초 사건은 Worker SystemError**. 이후 HEALTH12s 만료는 파생 증상이지 원인 아님.
- 첫 HEALTH 표본: Supervisor state NULL, Clock 미진행, Scan 없음, `cm_lifecycle_ok=NULL`. 마지막 표본도 Supervisor state NULL, Scan 없음, CM lifecycle NULL, 마지막 Clock/Odom 콜백 age 약11773ms. 별도 Python heartbeat는 지속. `goal_sent=false`, `release=HOLD`.
- 기존 2/2 real native Multi 성공 SHA와 **다른** 실험용 Executor 설정이며, S3 로그만으로 rclpy C++ 내부 함수의 causal root는 규명되지 않음. 단, 현 환경에서 candidate rejection의 충분한 실증.

### 실제 Jazzy 2-process native L1 #44864606500 (NO_GAZEBO / NO_GOAL, FAIL)
- 동일 공개 고정 Jazzy 이미지에서 별도 DDS publisher process의 300Hz `/clock`, 10Hz `/scan`을 동시에 수신하는 `rclpy.experimental.EventsExecutor`의 `ex.spin_once(timeout_sec=.04)`가 **동일 `SystemError: null argument to internal routine`** 발생.
- 따라서 본 오류는 Gazebo Goal/Stop/Cancel/Nav2 lifecycle, 장애물 물리 이동과 무관한 최소 별도 ROS DDS 이벤트 환경에서도 재현됨.
- 해당 실증은 특정 버전의 `EventsExecutor` 조합 실패를 입증하지만 upstream C++/RMW 직접 원인을 인증하지 않음. 관련 upstream [rclpy#1644](https://github.com/ros2/rclpy/issues/1644)는 pub/sub destruction SIGSEGV로 증상이 다르므로 인과 근거로 오용하지 않음.
- **결정**: 실제 G07 L3 Owner/CI release에서 EventsExecutor candidate 사용 금지. 기본 2-worker MultiThreadedExecutor는 보존. EventsExecutor 기반 신규 2/2 실행으로 인수 승격 금지.

### CI 회귀 편입 (원인 미확정이어도 첫 Worker 예외는 판별)
- 기존 코드 `d06/diagnostic/g07_events_first_abort.py`와 `tests/test_g07_events_first_worker_abort.py`를 **재사용/최소 확장**, 새 진단 모듈 중복 개발 없음.
- 새 실증 L1 #44864606500의 정확한 `ex.spin_once` + `SystemError` 원본 오류를 이전 native worker 추적과 별도 구분해 `JAZZY_EVENTS_EXECUTOR_L1_SYSTEMERROR_HOLD`로 fail-closed.
- RED [#44864803377](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44864803377) expected missing classifier, GREEN [#44864874167](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44864874167) **310 passed, 3 skipped** + Student 필수 안전 테스트. `root_cause_proven=false`, `certified_estop=false`, `owner_l3_accepted=false`.

### 검증 한계와 다음 최소 개발 단위
```text
LATEST_PUBLIC_FULL_L0=310_PASS_3_SKIP
LATEST_REAL_GAZEBO_EXPERIMENTAL_EVENTS_L2=FAIL
EVENTS_EXECUTOR_WORKER_SYSTEMERROR_CAUSING_HEALTH_TIMEOUT=CONFIRMED
EVENTS_EXECUTOR_SECOND_ROS_PROCESS_L1_SYSTEMERROR=CONFIRMED
EXPERIMENTAL_EVENTS_EXECUTOR_RELEASE=REJECTED
PREG0AL_SCAN_300_MS_ROOT=UNPROVEN
ORIGINAL_MULTI_2_WORKER_NATIVE_2_OF_2=HISTORIC_DIFFERENT_SHA
OWNER_WSL2_FINAL_L3=NOT_RUN_HOLD
MAIN_MERGE=false
```

다음 후보는 **기존 2-worker baseline**을 고정하고 Scan 첫 424.373ms 대 independent rosbag 동일 header 101.297ms를 근거로 **원 Observation 프로세스의 수신/take/Executor 경계**만 최소 분석하는 것. DDS Received 실제 시간차·독립 CM publication seq 및 ROS bag 동일 헤더 증거를 대조해 처음 실패를 결정. Python Callback / Writer / flush 자체 max <3ms 관측 이전 증거 보존. `EventsExecutor` 재선정, ROS2 내부 직접 패치, 안전 TTL 완화, 새로운 Planner/Supervisor/CM 및 과도한 C++ 노드 추가 금지. 기본 Multi2에서도 120/150/300ms 전체 safety gate 실제 Gazebo 2/2 GREEN과 현장 WSL2 단일 인수가 전까지 출고 HOLD.
