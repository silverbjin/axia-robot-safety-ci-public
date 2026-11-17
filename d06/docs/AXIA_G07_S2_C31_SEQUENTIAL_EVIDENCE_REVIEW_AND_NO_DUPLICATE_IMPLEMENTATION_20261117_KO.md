# AXIA G07 S2 → C31 순차 후속 작업: 원본 증거 재검토·중복 구현 방지 및 Go/No-Go

- 기준일: 2026-11-17 KST. 범위: **읽기 전용 원인 검토 + 기존 회귀 재사용 여부 판정**. 런타임/공식 Nav2/Guard/CM 수정, ROS/Gazebo/새 Goal 실행 없음.
- S2 공개 진단 소스/계측: `9bcdc5cb92ff4da61efb2eba1d2fd77c30dfff96`, Instructor 원본 `966886c4627deb2bb3b37111fe336eeee6b9ebb4`.
- S2 기준 Draft [Public PR #156](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/156) (진단 증거/교육용).
- 종료 독립 작업: [Instructor Draft PR #205](https://github.com/silverbjin/axia-robot-safety-instructor/pull/205), 브랜치 `fix/g07-c31-localization-shutdown-ack-evidence-20261117`, 기준 보고 HEAD `199213c6f9710bc9d6be107afa967c503a0a0ed2`.
- 기준 문서: `d06/docs/AXIA_G07_CM120_S2_FINAL_EVIDENCE_AND_CAUSAL_HOLD_20261117_KO.md`, 기존 C31 `docs/reports/AXIA_G07_C31_LOCALIZATION_NATIVE_ACK_D06_GUI_INTEGRATION_20261117_KO.md`.

## 단계 1 — S1/S2 최초 원인 대조: 원인 확정 불가, 재주행하지 않음

| 원본 GitHub Actions | 다른 세션이 측정한 사실 | 최초 실패 인과관계 수준 |
|---|---|---|
| [S1 #44011055816](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44011055816) | first CM source **139.723543ms** / Observer **123.527663ms** / 같은 CM callback **102.456878ms**, advanced TF wall **101.682875ms**, thread CPU **0.322830ms** | 같은 최초 source-gap의 **TF 함수 wall 지배 사실**. sleep vs runqueue 미측정 |
| [S2 L0 #44013410740](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44013410740) | 15 tests 및 원본 Jazzy ABI/`sleep_for` interpose **PASS**; kernel `sched_schedstats=0` | 계측 기능 증명, 첫 실패 창 증명 아님 |
| [S2 NO_GOAL #44013676608](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44013676608) | 공식 CM Advanced TF 477호출, **실제 libc sleep 427회/합계 4399.656895ms**, 네이티브 Navigation+Localization ACK PASS | 공식 TF 내부 실제 sleep의 **가능한 메커니즘 증명**. S1 첫 source-gap과 실행·PID·TID 다른 데이터 |
| [S2 Moving #44014107942](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44014107942) | 실제 Goal 1회. first source >120ms 미재현, Observer max **121.776640ms** 초과, Localization 종료 ACK Timeout25s | 동일 source-gap callback TF sleep join **UNPROVEN**, 릴리스 FAIL |

**기술 판정:** S1과 S2의 PID/TID와 clock anchor는 개별 실행 내부에서만 유효하다. NO_GOAL에서 집계된 427 sleep을 S1의 139.724ms 최초 source 지연에 할당할 수 없다. S2 Goal에서 source gap 자체가 재현되지 않았으므로 `analyze_first_cm_tf.py`의 `FIRST_120MS_RMW_SOURCE_PAIR_UNVERIFIED` 경계는 의도대로 fail closed. `sched_schedstats=0`이므로 runqueue 숫자 0은 실제 스케줄러 지연 0ms가 아니다.

기존 `d06/diagnostic/analyze_first_cm_tf.py`는 원본 first source pair → 공식 CM topic subscription/callback PID/TID → TF 동일 callback interval을 연결하는 조건이 이미 있고, `d06/tests/test_g07_cm120_s2_exact_tf_offcpu_join.py` 및 `test_g07_cm120_s2_actual_sleep_provenance.py`가 기존 fail-closed 음성 테스트다. 여기서 **두 번째 진단기/회귀 워크플로를 만들 필요가 없다**.

### 추가 비침습 검증 가능성 — read-only 의사결정

1. GitHub 실행 결과 요약과 로그만으로는 해당 최초 S1 source-gap에 없던 sleep count를 **복원할 수 없다**.
2. 같은 실행의 CM callback PID/TID, TF function wall/CPU, libc sleep requested/actual, kernel scheduler runqueue를 동시에 보려면 새로운 실행의 별도 관측이 필요하다. 현재 `sched_schedstats=0`은 직접 runqueue attribution을 차단하며, sleep elapsed에는 깨운 뒤 스케줄러 지연이 섞일 수 있다.
3. 추적기로 실제 주행 타이밍이 변하므로 **diagnostic trace-on 결과를 Gate D tracer-OFF release PASS로 간주하지 않는다**.
4. 결론: **S2 증거 고정**. 기존 원인 가설의 더 깊은 검증은 별도 승인·비교 가능한 동일 source-gap 재현 방법 없이 시작하지 않는다. 인위적으로 Goal을 반복하여 초과가 우연히 발생할 때까지 수집하지 않는다.

## 단계 2 — Localization 종료 ACK: C31 원본 회귀 사용, 원인 아직 미확정

**독립 최신 원본:** [C31 실제 Gazebo/Gazebo GUI+RViz2 one-Goal #44017286929](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44017286929), 정확한 Instructor 실행 SHA `77eb00993ab3884fe9641ad0f3668fdacf71bc1b`, 공개 워크플로 `a6a79d4ec9ecfa294d730aa0ce1e95862e7bd80f`, **overall FAILURE**.

- 단일 Goal의 CLEAR→SLOW→STOP 및 odom 이동 **0.2241m**, STOP dwell **1.015814s**, CM 메시지 최대 **146.488266ms**(기존 Guard 150ms 기준 내), Scan 최대 **215.135697ms**(300ms 내). 주행 기능의 한정 증거이지 안전 통합 PASS가 아니다.
- Navigation `ManageLifecycleNodes` ACK 수신: `response_wait_sec=3.851545`. Localization 서비스 discovery `0.004453s`, request submitted `0.004543s`, **`response_wait_sec=12.997088s`** 후 `ack_response_received=false`. 결과 `BLOCKED_LIFECYCLE_LOCALIZATION_SERVICE_TIMEOUT`.
- 실제 GitHub job log에는 `[lifecycle_manager_localization]: Running Nav2 LifecycleManager rcl preshutdown`, AMCL·map_server `rcl preshutdown`과 종료 후 `process has finished cleanly`가 남았음. 그러나 이 기록은 **SIGINT에 따른 Context 종료** 과정이며, 원래의 `manage_nodes(SHUTDOWN)` 서비스 응답을 받았다는 증거가 아니다.
- 기존 C31 `tools/p2_g07_lifecycle_service.py`, `tools/p2_g07_ordered_shutdown.py`는 `request_sent`, `response_wait_sec`, `ack_response_received`, 최초 ACK 실패를 따로 보존하도록 이미 개발. [C31 RED #44015197396](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44015197396) → [GREEN #44015268905](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44015268905) / [#44015565478](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44015565478). 새 fake service 재구현은 중복.
- 공식 Jazzy LifecycleManager 코드는 `managerCallback()`가 `SHUTDOWN`을 받으면 `shutdown()`을 실행하며, 시스템 rcl preshutdown인 `onRclPreshutdown()`은 **다른 경로**다. 근거: https://api.nav2.org/nav2-jazzy/html/lifecycle__manager_8cpp_source.html .
- 서비스 **client request sent**는 입증되었지만, **server callback entry / 내부 AMCL·map_server lifecycle state transition / response transport** 중 첫 실패 지점을 로그로 특정하지 못했다. 로그에서 서비스 콜백 진입 문자열이 보이지 않는다는 사실은 그 콜백이 호출되지 않았다는 강한 증명이 아니다.

### C31에 인계할 최소 잔여 항목 (실행하지 않은 작업)

1. 먼저 기존 `launch.log`의 서버측 `lifecycle_manager_localization` 메시지 및 같은 요청의 시간축을 읽기 전용으로 필터링하고, 부족하면 **원본 첫 service request → server callback entry/transition → native ACK response** 경계를 단일 창에서 보존할 방법만 설계.
2. 현 원본에는 그 서비스 호출의 server-side enter/end 식별자가 없으므로 `CAUSE_UNPROVEN` 유지. Nav2 내부 서비스 응답이 늦은 것인지 DDS 응답이 유실된 것인지 추정하지 않는다.
3. C31 자체 Draft PR #205에서 **기존 first-timeout pure regression**만 재사용하고 근거가 있는 1개 실패 경계만 최소 수정. 무단 13→25/40s timeout 확대, 안전 TTL/CM 설정 변경, S2 첫 source-gap과 결합 금지.
4. 재현 가능한 축소 CI RED→GREEN 이후, 통합 안전 게이트·native shutdown이 같은 source에서 충족된 경우에만 별도 승인된 실제 L2/Owner 단계 검토.

## 단계 3 — Go/No-Go 결정과 후속 범위

| 후속 게이트 | 상태 | 이번 단계의 의미 |
|---|---|---|
| S2 진단 RED/GREEN·공식 NO_GOAL 및 단일 Goal | **이미 수행 완료** | 추가 반복 불필요 |
| S2 첫 source-gap 실제 sleep vs scheduler 인과 입증 | **UNPROVEN** | 튜닝 근거 없음 |
| C31 Localization native response와 서버 내부 첫 경계 | **HOLD** | 기존 C31 회귀·소스 재사용 |
| 성능 파라미터 수정 Gate C | **NOT_STARTED** | 기존 120/150/300ms 기준 그대로 |
| tracer-OFF 동일 소스 릴리스 Gate D | **NOT_STARTED** | 전체 동일세션 L2 GREEN 부재 |
| Owner WSL2 L3 / main / Student | **NOT_AUTHORIZED** | 공개 CI 기술 PASS 범위/사용자 승인 전 진행 안 함 |

## 4. 리뷰 및 검증 수준

- 직접 다시 확인: GitHub PR #156, #205, C31 실제 작업 보고 원문, 원본 C31 L2 job log `133818145326`의 Native ACK + SIGINT/preshutdown/clean exit, 공개 Run #44014107942의 FAIL, 원본 공식 Jazzy LifecycleManager source. **새 CI 실행 또는 새 ROS/Gazebo 실행은 없었다.**
- 자동검증: 기존 S2 [#44013410740](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44013410740) 및 C31 [#44015268905](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44015268905) L0 GREEN을 **재사용**. 본 리뷰 문서의 생성/커밋은 과거 테스트의 재실행 또는 ROS PASS가 아니다.
- 보고만 추가. **새 C++/Python runtime, 안전코드, 진단기, 워크플로, 비공개 Instructor 정답, Student TODO 미변경**. Main 병합하지 않음.

```text
AXIA_G07_S2_REVIEW=COMPLETE_EXISTING_EVIDENCE_ONLY
AXIA_G07_S2_SAME_FIRST_GAP_SLEEP_SCHED_CAUSAL=UNPROVEN
AXIA_G07_C31_NATIVE_SERVICE_REQUEST_SENT=true
AXIA_G07_C31_LOCALIZATION_NATIVE_RESPONSE_RECEIVED=false
AXIA_G07_C31_SERVER_SIDE_FIRST_FAILED_STAGE=UNVERIFIED
AXIA_G07_GATE_C=NOT_STARTED
AXIA_G07_GATE_D=NOT_STARTED
AXIA_MVP_DEMO_ACCEPTED=HOLD
OWNER_WSL2_L3=NOT_RUN
MAIN_MERGED=false
CERTIFIED_ESTOP=false
```

**결론:** 사용자가 지시한 후속 순서를 원본 증거 조사·기존 회귀 확인·릴리스 판단까지 수행했다. **추가 성능 튜닝, 새 Goal, 중복 디버거 생성이 아닌 C31의 종료 ACK 서버측 첫 경계 확보**가 다음 독립된 유일한 미해결 조사 과제다.
