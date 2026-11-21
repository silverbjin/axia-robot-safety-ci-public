# AXIA G07 — S1/S3 최초 안전 타이밍 위반 근거·최소 조치·CI 정밀 회귀 최종 HOLD 보고서

기록일: 2026-11-21 · **검증 수준: L0 PASS / L1 제한적 PASS / 실제 Gazebo L2 FAIL / Owner WSL2 L3 NOT_RUN**  
안전 구분: **소프트웨어 STOP != 인증 E-Stop**. `CERTIFIED_ESTOP=false`  
기준: `AXIA_Robot_Safety_MVP_Baseline_Scenario_Acceptance_v1_KO.md`

## 1. 범위와 이력 보존
- 공식 TurtleBot3 Waffle, Nav2/CM 재사용. Supervisor/Guard/CM 발행·QoS·실제 Goal authority·CM120ms/Guard150ms/Scan/Clock/Odom300ms **불변**.
- 선행 성공 원본 Public native Multi 2/2 [#44830956042](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44830956042), Original Student `891bf65349cf8dfb203bb8b97ffe0346b3fb8b3f`; **새 수정의 인수 증거로 재사용하지 않음**.
- 이전 WSL2 Owner 1ibYCGPg L3 **HOLD**, 첫 CM Observer124.069382ms (RMW source48.746752ms, Received41.902093ms) 및 RMW 시스템시각+2815ms 동시 forward step은 별도 원인. SW STOP은 인증된 E-Stop이 아님.
- 기존 SingleThreaded 후보 실제 native [#44855963095](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44855963095) 1/2 FAIL; 최초 Odom360.425ms, 7채널 교차 최초 위반.

## 2. S1 Observer 내부 lock/JSON/Flush 근본 원인 조사
- Student [PR #83](https://github.com/silverbjin/axia-robot-safety-student/pull/83) 변경 경계:
  `block_B/day07/h01_runtime/tools/p2_g07_observer_io_probe.py`,
  `p2_l3_live_session.py`, `p2_g07_ci_moving_goal.py`, `test_g07_observer_io_first_boundary.py`.
- Original 2-worker Profile `AXIA_G07_OBSERVER_IO_PROBE=1` 공개 CI만 허용, 기존 callback 내부 I/O/0.75s flush 동작 보존, bounded monotonic_ns entry/lock/JSON/write/flush, 독립 Python 20ms heartbeat 숫자.
- RED [#44859009999](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44859009999) → GREEN [#44859130675](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44859130675) 신규4+기존 Stop3/Scan12 PASS.
- Native [#44859276354](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44859276354) Cycle1 preGoal Clock retention insufficient, Cycle2 real Goal PASS. 그 Cycle2 max lock0.085838ms, JSON0.935215ms, write0.16877ms, flush1.049721ms, heartbeat36.538ms.
- Native [#44859905000](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44859905000) FAIL 0/2: Cycle1 preGoal safety_scan window insufficient; Cycle2 actual Moving 첫 PRE_STOP /odom335.761137ms, CM365.545765ms, Clock343.559387ms, Scan367.190792ms, Guard+Supervisor도 동시 첫 수신간격 위반. 첫 위반 구간 내 **Python heartbeat는20~30ms로 연속 실행**, 전체 세션 heartbeat max337.993946ms는 다른 시각. 따라서 **첫 장애 시점 Python 프로세스 전체 정지라고 단정하지 않음**.
- 같은 Cycle2 max lock0.069941ms, JSON0.886015ms, write0.096034ms, flush2.839563ms. **I/O 동기화가 첫 335~367ms 수신공백을 만들었다는 증거가 없으므로 파일 Writer 교체 S2 중단**.
- first-local heartbeat 구분 RED [#44860766009](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44860766009) → GREEN [#44860820606](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44860820606); 첫 timing violation vs global Python heartbeat 구분.

## 3. S3 실험: PreGoal Clock retention / postGoal graph / full 12s discovery
- Student [PR #84](https://github.com/silverbjin/axia-robot-safety-student/pull/84) 경로:
  `p2_g07_scan_wall_pregoal.py` Clock witness deque 4096→16384 **증거 보존만** 확대. 12s 전 Scan/SafetyScan/Clock/Odom 네 토픽 각각 두 개의 유효·최신 수신 callback을 확인, 준비 max8s; 그 뒤 원래 **12s window를 그대로** 유지; timeout은 Goal 전 HOLD.
  `p2_g07_ci_moving_goal.py` preGoal exclusive publisher graph 인증 이후 Graph 불필요한 postGoal snapshot 4개만 `include_graph=False`. 안전 publisher, Cmd, TF, Goal, Nav2 수정 없음.
- Clock+Graph RED [#44859758236](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44859758236) → GREEN [#44859836161](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44859836161).
- Late /safety/scan discovery RED [#44860542348](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44860542348) → GREEN [#44860705515](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44860705515): 초기 재현 + SafetyScan/Clock/Odom/Scan 4-topic exact12sec 회귀. Original Student branch `fix/g07-clock-retention-postgoal-graph-20261121`.
- Native actual [#44860872488](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44860872488) **0/2 FAIL, Goal 발행 없음**:
  * Cycle1 first `/scan` **357.337793ms**, SafetyScan355.867484ms, Odom336.684358ms, header period102ms.
  * Cycle2 first `/odom` **367.403268ms**, Scan373.847900ms, SafetyScan373.885133ms, Clock332.857517ms, header period99ms.
  * Both total local Clock RTF≈1.0; ROS callback/DDS delivery latency exists preGoal; Moving action/cancel solely responsible **아님**.

### 독립 Witness MessageInfo 실제 오류 수정
- 기존 `d06/diagnostic/g07_independent_cm_rmw_witness.py::normalize_witness_metadata`는 Jazzy rclpy 2-arg MessageInfo **dict**를 Python 객체 속성으로만 조회하여 독립 witness Source/Received/Seq 모두 `-1` 기록. Original Observer normalizer는 dict를 정상 처리. 공개 증거 정확한 seq+source pair를 비교하기 어려웠던 **검증기 결함**.
- `tests/test_g07_jazzy_info_dict_independent_cm.py` 3경계 RED [#44860380073](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44860380073) → GREEN [#44860433448](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44860433448) **307 PASS/3 SKIP**. Dict fields independently normalize. No L3 acceptance or safety override.
- 원래 Source header simulation period~100ms + independent bag exact first pair Receive ~83ms일 때도 Primary Python Observer wall385ms, 이는 **동일 원천의 별도 수신 관측이 다름**을 입증하는 제한적 증거. 하지만 특정 RMW/Executor 함수 root는 미입증.

## 4. S3 공식 Jazzy EventsExecutor 최소 A/B — 채택 실패
- 참고: [ros2/rclpy PR #1435](https://github.com/ros2/rclpy/pull/1435) 2025-03 Jazzy experimental EventsExecutor 백포트. Upstream [ros2/rclpy #1452](https://github.com/ros2/rclpy/issues/1452) MultiThreadedExecutor/Clock 수신 성능 보고. 둘 모두 **이 장애 원인 직접 증명 아님**.
- Student [Draft PR #86](https://github.com/silverbjin/axia-robot-safety-student/pull/86), source SHA `26f4abecad2d714721ad27cebe6e5c36d7705b2c`. `p2_g07_events_executor_policy.py` CI-only `AXIA_G07_EVENTS_EXECUTOR_AB=1`, `p2_g07_scan_wall_pregoal.py`과 `p2_g07_ci_moving_goal.py` **read-only Observers에만** 선택. 기본 original 2-worker 동일. Owner는 opt-in 부정 (실수 배포 방지).
- 실제 pinned Jazzy container L1 noGoal [#44861195626](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44861195626) callback8개 max40.181ms PASS.
- 공식 Events L0 RED [#44861246304](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44861246304)→ GREEN [#44861480027](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44861480027) 신규4+기존 사전검사3+Observer5+Stop3 PASS.
- 전체 공개 안전 Python L0 [#44861606692](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44861606692): **307 passed, 3 skipped** + Student 핵심 전부 PASS. `L0 PASS`는 **native Gazebo 성공 증거 아님**.
- **실제 Jazzy/Harmonic/Nav2/Gazebo GUI 2 independent cold-run [#44861540326](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44861540326): 0/2 FAIL**
  * Cycle1 preGoal first Clock331.671633ms, Odom345.761068ms, Scan385.643415ms, SafetyScan382.329901ms, Scan header99ms; 12s FULL Clock coverage, Goal 미발행. Exact first Scan header pair 독립 rosbag receive gap83.539915ms (참고: 모든 Clock bag interval에도 최대476.6ms 변동; 전역 DDS/root 증명 아님).
  * Cycle2 preGoal PASS, Moving read-only C++ `EventsExecutor.spin()` worker 스레드 **SystemError: null argument to internal routine**, HEALTH ready timeout, **Goal 미발행**; no exact Goal/STOP/Shutdown PASS. 새 런타임 장애 실제 ROS2에서 재현. Synthetic L1 timer pass만으로 런타임 안정성 주장 불가.
- 공식 Experimental Events Executor **adopt REJECTED for G07 MVP release**. No Owner WSL2 export or main merge.

## 5. 현재 검증 수준 / 인수 상태
```text
STRICT_CM120_GUARD150_SCAN_CLOCK_ODOM300=UNCHANGED
PUBLIC_ORIGINAL_HISTORICAL_MULTITHREAD_L2=PASS_2_OF_2_OLD_SHA
S1_OBSERVER_WRITE_FLUSH_CAUSE=NOT_PROVEN_NOT_SELECTED
S3_PREGOAL_DISCOVERY_FIX_L0=PASS_REAL_GAZEBO_L2=FAIL_0_OF_2
S3_JAZZY_EVENTS_EXECUTOR_SMOKE_L1=PASS_LIMITED_NO_GOAL
S3_JAZZY_EVENTS_EXECUTOR_ACTUAL_NATIVE_L2=FAIL_0_OF_2
PUBLIC_FULL_PYTHON=307_PASS_3_SKIP
OWNER_WSL2_NEW_L3=NOT_RUN_HOLD
MAIN_MERGED=false
CERTIFIED_ESTOP=false
```

## 6. 다음 재개 단위 — 단 하나의 실패 경계
이번 S3 결과는 **로그·Source/Header·독립 rosbag의 정확한 동일 시퀀스 쌍과 Python 콜백 수신 사이의 차이**를 좁혀야 함을 보임.
- 원래 source/RMW received/host Monotonic clock domain을 혼합하지 않고, 독립 witness의 같은 Source+pub seq 쌍으로 RMW take가 프로세스별로 지연되는지 검증.
- ROS2 Jazzy C++ EventsExecutor의 worker `SystemError` 재현은 **별도 CI 회귀**로 분리, 단순 timer L1로 재승인 금지.
- 추가 안전 노드/Planner/Collision Monitor/Guard/TTL 변경 금지. 실제 Goal·현장 WSL2 재시도 반복 금지. 최초 위반 범위를 제거한 최소 패치에 대해서만 strict 2/2 native 후 Owner 새 단일 인수 실행기 출고.
- 기존 Owner 원본 압축증거 및 public CI 성공 증거는 덮어쓰지 않음. 강사 정답/학생용 패키지 분리, 학생 명령은 사용자 WSL2 인수 준비 전까지 비배포.

### 테스트 명령(실제 공개 CI에서 실행)
```bash
python3 -m unittest discover -s tests -p 'test_g07_jazzy_info_dict_independent_cm.py' -v
python3 -m pytest -q -ra tests
# Student checkout exact source at block_B/day07/h01_runtime:
python3 -m unittest discover -s tools -p 'test_g07_events_executor_ci_ab.py' -v
python3 -m unittest discover -s tools -p 'test_g07_pregoal_stream_discovery.py' -v
python3 -m unittest discover -s tools -p 'test_g07_observer_io_first_boundary.py' -v
```

## 7. GitHub 보호
- Public Draft PR [#211](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/211), [#212](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/212), [#213](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/213).
- Student Draft PR [#83](https://github.com/silverbjin/axia-robot-safety-student/pull/83), [#84](https://github.com/silverbjin/axia-robot-safety-student/pull/84), [#86](https://github.com/silverbjin/axia-robot-safety-student/pull/86).
- 기존 Owner 실행기는 immutable. CI FALSE acceptance gate는 여전히 **block**. Main 미병합.
