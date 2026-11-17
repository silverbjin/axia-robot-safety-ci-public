# AXIA G07 — Task01 Cycle05: 첫 CM source gap의 TF 가용성 read-only 판별 계약

**작성: 2026-11-17 KST | 공개 CI `silverbjin/axia-robot-safety-ci-public` | 브랜치 `fix/g07-cm120-task01-clock-firstgap-causality-20261117` | Draft PR #161 | 결론 HOLD**

> 이 보고서는 단일 원인의 증명을 위한 기존 공식 Nav2 TF Buffer **읽기 전용 진단**만 다룬다. 일반적 Nav2 개발 확장, 새 ROS 노드, kernel tunings, base-shift/TTL/STOP 변경, 시연 릴리스 PASS가 아니다.

## 1. 실제 최초 안전/타이밍 위반 및 최근 인계

- [실제 G07 진단 Goal #44049067368](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44049067368): CM publisher RMW 첫 gap **129.299071ms** (>120ms), 별도 Observer **128.391951ms** (>120ms), Advanced TF 함수 최대 약 **91.733ms**, 동일 첫 Observer 창의 libc 10ms sleep **9회 / 요청90.000ms / 실측91.416406ms**. 이는 TF 함수 내 자발적 폴링의 강한 증거이나, 왜 TF를 기다렸는지·source SYSTEM 대 MONOTONIC causal alignment는 증명하지 못함.
- [이후 Moving Goal #44059005075](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44059005075): 공식 Goal CLEAR→SLOW→STOP, exact UUID cancel, Nav/Localization ACK, CM exit0 등은 개별 단계 PASS이나 **첫 source>120ms 위반이 재현되지 않아 전체 진단 workflow FAIL**. 실제 RMW source 최대117.210ms, Observer117.861ms (tracer ON). 이 실행으로 과거 129.299ms 원인을 역산하지 않는다.
- [진단 NO_GOAL #44066540314](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44066540314): 원본 공식 CM Advanced TF 호출447, libc sleep402, native Navigation/Localization ACK=true, private NO_GOAL runner rc0. 그러나 `rcl_clock_get_now`/Clock hooking event **0건**, 공개 전체 FAIL. 시계가 정지했다는 근거가 아니라 실제 동적 binding 미관찰.
- 다음 [공식 TF2 Buffer cross-DSO 순수 Jazzy ABI #44067225025](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44067225025) PASS. L0의 인위적 selftest 통과와 실제 CM binding을 혼동하지 않는다.

## 2. 공식 근거 및 가설

- [Nav2 Jazzy Collision Monitor source.cpp](https://github.com/ros-navigation/navigation2/blob/jazzy/nav2_collision_monitor/src/source.cpp): `base_shift_correction=true`에서 advanced fixed-frame transform.
- [Nav2 Jazzy robot_utils.cpp](https://github.com/ros-navigation/navigation2/blob/jazzy/nav2_util/src/robot_utils.cpp): 입력 source/target timestamp와 fixed frame, tolerance로 `tf_buffer->lookupTransform(...)`.
- [ROS2 geometry2 Jazzy buffer.cpp](https://github.com/ros2/geometry2/blob/jazzy/tf2_ros/src/buffer.cpp): `lookupTransform`→`canTransform`, 실제 변환이 아직 없을 때 반복 `canTransform(..., timeout=0)` 과 `std::this_thread::sleep_for(10ms)`. 기존 목적은 fixed-frame TF 가용성을 기다리는 것.
- [공식 Nav2 Issue #3402](https://github.com/ros-navigation/navigation2/issues/3402)와 병합된 [PR #3412](https://github.com/ros-navigation/navigation2/pull/3412): Advanced TF는 더 정확한 시공간 보정을 제공하지만 성능 부담. 단순 TF로 바꾸면 안전 좌표 보정 정확도 손실 가능. **이번에는 변경 금지**.

**하나의 반증 가능한 가설:** 같은 공식 CM Advanced TF 호출 **직전** nonblocking `canTransform(..., timeout=0)` 결과가 false이고, **직후** true이며, 그 *원본 TF 내부* libc sleep이 10ms 주기로 반복된다면, 적어도 TF 함수가 기다린 시간은 호출 시작 당시 TF 가용성 부족과 정합하는 후보가 된다. 첫 CM RMW source gap의 시계영역 정합이나 내부 ROS Clock 진행, kernel runnable queue를 증명하는 것은 **아니다**. 반대로 직전에 true이면 TF 가용성 단독 가설을 보류한다.

## 3. RED → GREEN: 정확한 원본 TF 시간 분리 및 fail-closed

**신규 파일**
- `d06/tests/test_g07_task01_tf_zero_timeout_availability.py` — 7 tests: 실제 legacy first-gap artifact는 가용성 원시 증거가 없어 HOLD, false→true는 후보, 잘못된 PID/TID 제외, 호출 경계 횡단·중복 검사 HOLD, 시작 true인 경우 TF wait 미입증, 두 probe overhead는 official TF wall에 포함하지 않음
- `d06/diagnostic/classify_tf_availability.py` — 원인 추측과 시연 PASS를 금지한 최소 진단 결과 분류
- `d06/diagnostic/analyze_first_cm_tf.py`와 `export_public_cm120_first_gap.py` — 동일 CM PID/TID와 원본 TF call 시간창을 검증한 `TF_AVAIL` raw 행만 숫자형 공개 allowlist로 보존; raw frame/pose/PID/TID/TF geometry/비공개 강사 코드 제외
- `d06/diagnostic/cm_tf_gettransform_preload.cpp` — **CI 전용** `AXIA_G07_TASK01_TF_AVAIL_PROBE=1`에서만 같은 공식 TF Buffer의 `canTransform(..., timeout=0)`을 원본 호출 직전·직후 읽음. *두 추가 쿼리 시간을 원본 official TF_ADV wall 계측에서 분리*. 기존 official `getTransform`은 RTLD_NEXT로 원형 그대로 호출
- 기존 `.github/workflows/axia-g07-task01-real-firstgap-polling-bounds-l0-20261117.yml` 및 `axia-g07-task01-jazzy-abi-sleep-bracket-l0-20261117.yml`에 새 7 테스트 및 정식 Jazzy C++ API selftest 편입

**증거**
- [초기 L0 RED #44071552792](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44071552792): 신규 검사기/가용성 필드가 아직 없어 회귀 실패
- [L0 GREEN #44071779545](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44071779545), tested code SHA `96310825354908dd4300c48cf176b60763b025a3`: 실제 고정 SHA 증거 회귀5+2, 호출경계6, 신규 TF 가용성7, 내부 clock6, 공개 프라이버시5, 원시 누락 방어3 = **34/34 PASS**. ROS 미실행 L0
- [실제 Jazzy C++ ABI GREEN #44072012680](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44072012680), code SHA `5a067af927a06be6d08d62994fcb578d8a571404`: 정식 GCC/CMake, 원본 Nav2 ABI, 실제 sleep_for, Clock C/C++/cross-DSO, 신규 **Buffer zero-timeout nonblocking lookup** 모두 PASS. 별도 Python 6+3+4, **실제 Jazzy 환경, NO_GOAL/L0, Gazebo 미실행**.
- 공개 release-lane NO_GOAL 실제 Gazebo 신규 workflow `.github/workflows/axia-g07-task01-tf-zero-timeout-nogoal-l2-20261117.yml`, SHA `ee0cdd74c32b71ca5de53c6b0b1d33313c479306`, public diagnostic SHA `5a067af...`와 original private Instructor SHA `966886c4627deb2bb3b37111fe336eeee6b9ebb4` 고정. `AXIA_G07_CI_SIM_GOAL_ALLOWED=0`, `TF_AVAIL_PROBE=1`, Native Shutdown ACK/CM mapping/extra probe overhead ≤20ms 모두 필수. [실제 Run #44072394317](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44072394317) **실행 결과 별도 확인 필요 — 이 문서 생성 시 PASS 주장 금지**.

## 4. 안전/개인정보 REVIEW

- 모든 추가 조회는 **동일 공식 `tf2_ros::Buffer`의 읽기 전용 `canTransform(... timeout=0)`**. 조회 자체가 CM callback 스케줄에 미치는 영향은 zero 아님: ms 단위 overhead를 실제 측정하고, >20ms면 진단 준비 자체 HOLD.
- 신규 TF 가용성 단독으로 120ms source latency 원인이나 Guard age 150ms, Scan/Odom/Clock 300ms, 실제 SW STOP/odom/contact/Goal 결론은 판정하지 않음. 실제 성공 주행이 아닌 진단기의 green.
- 기존 `base_shift_correction=true`, `source_timeout=1.0s`, tolerance `0.02s`, STOP `0.40m`, SLOW `0.75m`, 기존 Guard TTL 150ms/센서 TTL 300ms **변경 없음**. **SW 정지는 인증된 물리적 E-Stop이 아님**.
- 공개 CI는 private Instructor 코드를 세션 안에서만 읽고, raw 로그/비공개 원본을 공개 artifact에 업로드하지 않음. 정제된 숫자 필드에는 PID/TID, frame, pose, 원문 ROS 메시지 불포함. 학생용 독립 저장소 및 main 미변경.

## 5. 다음 유일 단계 및 릴리스 상태

1. 공개 실제 NO_GOAL [#44072394317](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44072394317) 완료/FAIL 경계와 **공식 CM 변환 전·후 가용성, 실제 probe overhead, Native Navigation/Localization ACK** 확인. 실패 시 첫 경계를 기존 Python L0/Jazzy ABI로 축소, 같은 설정으로 Gazebo 반복 금지.
2. NO_GOAL 전체 GREEN 이후에만 원본 공식 **single Moving diagnostic Goal 1회**를 검토할 수 있다. 이때 새 관측은 최초 **같은** source>120ms와 TF call/sleep/probe/Clock/scheduler 검증 범위에서만 인정. 이번 NO_GOAL만으로 TF source causality는 미입증.
3. 정확히 원인이 입증되지 않으면 Task02 성능 조정 금지. Task03 tracer-OFF 공개 실제 L2와 Task04 Owner WSL2 L3는 계속 NOT RUN. Owner 승인·원본 SHA가 없는 Goal/최종 ACCEPTED/사용자 main 병합 모두 금지.

```text
AXIA_G07_TASK01_ZERO_TIMEOUT_TF_READINESS_PY_L0=PASS_34
AXIA_G07_TASK01_REAL_JAZZY_TF_BUFFER_ZERO_TIMEOUT_ABI_L0=PASS_44072012680
AXIA_G07_TASK01_REAL_GAZEBO_NO_GOAL_PROBE=VERIFY_RUN_44072394317
AXIA_G07_TASK01_FIRST_SOURCE_GAP_ROOT_CAUSE=UNPROVEN
AXIA_G07_TASK02=BLOCKED_CAUSE_UNPROVEN
AXIA_G07_TASK03_TRACER_OFF=NOT_RUN
AXIA_G07_TASK04_OWNER_WSL2_L3=NOT_RUN
CM120_TRACER_OFF_RELEASE=HOLD
AXIA_MVP_DEMO_ACCEPTED=HOLD
MAIN_MERGED=false
CERTIFIED_ESTOP=false
```

## 6. 실제 Gazebo L2 NO_GOAL verdict 및 단일 신규 Moving 진단

- [공개 official Gazebo/Harmonic NO_GOAL L2 Run #44072394317](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44072394317): workflow SHA `ee0cdd74c32b71ca5de53c6b0b1d33313c479306`, public diagnostic source pin `5a067af927a06be6d08d62994fcb578d8a571404`, private original Instructor SHA `966886c4627deb2bb3b37111fe336eeee6b9ebb4`. **completed/success**.
- 실제 stdout:

```text
AXIA_G07_TASK01_NO_GOAL_REAL_TF_AVAILABILITY {"exact_same_call_availability_rows":589,"goal_sent":false,"initial_unavailable_later_available_count":478,"max_nonblocking_probe_elapsed_ms":0.460882,"official_tf_calls":589,"release_pass":false,"root_cause_proven":false,"same_first_moving_source_gap":false,"scheduler_runqueue_proven":false,"total_availability_rows":589}
AXIA_G07_TASK01_ORIGINAL_CM_TF_ZERO_TIMEOUT_READBACK_PASS_NO_GOAL
AXIA_G07_S2_REAL_NO_GOAL_CM_TF_READINESS {"actual_tf_call_count":589,"goal_sent":false,"localization_shutdown_status":"NAV2_LIFECYCLE_SHUTDOWN_ACK","navigation_ack":true,"localization_ack":true,"runner_rc":0,"tf_nanosleep_calls_total":511,"tf_actual_sleep_wall_ms_total":5175.867731,"root_cause_proven":false,"release_pass":false}
```

- **검증된 사실:** 실제 공식 CM의 동일 source/target/time/fixed-frame TF 요청의 nonblocking 0ms 가용성이 589 호출에 대해 원본 Advanced TF 직전·직후에 검증됐으며, 그 중 478회에서 **처음 false→끝 true**. 추가 probe 최대 오버헤드 0.461ms. 기존 native shutdown ACK 및 NO_GOAL 준비 절차도 모두 통과했다.
- **아직 미증명:** 최초 *Moving* publisher RMW source>120ms와 정확한 동일 TF 호출/비차단 가용성의 인과, TF Buffer 내부 Clock 진행량, kernel runnable latency, Guard/센서 타이밍의 다른 계층. NO_GOAL 성공으로 Task02 변경 권한을 부여할 수 없다.
- **사용자 승인 범위 내 새로운 증거 목적의 딱 한 번 Moving 진단**: 공개 릴리스 lane `.github/workflows/axia-g07-task01-tf-availability-one-goal-l2-20261117.yml` commit `c3f50090350ac0084bced778d0df2d72c08e663c`의 [Run #44073078458](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44073078458). 기존 original one Goal / same private source / existing lifecycle·bag·contact·timing evidence를 재사용하며 **추가 옵션은 read-only `AXIA_G07_TASK01_TF_AVAIL_PROBE=1`**, 새로운 0ms TF 읽기만 한다. 첫 RMW source gap이 나타나면 동일 TF call 전후 availability와 TF sleep을 공개 sanitized JSON의 숫자만으로 연결하고 SHA256 보존. 원본 Instructor/raw trace를 공개하지 않음. 첫 gap이 미재현이면 그 자체를 HOLD로 보존; 동일 코드로 추가 Goal 반복 금지.
- 본 보고서 작성 시 이 Moving 진단은 **PENDING**. PASS, 원인 제거, tracer-OFF release, Owner L3 인수로 승격하지 않음.

```text
AXIA_G07_TASK01_REAL_NO_GOAL_TF_AVAILABILITY=PASS_44072394317
AXIA_G07_TASK01_NO_GOAL_TF_ENTRY_FALSE_EXIT_TRUE_COUNT=478
AXIA_G07_TASK01_REAL_SINGLE_MOVING_FIRST_GAP=VERIFY_RUN_44073078458
AXIA_G07_TASK01_ROOT_CAUSE=UNPROVEN
AXIA_G07_TASK02=BLOCKED
AXIA_G07_TASK03_TRACER_OFF=NOT_RUN
AXIA_G07_TASK04_OWNER_WSL2=NOT_RUN
AXIA_MVP_DEMO_ACCEPTED=HOLD
MAIN_MERGED=false
CERTIFIED_ESTOP=false
```
