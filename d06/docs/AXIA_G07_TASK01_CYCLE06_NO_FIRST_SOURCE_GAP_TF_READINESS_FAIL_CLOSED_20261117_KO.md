# AXIA G07 Task 01 Cycle 06 — 최초 source gap 없는 TF 가용성 오인 방지 (공개 CI RED→GREEN)

**작성:** 2026-11-17 KST  
**정책:** 공개 GitHub Actions만 실행, 새 Moving Goal 0회, 실제 WSL2 0회, 안전 정책·공식 Nav2 불변.  
**판정:** `Task01 진단 FAIL-CLOSED 개선 L0 PASS`; **최초 CM source gap의 근본 원인 UNPROVEN**. Task02~04는 HOLD.

## 1. OBSERVE — 기준선·실제 실패 증거와 최신 개발계열

- Legacy [Task01 PR #158](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/158) 원격 HEAD `0a5f968073902f3f677ad88e9f0c5aa9c0a31bc6`, 최종 [L0 #44036795558](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44036795558) **14/14 PASS**, 단 ROS/Gazebo 없음.
- 이 PR의 후속은 별도 Draft [#161](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/161), 작업 브랜치 `fix/g07-cm120-task01-clock-firstgap-causality-20261117`. GitHub `compare_commits`에서 legacy HEAD `0a5f...` → 이번 GREEN `8a170246...`은 **ahead 95 / behind 0**; 기존 작업 소거 없음.
- S1 실제 [#44011055816](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44011055816): CM source139.723543ms, Observer123.527663ms, Advanced TF101.682875ms, CPU0.322830ms; 원시 raw artifact **0개**, S2 NO_GOAL [#44013676608](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44013676608): 원본 TF477회·sleep427회, raw artifact **0개**; S2 Moving [#44014107942](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44014107942): 첫 source>120ms 미재현, 원시 artifact **0개**. 서로 다른 런의 원본을 합쳐 원인을 만들지 않음.
- 이후 동일 실행의 실제 첫 breach [#44049067368](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44049067368): RMW publisher source **129.299071ms**, Observer **128.391951ms**, advanced TF 약91.753ms, 동일 첫 Observer pair의 libc sleep **9회, 요청90ms / 측정91.416406ms**. 공개 allowlisted ZIP artifact **14313016879** 존재. 오직 숫자형 `d06/evidence/g07_cm120_task01/run_44049067368_first_gap_sanitized.json` + SHA256 보존. **정확한 per-call wall-clock 시작/종료·same sender source↔MONOTONIC calibration은 원본 보존 부족**, scheduler runqueue `sched_schedstats=0`, 가용성 first-gap 직접 결합 없음. L2 전체 FAIL.
- 추가 NO_GOAL 실제 Gazebo [#44072394317](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44072394317) **PASS**: 공식 TF 호출589회, zero-timeout `canTransform` 시작 false→종료 true **478회**, probe 최대0.461ms, native Nav/Loc ACK. **NO_GOAL**이므로 원래 Moving first-gap의 원인 증명이 아니다.
- 가장 최근 실제 Moving 진단 [#44073078458](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44073078458) **FAIL**: CM source 최대 **117.998ms**, Observer **118.261395ms**. 첫 source>120ms **미재현**; 이후 exact UUID CANCELED→Navigation SHUTDOWN 요청 후 ACK **40.000372s timeout**, Localization 요청 이전 중단, CM clean exit 미인수. 종료 결함은 별도 [Issue #163](https://github.com/silverbjin/axia-robot-safety-ci-public/issues/163)에서 추적하며 TF 인과/CM120 결과와 혼동 금지.
- C34 실제 native shutdown PASS [#44030235323](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44030235323) private Instructor **다른 SHA `49f38d7912bf8930a331577090522ccf52337fba`**. CM120 실제 tracer-OFF 인수 증거로 합성 불가.

## 2. RESEARCH — 공식 Jazzy 및 유사 사례의 적용 경계

| 자료 / 실제 버전 | 입증된 외부 사실 | AXIA 공통점 및 차이 | 판정 / 안전 영향 |
|---|---|---|---|
| [Jazzy Collision Monitor source.cpp](https://github.com/ros-navigation/navigation2/blob/jazzy/nav2_collision_monitor/src/source.cpp) / [Jazzy nav2_util robot_utils.cpp](https://github.com/ros-navigation/navigation2/blob/jazzy/nav2_util/src/robot_utils.cpp) | `base_shift_correction=true`인 공식 Source가 advanced fixed-frame TF 경로 사용 | 실제 AXIA advanced 함수 계측·동일 공식 경로 | **경로 일치**, 변경하지 않음 |
| [ROS geometry2 Jazzy buffer.cpp](https://github.com/ros2/geometry2/blob/jazzy/tf2_ros/src/buffer.cpp) | timeout `canTransform` 반복·원본 `std::this_thread::sleep_for(10ms)` 사용 | AXIA 첫 Observer pair에 실제 9회 sleep; 그러나 transform이 언제 unavailable인지 첫 source gap에서 미계측 | **polling 관측 확인**, root cause 미증명 |
| [Nav2 Issue #3402](https://github.com/ros-navigation/navigation2/issues/3402), merged [PR #3412](https://github.com/ros-navigation/navigation2/pull/3412) (2023) | simple TF는 latency 개선 가능, advanced 경로는 이동 중 시공간 보정 정확도 이점. PR 테스트 환경은 당시 Rolling/Ubuntu20.04 + TB3 Gazebo | AXIA는 Jazzy/Waffle/Harmonic, STOP0.40m/SLOW0.75m, 아직 동일 causal provenance 없음 | **현재 simple TF 변경 보류**; 안전 거리/스캔 지연 오차의 별도 검증 전 채택 금지 |
| [Nav2 Issue #4863](https://github.com/ros-navigation/navigation2/issues/4863) | 다중 호스트 센서와 navigation timestamp 불일치 증상 | AXIA 같은 호스트 CI의 SYSTEM–MONOTONIC provenance 부족이며 751155초 어긋남과 동일하지 않음 | **다른 현상**, 추정 동기 수정 금지 |
| [Linux schedstats 공식 문서](https://www.kernel.org/doc/html/latest/scheduler/sched-stats.html) | runnable wait는 활성화된 커널의 per-thread counter 변화량 필요 | 해당 원래 실험 `sched_schedstats=0`; voluntary context switch 수는 runnable ns가 아님 | **RUNQUEUE_UNAVAILABLE**, 0ms로 간주 금지 |

## 3. HYPOTHESIZE — 최소 재현 결함

**단일 가설:** `d06/diagnostic/classify_tf_availability.py`는 `first_gap` 부재·120ms 이하에서도 `TF_AVAILABILITY_READ_ONLY_RECORDED_HOLD`의 pre=false/post=true만 보고 `TF_INITIAL_UNAVAILABLE_LATER_AVAILABLE_CANDIDATE_HOLD`로 분류한다. 이는 실제 #44073078458처럼 source>120ms가 재현되지 않은 실행에 **최초 gap 원인 후보를 잘못 붙일 위험**이 있다.

**반증 실험:** 기존 `sample(probe())`를 사용해 (1) `first_gap=None`, (2) `rmw_source_gap_ns=117_998_000`만 만드는 두 ROS-free 반례. OLD는 잘못된 TF 후보 상태; 신규는 `FIRST_SOURCE_GAP_NOT_REPRODUCED_HOLD`. 예측 실패 시 변경 취소. TF와 발행기 성능·시계영역은 **전혀 수정하지 않음**.

## 4. RED → GREEN → REFACTOR → REVIEW → COMMIT → VERIFY

### RED
- 단일 파일 `d06/tests/test_g07_task01_tf_zero_timeout_availability.py`에 위 두 negative fixture 추가.
- RED commit `da037009dde3db907a9bf2e4f8c9973368bba109`.
- 실제 공개 [Actions #44083601997](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44083601997) job `134040177661`, **completed/failure**:
```text
run_44049067368_first_gap_sanitized.json: OK
test_no_first_source_gap_must_not_claim_same_gap_availability ... FAIL
test_subthreshold_source_interval_must_not_claim_same_gap_availability ... FAIL
AssertionError: 'TF_INITIAL_UNAVAILABLE_LATER_AVAILABLE_CANDIDATE_HOLD' != 'FIRST_SOURCE_GAP_NOT_REPRODUCED_HOLD'
Ran 9 tests
FAILED (failures=2)
```
- 이는 실제 ROS/TF 성능 위반이 아닌, **기존 진단기 오류의 최소 정적 반례**.

### GREEN
- `d06/diagnostic/classify_tf_availability.py`: root/release=false 검증 직후, 정확한 `first_gap.rmw_source_gap_ns`가 **정수이며 >120_000_000**인 경우만 TF availability 후보 판별. `first_gap` 없음/부정확한 값/경계 이하⇒fail-closed.
- GREEN commit **`8a170246551ef936ad9fb55d3d52f47e655cabac`**.
- 실제 공개 [Actions #44083837619](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44083837619), job `134040968326`, **completed/success**, source SHA는 위 GREEN commit.
```text
run_44049067368_first_gap_sanitized.json: OK
Ran 5 tests ... OK
Ran 2 tests ... OK
Ran 6 tests ... OK
Ran 9 tests ... OK
Ran 6 tests ... OK
Ran 5 tests ... OK
Ran 3 tests ... OK
AXIA_G07_TASK01_REAL_FIRST_GAP_POLLING_BOUNDS_L0_GREEN_RELEASE_HOLD
```
**36/36 L0 PASS**, py_compile PASS. 신규 실제 ROS/Gazebo/Goal 실행 없음.

### REFACTOR / REVIEW
- 기존 공개 workflow `.github/workflows/axia-g07-task01-real-firstgap-polling-bounds-l0-20261117.yml`의 정확한 branch+file path-trigger 재사용. 신규 workflow/서비스/계측기 없음.
- 변경된 production/safety source 0, 공식 Nav2/TF 0, TF/CM timeout·CPU affinity·STOP 0.40/SLOW0.75·Guard150ms·센서300ms·Goal 권한·Scenario Verifier 불변.
- source SYSTEM의 두 연속 source interval만 임계치 비교, Observer MONOTONIC 시각을 절대 source로 변환하지 않음.
- `root_cause_proven=false`, `gate_c_authorized=false`, `cm120_release_pass=false`, `certified_estop=false`는 변함없음.
- 리뷰한 patch: RED는 신규 negative fixture 2개, GREEN은 최초 RMW source gap 실제 존재 검사뿐. 중복 경계나 범용 진단기 추가하지 않음.
- Git 원본 PR #158와 현재 GREEN 비교: `ahead 95, behind 0`. 기존 소스 위에 누적한 최소 수정.
- 강사 private/학생/원본 raw 비공개 유지. 어떠한 runtime 개선을 주장하지 않음.

## 5. 남은 근본 원인과 다음 단일 착수 조건

**Task 01 핵심 원인은 STILL UNPROVEN.** 같은 첫 source gap #440490에서는 observer-matched 9 sleep의 요청90ms/실측91.416406ms를 알고, clock same-host offset anchor도 보존했지만 **그 TF 실행과 동일 publisher source SYSTEM epoch·사이클, 정확한 TF 내부 ROS Clock·가용성, 동일 PID/TID kernel runqueue**는 모두 인증되지 않았다. 오래된 S1/S2 raw artifact는 0개이며 복구하여 새 정확한 per-call 증거로 만드는 것은 불가능. `sched_schedstats=0`에서는 runnable ns를 0으로 간주할 수 없다.

**추가 Moving Goal 없이 가능한 증거 확인은 여기까지 실행:** 최초 sanitized JSON+SHA256, S1/S2/C34 GitHub run/artifact, Jazzy official TF code, TF2 zero-timeout 실제 NO_GOAL 및 정확한 기존 Clock ABI L0를 재조회했다. 새 동일 원인 분리 데이터는 기존 보존 원본만으로 추가 산출 불가. 과거 #440730은 첫 source breach **미재현**이므로 그 실행의 TF query로 원본 #440490의 원인을 역산하지 않는다.

**다음 차별화 실험의 필수 단일 조건:** runtime 원본 동일 최초 breach의 sender/system source epoch→host MONOTONIC 대응 보정과 같은 exact CM TF call 내 `canTransform` 가용성·sleep·ROS Clock(및 사용 가능한 경우 runnable scheduling) 결합. 데이터 보존은 기존 numeric allowlist+SHA256, private raw의 공개 유출 금지, 실제 Goal 추가는 현재 사용자 승인 범위를 준수. 재현되지 않으면 HOLD로 종료, 반복 금지. 추가 센서 전달/안전 시간 위반을 단일 TF 수정으로 해결됐다고 주장 금지.

```text
AXIA_G07_TASK01_CYCLE06_RED=FAIL_44083601997_EXPECTED_2
AXIA_G07_TASK01_CYCLE06_GREEN=PASS_44083837619_L0_36
AXIA_G07_TASK01_CYCLE06_CODE_SHA=8a170246551ef936ad9fb55d3d52f47e655cabac
AXIA_G07_TASK01_ORIGINAL_FIRST_SOURCE_CAUSE=UNPROVEN
AXIA_G07_TASK02=BLOCKED_CAUSAL_EVIDENCE
AXIA_G07_TASK03_TRACER_OFF=NOT_RUN
AXIA_G07_TASK04_OWNER_WSL2=NOT_RUN
CM120_TRACER_OFF_RELEASE=HOLD
AXIA_G07_PUBLIC_L2_ACCEPTED=false
AXIA_G07_OWNER_WSL2_L3_ACCEPTED=false
AXIA_MVP_DEMO_ACCEPTED=HOLD
CERTIFIED_ESTOP=false
MAIN_MERGED=false
```
