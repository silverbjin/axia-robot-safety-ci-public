# AXIA G07 — G10/G30 first postGoal RMW/heartbeat evidence join and native HOLD (2026-11-21)

> **RELEASE=HOLD / ROOT_CAUSE=UNDETERMINED / NEW_OWNER_RUN=PROHIBITED / OWNER_WSL2_L3=NOT_RUN / MAIN=NOT_MERGED / CERTIFIED_ESTOP=false.** This is simulation SW STOP, not a certified E-Stop.

## Frozen inputs, no duplicate changes

- Baseline `AXIA_Robot_Safety_MVP_Baseline_Scenario_Acceptance_v1_KO.md`.
- Public Draft PR #215 original `d4ec6410630f3d8eba07eff2a425d3b4e6263003`; Student Draft PR #89 `e1241a2f3cc4fe85412b68ce026c337312d56a02`. No Student changes.
- Old actual native #44907226265: Cycle1 FAIL, Cycle2 PASS. Original artifact #14708641486 SHA256 `8d03aa308034fba31b11cde740eb99cbbab1524d5d16d8e1046742866610b327`; #14708670690 SHA256 `5fb6d763eea7b7acdb09f5c0c4bebc91f9596d8b039a0e486af6c8fa1d750bf8`.
- Previous public Python #44907251974 339 PASS / 3 SKIP. Older #44902396373 GUI-present native 2/2 remains a different exact source, not a release of this SHA.
- Parallel Public #221 addresses different G25 Guard shutdown context; its L1 PASS did not establish a successful G07 native Moving 2/2. Earlier #211/#212/#213/#214 and Student #83/#84/#86/#88 evidence preserved; rejected EventsExecutor/20ms wait/Guard wake remain rejected.

## G10: what the original first exact pair proves

In #44907226265/Cycle1 first observed FSM `BOOT_SAFE→NORMAL` at host monotonic 837.924096507, **before** the first callback fault, no Guard latch observed. First Odom breach 839.368603139→839.734406805 = **365.803666ms**. Correlated Clock334.970987ms, CM callback364.794637ms, Guard355.514836ms, Supervisor358.081536ms, Scan354.546990ms. Same CM publication seq+1 RMW source interval **55.973048ms**, independent ROS received interval **55.938737ms**, original Observer RMW received interval **360.356970ms** (excess **304.418233ms**). Source publishing stall is not the first demonstrated mechanism; the original subscriber reception path is different. The exact Fast DDS native thread / transport / wait-set / OS cause is **UNPROVEN**. Callback host-monotonic and DDS/RMW epochs are never subtracted as absolute times. Session `heartbeat_max_gap_ms=364.989207` cannot establish first-window process-wide starvation, and the final safety TTL exception was not the first event.

### Minimal RED→GREEN→REVIEW→COMMIT

