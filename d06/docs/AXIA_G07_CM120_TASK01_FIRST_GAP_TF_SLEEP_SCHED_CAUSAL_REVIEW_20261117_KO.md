# AXIA G07 CM120 — Task 01 최초 CM source 지연: TF sleep 대 Scheduler 원인 분리 실행·검증 보고서

- 기록일: **2026-11-17 KST**
- 결론: **Task01 기존 증거 재조회 + 경계 결함 RED→GREEN→REFACTOR·REVIEW 완료**, 그러나 **최초 RMW source 간격의 TF sleep vs scheduler 직접 인과는 UNPROVEN**; Gate C 최소 성능 수정 **NOT STARTED**, Gate D tracer-OFF release **NOT RUN**.
- 공개 CI: `silverbjin/axia-robot-safety-ci-public`, 신규 분리 브랜치 `fix/g07-cm120-task01-first-gap-tf-overlap-20261117`(S2 원본 인계 HEAD `b32c6be7a4205b81ae04a8d68b5cfaec619a1f2b`에서 분기).
- 기존 원본 Instructor: `966886c4627deb2bb3b37111fe336eeee6b9ebb4`; 이번 Task01 **Instructor/학생/공식 Nav2/실제 CM/ROS 코드는 변경하거나 실행하지 않음**.
- 정책: `CM_RMW_SOURCE_MAX<=120ms`, `CM_OBSERVER_MAX<=120ms`, Guard/CM 150ms hard safety TTL, Scan/Odom/Clock 300ms, STOP0.40/SLOW0.75, original `base_shift_correction=true`, `source_timeout=1.0s`, Nav2 native ACK; Owner WSL2 미실행. **인증 E-Stop 아님**.

## 1. 복원한 실제 첫 실패와 교차 실행 증거

