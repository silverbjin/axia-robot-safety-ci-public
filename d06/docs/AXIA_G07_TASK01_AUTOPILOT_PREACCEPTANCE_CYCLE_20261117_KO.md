# AXIA G07 — Task01~04 최종 현장검수 전 자동화 Cycle 01 개발·디버깅·인계 보고서

**2026-11-17 KST | 성격: 근거 수집/CI 자동화, 공식 Nav2·Safety 정책 미수정 | 결론: TASK01 진단기 GREEN, 실제 NO_GOAL 프로세스 계측 성공 범위 확보, 전체 L2 FAIL, 비공개 원시 보관 권한 차단 → Goal 차단. Task02/03/04 미착수.**

## 0. 사용자 승인·범위

사용자는 Task01~Task04 중 **최종 Owner WSL2 검수 이전 개발·진단·공개 CI를 자동으로 진행할 권한**을 승인했다. 이 승인은 새로운 CI-only **단일 진단 Moving Goal**을 허용하지만, **실제 데이터의 비공개 보존 사전검사 실패 시 Goal을 발행할 권한은 아니다.** 현장 WSL2 L3/물리 E-Stop/main 병합은 미허가/미실행. `AXIA_MVP_DEMO_ACCEPTED=HOLD`.

기준: `AXIA_Robot_Safety_MVP_Baseline_Scenario_Acceptance_v1_KO.md`, ROS2 Jazzy, Gazebo Harmonic, 공식 Nav2/TB3 Waffle, 기존 Safety Supervisor/Guard/Fault Injector/Scenario Verifier 재사용. CM RMW source 최대 ≤120ms, observer 최대 ≤120ms, Guard/CM TTL150ms, Scan/Odom/Clock300ms, STOP0.40/SLOW0.75 및 Goal terminal/native ACK 불변. tracer-ON 진단과 tracer-OFF 릴리스는 다른 평가이다.

## 1. 기준선 재조회와 Git 분리

