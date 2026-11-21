# AXIA G07 — WSL2 최종 인수 전 최초 RMW/Executor·SLOW 경계 회귀 보고서

2026-11-21. 기준: AXIA_Robot_Safety_MVP_Baseline_Scenario_Acceptance_v1_KO.md.
**RELEASE=HOLD / ROOT_UNDETERMINED / NATIVE_STRICT_2_OF_2_NOT_PROVEN / OWNER_WSL2_L3_NOT_RUN / MAIN_NOT_MERGED / CERTIFIED_ESTOP=false.**

## 1. 출처와 중복 보존
- Public Draft #215, branch `diag/g07-first-scan-rmw-exact-native-20261121`; Student Draft #89, branch `diag/g07-rmw-messageinfo-capability-20261121`.
- 기존 Public #211(S1), #212/#213(S3), #214(EventsExecutor SystemError 기각), #215(정확한 Scan RMW/bag 첫 쌍)의 구현은 중복하지 않음. SingleThreadedExecutor와 EventsExecutor 사용 금지. 공식 TB3 Waffle/Nav2/Collision Monitor, original MultiThreadedExecutor 2 workers, safety TTL Scan/Clock/Odom <=300ms, CM <=120ms, Guard <=150ms, 정확 UUID Cancel/Nav+Loc SHUTDOWN, raw 14-topic custody 그대로.
- 첫 시간 위반이 실제 원인인지 확정하지 않은 채 Goal 반복·임계값 완화·Observer writer rewrite 금지. 강사 원본/Goal UUID/rosbag 원본은 공개 저장소 업로드하지 않음.

## 2. 실제 Public native 최초 위반 — 반드시 첫 이벤트로 분류
### 직전 원본 Multi2 #44870371777
- Public `9d229c86e77dfe138a59ca446e8ac78e322b24cc`, Student `78483d12a664d2a92960ecf2721b32916baba231`: Cycle1 FAIL/Cycle2 PASS = 1/2 FAIL.
- Cycle1 최초 Observer Odom 364.600854ms>300; CM pre_guard388.878454>120; supervised390.295463>150; Guard350.320489>150; Supervisor390.286458>150; Scan397.610405>300; Clock343.914547>300. CM same publisher seq+1 source 50.018636ms, original RMW received382.004174ms; 독립 subscriber received 정상 ~50ms.
- Executor 첫 Python stack `_wait_for_ready_callbacks → wait_for_ready_callbacks → _spin_once_impl → spin`; worker 둘 `_worker` 유휴. Observer lock/write/flush <1ms. 관측 Supervisor BOOT_SAFE→NORMAL은 **첫 위반 이전**, 안전 악화 전이 아님. Global process heartbeat 진행. RMW wait-set/원 subscriber 경계 원인 후보, Causal root는 UNDETERMINED.

### 20ms wait-set CI-only A/B #44870974857 — REJECTED
- Public `60636e1172e71fddc120015ddf263350201d690e`, Student `ba20f93a8cfc839342df9b543d29a0ae3a4e51c9`: **Cycle1 FAIL / Cycle2 FAIL = 0/2**. Static L0 #44870974907 GREEN, full #44870979816 **324 PASS, 3 SKIP**, Canary #44870979892 PASS.
- Cycle1 최초 Odom364.150617ms>300; Scan390.522985>300, CM callback361.513010>120, Guard363.100137>150, Supervisor363.095934>150, Clock340.596516>300; same CM publisher Source50.456883ms vs independent RMW Received50.411921ms vs original Received354.987322ms; callback361.513010ms. Executor stack `_wait_for_ready_callbacks → ... → spin_once → spin_multi_with_bounded_wait` while worker two idle. Goal L2 FAIL.
- Cycle2 Goal 이전 첫 Scan Observer **600.502826ms**>300, same Header stamp 102ms, source **107.857389ms**, original RMW Received **599.696375ms**, independent rosbag same header pair **107.737729ms**, seq+1. SafetyScan599.135713ms, Clock/Odom session max574.95851/572.479777ms are **not aligned to same Scan pair**. No Goal, first Supervisor state NOT_CAPTURED_BEFORE_GOAL.
- Artifacts #14694147401 and #14694186347, SHA sidecars 6/6 each PASS. CI-only bounded wait did not cure 120/150/300ms, **do not ship A/B to Owner**. OS/RMW precise cause remains unproven.

