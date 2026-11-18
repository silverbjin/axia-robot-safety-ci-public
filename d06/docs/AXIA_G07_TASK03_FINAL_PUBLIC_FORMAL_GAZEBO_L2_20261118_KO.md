# AXIA G07 — Task 03 최종 개발·검증 보고서

**판정일:** 2026-11-18 KST  
**Task03 최종:** `COMPLETE_PUBLIC_FORMAL_L2_SCOPED`  
**전체 MVP 최종:** `AXIA_MVP_DEMO_ACCEPTED=HOLD`

## 1. 검증 기준과 출처

공개 GitHub Actions [Run #44215546368](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44215546368) / Job `134504345226` **completed/success**. 공식 ROS 2 Jazzy, Gazebo Harmonic, Nav2, TurtleBot3 Waffle을 사용하였다. TF tracer/LTTng/LD_PRELOAD 진단 shim 없이 **실제 Gazebo 움직이는 Goal 1회**를 수행했다.

- Public CI 실행 원본 SHA: `c996a5f415ca90e9dac99d798944a56d6b70d8be` (브랜치 `fix/g07-task03-formal-public-l2-20261118`).
- Student 실행 소스 SHA: `b53a5128cd7165f6465f2916b4c4554f9663798d` (브랜치 `fix/g07-task03-public-proof-20261118`).
- 공개 학생 Draft PR [#46](https://github.com/silverbjin/axia-robot-safety-student/pull/46), 공개 CI Draft PR [#168](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/168). Main 병합 없음.
- Task02의 성공한 공식 CM Simple TF 시뮬레이션 전용 변경을 그대로 재사용. `base_shift_correction=false`는 오직 이 공개 교육용 단일 시나리오의 검증 결과다. CM120, Guard150, Scan/Odom/Clock300ms, CM source_timeout=1.0s, STOP0.40m/SLOW0.75m 정책은 **수정·완화하지 않았다**.

## 2. 원인 기반 최소 수정

Task02 성공 이후 실제 인수에서 네 가지 미검증 경계가 있었다: (a) S02 Contact 이벤트 침묵만으로는 충돌 0건이라고 할 수 없음, (b) 원본 rosbag 14토픽 기록 여부와 달리 기존 종료 검증은 6개만 검사, (c) Goal EXECUTING만으로 정확 UUID의 최종 CANCELED 확인 불가, (d) 독립 CM Observer 주기가 실제 Guard 내부 CM age와 다름.

최소 구현은 기존 ROS/안전동작을 바꾸지 않고 증거를 읽도록 했다.

1. `tools/native_s02_public/{CMakeLists.txt,s02_witness.cc}`: Gazebo Harmonic의 실제 `ContactSensorData`를 읽는 read-only PostUpdate plugin. 공식 [Gazebo Sim8 Contact.cc](https://github.com/gazebosim/gz-sim/blob/gz-sim8/src/systems/contact/Contact.cc)에서 실제 컴포넌트가 센서 엔티티가 아닌 **obstacle_collision 충돌 엔티티**에 부착됨을 확인했다. 같은 C++ 바이너리로 폐기할 **NO_GOAL 실제 양성 접촉 검증**과 독립 실제 주행 월드의 연속 물리계측을 수행한다.
2. `tools/{p2_g07_task03_ecm_positive.py,p2_g07_task03_calibration_cleanup.py}`, `tools/p2_l3_world_overlay.py`, `scripts/p2_no_goal_smoke_ci.sh`: 별도 ROS_DOMAIN_ID/GZ_PARTITION을 사용한 양성 접촉 월드를 종료·폐기하고, native 접촉 양성+정상 teardown+남은 프로세스 0일 때만 다음 Goal 허용. 일시적인 **NO_GOAL disposable Localization ACK timeout**은 그 월드에서만 접촉 센서 교정 증거로 유지할 수 있지만 **Moving Goal L2에서는 Navigation·Localization ACK/CM clean exit 전부 필수**.
3. `tools/p2_g07_ci_moving_goal.py`: 실제 STOP 및 odom ZERO 1초 확인 후, 정확 발행 UUID만 native Nav2 CancelGoal로 취소하고 원본 ROS ActionStatus **5=CANCELED** 확인.
4. `ros2_ws/src/axia_safety_supervisor/axia_safety_supervisor/p2_base_guard_node.py`: 원래 Guard 상태 토픽에 공개 sim-only `cm_age_sec`, `supervisor_age_sec`, `guard_ever_moved`를 read-only로 부가한다. 150ms watchdog이나 SW STOP/Velocity 명령은 수정하지 않는다.
5. `tools/{p2_g07_task03_contract.py,p2_g07_task03_review.py,test_g07_task03_formal_evidence.py,test_g07_task03_calibration_cleanup.py}`: fail-closed SQL14·ECM·Guard 내부 age·정확 UUID 판정. 기존 `d06/diagnostic/g07_task02_strict_gate.py`의 RMW source/Observer 120ms 검사 재사용.

**실패 최초 원인 분리:** 최초 실제 [#44212258824](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44212258824)에서 Guard 내부 최대 age **30,128.738ms**가 보고됐지만 Guard 래치 없음과 실제 CM publisher 정상 주기와 모순됐다. 원래 Guard 정책은 **최초로 비영 명령을 실제 전달하기 이전** `NO_FRESH_PAIR`일 때 ZERO 유지, 이후 `ever_moved=true`일 때 150ms stale latch이다. 새 진단은 Guard 자신의 동일 타이머 시각에서 `ever_moved` 최초 전이를 직접 읽어 **전송 전 긴 idle age를 별도 집계**한다. **전송 후 age 150ms 초과/누락/상태 역행은 그대로 FAIL**. 타이밍 정책 변경 없음.

## 3. RED→GREEN→REFACTOR→REVIEW→COMMIT

| 단계 | GitHub Actions 원본 | 실제 결과 |
|---|---|---|
| Task03 계약 RED | [#44210394942](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44210394942) | 필수 검증 모듈 부재 실패 |
| Task03 최초 GREEN | [#44211063396](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44211063396) | 신규 4/4 PASS |
| Contact ECM 원본 실패 | [#44211658321](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44211658321) | 충돌 엔티티 불일치로 보고서 미생성, Goal 전 BLOCK |
| 실제 1회 Guard age HOLD | [#44212258824](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44212258824) | Contact0/SQLite14/UUID PASS, Guard age 혼합 판정으로 HOLD |
| Guard pre-motion RED→GREEN | [RED #44213426629](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44213426629), [GREEN #44213715360](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44213715360) | 실제 첫 이동 전·후 구분 및 이동 후 엄격한 TTL 유지 6/6 PASS |
| Disposable Contact cleanup RED→GREEN | [RED #44214758294](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44214758294), [GREEN #44215229445](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44215229445) | NO_GOAL 폐기 범위, 강제 종료/누수/잘못된 RC 차단 3/3 PASS |
| 최종 공개 CI | **[#44215546368](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44215546368)** | **L0 19/19 PASS + 실제 Gazebo L2 FORMAL EVIDENCE PASS SCOPED** |

최종 19개 L0: Task03 본 계약 6, Contact calibration cleanup 3, Task02 공식 Simple TF 불변조건 5, Task02 RMW/센서 엄격 판정기 5. 추가로 Python compile, Bash -n, 실제 ROS 2 Jazzy 공식 런타임 25 package/5 official files parity, native C++ plugin 컴파일을 검증했다.

## 4. 동일 Gazebo 1회 실제 계측

**Goal UUID: `d5e8b10633f04f74a24186022082aaab` — 실제 Nav2 ActionStatus=5 CANCELED.**

| 검증 항목 | 실제 결과 | 인수 기준 |
|---|---:|---|
| NO_GOAL native Contact 양성 | 21,692 physics step, **5,346 contacts** | sensor 동작 양성 검증 |
| 실제 Moving Goal Contact | **0 contacts**, 22,724 native physics step, missing 0 | 같은 바이너리/주행 구간 연속 감시 PASS |
| 움직임 Contact window | sim ns 38,730,000,000→59,121,000,000 | 실제 Goal/STOP 구간 포함 |
| CLEAR LaserScan front | **2.044095m** | 실제 LiDAR |
| SLOW front, Supervisor→CM | **0.740520m, 0.035777→0.010733m/s** | 실제 약 30% 감속 |
| STOP front, Supervisor→CM/final | **0.392077m, -0.027735→0.0/0.0m/s** | 실제 STOP |
| CM 실제 RMW publisher source max | **52.513109ms**, 412 연속 seq 쌍 | 120ms 이내 |
| CM Observer callback max | **67.913195ms** | 120ms 이내 |
| Guard 내부 CM receive age max | **49.872948ms**, 처음 움직임 이후 408 samples | 150ms 이내 |
| Guard interarrival max | **68.885180ms** | 150ms 이내 |
| Supervisor max | **68.887702ms** | 150ms 이내 |
| Scan max | **196.175694ms** | 300ms 이내 |
| Odom max | **132.075874ms** | 300ms 이내 |
| Clock max | **103.167687ms** | 300ms 이내 |
| Goal terminal | **정확 UUID CANCELED** | native ACK + status 5 |
| Nav2/CM 종료 | **Navigation ACK, Localization ACK, CM exit clean** | 모두 필수 |
| 원본 실행기 | **rc=0** | PASS |

**최초 위반:** `first_failure=NONE`, Guard stale latch 관찰되지 않음. 이 결과는 **S02 장애물 ContactSensorData의 접촉 0건**이지 Gazebo 전 세계 모든 충돌에 대한 인증이 아니다.

### 실제 rosbag SQLite 14개 토픽 전수

같은 Goal Job에서 SQLite3 **read-only** `pragma quick_check=ok`, 실제 count >0, 원본 .db3 SHA256 및 metadata SHA256 계산을 확인했다.

| 토픽 | 실제 메시지 |
|---|---:|
| `/clock` | 22659 |
| `/tf` | 3364 |
| `/tf_static` | 1 |
| `/map` | 1 |
| `/scan` | 680 |
| `/safety/scan` | 675 |
| `/odom` | 1888 |
| `/cmd_vel_smoothed` | 428 |
| `/cmd_vel_supervised` | 1359 |
| `/cmd_vel_pre_guard` | 537 |
| `/cmd_vel` | 1409 |
| `/axia/safety/state` | 1359 |
| `/axia/p2/base_guard` | 1409 |
| `/navigate_to_pose/_action/status` | 3 |

- SQLite3 원본 SHA256: `b1975aa6e5dd55e599e60442a30ad01c656d4a72e960e3fe60c3c583110ff4d0`.
- metadata 원본 SHA256: `839362bfb174f3c0fe4c4174733985cacc426bd12e725e2a942e7eebb15a2bcd`.
- **한계:** 원본 .db3는 공개 아티팩트로 게시하지 않았다. 원본은 실제 CI 내에서 전수 조회·해시 계산했지만, 독립 오프라인 rosbag 복원·재생은 **미검증**이다. 공개 원장은 counts, SHA256, 판정 상태만 보존한다.

## 5. 증거 해시·실행기·미검증

- GitHub 원본 **Run #44215546368, Job #134504345226**, artifact ID **14387738909**, 이름 `axia-task03-formal-public-numeric-44215546368`.
- 원본 ZIP **3449 bytes**, SHA256 `a0cb7e7a4c961c321e0f9c32fc0854e93b5b9137e72da5d21d9052a17d109cbe` — 직접 다운로드 확인.
- `public_evidence/task03_formal_verdict.json` SHA256 `c02a77d45a72f771e7505f0798014c528c49fbe9d4ea77c6884265cb2ca28b86`.
- `public_evidence/task03_positive_calibration.json` SHA256 `ef33d89b2c4a9c06f412c73a4d555fe5ae731af3399ecebcd6eabf5e60494bc6`.
- `task03_runtime_parity.json` SHA256 `94c089a022c1266fb4d1909168d0ff571d5f08dbff4fe423737454cde1ca44a7`.
- `task03_witness_SHA256SUMS.txt` SHA256 `d50170999fba36fab6e49f96d785f7cedfbe23ce53d906c5bda7617664682310`.
- GitHub 영구 파생 원장: `d06/evidence/g07_task03/run_44215546368_formal_public_l2.json`.

**주요 공개 CI 명령** (실제 GitHub Actions만 실행, 로컬 Owner Goal 아님):

~~~bash
python3 -m unittest discover -s tools -p test_g07_task03_formal_evidence.py -v
python3 -m unittest discover -s tools -p test_g07_task03_calibration_cleanup.py -v
python3 -m unittest discover -s tools -p test_g07_task02_simple_tf.py -v
python3 -m unittest discover -s ci/d06/tests -p test_g07_task02_public_strict_gate.py -v
cmake -S tools/native_s02_public -B task03-native-build -DCMAKE_BUILD_TYPE=Release
cmake --build task03-native-build --parallel 2
# NO_GOAL 별도 disposable world: positive contact -> clean process gate
# 실제 ONE Goal 새 Domain/Partition, tracer OFF:
env -u LD_PRELOAD -u AXIA_G07_TASK01_TF_AVAIL_PROBE timeout --signal=TERM --kill-after=10s 900s bash scripts/p2_no_goal_smoke_ci.sh
# 같은 run 원본 수치형 통합검사: tools/p2_g07_task03_review.py
~~~

**REVIEW 및 미검증 항목:** 고속 주행·실물 센서/물리 안전 인증·전체 월드 모든 충돌·인증된 E-Stop은 범위 밖. **Task04 Owner WSL2 GUI(RViz2+Gazebo) L3는 아직 실행하지 않았다.** 공개 CI 한 실행의 PASS를 WSLg scheduler 및 현장 실제 시연 전체 PASS로 승격하지 않는다. 일반 경로에서 Simple TF 시각 보정 상실의 상한은 입증되지 않았다. 공개 학생/CI **main은 병합하지 않았다**. 비공개 Instructor 및 비공개 CI를 호출하지 않았다.

~~~text
AXIA_G07_TASK03=COMPLETE_PUBLIC_FORMAL_L2_SCOPED
AXIA_G07_TASK03_PUBLIC_L0=PASS_19_OF_19
AXIA_G07_TASK03_REAL_GAZEBO_L2=PASS_SCOPED
AXIA_G07_TASK03_S02_CONTACT0=true
AXIA_G07_TASK03_CM_RMW_SOURCE_MAX_MS=52.513109
AXIA_G07_TASK03_CM_OBSERVER_MAX_MS=67.913195
AXIA_G07_TASK03_GUARD_INTERNAL_CM_AGE_MAX_MS=49.872948
AXIA_G07_TASK03_SQLITE14_ACTUAL_COUNTS_SHA256=PASS
AXIA_G07_TASK03_EXACT_NAV2_GOAL_TERMINAL=CANCELED
AXIA_G07_TASK03_NAV2_NAV_LOCAL_ACK=true
AXIA_G07_TASK03_CM_CLEAN_EXIT=true
AXIA_G07_TASK03_FIRST_FAILURE=NONE
CM120_TRACER_OFF_RELEASE=PASS_PUBLIC_L2_SCOPED
AXIA_G07_TASK04_OWNER_WSL2_L3=NOT_RUN
AXIA_MVP_DEMO_ACCEPTED=HOLD
CERTIFIED_ESTOP=false
MAIN_MERGED=false
~~~