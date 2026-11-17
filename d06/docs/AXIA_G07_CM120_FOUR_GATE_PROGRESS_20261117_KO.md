# AXIA G07 CM120 — 4-Gate 원인 우선 개발·디버깅 교육용 경과보고서

## Gate A — 최초 실패 증거 재판정 [완료: 부분 증명]
- Baseline original private Instructor SHA `966886c4627deb2bb3b37111fe336eeee6b9ebb4`, public original C05 tool `202b66eb49001e59a06adecb70dde67a457f0780`, same actual Gazebo Harmonic/Jazzy Nav2 one-Goal [Run #43995793080](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43995793080).
- Live first CM `/cmd_vel_pre_guard` RMW publisher source gap **120.172578ms**, external Observer gap **120.523837ms**, exact real official `/cmd_vel_supervised` C++ callback handle wall elapsed / overlap **81.972669ms**. Two more upstream Supervisor source messages in that gap, CM output seq delta=1. This is *not* a direct per-message input→callback→output pairing.
- The original private `tools/p2_l3_live_session.py` records the observer's `supervised`, `pre_guard` RMW MessageInfo `rmw_source_ns`/`rmw_received_ns`/`rmw_publication_seq`, and the original `tools/p2_g07_ci_moving_goal_oracle.py` compares within-domain gaps. Live actual logger `actual_ros_events.jsonl` existed in the runtime but is absent from Actions artifacts (**0 artifacts** on Run #43995793080); original cleanup deletes local trace. GitHub job log retains only aggregate first boundary, not raw per-message records. Cannot reconstruct exact 1:1 pairing offline. **Gate A=FIRST_CM_GAP_CONFIRMED_ROOT_CAUSE_UNPROVEN.**
- Original official Jazzy `nav2_collision_monitor/src/collision_monitor_node.cpp` invokes `cmdVelInCallbackStamped → process → source->getData → publishVelocity`. `src/scan.cpp` invokes `Source::getTransform`; `nav2_util::getTransform` advanced overload uses source and target times. CM zero publication may be suppressed after `stop_pub_timeout` when already stopped. C05 first 120ms occurred during actual moving window; no independent evidence ZERO suppression caused that first gap. Do not attribute to it.
- First **actual** Gate A verdict: source RMW publish gap proven, exact CM callback duration is a large possible contributor, TF call wall/CPU/scheduling/other processing time unmeasured. No parameter tuning authorized, `AXIA_MVP_DEMO_ACCEPTED=HOLD`.

## Gate B — bounded diagnostic, no official production source changes
- User authorized **one** exact pinned public diagnostic moving simulation Goal only **after** a NO_GOAL L0 ABI preflight proves installed official advanced `nav2_util::getTransform` symbol can be transparently delegated by a CI-only userspace wrapper. Avoid custom Nav2 fork, kernel privilege/uprobes, new general profiler.
- Files: `d06/diagnostic/cm_tf_gettransform_preload.cpp`, `d06/diagnostic/CMakeLists.txt`, `d06/diagnostic/analyze_first_cm_tf.py`, tests `d06/tests/test_g07_cm120_tf_first_gap_join.py`, preflight workflow `.github/workflows/axia-g07-cm120-tf-shim-build-l0.yml`. Exact pins and runtime remain previous.
- Intended TF wrapper: intercept only official advanced overload, forward unmodified to `RTLD_NEXT`, record bounded per process/thread CLOCK_MONOTONIC, CLOCK_THREAD_CPUTIME_ID and return status; no ROS publisher, no sensor data or private position. On actual CM process only, public simulation only. Diagnostic execution instrumentation can bias timing; not a release benchmark.
- Gate B tests must prove same CM pid/tid and callback-to-TF event alignment with C05 LTTng and RMW source pair. TF wall cost alone **is not** proof of TF waiting vs OS preemption; script never grants `gate_c_authorized` from unmeasured scheduler data.
- First preflight [Run #44006345463](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44006345463) `completed/failure`, **before ROS/Goal**: CMake RED: `ament_target_dependencies` used plain signature but new CMake `target_link_libraries(... PRIVATE dl)` used keyword signature. First failure is `CMake Error at CMakeLists.txt:13`, not CM logic. Minimal one-line fix to plain `target_link_libraries(... dl)` commit `1cc5a8463d06508ed9656a2a3a6ad06f7cfb4957`. Revalidated ABI pending. Fail-fast prevents any moving Goal on unverified instrumentation.
- If direct TF shared-object linkage cannot be proven in L0, do not send Goal. If TF diagnostic itself fails, mark `CAUSE_UNPROVEN` and stop. Never repeatedly retry the same moving Goal.

## Gate C — one proven cause only [NOT STARTED]
No extra CM/Nav2/Guard/Supervisor source, CPU affinity, QoS, TF motion-correction, source_timeout=1.0, CM120/Guard150/ScanOdomClock300 or Stop zone parameter changes. At Gate B with confirmed actionable root do RED→GREEN→REFACTOR→REVIEW→COMMIT; otherwise STOP.

## Gate D — original tracer-OFF all-layer CI [NOT STARTED]
Only with Gate C proven Green. Same official C37 original Waffle/Harmonic/Nav2 one Goal; real first CM source+Observer <=120ms, Guard actual <=150ms, Scan/Odom/Clock <=300ms, S02 native Contact0, CLEAR/SLOWDOWN/STOP, odom zero dwell>=1s, original Goal Cancel and Navigation+Localization lifecycle ACK, CM exit0. Only **then** one Owner WSL2 final and separate user approval before main merge.

## 교육용 학습 요소
1. 소스 publication 간격과 Observer callback 간격을 각각 재고 RMW SYSTEM timestamps와 host-monotonic values를 직접 빼지 않기.
2. 81.973ms 콜백 elapsed가 TF `lookupTransform` 81.973ms 또는 스케줄러 runqueue 지연임을 증명하지 않는 이유.
3. CMake 링크 오류/원본 CI preflight와 실제 moving Safety TTL 오류의 최초 실패 분류.
4. TF 함수의 wall time 중 CPU vs non-CPU는 TF wait과 preempt를 구분하지 못하므로 fail-closed 인과 판정을 유지하는 방법.

```text
AXIA_G07_CM120_GATE_A=FIRST_GAP_CONFIRMED_ROOT_CAUSE_UNPROVEN
AXIA_G07_CM120_GATE_B=ABI_L0_PENDING_NO_GOAL
AXIA_G07_CM120_GATE_C=NOT_STARTED
AXIA_G07_CM120_GATE_D=NOT_STARTED
AXIA_G07_CM120_RELEASE=HOLD
AXIA_MVP_DEMO_ACCEPTED=HOLD
OWNER_WSL2_L3=NOT_RUN
CERTIFIED_ESTOP=false
MAIN_MERGED=false
```

## Gate B 사전검증 실제 결과 — L0 GREEN, 실제 Goal은 별도

- 최초 CI [#44006345463](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44006345463) RED: `ament_target_dependencies` plain과 `target_link_libraries PRIVATE` 혼용. 최초 오류 `CMake Error at CMakeLists.txt:13`; ROS·Goal 시작 전 실패. 한 줄 변경 commit `1cc5a8463d06508ed9656a2a3a6ad06f7cfb4957`.
- 수정 뒤 실제 pinned Jazzy toolchain CI [#44006597068](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44006597068) **completed SUCCESS**:
```text
[100%] Linking CXX shared library libaxia_g07_cm120_tf_diag.so
AXIA_G07_CM120_OFFICIAL_ADVANCED_TF_ABI_INTERPOSITION_L0_PASS_NO_ROS_NO_GOAL
AXIA_G07_CM120_DIAGNOSTIC_ONLY_L0_PASS_NOT_RELEASE
```
- 시간창·Clock negative cases 추가 CI [#44006795555](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44006795555) **completed SUCCESS**, same source SHA `35abdbef803e08de14d0ffc955bf06ef478a56f0`:
```text
Ran 3 tests in 0.001s
OK
Ran 3 tests in 0.001s
OK
AXIA_G07_CM120_FIRST_GAP_TF_INTERVAL_JOIN_GREEN3_AND_C05_REGRESSION_NO_ROS_NO_GOAL
AXIA_G07_CM120_OFFICIAL_ADVANCED_TF_ABI_INTERPOSITION_L0_PASS_NO_ROS_NO_GOAL
```
- 신규 분석기는 실제 `cm` PID + vtid + C05 callback handle + same host-monotonic TF interval만 인정하고, 잘못된 프로세스·누락된 함수 호출·시계 offset drift를 fail-closed. **TF elapsed가 콜백을 대부분 차지해도 TF function wall 자체가 OS preemption을 포함할 수 있으므로 `tf_wait_proven=false`, `root_cause_proven=false`, `gate_c_authorized=false`로 고정**. 단일 진단만으로 확인 가능한 단계와 실제 원인 분리를 혼동하지 않는다.
- 사전검증이 통과한 뒤 Original C05 exact private `966886c4627deb2bb3b37111fe336eeee6b9ebb4`, public diagnostic `35abdbef803e08de14d0ffc955bf06ef478a56f0` 소스가 고정된 one-off 공개 진단 workflow `.github/workflows/axia-g07-cm120-four-gate-one-diagnostic-l2.yml`, trigger release commit `3332d7704bc6057f06ddcc15dd188d1188eabb2d`, actual [Run #44007105539](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44007105539) 시작.
- 이 **한 번의 실제 Goal 진단**은 원래 C05 LTTng, official Waffle/Nav2/Harmonic, original Stop·Contact0·CancelGoal·ordered shutdown·7-channel 120/150/300ms oracle을 그대로 재사용하되, original advanced TF 호출의 entry/end/CPU만 bounded LD_PRELOAD로 관측. 해석 결과나 CI status는 Run 완료 후 아래에 추가. Tracer-ON Goal은 릴리스 PASS 근거가 아니다.
