# AXIA G07 CM120 — 4-Gate 단일 원인·단일 수정·통합 인수 (기능 확장 금지)

## 승인된 고정 범위
Gate A Cycle05 기존 ROS Observer 원본 `actual_ros_events.jsonl`, LTTng callback events / original safety first latch / RMW timestamps / published state 1회 재판정 → 기존 증거로 불충분할 때만 Gate B 실시간 단일 진단 Goal → 확정된 원인 하나만 Gate C RED→GREEN→REFACTOR→REVIEW→COMMIT → 추적 없는 원래 C37 Moving Goal 공개 CI 단일 통합 L2 Gate D → Owner WSL2 1회 L3; `main` 병합은 별도 사용자 승인.

기준: public `202b66eb49001e59a06adecb70dde67a457f0780`, Instructor original `966886c4627deb2bb3b37111fe336eeee6b9ebb4`, runtime `ghcr.io/silverbjin/axia-g07-runtime@sha256:861ae1df0560f991698d8967193380b1619589ba7770b5e2ca91ea4ef31f0c8e`. Original `base_shift_correction=true`, installed `source_timeout=1.0s`, TF tolerance `0.02s`; Guard 150ms, CM release 120ms, Scan/Odom/Clock 300ms, STOP0.40/SLOW0.75 unchanged.

## Gate A — 원본 사건 대응 / 준비 완료 → 판정
- Proven C05 actual Moving Goal [#43995793080](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43995793080) first output CM RMW source gap=120.172578ms, Observer gap=120.523837ms, matched actual official /cmd_vel_supervised callback elapsed+overlap=81.972669ms, same first source gap 2 extra upstream Supervisor publications, CM seq delta=1, original Guard latch not seen in this run, moving CLEAR→SLOW→STOP and ordered shutdown ACK. Actual CI release gate FAILED 120ms.
- Original private `tools/p2_l3_live_session.py` writes per-channel `actual_ros_events.jsonl` with supervisor/pre_guard RMW source/received/sequence. `tools/p2_g07_ci_moving_goal_oracle.py` aligns source relative gaps only and `d06/live/g07_cycle05_cm_callback_window.py` aligns LTTng callback entry/exit to observer MONOTONIC.
- Official Nav2 source: `CollisionMonitor::cmdVelInCallbackStamped()→process()→Source::getData()→Source::getTransform()→nav2_util::getTransform()→publishVelocity()`; `publishVelocity()` can stop emitting ZERO after `stop_pub_timeout`; this is not necessarily CM starvation. Current first-gap is active moving Goal, no STOP suppression proven.
- GitHub Actions Run #43995793080 original downloadable artifacts **0**. Private runner post-job cleanup removes original raw JSONL/LTTng. Only sanitized aggregates in immutable logs. **Cannot pair exact per-message input→callback→output or TF entry/end using log summaries. Gate A=FIRST_GAP_CONFIRMED_ROOT_CAUSE_UNPROVEN.**
- Do not infer TF wait from callback wall 81.973ms or scheduler wait from 120.173-81.973. Reconstruct exact per-message only if raw evidence subsequently identified; otherwise Gate B.

## Gate B — 최소 진단, 조건부 단 한 번의 Goal
- Pre-goal public L0 compile and load check **before** enabling Goal. Prefer a bounded CI-only userspace shared-library symbol interceptor of exact official exported `nav2_util::getTransform` advanced overload, no official file patch, no Privileged BPF/uprobe. Existing Cycle05 userspace LTTng on real CM C++ input callback; bounded interceptor saves only PID/TID, steady clock entry/end, thread CPU time, success flag, no raw positions/secrets.
- CI-only `LD_PRELOAD` attached to the original source-pinned C37 runner, and CI-only `GITHUB_ACTIONS`/simulation scope, actual original official CM and source/Goal/Guard unchanged. **Diagnostic-only** trace overhead, no release-green claim. Build/loader/link symbol/publisher contract preflight failure => stop before Goal. No duplicate GOAL retries for a software defect, fix via L0.
- Measure TF interval inside exact C05 observed CM input callback vpid/vtid/time window and first RMW source gap using original Observer. No timestamp cross-subtractions (RMW SYSTEM gap calculated source-to-source, callback+diagnostic MONOTONIC). Require valid matched complete TF intervals and one Goal. If marker missing or ambiguous => `CAUSE_UNPROVEN`, STOP, no owner.
- TF function wall duration could itself include preemption; compare CLOCK_THREAD_CPUTIME_ID to wall but CPU delta alone does **not** distinguish waiting TF from thread descheduling. Only claim `TF_FUNCTION_DOMINANT` when it genuinely explains measured callback timeline; `SCHEDULER_WAIT_PROVEN` needs actual scheduling trace (not in current scope). Otherwise `CAUSE_UNPROVEN`. Gate B result itself never grants CM120 release.

## Gate C — proven one cause only
- `CAUSE_PROVEN` only: fail-closed reduced test RED on first timing boundary → one minimal source/config change GREEN → REFACTOR→REVIEW→COMMIT. No mixed `source_timeout=0.3` + `base_shift=false` experiments.
- If TF path is proven causal, first check original TF publishing cadence and advanced vs simple semantic safety, do not remove temporal correction without motion error/scan stamp age/STOP geometry proof. Otherwise fix only confirmed Executor/RMW path.
- Not proven => `C_NOT_STARTED_CAUSE_UNPROVEN`.

## Gate D — same-source original release CI and Owner
- Actual original Waffle/Nav2/Harmonic one Goal, tracer OFF, no diagnostic wrapper. Same run simultaneously require CM RMW source AND Observer max<=120ms, Guard actual internal <=150ms, Scan/Odom/Clock interarrival<=300ms, CLEAR→SLOWDOWN→STOP, S02 native contact0, native STOP+CancelGoal ACK, odom ZERO dwell>=1s, Nav2 Navigation+Localization lifecycle ACK + CM exit0 and 14-topic evidence.
- First `CLOCK_MISSING` / `BLOCKED_LIFECYCLE_NAVIGATION_SERVICE_TIMEOUT` triggers separate **minimal** public CI regression RED→GREEN rather than blindly running same Goal again. CI PASS only for verified same Goal scenario, and ONLY THEN prepare one SHA-pinned Owner WSL2 bootstrap. Main merge user approval only.

## 각 단계 산출
Branch `fix/g07-cm120-four-gates-evidence-first-20261117`. Paths/exact SHA/Run ID/raw proof status, first failed boundary, C05 evidence, verification level, unverified items and authorized next gate recorded in `d06/docs/AXIA_G07_CM120_FOUR_GATE_PROGRESS_20261117_KO.md`. Student TODO and private Instructor unchanged unless actual fix verified. SW Stop is NOT certified E-Stop.
