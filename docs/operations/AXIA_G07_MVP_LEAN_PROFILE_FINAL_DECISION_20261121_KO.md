# AXIA G07 — MVP 기능 동결 및 경량 프로필 1회 검증 최종 판정 (2026-11-21)

## 0. Executive decision

**Educational G07 baseline `jrCIgoGl` = ACCEPTED (historical original evidence preserved). NEW lean native candidate = HOLD / 0-of-2; no Owner WSL2 release.**
This report explicitly stops speculative middleware/GUI/sensor-rate experiments and avoids expanding the MVP.

The baseline `AXIA_Robot_Safety_MVP_Baseline_Scenario_Acceptance_v1_KO.md` (2026-11-01) scopes ROS 2 Jazzy, Gazebo Harmonic, TB3 Waffle, official Nav2 + Collision Monitor, self-built Supervisor/Fault Injector/Verifier, software stop NOT hardware-certified E-Stop. RGB-D real-time is **P5 optional**, not prerequisite to G07 LiDAR S02.

Preserved actual WSL2 educational acceptance: `docs/operations/AXIA_G07_TASK04_JRCIGOL_OWNER_MVP_ACCEPTANCE_20261120_KO.md`; exact observed CLEAR→SLOW→STOP, same UUID Goal Cancel, odom ZERO 1.029446s, Nav/Loc ACK, raw 14-topic bag 50,172 messages, derived 21/21 PASS and Scan max253.822ms. That is a *scoped educational acceptance*, NOT new code SHA 2/2 safety reliability or certified E-Stop.

## 1. Reuse and scope freeze

- Public parent Draft PR #215 `diag/g07-first-scan-rmw-exact-native-20261121` base `ec8f5620bc2979525c7d8b9daa4d9df160850678`, previous Native #44910120009 **0/2**.
- Public **new Draft PR #228**, branch `perf/g07-lean-native-no-heavy-probe-20261121`. Exact actual native workflow source `233623e900893cdf84103558e50ecfc16a77918b`; latest L0 test source `a7c087c3701adb2502843a5647290fb2f1c386a0`. Student runtime remains **unchanged** at `e1241a2f3cc4fe85412b68ce026c337312d56a02` (Draft PR #89).
- Files changed against parent: `.github/workflows/axia-g07-original-multi-first-scan-rmw-native-l2.yml`, `tests/test_g07_lean_native_profile.py`, `tests/test_g07_first_scan_rmw_evidence_export.py`. No ROS runtime source, Publisher, Guard, CM, TF, Goal, LiDAR SDF, world, main, or Owner release script altered.
- Lean settings: `AXIA_G07_OBSERVER_IO_PROBE=0` (removes optional callback I/O measurements, 20ms heartbeat, stack capture) and CI independent read-only CM DDS receiver disabled. Optional evidence classifiers still output HOLD when inputs absent; this is *expected absence*, not a new timing PASS or a bypass of safety protection.
- Baseline still uses original `MultiThreadedExecutor(num_threads=2)`; `AXIA_G07_EVENTS_EXECUTOR_AB=0`, bounded wait and Guard wake candidates = 0. `AXIA_G07_DEPTH_SENSOR_ENABLED=0`, actual 10Hz G07 LiDAR temporary SDF overlay and `/safety/scan`, original CM120/Guard150/Clock/Odom300 and safety freshness remain unchanged. Existing 14-topic raw bag and Gazebo Contact witness stay.
- **No new RGB/Depth optimization code:** G07 named depth sensor already removed in session-local SDF (installed upstream remains intact), D08 already has optional 30→10Hz RGB-D configuration, not an essential G07 input. G07 LiDAR upstream 5Hz was previously adapted to 10Hz to maintain Scan300; reverting to 5Hz would shrink the latency margin and was explicitly NOT attempted. No unsupported performance gain is claimed.
- Native GUI is preserved as a diagnostic client because old headless experiments failed; GUI appearance is not a formal safety PASS gate.

## 2. Actual RED→GREEN→REFACTOR→REVIEW→COMMIT