| 원본 단일 실행/소스 | 실제 결과 | 본 Task01에서 사용할 수 있는 결론 |
|---|---|---|
| S1 public [#44011055816](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44011055816), job `133797884405`, public S1 analyzer `ec059007670c0a5c1c13b0fe7d06ad1107f2e1d6`, private `966886c...` | **CM RMW source gap139.723543ms**, Observer123.527663ms, 동일 CM 입력 콜백102.456878ms, TF Advanced 함수101.682875ms, thread CPU0.322830ms, 약101.360045ms nonCPU | **TF 함수가 첫 source-gap으로 선택된 observer 구간과 겹치는 CM 콜백에서 오래 실행한 것은 기존 코드가 관측함**. 그러나 TF 함수가 *source publisher의 실제 발행 시각 간격 안에서* 언제 실행됐는지는 원본 raw가 없어서 현재 재검 불가. 101.36ms를 전부 sleep 또는 scheduler로 볼 수 없음 |
| S2 NO_GOAL [#44013676608](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44013676608), job `133806366958`, S2 source `9bcdc5cb92ff4da61efb2eba1d2fd77c30dfff96` | 공식 CM TF calls477, 실제 libc nanosleep427, 477호출에 걸친 sleep elapsed 총4399.656895ms, Nav/Loc native ACK | 공식 TF 경로에서 실제 sleep이 발생한다는 사실 **PROVEN_NO_GOAL**. S1의 **동일 source gap에서 sleep이 몇 ms인지**는 증명 불가 |
| S2 Moving [#44014107942](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44014107942), job `133807789938` | 첫 **CM RMW source >120ms pair = NOT REPRODUCED**, Observer max121.776640ms (release FAIL), source/other channel 별도 기록, Localization ACK25.000516s TIMEOUT | 해당 1회에선 S1 첫 source-gap 안에 TF sleep/runqueue를 연결할 수 없음. Observer gap과 publisher gap, 종료 ACK 오류는 서로 다른 경계 |
| C34 [#44030235323](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44030235323), 다른 private source `49f38d...` | 동일 GUI Gazebo Moving Goal, 150/300ms 게이트, exact UUID terminal+Navigation/Localization native ACK+CM exit0 **PASS** | CM120 source+Observer <=120ms **미검증**, 이전 S1/S2 root cause와 SHA 합성 금지 |

원본 GitHub artifact API 재확인: S1 #44011055816, S2 NO_GOAL #44013676608, S2 Moving #44014107942 모두 업로드 artifact **0건**. S1/S2 GitHub job **출력에는 집계 JSON은 있지만 `TF_ADV pid=... mono_start_ns=...` 개별 원시 행은 0건**. 원본 CI cleanup으로 삭제된 `actual_ros_events.jsonl`, bounded TF log, exact LTTng callback rows를 복구할 수 없으므로 **기존 S1을 새로운 시간창 계약으로 다시 계산했다고 주장하지 않는다.**

## 2. Task01에서 발견한 분석기 실제 결함 — 최초 source pair와 TF를 연결하는 방식

기존 `d06/live/g07_cycle05_cm_callback_window.py::_first_pair`는 연속 `pre_guard` RMW **source SYSTEM** 간격이 >=120ms이고 `publication_seq+1`인 메시지 **쌍**을 고른다. 그러나 반환되는 `a["t"],b["t"]`는 **Observer callback MONOTONIC** 수신 시각이다. 이는 RMW publisher가 실제 전송한 source 타임스탬프의 MONOTONIC 대응 시각이 아니다.

기존 `d06/diagnostic/analyze_first_cm_tf.py::analyze`는 그 Observer 창과 겹치는 공식 CM 콜백 안에 TF 호출이 있다는 것까지만 요구했다. 그 결과 콜백이 최초 source 쌍의 Observer 창과 20ms 겹치고, TF는 그 창 전에 이미 종료했어도 `TF_FUNCTION_DOMINANT_WAIT_CAUSE_UNPROVEN`로 분류될 수 있었다. ROOT_CAUSE/GATE_C는 원래 false였지만, 사람이 **해당 발행 공백을 TF sleep 탓으로 오인할 위험**이 있다.

세 시간 관계를 구별해야 한다.

1. RMW **publisher/source**: `rmw_source_ns` (source SYSTEM에 속한 두 샘플 사이 *간격* 계산 유효).
2. Observer callback `t`: CM 발행 메시지를 관찰한 **host MONOTONIC** 시각. source로 선정된 동일 메시지 쌍의 수신 창임.
3. LTTng 콜백과 TF `mono_start_ns/mono_end_ns`: 검증된 앵커로 MONOTONIC에 놓은 해당 **공식 CM 프로세스 PID/TID 함수 실행**.

**안전한 계산:** (2)–(3)의 시각창 교집합을 계산하여 겹치지 않은 TF 콜백 후보를 배제한다. **금지:** (1)의 절대 SYSTEM ns에서 (2)/(3)의 MONOTONIC ns를 단순 차감해 “원본 publisher gap 안의 TF sleep 구간”이라고 주장한다. sender-side, same-host, time-epoch offset+drift 증명이 없다면 `source_publication_to_monotonic_alignment_proven=false`다.

추가 한계: S2 `TF_ADV` 로그의 `sleep_ns`는 **한 TF 호출 내 모든 sleep 경과시간의 합계**다. sleep마다 정확한 시작/끝 시각이 없고, libc sleep wall에는 wake-up 뒤 scheduler 지연도 포함될 수 있다. 해당 호출이 observer 창에 완전히 들어가도 scheduler-vs-TF availability wait의 단독 인과는 **아직 false**.

## 3. RED → GREEN → REFACTOR → REVIEW

### RED (실제 공개 CI)
- 신규 `d06/tests/test_g07_cm120_task01_tf_first_source_gap_overlap.py` 3개 반례:
  - TF는 콜백 140ms 중 100ms를 쓰지만 Observer pair [12.000,12.132] 전 11.989에 종료 ⇒ `HOLD` 필요.
  - TF가 observer 창을 일부만 가로지르면 해당 함수의 집계 sleep을 publisher gap 내부 sleep으로 간주 불가.
  - TF가 observer 창 안에 nominally 있어도 **TF Buffer wait 또는 scheduler 원인은 미증명**.
- 최초 RED: [public Run #44035728070](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44035728070) / test source SHA `83186ab4333c5d4b47e7f7279834fe728a732ae1`, workflow commit `f6994ee76f8e69e0d6845f50efb21d338b4b2f12`, `completed/failure`:
```text
AssertionError: 'TF_FUNCTION_DOMINANT_WAIT_CAUSE_UNPROVEN'
    != 'TF_OUTSIDE_FIRST_CM_SOURCE_GAP_HOLD'
Ran 3 tests in 0.001s
FAILED (failures=1, errors=2)
```
- **RED는 ROS/Gazebo 실패가 아님.** 새 진단 시간창 가드가 없다는 증거.

### GREEN
- `d06/diagnostic/analyze_first_cm_tf.py`의 기존 PID/TID/콜백 메타데이터 검증과 TF interval 파서는 그대로 재사용한다.
- 동일 source pair로 선택한 **Observer MONOTONIC 창과 TF MONOTONIC interval** 간 실제 교집합을 계산.
- TF interval 교집합 0 ⇒ `TF_OUTSIDE_FIRST_CM_OBSERVER_PAIR_HOLD`, `gate_c_authorized=false`.
- nominal partial/full overlap ⇒ 위치·duration 메타데이터만 기록, `tf_sleep_in_source_gap_proven=false`, `root_cause_proven=false`, `tf_wait_proven=false`, `scheduler_wait_proven=false`, `cm120_release_pass=false`.
- ROS/TF 함수 구현, 공식 CM 동작, actual safety TTL 및 Goal runner **변경 없음**.
- 초기 GREEN [Run #44035873102](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44035873102), source `f535847cee97537280b0aae3c5f1e5ae5b7b3eca` — 신규3, 기존 S1/S2 10개 **13/13 PASS**.

### REFACTOR — 시간 영역 오인 방지
- 콜백 선정 근거와 관측 구간의 의미를 더 정확히 `tf_observer_pair_temporal_relation`, `tf_nominal_overlap_observer_pair_ms`로 표현.
- 모든 분석 결과에 `source_publication_to_monotonic_alignment_proven=false`를 명시. `tf_sleep_in_source_gap_proven=false`를 별도 보존.
- source SYSTEM ↔ observer MONOTONIC을 직접 맞췄다는 오해를 막는 **네 번째 반례** 추가.
- 리팩터링 중 코드/테스트 커밋이 순차 반영된 중간 CI [#44036298780](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44036298780)는 **구버전 테스트 기대 문자열과 신버전 결과 불일치로 FAIL**, ROS/Gazebo 오류 아님; 최종 갱신 후 재검.
- **최종 공개 GREEN** [#44036336021](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44036336021), Job `133879980030`, 정확한 tested source **`19601b688a1d4ad91e91f5f763ff3e12a7216706`**, `completed/success`:
```text
Ran 4 tests in 0.001s
OK
Ran 4 tests in 0.001s
OK
Ran 3 tests in 0.001s
OK
Ran 3 tests in 0.001s
OK
AXIA_G07_CM120_TASK01_FIRST_GAP_TF_TEMPORAL_JOIN_L0_PASS_NO_ROS_NO_GOAL
```
총 **14/14 pure unit PASS** + Python compile. **실제 Jazzy/Gazebo/NO_GOAL/Moving Goal 실행이 아님**. 기존 S2 NO_GOAL L2 성공과 실제 Moving 증거는 수정 없이 참조.

### REVIEW
- 확인한 수정은 진단기 `analyze_first_cm_tf.py`의 실제 옵저버창과 TF 호출의 교집합 검증, 안전한 메타데이터, 신규 ROS-free 반례뿐이다.
- `rmw_source_ns`와 `observer.t` 시간축 직접 차감은 **추가하지 않음**.
- 최초 source 위반의 실제 sender-side 입력/발행 인과를 직접 관찰한 것처럼 표시하지 않음.
- 공백을 설명하는 단독 원인 `TF_BUFFER_WAIT_PROVEN`·`SCHEDULER_RUNQUEUE_PROVEN` 둘 다 **false**.
- Scheduler `sched_schedstats=0`인 기존 runner에서는 runqueue counter 0을 “실제 대기 0”으로 해석하지 않음. `getrusage` 전환 횟수는 시간 분석이 아님.
- 제품 Safety Supervisor, Guard/Collision Monitor, official Jazzy Nav2, Owner TTY/PID/Goal authority, CM120/Guard150/Scan300, STOP geometry, hardware E-Stop 모두 변경 없음.
- **추가 Moving Goal 자동 실행 없음**. 과거 S2 single diagnostic Goal 소모 및 private raw artifact 부재라는 stop rule 준수.

## 4. Task01 최종 인과 판정표

| 검증하고 싶은 명제 | 확인된 증거 | 최종 Task01 |
|---|---|---|
| 실제 공식 CM Advanced TF 함수가 콜백 elapsed를 크게 차지 | S1 같은 CM 콜백의 TF101.683ms / callback102.457ms | **PROVEN_CALLBACK_LEVEL** (기존 S1 측정) |
| TF 함수가 S1의 최초 RMW **publisher source** gap 내부 정확히 존재 | S1 집계 결과만 보존, publisher source clock→host mono 엄격 대응 및 TF raw 불가 | **UNPROVEN_SOURCE_WINDOW** |
| TF 경로에 `nanosleep` 실제 호출이 존재 | S2 NO_GOAL 427 sleep calls / 477 TF calls | **PROVEN_IN_DIFFERENT_RUN_NO_GOAL** |
| S1 첫 source gap 중 TF sleep이 지배 | S1은 sleep 미계측; S2 Moving은 first source gap 자체 미재현 | **UNPROVEN_CAUSAL** |
| scheduler runqueue가 실제 최초 source gap 주원인 | CI scheduler stats disabled, 직접 thread scheduling trace 없음 | **UNPROVEN_CAUSAL** |
| C34 독립 ACK 경로가 이번 CM120 source gap을 해결 | [#44030235323](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44030235323)는 150/300ms 다른 게이트 | **NOT TESTED_FOR_CM120** |
| 수정한 신규 Task01 진단기 경계 | RED→GREEN 공개 L0 14/14, source SHA pinned | **PASS_ROS_FREE_DIAGNOSTIC_ONLY** |
| CM120 tracer-OFF release 및 Owner WSL2 | 신규 동적 시험 없음 | **HOLD** |

## 5. 다음 작업의 Stop/Go 결정

**현재 Task01은 외부 원인 증명까지 완료되지 않았다.** 기존 raw 소스/스케줄러 내부 증거가 복구되지 않는다면 Gate C를 **시작할 수 없다**. Task01 분석기의 안전한 분류 계약은 완료했으나 root cause 자체를 증명했다고 말할 수 없다.

다음 움직임에 필요한 **최소 증거**는 같은 단일 source SHA/run에서:
1. 첫 연속 RMW `source` gap>120ms, 동일 publish sequence, source/received 시스템 시계 영역과 observer mono의 검증된 clock anchor 및 송신자 clock domain readback.
2. 같은 공식 CM PID/TID의 실제 `/cmd_vel_supervised` 콜백 start/end와 그 안의 Advanced TF span, 각 실제 sleep 호출의 interval 또는 해당 source 간격 내 포함 증거.
3. wake-up 이후 runqueue 관련 kernel data가 실제 사용 가능한지 확인. CI `sched_schedstats=0`이면 `UNAVAILABLE` 처리(선점 시간 0이라고 간주 금지).
4. 원본 Scan stamp/TF availability/clock freshness와 가용성 경계, 최초 Guard latch/TTL을 같이 확인.
5. raw evidence를 덮어쓰지 않고 한정된 비공개 보관 영역에 SHA256 custody하는 실행 전 실패-차단 계약.

**현재는 이 다섯 조건을 과거 원본만으로 충족할 수 없다**. S1/S2 증거는 유효하되 서로 다른 실행의 결과를 한 first-gap으로 합칠 수 없음. 따라서 **새 Moving Goal·TF/simple-lookup 설정·source_timeout·CPU-affinity·Guard/CM TTL 변경을 하지 않는다**. 후속 진단을 별도로 승인하더라도 새로운 Goal 1회와 기존 bounded 진단기에 한정하고, 새 first source gap이 재현되지 않으면 HOLD 종료. 검증 안 된 조합을 추측해서 tracer-OFF 릴리스를 시작하지 않는다.

## 6. 경로·명령·검증 수준·소유권

```bash
# 공개 GitHub ROS-free L0에서 실제 실행한 4회 축소 테스트
python3 -m unittest discover -s d06/tests -p 'test_g07_cm120_task01_tf_first_source_gap_overlap.py' -v
python3 -m unittest discover -s d06/tests -p 'test_g07_cm120_s2_exact_tf_offcpu_join.py' -v
python3 -m unittest discover -s d06/tests -p 'test_g07_cm120_s2_actual_sleep_provenance.py' -v
python3 -m unittest discover -s d06/tests -p 'test_g07_cm120_tf_first_gap_join.py' -v
python3 -m py_compile d06/diagnostic/analyze_first_cm_tf.py

# 기존 공개 실행 원본 로그 열람 (명령 예시)
gh run view 44011055816 -R silverbjin/axia-robot-safety-ci-public --log
gh run view 44014107942 -R silverbjin/axia-robot-safety-ci-public --log
gh run view 44036336021 -R silverbjin/axia-robot-safety-ci-public --log
```

변경 파일:
- `d06/diagnostic/analyze_first_cm_tf.py` (같은 Observer 창의 TF 구간 교집합, source clock 연결 거짓 주장 방지)
- `d06/tests/test_g07_cm120_task01_tf_first_source_gap_overlap.py` (새 반례 4)
- `.github/workflows/axia-g07-cm120-task01-first-gap-overlap-l0.yml` (공개 CI ROS-free L0)
- `d06/docs/AXIA_G07_CM120_TASK01_FIRST_GAP_TF_SLEEP_SCHED_CAUSAL_REVIEW_20261117_KO.md` (교육·인계 원본)

검증: **공개 CI L0 Python unit + compile GREEN14**, 읽기 전용 GitHub 원본 logs+artifacts 재조회; **ROS Jazzy runtime / Gazebo / Owner WSL2 새 실행 없음**. GitHub Action suite만 표기하고 로컬에서 동일 명령을 실행했다고 주장하지 않음. Main/student/Instructor 소스·실행기 미변경, 병합 별도 사용자 승인 필요.

```text
AXIA_G07_CM120_TASK01_DIAGNOSTIC_GUARD=GREEN_PUBLIC_L0_14
AXIA_G07_CM120_TASK01_S1_CALLBACK_TF_WALL=OBSERVED_101_682875MS
AXIA_G07_CM120_TASK01_S1_SOURCE_PUBLISH_TF_ALIGNMENT=UNPROVEN
AXIA_G07_CM120_TASK01_S2_NO_GOAL_SLEEP=OBSERVED_427_CALLS
AXIA_G07_CM120_TASK01_S2_MOVING_SOURCE_GAP=NOT_REPRODUCED
AXIA_G07_CM120_TASK01_TF_SLEEP_VS_SCHEDULER_CAUSE=UNPROVEN
AXIA_G07_CM120_GATE_C=NOT_STARTED_CAUSE_UNPROVEN
AXIA_G07_CM120_GATE_D=NOT_STARTED_TRACER_OFF
AXIA_G07_CM120_RELEASE=HOLD
AXIA_MVP_DEMO_ACCEPTED=HOLD
OWNER_WSL2_L3=NOT_RUN
CERTIFIED_ESTOP=false
MAIN_MERGED=false
```

## 7. 최종 REVIEW 문구 정합화 / 출고 게이트 보존

리뷰 중 테스트 docstring 및 공개 workflow 이름에도 RMW publisher source interval과 host MONOTONIC Observer 수신창을 혼동할 수 있는 표현이 발견되어 **진단 의미를 보수적으로 정정**했다. 소스 발행 간격을 직접 TF 실행 구간으로 변환한다는 주장은 하지 않고, 오직 source gap으로 선택한 관찰자 메시지 **쌍의 receipt window**와 TF interval의 nominal overlap만 검사한다.

- 정적 테스트 이름·docstring 정정: `d06/tests/test_g07_cm120_task01_tf_first_source_gap_overlap.py`, commit `e43756d26ef677f3f1ba0b4baae558d1214f9135`.
- 공개 L0 workflow 이름 정정: `.github/workflows/axia-g07-cm120-task01-first-gap-overlap-l0.yml`, commit `4c9575403d06732a54235aada1abfdfa26be5716`. 새 ROS/Goal 호출이나 sensor/TF 설정 변경 없음.
- **최종 공개 CI 코드/테스트 정합성:** [Run #44036795558](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44036795558), job `133881509747`, `completed/success`, test subject commit `4c9575403d06732a54235aada1abfdfa26be5716`. 원본 stdout:
```text
Ran 4 tests in 0.000s
OK
Ran 4 tests in 0.001s
OK
Ran 3 tests in 0.000s
OK
Ran 3 tests in 0.000s
OK
AXIA_G07_CM120_TASK01_FIRST_GAP_TF_TEMPORAL_JOIN_L0_PASS_NO_ROS_NO_GOAL
```
- **REVIEW 범위:** 공식 ROS2 Jazzy CM 바이너리/TF 조회·Safety Supervisor/Guard TTL·Goal·shutdown·WSL2 Owner 동작 불변. 변경 파일 네 개의 Draft PR 패치 및 소스-시간영역 판단을 점검.
- 보고서가 첨부된 이후 Git HEAD SHA는 다시 달라질 수 있다. **실제 실행 SHA는 `4c957540...`이고, 문서 커밋이 ROS/Gazebo 실행 증거로 승격되는 것은 아니다.**

```text
TASK01_PUBLIC_FINAL_L0=PASS_14_NO_ROS_NO_GOAL
TASK01_PUBLISHER_SOURCE_CLOCK_TO_OBSERVER_MONO=UNPROVEN
TASK01_SLEEP_VS_SCHEDULER_SOURCE_GAP_CAUSALITY=UNPROVEN
TASK01_TRACER_OFF_RELEASE=HOLD
TASK01_ADD_DIAGNOSTIC_MOVING_GOAL=NOT_AUTHORIZED_NOT_RUN
TASK02_CAUSAL_PERFORMANCE_CHANGE=BLOCKED
TASK03_PUBLIC_MOVING_RELEASE=NOT_RUN
OWNER_WSL2_L3=NOT_RUN
```
