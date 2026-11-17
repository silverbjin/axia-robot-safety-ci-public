# AXIA G07 — CM120ms tracer-OFF 릴리스: S2 이후 통합 계획 재점검·실행 인계
작성일: 2026-11-17 KST | 유형: **기존 계획/증거 재검토 및 최소 후속 개발 계획, 제품 코드 수정 없음**

## 0. 최종 결정 (가장 먼저 읽을 것)

**CM120 tracer-OFF RELEASE=HOLD.** S1에서 동일 최초 RMW source gap과 101.683ms Advanced TF 함수 wall을 결합한 사실, S2 NO_GOAL에서 실제 libc sleep 427회를 관찰한 사실은 각각 유효하다. 그러나 두 사실은 **서로 다른 실행**에서 얻어졌고, S2 Moving Goal은 최초 publisher/source >120ms 구간을 재현하지 못했다. 동일 위반창의 TF-sleep/runqueue 기여량 및 TF availability wait의 단독 인과 **UNPROVEN**. 따라서 앞서 확정한 **원인 증명 → 단 하나 최소 수정 → tracer-OFF 동일세션 통합 L2 → Owner WSL2 단일 L3** 순서를 변경하지 않는다.

이번 문서는 별도 성능 개선 Cycle을 만들거나 수동 Goal 실행을 승인하는 문서가 아니다. 새 표준 배포·main 병합·Student 변경·Owner 자동실행 금지.

## 1. 이전에 확정·변경된 계획의 우선순위 (충돌 해소)