| 구분 | 정확한 기준 |
|---|---|
| Task01 선행 [Draft PR #158](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/158) | head `c32a8a1e842814415c4f467b8ad9d3f6429ac182` 재조회 당시; 공개 L0 14/14 [#44036795558](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44036795558) |
| S2 [Draft PR #156](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/156) | `b32c6be7a4205b81ae04a8d68b5cfaec619a1f2b`; original actual Instructor `966886c4627deb2bb3b37111fe336eeee6b9ebb4` |
| C34 Instructor [Draft PR #208](https://github.com/silverbjin/axia-robot-safety-instructor/pull/208) | actual code `49f38d7912bf8930a331577090522ccf52337fba`, separate 150/300ms + Native ACK actual L2 [#44030235323](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44030235323) |
| 본 신규 공개 작업 브랜치 | `fix/g07-cm120-task01-autopilot-preacceptance-20261117` from previous Task01 `0a5f968073902f3f677ad88e9f0c5aa9c0a31bc6` |
| 공개 Draft PR | [#159](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/159), parent `fix/g07-cm120-task01-first-gap-tf-overlap-20261117`, **main 병합 안 함** |
| 비공개 증거 브랜치 | `silverbjin/axia-robot-safety-instructor:evidence/g07-cm120-task01-20261117`, 기존 original private SHA에서 생성; 공개 파일/아티팩트 아님 |
| 공개 릴리스-lane NO_GOAL preflight | `.github/workflows/axia-g07-task01-private-custody-release-preflight-20261117.yml`, dispatch-only 계약 commit `f0e3639625436cdd22f56bac700a8c833ee74457` |

서로 다른 source/branch의 성공을 동일 런으로 합산하지 않았다.

## 2. 공식 Jazzy 근거·단일 조건부 가설

- [Nav2 jazzy source.cpp](https://github.com/ros-navigation/navigation2/blob/jazzy/nav2_collision_monitor/src/source.cpp) `base_shift_correction=true`는 sensor stamp→current base advanced TF 경로.
- [Nav2 jazzy robot_utils.cpp](https://github.com/ros-navigation/navigation2/blob/jazzy/nav2_util/src/robot_utils.cpp): `tf_buffer->lookupTransform(... fixed_frame, transform_tolerance)`.
- [geometry2 Jazzy Buffer](https://github.com/ros2/geometry2/blob/jazzy/tf2_ros/src/buffer.cpp): advanced `canTransform`은 `clock_->now()`로 timeout을 확인하면서 실제 libc `std::this_thread::sleep_for(10ms)`로 폴링. [Nav2 PR #3412](https://github.com/ros-navigation/navigation2/pull/3412)는 advanced vs simple 정확도/성능 절충. [Issue #3402](https://github.com/ros-navigation/navigation2/issues/3402)와 AXIA 증상 비슷해도 동일 인과 불명.
- **H1:** 실제 CM이 ROS simulation clock을 사용하고 TF availability/clock advancement 지연이 존재하면 TF 함수 wall이 configured tolerance .02s보다 늘 수 있음. 하지만 S1 first RMW source gap139.724ms / TF wall101.683ms에서 actual poll intervals와 scheduler runqueue를 함께 기록하지 않아 **H1=UNPROVEN**. `sched_schedstats=0`의 runqueue는 UNAVAILABLE, 0ms로 판정 금지.

## 3. Task01-1 — 비공개 원시 증거 custody 사전게이트 RED→GREEN와 실제 실패

**이유:** 기존 [S1 #44011055816](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44011055816), [S2 NO_GOAL #44013676608](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44013676608), [S2 Moving #44014107942](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44014107942)의 GitHub artifact가 모두 **0건**이고 개인별 `TF_ADV` raw 행은 public job log에 남아 있지 않음. 실행 후 private raw cleanup을 반복하면 동일 인과 검증이 불가능.

구현: `d06/scripts/g07_task01_private_custody_canary.sh`
- `GITHUB_ACTIONS=true`, `AXIA_P0_SIM_ONLY=1`, `AXIA_G07_TASK01_GOAL_ALLOWED=0`, source SHA 형식/Run ID, 비공개 evidence branch/remote 검증.
- private branch에 **민감정보 없는** canary를 커밋→원격 push→원격 fetch `FETCH_HEAD` SHA256 비교. 어느 하나 실패하면 **GOAL_NOT_AUTHORIZED**.
- 기존 `AXIA_CLOUD_CI`는 비공개 Instructor 읽기용이므로, 가급적 해당 credential의 권한을 확대하지 않고 별도 최소권한 `AXIA_G07_EVIDENCE_WRITE_TOKEN`을 사용하도록 REFACTOR.
- 스크립트는 public logs에 token이나 private content를 출력하지 않는다. 원래 비공개 artifact는 공개로 업로드하지 않는다.

| 검증 | 실제 공개 결과 |
|---|---|
| RED (스크립트 미구현) | [#44042706598](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44042706598) completed/failure |
| GREEN public 순수 L0 | [#44042808232](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44042808232) completed/success: `Ran 4 tests ... OK` |
| 별도 token 사용 회귀 | [#44044744921](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44044744921) completed/success: 4/4 |
| feature-branch sealed 실행 | [#44042919213](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44042919213) pre-job failure, step detail 없음; 원인 단정 금지 |
| 기존 승인된 public release lane 실제 read + push | [#44043200646](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44043200646) private checkout/read PASS, remote push FAIL |
| 실패 분류 후 새 source | [#44043431253](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44043431253) `AXIA_G07_TASK01_PRIVATE_REMOTE_PUSH_FAILED_NO_GOAL class=AUTH_OR_CONTENT_WRITE_DENIED` |
| 분리 최소권한 credential 직접 검사 | [#44045232799](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44045232799) `AXIA_G07_EVIDENCE_WRITE_TOKEN: narrow private evidence write token required`, NO_GOAL |

**의미:** 기존 sealed runner는 private Instructor **읽기는 할 수 있으나 쓰기 권한은 증명되지 않았고, 기존 토큰 push는 거부**되었다. 새 최소권한 토큰은 **아직 설정되지 않음**. 비공개 SHA256 원격 round-trip **NOT_PASS**, 따라서 실제 Moving Goal **0회 추가**. 공개 원시 ROS 데이터를 올려 검증을 우회하지 않는다.

**블로커 해제에 필요한 환경 설정(사용자/저장소 관리자의 일회성 작업):** 공개 repo의 GitHub Actions environment `axia-instructor-sealed`에 `AXIA_G07_EVIDENCE_WRITE_TOKEN` 등록. Fine-grained GitHub token은 `silverbjin/axia-robot-safety-instructor` **해당 private 저장소 하나**에만 접근하고 **Contents: Read and write** 부여, 짧은 만료기간. 기존 `AXIA_CLOUD_CI`는 read-only 유지. 미등록 상태에서 workflow를 무작정 재실행하지 않는다.

preflight 실행기는 GitHub release lane에서 **dispatch-only**로 전환했다. 실제 비공개 canary 확인 없이 Goal을 시작하는 workflow는 허용하지 않는다.

## 4. Task01-2 — 최초 TF 함수 내 개별 sleep span 추가 계측, RED→GREEN

**기존 결함:** S2 `TF_ADV`는 함수 호출별 sleep **총 횟수/총 경과시간**만 있었다. 최초 source/observer interval 내 정확히 어떤 sleep이 있었는지 확인 불가. Scheduler `ru_nvcsw` count는 wait duration이 아니고, `/proc/schedstat` disabled이면 runqueue도 알 수 없음.

변경:
- `d06/diagnostic/cm_tf_gettransform_preload.cpp`: 원래 공식 Advanced TF 함수의 `RTLD_NEXT` 위임 그대로, libc `nanosleep/clock_nanosleep` outermost 호출마다 `TF_SLEEP pid/tid mono_start/end req_ns rc`를 bounded(≤15,000) 기록. wrapper `errno` 보존; no new publish/Goal; private source/pose 미기록.
- `d06/diagnostic/analyze_first_cm_tf.py`: S2 Legacy `TF_ADV` backward compatibility 유지; 신규 `TF_SLEEP`의 PID/TID 및 **동일 TF_ADV 실제 call interval** 소속 검사, 중첩·TF 경계 이탈·잘못된 numeric interval·aggregate sleep calls 대비 누락은 fail closed. RMW publisher SYSTEM/source interval과 Observer MONOTONIC receipt window를 직접 동일 epoch으로 간주하지 않으며 `source_publication_to_monotonic_alignment_proven=false` 유지.
- `d06/tests/test_g07_cm120_task01_per_sleep_span_join.py`: 신규 **6개** 회귀(동일 call, 타 PID, call 초과, 중첩, malformed, 부분 손실). 기존 S1/S2 **14개** 관련 회귀 재사용. 합계 20.

| 검증 | 실제 결과 |
|---|---|
| RED 신규 5개 | [#44043777862](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44043777862) FAIL, parser/marker 미구현 |
| GREEN per-sleep | [#44044014251](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44044014251), 5+3+4+3+4 = **19/19** ROS-free PASS |
| coverage 누락 신규 RED | [#44044942875](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44044942875), 새 6번째 항목 FAIL `TF_FUNCTION_DOMINANT_WAIT_CAUSE_UNPROVEN != TF_SLEEP_EVENT_COVERAGE_INCOMPLETE_HOLD` |
| 최종 GREEN | [#44044988154](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44044988154), tested `66310dd4d7c003ed3e87eb7342bee373935f5fec`, `Ran 6,3,4,3,4 tests ... OK`, **20/20 PASS** |
| 공식 Jazzy/Nav2 ABI 최초 | [#44044146329](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44044146329), actual GCC/CMake shared library build+original exported TF symbol+libc `sleep_for` selftest PASS, 12 pure tests |
| 최종 analyzer official Jazzy ABI | [#44044988111](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44044988111), tested `66310dd4d7c003ed3e87eb7342bee373935f5fec`, 6+3+4 tests + actual C++ build/selftest PASS |

본 단계는 **진단 코드 품질 GREEN**이지 실제 120ms 릴리스가 아니다.

## 5. Task01-3 — 실제 공식 CM NO_GOAL Jazzy/Gazebo 재실행의 성공과 실패 분리

검증: [공개 실제 NO_GOAL L2 #44044562869](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44044562869), job `133906940107`, public workflow `e7fb95c35d8d8061b80684828b7917eda035d07b`, compiled diagnostic public source `32df8c296a51757c899283b91552593686d94fca`, private Instructor original `966886c4627deb2bb3b37111fe336eeee6b9ebb4`.

**실제 stdout의 진단 영역:**
```text
AXIA_G07_S2_CM_PRELOAD_MAP_OBSERVED=1
AXIA_G07_TASK01_REAL_NO_GOAL_PER_SLEEP_SPAN_READBACK {
  "real_cm_tf_calls":1264,
  "same_pid_tid_inside_real_tf_call_polls":1059,
  "all_polls":1059,
  "poll_monotonic_wall_ms_total":10751.37476,
  "goal_sent":false,"release_pass":false,
  "source_first_gap_causality_proven":false
}
AXIA_G07_TASK01_REAL_NO_GOAL_PER_SLEEP_INTERVAL_PID_TID_JOIN_PASS
```
여기서 **10,751ms는 한 번의 지연이 아니라 1,059개 sleep wall의 전체 합계**. 동일 first source gap에 10,751ms가 있었다고 주장하지 않는다.

**실제 전체 workflow 결론은 completed/failure**. 후속 stdout:
```text
startup_status=SMOKE_READY
goal_sent=false
runner_rc=3
localization_shutdown_status=BLOCKED_LIFECYCLE_NAVIGATION_SERVICE_TIMEOUT
navigation_ack=false
localization_ack=false
AssertionError: LOCALIZATION_SHUTDOWN_FIRST_ACK_HOLD
```
**첫 관측 종료 경계는 Navigation lifecycle service timeout**이며 최종 Localization assert는 그 이후의 판정 메시지. NO_GOAL 구간에서 robot motion은 전혀 의도되지 않았으므로 첫 Guard-after-motion과 연결하지 않는다. 이번 실제 실행은 **노드 적재+TF sleep span PID/TID 관찰 PASS / 전체 NO_GOAL shutdown L2 FAIL**로 분리. 오래된 Instructor original과 이번 계측 overhead가 직접 원인인지 **UNPROVEN**. 이전 C34의 별개 SHA 실제 Navigation+Localization ACK PASS와 무조건 결합하지 않는다.

본 실행에서 추가 moving Goal을 발행하지 않았다. source gap>120ms의 동일 Moving 세션 TF sleep vs scheduler 원인은 여전히 **UNPROVEN**. 정상 tracer-OFF release 측정 아직 없음.

## 6. 수행하지 않은 단계 / 자동화 중단조건

| 게이트 | 최종 |
|---|---|
| Task01 새 TF sleep 원시 계측 분석/ABI | **PUBLIC_L0_GREEN20 + OFFICIAL_JAZZY_ABI_PASS**, genuine original official NO_GOAL exact span observability 관측 |
| Task01 private evidence remote commit + readback | **BLOCKED_MISSING_PRIVATE_WRITE_SECRET** |
| Task01 same-first-moving-source-gap TF-sleep vs runqueue 인과 | **UNPROVEN**, 진단 Moving Goal 아직 0회 추가 |
| Task02 proven-cause 최소 성능 수정 | **NOT_STARTED** — 근거 없는 `base_shift_correction`, `source_timeout`, affinity/TTL 변경 안 함 |
| Task03 tracer-OFF 실제 Moving Goal 120ms source+observer 통합 L2 | **NOT_STARTED** |
| Task04 Owner WSL2 live Gazebo+RViz2 L3 | **NOT_RUN** |
| Instructor/Student/main merge | **NO** |

## 7. 개발 파일·실행 명령·브랜치

변경 파일:
- `d06/scripts/g07_task01_private_custody_canary.sh`
- `d06/tests/test_g07_cm120_task01_private_custody_gate.py`
- `d06/diagnostic/cm_tf_gettransform_preload.cpp`
- `d06/diagnostic/analyze_first_cm_tf.py`
- `d06/tests/test_g07_cm120_task01_per_sleep_span_join.py`
- `.github/workflows/axia-g07-cm120-task01-private-custody-l0.yml`
- `.github/workflows/axia-g07-cm120-task01-private-custody-canary-sealed-l0.yml`
- `.github/workflows/axia-g07-task01-per-sleep-exact-join-l0-20261117.yml`
- `.github/workflows/axia-g07-task01-jazzy-abi-sleep-bracket-l0-20261117.yml`
- 공개 release 브랜치 별도 변경: `.github/workflows/axia-g07-task01-private-custody-release-preflight-20261117.yml`, `.github/workflows/axia-g07-task01-per-sleep-real-nogoal-20261117.yml`
- 본 교육·검증 보고서.

공개 순수 L0 명령:
```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s d06/tests -p 'test_g07_cm120_task01_private_custody_gate.py' -v
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s d06/tests -p 'test_g07_cm120_task01_per_sleep_span_join.py' -v
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s d06/tests -p 'test_g07_cm120_s2_exact_tf_offcpu_join.py' -v
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s d06/tests -p 'test_g07_cm120_s2_actual_sleep_provenance.py' -v
python3 -m py_compile d06/diagnostic/analyze_first_cm_tf.py
bash -n d06/scripts/g07_task01_private_custody_canary.sh
```
C++ Jazzy L0 실행 원본은 workflow `.github/workflows/axia-g07-task01-jazzy-abi-sleep-bracket-l0-20261117.yml`의 `cmake -S d06/diagnostic ...; cmake --build ...`. 실제 모든 CI raw stdout은 위 불변 Run URL에 존재한다.

이번 조사 중 **ROS Jazzy/Gazebo 실제 NO_GOAL**은 공개 Run #44044562869에서 실행했고 종료 L2는 실패했다. **WSL2 직접 실행은 불가능하여 실시하지 않음**. 증거가 없는 타이밍이나 인증된 E-Stop 성공을 주장하지 않는다.

## 8. 다음 자동 작업을 개시할 수 있는 정확한 조건

1. 저장소 관리자가 sealed environment `axia-instructor-sealed`에 제한된 private Instructor **Contents: read and write** 토큰을 `AXIA_G07_EVIDENCE_WRITE_TOKEN` 이름으로 추가. 기존 `AXIA_CLOUD_CI`는 Instructor checkout read-only로 유지.
2. 정확한 공개 release branch `release/p2-g06-cm-ttl-20261110`에서 등록된 **dispatch-only** `axia-g07-task01-private-custody-release-preflight-20261117.yml`을 단 한 번 실행하여 실제 private canary push + `FETCH_HEAD` SHA256 roundtrip **PASS** 확인. 이번 시도는 NO_GOAL, 최종 Owner 인수와 무관.
3. 진단 Moving Goal *한 번*을 실행하기 전 실제 원시 시계·callback/TF/sleep/event 및 Goal evidence의 **private upload+readback after failure** 보관 단계가 원본 코드에 포함되어 있고 L0에서 확인됐는지 다시 검토. 이 단계가 불충분하면 Goal은 계속 차단. 첫 source gap 미재현이면 같은 소스 재시도 금지.
4. 원인이 증명되기 전까지 Task02 성능 설정 변경과 Task03 tracer-OFF release를 시작하지 않는다. Task03 실제 공개 L2 정량 GREEN이어야 Owner WSL2 L3 한 번 인수 준비 가능.

```text
AXIA_G07_TASK01_AUTOPILOT_PUBLIC_CUSTODY_L0=PASS_4
AXIA_G07_TASK01_AUTOPILOT_PER_SLEEP_L0=PASS_20
AXIA_G07_TASK01_ORIGINAL_JAZZY_ABI=PASS
AXIA_G07_TASK01_REAL_NO_GOAL_TF_SPAN_JOIN=OBSERVED_1059_OF_1264
AXIA_G07_TASK01_REAL_NO_GOAL_NAV_LIFECYCLE=FAIL_SERVICE_TIMEOUT
AXIA_G07_TASK01_PRIVATE_REMOTE_CANARY=BLOCKED_MISSING_WRITE_SECRET
AXIA_G07_TASK01_NEW_MOVING_GOAL_COUNT=0
AXIA_G07_TASK01_ROOT_CAUSE=UNPROVEN
AXIA_G07_TASK02=BLOCKED_CAUSE_UNPROVEN
AXIA_G07_TASK03_TRACER_OFF=NOT_RUN
AXIA_G07_TASK04_OWNER_WSL2=NOT_RUN
AXIA_G07_CM120_RELEASE=HOLD
AXIA_MVP_DEMO_ACCEPTED=HOLD
CERTIFIED_ESTOP=false
MAIN_MERGED=false
```
