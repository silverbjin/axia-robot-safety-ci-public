# AXIA D06/G07 — 최초 Student Scan300 수신 지연·안전 관찰창·Lifecycle 종료 재현 보고서

- 기준 날짜: 2026-11-19
- 실험 영역: 공개 GitHub Actions Ubuntu24.04 ROS2 Jazzy/Gazebo Harmonic/공식 Nav2/TurtleBot3 Waffle + Xvfb Gazebo/RViz NO_GOAL 단일 월드
- 인수 수준: 공개 CI의 **NO_GOAL 통합 L2**, 강사 NVIDIA WSL2 **L3 미수행**
- 공개 CI: `silverbjin/axia-robot-safety-ci-public`, PR #177 `fix/d06-wslg-lidar-vs-rtf-ci-20261118`
- 학생: `silverbjin/axia-robot-safety-student`, PR #62 `fix/g07-nogoal-ordered-cm-shutdown-20261119`, **실행 코드 SHA `f1f5d932de831d3dabedf9a44a5fa27cf5705f42`**
- 강사 실행기: `d06/scripts/axia_d06_g07_wslg_gpu_rtf_compare_once.sh`, blob `aa032b3fef250369804cf5151e11d52821dd63bc`
- 본 작업은 단순 서비스/센서 계측 경계 최소 수정; 안전 임계값 및 공식 Nav2/CM/Gazebo 소스 변경 없음

## 1. 원본의 최초 실패 계층 분리

### A. 기존 강사 WSL2 ZOAgryLW
- 제출 원본 SHA256 `5fe3f39b02cda4a7255a0e733a425efb0a9880fddb89285c8c85fcef72618a03`.
- 센서 거리 157/157 CLEAR, 전방 1.414m, 측면 2.520m. 그러나 Raw/Safety host receipt 각각 최대452.540ms/458.803ms로 **Scan300ms FAIL**, 전체 Clock RTF0.782939.
- 첫 global startup: native Scan96.390ms, ROS Raw96.791ms, ROS Safety379.498ms. Nav2 준비 뒤 첫 20s *proxy*는 Gazebo native Scan374.240ms·국소 Clock RTF≈0.331. 이 두 현상은 발생 시각과 경계가 다름.
- 종료: Navigation/Localization ACK=true, CM exit0, **Gazebo server exit -11**. 이전 CM SIGSEGV와 다른 프로세스의 결함.

