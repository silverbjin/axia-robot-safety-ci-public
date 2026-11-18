# AXIA G07 — Task 02 최종 개발·디버깅·공개 Gazebo L2 보고서

**2026-11-18 KST | Task02 완료: COMPLETE_SCOPED_PUBLIC_L2 | 전체 MVP 출고: HOLD**

이번 작업은 ROS 2 Jazzy + 공식 Nav2 + TurtleBot3 Waffle + Gazebo Harmonic의 **공개 GitHub Actions와 공개 Student 저장소만** 사용했다. Private Instructor/비공개 Action/공식 Nav2 소스 패치 없음. main 병합 없음. **실제 단일 Gazebo 교육용 주행 범위 내 성능 수정 후보의 완료**이지, 물리 로봇의 인증된 안전, E-Stop, 전체 시연 출고 인수는 아니다.

## 1. Task01 첫 실패 및 수정 후보 검토

Task01 실제 [Run #44109119429](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44109119429) 최초 연속 CM RMW source 발행 간격 172.590315ms, Observer 173.162403ms. 동일 공식 CM callback의 TF 호출 122.282121ms 중 실제 10ms libc polling sleep 요청 12회 = **120ms**. 첫 Guard latch: UPSTREAM_STALE_AFTER_MOTION, CM age 156.944056ms / TTL150ms. Fast DDS 원본 publisher handle/Source timestamp와 native publish 시각까지 직접 조인한 근거.

공식 연구 출처:
- [Nav2 Jazzy CM Source](https://github.com/ros-navigation/navigation2/blob/jazzy/nav2_collision_monitor/src/source.cpp): base_shift_correction true는 센서시각→현재시각 Advanced TF, false는 base/source Simple TF 조회.
- [Nav2 Jazzy CollisionMonitor](https://github.com/ros-navigation/navigation2/blob/jazzy/nav2_collision_monitor/src/collision_monitor_node.cpp): 소스 getData 실패 + source_timeout 양수이면 STOP 명령 출력.
- [Nav2 Jazzy Scan source](https://github.com/ros-navigation/navigation2/blob/jazzy/nav2_collision_monitor/src/scan.cpp): 실제 LaserScan의 header-valid 및 TF 변환 사용.
- [TF2 Jazzy Buffer](https://github.com/ros2/geometry2/blob/jazzy/tf2_ros/src/buffer.cpp): TF polling 시 10ms sleep.
- [Nav2 Issue #3402](https://github.com/ros-navigation/navigation2/issues/3402), [Nav2 PR #3412](https://github.com/ros-navigation/navigation2/pull/3412): Advanced/Simple TF의 성능-시간보정 정확도 절충.

### 폐기한 후보 A — TF timeout 0.2→0.02초, Advanced 유지

공개 Student 실패 후보 SHA 7292659a7ea92f25076f4ef605d0dc1e0d1f3c5a. RED [#44114170268](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44114170268) → GREEN [#44114523219](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44114523219) (L0 5/5). 실제 [tracer-ON #44116419349](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44116419349): active TF0.02초 readback PASS였지만 첫 CM RMW source130.015ms, Observer125.158ms, TF111.475ms 안에 110ms sleep; Odom359.798ms/300ms 첫 위반 및 여러 센서 동시 지연으로 L2 FAIL. 같은 후보 [tracer-OFF #44118124163](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44118124163)는 CLEAR→SLOW→STOP·Odom dwell1.004초 성공에도 CM Observer **134.721ms >120ms**, Localization shutdown ACK timeout으로 L2 FAIL. 이 후보는 채택하지 않는다. sim-time과 wall-time 차이의 내부 TF Clock 세부 배율은 미측정이며 원인으로 단정하지 않는다.

### 채택한 후보 B — 공식 Simple TF, 공개 Gazebo만

유일한 파라미터 변경은 Collision Monitor의 base_shift_correction: **true → false**. 오직 PUBLIC GitHub Actions + AXIA_P0_SIM_ONLY=1 + AXIA_G07_CI_SIM_GOAL_ALLOWED=1 + AXIA_G07_OWNER_STARTUP_PARITY=1 + AXIA_G07_TASK02_SIMPLE_TF_CANDIDATE=1을 모두 만족할 때만 적용. 실제 주행 Goal 전 ROS node에서 false를 직접 readback했다.

유지한 값: transform_tolerance **0.2초**, source_timeout **1.0초(양수; invalid source STOP 유지)**, 기존 G07 sim-only stop_pub_timeout 5초, STOP 0.40m, SLOW 0.75m, Slow ratio0.30, Guard TTL0.15초, Scan/Odom/Clock TTL0.3초, 기존 Velocity/Gazebo/Nav2/Goal 구조. 일반 P1/P2와 사용자 Owner WSL2 기본 설정에는 적용하지 않는다.

**시간보정 정확도 위험:** Simple TF는 이동 중 scan timestamp→현재 로봇 자세의 보정을 생략한다. 이번 교육용 저속 Gazebo 1 Goal에서는 실제 LiDAR·CM 구역 행동·odom 정지/주기 검증이 통과했다. 그러나 다른 속도/센서 지연/사람/물리 충돌에 대한 기하·타이밍 오차 상계는 증명하지 않았으며, 물리 로봇 또는 안전 인증용 설정으로 배포할 수 없다.

## 2. 실제 RED→GREEN→REVIEW→COMMIT

| 단계 | 공개 Actions / 증거 | 결과 |
|---|---|---|
| Shell 오류 식별 | #44119294900: 기본 sh가 pipefail 불인식 | CI 실행기 오류, 기능 RED로 계산하지 않음 |
| 실제 Simple TF RED | [#44120024711](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44120024711): 신규 함수 미구현으로 5개 단위 테스트 실패 | RED |
| Simple TF 설정 GREEN | [#44206162519](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44206162519): 5/5 PASS, Bash -n, Python compile PASS | GREEN |
| 엄격한 안전 게이트와 실제 Gazebo | [#44206510291](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44206510291): L0 **10/10 PASS** 후 실제 공식 Jazzy/Harmonic moving Goal 1회 | **Scoped L2 PASS** |

Student 실행 소스 SHA: **f890c580b025dde1038296401aed251d384d98b8** (학생 Draft PR #44, branch fix/g07-task02-simple-tf-sim-ci-20261118). 실제 공개 CI workflow source SHA: **b2f73c5a62ef61c78ea15c8d5d21d183510687a2** (branch fix/g07-task02-simple-tf-public-ci-20261118). 실제 Gazebo job ID **134474375107** 결론 success, ROS/Gazebo runtime parity: 25 packages, 5 official files, CORE_PARITY_PASS. LD_PRELOAD 진단 shim/LTTng 없음.

실제 CI 실행 명령: python3 -m unittest discover -s tools -p test_g07_task02_simple_tf.py -v ; PYTHONPATH="$GITHUB_WORKSPACE/ci" python3 -m unittest discover -s ci/d06/tests -p test_g07_task02_public_strict_gate.py -v ; bash -n scripts/p2_no_goal_smoke_ci.sh ; python3 -m py_compile ros2_ws/src/axia_safety_bringup/launch/axia_p2_launch_policy.py ; python3 tools/p2_g07_owner_env_parity.py --mode ci --output runtime_parity.json ; env -u LD_PRELOAD -u AXIA_G07_TASK01_TF_AVAIL_PROBE timeout --signal=TERM --kill-after=10s 900s bash scripts/p2_no_goal_smoke_ci.sh ; python3 ci/d06/scripts/g07_task02_public_candidate_verdict.py --report .../ci_moving_goal_result.json --events .../actual_ros_events.jsonl --output .../task02_candidate_verdict.json --runner-rc 0.

## 3. 실제 Gazette 단일 Goal과 최초 안전 경계 증거

동일 공개 Run **44206510291**, 실제 GOAL EXECUTING UUID **f961d8d935ec40bc97e0c25547f05b54**:

| 원본 LaserScan/Control 시연 | 실측 |
|---|---|
| CLEAR | front 2.028522m, supervised/CM/final vx 0.037533m/s |
| SLOW | front 0.747276m, supervised0.043840m/s, CM0.013152m/s, final0.011782m/s |
| STOP | front 0.397300m, supervised vx -0.059070m/s, CM vx 0.0, final vx 0.0 |
| 실제 이동/STOP 후 오도메트리 ZERO 유지 | 0.1956m / **1.003059초** |

**RMW source/Observer 실제 연속 발행 seq 520쌍** 검증. CM publisher source 최대 간격 **56.127093ms**, Observer 최대 **67.061350ms**, 각 기준120ms 이내. 첫 source/Observer gap 위반 없음. Guard 안전 래치 **미관찰**, Guard Observer 최대 **66.305557ms**/150ms PASS. Supervisor Observer65.456643ms/150ms PASS, /safety/scan205.521258ms/300ms PASS, /odom152.999363ms/300ms PASS, /clock110.380606ms/300ms PASS. 동일 안전 계층의 실제 주기 검증 범위 내에서 **CM/Guard/sensor TTL 전부 PASS**.

원본 shutdown: Navigation lifecycle ACK true / Localization lifecycle ACK true; CM child 실제 clean exit after ACK PASS, recorder 정상 종료, 원본 runner **rc=0**. 14개 topic bag recorder 실제 시작, 6개 핵심 topic 메시지 count: Guard1907, Clock30672, /cmd_vel_pre_guard674, Supervisor1893, Odom2556, Scan921. 관찰 노드 15초 이상 생존, native crash 없음.

**REVIEW 한계:** Guard 내부 CM age 전체 세션 최대치(다른 계측 지표), 14-topic 전체 raw custody, S02 물리 Contact0 원본, 정확한 최종 Goal UUID terminal status는 본 수치 원장만으로 별도 검증되지 않았다. 이 항목은 Task03 정식 시연 인수에서 확인한다. 실제 sim STOP ≠ 인증 E-Stop.

### 다른 CI 실행과의 비교 한계

Advanced TF timeout0.02 tracer-OFF #44118124163은 CM Observer134.721ms >120ms, localization ACK TIMEOUT. Simple TF tracer-OFF #44206510291은 Observer67.061ms, Nav/Loc ACK와 clean CM exit 모두 PASS. 실행 시점/부하가 다른 **각 1회 표본**이므로 범용 성능 개선률이나 신뢰도 통계로 일반화하지 않는다.

## 4. 공개 Evidence 소유권

- GitHub Actions Run #44206510291, artifact ID **14383539065**, 이름 axia-task02-simple-tf-numeric-44206510291.
- 직접 다운로드한 공개 원본 ZIP 1938 bytes SHA256 **48288dbaf79b3bbbbe4dde54eeff3634bb247faa823243b63919257c40c94ae0**.
- 내부 task02_candidate_verdict.json 707 bytes SHA256 **43fc910b35c1a48eb76bcce7f9be4c2b8403f979e13a17f06a739ef4aacfc7ce**.
- 내부 runtime_parity.json 5652 bytes SHA256 **94c089a022c1266fb4d1909168d0ff571d5f08dbff4fe423737454cde1ca44a7**.
- GitHub 숫자형 파생 원장 d06/evidence/g07_task02/run_44206510291_simple_tf_public_l2.json은 정확한 original ID/SHA를 포함. CI 로그·artifact의 공개 수치형 기록만, 원시 rosbag/TF/PID/TID/개인정보 공개 없음. 원본 ZIP을 실제로 SHA256 검증하였음.

## 5. 파일 경로, 최종 범위, 미검증, main 보호

변경 경로:
- Student: block_B/day07/h01_runtime/ros2_ws/src/axia_safety_bringup/launch/axia_p2_launch_policy.py — 단일 공식 CM sim-only 설정 오버레이.
- Student: block_B/day07/h01_runtime/scripts/p2_no_goal_smoke_ci.sh — Goal 전에 실제 base_shift_correction=false, timeout0.2, source_timeout1.0 readback 필수.
- Student: block_B/day07/h01_runtime/tools/test_g07_task02_simple_tf.py — fail-closed RED→GREEN 5개.
- Public CI: .github/workflows/axia-g07-task02-simple-tf-public-l0-l2-20261118.yml — 공개 소스 pin, 엄격 L0 10개 전제, 실제 Gazebo 1 Goal, 숫자형 artifact.
- Public CI 재사용: d06/diagnostic/g07_task02_strict_gate.py, d06/tests/test_g07_task02_public_strict_gate.py, d06/scripts/g07_task02_public_candidate_verdict.py.
- Public CI 신규: d06/evidence/g07_task02/run_44206510291_simple_tf_public_l2.json 및 본 최종 보고서.

**Task02 완료 정의 충족: 단 하나 공식 Simple TF sim-only 설정, 원본 STOP/SLOW·Guard TTL 보존, 실제 Gazebo CM source/Observer120ms + Guard150ms + Scan/Odom/Clock300ms + CLEAR/SLOW/STOP/odom dwell + Nav/Loc ACK/CM clean exit 검증**. L0 10/10 PASS와 실제 Gazebo L2 수치형 scoped PASS를 구분하여 기록한다.

**Task03 = NOT RUN/FORMAL RELEASE HOLD:** 동일 release SHA에서 별도 S02 Contact0, 14-topic 전수 custody, 정확 Goal terminal, 모든 safety layer 원본 검토 후 판정. **Task04 = OWNER WSL2 GUI L3 NOT RUN**. Task02 성공을 근거로 hardware safety 인증, E-Stop, 제품 출고 PASS를 주장하지 않는다. 학생/공개 CI main 병합 없음.

AXIA_G07_TASK02=COMPLETE_SCOPED_PUBLIC_L2

AXIA_G07_TASK02_SELECTED_CONFIG=BASE_SHIFT_CORRECTION_FALSE_SIM_ONLY

AXIA_G07_TASK02_PUBLIC_L0=PASS_10

AXIA_G07_TASK02_ACTUAL_PUBLIC_GAZEBO_L2=PASS_SCOPED

AXIA_G07_TASK02_CM_RMW_SOURCE_MAX_MS=56.127093

AXIA_G07_TASK02_CM_OBSERVER_MAX_MS=67.061350

AXIA_G07_TASK02_GUARD_MAX_MS=66.305557

AXIA_G07_TASK02_NAV2_NAV_AND_LOCALIZATION_ACK=true

AXIA_G07_TASK02_CM_CHILD_CLEAN_EXIT=true

AXIA_G07_TASK03_FORMAL_RELEASE=NOT_RUN

AXIA_G07_TASK04_OWNER_WSL2_L3=NOT_RUN

CM120_TRACER_OFF_RELEASE=HOLD

AXIA_MVP_DEMO_ACCEPTED=HOLD

CERTIFIED_ESTOP=false

MAIN_MERGED=false
