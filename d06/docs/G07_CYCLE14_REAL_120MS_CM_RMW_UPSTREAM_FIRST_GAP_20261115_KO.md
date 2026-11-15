# AXIA G07 Cycle 14 — 120ms 출고 여유 최초 RMW 겹침 진단

날짜: 2026-11-15. 교육용 재현·원인 좁히기 보고서. 비공개 Instructor 소스, Owner 원본은 공개하지 않는다.

**판정:** sealed L0 36/36 GREEN; 실제 Jazzy/Harmonic/Nav2+Gazebo GUI/RViz 한 Goal G07 S02 동작 범위 PASS; **CM 120ms 출고 여유 FAIL**, 실제 Owner WSL2/WSLg NOT_RUN, `AXIA_MVP_DEMO_ACCEPTED=HOLD`.

- private branch `fix/g07-field-cm-delivery-cpu-headroom-20261115` 후보 SHA `0c25c3ff6739d7824f4301cfee116cf41e0be425`
- public workflow L2 SHA `1d4ed41c230fc67b0503dbf0b4a5b8a3133101dd`
- RED L0 [43725244770](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43725244770), GREEN L0 [43725365954](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43725365954), real Gazebo L2 [43725471512](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43725471512).
- `main` 미병합, WSL2 주행 원샷 미배포, 기존 안전 HOLD·잠금·Owner 원본 보존.

## 1. 첫 실패와 가설

Cycle13 실제 L2 `43724525115`: CLEAR/SLOW/STOP, 정확 UUID Cancel, CM exit0, S02 Contact 0이 성공했으나 RMW/source·Supervisor Observer 간격 최대 약 121.4ms, CM 약 143.5ms. 150ms Guard hard TTL 내부이나 120ms 별도 출고 여유 미달. upstream이 먼저 멈춘 것인지 CM가 입력을 받고도 느린지를 **동일 RMW source clock-domain의 첫 120ms 초과 구간**에서 검사한다.

## 2. RED→GREEN 구현

- `tests/unit/test_g07_cycle14_first_120ms_rmw_margin_20261115.py`: 실제 이벤트 스키마를 닮은 비식별 RMW source ns·publish sequence fixture 3건. threshold=120ms에서 첫 CM 공백/동일 창 Supervisor coverage, 기존 150ms 별도 유지, actual Goal 종료 후 분석기 위치 및 안전 PASS 권한 없음.
- `tools/p2_g07_ci_moving_goal_oracle.py`: 기존 `cm_upstream_rmw_gap_window()`의 기본 150ms와 판정은 그대로 두고, **전달된 실제 임계치에 맞는** `CM_SOURCE_GAP_EXCEEDS_120MS`/150MS 라벨과 `threshold_sec` 값만 추가.
- `tools/p2_g07_ci_moving_goal.py`: 동일 ROS Observer의 **원본 event ledger를 목표 수행 완료 후 읽는** pure 진단. 새로운 구독·제어 publish·센서·Gazebo 이동·안전 TTL·Goal 없음. `AXIA_G07_CI_FIRST_120MS_CM_SUPERVISOR_RMW_WINDOW` 비식별 요약.
- RED L0 `43725244770`: `TEST_120MS_RMW_RC=1` (신규 3개 기대 불충족); GREEN L0 `43725365954`: `TEST_120MS_RMW_RC=0` 및 기존 모든 RC0. 36개 unit PASS, bash/compile PASS.
- L0는 ROS/Goal 미실행이다.

## 3. 실제 GUI Gazebo L2: 첫 120ms 구간

Run `43725471512` 실제 한 Goal:
- 실제 CLEAR Scan `2.03351m`, SLOWDOWN `0.746318m`, STOP `0.393452m`; pre-STOP **실제 CM age 2.570925ms**, native obstacle Gazebo pose RPC `110.796ms`.
- `AXIA_G07_CI_FIRST_120MS_CM_SUPERVISOR_RMW_WINDOW`: `status=CM_SOURCE_GAP_EXCEEDS_120MS`, **첫 CM source 공백 128.891188ms**, publication sequence gap=1, **Supervisor messages within=3**, upstream 최대 coverage gap `49.777624ms`. 분류 `CM_POST_INPUT_EXECUTION_OR_SCHEDULING_GAP_CANDIDATE`.
- 7채널 최대 Observer 수신 간격(ms): source `59.558149`, supervisor `59.575685`, CM `131.602122`, Guard `50.115547`, Scan `199.749807`, Odom `130.957043`, Clock `100.813609`.
- 첫 Guard latch **없음**, `P2_L2_SMOKE_RC=0`, 정확 Goal UUID `deae40ef36e74719ab30f18bdf0bff99` status CANCELED, Shutdown clean / CM exit0, S02 Native ECM physical positive contact=0.
- **독립 120ms 출고 게이트 실패:** `AssertionError: FIELD_CI_L2_PASS_LOW_MARGIN_OWNER_NOT_READY`; CM 131.602ms는 150ms HARD 미만이나 120ms 운용 출고 기준 초과.

## 4. 귀납적 원인 범위와 Cycle15 최소 실험

같은 구간 Supervisor가 약 50ms 간격으로 3회 발행했는데 CM 출력은 약 129ms 멈춤. **Supervisor 발행 공백은 이 첫 120ms 초과의 직접 설명이 아님**. Collision Monitor 내부 TF lookup / executor/CPU 스케줄링 또는 DDS 전송 내 지연은 아직 구분되지 않는다. 기존 RPC 동안 CM 16개 thread의 /proc 스냅샷에서 대부분 잠자는 상태이며 runnable 0~1개였지만 이는 C++ 콜백 stack 증거가 아니다.

이전 Cycle11 `transform_tolerance .02s` 단독 시도는 STOP 이전 CM 신선도 정렬이 없어서 Guard TTL 155.83ms 위반 후 실패했다. **새로운 이유가 생긴 경우에만** Cycle15에서 공식 CM G07-simulation의 `.05 -> .02s` TF 대기 상한을 현재의 **실제 fresh CM STOP-RPC 정렬과 결합**해 재검증한다. 다른 주행·Nav2·Guard 소스/센서/CM 안전 정책 변경 금지. TF 미해결 시 CM은 fail-closed STOP이어야 한다. 성공했더라도 같은 7채널 120/150/300/500ms 경계를 실측하지 않았으면 Owner 출고 금지.

**최종: Owner WSL2 ONE-SHOT NOT_RELEASED / AXIA_MVP_DEMO_ACCEPTED=HOLD.**