### B. 실제 공개 L2 재현: #44455727595
- [Run #44455727595](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44455727595), 원본 [artifact](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44455727595/artifacts/14496589561) 및 checksum.
- Student 첫 Raw TTL 수신 실패: source stamp **44.400→44.502s**, Student callback wall mono206.976532→207.410886s = **434.354ms**.
- *정확히 같은 두 source stamp*의 Gazebo native receipt gap **103.745ms**; 독립 ROS raw observer 역시 약103ms. 결론: 이 최초 위반은 Gazebo native 수신 **이후** Student ROS 초기 구독/콜백 경계에서 발생.
- 원본 `raw_first_gap_diagnostics.phase=BEFORE_FIRST_SAFETY_SCAN`: Student Raw가 먼저 수신되는 동안 Safety의 첫 샘플이 없었음. **안전 READY가 아직 성립하지 않았는데 첫 Raw 시점부터 20초 검증을 카운트**했던 관찰 시작점 오류가 결정적. 이 구간의 안전 증거는 버리지 않고 PRE-READY 사건으로 별도 보존.
- 별도 native READY 근방 첫 gap301.227ms, 국소 Clock RTF0.367259. 이것은 최초 Student Raw 434ms와 다른 시각·메시지 쌍이며 Gazebo 내부 publisher CPU/GPU 원인은 검증되지 않았음.
- 종료 helper는 `SERVICE_MISSING:/lifecycle_manager_navigation/get_parameters`: 기존 신규 rclpy 클라이언트의 단발 3s 발견 실패. 실제 launch에서는 lifecycle manager가 계속 동작하다가 SIGINT 때 preshutdown 수행. 종료 ACK 미수신 뒤 일괄 SIGINT로 CM child `exit -11`, Gazebo server exit0. 3초 탐색 실패와 CM crash 사이의 **인과 관계는 스택 없이 단정 불가**.

## 2. RED → GREEN: 두 번째 시연을 위한 최소 조치

### Sensor Gate
- 학생 `tools/g07_wslg_no_goal_sensor_probe.py`에 `select_dual_topic_window(records)` 도입, Raw와 Safety 두 토픽이 모두 실제 도착한 호스트 시각에서 **새 20초 wall 관찰**을 시작. 그 전에는 NO_GOAL·승인 거부.
- 원래 `assess_window`의 300ms receipt TTL, 센서 source stamp 단조, 전방 >0.75m·측면 >1.2m, Odom 정지, Clock 순서, CLEAR count 확인을 바꾸지 않음. 시작 이후 지연 300ms 초과·20s 미달·토픽 누락은 모두 HOLD.
- READY 이전 원본 434ms 같은 Raw gap은 `startup_pre_both_scan_diagnostics` 및 compact forensic에 보존. 이를 정상 주행 중 수신 0.1초로 고쳐 적지 않음.
- D08 native `/scan` 및 Clock + 별도 ROS 수신 2개 witness + *Student 실제 최초 TTL source stamp*와 동일 세션 자동 일치. 한 번의 CI/Gazebo 실행으로 계측하고 초대용량 로그 대신 작은 tar/JSONL 관리.

### Lifecycle / Gazebo shutdown
- 학생 `tools/p2_g07_ordered_shutdown.py`의 `GetParameters` 신규 서비스 탐색에 `wait_for_service_bounded()` 추가: 최대12초, 1초 단위 반복, 원래 **60초 전체 shutdown deadline 내**에서만 실행. 실패면 ACK 없이 fail-closed.
- 이미 검증된 공식 Nav2 navigation→localization ACK 후 Gazebo WorldControl `pause:true` 요청, 이후 launch SIGINT. Collision Monitor와 Gazebo server의 **각 child 실제 exit0**를 분리 검증.
- Goal/Twist, Fault, 임의 ROS Nav2 Planner/CM 변경, Scan300/CM120/Guard150 파라미터 변경은 전혀 없음. SW STOP ≠ 인증 E-Stop.

## 3. 공개 CI 실제 결과

- **RED** [#44458939278](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44458939278): 새 service-discovery 재시도 계약 실패. Raw-before-Safety 최초 gap을 중간에 숨기거나 창을 20s 미만으로 줄이지 않는 fixture 포함.
- **GREEN L0** [#44459147066](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44459147066): 두 토픽 준비, 준비 뒤 300ms 위반, 누락 토픽/시간 부족, 최대12s service discovery 계약 PASS.
- **실제 L2** [#44459151881](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44459151881), [artifact #14499585664](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44459151881/artifacts/14499585664):
  ```text
  AXIA_D06_G07_NATIVE_SHUTDOWN_SMOKE_RC=0 RVIZ=1 GAZEBO=1
  AXIA_D06_L2_FIRST_SENSOR_STATUS=NO_GOAL_SENSOR_WINDOW_CLEAR_CANDIDATE reasons=[]
  AXIA_D06_L2_NAV2_SHUTDOWN=NAV2_LIFECYCLE_SHUTDOWN_ACK nav_ack=True loc_ack=True
  AXIA_D06_L2_CM_PROCESS_AUDIT=SHUTDOWN_CLEAN_CANDIDATE cm_exit_code=0
  AXIA_D06_G07_REAL_GAZEBO_CHILD_EXIT0=True bad=[]
  ```
  센서 원본 `dual_topic_actual_wall_observation_sec=20.002`, Raw196개 최대124.332ms, Safety196개 최대122.827ms, CLEAR196/196, 전방 median1.414378m, 측면2.521269m.
  별도 native post-ready *proxy* Scan305.610ms/RFT0.396736이 dual-topic 준비 전 발생함. 이때 Goal 미송신, READY 후 완전한 20초 안전창에서만 PASS.
- **검증 강화**: 기존 종료-only L2는 sensor rc3이어도 pass 가능했으므로 새 엄격 계약을 추가. [L0 RED #44459839503](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44459839503), [L0 GREEN #44459907303](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44459907303). 실제 엄격 L2 [#44459901466](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44459901466)는 본 초안 시점 결과 대기; 검사 항목은 sensor status CLEAR, 20초 elapsed, 각 Scan300ms, CM child0, Gazebo server child0, Nav2 ACK, NO_GOAL이고 하나라도 위반하면 CI FAIL.

## 4. 인수 범위와 미검증

- 출고 게이트: 공개 L0 source pin/compact custody, 공개 실제 Gazebo strict L2, 강사 WSLg NVIDIA renderer + 실제 동일 월드 및 안전 timing L3.
- 공개 CI Ubuntu24.04의 Xvfb+software renderer와 강사 WSL2/WSLg D3D12 NVIDIA는 동일 환경이 아니므로 CI 통과를 현장 L3로 표시하면 안 됨.
- CM120ms, Guard150ms, Moving Goal GOAL/CANCEL 및 실제 정지 안정성은 NO_GOAL 검사만으로 미검증. 기존 성공 증거는 보존하고 별도 통합 시연 인수에서 확인 필요.
- `AXIA_MVP_DEMO_ACCEPTED=HOLD`, `D06_GAZEBO_LIVE_RELEASE=HOLD`, `CERTIFIED_ESTOP=false`, main 병합 없음.

참고: [ROS 2 Jazzy 서비스 Client 패턴](https://docs.ros.org/en/jazzy/Tutorials/Beginner-Client-Libraries/Writing-A-Simple-Py-Service-And-Client.html), [Gazebo Sim WorldControl Pause](https://gazebosim.org/api/sim/9/pause_run_simulation.html), [Nav2 Lifecycle Manager 설정](https://docs.nav2.org/rolling/configuration_and_development/configuration_guide/core_servers/configuring_lifecycle_manager/).
