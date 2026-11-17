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
