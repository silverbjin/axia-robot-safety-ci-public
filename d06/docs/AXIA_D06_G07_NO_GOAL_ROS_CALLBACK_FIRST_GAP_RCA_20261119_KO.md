# AXIA D06/G07 — 최초 Scan 수신 지연 계층 분리 및 진단 노드 최소 수정

작성일: 2026-11-19 · 기준: AXIA Robot Safety MVP, ROS 2 Jazzy, Gazebo Harmonic, TurtleBot3 Waffle, 공식 Nav2

## 증거 보존 및 최초 실패

본 보고서는 같은 G07 NO_GOAL 물리 월드와 Safety 300ms 규칙을 고정하며, 현장 NVIDIA WSL2 `fr1FN4YJ`에서 얻은 20.003초 센서 안전창 PASS와 종료 시 native witness134 / Gazebo-11 실패를 **별도**로 다룬다. 최초 오류는 사후 최종 예외가 아니라 동일 source-stamp 쌍과 host callback 수신 시각으로 판단한다.

- 공개 실제 Gazebo L2 [#44476730420](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44476730420): Raw181.869ms, Safety178.448ms, 두 토픽 관찰20.003초, Native witness0, Nav2 Navigation ACK true/Localization ACK false (서비스 TIMEOUT), CM exit0, Gazebo exit0. 최초 차단은 Localization 관리 서비스의 응답 경계.
- G07 Task04의 **기존** 독립 per-manager rclpy 노드 종료 구현을 `student/.../tools/p2_g07_ordered_shutdown.py`에 재사용함. 한 관리자를 한 번씩만 호출, 기존 총 60초 제한과 ACK 필수, 프로세스 신호·Goal·Scan300/CM120/Guard150 불변.
- RED [#44489372953](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44489372953) / GREEN [#44489757561](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44489757561) **L0 97/97**, 독립 rclpy 노드 생성·반납 및 NO_GOAL 강사 소스 핀 계약.
- 공개 실제 Gazebo L2 [#44489912476](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44489912476): Nav2 Navigation ACK **2.346458s**, Localization ACK **0.257451s**, CM exit0, Gazebo 정상 종료 및 /server_control ACK. Guard/Supervisor도 실제 process finished cleanly. 다만 **Raw 388.529ms / Safety 385.188ms**로 300ms 엄격 TTL 위반. 이 실행은 당연히 NO_GOAL 인수 실패다.

## 동일 Scan 소스 타임스탬프 비교 (실제 아티팩트)

첫 Student 안전창 위반의 정수 source stamp: `36300000000 → 36402000000 ns`. 이 쌍은 매개 계층별로 다음 시간간격을 갖는다.

| 동일 LaserScan 쌍 수신기 | host 간격 |
|---|---:|
| Gazebo Transport native | **109.453ms** |
| 독립 ROS Raw observer | **110.658ms** |
| 독립 ROS Safety observer | **112.480ms** |
| Student `/scan` 단일 Executor 콜백 계측 | **388.529ms** |
| Student `/safety/scan` 단일 Executor 콜백 계측 | **385.188ms** |

Student Safety callback `after`의 지연은 독립 ROS Safety observer의 같은 source-stamp `after`에 비해 **273.481ms**이다. 이 자료는 Gazebo 내부 LiDAR publish 및 DDS send 시각을 측정하지 않는다. 그러나 Gazebo와 **독립적인 ROS 구독기까지 이미 같은 데이터가 적시에 도착**했다는 사실을 확정한다. 따라서 최초 지연 경계는 Student 진단 콜백/프로세스 스케줄링 이후로 좁혀지지만, Executor와 CPU 스케줄러 중 단일 근본 원인까지 확정한 것은 아니다.

## RED → GREEN → REFACTOR → REVIEW → COMMIT

1. `d06/tests/test_d06_g07_student_first_receipt_pair.py`: 동일 source stamp로 native/독립 ROS/Student 진단 수신 간격을 교차 검증하고, ROS observer를 통한 도착을 증명하는 RED. [#44491080168](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44491080168).
2. `d06/tools/d06_g07_scan_rx_witness.py`: 기존 `classify_student_first` 함수에 독립 ROS peer 수신 시각 필드만 추가. `student_first_boundary=AFTER_INDEPENDENT_ROS_RECEIPT`, `cause=UNDETERMINED`, `release=HOLD`를 검증. GREEN [#44491172539](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44491172539), **L0 98/98**.
3. **측정 로직 자체에서 발견한 한정된 오류:** 기존 `student/.../tools/g07_wslg_no_goal_sensor_probe.py`는 callback 진입 후 전방·측면 거리 계산을 마친 시점에 `time.monotonic()`을 기록함. 이 시각을 'host receipt'로 보고하면 콜백 진입과 계산 시간이 섞인다. 해당 RED [#44491393783](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44491393783)에서 코드 순서 위반을 입증.
4. **최소 GREEN**: Student 진단 `scan_callback`의 수신 시각 취득만 **콜백 최상단**으로 이동. Scan 비즈니스 로직, 기존 300ms FAIL 조건, 20초 full 두 토픽, Safety Supervisor/Guard/Nav2, E-Stop, Goal/Fault 금지 불변. 공개 Student SHA `ad86587c30e41a2bbc291c0418bdddd6dcea974f` / Probe blob `1f00c7118f55ed72257155b92e83a98d6dcbc017`.
5. 강사 원샷은 Student 및 native/ROS peer 소스를 immutable Git commit+blob으로 검증 후 사용. 공개 CI 최종 RED/GREEN [#44491667072](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44491667072)에서 **L0 99/99**.
6. 실제 Gazebo L2 동일 월드 실행 [#44491751936](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44491751936): 작성 시점 **진행 중**. 이 결과로 최초 측정 결함 최소 수정의 효과를 판단. 수신 지연이 계속되면 Python 진단 Executor/clock/odom 콜백 경쟁과 OS 스케줄링을 별도로 분류할 것.

## 인증·검증 한계

- **실제 현장 WSL2 NVIDIA NO_GOAL 재인수:** 미실행. 기존 fr1 증거는 센서 20초 성공/종료 오류를 분리해 보존.
- 공개 CI **L0 99/99**는 ROS/Gazebo 실행 결과가 아님. 실제 L2는 위 실행 결과를 참조해 별도 판정.
- **Moving Goal**: 송신하지 않음. CM120ms/Guard150ms 노드 간 전송 TTL, Goal 취소 및 물리 정지, 속도 감속·STOP 통합 검증 **미완료**. CI 단독 PASS 또는 센서 관찰 성공은 Moving L3 승인으로 승격 불가.
- `AXIA_MVP_DEMO_ACCEPTED=HOLD`, `D06_GAZEBO_LIVE_RELEASE=HOLD`, `CERTIFIED_ESTOP=false`. main 병합은 사용자 승인 필요. 기존 Task04 Moving Goal/공식 Nav2 재사용; 별도 주행 알고리즘·Supervisor 개발 금지.