| 구 문서·변경 단계 | 유효한 규칙 | 후속 해석 |
|---|---|---|
| [최초 통합 인수 계획](https://github.com/silverbjin/axia-robot-safety-ci-public/blob/fix/g07-cm120-final-owner-gate-20261117/d06/docs/AXIA_G07_CM120_FINAL_INTEGRATED_ACCEPTANCE_PLAN_20261117_KO.md) | 원본 기준선/first gap, one-fix, 원본 통합 L2, Owner 1회; no TTL tuning | 릴리스 게이트 그대로 유지 |
| [공식 Nav2 아키텍처 리뷰](https://github.com/silverbjin/axia-robot-safety-ci-public/blob/docs/g07-cm120-architecture-review-20261117/d06/docs/AXIA_G07_CM120_ARCHITECTURE_REVIEW_EXTERNAL_CASES_20261117_KO.md) | `cmdVelInCallbackStamped→process→Source::getTransform→publishVelocity`; TF와 Executor 경쟁 가설 구분 | 탐색 우선순위 결정, 원인 입증은 아님 |
| [2단계 원인 우선안](https://github.com/silverbjin/axia-robot-safety-ci-public/blob/review/g07-cm120-2stage-cause-gate-20261117/d06/docs/AXIA_G07_CM120_TWO_STAGE_CAUSE_FIRST_PLAN_20261117_KO.md) | 최초 실제 gap의 TF 내부 시간/스케줄링을 분리; 확정 전엔 파라미터/안전 코드 변경 금지 | 최종 개발의 원인 선행조건 |
| [4-Gate 실행안](https://github.com/silverbjin/axia-robot-safety-ci-public/blob/fix/g07-cm120-four-gates-evidence-first-20261117/d06/docs/AXIA_G07_CM120_FOUR_GATE_ACCEPTANCE_PLAN_20261117_KO.md) | Gate A 기존 증거→Gate B 제한된 diagnostic→Gate C one-fix TDD→Gate D tracer OFF original L2/Owner | 지금 사용하는 실행 게이트 구조 |
| [S0/S1/S2 최종 증거](https://github.com/silverbjin/axia-robot-safety-ci-public/blob/fix/g07-cm120-s2-offcpu-provenance-20261117/d06/docs/AXIA_G07_CM120_S2_FINAL_EVIDENCE_AND_CAUSAL_HOLD_20261117_KO.md) | loader 확인/trace bounded + TF wall dominance + 실제 sleep 사용. 단 최초 간격의 sleep attribution 미완 | Gate A 부분 확인·Gate B 진단 충분성 **미달**; Gate C/D 아직 비허가 |
| C32/C34 별도 ACK 계열 [실제 C34 L2](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44030235323) | exact Goal terminal→Navigation & Localization native ACK→CM exit0 통합 성공 | **150/300ms 범위의 동적 종료 안정화**. CM source+Observer120ms 릴리스 성공 아님; 별도 SHA/브랜치의 증거를 현재 CM120 원본에 자동 전가 금지 |

**규칙 변경 해설:** 초반의 `base_shift_correction=false`, `source_timeout=.3`, 임의 CPU/nice/affinity, TF 기다림 최적화는 S1/S2에서 직접 인과가 검증되지 않아 **조건 없는 구현 후보에서 제외**했다. S2 후 다른 진단 Goal을 자동 반복하지 않는다. 이전 L2 성공의 부족한 raw artifacts를 원본에 있었다고 주장하지 않는다.

## 2. 검증된 수치와 절대 섞으면 안 되는 SHA

| 독립 실행 | 원본 증거 | 검증 수준 |
|---|---|---|
| C37 tracer-OFF [#43898345608](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43898345608) | CM RMW source 128.644215ms, Observer 128.318661ms | 원래 120ms FAIL; 기존 150ms hard TTL의 별개 판단 |
| Cycle01 tracer-OFF [#43981875149](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43981875149) | CM source133.658796ms / Observer131.488230ms | 단일 현장 오류 아님, release margin 재실패 |
| Cycle05 tracer-ON [#43995793080](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43995793080) | source120.172578ms / Observer120.523837ms / cmd callback81.972669ms | 정확한 함수 내부 TF 시간 정보 없음 |
| S1 tracer-ON [#44011055816](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44011055816) | source139.723543ms / Observer123.527663ms / callback102.456878ms / Advanced TF101.682875ms / CPU0.322830ms | **동일 첫 간격에서 TF 함수 wall 지배 PROVEN**. TF sleep·runqueue 원인 UNPROVEN |
| S2 진단 NO_GOAL [#44013676608](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44013676608) | TF calls477, libc sleep427, 합계4399.656895ms | 공식 CM의 TF 함수에서 sleep 발생 PROVEN; 서로 다른 호출 총합이며 S1 첫 창 원인 아님 |
| S2 진단 Moving [#44014107942](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44014107942) | 최초 RMW source >120ms **NOT_REPRODUCED**, Observer max121.776640ms, Localization native ACK25.000516s timeout | Observer-only release FAIL, source/sleep 동일창 인과 미확정 |
| C34 tracer-OFF 통합 [#44030235323](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44030235323) | genuine Moving Goal/7-channel **기존 150/300ms**, exact UUID terminal, both native ACK, CM exit0 | 실제 GUI L2 PASS이나 CM RMW source+Observer <=120ms **검사하지 않음** |

원래 S2 계측 소스 `9bcdc5cb92ff4da61efb2eba1d2fd77c30dfff96`, original Instructor `966886c4627deb2bb3b37111fe336eeee6b9ebb4`; CI 자체 정리 보고서 branch tip `0fee8ad527ea341aa641978342a0f87c3087c4ae`는 같은 **런타임 테스트 SHA가 아님**. C34 별도 Instructor 실제 테스트 소스 `49f38d7912bf8930a331577090522ccf52337fba`, C34 workflow `f26342cf72dddbb7d15ddfaf393372049d0c471d`. 독립 브랜치 간 미검증 코드 조합으로 `READY` 만들지 않는다.

## 3. 안전·설정 상수 / 오라클 (불변)

- CM RMW publisher/source 간격 **max <=0.120s**, CM observer callback 간격 **max <=0.120s**, 둘 다 **tracer-OFF 실제 Moving Goal 한 세션**에서 계측 필요.
- 독립 Guard 실제 내부 CM age/TTL **<=0.150s**, CM/Guard 메시지 전달의 기존 0.150s hard gate 유지, 첫 fail-safe latch/race 이력 포함. Scan·Odom·Clock 실제 interarrival **<=0.300s**; source/supervisor/guard 주기도 기존 안전 계약 검사.
- 공식 Waffle/Harmonic/Nav2 Goal CLEAR→SLOW→STOP, Front Slow0.75m/Stop0.40m, S02 native Contact0, zero-velocity odom dwell>=1s, 정확한 UUID Goal `CANCELED/SUCCEEDED` terminal, Cancel ACK(필요시), **두 Nav2 native lifecycle ACK와 CM exit0**, original 14-topic SQLite/sha/first trace를 동일 세션에서 확인.
- 원래 공식 `collision_monitor`: `base_shift_correction=true`, installed/live `source_timeout=1.0s`, `transform_tolerance=0.02s`(기존 AXIA overlay). 차원이 서로 다른 Scan TTL 300ms와 source_timeout 1초를 혼동하지 않는다. QoS/Guard fail-closed/stop geometry 임의 변경 금지.
- RMW SYSTEM source/received와 observer host MONOTONIC 간 epoch 차감 금지. 동일 clock domain 내부 **간격** 및 seq, pid/tid, callback identity, TF span을 엄격히 대응. 숫자가 없으면 `MISSING`으로 HOLD.
- tracer-ON 진단을 tracer-OFF 릴리스 통계로 승인 금지. CI GitHub Actions `success`만 있고 정확한 120ms 오라클이 없으면 HOLD. 실제 사용자 WSL2 GUI/CPU 동등성은 CI 성공과 구분.

## 4. 실행 가능한 후속 범위 — 이미 성공한 것을 반복하지 않는 5개의 태스크

### Task 00: 기준선/미완 증거 고정 (READ-ONLY, Goal 없음)
**입력:** 본 문서의 최초 source/Observer/S1/S2 원본 Run과 현 release 및 C34 Branch HEAD. `gh run view ... --log`, ROS 원본 변경 없이 코드/워크플로의 SHA, 7-channel 비교 구간, retained artifacts 0건, first timing/first Guard state, native ACK를 한 표로 동결.
**수행 파일:** 본 계획 문서 + 기존 `d06/docs/AXIA_G07_CM120_S2_FINAL_EVIDENCE_AND_CAUSAL_HOLD_20261117_KO.md`, `d06/diagnostic/analyze_first_cm_tf.py`, `tools/p2_g07_ci_moving_goal_oracle.py`(비공개 read-only).
**완료:** C34의 ACK 기술적 성공을 CM120 first source 병목의 해결로 추정하지 않음. 과거 NO_GOAL/실제Goal 결과를 다른 source SHA와 합치지 않음.
**현재:** 이 재점검으로 READ-ONLY 분석 완료. baseline 원문 파일은 이번 조회에서 확보되지 않아 문서-원문 완전 일치 **UNVERIFIED**.

### Task 01: 동일 첫 source gap의 원인 분리 여부를 먼저 판정 (우선순위 1)
**먼저 무실행 검토:** 기존 S1 `d06/diagnostic/cm_tf_gettransform_preload.cpp`, `d06/diagnostic/analyze_first_cm_tf.py`, S2 `d06/diagnostic/classify_tf_non_cpu.py`의 원본 누락 증거를 정리. 실제 S1 first-gap에는 libc sleep count와 runqueue 분리가 없으며 S2와 완벽한 공통 Goal trace가 없다. **현재 원인은 아직 UNPROVEN.**
**추가 Goal 전 선행 계약:** 무제한/범용 계측기 신규 개발 금지. 기존 analyzer를 그대로 활용하여 (i) **먼저 발견된 동일 CM RMW source>120ms pair**, (ii) exact upstream /cmd_vel_supervised callback pid/tid, (iii) Advanced TF entry/exit, (iv) 해당 TF 내부 actual libc sleep/cpu/context-switch, (v) TF availability·scan/odom/clock stamp의 시간창, (vi) scheduler runqueue 가능 여부를 하나의 단일 원본 기록에 묶을 수 있는지 static+NO_GOAL L0로만 검토.
**작업 결정:** 새로운 Moving 진단 Goal은 S2에서 허용된 단일 회차를 이미 소진했으므로 **자동 실행 금지**. 기존 raw 원본이 복구되거나 사용자가 소규모 **추가 1회 진단**을 명시적으로 승인하는 경우에만 후보. 기존 필터·ABI 자기검사를 L0에서 모두 통과한 새 SHA로만, 정확한 한 번 실행. first-gap 미재현이면 **CAUSE_UNPROVEN**으로 종료, 원인 낙관 승격 금지.
**원인 분류:** 동일 first gap에서 함수 sleep이 지배하고 동일 TF 시각의 변환 가용성 부족이 실증되면 `TF_AVAILABILITY_WAIT_PROVEN` 후보; runnable queue gap이 runqueue 증거로 우세하면 `SCHEDULER_WAIT_PROVEN`; output publish gap은 있으나 TF span이 미미하고 입력 콜백 간격이 먼저 벌어지면 `CM_INPUT_OR_EXECUTOR_PENDING`; source<=120인데 Observer>120이면 `DDS_RECEIVE_OR_OBSERVER_DELAY`. `sched_schedstats=0`이면 scheduler wait 0으로 보고하지 않는다. 증거 부족 시 `UNPROVEN`.
**Stop rule:** 관찰 원인만으로 타이밍 수치가 개선된 것처럼 주장/추정 설정 변경 금지.

### Task 02: 실제 증명된 원인 하나에 대해서만 TDD 최소 수정
**착수 조건:** Task01에서 하나의 동일실행 최초 위반 원인이 입증된 경우 **만**. 
- `TF_AVAILABILITY_WAIT_PROVEN`이면 공식 Nav2 `base_shift_correction` advanced/simple 선택 또는 TF availability가 어느 시각에 충족되지 않았는지 원인 경로 하나만 검토. `base_shift=false`를 **자동 채택 금지**; 먼저 scan stamp age·최대 선형/각속도×age 위치·각도 오차·STOP0.40/SLOW0.75 polygon 안전 여유를 실제 데이터로 증명. `source_timeout=1.0` 값을 근거 없이 .3/.5로 줄이거나 TTL 완화 금지.
- `SCHEDULER_WAIT_PROVEN`이면 CI에만 적용됐던 CM core isolation 및 GUI sidecar schedule 영향과 함께 단일 CPU 배치 계약 후보만 검토하되, 기존 #44028139392 CM source169.524ms 및 #44029638918 Observer RMW receive349ms 같은 **다른 층의 악화 반례**부터 검토. 단순 `taskset` 실험 반복 금지.
- `DDS_RECEIVE_OR_OBSERVER_DELAY`이면 공식 CM publisher 변형이 아니라 동일 source/received/observer delivery path의 최초 경계만 회귀 고정.
**RED:** 실측 재현 수치와 실제 정책/반례(Goal 권한, first Guard latch, stale scan, tf pose accuracy, Clock-domain negative, Cancel-before-Shutdown)를 축소 공개 CI에 넣음.
**GREEN:** 기존 Supervisor/Guard/Fault Injector 및 공식 Nav2 재사용, 1개의 source/config 라인에 국한되는 변경. RED→GREEN→REFACTOR→REVIEW→COMMIT; 개발 보고서와 SHA 고정.
**원인 미확정일 때:** `TASK02=BLOCKED_CAUSE_UNPROVEN`으로 종료. 개발 범위 확장 금지.

### Task 03: tracer-OFF 실제 공개 L2 원래 조건 검증 (정확히 한 시험)
**착수 조건:** Task02 공개 L0 GREEN, 해당 source/CI/official Jazzy runtime SHA 고정, 실행 전에 새 코드가 C34 exact UUID terminal-before-Navigation/Localization native shutdown을 **어느 private ancestry에서 어떻게 적용하는지** 별도 정적 계약 확인. S2 original Instructor `966886...`와 C34 Instructor `49f38d...`가 같다고 간주 금지. 기존 성공 C34의 150/300ms Gate를 120ms Gate로 표기 변경하는 것만으로 완료 처리 금지.
**경로:** 기존 공개 CI `.github/workflows/axia-g07-unified-gui-one-goal-l2.yml` 또는 C34 실제 L2 원샷/14-topic oracle를 재사용; 새 안전 노드/새 기능/병렬 full suite 금지. `LD_PRELOAD` TF diag, LTTng, 프로세스 sampler **OFF**; CI 정상 관찰/원본 custody 계측은 유지.
**필수 PASS:** 같은 source SHA / Goal / session에서 CM RMW source **max<=120ms** AND Observer **max<=120ms**, Guard150 및 Scan/Odom/Clock300, Supervisor→CM→Guard 전달, actual first latch NONE, CLEAR/SLOW/STOP/Contact0/odom>=1s, exact Goal terminal, Nav & Localization native ACK, CM exit0, 14-topic bag 검증. `max`가 없는 로그·artifact는 PASS가 아님.
**실패:** 최초 안전 전이 또는 첫 timing violation만 CI 회귀 RED로 환원한 뒤 한 번의 원인 수정; 동일 Owner 현장 반복 금지. 실제 L2 미실행/partial PASS => HOLD.

### Task 04: Owner WSL2 단일 최종 시연 인수 (CI Gate03 완료 **후**)
정확히 Gate03 CI passed SHA가 배포 전 후보. Owner는 공개 GitHub에 올라온 SHA pinned script를 단일 블록으로 다운로드·`bash -n`·출처 검증 후 실행, private code는 authorized checkout. 기존 WSL2 WSLg Gazebo+RViz, NO_GOAL 사전 /scan/clock/TF+PID/CPU affinity/원본 환경 검증, **수동 TTY `YES-P2-G07-GOAL` 승인** 후 한 Goal. 실제 first cm/guard age/CM 120 source+observer, 150/300 다른 안전 경계, STOP/odom dwell/Collision0/Goal terminal/Nav native ACK/CM exit0, 원본 bag/sha를 제출.
WSL2에서 새 오류가 발견되면 먼저 재현 가능한 최소 CI 회귀 RED→GREEN 편입, **동일 SHA 현장 반복 금지**. 성공이라도 인증된 하드웨어 E-Stop이 아니라 SW 정지임을 명시. `main` 병합은 사용자 승인 필요.

## 5. 금지·재검증 결정

- 완료한 S0/S1/S2 원본 진단을 다시 만들거나 원인 불명 상태에서 매개변수를 바꾼 다음 우연한 GREEN을 낚는 방식 **금지**.
- C34 실제 L2 shutdown ACK PASS와 CM120 delivery timing은 **서로 다른 검증 게이트**. 런타임 SHA를 동결한 이후 동일 세션의 결과만 통합 인수로 인정.
- 원본 실제 raw trace/bag의 artifact가 0건이었던 과거 회차를 현재 조회 가능한 것처럼 보고하지 않음. 향후 승인된 진단에서는 첫 실패 원시 증거의 제한적 SHA256 custody·보존을 실행 전에 검사.
- 공개 CI `success`에서 **원래 120ms 검증 assertion 범위가 비어 있으면** `ACCEPTANCE_READY=false`. 
- 원인 증명 전에 `base_shift_correction=false`, TF advance 변경, `source_timeout`, CPU affinity, CM/Guard TTL, 임의 timer heartbeat, 새 fake ROS status, new Goal automations 금지.
- 독립 ACK C34/Owner C33 진척은 보존하되 이번 원인 조사에서 Nav2 종료를 다시 변경하지 않음.
- 강사 정답 비공개, 학생 TODO 별도 저장소. ROS/Gazebo/WSL2 이번 문서 검토 과정에서 새로 실행하지 않았음.

## 6. 기록·검증 현황

### 재조회에 사용한 경로/명령 (읽기 전용)
```bash
# 공개 repository 원본 Read-only, GitHub CLI 권한 필요
gh pr view 156 -R silverbjin/axia-robot-safety-ci-public
gh run view 44011055816 -R silverbjin/axia-robot-safety-ci-public --log
gh run view 44013676608 -R silverbjin/axia-robot-safety-ci-public --log
gh run view 44014107942 -R silverbjin/axia-robot-safety-ci-public --log
gh run view 44030235323 -R silverbjin/axia-robot-safety-ci-public --log
```
본 재점검에서는 GitHub 앱의 비공개/공개 branch·PR·문서 조회와 기존 workflow 결과에 근거했으며 위 `gh` 명령을 사용자의 WSL2에서 직접 수행한 것은 아니다.

```text
AXIA_G07_CM120_PLAN_REVIEW=COMPLETE_DOCS_ONLY
AXIA_G07_CM120_GATE_A=S1_TF_FUNCTION_ELAPSED_DOMINANT_PROVEN
AXIA_G07_CM120_GATE_B=S2_REAL_SLEEP_MECHANISM_PROVEN_NO_FIRST_GAP_CAUSALITY
AXIA_G07_CM120_ROOT_CAUSE=UNPROVEN_FIRST_SOURCE_GAP
AXIA_G07_CM120_GATE_C=BLOCKED_CAUSE_UNPROVEN
AXIA_G07_CM120_GATE_D=NOT_STARTED_TRACER_OFF
AXIA_G07_C34_NATIVE_ACK_SCOPED_L2=PASS_SEPARATE_150_300_MS_GATE
AXIA_G07_CM120_RELEASE=HOLD
AXIA_MVP_DEMO_ACCEPTED=HOLD
OWNER_WSL2_L3=NOT_RUN
MAIN_MERGED=false
CERTIFIED_ESTOP=false
```

향후 각 태스크 완료 보고에는 파일 경로/실행명령/실제 출력/검증 수준/미검증 항목/브랜치·커밋·공개 CI Run ID를 반드시 포함한다.
