# AXIA G07 Cycle05 — 공식 CM 최초 120ms 공백 콜백 실행시간 진단 교육용 경과보고서

## 학습 목표: RMW source 간격을 C++ callback 실행시간으로 오인하지 않는다
이전 **실제** Moving Goal #43898345608에는 CM RMW source128.644215ms, #43981875149에는 133.658796ms, Observer도 120ms 초과. 그 공백 동안 Supervisor RMW 추가 발행 2건. 그러나 첫 RMW 공백은 callback 실행지연, executor 대기, TF lookup 대기의 어느 하나로 확정할 수 없다.
- Cycle04 official CM NO_GOAL #43994237080에서 /cmd_vel_supervised 구독 callback handle 1개를 처음으로 실측 식별했다. **Handle identity는 입력 callback duration의 직접 측정이 아니다.**
- 공식 Nav2 Jazzy 원본 CM·Guard/Supervisor·120ms release margin/150ms Guard hard TTL/300ms Scan·Odom·Clock TTL, Stop/Goal 권한 변경하지 않음.
- 본 Cycle의 LTTng tracing은 **과도한 관찰자 부하 자체가 지연을 만들 수 있는 진단 도구**이므로 해당 Run이 120ms 이하라도 그 수치만으로 출고 승인 금지. 실제 릴리스에는 tracer OFF 같은 SHA/원본 시나리오의 별도 통합 Green이 필요.

