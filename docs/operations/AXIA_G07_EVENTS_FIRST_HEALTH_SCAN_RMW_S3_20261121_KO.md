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
