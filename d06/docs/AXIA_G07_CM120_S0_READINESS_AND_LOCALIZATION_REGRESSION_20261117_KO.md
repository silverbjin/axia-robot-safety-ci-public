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


## S0-2 실제 Gazebo Harmonic/Jazzy/Nav2 NO_GOAL L2 검증 완료

**Run [#44009454224](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44009454224), complete SUCCESS**. 실제 원본 SHA `966886c4627deb2bb3b37111fe336eeee6b9ebb4`, public S0 analyzer frozen SHA `ec059007670c0a5c1c13b0fe7d06ad1107f2e1d6`, original pinned image digest `861ae1df...`. Trigger release commit `764e709db957f4c6c8f83771211f8467b1dff1bc`.

실제 원본 로그(비공개 raw PID/TF trace는 공개하지 않음):
```text
Ran 3 tests in 0.005s
OK
Ran 4 tests in 0.037s
OK
AXIA_G07_S0_FIRST_LOCALIZATION_TIMEOUT_EXISTING_CI_REGRESSION_GREEN_NO_GOAL
AXIA_G07_S0_CM_PRELOAD_MAP_OBSERVED=1
AXIA_G07_S0_REAL_NO_GOAL_CM_TF_READINESS {
  "actual_tf_call_count": 337,
  "certified_estop": false,
  "goal_sent": false,
  "localization_ack": true,
  "localization_shutdown_status": "NAV2_LIFECYCLE_SHUTDOWN_ACK",
  "navigation_ack": true,
  "owner_accepted": false,
  "process_mapping_proven": true,
  "release_pass": false,
  "root_cause_proven": false,
  "runner_rc": 0,
  "startup_status": "SMOKE_READY",
  "tf_call_observed": true
}
AXIA_G07_S0_REAL_CM_LOADER_AND_LOCALIZATION_NO_GOAL_PASS
AXIA_G07_S0_TF_FUNCTION_CALLED_NO_GOAL_DIAGNOSTIC_NOT_RELEASE
AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false
```
- 실제 CM 프로세스 `/proc/<pid>/maps`에서 CI 전용 TF 계측 SO 로딩 확인, 그리고 런타임 TF_ADV 337건 기록. Shim은 `/proc/self/comm`으로 공식 CM 프로세스를 한정한다. 단, NO_GOAL TF 호출이 기록됐다는 사실이 **이전 Moving Goal의 138.611ms 최초 공백에 동일한 TF 대기가 있었다는 원인 증명은 아니다**.
- 원래 `scripts/p2_no_goal_smoke_ci.sh`의 startup SMOKE_READY, Navigation ACK, Localization ACK 및 rc=0 모두 확인. **NO_GOAL 종료 1회 성공**은 과거 C05/C37 Moving Goal의 Localization ACK timeout이 해결됐다는 보장이 아니다. 원본 lifecycle 코드/타임아웃값 수정 0건, 추가 재실행으로 PASS 승격하지 않는다.
- Live L2 전용 release workflow는 원본 실제 CI 결과 확인 후 **퇴역**. Cleanup commit `c4c5300304f89f9cc999bfdd3ec9c8a8153c63b5`. 공개 CI 성공을 이유로 기존 Moving Goal 자동 트리거를 켜지 않았다.

## S0-3 장래 단일 진단 실행기의 정적 회귀

- 과거 진단 CI의 `if len(rows)>100000`이 raw callback events를 100k 이상 메모리에 쌓다 HOLD를 만들었다. 미래용 Draft `.github/workflows/axia-g07-cm120-four-gate-one-diagnostic-l2.yml`에서 해당 loop를 `select_exact_cm_callbacks(source_rows())`로 교체하고, **이전 public 검증 소스 `ec059...`로 3개 SHA 핀**을 업데이트함.
- 과거 `ld.so: cannot be preloaded` 경고를 줄이기 위해 진단 모듈의 `LD_PRELOAD`를 워크플로 전체 shell에서 원본 `bash scripts/p2_no_goal_smoke_ci.sh` **자식 트리**에만 지정. S0 실제 NO_GOAL에서 확인한 방식 재사용. Moving Goal 진단 코드는 이번 작업에서 **실행하지 않았다**.
- 추가 RED 정적 워크플로 계약: `d06/tests/test_g07_cm120_s0_diag_runner_contract.py` commit `69972ab23f5ee9cd74ad57817da5bec5ef140005`. 과거 loop / shell-level preload / inline Python script syntax 분리.
- 마지막 공개 L0 [#44009950139](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44009950139) **completed SUCCESS**:
```text
AXIA_G07_S0_BASELINE_RED_100K_AND_CM_LOADER_CHECK_ABSENT
Ran 4 tests in 0.030s
OK
Ran 3 tests in 0.000s
OK
Ran 2 tests in 0.001s
OK
AXIA_G07_S0_FUTURE_DIAG_RUNNER_STATIC_GREEN2_NO_GOAL
AXIA_G07_S0_EXACT_CM_FILTER_GREEN4_AND_PREVIOUS_TF_JOIN_GREEN3
```
이는 **S0 pure filter GREEN4 + prior C05 TF join GREEN3 + 미래 Draft Workflow 정적 GREEN2**이며 ROS L2 전환이 아님. 현재 future moving script 자체는 L0 정적만 검증했고, 실제 TF time vs callback same window 연결은 여전히 미검증이다.

## 별도 공개 CI 변화와 증거 혼합 금지

- 병행 실행된 [Run #44008818507](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44008818507)은 *다른 pinned source*의 Moving Goal에서 Clear/Slow/STOP, Navigation+Localization ACK, 150/300ms 통합 게이트 PASS. 그러나 해당 run Observer CM max interval `0.129399543s`로 **여전히 120ms 기준 초과**. 이것을 우리 S0의 추가 Moving Goal이나 120ms release GREEN으로 계산하지 않는다.
- 실제 120ms 첫 공백 관련 원인은 계속 `CAUSE_UNPROVEN`. 사용자 승인한 기존 한 회 진단 Goal #44007105539은 재실행하지 않았다.

## 최종 REVIEW→COMMIT·미검증·다음 권한 분기

- Source paths: `d06/diagnostic/s0_cm_diag_readiness.py`, `d06/tests/test_g07_cm120_s0_no_goal_diagnostic.py`, `d06/tests/test_g07_cm120_s0_diag_runner_contract.py`, 위 2개 CI workflow, 이 보고서. **No change** to official Nav2, Instructor Safety Supervisor/BaseGuard, `tools/p2_g07_ordered_shutdown.py`, Student TODO; `main` 미병합.
- Public Draft [PR #153](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/153). L0 실제 RED→GREEN, 원본 runtime NO_GOAL L2, 하나의 shutdown ACK success 확인 및 release one-off cleanup. Trace parser/CM loader 경계 테스트의 검증 범위를 구분해 보존.
- Next Gate B Moving Goal: **별도 명시적 승인 필요**, 이때도 원래 120/150/300ms/Contact0/Cancel/Shutdown 계약 동일한 한 개 run. 이전 L2 실패 원본 재실행하지 않고 새 소스 SHA 고정·same first gap TF interval이 없으면 `CAUSE_UNPROVEN` 종료. 진단 추적이 켜진 Moving Goal은 릴리스 인수 증거로 사용 불가.
- Next Gate C root verified before single code fix. Gate D original tracer OFF complete live public CI all-layers, Owner WSL2 one final only then, main merge user separate approval. SW STOP ≠ 인증된 물리 E-Stop.

```text
AXIA_G07_S0_L0=RED_GREEN4_PLUS3_PLUS2_PASS
AXIA_G07_S0_REAL_NO_GOAL_L2=PASS
AXIA_G07_S0_CM_SHIM_PROCESS_MAPPING=PROVEN
AXIA_G07_S0_REAL_TF_FUNCTION_CALL_COUNT=337
AXIA_G07_S0_LOCALIZATION_SHUTDOWN_NO_GOAL=ACK
AXIA_G07_GATE_B_MOVING_DIAGNOSTIC=NOT_RUN_THIS_CYCLE
CM120_ROOT_CAUSE=UNPROVEN
CM_120MS_RELEASE=HOLD
AXIA_MVP_DEMO_ACCEPTED=HOLD
OWNER_WSL2_L3=NOT_RUN
MAIN_MERGED=false
CERTIFIED_ESTOP=false
```
