# AXIA D08 — spin_once 최초 Scan 공백 계측/증거 보존 RED→GREEN L2 보고서 (2026-11-19 KST)

## 검증 원칙과 이전 결과

- 공개 개발 Draft PR [#183](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/183); 코드 브랜치 `fix/d08-executor-spin-timing-20261119`.
- 기준 SHA `ed056f9662e2b2621e464f47a5908357df38a905`: D08 read-only Observer의 `spin_once(timeout_sec=.05)` A/B. 이전 공개 [Run #44431911431](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44431911431) L0 176 PASS 및 실제 Gazebo 8사이클 L2 PASS. 그러나 370.251ms(Heartbeat 321.277ms), 340.246ms(Heartbeat 22.674ms)의 서로 다른 Scan 지연 양상 지속.
- 기존 518.394ms Owner WSL2 HOLD, 공개 CI 505.365ms와 512.136ms / 667.085ms 위반 증거를 보존. ROS Scan host 수신 간격 **500ms 초과**는 최초 안전 타이밍 위반으로 FAIL-CLOSED; 나중 회복한 Path나 뒤따르는 정상 Gap으로 소급 PASS 금지.
- 가설: `spin_once(50ms)` 지정이 실제 callback dispatch를 50ms 안에 보장하는가? 두 같은-Python-process ROS subscriber는 모두 지연했지만 독립 `/scan` ROS process는 그때 정상 수신할 수 있으므로, `spin_once` 실제 wall elapsed/thread CPU와 메시지 *동일 source-stamp pair*를 함께 비교.

## RED → GREEN → REFACTOR → REVIEW → COMMIT

1. `d08/tests/test_d08_spin_once_first_gap.py` 신규 RED: `diagnose_spin_once_during_scan_gap` 부재. [Public Run #44434493770](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44434493770) 오류 `ImportError: cannot import name 'diagnose_spin_once_during_scan_gap'`. L2 SKIPPED.
2. `d08/harness/d08_scan_gap_trace.py`에 순수 분류 함수, `d08/harness/d08_same_world_replan.py`에 원래 Observer/같은 프로세스 ROS Executor의 `spin_once` 시작/끝 host monotonic 및 `time.thread_time()` 차이 bounded 기록. 원래 `spin_once(timeout_sec=.05)`, 공식 Nav2, 수신 주기 500ms/CM 120ms/Guard 150ms 모두 그대로.
3. 첫 GREEN L0 [#44434770157](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44434770157): `180 passed in 0.86s`. **실제 Gazebo L2 BLOCKED**: 최초 3상 Path에서 Observer 365.171ms/native 138.206ms/isolated ROS 138.025ms, `D08_EXECUTOR_SPIN_ONCE_TRACE_INCOMPLETE` (최대 1024개 샘플이 실제 첫 구간을 덮어씀). **안전 위반 >500ms는 아님**. 증거 #14488321646 보존.
4. `d08/tests/test_d08_spin_once_history_custody.py` RED [#44435397636](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44435397636): `ImportError new_spin_once_event_buffer`. GREEN bounded 4096개 및 기존 정적 문자열 계약 최신화. [#44435523620](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44435523620)에서 `1 failed, 181 passed` 정적 계약 불일치 확인 후 테스트만 최소 수정.
5. [#44435647053](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44435647053) L0 `182 passed in 1.00s`; L2에서 원래 Observer 287.071ms/native 164.989ms/독립 ROS 164.984ms, `D08_EXECUTOR_SPIN_ONCE_TRACE_INCOMPLETE` 재발. 당시 같은 정확한 Scan 구간의 각 Executor가 13/11회 spin을 기록하고 wall duration 최대 51.360/53.007ms였음. 4096버퍼 전체 포화만으로 구간 유효성을 부정하는 검증 로직 과도함.
6. `d08/tests/test_d08_spin_once_first_gap_proof.py` RED [#44436495297](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44436495297) `ImportError spin_trace_window_proof`. 이후 최초 >500ms 위반 존재 시 정확한 *그 source-stamp pair*가 매칭되고 spin window bracketed인지 확인하는 bounded gate로 수정. `history_complete=false`는 그대로 표시.
7. [#44436779871](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44436779871): L0 `186 passed in 0.96s`; 실제 L2 Observer 439.101ms/native 128.120ms/isolated ROS 130.976ms 사례. buffer 4096 다시 포화해 구간이 이미 소실, `D08_EXECUTOR_SPIN_ONCE_FIRST_GAP_PAIR_UNVERIFIED`. **기존 500ms 안전 기준과 별개의 계측 보존 실패**.
8. `d08/tests/test_d08_spin_once_sparse_evidence.py` RED [#44437771745](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44437771745): `ImportError append_sampled_spin_event`. GREEN `append_sampled_spin_event()`: `spin_once()` 실행 방식 불변, **기록만** 각 Executor별 최소 50ms 간격; wall 75ms 초과 호출은 무조건 기록; bounded maxlen 4096 유지. 마지막 실측 코드 SHA **`d7cf8dc742481e57bd92a0087263e6c761a9855d`**.

## 최종 공개 CI와 직접 검증한 아티팩트

[Public Run #44437921180](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44437921180) — 실제 checkout/source SHA `d7cf8dc742481e57bd92a0087263e6c761a9855d`.

```text
189 passed in 1.09s
D08_PUBLIC_MAIN_NO_GOAL_L0_PASS
D08_OFFICIAL_SAME_WORLD_THREE_PHASE_PATHS_L2_PASS_NO_GOAL
D08_CI_REAL_GUI_EIGHT_REPEAT_PATHS_L2_PASS
D08_REAL_SAME_RUN_EIGHT_CYCLES_SCAN_ODOM_CLOCK_CADENCE_L2_PASS_NOT_CM
```

- 공식 Gazebo Harmonic·공식 Nav2 ONE World + Waffle no-goal, 첫 3상 `official_path_phases` 및 `ci_owner_replan_cycles/cycle_0000~cycle_0007`: 실제 **9개 verdict 모두 `D08_REAL_THREE_OFFICIAL_NAV2_PATH_PHASES_L2_PASS_NO_GOAL`**. 첫 500ms 초과 위반 0건.
- 성공된 범위는 **Nav2 Path + 동일 ROS Scan source stamp 세 수신 계층 증거 + Scan/Odom/Clock cadence**. Contact/YOLO 별도 jobs는 의도적으로 SKIPPED.
- [L2 evidence artifact #14489801251](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44437921180/artifacts/14489801251), ZIP SHA256 `7e5a56c71bf8570b0d9b0be8b318a3be62ec45a8f7281c1adb6af6715b0bf714`, 113 entries, CRC PASS.
- source_sha in all 9 cycle verdicts matches exact code SHA. Spin trace sample_count per repeating cycle 214~329 with `history_complete=true`, same source-pair `MATCHED_CURRENT_SOURCE_PAIR_ONLY`, each `bracketed=true`.
- `cycle_0004` real same-source first/last Scan pair:
  - **Native Gazebo transport 140.871ms**.
  - **Independent ROS Python process 341.956ms**.
  - **Original Observer 346.500ms**.
  - Same-Python secondary ROS Executor **347.729ms**.
  - Process heartbeat max **23.529ms**.
  - Same gap `spin_once` max wall **58.294ms Observer / 53.906ms same-Python ROS**, 6 calls each; candidate `ROS_BRIDGE_DDS_OR_SHARED_HOST_DELAY_CANDIDATE`. This is strong evidence of post-Gazebo subscriber delay shared across independent ROS processes, **but does not disambiguate bridge's ROS publish, DDS, RMW, host scheduling**.
- Initial `official_path_phases`: Native Gazebo Transport **302.741ms**, independent ROS **148.779ms**, Observer **321.348ms**, secondary same-Python ROS **319.449ms**, process heartbeat **195.863ms**, Observer/secondary `spin_once` wall **206.315/214.310ms**. This differs from cycle_0004 and points to a **second process-level scheduling/wait pattern**; do not conflate with the first.
- `d08/harness/d08_amcl_initial_pose.py` blob `f44ffe3aa67bbbde03a28319d0db3587742b6f52` unchanged from earlier GREEN. NO Goal/Velocity generation or safety TTL changes.

## Review verdict and next one-step diagnostic

```text
D08_SPIN_ONCE_FIRST_GAP_L0=PASS
D08_REAL_GAZEBO_FIRST_AND_EIGHT_CYCLE_L2=PASS
D08_SPIN_ONCE_EXACT_PAIR_EVIDENCE=PASS
D08_FIRST_518394MS_HISTORICAL_ROOT_CAUSE=UNDETERMINED
D08_INTERMITTENT_POST_NATIVE_ROS_DELAY=OBSERVED
D08_PUBLISH_TO_SUBSCRIBE_RMW_DELAY=NOT_MEASURED
D08_CM_INTERNAL_RX_AND_GUARD_TTL=NOT_VERIFIED
D08_OWNER_WSL2_L3=NOT_RUN
D08_G07_MOVING_E2E=HOLD
D08_MAIN_MERGED=NO
```

**Next smallest causal boundary**: without modifying official Nav2, sensor, or Safety Supervisor, add **CI-only optional native ROS tracing at ROS bridge publisher and subscriber take**, gated by availability of Jazzy's bundled `tracetools`/LTTng. Use official [ROS 2 Jazzy tracing guide](https://repo.test.ros2.org/en/jazzy/Tutorials/Advanced/ROS2-Tracing-Trace-and-Analyze.html) and [ros2_tracing](https://github.com/ros2/ros2_tracing). LTTng timing can separate bridge publisher timestamp from subscriber callback, but `rcl_publish` and `rcl_take` events are not automatically per-Scan causally matched without stronger tracing/message metadata; do not claim DDS vendor bug or publisher cadence proven on event counts alone. Only proceed if this is a strictly bounded (CI-only / no core modifications) diagnostic that preserves first safety violation and bounded artifact.
 
**No Owner WSL2 tests, no new Goals/Twist, no main merge.** Report committed on separate docs branch to keep real L2 verified source SHA immutable.
