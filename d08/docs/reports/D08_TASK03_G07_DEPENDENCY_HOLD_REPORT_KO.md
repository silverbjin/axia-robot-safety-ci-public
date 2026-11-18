# AXIA D08 Task03 — G07 strict Moving dependency HOLD (2026-11-18)

## 기준
- Repo: silverbjin/axia-robot-safety-ci-public, integration branch feat/d08-unified-sensor-cm-path-20261118; base main 62e366b51c64da25ad0216328fe1e019b78e0bef; PR #166.
- D08_NO_GOAL and MOVING are distinct deliverables; no robot Moving Goal was issued by this Task.

## PLAN → RED → GREEN → REFACTOR → REVIEW → COMMIT
- Up-to-date consulted public G07 Task02 simple TF Run https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44120024711 (source 092124d288b7a758f506ed725697aeff470e2962): conclusion FAILURE. First failed job step: "RED official simple TF is not yet present" (intentional RED; NOT itself a measured Guard timing violation). Prior #44118124163 failed different SHA, and successful canary #44118141906 is not moving strict gate.
- No proven same-SHA tracer-OFF Moving Goal full strict result: CM native RMW-source + observer first gap <=120ms, Guard input age <=150ms, scan/odom/clock freshness, Goal UUID terminal, first latch, lifecycle ACK and clean exit0.
- RED/GREEN not executed in D08 because prerequisite not passed. Official Nav2, CM, Supervisor, Guard timeouts unchanged. No D08 code path authorizes Goal.
- Report to be committed; SHA PR note later.

## 판정
- D08_MOVING_E2E_ACCEPTED=HOLD; reason D08_MOVING_E2E_HOLD_G07_DEPENDENCY.
- G07 strict L2: NOT_VERIFIED / prerequisite failure; Owner WSL2 L3: NOT_RUN.
- D08 NO_GOAL Task00~02 remains independently eligible for education once verified.
- No SW Stop claim is a certified E-Stop; do not infer collision-free movement from stationary Gazebo.

## 다음
- Wait for a *new independently evidenced* full G07 moving strict source+observer+Guard+Goal/odom/Contact/shutdown PASS at one exact SHA, then separately authorize one moving Task03. No retries or TTL relaxation from D08.

## 2026-11-18 최신 G07 공개 Task03 실증 범위 재대조 (Moving 보류 유지)

- 기존 2026-11-18 문서의 G07 실패 사례는 **과거의 의도적 RED**. 최신 정확한 Public CI [Run #44223320904](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44223320904)의 `task03-public-one-formal-l2` job은 SUCCESS이며 raw artifact `axia-task03-formal-public-numeric-44223320904` #14391079934 `public_evidence/task03_formal_verdict.json`을 직접 재검토함.
- 해당 G07 **범위 한정** 실제 numeric 결론: `TASK03_PUBLIC_L2_FORMAL_EVIDENCE_PASS_SCOPED`. CM RMW-source gap max **56.642455ms**, Observer gap max **71.462708ms**, Guard 내부 CM age max **53.971531ms**, 실제 Goal UUID `99e27f7a45b04e9890b17f81dc453f20` `EXACT_GOAL_UUID_TERMINAL_CANCELED_PASS`, Goal-window native ECM Contact 0, managed Nav2 lifecycle shutdown ACK, owner runner exit0, 14-topic SQLite custody. 물리 E-Stop 인증 아님.
- **그러나 그 원본 verdict에 명시**: `axia_mvp_demo_accepted=false`, `task04_owner_wsl2_l3_accepted=false`. 실제 S02/G07 속도비·정지 dwell/새 D08 구성에 대한 **동일 moving run의** 모든 요구 항목, Owner WSL2 GUI L3 판정이 기록됐다고 볼 수 없음. 무엇보다 해당 G07 작업의 소스/런타임 World는 현 D08 기능 브랜치의 실시간 YOLO+registered RGBD+물리 Proxy World와 동일하지 않음. 다른 Run 수치를 이어 붙여 D08 Moving E2E로 승격 금지.
- 따라서 선행 G07 공개 CI에서 scoped numeric 부분 PASS가 생겼음을 인정하되 D08 Task03은 **`D08_MOVING_E2E_HOLD_G07_DEPENDENCY`** 그대로. D08 Task01/02 NO_GOAL 출고를 막지 않고, 실제 Moving Goal·cmd_vel 테스트·CM TTL 우회는 추가하지 않음.
- Task03 조건부 진입 시에는 별도 사용자 승인 후 이전 G07 owner one-shot과 동일한 실제 source/Guard/CM 증거, S02 감속 비율·정지 dwell·Contact·Goal UUID·종료 ACK를 다시 검증. 기존 scoped 수치를 이 출발점으로 재사용할 수 있지만 전체 PASS로 주장 불가.
