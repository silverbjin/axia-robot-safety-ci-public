# AXIA G07 CM120 — Task01 Cycle04: 최초 CM 지연의 동일 TF 호출·내부 ROS Clock 인과 검증 계약

**2026-11-17 KST | 공개 개발 브랜치 `fix/g07-cm120-task01-clock-firstgap-causality-20261117` | Draft PR #161 | Task01 L0만 신규 검증 / Task02~04 및 원인 규명 HOLD**

## 1. 기준선과 최초 지연

- 원본 실제 공식 Gazebo/Harmonic, Nav2/Jazzy 단일 진단 Goal [Run #44049067368](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44049067368): **전체 L2 FAIL**, 첫 RMW CM publisher source 129.299071ms, 동일 Observer receive 128.391951ms, Advanced TF 함수 실행 약 91.753ms, 실제 10ms libc sleep 9회/총 91.416406ms. 원시 trace는 원본 job cleanup으로 소실되어 공개 **숫자형 허용목록 JSON**만 남았다.
- 그 실행에서 동일 TF invocation 시작·종료값과 **TF Buffer 내부 ROS Clock 값**은 공개 증거에서 누락. 원본 S1/S2를 서로 다른 실행으로 합치지 않는다.
- 새로운 동시 /clock sidecar가 있는 실제 [Run #44059005075](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44059005075): 주행/정지/Native ACK/CM exit0 개별 동적 단계는 통과했으나 **120ms 첫 CM source breach 미재현** (실제 RMW publisher 최대117.210ms, CM Observer 최대117.861ms). C05 최초 breach 분석기는 실패, workflow **completed/failure**, `root_cause_proven=false`, 전체 tracer-ON 진단 **HOLD**. 이 성공 주행을 tracer-OFF 릴리스 PASS로 승격하지 않는다.
- 원본 수치 및 SHA256: `d06/evidence/g07_cm120_task01/run_44049067368_first_gap_sanitized.json`, `run_44049067368_SHA256SUMS.txt`, `run_44059005075_first_gap_sanitized.json`, `run_44059005075_SHA256SUMS.txt`. 두 원본 모두 GitHub public-only timing artifact에서 불변 bytes를 저장했다.
- 기존 [PR #161](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/161)에서 계속 개발한다. 새로운 병렬 서브 브랜치/새 서비스 노드/공식 Nav2 fork는 만들지 않는다.

## 2. 공식 Jazzy 코드 기반 원인 후보와 반증 방법

| 공식 정확한 경로 | 공식 근거 | AXIA에서 확인된 것 | 아직 미입증 |
|---|---|---|---|
| CollisionMonitor→Source advanced | [Nav2 Jazzy collision_monitor_node.cpp](https://github.com/ros-navigation/navigation2/blob/jazzy/nav2_collision_monitor/src/collision_monitor_node.cpp), [source.cpp](https://github.com/ros-navigation/navigation2/blob/jazzy/nav2_collision_monitor/src/source.cpp) | `base_shift_correction=true`, official CM TF 함수 wall≈91.753ms | 정확한 source event→native CM TF 내부의 causal source timestamp alignment |
| `nav2_util::getTransform` | [Jazzy robot_utils.cpp](https://github.com/ros-navigation/navigation2/blob/jazzy/nav2_util/src/robot_utils.cpp) | advanced fixed-frame overload와 실제 C++ ABI interposition 기존 L0 확인 | 내부 request마다 변환 가용성 false/true 전이 |
| `tf2_ros::Buffer::canTransform` | [ROS geometry2 Jazzy buffer.cpp](https://github.com/ros2/geometry2/blob/jazzy/tf2_ros/src/buffer.cpp) | timeout 판정은 `clock_->now()`, 폴링은 실제 `std::this_thread::sleep_for(10ms)`. 첫 observer window에 9회 sleep이 있었음 | 변환 요청 timeout의 **실측** ns, 내부 시계 progression, 실제 변환 availability |
| `rclcpp::Clock::now` → `rcl_clock_get_now` | [ROS2 rclcpp Jazzy clock.cpp](https://github.com/ros2/rclcpp/blob/jazzy/rclcpp/src/rclcpp/clock.cpp), [rcl time.h](https://github.com/ros2/rcl/blob/jazzy/rcl/include/rcl/time.h) | C ABI 후킹 후보 확인 | 해당 CM advanced TF 내부 실제 `RCL_ROS_TIME`와 override 활성 상태/각 반복의 ROS Clock ns |
| kernel Scheduler | [Linux schedstats](https://www.kernel.org/doc/html/latest/scheduler/sched-stats.html) | `sched_schedstats=0`이던 기존 CI에서 runqueue latency는 수집되지 않음 | runnable wait ns, wakeup 동작. UNAVAILABLE를 0으로 처리 금지 |

**중요한 해석:** TF 함수 91.7ms 중 공식 10ms sleep 요청이 최소90ms라면, 같은 단일 호출임이 검증된 경우 그 호출 시간의 **대부분이 실제 폴링 요청**이었다고 할 수 있다. 단, sleep과 주행 최초 source gap 사이의 SYS↔MONO 정합, TF Buffer 내부 Clock 활성 상태 및 canTransform availability가 없으면 **최종 근본 원인/안전 수정 승인**은 불가능하다.

## 3. 동일 Advanced TF call 경계 누락을 보완하는 최소 RED→GREEN

- 추가한 테스트: `d06/tests/test_g07_task01_tf_call_exact_sleep_budget.py` 6개. 실제 440490 이전 공개 숫자에는 시작/종료가 없어 **`EXACT_TF_CALL_INTERVALS_NOT_PRESERVED_HOLD`**로 처리한다. 기존 데이터에 가짜 값을 추가해 PASS로 고치지 않았다.
- 추가한 순수 검사기: `d06/diagnostic/classify_exact_tf_sleep_budget.py`.
- 공개 출력기 `d06/diagnostic/export_public_cm120_first_gap.py`는 공식 CM PID/TID를 sealed runner **메모리에서만** 검증하고 TF 함수 시작·종료 **상대 ns**, sleep 요청·실측 ns, CPU ns와 per-call sleep 횟수만 보존한다. PID/TID, ROS frame, pose, TF geometry, 메모리 주소, 비공개 Instructor 코드는 공개 출력에 포함하지 않는다.
- 검증 흐름: 공개 CI RED [#44062265603](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44062265603) (검사기 import 불가) 및 [#44062419823](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44062419823) (새 per-call interval 미보존) → 코드/구문 정리 → [GREEN #44062678469](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44062678469) **13/13 PASS**.
- 실제 clock first-window 및 기존 exporter 호환 [GREEN #44062678415](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44062678415) **9/9 PASS**.
- 내부 clock 추가 전날? 누적된 공개 allowlist+원본 SHA/negative tests [GREEN #44063650766](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44063650766): 기존 5+2 + exact call6 + internal clock6 + privacy5 + raw missing3 = **27/27 PASS**. 이 검증은 ROS/Gazebo 미실행 **L0**.

## 4. 최소 내부 Clock 계측 후보 — 실제 ABI GREEN 필수

새로운 기능이나 ROS 노드 대신, 기존 CI 전용 `d06/diagnostic/cm_tf_gettransform_preload.cpp`에 **`rcl_clock_get_now` C ABI read-only interposition**을 추가한다. 원본 공식 `RTLD_NEXT` 호출을 원형 그대로 위임하며, **이미 진단 중인 같은 원본 공식 CM Advanced TF 함수의 thread-local 활성 구간에서만** 다음 정보를 제한된 개수로 기록:
- `TF_CLOCK pid/tid mono_ns ros_ns clock_type override_active`: private raw 메모리/runner 로그에만 존재. 정제 exporter는 실제 CM PID/TID·해당 Advanced TF 호출 시간 구간을 확인한 뒤 상대 MONOTONIC ns와 상대 ROS ns, clock type/override boolean만 공개.
- 다른 프로세스나 TF 호출 바깥의 `rcl_clock_get_now` 호출, 시계 역행, override inactive, clock sample 부족/누락은 각각 HOLD.
- 수치형 JSON의 `root_cause_proven=false`, `tf_buffer_availability_wait_proven=false`, `same_rmw_source_clock_alignment_proven=false`, `gate_c_authorized=false`, `cm120_release_pass=false` 고정. 내부 clock만 봐도 canTransform 실제 가용성은 별도 정보이므로 원인 최종 PASS 불가.
- `d06/diagnostic/analyze_first_cm_tf.py` 원래 S1/S2 분석기는 신규 TF_CLOCK 행을 읽어도 기존 안전/인과 verdict 의미를 바꾸지 않는다.
- 6개 새 synthetic clock 테스트와 기존 privacy 회귀가 공개 L0에서 GREEN. 이후 **정확한 Jazzy OCI C++ ABI 빌드/real symbol selftest**를 별도 수행.

**실제 C++ ABI RED→GREEN:**
- [RED #44064016874](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44064016874): `rcl_get_zero_initialized_clock` 함수는 Jazzy rcl API에 존재하지 않아 컴파일 실패.
- 정확한 공식 `rcl_clock_init()` 계약에 따라 `rcl_clock_t c{};` zero-init 후 API를 호출하는 최소 수정.
- [실제 Jazzy ABI GREEN #44064224537](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44064224537), tested public code **`7dc045b82c953b17d697b7896ead5317fca97102`**, `completed/success`, 공식 GCC/CMake shared lib 빌드+원본 nav2_util ABI/sleep_for selftest + 신규 **rcl_clock_get_now C ABI selftest PASS**, 기존 6+3+4 Python unit **13/13 PASS**, ROS/Gazebo/Goal 실행 없음. 실제 stdout:
```text
[100%] Built target axia_g07_cm120_tf_diag
AXIA_G07_TASK01_ORIGINAL_JAZZY_ADVANCED_TF_ABI_AND_SLEEP_SELFTEST_PASS_NO_GOAL
AXIA_G07_TASK01_GENUINE_RCL_CLOCK_GET_NOW_ABI_SELFTEST_PASS_NO_GOAL
```
- 별도 공식 Jazzy/Harmonic **실제 CM NO_GOAL** 시계 후킹 L2는 공개 릴리스 lane `.github/workflows/axia-g07-task01-internal-rcl-clock-nogoal-l2-20261117.yml`, workflow commit `153ad2ccf16f74562d42989bcb41d3f7b4b77476` [Run #44064889546](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44064889546) **실행 중이며 완료판정 미검증**. 공개 CI는 Instructor SHA `966886c4627deb2bb3b37111fe336eeee6b9ebb4`를 읽기 전용 checkout하며 `AXIA_G07_CI_SIM_GOAL_ALLOWED=0`. 실증 전 `TF_CLOCK` native event/ROS clock 활성/CM PID·TID mapping 성공을 주장하지 않는다.

## 5. 실행·검증 명령 및 원본 정책

공개 L0:
```bash
python3 -m unittest discover -s d06/tests -p test_g07_task01_actual_first_gap_polling_bounds.py -v
python3 -m unittest discover -s d06/tests -p test_g07_task01_real_no_first_gap_custody.py -v
python3 -m unittest discover -s d06/tests -p test_g07_task01_tf_call_exact_sleep_budget.py -v
python3 -m unittest discover -s d06/tests -p test_g07_task01_internal_tf_clock_source.py -v
python3 -m unittest discover -s d06/tests -p test_g07_task01_public_evidence_allowlist.py -v
python3 -m unittest discover -s d06/tests -p test_g07_task01_public_evidence_adapter.py -v
# 실제 Jazzy OCI 빌드 명령은 공개 workflow:
# .github/workflows/axia-g07-task01-jazzy-abi-sleep-bracket-l0-20261117.yml
# cmake -S d06/diagnostic -B /tmp/axia_task01_sleep_abi
# cmake --build /tmp/axia_task01_sleep_abi --parallel 2
```

수정 파일: `d06/diagnostic/classify_exact_tf_sleep_budget.py`, `classify_internal_tf_clock.py`, `analyze_first_cm_tf.py`, `export_public_cm120_first_gap.py`, `cm_tf_gettransform_preload.cpp`, `d06/tests/test_g07_task01_tf_call_exact_sleep_budget.py`, `test_g07_task01_internal_tf_clock_source.py` 및 공개 L0 workflows.

## 6. 후속 실행 게이트

1. 공식 Jazzy rcl ABI selftest에서 PASS이면 **진단기 자체 ABI L0 GREEN**만 인정. 이후 실제 NO_GOAL 공식 CM에서 TF_CLOCK이 실제 기록되고 같은 PID/TID에 묶이는지 한 번 검증한다. 기존 private source SHA와 public sha pin; 이때 Goal 발행 금지.
2. 새 계측이 실제 공식 CM에서 동작하고 전체 NO_GOAL 안전 종료 계약이 유지될 때에만, **새로운 TF 내부 Clock 인과 증거를 확보할 수 있는 단 한 번의 차별화된 진단 Moving Goal**을 고려한다. 같은 조건으로 이미 실패했던 목표를 무제한 재시도하지 않는다.
3. 최초 120ms CM source breach가 그 실행에 없으면 Task01 원인 미입증 HOLD. 반대로 발생해도 sim clock/transform availability/runnable scheduler를 같은 TF call/CM source 시간창으로 연결하기 전 root cause PASS 금지.
4. 원인이 입증돼야 Task02 최소 수정 RED→GREEN. 그 뒤에만 tracer/LD_PRELOAD OFF **공개 원본 실 Gazebo 단일 Goal L2**에서 CM publisher max≤120ms/Observer max≤120ms, Guard 내부150ms, Scan/Odom/Clock300ms, source→CM→Guard 전달·최초 안전 전이, CLEAR→SLOW→STOP, ZERO dwell≥1s, S02 Contact0, exact UUID terminal, native Nav/Localization ACK, managed CM exit0, 14-topic 원본을 동일 source SHA로 검증. Owner WSL2 L3는 마지막 수동 인수.
5. 강사 비공개 정답 공개 금지. 공개 CI 시간값 숫자만 artifact, 추가 private Contents:Write 토큰 불필요, `main` 미병합. **SW STOP≠인증된 E-Stop**.

```text
AXIA_G07_TASK01_PUBLIC_EXACT_TF_CALL_L0=PASS_13
AXIA_G07_TASK01_PUBLIC_CLOCK_FIRST_WINDOW_L0=PASS_9
AXIA_G07_TASK01_PUBLIC_PRIVACY_AND_CAUSAL_CONTRACT_L0=PASS_27
AXIA_G07_TASK01_REAL_RCL_CLOCK_ABI=PASS_44064224537
AXIA_G07_TASK01_GAZEBO_NO_GOAL_NEW_HOOK=VERIFY_RUN_44064889546
AXIA_G07_TASK01_NEW_DIAGNOSTIC_MOVING_GOAL=NOT_RUN
AXIA_G07_TASK01_TF_BUFFER_CAUSE=UNPROVEN
AXIA_G07_TASK02=BLOCKED_CAUSE_UNPROVEN
AXIA_G07_TASK03_TRACER_OFF=NOT_RUN
AXIA_G07_TASK04_OWNER_WSL2=NOT_RUN
CM120_TRACER_OFF_RELEASE=HOLD
AXIA_MVP_DEMO_ACCEPTED=HOLD
CERTIFIED_ESTOP=false
MAIN_MERGED=false
```
