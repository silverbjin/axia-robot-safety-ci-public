# AXIA G07 Task04 — oZG 후속 Localization 종료 ACK 최초 경계·RED→GREEN 디버깅 보고서

작성일: 2026-11-19 (KST) / ROS 2 Jazzy / Gazebo Harmonic / 공식 Nav2.

## 1. 개발 범위와 이전 성공 증거 보존

- 공개 CI: `silverbjin/axia-robot-safety-ci-public`, `fix/g07-task04-owner-timing-evidence-20261119`.
- Student: `silverbjin/axia-robot-safety-student`, 동일 브랜치.
- 원본 강사 WSL2 oZGSnDD1의 임시 Nav2 월드 `/tmp/nav2_*.sdf` 미생성 경계는 기존 H01의 Xacro→Gazebo OnProcessExit 재사용으로 재현·최소 수정했다. 현장 원본 TAR/ZIP은 비공개 보존, 공개에는 기밀 rosbag을 올리지 않는다.
- 새 Student `bcebc5d1f3a7d00860a541507e263dd05b27a9a3`에서 공개 L0 5/5 [#44440787429](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44440787429), 실제 ROS Jazzy Launch L1 3/3 [#44440794690](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44440794690) 성공.
- 그러나 **실제 Moving Goal L2는 동일 Student SHA에서 2회 종료 실패**하였으므로 새 Owner 출고 중단. Goal, CM, Guard, Sensor, world, Source 120ms, Guard 150ms, LiDAR 10Hz, 안전 정책은 일절 수정하지 않는다.

## 2. 실제 최초 실패 경계: Localization 매니저 서비스 ACK

공개 실제 native Gazebo/Nav2 Moving+GUI:
- [#44440932197](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44440932197): 실제 CLEAR→SLOW→STOP, 이동 약 0.2015m, zero dwell 1.016s, 정확 UUID CANCEL 성공. Navigation shutdown ACK 약 2.584s 후 Localization ManageLifecycleNodes SHUTDOWN **30.000756s SERVICE_TIMEOUT**.
- [#44442176276](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44442176276): 실제 CLEAR→SLOW→STOP, 이동 약 0.2166m, zero dwell 1.043s, 정확 UUID CANCEL 성공. Navigation shutdown ACK 약 2.491s 후 Localization SHUTDOWN **30.002923s SERVICE_TIMEOUT**.
- 전자는 실제 Gazebo 시작, Clock 및 Goal 모두 정상. 최초 안전 상태 전이/시간 공백이 아니라 종료 관리 서비스의 최초 ACK 지연으로 구분한다.
- 로그에 실제 Localization manager가 사전 SIGINT 상태에서 SHUTDOWN 전이를 시작했다고 입증할 항목은 확인되지 않았다. Nav2 종료 요청이 매니저까지 전달됐는지, Client executor의 응답 처리가 막혔는지, 매니저가 요청을 처리하지 못했는지 아직 최종 규명 불가.
- 뒤따르는 Supervisor `rcl node's context is invalid` 예외는 전체 프로세스 그룹 SIGINT에 따른 후속 증상이지 첫 실패로 취급하지 않는다.
- 해당 두 L2 모두 `G07_NAV2_ORDERED_SHUTDOWN.status=BLOCKED_LIFECYCLE_LOCALIZATION_SERVICE_TIMEOUT`, `localization_ack=false`. **21/21 PASS가 아니다.**

## 3. 기존 코드 분석 및 가장 작은 검증 가설

기존 `block_B/day07/h01_runtime/tools/p2_g07_ordered_shutdown.py`는 단일 `rclpy.create_node('axia_g07_ordered_shutdown_guard')`에서 preflight GetParameters 후 Navigation SHUTDOWN, Localization SHUTDOWN을 차례로 호출했다. `p2_g07_lifecycle_service.py::call_native_manage()`는 공통 Native Service Client와 `rclpy.spin_until_future_complete`를 재사용한다.

가설: Navigation 서비스 요청/응답 후 동일 rclpy node/executor 상태가 Localization 서비스 요청을 관측하는 데 영향을 줄 수 있다. 두 번의 실제 timeout만으로 이 가설이 증명된 것은 아니다. 공식 Nav2 manager가 거절하거나 반응하지 않았을 가능성도 남는다.

시스템 전체 안전 임계값과 기존 ACK/60s 총 마감/Localization 30s response 마감은 유지한다.

## 4. 재현 RED → 최소 수정 GREEN

- Student `tools/test_g07_task04_localization_isolated_client.py`에서 fake rclpy를 이용해 (a) 내비게이션·로컬라이제이션 각각 독립 노드 사용, (b) 딱 1회 Native SHUTDOWN 요청, (c) TIMEOUT은 ACK로 위장하지 않음, (d) 기존 30s/40s budget 및 total deadline 유지 회귀 3개 추가.
- RED 공개 [#44443257191](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44443257191) 3개 중 2개 ERROR:
  ```text
  AttributeError: module 'p2_g07_ordered_shutdown' has no attribute '_call_isolated_stage'
  Ran 3 tests; FAILED (errors=2)
  ```
- Student 수정 `_call_isolated_stage(rclpy, manager, timeout_sec)`: 기존 `call_native_manage`를 **새 일회성 노드**로 호출한 뒤 `destroy_node()`. 기존 `p2_g07_ordered_shutdown.run`에서 Navigation·Localization 각각 이를 사용. **새 서비스 타입·별도 재요청·시간 초과 예외 완화 없음**. ROS Graph 조회 노드는 동일 범위 유지.
- Student 수정 SHA `6579e2eef7e99691da558cd2de1964fd26a04621`.
- GREEN 공개 [#44443374979](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44443374979): 신규 3/3 + 기존 `test_g07_task03_localization_shutdown_budget.py` 3/3, **6/6 PASS**.
- 기존 Guard/CM 계약 [#44443381457](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44443381457), Python [#44443381499](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44443381499), Runner Canary [#44443381520](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44443381520) PASS.
- 여기까지는 ROS/Gazebo를 실행하지 않은 **L0 검증**이다.

## 5. 실제 Gazebo Moving Goal L2 검증·출고 경계

- 공개 workflow: `.github/workflows/axia-g07-task04-owner-n7-parity-native-l2-20261119.yml`, commit `7b7ae03cb1036262d7772165aecae77bcd386aea`.
- CI에서 정확한 Student `6579e2eef7e99691da558cd2de1964fd26a04621`을 clone, 6개 L0 회귀를 원샷에 포함, 동일 native Gazebo8 Contact 증인을 빌더 Job에서 빌드한 뒤 13.6 런타임에서 실제 Gazebo+Nav2+Waffle Moving Goal+Gazebo/RViz Xvfb를 실행한다.
- 최종 실제 CI: [#44449459417](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44449459417) **SUCCESS**, 21/21 scoped gate verdict; L2 실행 GitHub workflow commit `7b7ae03cb1036262d7772165aecae77bcd386aea`, source pin `6579e2eef7e99691da558cd2de1964fd26a04621`. 실제 Xvfb Gazebo/RViz 2개 관찰, runner rc=0, verdict `first_failure=NONE`, `status=TASK04_REAL_GAZEBO_MOVING_GUI_L2_SCOPED_PASS`, runtime `libgz-transport13=13.6.0` 유지. Allowlisted numerical artifact [#14495301259](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44449459417/artifacts/14495301259).
- 필수: Gazebo World SDF 정상 로드, Clock/Scan/Odom/TF, Goal UUID, CLEAR→SLOW→STOP, Source/Observer 120ms, Guard 150ms, Contact0, zero dwell≥1s, Navigation ACK와 Localization ACK, CM clean exit, SQLite14, GUI2, 21개 엄격 게이트 **동일 실행에 모두 PASS**.
- L2 실패 시 기존 성공 Goal/감속/정지 조건을 반복 확장하지 말고 최초 localization service transition과 ROS timestamp/CPU·executor 증거를 먼저 좁힌다. 30s을 늘리거나 Retry로 결과를 우회하지 않는다.
- 실제 Owner WSL2 L3는 한 번도 새 고정 소스로 실행되지 않았으므로 `AXIA_MVP_DEMO_ACCEPTED=HOLD`; 인증된 E-Stop과 SW Stop 구분.

## 6. 검증 수준

```ini
L0_LOCALIZATION_CLIENT_RED=REPRODUCED
L0_LOCALIZATION_CLIENT_GREEN=PASS_6_OF_6
PUBLIC_CI_REAL_GAZEBO_L2_FINAL=PASS_21_OF_21_RUN_44449459417
OWNER_WSL2_L3=NOT_RUN
CERTIFIED_ESTOP=false
AXIA_MVP_DEMO_ACCEPTED=HOLD
MAIN_MERGED=false
```

## 7. REVIEW 및 Owner L3 출고 경계

- 수정 범위: 서비스 Client별 일회성 노드; 기존 `call_native_manage`, 원본 Nav2 SHUTDOWN 서비스, 40s/30s 개별 timeout, 60s 총 마감, Navigation+Localization 두 개의 실제 ACK 검사 및 CM clean exit 모두 유지.
- 단일 L2 GREEN은 Client 재사용이 유일한 물리적 원인임을 증명하지는 않는다. 기존 실패 2회의 Localization timeout과 후속 성공이 **구체적인 최소 변경 전·후 경계**를 검증하지만, DDS의 간헐적 지연 재발 가능성 및 강사 WSL2는 미검증으로 분리한다.
- 정확한 Owner runner source `scripts/axia_g07_task04_owner_moving_l3_once.sh`가 Student `6579e2eef7e99691da558cd2de1964fd26a04621`과 public actual L2 `44449459417`을 pin했다. 원샷 배포 코드 commit `615a43fae7b82e583e34440f9673e1862843e659`, 함께 고정된 테스트 commit `1816fbbbfdb972e52c5168ade26c768167998556`.
- [Owner Bootstrap L0 #44450173850](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44450173850) **8/8 PASS**: exact SHA, manual /dev/tty consent, source validation, private tar/zip SHA256, no global kill, GPU server/GUI separation, original pregoal failure preservation.
- 공개 L0/actual L2/Bootstrap 성공 후 강사 WSL2에서는 `--self-check`에 이어 단일 `--run` L3 수행. 새 현장 실패 발생 시 동일 증상 반복 재실행 대신 최초 Safety state 및 서비스 응답 시간 경계 증거를 회귀로 편입.
- **Main 병합 안 됨. 인증된 HW E-Stop 아님.**

```ini
G07_WORLD_XACRO_RACE_L0=PASS_5_OF_5
G07_ROS_JAZZY_LAUNCH_L1=PASS_3_OF_3_NO_GAZEBO
G07_SHUTDOWN_FRESH_CLIENT_L0=PASS_6_OF_6
PUBLIC_CI_MOVING_NATIVE_GAZEBO_L2=PASS_21_OF_21
OWNER_BOOTSTRAP_L0=PASS_8_OF_8
OWNER_WSL2_L3=NOT_RUN
AXIA_MVP_DEMO_ACCEPTED=HOLD
CERTIFIED_ESTOP=false
MAIN_MERGED=false
```