## 계획 및 실제 RED→GREEN L0
- 계획 `d06/docs/AXIA_G07_CM120_CYCLE05_BOUNDED_CMD_CALLBACK_PLAN_20261117_KO.md`, 계획 commit `91f80fc85047c46891f4de42a7f09de965318c44`.
- 공개 pure RED test `d06/tests/test_g07_cycle05_cmd_callback_window.py`, commit `73582e562549bc018957f863b14f60096b3499c4`.
- 공개 pure GREEN `d06/live/g07_cycle05_cm_callback_window.py`, commit `8365511c1c508034b7fdb8eddc5d06c9aa084a06`, 기존 Cycle31 topic→rcl→C++ callback handle resolver 재사용. 기존 LTTng non-Goal Cycle04 suite 함께 실행.
- Public [Run #43995108388](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43995108388) **completed SUCCESS**: 불변 C04 baseline에서 신규 analyzer missing expected RED; 수정본 3개 신규 test + 기존 Cycle04 test 4개 PASS. 원본 로그:
```text
AXIA_G07_C05_BASELINE_RED_MISSING_NEW_BOUNDARY_ANALYZER
Ran 3 tests in 0.000s
OK
Ran 4 tests in 0.000s
OK
AXIA_G07_C05_PUBLIC_L0_GREEN_3_PLUS_PREV4_NO_ROS_NO_GOAL
```
- 검증 명령: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s d06/tests -p 'test_g07_cycle05_cmd_callback_window.py' -v`; `... -p 'test_g07_cycle04_cm_metadata_audit.py' -v`. L0는 ROS/Gazebo 실제 콜백이 아님.

## 실제 공개 진단 Moving L2 — 시작 기록
- 원본 C37 공식 Gazebo Harmonic+Nav2 Waffle 단일 Goal/14-topic/S02 Contact0/Shutdown 실험과 public immutable display SHA `352ea7c2197b937e8566ba90cd4d8fff46dd9f88`, private Instructor SHA `966886c4627deb2bb3b37111fe336eeee6b9ebb4` 고정.
- 전용 CI workflow `.github/workflows/axia-g07-cycle05-cm-callback-diagnostic-l2.yml`, 개발 commit `d7bce119e3aeed084558fd956bf91beb5e853fa7`, tracing raw cleanup update `6043c6d34359edbce6c0d2a59dd5bedb11dd573d`, actual temporary release commit `27746173bdb6ea699337dd59e2d00c0a0827b067`. [Run #43995476156](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43995476156) 시작; 실제 Goal/trace 결과는 후속 확정 판정 전까지 **NOT VERIFIED**.
- LTTng metadata 3종은 모든 노드에서 기록하되 callback_start/end는 `$ctx.procname` 정확 CM 프로세스만 필터링; `vpid/vtid`와 wall/monotonic anchor를 보존하여 CM 콜백만 측정. 비공개 원본 PID, 핸들, trace bytes, UUID와 소스 코드를 공개 로그/아티팩트에 저장하지 않는다.
- official LTTng filter 문법 확인: https://lttng.org/man/1/lttng-enable-event/v2.11/ 및 https://lttng.org/man/1/lttng-add-context/.
- 각 첫 RMW gap duration은 **RMW SYSTEM source_ns의 두 연속 메시지 차이**로만 측정한다. 같은 window 선정은 Observer host monotonic callback time을 사용하며, trace의 wall epoch→mono 변환 anchor drift >=50ms는 FAIL-CLOSED.
- 정적 콜백 duration이 120ms 초과/미만인 경우에도 TF lookup이나 OS scheduling 인과를 **직접** 증명한 것은 아니다.

## 향후 분기 및 최소 정책
- 실제 callback duration이 source 120ms gap을 대부분 차지하면 공식 TF time alignment/scan freshness·STOP zone 오차 한정 후보를 설계. 그렇지 않으면 Executor/DDS queue 전달을 우선. 내부 시간·핸들·source clock 불명확하면 원인 UNPROVEN 유지.
- 이 trace Run 후 원본 안전 L2 FAIL이면 Owner WSL2 실행기 **배포하지 않는다**. 성공한 과거 C38 GUI-only/NO_GOAL은 유지; 임계값 완화·재주행 반복 없이 첫 경계만 좁힌다.
- 미검증: 실제 C05 trace Goal의 first CM cmd callback duration, 120ms untraced release GREEN, Owner L3, baseline 원문 직접 대조. 사용자 승인 전 main 병합 불가. SW Stop ≠ certified E-Stop.

```text
AXIA_G07_C05_PUBLIC_L0=RED1_GREEN7_PASS
AXIA_G07_C05_REAL_DIAGNOSTIC_L2=PENDING
CM_FIRST_CALLBACK_ROOT_CAUSE=UNPROVEN
CM_120MS_RELEASE=HOLD
AXIA_MVP_DEMO_ACCEPTED=HOLD
CERTIFIED_ESTOP=false
MAIN_MERGED=false
```

## Cycle05 실제 진단 L2 종료 — 교육용 최초 실패 및 실제 인과 증거

### 실제 공개 Run 2회 및 최초 실패 경계
- 최초 진단 CI [#43995476156](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43995476156) FAILED PRE-GOAL. 최초 실제 오류: ModuleNotFoundError: No module named 'd06' (중첩 public checkout analyzer의 PYTHONPATH 누락). 후속 FIELD_NO_REAL_GOAL_CANNOT_RELEASE는 연쇄 오류이므로 CM root cause가 아니다. 공식 Goal은 전송되지 않았다.
- 실제 중첩 public root import 및 사전검사를 추가한 공개 CI 코드 commit d35b8dbbbcc0b6d070e0ffbbe1b602b521bd5fe7; release commit f4ec8feb3f4a8047fe93bdd9ef53f82b8acb4efa. 임계값·Safety code 변경 0.
- 재검 [#43995793080](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43995793080) completed FAILURE, BUT 실제 Harmonic/Nav2 Waffle ONE Goal이 실행되었으며 CLEAR→SLOW→STOP, native STOP ACK, ordered Shutdown/CM exit0, 14-topic original/first RMW provenance 검사 통과. 유일한 terminal FAIL은 Field 120ms release margin. 다른 safety PASS를 120ms RELEASE PASS로 승격하지 않았다.

### 실제 동일 Goal에서 공식 CM callback 측정
- AXIA_G07_C05_NESTED_PUBLIC_CHECKOUT_IMPORT_GREEN_BEFORE_GOAL
- AXIA_G07_C05_LTTNG_ONLY_CM_PROCNAMES_FILTER_PREFLIGHT_PASS_NO_ROS_NO_GOAL
- AXIA_G07_C05_OFFICIAL_CM_ONLY_CALLBACK_WINDOW_TRACE_ARMED_DIAGNOSTIC_NOT_RELEASE
- AXIA_G07_C05_FIRST_CM_CMD_CALLBACK_DIAGNOSTIC status=CM_INPUT_CALLBACK_INTERVAL_OBSERVED_HYPOTHESIS_ONLY
- first_cm_rmw_source_gap_ms=120.172578; first_cm_observer_wall_gap_ms=120.523837
- matched_cm_cmd_callback_count=2; max_matched_cm_cmd_callback_duration_ms=81.972669; max_callback_overlap_first_gap_ms=81.972669
- trace_clock_domain=LTTNG_WALL_EPOCH_MAPPED_MONOTONIC; official_cm_topic_to_callback_link_proven=true
- tf_lookup_causality_proven=false; scheduler_causality_proven=false; cm120_release_pass=false
- first gap 동안 Supervisor 원본 발행 2회, upstream 최대 source coverage 49.902254ms. 이전 scheduler sampled coverage51.29244ms 2개 표본만 있어 OS ready-queue 인과 미입증.
- 원본 timing: clock105.197ms, odom107.032ms, scan205.252ms, guard74.362ms, supervisor103.508ms, upstream103.495ms, CM observer120.524ms. source120.173ms.
- 실제 field safety gate terminal failure: AssertionError: FIELD_CI_L2_PASS_LOW_MARGIN_OWNER_NOT_READY. 실제 release HOLD 유지.

### 교육용 분석: 무엇이 증명되고 무엇이 아닌가
1. VERIFIED: 정확한 공식 /cmd_vel_supervised ROS C++ 콜백 핸들을 연결해 최초 120.173ms CM RMW 발행 공백과 동일 Observer monotonic 구간에 81.973ms의 완료된 입력 callback 실행을 직접 측정했다.
2. UNVERIFIED: 그 81.973ms가 TF lookup, LaserScan point transformation, callback executor contention 중 어디에서 발생했는지는 아직 분해되지 않았다. 정확한 TF 내부 처리시간 자료가 없다.
3. UNVERIFIED: RMW source SYSTEM 간격120.173ms와 callback MONOTONIC 실행81.973ms를 단순 차감해서 나머지가 scheduling 지연이라고 주장하면 두 clock의 provenance와 발행 종단을 혼동한다.
4. TRACE OVERHEAD: LTTng가 활성화된 진단 Goal은 tracer-OFF release benchmark가 아니다. 본 Run이 120ms 미달한 것은 실제 fail이지만 원인 비가역적 의미나 safety 결론은 제한된다.
5. 교육 질문: 최초 ModuleNotFoundError와 후속 FIELD_NO_REAL_GOAL 중 어떤 실패를 CI 회귀로 만들어야 하는가? Callback이 오래 실행돼도 왜 TF 원인을 단정하면 안 되는가? 이른바 callback wall duration과 scheduler wait은 왜 서로 다른가?

### 다음 개발 게이트
- Cycle06: 기존 Nav2 source::getTransform의 advanced mode 및 공식 base_shift_correction 옵션을 검토하되 G07 sim-only STOP polygon/scan age/속도 기반 위험 경계를 먼저 L0/NO_GOAL에서 검토. 현장 안전 설정을 증거 없이 false로 변경하지 않는다.
- 그 후보의 실험 가능성이 검증된 경우에만 ONE scoped public CI A/B; 추적을 켠 이번 Run을 120ms release 기준 통과 증거로 사용하지 않는다. tracer-OFF 완전 원본 시연 시나리오에서 CM source/Observer <=120ms, Guard150ms, Scan/Odom/Clock300ms, Contact0, CancelGoal, shutdown ACK 동시 통과 시에만 Owner WSL2 단일 인수를 준비.
- 사용자 WSL2 L3 NOT_RUN, main 미병합, certified E-Stop 아님. Actual C05 diagnosis report/PR remain public, private Instructor source strictly private.

AXIA_G07_C05_L0=RED_GREEN_PASS_3_PLUS_PREV4
AXIA_G07_C05_ACTUAL_CM_INPUT_CALLBACK_DURATION_MS=81.972669
AXIA_G07_C05_REAL_DIAGNOSTIC_L2=FAIL_CM_SOURCE_120.172578MS
CM_120MS_RELEASE=HOLD
OWNER_WSL2_L3=NOT_RUN
AXIA_MVP_DEMO_ACCEPTED=HOLD
CERTIFIED_ESTOP=false

## Cycle05 최종 정리/REVIEW/COMMIT
- 일회성 공개 release 진단 Moving Goal 워크플로는 전체 L2 결과 보존 후 release 브랜치에서만 삭제, cleanup commit c10b6b27d0fbb62c92ef238732f46c6302eac9e9. 기존 C37/Unified moving HOLD 소스는 수정하지 않았다.
- 첫 CI #43995476156 NO_GOAL(최초 nested import failure), 둘째 CI #43995793080 실제 Goal·callback81.973ms 관측·120.173ms release FAIL, 둘 다 삭제하지 않고 보존한다. 새 Owner Goal 원샷 배포 금지.