### first in-flight spin_once timing native #44871515361
- Public exact `8fabdb2507b1d13b1ee8406c9d05f733ab2c6482`, Student exact `6895f90815fe62a4358abe6b306854af5b8cb6a5`. **Cycle1 PASS / Cycle2 FAIL = L2 1/2 FAIL**. Native artifact #14694540399 7/7 sidecars PASS, #14694256885 6/6 PASS.
- Cycle1 full scoped Moving Goal GUI PASS, no first 120/150/300ms breach, Source/RMW usable; first spin in-flight stall was NOT_CAPTURED, so timeout overrun root not proven.
- Cycle2 first actual phase `CI_MOVING_GOAL_TIMEOUT_SLOW` after CLEAR, exact active Goal, genuine physical Slow cylinder set-pose ACK. 97 observed samples, first front0.6776m with **negative supervised vx**; within `0.4<front<0.75` maximum forward supervised vx **0.0001208934m/s**. Odom yaw0.1147→1.5198rad while robot turns, front later >1.6m and obstacle no longer in front. Existing strict SLOW requires positive supervised vx>0.005m/s AND CM/Final slowdown. No SLOW success, no STOP success; late UUID Cancel is not SLOW proof. Supervisor `NORMAL`, Guard `FORWARDING_MONITORED_CM` but not FULL DEMO PASS.
- Actual latest two cycles did not reproduce a first 160ms executor stall; extra first `spin_once` in-flight metric could not prove waitset timeout violation. New SLOW failure is a **separate** obstacle-heading/positive command demonstration boundary, do not rewrite it as Scan root or relax safety oracle.

## 3. 실제 TDD 및 경로
- Student stack first-gap diagnostic RED `1cd80c36240b85b99d0d5d952c7e725ffcf99203` + Public RED #44869836836 1 FAIL+1 ERROR → Student GREEN `78483d12...`, Public L0 #44869914875 7/7.
- First Supervisor observed transition RED Public #44870171788 two ERROR → GREEN #44870237478 full 322 PASS/3 SKIP. No missing FSM transitions invented.
- Native strict 2cycle RED #44870330547 → GREEN #44870371777 1/2 FAIL actual Gazebo. L0 323 PASS/3 SKIP.
- Multi2 bounded wait RED Public #44870814633 1 FAIL+1 ERROR → GREEN #44870886742 Student 9/9; native source RED #44870936136 4 FAIL → GREEN static #44870974907; **actual native #44870974857 0/2 FAIL**, candidate rejected.
- First `spin_once` same-host-monotonic overrun diagnostic RED #44871307810 1 FAIL+1 ERROR → GREEN L0 #44871402419 Student 11/11; native pin RED #44871467876 4 FAIL → GREEN Public L0 #44871515345, full #44871520229 **324 PASS,3 SKIP**, runner canary #44871520258. Actual Gazebo #44871515361 1/2 FAIL.
- Student paths: `block_B/day07/h01_runtime/tools/p2_g07_observer_io_probe.py`, `p2_g07_ci_moving_goal.py`, `test_g07_observer_io_first_boundary.py`. Public paths: `d06/diagnostic/g07_first_actual_delivery_gap.py`, `tests/test_g07_first_scan_rmw_evidence_export.py`, `.github/workflows/axia-g07-first-scan-rmw-pair-l0.yml`, `.github/workflows/axia-g07-original-multi-first-scan-rmw-native-l2.yml`.
- Commands actually run in GitHub-hosted Ubuntu24.04:
```bash
python3 -m unittest discover -s tests -p 'test_g07_first_scan_rmw_evidence_export.py' -v
python3 -m pytest -q -ra tests
cd student/block_B/day07/h01_runtime
python3 -m unittest discover -s tools -p 'test_g07_observer_io_first_boundary.py' -v
```
ROS2 Jazzy/Gazebo Harmonic/real Nav2 executed **only** by linked native GitHub Actions CI runs; not local WSL2. Do not equate Python L0 with Gazebo L2.

## 4. 정확한 다음 최초 경계 및 출고 게이트
- PREGOAL Scan 최초 600.503ms versus independent same-header bag107.738ms and Source107.857ms, original RMW Received599.696ms: first waitset/take/host scheduling boundary remains unresolved. Do not invent cross-process DDS publication match beyond exact Header. Bounded wait 20ms A/B already rejected.
- Separate SLOW/Goal positive-forward command failure has actual numeric evidence from #44871515361 Cycle2 and earlier #44865216748. Before any fixture geometry change, establish original Goal heading, odom yaw and when obstacle leaves forward LiDAR sector; preserve true physical SLOW/STOP criteria; do not retry same field Goal blindly.
- New concrete code modification needs actual first boundary, RED→GREEN→REFACTOR→REVIEW→COMMIT, full public L0, **new exact-code independent actual Gazebo Moving Goal 2/2 PASS**, strict 120/150/300ms and Guard internal age/Goal same UUID cancel/Nav/Loc ACK/CM+Guard child exit0/14-topic bag custody. Only then release SHA-pinned owner one-shot with `bash -n`, `--self-check`, `--ci-check`, positive actual 2/2 CI gate, **then** one TTY-approved WSL2 L3. No WSL2 command published at HOLD.
- No main merge before user approval; no hardware certified E-Stop assertion. Ending status `PRE_WSL2_GATE=BLOCKED / PUBLIC_FULL_L0_GREEN / REAL_L2_2_OF_2_FAILED / ROOT_UNDETERMINED / OWNER_L3_NOT_RUN`.
