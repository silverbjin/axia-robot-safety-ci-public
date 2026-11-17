# AXIA G07 — S2 종료 및 후속 대화 인계문서 (2026-11-17)

> **기준 대화:** `05_P4_AXIA_G07_UNIFIED_MVP_4`  
> **대상:** CM120ms 첫 발행 간격 초과의 TF off-CPU 원인 분리(S2). **P4 S02 ECM Contact 시나리오와 별개다.**  
> **결론:** S2 진단 구현 및 제한된 실증 **완료** / S1 첫 실패 창의 정확한 원인 **UNPROVEN** / `AXIA_MVP_DEMO_ACCEPTED=HOLD`.

## 1. 현재 고정된 GitHub 기준선

- 공개 CI: [silverbjin/axia-robot-safety-ci-public](https://github.com/silverbjin/axia-robot-safety-ci-public), 브랜치 `fix/g07-cm120-s2-offcpu-provenance-20261117`.
- 본 인계 작성 직전의 조사 기준 HEAD: `585fa8870c5df6292490df7c67b806ab22e0d649`(S2 실제 검증 결과 기록). 이 파일/최종 보고서 추가 이후에는 HEAD가 달라질 수 있으므로 **추가된 문서 커밋을 실행 검증 SHA로 혼동하지 않는다**.
- [Draft PR #156](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/156) — S1 진단 브랜치를 기반으로 열려 있으며 **미병합**.
- S2 실행에 사용한 변경 불가 공개 계측 SHA: `9bcdc5cb92ff4da61efb2eba1d2fd77c30dfff96`.
- 실제 NO_GOAL/Moving CI에서 불러온 비공개 Instructor 원본 SHA: `966886c4627deb2bb3b37111fe336eeee6b9ebb4`. 비공개 저장소 원본/Student/main은 이번 S2 작업으로 변경하지 않았다.
- 이 단계의 안전 범위: 공식 Nav2/Collision Monitor/TF 함수 구현, 기존 Safety Supervisor/Guard, STOP·SLOW 지오메트리, 120ms 릴리스 목표, 150ms Guard TTL, 300ms Scan/Clock/Odom TTL을 **수정하지 않음**. LD_PRELOAD는 CI 시뮬레이션에서만 진단용.

## 2. 중단되었던 정확한 지점과 복원된 결과

S1의 공식 실제 Moving Goal [#44011055816](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44011055816)은 동일 이벤트 창에서 CM RMW 첫 source gap **139.723543ms**, Observer **123.527663ms**, 공식 CM callback **102.456878ms**, Advanced TF 함수 wall **101.682875ms**, 동일 스레드 CPU **0.322830ms**를 관측했다. 차이 **101.360045ms**의 구성은 S1 당시 불명확했다.

S2에서는 스레드별 `getrusage(RUSAGE_THREAD)` 문맥 전환 수, 조건부 `/proc/thread-self/schedstat` runqueue, 공식 Advanced TF 함수 안의 실제 `nanosleep/clock_nanosleep` 호출 횟수 및 경과시간을 계측했다. 원래 공식 함수 호출은 그대로 `RTLD_NEXT`에 위임한다. CI 커널 `sched_schedstats=0`은 runqueue 수치 **UNAVAILABLE**이며 0ms 선점의 증거가 아니다. 커널 옵션을 변경하지 않고 libc sleep 관찰로 보완했다.

| 검증 | 불변 원본 | 결과와 허용 해석 |
|---|---|---|
| L0 RED→GREEN/원본 Jazzy ABI | [#44013410740](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44013410740) | **SUCCESS**, 5+4+3+3=15 시험, 실제 C++ `sleep_for` interposition 확인, NO_GOAL |
| 공식 CM NO_GOAL L2 | [#44013676608](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44013676608) | **SUCCESS**. CM 프로세스 shim 매핑, TF 함수 477회, 내부 실제 sleep 427회, **총 4399.656895ms**(477회에 걸친 합), Goal 없음, Navigation/Localization ACK, rc0 |
| 공식 단일 Moving Goal L2 | [#44014107942](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44014107942) | **FAILURE**. 첫 CM **source** gap >120ms 비재현 → 같은 실패창 TF/sleep 결합 실패. CM **Observer** 최대 **121.776640ms** 별도 위반. Localization SHUTDOWN 요청 후 25.000516s ACK 타임아웃 |
| Goal 부수 관측 | 위 단일 Goal | CLEAR→SLOW→STOP, 이동 약 0.1921m, odom 정지 dwell 1.015s, Goal CANCELED. 그러나 원본 14-topic/Contact0/안전 채널 통합 인수 및 Guard 내부 age는 PASS로 승격 금지 |

**중요:** NO_GOAL의 427회/4399.657ms는 과거 S1 최초 139.724ms source 위반창에서 측정된 값이 아니다. libc sleep 경과시간에도 재스케줄링 지연이 섞일 수 있다. 해당 첫 창의 TF poll sleep과 runqueue 정량 분해, CM120 실패의 우세 원인은 **UNPROVEN**이다.

## 3. 재개할 때 읽을 정확한 파일

- `d06/docs/AXIA_G07_CM120_S1_OFFICIAL_NAV2_RESEARCH_AND_SINGLE_DIAGNOSTIC_20261117_KO.md` — S1 실제 first-gap 원본.
- `d06/docs/AXIA_G07_CM120_S2_OFFCPU_CLASSIFICATION_PLAN_20261117_KO.md` — 허용 계측/금지 변경 범위.
- `d06/docs/AXIA_G07_CM120_S2_OFFCPU_PROVENANCE_PROGRESS_20261117_KO.md` — RED/GREEN, 세 가지 실행 결과 및 첫 실패 상세 원문.
- `d06/docs/AXIA_G07_CM120_S2_FINAL_EVIDENCE_AND_CAUSAL_HOLD_20261117_KO.md` — S2 최종 결론과 의사결정.
- `d06/diagnostic/cm_tf_gettransform_preload.cpp`, `classify_tf_non_cpu.py`, `analyze_first_cm_tf.py`.
- `d06/tests/test_g07_cm120_s2_offcpu_classification.py`, `test_g07_cm120_s2_actual_sleep_provenance.py`, `test_g07_cm120_s2_exact_tf_offcpu_join.py`.
- 실제 워크플로: `.github/workflows/axia-g07-cm120-s2-offcpu-capability-l0.yml`, `axia-g07-cm120-s2-real-nogoal-sleep-probe-l2.yml`, `axia-g07-cm120-s2-one-diagnostic-moving-l2.yml`.

## 4. 후속 대화의 작업 경계

1. **S2 재작업/Goal 반복 금지.** 1회 Moving Goal을 이미 사용했다. 원본 LTTng trace/TF 이벤트는 CI 종료 시 정리되었고 [Goal Run #44014107942](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44014107942)의 다운로드 가능한 artifact는 0건이다.
2. 원인 논의가 계속 필요하면 S1/S2 **서로 다른 run을 억지로 합치지 말고**, 먼저 현존 원본과 도출 가능한 근거만 비교하는 읽기 전용 리뷰로 시작한다. 최초 gap과 동일 창의 sleep/scheduler 구분을 포착할 독립적이고 비침습적인 방법을 검토할 수 있으나 **새 Moving Goal/성능 튜닝은 별도 명시적 결정 전 금지**.
3. Navigation ACK는 성공하였으나 Localization 종료 ACK는 실패했다. 이 실패는 **Observer 121.777ms의 원인으로 간주하지 않는다**. 필요 시 별도 종료 경계의 최소 회귀로 관리.
4. 다음 성능 수정 `Gate C`와 tracer-OFF 동일 소스 릴리스 측정 `Gate D`는 **NOT_STARTED**. `CM120_RELEASE=HOLD`, `OWNER_WSL2_L3=NOT_RUN`, `AXIA_MVP_DEMO_ACCEPTED=HOLD`, `CERTIFIED_ESTOP=false` 유지.
5. S2 Draft PR #156은 진단·교육용으로 유지, main 병합/학생 배포/Owner 실제 주행 승격을 하지 않는다.

## 5. 다음 대화에 붙일 실행 지시

> `AXIA_G07_CM120_S2_TO_NEXT_CHAT_HANDOFF_20261117_KO.md` 및 `AXIA_G07_CM120_S2_FINAL_EVIDENCE_AND_CAUSAL_HOLD_20261117_KO.md`를 기준으로 S2는 계측·보고 완료(원인 미확정)로 동결한다. 기존 S1/S2 첫 실패 자료를 보존하고, 더 이상 Goal을 반복하지 않는다. 다음 기술 결정은 동일 source-gap 실패 창에서 tf2 sleep과 scheduler wait를 구분할 수 있는 *비침습적 검증 가능성*과 Localization ACK 타임아웃의 별도 처리 여부부터 평가한다. 안전 수치·공식 Nav2/CM 구현 변경과 Gate C/D, Owner 주행은 승인 전 시작하지 않는다.`

**인수 판정:** `S2_DIAGNOSTIC_WORK_COMPLETED=true`, `S2_CAUSAL_CLASSIFICATION_PROVEN=false`, `S2_RELEASE_ACCEPTED=false`.
