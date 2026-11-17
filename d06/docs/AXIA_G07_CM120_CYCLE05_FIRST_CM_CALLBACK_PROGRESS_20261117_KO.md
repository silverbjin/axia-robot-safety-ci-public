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
