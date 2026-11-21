# AXIA G07 — MVP 리팩토링 실제 CI·Gazebo 검증 보고서

검증일: 2026-11-21. **최종 NEW G07 MOVING RELEASE = HOLD (0/2)**. 기존 jrCIgoGl 교육용 실제 WSL2 성공 기준선은 그대로 보존함.

## 수정 및 검증 대상

Student PR #105 HEAD a04f9a7da8d54bbd9f944d05388792cb706adf28:
- block_B/day07/h01_runtime/ros2_ws/src/axia_safety_supervisor/axia_safety_supervisor/p2_shutdown_context.py (17줄 확장)
- block_B/day07/h01_runtime/ros2_ws/src/axia_safety_supervisor/axia_safety_supervisor/p2_supervisor_node.py (약 6줄 추가/2줄 제거)
- block_B/day07/h01_runtime/tools/test_g07_context_graph_shutdown.py (81줄)
- .github/workflows/block-b-python.yml (기존 L0 workflow에 unittest 1개)

Public PR #229: .github/workflows/axia-g07-original-multi-first-scan-rmw-native-l2.yml 및 tests/test_g07_first_scan_rmw_evidence_export.py, tests/test_g07_stabilization_wsl2_release.py. Main/공식 Nav2/CM/Guard/Fault/Launch/센서 SDF/안전 TTL **변경 없음**.

## 실제 테스트 명령 및 결과

| 단계 | 실제 명령·CI Run | 실제 결과 |
| --- | --- | --- |
| RED | python -m unittest discover -s block_B/day07/h01_runtime/tools -p test_g07_context_graph_shutdown.py -v / Student #44914584695 | Ran 4 tests; FAILED (failures=1, errors=2), 1 PASS. 원 classifier 부재 및 main 연결 누락 |
| GREEN | 동일 unittest / Student #44914690178 | Ran 4 tests in 0.001s; OK. Block B: 59 passed in 8.83s |
| Student 실 ROS/Gazebo NO_GOAL | #44914690240 | public-source-l0 success, actual-gazebo-physical-rviz-l2 success. Moving Goal은 전혀 검증하지 않음 |
| Public Python 첫 변경 | #44914842301 | 1 failed, 340 passed, 3 skipped. 냉동 Owner pin을 새 Native Student와 비교한 정적 테스트 수정 필요 |
| Public Python 완료 | python -m pytest -q -ra tests / #44914941704 | 341 passed, 3 skipped in 4.46s |
| 실제 G07 Jazzy/Harmonic MOVING Native | #44914827138 / exact Public 8e03ac0a912ca9b81bdddda70212e52e6d804389 + Student a04f9a7da8d54bbd9f944d05388792cb706adf28 | Cycle1 FAIL, Cycle2 FAIL, 0/2. WSL2 L3 NOT_RUN |

Links:
- https://github.com/silverbjin/axia-robot-safety-student/actions/runs/44914584695
- https://github.com/silverbjin/axia-robot-safety-student/actions/runs/44914690178
- https://github.com/silverbjin/axia-robot-safety-student/actions/runs/44914690240
- https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44914941704
- https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44914827138

## Native FIRST boundary — cycle1 PRE-GOAL (job 136878073308)

최초 수신 위반은 /scan 439.011892ms (기준 300ms), Header SIM 간격 99ms, 원 소스 RMW 간격 107.872841ms, 원 Subscriber RMW receive 간격 436.808763ms, 발행 seq +1. /safety/scan max437.854482ms, /clock max335.393855ms, /odom max374.025229ms. Scan wall 간격 자체는 진단이지만 Clock/Odom 300ms blocking 정책을 위반했으므로 SCAN_PREFLIGHT_CLOCK_ODOM_INTERVAL_BREACH, Goal 미발행. Window RTF 0.997764는 첫 위반을 무효화하지 못함. DDS publish/receive/Executor 근본원인 미입증.

## Native FIRST boundary — cycle2 POST-GOAL (job 136878073552)

최초 관측 FSM: BOOT_SAFE→NORMAL at host monotonic 917.207396783, 당시 최초 Guard latch 관측 없음. 최초 timing breach /odom 362.100229ms (PRE_STOP, 300ms limit, at 918.887748365). 이어 /cmd_vel_pre_guard 379.730024ms (120ms limit), /supervised 380.284551ms, /guard 376.744460ms, /clock 330.512499ms, /scan 399.010137ms.

동일 CM publisher seq+1 pair: original Observer RMW received 375.941379ms vs independent RMW 54.116537ms, source 53.837048ms; first independent heartbeat max22.371395ms. 원 Subscriber 수신 경계 지연 후보이지만 DDS/Executor/OS 원인은 미입증. 실제 oracle은 ACTUAL_MOVING_GOAL_CI_ORACLE_SAFETY_DELIVERY_TTL_BOUNDARY_max_source_interval_sec로 fail-closed. 즉 본 종료 예외 수정으로 안전 계층 전체 문제는 해결되지 않음.

## SHA256·raw custody

GitHub Actions artifact API에서 직접 확인한 ZIP digest (WSL2 raw bag SHA가 아님):
- Cycle1 artifact #14711535706; sha256:c81c9fa17c7d42edad6ea4265e6014797e82d9eba99a9ef90f0cc16e0687ad42 (11,847 bytes)
- Cycle2 artifact #14710974261; sha256:5b0fa367f68f19b69b68d018951beb52e3320860c09855fa295500c99aa46d55 (23,804 bytes)
- Student D07 artifact #14711470808; sha256:ea3845d3a6841d90f4925a57a2d74711eff97ed1b5a581a3f9cb831434aab2b9 (369,685 bytes)
- Artifacts expire 2026-12-05. 추후 장기 보존은 원본 안전 정책대로 별도 보관할 것.

## 변경 전후 비교 (미측정 항목 엄격 구분)

| 항목 | 변경 전 | 변경 후 | 검증 |
| --- | --- | --- | --- |
| ROS2 패키지 | 4 ament_python | 동일 | Git tree PASS |
| G07 scripts | 3 Shell | 3 Shell (제거0) | Git diff |
| Runtime ROS 노드 수 | 기존 | 동일 | 새 Node 없음, 실제 PID 정량 비교 NOT_MEASURED |
| 환경 변수·Launch | 기존 구조 | 동일 | 소스 diff PASS |
| Supervisor 종료 오류 | 해당 RCLError unhandled | 이미 shutdown한 context만 정확히 분류 | Unit PASS; 실제 Moving 해당 예외 경로 재재현 여부 NOT_PROVEN |
| CPU/RAM/동시 스레드 | NOT_MEASURED | NOT_MEASURED | 개선 주장 불가 |
| RTF·수신 TTL | 간헐 지연 | 두 사이클 다시 위반 | G07 Moving L2 FAIL |
| D07 NO_GOAL | 기 구축 | PASS | 실 Gazebo만, Goal 아님 |
| 새 G07 Moving 인수 | 별도 이전 성공 교육용 baseline 존재 | 0/2 FAIL | 새 source L3 NOT_RUN |

## 결론

L0 PASS; 실제 ROS 패키지 진입/NO_GOAL L2는 관측됐으나 전체 독립 CLI L1은 PARTIAL; strict G07 Moving Native L2 FAIL 0/2; WSL2 L3 NOT_RUN; RELEASE HOLD; main NOT MERGED. SW STOP != certified E-Stop.
