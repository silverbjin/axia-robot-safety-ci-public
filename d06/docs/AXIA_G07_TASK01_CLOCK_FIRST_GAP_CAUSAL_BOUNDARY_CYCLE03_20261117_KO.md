# AXIA G07 CM120 — Task01 Cycle 03: 동일 최초 지연창의 TF sleep·시뮬레이션 시계·Scheduler 원인 분리

**2026-11-17 KST / 공개 CI 개발 브랜치 `fix/g07-cm120-task01-clock-firstgap-causality-20261117` / Draft PR #161 / 인수 상태 HOLD**

> 이번 Cycle은 신규 기능 개발이나 STOP/TTL 조정이 아니다. 기존 실제 Moving Goal 공개 증거를 재활용해 TF 10ms sleep 기여량을 정확히 계산하고, 최초 CM gap과 **같은 ROS /clock 수신 구간**을 관찰할 수 있는 최소 읽기 전용 진단기와 검증 계약을 추가한다. 원본 Instructor 소스, 센서/TF pose, 원시 데이터는 공개하지 않는다.

## 1. 기존 실제 기준선 다시 확인

- 2026-11-17 공개 진단 Moving Goal [Run #44049067368](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44049067368), **completed/failure**, 원본 공식 Waffle/Harmonic/Nav2, 원본 private Instructor SHA `966886c4627deb2bb3b37111fe336eeee6b9ebb4`, public diagnostic SHA `5e6db932728085398fd1b6d9441847286d70c2be`.
- 공개 정상 증거 artifact SHA256 `3563b21f0b7a81760edd026bb28a14aee677593703e3f14cda4bbc285ebe6f92` [artifact ID 14313016879](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44049067368/artifacts/14313016879), 내부 JSON SHA256 `d242ea84b3b8cb3d133960998b62393bd34ad12ca1edef96e271695ac74977f9`.
- 저장된 공개 허용목록 원본: `d06/evidence/g07_cm120_task01/run_44049067368_first_gap_sanitized.json`와 대응 SHA256SUMS. **기존 성공 증거를 같은 조건으로 재생성하지 않고 사용.**
- 최초 publisher RMW source interval **129.299071ms**, observer receive interval **128.391951ms**, CM 입력 콜백 **91.944586ms**, Advanced TF wall **91.752789ms**, TF thread CPU **0.388890ms**. 동일 첫 Observer 쌍 내부 실제 libc sleep **9×10ms 요청, 실측 합계 91.416406ms**, 요청 초과량 **1.416406ms**. 서로 다른 TF 호출에서 추출된 수치를 임의로 하나의 블로킹 원인으로 합치지 않는다.
- 원본 안전 인수에서는 `source=344.101ms`, `clock=333.515ms`, `odom=346.212ms`, `scan=365.053ms`, `guard=372.483ms` 등 다른 300ms 경계도 초과. `CM120_RELEASE=HOLD`, 전체 실 Gazebo L2 FAIL.

## 2. 공식 Jazzy 코드 및 이전 성공 검사 재사용

- [ros2/geometry2 jazzy tf2_ros/src/buffer.cpp](https://github.com/ros2/geometry2/blob/jazzy/tf2_ros/src/buffer.cpp): Advanced `canTransform`은 node `clock_->now()`로 timeout을 보고 실제 `std::this_thread::sleep_for(10ms)`로 반복 대기.
- [ros-navigation/navigation2 jazzy nav2_collision_monitor/src/source.cpp](https://github.com/ros-navigation/navigation2/blob/jazzy/nav2_collision_monitor/src/source.cpp): `base_shift_correction=true`일 때 Advanced TF 조회. `base_shift_correction=false`는 좌표 보정 안전성 영향이 있으므로 원인 증명·구역 위험 분석 없이 적용 금지.
- Linux [schedstats 공식 문서](https://www.kernel.org/doc/html/latest/scheduler/sched-stats.html): per-thread runqueue nanoseconds는 **커널 통계 활성화와 실제 thread 값 확인**이 필수. 기존 `sched_schedstats=0`이므로 runqueue time은 **UNAVAILABLE**, `0ms`가 아님.
- 기존 공개 CI **실제 NO_GOAL 성공** [Run #43992804389](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43992804389): `clock_max_wall_interarrival_s=0.333601`, `odom_max_wall_interarrival_s=0.338193`, `tf_max_wall_interarrival_s=0.338594`, 동일 수신 시간대 공통 gap overlap 0.333601s, `sim_to_wall_factor=1.211201`, `goal_sent=false`, `rc=0`. **다른 실제 NO_GOAL 실행**이며 #44049067368 최초 source gap의 원인으로 합성 금지. 기존 성공 시험의 재실행 생략.

## 3. RED→GREEN — 기존 최초 지연창의 계측 산술과 안전한 분류

- 신규 `d06/tests/test_g07_task01_actual_first_gap_polling_bounds.py` **5개**, `d06/diagnostic/classify_first_cm_gap_polling.py`. 실제 공개 SHA 고정 원본을 검증 후 계산.
- [공개 RED #44053957281](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44053957281): 분석기 부재로 실패.
- [공개 GREEN #44054119394](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44054119394): **5/5 PASS**, 실제 JSON SHA256 확인, `AXIA_G07_TASK01_REAL_FIRST_GAP_POLLING_BOUNDS_L0_GREEN_RELEASE_HOLD`.
- 정확히 첫 Observer 구간에 **완전히 들어온 sleep 9개 / 91.416406ms**만 집계, 구간 전후 5개 배제. 각 요청 10ms×9 → 실제 초과 1.416406ms. 실제 TF 최대 단일 함수 wall91.732660ms 대비 nominal sleep coverage 약 99.655%.
- **해석:** 기존 첫 Observer 쌍과 연관된 TF 호출 내부의 대부분 시간이 자발적 10ms nanosleep이며, 추가 경과분은 1.416ms 수준이라는 숫자 자체는 근거 있음. 그러나 Python 숫자 비교만으로 **TF 변환이 왜 사용 불가능했는지**, **ROS sim clock이 첫 source interval 중 얼마 진행했는지**, **scheduler runqueue가 얼마나 대기했는지**는 확정 불가. 최대 TF call과 특정 아홉 sleep의 정확한 단일-call 식별은 공개 축약된 artifact만으로 재구성할 수 없음.
- 모든 경로에서 `root_cause_proven=false`, `gate_c_authorized=false`, `cm120_release_pass=false`, `scheduler_runqueue=UNAVAILABLE_SAME_RUN`, `first_gap_ros_clock_progress=UNAVAILABLE_SAME_RUN`.

## 4. RED→GREEN — 동일 Observer 시간창 ROS /clock 구독자 계측

- 신규 `d06/diagnostic/firstgap_clock_progress.py`, read-only `d06/diagnostic/g07_clock_probe_ros.py` (실제 `/clock` **구독만** 수행, 50,000개까지 monotonic host receive ns와 ROS sim stamp ns 보관, 원본 파일은 sealed CI 안에서만).
- 같은 first Observer pair의 시작/종료를 host MONOTONIC으로 고정하고, 시계 구독자 표본이 앞뒤로 bracketing하는지 검사; ROS 시각 역행·원본 누락·범위 초과·표본 부족·중복 timestamp → HOLD.
- `clock_progress` 필드는 기존 공개 허용목록 JSON에 **상대 숫자**만 추가. 강사 소스/센서 frame/pose/raw Clock message/epoch/TF geometry·callback 주소는 절대 공개하지 않음.
- 이 구독자는 tf2 Buffer의 실제 `clock_->now()`을 내부에서 읽는 게 아니다. **`clock_causality_proven=false`, `tf_buffer_clock_progress_proven=false`, `source_publication_to_monotonic_alignment_proven=false`, `cm120_release_pass=false`는 불변**.
- clock helper [RED #44054530865](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44054530865) → [GREEN #44054641245](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44054641245): **5/5 PASS**.
- 공개 JSON 결합 [RED #44054976700](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44054976700) → [GREEN #44055058317](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44055058317): **5+4 / 9개 PASS**, Python compile.
- `d06/scripts/g07_task01_extract_public_gap.py`에 옵션 `--clock-file` 추가; 없으면 기존 파일 스키마/출력을 그대로 유지하고, 지정됐으나 누락되면 실패-차단 clock 상태를 넣는다.

## 5. 공식 NO_GOAL 현장 사전시험 — 상태 업데이트 필요

- 기존 실제 Gazebo NO_GOAL 성공 runner를 재사용하여 읽기 전용 sidecar를 포함한 **새 공개 CI L2 [Run #44055379123](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44055379123)** 를 제출했다.
- Workflow: `.github/workflows/axia-g07-task01-live-clock-no-goal-l2-20261117.yml`, 공개 릴리스 경로 `release/p2-g06-cm-ttl-20261110`, workflow SHA `d91808aa5eee28afdfb737bd03838c43335e728a`, 공개 코드는 `05fbfeaf5cded7dabf991d7ecba045c8563d39c5` pin, sealed private noGoal Instructor code SHA `2df98da9cb9507ce905acbe82da46e93a79f0398`.
- **보고서 생성 시 실제 GitHub job 진행 중.** 현장 `SMOKE_READY`/lifecycle ACK/clock probe 수치/전체 conclusion을 재조회해 검증한 뒤 결과를 추가 기재할 것. 이 시점에서 PASS를 주장하지 않는다.
- 이 새 NO_GOAL 시험은 **원인 입증용 ROS clock probe 자체의 준비 검증**이며, 첫 Moving Goal의 동일 source gap 인과 테스트가 아니다.
- Goal은 **자동으로 발행하지 않음**. NO_GOAL STOP/종료 실패면 그 첫 경계를 공개 CI 회귀로 좁히고 같은 조건 반복 금지.

## 6. 다음 단계 Stop/Go

1. NO_GOAL 실제 시계 프로브가 **전체 GREEN**이어야 **새 증거를 확보할 수 있는 한정된 진단 Moving Goal**을 별도 공개 CI에서 고려한다. 사용자가 인수 전 자동화/진단 Goal을 승인했으나, CI GREEN이 아니라면 Goal 금지.
2. 신규 진단 Moving에서만 동일 first RMW source gap과 /clock 표본이 재현되면, 함수 sleep 10ms 반복과 실제 ROS sim 진행비를 같은 host MONOTONIC에 맞춰 **TF/clock drift 후보를 반증**한다. 실제 Buffer 내부 clock 가용성·source SYSTEM mapping·runqueue는 여전히 별도 검증 항목이다.
3. Task02는 **원인 증명 후 단 하나의 최소 성능 코드/설정 수정**과 RED→GREEN; 안전 STOP/Guard TTL/Scan/Odom/Clock 정책 완화 금지. Task03은 기존 공식 Nav2 tracer-OFF 실제 Gazebo 단일 Goal에서 CM source·Observer 양쪽 최대 ≤120ms 등 **전부** 실측해야 PASS. Task04는 사용자 WSL2 GUI 최종 인수 전에는 PASS 보고 금지.

## 7. 변경 파일 및 확인된 실행 명령

```bash
# 공개 pure L0 — 이미 실제 GREEN 원본 Run ID 존재
python3 -m unittest discover -s d06/tests -p 'test_g07_task01_actual_first_gap_polling_bounds.py' -v
python3 -m unittest discover -s d06/tests -p 'test_g07_task01_first_gap_clock_probe.py' -v
python3 -m unittest discover -s d06/tests -p 'test_g07_task01_clock_probe_public_export.py' -v
python3 -m py_compile d06/diagnostic/classify_first_cm_gap_polling.py
python3 -m py_compile d06/diagnostic/firstgap_clock_progress.py
python3 -m py_compile d06/diagnostic/g07_clock_probe_ros.py
python3 -m py_compile d06/scripts/g07_task01_extract_public_gap.py
```

변경 대상:
- `d06/diagnostic/classify_first_cm_gap_polling.py`
- `d06/diagnostic/firstgap_clock_progress.py`
- `d06/diagnostic/g07_clock_probe_ros.py`
- `d06/diagnostic/export_public_cm120_first_gap.py`
- `d06/scripts/g07_task01_extract_public_gap.py`
- `d06/tests/test_g07_task01_actual_first_gap_polling_bounds.py`
- `d06/tests/test_g07_task01_first_gap_clock_probe.py`
- `d06/tests/test_g07_task01_clock_probe_public_export.py`
- `.github/workflows/axia-g07-task01-real-firstgap-polling-bounds-l0-20261117.yml`
- `.github/workflows/axia-g07-task01-ros-clock-firstgap-l0-20261117.yml`
- release CI 별도 `.github/workflows/axia-g07-task01-live-clock-no-goal-l2-20261117.yml`
- 본 교육용 Cycle 03 증거 보고서.

```text
AXIA_G07_TASK01_REAL_FIRST_GAP_SLEEP_L0=PASS_5
AXIA_G07_TASK01_SAME_OBSERVER_CLOCK_PROBE_L0=PASS_9
AXIA_G07_TASK01_REAL_NO_GOAL_CLOCK_PROBE=VERIFY_RUN_44055379123
AXIA_G07_TASK01_SAME_MOVING_FIRST_SOURCE_CLOCK=NOT_YET_MEASURED
AXIA_G07_TASK01_TF_SLEEP_VS_SCHEDULER_ROOT_CAUSE=UNPROVEN
AXIA_G07_TASK02=BLOCKED_CAUSE_UNPROVEN
AXIA_G07_TASK03_TRACER_OFF=NOT_RUN
AXIA_G07_TASK04_OWNER_WSL2=NOT_RUN
AXIA_G07_CM120_RELEASE=HOLD
AXIA_MVP_DEMO_ACCEPTED=HOLD
MAIN_MERGED=false
CERTIFIED_ESTOP=false
```

## 8. NO_GOAL 시계 진단기 실제 실패 → 최소 RED→GREEN

### 최초 실제 실패

신규 첫 NO_GOAL real Jazzy/Harmonic CI [#44055379123](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44055379123) source `d91808aa5eee28afdfb737bd03838c43335e728a`은 **completed/failure**. 외부 Python 검사 마지막 exception은 `FileNotFoundError: /__w/_temp/g07_task01_clock_probe.jsonl`, 실제 최초 검증 경계는 **읽기 전용 Clock 진단기가 SIGTERM 후 자신의 JSONL을 저장하지 못한 것**. 이 결과를 TF/Collision Monitor/Navigation 실패라고 합성하지 않는다. 구독자 자체 로그는 공개하지 않고 정리되어 정확한 내부 exception은 미보존이다.

### 공식 소스에 근거한 단일 가설

[ros2/rclpy Jazzy rclpy/__init__.py](https://github.com/ros2/rclpy/blob/jazzy/rclpy/rclpy/__init__.py) `init` 기본 컨텍스트는 `SignalHandlerOptions.ALL`로 SIGINT/SIGTERM을 설치한다. 이전 독립 구독자 `d06/diagnostic/g07_clock_probe_ros.py`는 커스텀 signal handler를 `rclpy.init()` **전** 설치했으며, `finally`의 `rclpy.shutdown()`이 파일 원자적 저장 **전** 있었다. 따라서 ROS signal shutdown 경로가 커스텀 handler를 덮거나 예외 발생 시 파일을 누락할 수 있는 구조였다. **명시적으로 검증한 것은 파일 보존 실패와 수정 후 결과이며, 최초 hidden Python exception의 직접 원문을 복구했다고 주장하지 않는다.**

### 실제 ROS 2 Jazzy 프로세스 TDD

- 새로운 **실제 Jazzy OCI** 공개 L0 `.github/workflows/axia-g07-task01-clock-signal-persistence-l0-20261117.yml`: Gazebo/Goal 없이 `rclpy` 구독자 프로세스를 구동→`SIGTERM`→JSONL 파일 실재/종료코드 확인.
- [RED #44056046571](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44056046571), code `adee432d65a139c0064fccfcc89e603d6945225a`: 실제 stdout `AXIA_G07_TASK01_REAL_JAZZY_CLOCK_SIGTERM_FILE_MISSING_RED child_rc=1`. 순수 mock가 아닌 실제 Jazzy `rclpy` RED.
- 수정 `d06/diagnostic/g07_clock_probe_ros.py`, SHA `74b076cc4d92a49e26953452b1c722ffb5550df3`: `rclpy.init(signal_handler_options=SignalHandlerOptions.NO)` 뒤에 SIGTERM handler 설치, `finally`에서 **file flush/atomic replace FIRST**, ROS node destroy/context shutdown SECOND.
- [GREEN #44056374762](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44056374762): `AXIA_G07_TASK01_CLOCK_JAZZY_SIGTERM_FILE_PERSISTENCE_L0_GREEN_NO_GOAL`.
- REVIEW: 단순 파일 생성만으로 정상 종료를 위장하지 않도록 프로세스 `rc=0`도 요구한 강화 [GREEN #44056618278](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44056618278), code/runner SHA `319b0b467acf1e0d2b31357cf626e1644734b58d`, PASS.
- 공식 Gazebo/Harmonic read-only NO_GOAL 시험은 **실제 원인 수정 코드로 한 번만** 재실행: [Run #44056741357](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44056741357), workflow SHA `e61d6f26528b50f47e6ca902ddb5cdd1cb16f0ef`; 결과는 실제 Run 종료 확인 뒤 확정. 이 보고서 갱신 당시 실행 중이면 **PENDING, NOT PASS**.

**수정 범위:** 공개 CI read-only clock observer의 shutdown/원시 타이밍 임시 파일 보존만. 공식 Nav2/TB3 Waffle, TF buffer, CM/Guard, ROS 노드간 publish, STOP/Goal, safety TTL은 변경 없음. 이것은 인증된 물리 E-Stop이 아니라 진단 저장 경계 수리다.

```text
AXIA_G07_TASK01_REAL_JAZZY_CLOCK_SIGTERM_RED=REPRODUCED_44056046571
AXIA_G07_TASK01_REAL_JAZZY_CLOCK_SIGTERM_GREEN=PASS_44056618278
AXIA_G07_TASK01_REAL_HARMONIC_NO_GOAL_RECHECK=VERIFY_RUN_44056741357
AXIA_G07_TASK01_FIRST_MOVING_CLOCK_CAUSALITY=UNPROVEN
AXIA_G07_CM120_RELEASE=HOLD
AXIA_MVP_DEMO_ACCEPTED=HOLD
```

## 9. 변경된 단일 가설: 장시간 외부 Clock 구독 vs 원본 Native ACK — 실제 GREEN

- 독립 Gazebo/Goal 없는 로봇 시계계측 결과가 아니라 **실제 공식 Gazebo+Nav2 NO_GOAL** 환경에서 비교했다. 최초 [#44056741357](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44056741357)는 읽기 전용 Clock sidecar를 startup부터 native shutdown까지 ~120초 유지한 채 결과 `clock subscriber samples=36402`, `sim_to_wall_ratio=0.993921`, 그러나 private NO_GOAL runner `rc=3`, 최종 전체 `completed/failure`. 이는 진단 구독자의 생존 기간과 native 종료 실패의 상관관계이며, 구독자가 *유일한 원인*이라는 엄격한 단독 인과는 미증명이다.
- 기존 private 원본 실제 CI 스크립트 `scripts/p2_no_goal_smoke_ci.sh`는 `AXIA_G07_CM120_BASE_SHIFT_CORRECTION_TRUE_READBACK_NO_GOAL` 출력 직후 **8초 TF/Clock audit**를 실행하고 **그 다음 Nav2 native Lifecycle 종료**를 시작한다. 안전 정책이나 노드를 수정하지 않고 새로운 Clock sidecar를 오직 이 8초 중 6초만 실행하는 단일 차이 가설을 수립했다.
- 공개 release-lane 변경 `.github/workflows/axia-g07-task01-live-clock-no-goal-l2-20261117.yml`, commit `e2ad54d53b727e20a4616526d0997889ccf4659b`, 같은 원본 private Jazzy SHA, 동일 기존 8초 audit를 사용하고 sidecar가 native shutdown 전에 자동 종료되는지 검증.
- **실제 [GREEN Run #44057915125](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44057915125)**, job `133951920938`, `completed/success`. 검증된 주요 stdout:
```text
AXIA_G07_TASK01_CLOCK_PROBE_ENDED_IN_TF_AUDIT_BEFORE_NATIVE_SHUTDOWN
AXIA_G07_TASK01_REAL_NO_GOAL_CLOCK_PROBE {"samples":1952,"sim_to_wall_ratio":0.98513,"goal_sent":false,"cm120_release_pass":false,"tf_buffer_clock_proven":false}
AXIA_G07_TASK01_REAL_NO_GOAL_CLOCK_PROBE_PASS_NOT_CM_CAUSALITY
AXIA_G07_C03_NO_GOAL_REAL_TF_CLOCK_RESULT {"rc":0,"status":"OBSERVED_NO_GOAL_NOT_CM_CALLBACK_PROOF","tf_odom_count":524,"clock_tf_max_sim_age_s":0.003,"tf_max_wall_interarrival_s":0.015641,"odom_max_wall_interarrival_s":0.015374,"scan_max_wall_interarrival_s":0.141792}
AXIA_G07_TASK01_FIRST_NO_GOAL_SHUTDOWN_BOUNDARY {"status":"NAV2_LIFECYCLE_SHUTDOWN_ACK","navigation_ack":true,"localization_ack":true,"navigation_elapsed_sec":2.084495,"localization_elapsed_sec":0.291072}
AXIA_G07_C03_COMMON_GAP_REAL_GAZEBO_NAV2_OBSERVED_NO_GOAL_CAUSALITY_UNPROVEN
```
- **검증 범위:** 진단 Clock probe와 공식 NO_GOAL runtime/Native Shutdown의 조합으로 한정. 새로운 Moving Goal/첫 CM source gap 인과는 여전히 **NOT VERIFIED**. Tracer OFF release도 NOT RUN. 이 변경은 진단기 동작·수명 조절일 뿐 Safety Supervisor/Guard/Collision Monitor 설정·ROS/TF source/Goal ownership/인증 E-Stop 변경이 없다.
- 추가 단일 Moving 진단을 수행한다면 **첫 source gap의 정확한 /clock 진행값을 새로 확보할 목적이 있는 단 한 번**으로 제한하고, 공식 source/observer/TF sleep 기록을 같은 run에 묶되 공개에는 수치형 허용목록 JSON+SHA256만 보존. NO_GOAL 통과를 Moving/L3 PASS로 승격하지 않는다.

```text
AXIA_G07_TASK01_NO_GOAL_NATIVE_SHUTDOWN_OBSERVER_ALIVE=FAIL_44056741357
AXIA_G07_TASK01_NO_GOAL_NATIVE_SHUTDOWN_AUDIT_SCOPED=PASS_44057915125
AXIA_G07_TASK01_NO_GOAL_NATIVE_NAV_ACK=true
AXIA_G07_TASK01_NO_GOAL_NATIVE_LOC_ACK=true
AXIA_G07_TASK01_MOVING_FIRST_GAP_CLOCK=NOT_YET_MEASURED
AXIA_G07_TASK01_ROOT_CAUSE=UNPROVEN
AXIA_G07_CM120_TRACER_OFF_RELEASE=HOLD
AXIA_MVP_DEMO_ACCEPTED=HOLD
```

## 10. 승인된 신규 첫-gap 동시 시계 진단 Moving Goal 실제 결과 — 조건부 종료(HOLD)

### 정확한 실행·증거 원본

- 공개 CI [Run #44059005075](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44059005075): **completed/failure**. 원본 repo/public single-Goal workflow SHA `cd93b3235d432f19e3d6792e81de64f774bacb33`, 진단 공개 SHA `19ec465b7fdcb99391419e8252906961f1cda1a1`, 원본 비공개 Instructor SHA `966886c4627deb2bb3b37111fe336eeee6b9ebb4`. 이 실행은 기존 Goal을 근거 없이 반복한 것이 아니라 **이전 같은 source gap에 없던 동시 /clock 기록**을 수집하도록 진단 코드를 바꾼 단 한 번의 Moving Goal이다.
- **실제 Nav2 주행 step #16 PASS**: 공식 Waffle/Harmonic 단일 Goal CLEAR→SLOW→STOP/odom dwell, exact UUID cancel, Nav+Localization lifecycle ACK 및 managed CM exit0 검증. Private Instructor 정답 코드는 공개하지 않음.
- 실제 최초 CM RMW source>120ms pair 추출 **FAIL**: **발행 source 최대 `0.11721s` (117.210ms)** — 해당 원본 Goal 창에서 최초 source>120ms breach **재현되지 않았다**. 관련 LTTng C05 단계 #17은 `FIRST_CM_RMW_SOURCE_PAIR_UNVERIFIED_HOLD`로 **명시적 fail**, 전체 workflow `completed/failure`. 그 밖의 post-Goal safety/Native provenance checker 다수는 PASS였지만 tracer-OFF CM120 release PASS **아님**.
- 정확한 인수 로그:
```text
AXIA_G07_TASK01_CLOCK_SIDECAR_SCOPE_GOAL_OBSERVER_ONLY
AXIA_G07_TASK01_MOVING_CLOCK_SIDECAR_ENDED_BEFORE_NATIVE_SHUTDOWN
AXIA_G07_REAL_EXACT_NAV2_GOAL_CANCEL_ACK_BEFORE_LIFECYCLE_PASS
AXIA_G07_REAL_POST_GOAL_OWNER_IDENTICAL_NAV2_SHUTDOWN_CM_EXIT0_PASS
AXIA_G07_CI_REAL_HARMONIC_NAV2_MOVING_GOAL_CLEAR_SLOW_STOP_L2_PASS_OWNER_L3_NOT_RUN
AXIA_G07_C05_FIRST_CM_CMD_CALLBACK_DIAGNOSTIC {..."status":"FIRST_CM_RMW_SOURCE_PAIR_UNVERIFIED_HOLD"...}
AXIA_P4_G07_REAL_RMW_CM_SOURCE_MAX_GAP_SEC=0.11721
AXIA_G07_FIELD_REAL_CM_BELOW_120MS_RELEASE_MARGIN_PASS
AXIA_G07_TASK01_PUBLIC_TIMING_EVIDENCE_STATUS=FIRST_RMW_SOURCE_GAP_NOT_REPRODUCED
AXIA_G07_TASK01_PUBLIC_TIMING_EVIDENCE_BYTES=751
AXIA_G07_TASK01_PUBLIC_EVIDENCE_NOT_RELEASE_NOT_ESTOP
```
- 같은 Run의 공개 artifact [ID14317213107](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44059005075/artifacts/14317213107), ZIP SHA256 `e1d54411e9e3b30d67389cd7f1dc7847a6c1b701228fb44e9cec3fffb2a3e82f`; 정확히 `first_gap_sanitized.json`과 `SHA256SUMS.txt` 두 파일.
- 실제 다운로드한 공개 허용목록 JSON bytes=751, SHA256 `03728855c60a0a8dd69ad8b48960db078980ea675f40936c14b991a1849f6b34`. JSON `run_id=44059005075`, `first_gap=null`, `status=FIRST_RMW_SOURCE_GAP_NOT_REPRODUCED`, `root_cause_proven=false`, `gate_c_authorized=false`, `cm120_release_pass=false`. 이 실행에서는 관찰 대상 첫 gap이 없어 `clock_progress`도 해당 gap에 대해 출력하지 않았다. 이 데이터는 이전 Run의 9회 TF sleep을 재판정하는 동일 원본이 아님.

### 자동 반복 중지 / 다음 단계 판단

원인 분리가 완료되지 않았다는 이유로 **동일 소스/장면/계측으로 Goal을 추가 반복하지 않는다**. 새로 확보한 원본으로 다음 사실만 인정한다.

1. 기존 최초 source gap129.299ms에서 TF 함수9회의 실제 nanosleep 91.416ms는 진짜 계측이다([#44049067368](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44049067368)); 외부 Clock 수신 기록은 당시 없었다.
2. 새로운 단일 Goal에서는 실제 source 최대117.210ms로 해당 최초 source gap이 **재현되지 않음**. 공식 Goal/CM/Shutdown 구동이 정상 범위였다는 관찰은 가능하지만 **불안정성이 영구 해결되었다는 증거는 아님**.
3. 기존 NO_GOAL 다른-run `/clock` sim-to-wall0.985와 Moving 최초 TF sleep91.416ms를 같은 실행으로 결합해 TF Buffer timeout/ROS sim clock stall의 원인을 증명해서는 안 된다.
4. Kernel `sched_schedstats=0`: runqueue latency는 `UNAVAILABLE`, 0이 아님. Sleep 요청 총90ms와 실제91.416ms 차이만으로 scheduler vs TF 가용성의 독립 인과를 증명할 수 없다.
5. Task02에서 `base_shift_correction=false`/timeout/affinity/TTL을 추측해 변경하지 않는다. Task03 tracer-OFF 본 인수와 Task04 Owner WSL2를 승격할 수 없다.

### 근거 기반 단일 후속 연구 제안(이번 Cycle에서는 **실행 안 함**)

다시 실제 Moving Goal을 실행하려면 동일 첫 source gap이 생겼을 때 새 데이터를 얻는 **전혀 다른, 사전 검증된 관측 계약**이 필요하다. 현재 허용된 공개 축약 데이터로도 source SYS→callback MONO sender clock 정합 및 TF Buffer 내부 clock available/runqueue 큐잉 구분을 완전히 증명할 수 없다. 과도한 커널 tracing 도입·공식 Nav2 fork·동적 장애물 별도 시나리오 개발로 MVP를 확장하지 않는다.

현 시점 **Task01: 분석 도구 완성 및 첫 gap 심층 수치계측 검증, ROOT_CAUSE 미입증**. Task02 원인 기반 최소 수정 차단, Task03 공개 tracer-OFF real L2 미실행, Task04 Owner WSL2 L3 미실행.

```text
AXIA_G07_TASK01_DIAGNOSTIC_GOAL_SINGLE_RUN=RUN_44059005075
AXIA_G07_TASK01_DIAGNOSTIC_GOAL_REAL_RUNTIME=PASS_SCOPED_ONLY
AXIA_G07_TASK01_CM_SOURCE_MAX_MS=117.210
AXIA_G07_TASK01_FIRST_SOURCE_OVER_120_PAIR=NOT_REPRODUCED
AXIA_G07_TASK01_PUBLIC_ARTIFACT=PASS_SHA256_SANITIZED_HOLD
AXIA_G07_TASK01_CAUSE=UNPROVEN
AXIA_G07_TASK02=BLOCKED_CAUSE_UNPROVEN
AXIA_G07_TASK03_TRACER_OFF=NOT_RUN
AXIA_G07_TASK04_OWNER_WSL2=NOT_RUN
AXIA_G07_CM120_RELEASE=HOLD
AXIA_MVP_DEMO_ACCEPTED=HOLD
CERTIFIED_ESTOP=false
MAIN_MERGED=false
```
