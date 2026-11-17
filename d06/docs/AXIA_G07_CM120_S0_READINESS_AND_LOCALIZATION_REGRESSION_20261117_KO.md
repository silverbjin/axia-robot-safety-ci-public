# AXIA G07 CM120 — S0 진단기 신뢰성·Localization NO_GOAL 개발 경과 (교육용)

## 목표와 변경 불가 계약
사용자 승인 후속 권고: ① TF 진단기 기존 첫 실패 **10만 건 이벤트 제한**/실제 CM 라이브러리 로드 미검증을 공개 CI 회귀로 고치고, ② 공식 Nav2의 Localization Shutdown 최초 timeout을 **독립 NO_GOAL 검사**. ③ 두 영역이 입증된 뒤에만 *별도 승인 후* 진단용 Moving Goal 1회를 검토. 공식 Nav2·Safety Supervisor·Guard·STOP zone·source_timeout=1.0·TF base_shift_correction=true·CM120/Guard150/ScanOdomClock300ms 변경 금지. main 병합 별도 승인.

### 기존 실제 실패 원본
- One actual C37/C05 official sim Goal public [#44007105539](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44007105539), private original `966886c4627deb2bb3b37111fe336eeee6b9ebb4`, diagnostic prior public `35abdbef803e08de14d0ffc955bf06ef478a56f0`.
- CM first RMW SOURCE GAP **138.610710ms** (>120ms), external CM gap138.523011ms, Supervisor inside gap 2 publications. Original C05 known callback wall81.973ms in different Goal. Mixing different runs/clocks forbidden.
- Prior first trace failure `AXIA_G07_C05_FILTERED_CM_TRACE_UNBOUNDED_HOLD`: 100,000 LTTng events. Prior shim pregoal ABI pass did not prove actual CM process loads it; launch log emitted `ld.so ... cannot be preloaded ... ignored` warning, actual cause/unverified scope unresolved.
- Separate post-goal shutdown `LOCALIZATION_SHUTDOWN_REQUEST_SENT_ACK_TIMEOUT` after25.000396s: Navigation ACK success, Localization ACK failure, Map Server/AMCL active. Original private `tools/p2_g07_ordered_shutdown.py::classify_localization_shutdown_failure` already produces fail-closed first-failure provenance. Root of lifecycle manager hang not yet proved.

## RED→GREEN Cycle S0-1 — bounded exactly owned callback evidence
- New RED tests `d06/tests/test_g07_cm120_s0_no_goal_diagnostic.py` commit `4e8e71850898ac5075a3ae48f98ae16d50e95a13`.
- New pure filter and /proc-maps checker `d06/diagnostic/s0_cm_diag_readiness.py` commit `4e1ef53dc375a3153c1c4308ee124be623551e49`.
- Reuse previously verified `d06/live/g07_cycle31_cm_topic_callback_identity.py`, `d06/diagnostic/analyze_first_cm_tf.py`. Exact topic `/cmd_vel_supervised` → official CM PID → subscription pointer → callback pointer. Stream all raw events without retaining unrelated ones; only limited CM topic metadata and matched C++ callback events retained. No cap relaxation or infinite memory. Multiple CM input owners/missing chain/excessive relevant events fail closed.
- Negative tests: >100,005 unrelated callback events no longer overflow, own callback bound overflow HOLD, missing/ambiguous owner HOLD, fake process maps HOLD. No ROS/Goal in test.
- Public [L0 Run #44009082369](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44009082369) **completed SUCCESS**, actual output:
```text
AXIA_G07_S0_BASELINE_RED_100K_AND_CM_LOADER_CHECK_ABSENT
Ran 4 tests in 0.041s
OK
Ran 3 tests in 0.000s
OK
AXIA_G07_S0_EXACT_CM_FILTER_GREEN4_AND_PREVIOUS_TF_JOIN_GREEN3
```
This is real public CI RED (old module missing), GREEN4+old TF join3; it **does not** prove real LTTng bt2 parser integration or that TF function was called in CM. The previous 10万 count in older workflow still exists: must replace it with this tested selector in next *approved diagnostic workflow*; no actual moving Goal now.

## S0-2 — actual NO_GOAL original official CM /proc maps, existing Localization ACK
- One-off public sealed workflow `.github/workflows/axia-g07-cm120-s0-live-loader-localization-nogoal-l2.yml` pinned original private SHA `966886c4627deb2bb3b37111fe336eeee6b9ebb4`, new public S0 source `ec059007670c0a5c1c13b0fe7d06ad1107f2e1d6` and exact Jazzy+Harmonic runtime digest `861ae1df...`.
- Uses existing `scripts/p2_no_goal_smoke_ci.sh` with `AXIA_G07_CI_SIM_GOAL_ALLOWED=0`, existing dedicated full Nav2/S02 NO_GOAL startup, official CM and original native Navigation→Localization shutdown.
- First tests existing private `tests/unit/test_g07_cycle16_first_localization_shutdown_20261115.py` verifying *the known exact* ACK timeout/first failure without expanding any timers. Existing actual real Lifecycle code unchanged.
- Builds the existing proven TF shim into /tmp only. Runs original official process tree **with** LD_PRELOAD, then reads **running collision_monitor** /proc/PID/comm + /proc/PID/maps to prove the actual shim mapping. Reads TF_ADV log if real NO_GOAL trigger calls official advanced transform. If no TF call, returns `TF_CALL_NOT_OBSERVED_NO_GOAL_GATE_B_HOLD`: do **not** invent a published command or Goal. Localized shutdown independent stage must ACK to call noGoal L2 GREEN.
- Correctness limitations: a /proc/maps mapping proves actual CM loader, **not** interception/call. If no tf event while stopped, we cannot infer TF call missing in a moving Goal or TF delay root. Also noGoal passing localization does **not** prove post-Goal localization ACK; Gate D will still require ACK same moving run.
- Raw source/log/trace remains in sealed runner, only sanitized outcome printed; no private Instructor answer or raw PID/UUID public. One-off release workflow must be removed after actual Run, even on FAIL; original C37 automatic Goal remains HOLD.

## Gate & safety policy
- S0-1 verified publicly, S0-2 real NO_GOAL pending. **No new Moving Goal approved or executed in this cycle**; no CPU/TF/Guard/scan policy changes.
- If S0-2 fails, retain exact first failure in public CI and do minimal RED→GREEN correction only if reproducible without Goal. No blind retry, no 25→60s timeout increment.
- Only after S0-2 GREEN and verified actual TF call can a *separate* authorized one-Goal diagnostic be considered. Otherwise `CAUSE_UNPROVEN` and no Gate C/D/Owner.

```text
AXIA_G07_S0_L0=RED_GREEN4_PLUS_PREV3_PASS
AXIA_G07_S0_REAL_NO_GOAL_L2=PENDING
CM120_CAUSE=UNPROVEN
CM120_RELEASE=HOLD
AXIA_MVP_DEMO_ACCEPTED=HOLD
OWNER_WSL2_MOVING_L3=NOT_RUN
CERTIFIED_ESTOP=false
MAIN_MERGED=false
```
