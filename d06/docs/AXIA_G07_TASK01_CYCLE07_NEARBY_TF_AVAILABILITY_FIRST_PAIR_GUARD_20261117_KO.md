# AXIA G07 Task 01 — Cycle 07: 인접 TF 콜백을 최초 CM source gap 원인 후보로 오인하는 결함 수정

작성 2026-11-17 KST. **공개 GitHub Actions만 실행**. 범위는 기존 ROS-free 진단기 검사 경계 한 건이다. 실제 Nav2, Collision Monitor, Safety Supervisor, Guard, Fault Injector, Scenario Verifier, Goal, 공식 TF, CM120/Guard150/Scan·Odom·Clock300, STOP0.40m/SLOW0.75m 등 **시연 동작 변경 없음**.

**전체 결과:** `PUBLIC_L0=PASS_37`, `Task01 최초 source-gap 근본 원인=UNPROVEN`, `Task02=BLOCKED`, `Task03 tracer-OFF=NOT_RUN`, `Task04 Owner WSL2=NOT_RUN`, `AXIA_MVP_DEMO_ACCEPTED=HOLD`. SW STOP은 실제 인증된 E-Stop이 아님.

## 1. OBSERVE — 최초 실패, 원본 SHA 및 별도 오류

기존 [공개 최초 breach #44049067368](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44049067368): **RMW publisher source 129.299071ms >120ms**, 동일 pair의 Observer 128.391951ms >120ms. 공식 Advanced TF 약91.753ms, 첫 Observer pair 내 9회 libc sleep 요청90.000ms / 실측91.416406ms. 진단 tracer ON **전체 L2 FAIL**. 숫자만 공개하는 allowlisted `d06/evidence/g07_cm120_task01/run_44049067368_first_gap_sanitized.json` + SHA256SUMS만 남아 있다. 해당 원시 TF call exact start/end, RMW source SYSTEM↔CM MONOTONIC 인증, 동일 가용성·runqueue raw는 없음.

[NO_GOAL 가용성 #44072394317](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44072394317)에서 TF 589회/시작 false→끝 true 478회를 **실제 공식 Gazebo NO_GOAL**에서 관찰. 다른 실행의 TF 가용성을 최초 Moving source gap에 붙일 수는 없다.

후속 [Moving #44073078458](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44073078458)은 **첫 source>120ms 미재현**(source 최대117.998ms), Navigation native SHUTDOWN request_sent 후 40.000372초 ACK timeout. 별도 [Issue #163](https://github.com/silverbjin/axia-robot-safety-ci-public/issues/163), Task01 TF 원인으로 합성 금지. 이전 성공 C34 [#44030235323](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44030235323)은 private source SHA `49f38d7912bf8930a331577090522ccf52337fba`로서 CM120 tracer-OFF 합격을 뜻하지 않는다.

## 2. RESEARCH — 공식 코드·Issue·채택 판단

| 출처 | 공식 사실 / 버전 | AXIA 유사점·차이 | 적용 결정 / 안전 영향 |
|---|---|---|---|
| [ROS geometry2 Jazzy tf2_ros buffer.cpp](https://github.com/ros2/geometry2/blob/jazzy/tf2_ros/src/buffer.cpp) | Jazzy C++ `Buffer::canTransform`의 제한시간 폴링은 `clock_->now()`와 `std::this_thread::sleep_for(10ms)`를 사용 | 실제 #440490 first observer pair에 9회 sleep; **같은 first RMW source gap의 직접 가용성은 없음** | 기존 공식 경로 유지 |
| [Nav2 Jazzy collision_monitor source.cpp](https://github.com/ros-navigation/navigation2/blob/jazzy/nav2_collision_monitor/src/source.cpp) | `base_shift_correction`에 따른 Advanced TF 조회 경로 | AXIA는 advanced=true, fixed frame 시간 보정을 사용 | 성능 옵션 변경하지 않음 |
| [Nav2 Issue #3402](https://github.com/ros-navigation/navigation2/issues/3402), [병합 PR #3412](https://github.com/ros-navigation/navigation2/pull/3412) | Advanced 조회 지연 사례; simple 조회는 보정 정확도를 희생할 수 있음. PR 원본 환경 당시 Rolling/TB3 Gazebo | AXIA Jazzy/Harmonic 안전 STOP·SLOW 구역과 부하가 다름 | **성능 수정 후보일 뿐**, 차이·안전 여유 미증명으로 보류 |
| [Linux schedstats](https://www.kernel.org/doc/html/latest/scheduler/sched-stats.html) | 실제 runnable 대기 증명에는 활성화된 per-thread counter 변화량이 필요 | 기존 CI `sched_schedstats=0` | 지연 기여량 `UNAVAILABLE`, 0ms로 추정 금지 |

공식 링크는 이 단계의 **진단 판단 근거**이며 해당 upstream Issue가 AXIA 원인까지 입증했다는 뜻이 아니다. 설치된 공식 ROS 패키지의 정확한 소스 커밋은 이번 L0에서 새로 판독하지 않았고 기존 Jazzy ABI 통과 기록 [#44072012680](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44072012680)만 재사용했다.

## 3. HYPOTHESIZE — 가장 작은 반증 가능한 결함

기존 `d06/diagnostic/export_public_cm120_first_gap.py`는 정확한 CM PID/TID를 필터하면서 **최초 선택한 Observer 창의 앞뒤 200ms까지** TF call 및 zero-timeout 가용성 관측을 수집한다. 이는 잠재 raw를 보존하려는 의도된 진단 범위다.

그러나 `classify_tf_availability.py`는 해당 가용성 span의 시작/끝 상대 시각이 실제 first Observer pair `[0, first_gap.observer_gap_ns]`와 겹치는지 확인하지 않았다. 따라서 **같은 PID/TID의 다른 CM 콜백**에서 TF entry false/exit true가 있으면, 최초 source 120ms 위반이 실제로 존재해도 무관한 콜백을 `TF_INITIAL_UNAVAILABLE_LATER_AVAILABLE_CANDIDATE_HOLD`로 분류할 위험이 있다.

**예상 RED:** 동일 source gap을 포함한 기존 synthetic Observer(12.000→12.132)에 다른 정확한 CM callback과 official TF probe를 (a) 전 11.864→11.955, (b) 후 12.160→12.240 배치. 기존 exporter는 설정상 두 범위를 허용하며, 기존 classifier는 둘 다 원인 후보로 잘못 표시.

**예상 GREEN:** producer 수집 범위와 ROS 동작은 그대로 두고 consumer에서 **관측 probe bracket이 Observer pair와 전혀 겹치지 않으면 반드시 HOLD**. 겹치는 probe도 정확한 TF 함수와 publisher SYSTEM clock 인과를 증명하지는 않음. 위 두 RED 외 의미 없는 반복/새 Goal을 실행하지 않는다.

## 4. RED → GREEN → REFACTOR → REVIEW → COMMIT → VERIFY

### RED — 공개 CI 실제 실패

- Commit `b0bb4dfa1d727b8d9609b7dae1ff65aa7d0538c2`.
- 파일: `d06/tests/test_g07_task01_tf_zero_timeout_availability.py`에 단일 검사 + **앞/뒤 2개 subcase**.
- [공개 Run #44089012960](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44089012960), job `134058942221`, `completed/failure`:
```text
AXIA_G07_TASK01_REAL_PUBLIC_FIRST_GAP_SHA256_VERIFIED
test_other_callback_availability_is_not_first_observer_pair (tf_start=11.864) ... FAIL
test_other_callback_availability_is_not_first_observer_pair (tf_start=12.16) ... FAIL
AssertionError: 'TF_INITIAL_UNAVAILABLE_LATER_AVAILABLE_CANDIDATE_HOLD'
  != 'TF_AVAILABILITY_OUTSIDE_FIRST_OBSERVER_PAIR_HOLD'
Ran 10 tests in 0.002s
FAILED (failures=2)
```
- 이는 실제 Gazebo 장애를 새로 관찰한 것이 아니라 **기존 진단기의 잘못된 근거 부여를 재현한 L0**.

### GREEN — 단일 조건 보강

- Commit `95b99f58b66ee20ac921d7a09d1d7790f4a0ed9e`.
- 파일: `d06/diagnostic/classify_tf_availability.py`만.
- 기존 `first_gap.rmw_source_gap_ns >120_000_000` 확인 유지. `observer_gap_ns` 양의 정수 및 최대 1초 범위 확인. 각 TF probe span `pre_start_rel_observer_ns < post_end_rel_observer_ns` 검증. `post_end <=0` 또는 `pre_start >= observer_gap_ns`이면 `TF_AVAILABILITY_OUTSIDE_FIRST_OBSERVER_PAIR_HOLD`. **이는 전혀 겹치지 않는 관측을 배제하는 최소 필요조건일 뿐, 겹치면 causality proven이라는 뜻이 아님**.
- [공개 Run #44089226512](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44089226512), job `134059675775`, `completed/success`, pinned GREEN SHA `95b99f58...`.
```text
run_44049067368_first_gap_sanitized.json: OK
AXIA_G07_TASK01_REAL_PUBLIC_FIRST_GAP_SHA256_VERIFIED
Ran 5 tests ... OK
Ran 2 tests ... OK
Ran 6 tests ... OK
test_other_callback_availability_is_not_first_observer_pair ... ok
Ran 10 tests ... OK
Ran 6 tests ... OK
Ran 5 tests ... OK
Ran 3 tests ... OK
AXIA_G07_TASK01_REAL_FIRST_GAP_POLLING_BOUNDS_L0_GREEN_RELEASE_HOLD
```
**37/37 공개 ROS-free L0 PASS** (5+2+6+10+6+5+3), `py_compile` 기존 workflow 검사 통과. 원본 ZIP/JSON SHA 값도 변하지 않음.

### REFACTOR / REVIEW

- 기존 동일 공개 CI workflow `.github/workflows/axia-g07-task01-real-firstgap-polling-bounds-l0-20261117.yml` 재사용. 새 ROS 노드, 실행기, workflow, 성능 계측기, 새로운 TF 변환 또는 ROS 파라미터 추가 **없음**.
- 콜백 PID/TID는 공개되지 않으며 기존 sealed runner에서만 비교; 숫자형 허용목록 외 원본 비공개 유지.
- 원본 source SYSTEM, Observer MONOTONIC을 직접 절대시각 차감하지 않음.
- 수정은 **원본 근거 분류의 fail-closed 보수성**만 증가. `root_cause_proven=false`, `gate_c_authorized=false`, `cm120_release_pass=false`, `certified_estop=false` 고정.
- Robot의 7개 노드 간 TTL·Guard age·Scan/Odom/Clock·odometry·contact·Goal native ACK는 이번 L0에서 **실행/검증하지 않았으므로 전체 시연 안정성은 미검증**.
- 기존 성공과 실패의 실행 SHA를 현재 문서-only commit의 동적 검증으로 승격하지 않는다.

## 5. 다음 단계 및 STOP 조건

**원래 같은 Moving 최초 CM RMW publisher source >120ms의 실제 root cause는 아직 미확정.** 보존된 #440490 allowlisted 9 sleep은 한 Observer pair 내부의 libc 대기만 확증한다. **원본 정확한 TF call / transform availability / ROS Clock / sender-to-mono alignment / thread runnable 시간**이 하나의 실제 source gap에 결합되지 않아 Task02 성능 수정은 BLOCKED.

이후 진행에 허용되는 것은 이미 있는 실제 NO_GOAL·AB I·정제 원본 증거의 재분석이나, 새 정보를 제공한다는 조건을 충족한 **최소 차별화 진단**뿐이다. 추가 Moving Goal은 별도 승인과 정확한 증거 목적이 필요하며 동일 코드 blind rerun 금지. 새 profiler framework/공식 Nav2 fork/TTLs·STOP 영역 완화/CPU tuning 금지.

Task03 tracer-OFF 공개 실제 Gazebo L2, Task04 강사 WSL2 L3는 아직 시작할 수 없다. Task03는 7계층 max delivery + exact UUID terminal + Nav/Loc ACK + CM exit0 + 원본 14-topic/Contact0가 **동일 release source SHA**로 검증될 때만 인수할 것. Owner L3 단일 원샷은 그 다음이다. `main` 병합은 사용자 승인 필요.

### 다음 작업 명령(실제로 공개 CI에서 사용된 범위)

```bash
python3 -m unittest discover -s d06/tests -p 'test_g07_task01_tf_zero_timeout_availability.py' -v
python3 -m unittest discover -s d06/tests -p 'test_g07_task01_actual_first_gap_polling_bounds.py' -v
python3 -m py_compile d06/diagnostic/classify_tf_availability.py
cd d06/evidence/g07_cm120_task01
sha256sum -c run_44049067368_SHA256SUMS.txt
```

### 상태

```text
AXIA_G07_TASK01_CYCLE07_RED=EXPECTED_FAIL_44089012960
AXIA_G07_TASK01_CYCLE07_GREEN=PASS_37_44089226512
AXIA_G07_TASK01_CYCLE07_TESTED_SOURCE_SHA=95b99f58b66ee20ac921d7a09d1d7790f4a0ed9e
AXIA_G07_TASK01_ORIGINAL_SOURCE_GAP_CAUSE=UNPROVEN
AXIA_G07_TASK02=BLOCKED_CAUSAL_EVIDENCE
AXIA_G07_TASK03_TRACER_OFF_L2=NOT_RUN
AXIA_G07_TASK04_OWNER_WSL2_L3=NOT_RUN
CM120_TRACER_OFF_RELEASE=HOLD
AXIA_G07_PUBLIC_L2_ACCEPTED=false
AXIA_G07_OWNER_WSL2_L3_ACCEPTED=false
AXIA_MVP_DEMO_ACCEPTED=HOLD
MAIN_MERGED=false
CERTIFIED_ESTOP=false
```