1. **RED** `7aeb3e16f45a6a81b79a8eb08c371e9c3752d9c0`: new `tests/test_g07_first_postgoal_rmw_heartbeat_join.py`, public Python [#44909971382](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44909971382) FAIL: `ImportError: cannot import name first_postgoal_reception_boundary`.
2. **GREEN** `509ed064d4d7645f15f4997a53a2567d68237f6c`: add pure read-only `first_postgoal_reception_boundary` to existing `d06/diagnostic/g07_first_actual_delivery_gap.py`. Public Python [#44910040287](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44910040287) **343 PASS / 3 SKIP**. Exact first Odom/CM/independent pub-seq and SAME host-monotonic first heartbeat window join, mismatches fail-closed.
3. **Native wiring + commit** `9e1ccdabf950c275271a80f0455b123d5a999741`: only existing `.github/workflows/axia-g07-original-multi-first-scan-rmw-native-l2.yml` adds allowlisted JSON/sidecar artifact `public_evidence/first_postgoal_rmw_heartbeat_join.json` and prints a numeric HOLD verdict. No Student, ROS nodes, official Nav2/CM, QoS, Executor, Goal, safety TTL, Depth OFF or Owner PIN changes. The diff against starting `d4ec641` is exactly 3 Public files (+97 +91 +36 lines). This changes the **diagnostic**, not the causally unproven DDS behaviour.

## G30 new actual native exact Public `9e1ccdab` / Student `e1241a2`

[Real Jazzy/Harmonic Moving Goal strict 2-cycle #44910120009](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44910120009): **0/2 FAIL; G30 HOLD**.

- **Cycle1** job `136863946878` FAIL before Goal. **First event** preGoal `/clock` Observer 333.329554ms >300; identical first Clock simulation-header pair (delta 3ms) independent rosbag receives in 5.902063ms. Later `/scan` Observer 693.476081ms; same Header pair delta201ms, rosbag reception197.242320ms; safety_scan 690.938396ms. Scan RMW publication sequence gap **2**, not exact consecutive seq; **DDS Reader root not proven**. First preGoal Clock violation correctly blocked any Goal. The new postGoal join returned `FIRST_POSTGOAL_EXACT_WINDOW_UNVERIFIED_HOLD` because Goal was not issued.
- **Cycle2** job `136863947100` FAIL after actual Goal. Goal EXECUTING and physical STOP fixture ACK observed; first observed FSM `BOOT_SAFE→NORMAL` at host monotonic 226.471881187; Guard latch absent. Actual postGoal Observer max(ms): Clock116.127, Odom152.425, Scan225.330, CM86.567, Guard112.025, Supervisor85.136; no postGoal TTL breach in measured window. **First final gate error:** `G07_CI_MANAGED_LAUNCH_EXIT_26S` then `G07_CI_LAUNCH_LIVE_AFTER_MANAGED_EXIT_BUDGET`. First retained process snapshot **2 sleeping processes** (`ros2_launch=1`, `other=1`); root unknown. PostGoal RMW positive gap absent, so exact join correctly `UNVERIFIED_HOLD`, not an RMW causal-root fix.
- New Cycle1 artifact ID **14710165152**, SHA256 `6f8b08e2f60ef5779254a970e378a1de0db6cfb53ea78ac19f08e814770e2ec2`; Cycle2 artifact ID **14710110383**, SHA256 `c39cac6551462e7d791e64445342ad59536950ecb3a089c15ca397f381acbbfc`. GitHub Actions artifact expires **2026-12-05**, and is not a WSL2 raw ZIP hash.
- GUI 1/1 observed on both jobs but it is **not** a safety acceptance substitute. Student Goal/CM/Guard unchanged. A full sensor/CM/Guard/Clock/Odom TTL / exact Goal Cancel / zero dwell / Nav+Loc ACK / 14-topic custody PASS **was not demonstrated 2/2**.

## Next strictly bounded work

1. Reuse existing `g07_first_scan_pair_attribution` CI regression for Cycle1's **first 333.329554ms Clock gap** vs exact bag 5.902063ms; do not redo old S1/Events Executor experiments or assert a publisher stall. Distinguish original Observer DDS reception vs rcl take and wait-set and native listener schedule only with real same-window data; the current Scan seq gap=2 prohibits exact consecutive-pair attribution.
2. Separately isolate Cycle2's retained `ros2_launch` + unknown process, actual shutdown ACK/server/parent wait ordering, without increasing 26s budget or falsely declaring shutdown complete. Reuse pending G25 issue evidence, not a speculative new shutdown manager.
3. An **actually causal** minimum change requires RED→GREEN, followed by new exact SHA actual native independent 2/2, first-transition/TTL checks and original bag. A passing Python test alone is L0, not simulation L2.
4. GUI lifetime is diagnostic. Localization STARTUP ACK timeout alone is not blocking if read-only `map_server`+`amcl` ACTIVE, actual pose and required TF are verified; Nav/Loc shutdown ACK and clean exit remain mandatory.
5. **NO NEW OWNER WSL2 `--run` RELEASE** until strict real native 2/2. Existing Owner source remains old pinned release; WSL2 L3 NOT_RUN. Main merge requires user approval.