- RED test addition commit `86ca7cb088bd185f025bfa8ccaea0d84afdd1ce2`, [public Python #44912676862](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44912676862): **2 FAILED, 343 PASSED, 3 SKIPPED**. The old workflow had optional probe=1 and no lean branch.
- Narrow test sentinel correction `661919cf98ea60e099f696839f1ac5bc30a6d90f`.
- GREEN implementation `233623e900893cdf84103558e50ecfc16a77918b`, minimal existing workflow toggles and shell guard for independent diagnostic receiver. No new ROS entities or runtime modules.
- Existing static tests still required the old diagnostic probe=1 unconditionally; public L0 #44912775473 **2 FAILED, 343 PASSED, 3 SKIPPED**. This was a **test assumption mismatch**. Corrected only the two tests to demand either explicit lean probe0 + independent off, or default diagnostic probe1; `a7c087c3701adb2502843a5647290fb2f1c386a0`.
- Final public full Python [#44912852034](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44912852034): **345 PASSED, 3 SKIPPED in 5.15s**; Runner Canary #44912851961 PASS.
- CI command: `python -m pytest -q -ra tests --junitxml=results/junit-public.xml`. Native workflow executes `python3 -m unittest discover -s tools -p 'test_g07_scan_wall_pregoal.py' -v`, plus original real Gazebo/Goal/CM/Guard checks.
- Code review: 3 paths only; no safety control changes. No evidence of increased reliability or runtime speed from 345 Python tests. Commit/review does NOT override real L2 failure.

## 3. Fresh actual Gazebo Native result — exact workflow SHA

[Real Jazzy/Gazebo Harmonic native #44912769355](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44912769355), actual public `233623e900893cdf84103558e50ecfc16a77918b`, Student `e1241a2f3cc4fe85412b68ce026c337312d56a02`:

**Cycle1 / job 136871887418: FAIL BEFORE GOAL.**
- Lean independent receiver disabled sentinel observed; RViz and Gazebo windows both seen.
- First pre-Goal `/clock` callback interval **334.256845ms >300** (sim header progressed **330ms**), `/odom` max **338.378592ms**.
- Same first `/scan` header sim pair **99ms**, original RMW source interval **100.063306ms** but original RMW received interval **335.960754ms**, callback **334.007205ms**; consecutive RMW publication seq gap=1. This localizes an original-subscriber reception timing gap, **does not prove** Fast DDS/Executor/OS root or publisher stall. `/safety/scan` callback **334.040574ms**. First failure is `SCAN_PREFLIGHT_CLOCK_ODOM_INTERVAL_BREACH`, **no Goal sent**.
- Full preGoal interval RTF estimate **0.999418** does not disprove the first interval violation; neither session heartbeat maxima nor the shell rc3 are the first cause.

**Cycle2 / job 136871887245: FAIL AT CLEAN SHUTDOWN.**
- Lean independent receiver disabled sentinel observed; Gazebo/RViz windows both seen.
- Native moving runner **rc=0**, preGoal Scan header continuity PASS. PostGoal numerical observer max (ms): Clock **103.315437**, Odom **141.167648**, Scan **193.040810**, CM preGuard **59.255521**, Guard **59.660767**, Supervisor **60.391726**, supervised **60.221774**; no first postGoal TTL breach in this observation window. First FSM observed `BOOT_SAFE→NORMAL` at host monotonic **471.898595180**, with no Guard latch.
- External strict job **FAIL**: real Supervisor child **exit1** after shutdown. Exact stack `rclpy.node._get_info_by_topic` → `Failed to get information by topic for publishers: rcl node's context is invalid`. This is **not** a moving Goal safety control failure demonstrated by this first exception; existing `p2_shutdown_context.py` WaitSet/publish shutdown classifiers did not classify this specific graph-query message. **No speculative runtime hotfix** in this lean experiment.
- In job same-session shutdown evidence Nav2 request/response reported ACK with response duration **2.406499s**; exact full child clean exit gate FAIL. Completion must not be reported as PASS.

**Aggregate: NATIVE 0/2 FAIL → RELEASE HOLD.** The additional probe being OFF is a verified fact; **an improvement in CPU/RAM, WSLg RTF, source→receive latency, or repeatability is NOT proven**.

## 4. Immutable artifact custody

- Cycle1 artifact **#14710541622**, ZIP SHA256 digest `05d087c83df87bd94329adb984030cfebd8d2da71b6cb63aab553d62625fa786`, size 9,375 bytes.
- Cycle2 artifact **#14710771455**, ZIP SHA256 digest `cf0bc9d6fce65e0d8ff768cc0cb4feab4c31fcac1a9026a68b3506c8aa06e111`, size 10,710 bytes.
- Both public artifacts expire **2026-12-05**. Never post instructor private bag or personal WSL2 paths publicly. These GitHub artifact digest values are not WSL2 user file hashes.

## 5. MVP stop rule / deliverable state

**STOP extending the runtime.** This experiment is an explicitly rejected release candidate, not an accepted new pin. Keep educational `jrCIgoGl` baseline intact and reusable (21/21 scoped actual WSL2 acceptance). Do **not** flip a failing strict 300ms/120ms/150ms or child exit0 gate to PASS merely to obtain a green badge. Do not add a new executor, Planner, camera/Depth stream, DDS witness, worker or ROS node.

If a **new** fully strict Owner release is explicitly required later, resolve only the first reproducible preGoal Clock/Scan boundary and independently narrow the already witnessed post-shutdown Supervisor graph-query invalid-context race, with RED→GREEN and actual same-SHA 2/2. This is a separate constrained defect-correction decision; no open-ended G10/G30 escalation in this MVP performance branch. No automatic re-running WSL2 Goal.

**Status:**
- G07 educational MVP `jrCIgoGl` — historically scoped ACCEPTED, preserved.
- New lean CPU load improvement — UNVERIFIED.
- New G30 strict real Gazebo — 0/2 FAIL / HOLD.
- New WSL2 Owner `--run` — NOT_RELEASED / L3_NOT_RUN.
- Public #228 Draft open; Public #215 and Student #89 unchanged. All main branches **NOT_MERGED** by this change.
- Safety STOP is software simulation, **CERTIFIED_ESTOP=false**.
