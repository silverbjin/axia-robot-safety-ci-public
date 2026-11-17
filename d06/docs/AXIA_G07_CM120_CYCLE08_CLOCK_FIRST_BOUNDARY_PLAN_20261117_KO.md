# AXIA G07 Cycle08 — CM 후보 동일 프로파일의 NO_GOAL Clock 첫 경계 증명

## 작업 성격·근거
- Cycle07 sealed public Run #43999271004: 공식 Nav2 Jazzy source_timeout=1.0 실제 소스 차이 RED1, coupled simple-TF + <=300ms freshness 설정 GREEN6. 하지만 실제 Moving attempt #43999412342에서는 Goal 전 CLOCK_READY: CLOCK_MISSING, launch PID alive, /clock 토픽 존재, ROS Clock callback 0 within90s; subsequent noGoal/14-topic failures were cascades. Root Clock producer vs ROS gz bridge vs callback unproven.
- 별도 official original NO_GOAL #43999183495: source_timeout=1.0/base_shift=true/TF .02 실제 readback, but ordered Nav2 shutdown BLOCKED_LIFECYCLE_NAVIGATION_SERVICE_TIMEOUT; not part of same Goal/Clock source. Do not mix different Run evidence.
- 이번 Cycle08은 이동 중 CM 120ms를 재시도하지 않는다. **기존 C07 official sim-only paired configuration**을 정확한 public CI NO_GOAL shared startup에서 한 번 기동하고 Clock readiness, actual parameter readback, lifecycle shutdown을 검사한다.
- C07 조건부 profile false + source_timeout0.3 원본 Guard TTL150/CM release120/Scan300 및 official Nav2 source unchanged, no Goal or /cmd_vel. New NO_GOAL diagnostic admission requires GITHUB_ACTIONS=true, ROS Jazzy, SIM_ONLY=1, G07 shared preflight+shutdown only, GZ_PARTITION axia_p2_ prefix, GoalAllowed0, additional explicit AXIA_G07_C08_PROFILE_CLOCK_NO_GOAL=1; without all, FAIL CLOSED.

## RED→GREEN→REFACTOR→REVIEW→COMMIT
1. RED: Previous exact C07 private SHA 3cdbb65ec6130ed74b28b1368246bb70f99ed423 cannot enable official coupled CM profile in NO_GOAL by policy. Add 3 tests for exact new CI-only admission, non-CI and Owner blockers, and unchanged default. RED expected 1 ERROR (or explicit false) on previous source.
2. GREEN: private tools/p4_g07_cm_sim_simple_tf.py modifies only profile admission predicate; original one-Goal rule remains untouched. private scripts/p2_no_goal_smoke_ci.sh uses same opt-in condition in preGoal actual ROS param readback. No new ROS node, no publishing, no safety TTL change.
3. Public sealed L0 RED prior source→GREEN3+prior6 and syntax; fail-closed provenance. RED/GREEN Run ID saved in educational Cycle08 report.
4. Public actual NO_GOAL Jazzy/Harmonic/Nav2 one run: reuse original .github/workflows/axia-p4-g07-owner-shared-pregoal-l2.yml, exact pinned private C08 candidate and container SHA. Do not send Goal. Explicit true CM base_shift false + source_timeout<=.300 readback before shutdown, P2 staged startup SMOKE_READY, native navigation+localization ordered shutdown ACK.
5. On CLOCK_READY fail, report first source/bridge/observer boundary not final FIELD_NO_REAL_GOAL. No retry of Moving Goal until first Clock failure regression GREEN. If NO_GOAL passes, it **does not** prove moving CM120; a trace-off original strict public moving L2 would still be needed.
6. Educational report: original error vs downstream cascading errors, exact L0/L2 test output, source/commit/Run ID, safety freshness caveat, evidence gaps and next stop rule. Commit report before cleanup of one-off release workflow. No main merge or WSL2 running.

AXIA_MVP_DEMO_ACCEPTED=HOLD; CM_120MS_RELEASE=HOLD; OWNER_WSL2_MOVING_L3=NOT_RUN; CERTIFIED_ESTOP=false.
