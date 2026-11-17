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
