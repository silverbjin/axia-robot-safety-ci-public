# AXIA G07 안정화 이슈 #185/#163/#157/#186 재점검 및 범위 고정

- 작성일: 2026-11-20 KST
- 목적: **교육용 MVP Baseline `20261120-jrCIgoGl` ACCEPTED는 보존**하면서, 미해결된 종료/데이터 전달/WSLg 크래시를 정확한 최초 경계로 분리한다.
- 기반 공개 CI main: `c1ea14b57ea25c0292befa4a493ccc25a82f1ad4`, 공개 Draft [PR #177](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/177), Student main: `be92d8bf13a2b547cac49cbe4696a71264dae57f`.
- 본 변경: **조사 결과·재사용 경로만 문서화**. ROS/CM/Guard/Nav2/TTL/렌더러/실행기/CI workflow 변경 없음. 신규 ROS/Gazebo/WSLg 테스트 **NOT_RUN**. main 병합 요청 아님.

## 0. 격리된 네 개의 판정

| 대상 | 확보된 증거 | 이번 판정 |
| --- | --- | --- |
| G07 교육용 시연 | Owner `jrCIgoGl` 21/21, 공개 Moving L2 2-cycle #44653465671 | **교육용 수치·기능 Baseline ACCEPTED 유지**, 영상 콘텐츠·정식 안전 인증 별도 |
| #185 + #163 종료 안정화 | 실제 #44491751936 Localization ACK 누락; 기존 PR #177 RED/GREEN과 #44503070174 L2 PASS | **간헐 서비스 무응답 근본 원인 OPEN**, 단일 종료 안정화 트랙 |
| #157 CM→Guard 첫 경계 | 실제 Moving L2 #44652034063 Guard 첫 래치 188.577986ms >150ms | **원인 미확정 HOLD**, 기존 D08/D06 계측 재사용 |
| #186 NVIDIA WSLg | 실제 Owner Gazebo server -11, 독립 native witness SIGABRT134 | **독립 HOLD**, 최초 충돌 스택 없는 상태에서 렌더러 수정 금지 |

`FORMAL_SAFETY_TIMING_ACCEPTANCE=NOT_CLAIMED`, `CERTIFIED_ESTOP=false`; 교육용 ACCEPTED를 정식 안전 인증/WSLg 안정화 완료로 승격하지 않는다.

## 1. 종료 안정화 #185 + #163: 신규 종료 시스템 금지

### 서로 다른 최초 ACK 실패
- [#44491751936](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44491751936): 실제 ROS2 Jazzy/Gazebo Harmonic 공식 Nav2 NO_GOAL. Sensor Raw/Safety 20초 정상 후보; Navigation SHUTDOWN 요청 ACK **2.633초**. Localization SHUTDOWN **단일 요청** `request_sent=true`, **30.000493초 SERVICE_TIMEOUT**, `localization_ack=false`. `BLOCKED_LIFECYCLE_LOCALIZATION_SERVICE_TIMEOUT`, runner rc3. CM exit0·Gazebo exit0·부모 `P2_L2_GRACEFUL_TEARDOWN`은 Localization ACK 부재를 해결하지 않는다. 서비스 광고/요청 전송은 서버 콜백 진입 또는 응답 완료의 증거가 아니다.
- [#163 원본 #44073078458](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44073078458): Goal terminal 뒤 **Navigation** SHUTDOWN 서비스 40.000372초 TIMEOUT, `navigation_ack=false`, Localization 요청 **NOT_SENT**. 이 두 사례를 하나의 일반적 'Nav2 종료 실패' PASS/FAIL 수치로 뭉개지 않는다.

### 기존 RED→GREEN을 재사용, 중복 구현하지 않음
- 공개 PR #177 `d06/tests/test_d06_g07_nogoal_ordered_cm_shutdown.py`의 `test_localization_30s_no_ack_probes_readonly_service_without_retry`가 #44491751936을 **이미 명시적으로 회귀 고정**.
- [RED #44493060902](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44493060902) → [GREEN #44502886416](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44502886416) **102/102**, [추가 GREEN #44504764400](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44504764400) **103/103**.
- Student pinned `df911a88f88f70a7e622170b55678ee821423d8f`의 `block_B/day07/h01_runtime/tools/p2_g07_ordered_shutdown.py`: 기존 Navigation→Localization ACK 순서를 유지하며, Localization 최초 timeout에만 **read-only** `/lifecycle_manager_localization/get_parameters`를 1회 제한 조회. SHUTDOWN 재송신 없음, 글로벌 60s 종료 예산 확대 없음, 응답했다고 ACK로 승격 없음.
- [실제 L2 GREEN #44503070174](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44503070174): Navigation ACK1.504530s, Localization ACK0.249842s, 센서 20.007s Scan300 PASS, CM/Gazebo server child exit0, NO_GOAL. **timeout이 재현되지 않아 read-only timeout 진단은 NOT_TRIGGERED**. 즉 간헐 root cause 제거는 **미증명**.
- 이후 PR #177의 C07 [#44561289931](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44561289931)에는 Nav/Loc ACK가 있었지만 별도 첫 Scan300 위반으로 통합 L2 FAIL. 성공한 종료 단계가 다른 타이밍 게이트를 무효화하지 않는다.

### 다음 실제 수정의 진입조건
서비스 타임아웃이 재발한 **동일 실제 세션**에서 client send/response host-monotonic, manager callback entry/phase/finish, single request ID를 대조해 (1) callback 미진입 (2) callback 내부 정체 (3) 완료/응답 전달 누락 중 하나를 **실증**할 때만 최소 수정. 기존 ROS-free 테스트 및 공식 Nav2 코드 재사용; 추측에 의한 timeout 확대, 무조건 재시도, 자체 종료 매니저 신설 금지.

## 2. D07 ROS Context 종료 보호 — 동일 오류 위치에서만 재사용

- Student main `block_B/day07/h01_runtime/ros2_ws/src/axia_safety_supervisor/axia_safety_supervisor/p2_shutdown_context.py`의 `is_context_waitset_shutdown`은 다음 조건 모두를 요구한다: **context_ok=false, type(exc).__name__=='RCLError', 'failed to initialize wait set', 'context is not valid'**.
- Base Guard/Supervisor `main()`은 `ExternalShutdownException`/SIGINT 및 **그 정확한 WaitSet 무효화만** 제한 처리하고 다른 예외는 raise, finally `rclpy.try_shutdown()`. 이미 Student main에 포함됨.
- `jrCIgoGl`과 #44652034063의 종료 후 `cannot use Destroyable because destruction was requested` / `The following exception was never retrieved`는 **동일 타입·동일 스택 위치가 입증되지 않음**. 이 경고를 기존 WaitSet RCLError로 재분류하거나 전역 suppress하지 않는다.
- 후속 조건: 원본 native exception traceback과 task/future 종료 시점이 기존 classifier의 정확한 발생 지점과 일치할 때만 하나의 테스트 RED → 동일 범위 패치 GREEN. 단순 경고 2회만으로 새로운 종료 관리자 구축 금지.

## 3. #157 D08 계측 재사용 — 첫 Guard 래치 증거

원본 [실제 실패 #44652034063](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44652034063) job 136009021796:

- Moving Goal STOP 경계에서 첫 Guard tick `tick_monotonic=255.365083096`, 마지막 Guard CM receipt `cm_rx_monotonic=255.176505110`, **Guard age188.577986ms >150ms**, `UPSTREAM_STALE_AFTER_MOTION`; 실제 Guard는 ZERO로 fail-closed 처리했고 Goal은 정상 취소 완료 아님.
- 같은 tick의 독립 CM Observer age **173.465091ms**, Guard와 Observer 간 **15.112895ms**. Observer가 더 최근 CM 한 메시지를 보았음. Supervisor age40.541022ms. 이를 단순한 'Guard subscriber만 느림' 또는 'CM publisher가 멈춤'으로 확정 불가.
- 원본 pre-latch Actual CM Observer 데이터의 최신 제시 시각 `255.191618` 이후 해당 출력 구간에 새 CM 수신이 기록되지 않았음. 하지만 CM 내부 publish 시점과 DDS/RMW source timestamp의 **동일 주기 직접 증거 부족**. 첫 원인은 `PUBLISHER_OR_TRANSPORT_OR_CALLBACK_SCHEDULING_UNDETERMINED`.

**재사용 경로**:
- D08 계열 Gazebo native→ROS 동일 source-stamp 및 host-monotonic 비교: PR #177 `d06/tools/d06_gz_native_scan_probe_safe.py` + `d06/tools/d06_g07_scan_rx_witness.py`.
- CM source→RMW→Observer 기존 검증: 공개 `d06/diagnostic/g07_task02_strict_gate.py`, Student `p2_g07_task03_contract.py::audit_guard_internal_cm_age`, 기존 `actual_ros_events.jsonl` 및 `p2_base_guard_node.py`의 read-only `cm_age_sec`.
- 다음 한 세션에서는 **같은 host-monotonic 축**으로 Gazebo raw/ROS `/scan`/Safety `/safety/scan` 구간, CM 실제 발행, CM RMW source·수신, Guard 마지막 CM callback·tick, Supervisor 수신을 기존 schema에 맞춰 정렬. source 시각이 없으면 `UNDETERMINED`, 동일 stamp pair 불가면 인과 주장 불가.
- Scan 300ms, CM 120ms, Guard 150ms, 원래 LiDAR Hz·DDS QoS 그대로. CPU affinity/renderer 변경이나 동일 Moving Goal 반복 재시도 금지.
- 기존 성공 [#44653465671](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44653465671) 실제 2-cycle과 Owner `jrCIgoGl` 21/21은 보존하되 실패 #44652034063을 소급 PASS하지 않는다.

## 4. #186 WSLg NVIDIA 독립 HOLD

- #186 실제 Owner ZOAgryLW: Nav/Loc ACK, CM exit0과 별개로 **Gazebo server `gz sim -r -s` exit -11(SIGSEGV)**. 짧은 Scan 300ms 위반도 별도이며, 이를 SIGSEGV의 원인이라고 단정하지 않는다.
- 다른 Owner fr1FN4YJ에는 **native gz.transport13 Python witness exit134(SIGABRT)**와 별도의 Gazebo server exit -11. 동일 프로세스/동일 스택 사고로 합치지 않는다.
- PR #177 C11의 `d06/scripts/axia_d06_g07_wslg_sigsegv_capture_once.sh`, `d06/tools/d06_wslg_latest_gz_sigsegv_core.py`, `d06/scripts/axia_d06_g07_wslg_existing_core_once.sh`는 이미 read-only 기존 core 우선·server-only PID 식별·bounded gdb_backtrace 수집 계약을 갖춤. 새 수집 시스템 불필요.
- [C11 L0 #44645744583](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44645744583) **143/143 PASS**는 script/fixture 증거이지 NVIDIA 실제 첫 stack 아님. 실제 GPU 동등 WSLg G3 및 Gazebo server SIGSEGV 최초 stack **NOT_CAPTURED**.
- NVIDIA D3D12/Wslg 렌더러 변경, Mesh·Ogre2 수정, LD_PRELOAD 등은 최초 server stack와 재현 가능한 CI RED 없이 적용하지 않음. 본 이슈는 #185/#163 및 #157과 독립 HOLD.

## 5. 승인/검증/상태

| 변경 대상 | 이번 수행 | 검증 |
| --- | --- | --- |
| 실제 강사 WSL2 | 실행·수정 없음 | 기존 `jrCIgoGl` Baseline 보존 |
| 학생/안전 로직 | 수정 없음 | 기존 immutable Student SHA와 public L0/L2 재사용 |
| 공개 CI/Gazebo | 신규 실행 없음 | 과거 RED/GREEN 및 실 L2 링크로 근거 보존 |
| 신규 문서 | 이 보고서만 | 내용/출처 검토; 런타임 PASS 주장하지 않음 |
| 코드 main 병합 | 없음 | 사용자 승인 전 HOLD |

**최초 원인 증거가 부족한 항목에 새로운 파라미터/timeout/종료 기능을 개발하지 않는다.** #185+#163을 하나의 종료 안정화 트랙으로 추적, #157은 기존 D08 경계 계측만 재사용, #186은 최초 SIGSEGV/SIGABRT stack 확보 전 독립 HOLD.

`G07_EDUCATIONAL_MVP_BASELINE=ACCEPTED`
`FORMAL_SAFETY_TIMING_ACCEPTANCE=NOT_CLAIMED`
`D06_GAZEBO_LIVE_RELEASE=HOLD`
`WSLG_NVIDIA_CRASH_CAUSE=UNDETERMINED`
`CERTIFIED_ESTOP=false`


## 6. 2026-11-20 후속 구현: #157 실제 첫 Guard Latch를 공개 CI L0 회귀로 고정

**범위:** 공개 파생 fixture 1개 + 기존 Baseline Python 테스트에 검사 1개만 추가. **Safety Supervisor / Collision Monitor / Guard / DDS / LiDAR Hz / ROS 실행기 / CI workflow 변경 없음**. 원본 2026-11-20 교육용 `jrCIgoGl` Baseline ACCEPTED 유지. 원본 rosbag/전체 사용자 로그 공개 업로드 없음.

**실제 최초 실패 출처:** [Moving Goal #44652034063](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44652034063), job `136009021796`. 최초 Guard 내부 `UPSTREAM_STALE_AFTER_MOTION`은 150ms TTL 대비 188.577986ms, 독립 Observer 수신 age 173.465091ms, 최근 Observer CM 수신은 Guard보다 15.112895ms 이후. Observer 수신 시각 `255.191618005`는 로그의 Guard tick `255.365083096`에서 관측된 age `0.173465091s`를 **역산한 비교용 값**이며 원본 publish 시각으로 간주하지 않는다. 원본 정확한 CM publisher source pair는 **NOT_PROVEN**. Guard ZERO 출력; Goal 취소 완료 false; 근본 원인 UNDETERMINED. 이전 성공한 #44653465671 2-cycle과 `jrCIgoGl` 21/21 결과를 소급 수정하지 않음.

### RED → GREEN

- **RED 커밋:** `5c43ee96b33bf4a066b5b7c61ebcf4619987d1a3`; `tests/test_g07_task04_jrcigogl_baseline_contract.py::FirstGuardLatchFailClosedRegression::test_actual_first_guard_latch_and_unproven_source_cause`.
  - [공개 Python 계약 #44663606595](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44663606595): `1 failed, 220 passed, 3 skipped`; 실패는 의도한 `FileNotFoundError: tests/fixtures/g07_c32_first_guard_latch_44652034063.json`.
  - [기존 Baseline CI RED #44663606699](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44663606699): 신규 테스트 1개가 동일 fixture 누락으로 ERROR; 다른 기존 Baseline 계약은 PASS.
- **GREEN 커밋:** `9815de8dbb5f7f33fa65f278aa22314a4c58fdf6`; 실제 CI 첫 래치의 공개 가능한 timestamp·TTL·증거 부족 범위를 `tests/fixtures/g07_c32_first_guard_latch_44652034063.json`에 보존.
  - [공개 Python 계약 #44663711469](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44663711469): **221 passed, 3 skipped**, 4.92초, 성공.
  - [기존 Baseline 계약 #44663711455](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44663711455): 9 기존 테스트 + 5 Baseline 테스트 모두 OK, 새로운 Guard 첫 래치 회귀 1개 포함. `AXIA_G07_TASK04_DEMO_BASELINE_L0_PASS=OWNER_PIN_9_CONTRACTS`.
  - Runner Canary [#44663711418](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44663711418): SUCCESS. 본 회귀 추가 이후 **새 Gazebo/WSLg 실행은 하지 않았음**.

### REVIEW / 허용 결론

- 정확한 두 수신 경계가 모두 늦었으며 `Observer newer sample count=1`이므로 'Guard만 늦었다' 또는 'CM 발행 중단 확정'은 모두 **증거 부족**. 실제 `cm_publisher_stopped_proven=false`와 `cm_source_publication_pair_proven=false`를 fixture에 명시.
- 숫자 회귀는 과거 한 실패의 불변 계약이며, **intermittent 스케줄러 오류를 수정하거나 근본 원인을 재현하는 테스트가 아님**.
- 코드 검증 명령: `python3 -m unittest discover -s tests -p 'test_g07_task04_jrcigogl_baseline_contract.py' -v`; CI에서는 이 명령과 전체 `pytest`를 수행.
- Task 01: #185/#163의 기존 RED/GREEN과 실제 Gazebo L2 성공 재사용, 서버 callback 최초 원인 미증명 → **추가 추정 코드 변경 없음**.
- Task 02: 기존 `p2_shutdown_context.py`는 정확한 RCLError WaitSet invalid-context만 보호; 실제 `Destroyable` 경고는 예외 타입/스택 일치 미증명 → **NO_CHANGE**. 관련 선례 [rclpy #1385](https://github.com/ros2/rclpy/issues/1385), [#1206](https://github.com/ros2/rclpy/issues/1206)는 AXIA에 대한 인과 확증 아님.
- Task 04: #186의 실제 NVIDIA WSLg server SIGSEGV 및 native receiver SIGABRT 최초 GDB stack 미확보; PR #177 C11/C16의 기존 코어·독립 호스트 진단만 재사용 → **독립 HOLD**.
- 공식 Nav2 `LifecycleManager`의 SHUTDOWN 서비스는 공식 [Jazzy 소스](https://api.nav2.org/nav2-jazzy/html/lifecycle__manager_8cpp_source.html)처럼 callback 경계를 갖지만, 서비스 광고·read-only `is_active` 응답은 해당 `manage_nodes` callback의 첫 진입 증거가 아니다.

**이번 후속 개발 검증 수준:** `L0=PASS`; `L1=NOT_RUN`; `L2_NEW=NOT_RUN`; `WSLG_G3=NOT_RUN`; `OWNER_L3_NEW=NOT_RUN`. 이미 성공한 실제 L2/WSL2 Baseline은 보존하지만 새 회귀로 전 계층 안정성을 PASS라 주장하지 않음.

`G07_SHUTDOWN_STABILIZATION=HOLD_ROOT_CAUSE_UNPROVEN`  
`G07_CONTEXT_EXCEPTION=NOT_APPLICABLE_UNTIL_SAME_STACK_PROVEN`  
`G07_CM_GUARD_TIMING=HOLD_FIRST_LATCH_L0_LOCKED`  
`G07_NVIDIA_WSLG_CRASH=HOLD_FIRST_STACK_NOT_CAPTURED`  
`G07_EDUCATIONAL_MVP_BASELINE=ACCEPTED`  
`MAIN_MERGED=false`  
`CERTIFIED_ESTOP=false`


### 6.1 REFACTOR / 최초 상태전이 계약 고정

- REFACTOR 커밋 `1a926cc02a06f6b0f564d8406ec2529f999220a0` (Python 회귀) 및 `b1590dd6f9c0f85720091e4e378accfe64a2e18b` (파생 fixture).
- 실제 Guard FSM 최초 상태 전이 전 마지막 비래치 `255.328142s` → 최초 내부 검사 Tick `255.365083096s` → 최초 래치 관측 이벤트 `255.381865s`. 실제 라치의 `reason=UPSTREAM_STALE_AFTER_MOTION`, 출력 ZERO.
- 독립 Observer 마지막 수신 시각 `255.191618005s`는 **관측된 최신 수신 age173.465091ms에서 역산한 진단값**. 이는 **두 연속 Observer 수신의 interarrival gap이나 CM publisher publish 간격을 증명하지 않는다**. 기존 CM source/Observer 120ms 주기 한도는 변경·완화하지 않았고, 이 스냅샷만으로 정확한 첫 CM source 위반 판정 금지.
- [최종 REFACTOR 공개 Python L0 #44664219189](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44664219189): **SUCCESS**.
- [최종 Baseline L0 #44664219191](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44664219191): **SUCCESS**.
- [최종 Canary #44664219211](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44664219211): **SUCCESS**.
- 이번 리팩터는 표본의 시간축 정의를 정확하게 한 계약 변경뿐이며 ROS/Gazebo/CM/Guard 동작을 수정하지 않았음.

### 6.2 다음 실제 원인 검증에 필요한 좁은 증거

첫 `UPSTREAM_STALE_AFTER_MOTION` 전후의 **동일 세션**에서 CM 프로세스 내부 마지막 출력 publish host-monotonic, ROS RMW source timestamp/sequence, 독립 Observer 수신, Guard 수신·Tick을 같은 시간축에 맞춰 확보해야 함. 기존 `d06/diagnostic/g07_task02_strict_gate.py`, D08-derived receipt witness, Student native Guard `cm_age_sec` 필드를 우선 재사용. 이 증거 없이 새 퍼블리셔/스케줄러 설정이나 Safety TTL 변경 금지. Root cause는 여전히 OPEN/HOLD.


## 7. Nav2 Jazzy ZERO 발행 중단과 #157 최초 Guard Latch: 원인 가설 검증

### 7.1 공식 Nav2 코드에 확인된 설계 경계

- 공식 Jazzy `nav2_collision_monitor/src/collision_monitor_node.cpp` `publishVelocity()` ([소스](https://api.nav2.org/nav2-jazzy/html/collision__monitor__node_8cpp_source.html#l00213)): 현재 출력 `req_vel`이 ZERO로 바뀌면 `stop_stamp_=this->now()` 기록, 이후 ZERO가 유지되어 `this->now()-stop_stamp_>stop_pub_timeout_`이면 **ZERO cmd_vel 출력 자체를 중단**함. 공식 [설정 문서](https://docs.nav2.org/jazzy/configuration_and_development/configuration_guide/core_servers/collision_monitor/configuring_collision_monitor_node/)도 종료 동작을 명시.
- 기존 실 Gazebo Moving #44652034063 동일 세션에서 활성 `stop_pub_timeout=5.0` 읽기 확인. 최초 Guard `UPSTREAM_STALE_AFTER_MOTION`, `cm_age_sec=188.577986ms>150ms`, Supervisor 입력은 당시 정상 수신. Guard는 ZERO로 fail-closed.
- 따라서 **CM의 의도된 ZERO 발행 종료**와 **Guard의 지속적 150ms 수신 요구** 사이에 설정상 호환성 위험이 있음. 단, 실패 원본의 최초 CM ZERO 전환 시각과 `stop_stamp_`은 원본 제한 공개 로그에 없어 **#44652034063의 실제 주 원인으로는 아직 미확정**.
- CM stop timeout은 ROS sim `now()` 기준이므로 **Host monotonic 5초를 그대로 비교하면 오판**할 수 있음. 소스 `/clock`을 동일 세션 기준으로 interpolation하여 실제 5 *sim*초를 비교해야 함.

### 7.2 RED → GREEN (실제 첫 원인 판정이 아닌 구분 가능한 회귀)

- **RED commit** `7ebaeb67d52ff3645a5c27cf5398e3754462c9c6`, `tests/test_g07_cm_stop_pub_boundary.py`; [실제 공개 Python CI #44668014337](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44668014337) `ModuleNotFoundError: No module named 'd06.diagnostic.g07_cm_stop_pub_boundary'`. Baseline 테스트·Canary 별도 PASS. 이는 ROS/Gazebo가 아닌 예상된 L0 import RED.
- **GREEN commit** `8f012a52b3daa1e6f5a7d2e998df500ebaf580de`, `d06/diagnostic/g07_cm_stop_pub_boundary.py`: 새 **읽기 전용** 분석기는 기존 `actual_ros_events.jsonl`의 CM 연속 ZERO *이전 비ZERO→이후 연속 ZERO* 구간, `/clock` sim timestamp, 실제 활성 `stop_pub_timeout` readback, 최초 Guard `first_latch_trace`를 비교. `CM_STOP_PUB_TIMEOUT_COMPATIBLE_UNPROVEN` / `...TIMING_INCOMPATIBLE` / `...UNVERIFIED` 모두 **root_cause_confirmed=false, release=HOLD**. `stop_stamp_` 내부 시각이 없으면 확정 불가.
- [실제 공개 Python #44668393503](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44668393503): **225 passed / 3 skipped**. Guard/CM 실제 소스 또는 안전 TTL 변경 없음.
- L2 workflow `.github/workflows/axia-g07-fv17-owner-evidence-parity-native-l2.yml` 최소 연결 commit `fa0c6915740838e6953a19cfadf02ea60d883506`: 기존 Student SHA/공식 Nav2/동일 real-Gazebo Moving Goal 2-cycle·CM/Guard 안전 게이트 보존, 종료 후 원본 events를 **읽기 전용** 분석하고 공개 가능한 작은 `cm_stop_pub_first_latch.json`만 업로드. 원본 raw bag 업로드·안전 출고 권한 없음.
- **실제 Gazebo/Nav2 L2 #44668565391**: 두 독립 사이클 모두 **SUCCESS**. Cycle1 Guard 실제 내부 CM age 최대 **13.328436ms**, Cycle2 **31.634086ms**; 원본 코드 그대로 실제 RViz/Gazebo Xvfb GUI 2개, Goal·종료 및 필수 Guard TTL 게이트 통과. 두 번 모두 진짜 `stop_pub_timeout` readback 확인. 새 진단 결과는 두 번 모두 `CM_STOP_PUB_FIRST_BOUNDARY_UNVERIFIED`, `root_cause_confirmed=false`, `release=HOLD` — 왜냐하면 **기존 실패 래치 자체가 재현되지 않았기 때문**. L2 PASS로 원래 실패 #44652034063을 소급 PASS하지 않음.
- 독립 최근 L0 성공과 기존 강사 `jrCIgoGl` 교육용 21/21 Accepted 보존. **이번 실 Gazebo L2가 Nvidia WSLg GPU의 SIGSEGV 해결 증거는 아님**.

### 7.3 이후 원인 확정 및 수정 게이트

1. 현재 raw 원본에서 `first_zero` 또는 네이티브 `stop_stamp_`를 확인할 수 없다면, 위 구분 가설은 `UNDETERMINED`. 임의로 `stop_pub_timeout`/Guard TTL 증감 금지.
2. 새로운 동일 가상 시뮬레이션 원본 래치가 발생하고 `sim_zero_to_latch_sec>=5.0`, `sim_zero_to_last_output_sec<=5.0+증거 오차` 및 실제 CMS callback/source 타임라인이 함께 있으면 그때 **publisher deliberate zero cessation**의 원인 후보를 검토. `stop_stamp_` 또는 공식 CM 내부 분기 증거가 없는 한 인과 확정 금지.
3. Guard CM age 초과가 ZERO 발행 중단 후라면 **기존 안전 fail-closed ZERO 유지**, CM120ms/Guard150ms/Scan300ms 절대 완화 금지. 시연 컨트롤러의 STOP→Odometry dwell→정확한 Goal Cancel 흐름이 기존 5 sim초 내 종료되는지 증거를 먼저 검토. 추가 기능이 아니라 기존 지연 경계만 최소 수정.
4. #185/#163 기존 독립 read-only ManageLifecycleNodes probe와 #186 WSLg 코어 스택은 별도 미해결. C16 별도 NVIDIA 동등 runner 부재이므로 #186 최종 해결을 주장할 수 없음.

**검증 상태:** `G07_EDUCATIONAL_BASELINE=ACCEPTED`, `TASK03_CM_ZERO_TIMEOUT_HYPOTHESIS=UNPROVEN`, `G07_SHUTDOWN_STABILIZATION=HOLD`, `WSLG_GPU_CRASH=HOLD`, `NEW_L2_PUBLIC_MOVING_TWO_CYCLES=PASS`, `NEW_OWNER_WSL2=NOT_RUN`, `CERTIFIED_ESTOP=false`, `MAIN_MERGED=false`.


## 8. 통합 REVIEW 및 CI 중복 실행 방지 — 종료 보고 (2026-11-20)

- 공개 실제 Gazebo/Nav2 Moving 2-cycle **#44668565391**: Cycle1 runner RC=0, RViz/Gazebo 각각 1개, 실제 Guard 내부 최대 CM age **13.328436ms**; Cycle2 runner RC=0, GUI 각각 1개, Guard 내부 최대 **31.634086ms**. 두 세션 모두 Goal·Nav2 종료·CM/Guard 및 native witness를 기존 엄격 L2로 검증했고, 독립 ZERO 발행 가설 분석기의 출력은 `CM_STOP_PUB_FIRST_BOUNDARY_UNVERIFIED` + 활성 파라미터 readback=true. **정상 실행이 간헐 원인을 재현하거나 설명하지 못했으므로 근본 원인 FIXED 아님**.
- `pull_request` 경로 필터는 PR 전체 diff를 매 synchronize마다 비교하므로 문서 커밋에서도 오래 걸리는 Gazebo L2가 중복 실행되는 현상 확인. `49bb593a6ee2d3a5188263675cc8aff2f319efc0`에서 실 L2 트리거를 해당 작업 브랜치의 **push + 정확한 코드/테스트/workflow 경로 변경**으로 한정. 기존 `fix/g07-task04-fv17-evidence-contract-20261120` 브랜치 트리거도 보존. 후속 보고서만 커밋할 때 재실행되지 않도록 개선했으며, 테스트·로봇 런타임과 안전 파라미터에는 영향 없음. GitHub [push/PR 경로 차이 공식 설명](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow).
- 최종 계약 CI `#44669300694` **225 passed, 3 skipped**, Baseline `#44669300693` PASS, Canary `#44669300751` PASS; 성공한 학생 `5c7983598fa3bcd7148433a06f37a4e78b091273` 소스 및 공식 Nav2 코드 **무수정**.
- 기존 실패 #44652034063은 Guard 내부 188.577986ms에서 ZERO Latch, 실제 환경 고정 `stop_pub_timeout=5.0`; 최초 ZERO 발생 시각/CM 내부 stop_stamp, 네트워크 publish timestamps가 빠진 한 **원인 확정은 금지**.
- **#185/#163** : 기존 30s Localization/40s Navigation timeout 읽기 전용 진단은 PR #177에 이미 존재. 정상 ACK 단기 L2만으로 intermittent DDS/서버 callback 원인 해결 선언 금지.
- **D07 Context** : 기존 `p2_shutdown_context.py`의 정확한 invalid WaitSet `RCLError`는 유지, 원래 `Destroyable` future 경고는 스택 동일성이 입증되지 않아 무변경.
- **#186** : 별도 RTX NVIDIA WSLg/G3 하드웨어와 최초 실제 SIGSEGV/SIGABRT core stack이 없으며, C11 기존 `--server-only` first core/GDB 증거 수집기와 C16 환경 사전검사만 보존. Linux Xvfb PASS를 WSLg crash 해결 증거로 대체 금지.
- **WSL2 현장 release gate** : 현재 승인된 교육용 `jrCIgoGl` 원본 Baseline은 보존하지만, **새 안정화 출고 원샷을 RELEASE하지 않음**. 첫 원인별 수정과 동등 CI 증거 확보 전 실행기 배포는 사용자가 요구한 CI-first 정책에 반함.
- 작업 브랜치: `docs/g07-185-163-157-186-stabilization-recheck-20261120`, 공개 Draft PR #199. 사용자 승인 전 main 병합 금지.

`G07_EDUCATIONAL_MVP_BASELINE=ACCEPTED`  
`ISSUE_157_FIRST_LATCH_L0_REPRO=PASS`  
`ISSUE_157_CM_STOP_PUB_HYPOTHESIS=UNPROVEN`  
`ISSUES_185_163_SERVER_CALLBACK_CAUSAL_ROOT=UNDETERMINED`  
`ISSUE_186_GPU_SIGSEGV_FIRST_STACK=NOT_CAPTURED`  
`STABILIZATION_ROOT_CAUSE_CLOSED=false`  
`NEW_WSL2_RELEASE=HOLD`  
`MAIN_MERGED=false`  
`CERTIFIED_ESTOP=false`


## 9. 2026-11-20 후속 안정화: 실제 Guard·신규 /clock 최초 위반·Context 범위

### P0 — 공식 CM ZERO 발행과 실제 Student Guard 정책: 결정적 L0

- 공식 [Jazzy CollisionMonitor::publishVelocity()](https://api.nav2.org/nav2-jazzy/html/collision__monitor__node_8cpp_source.html#l00213)에서 `stop_pub_timeout`은 **sim-time** 기준으로 ZERO 출력 발행 중단. 같은 입력 공백은 실제 Collision Monitor 고장으로도 발생하므로 `Twist`에 정지 원인 정보가 없는 Guard는 둘을 구별할 수 없음.
- 기존 Student 정확한 SHA `5c7983598fa3bcd7148433a06f37a4e78b091273`의 진짜 `p2_base_guard_policy.State`를 별도 개발·복사하지 않고 import해 수행한 결정적 구성요소 테스트. `d06/tests/test_d06_g07_cm_stop_pub_guard_real_policy.py`, 전용 공개 `.github/workflows/axia-g07-cm-guard-real-policy-l0.yml`.
- RED `28cd695522aec9f4b066d3558d7edda32ff393fb`, 공개 CI [#44674659405](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44674659405): 요구한 테스트 미존재로 명시적 `test -s` 검증 실패 (의도한 구조적 RED). GREEN `7f59f0b6753a9515ddf78407cec562c526692ceb`, [#44674762165](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44674762165): **4/4 PASS**.
- 실 CM의 정상 ZERO 연속 5 sim초 이후 입력 중단, 갑작스러운 CM 고장, STOP 이전 정상 CM ZERO 수신, 실제 보호 STOP 네 가지에서 **기존 Guard 안전 ZERO/래치 동작 PASS**. 이는 공식 CM process를 호출한 L1/L2가 아니라 **실 Student 정책 + 공식 분기에서 파생된 입력 일정**의 L0 검증. 실제 실패 #44652034063의 STOP 5초 원인은 증명하지 않음.
- CM/Guard TTL, 공식 Nav2, 기존 구현, 시연 속도/센서 Hz **변경 없음**. 정지를 위해 ZERO 메시지를 의도적으로 생략하는 경우와 고장 수신 공백의 구분 불가능성이 있으므로 안전 래치 무력화 금지.

### P0 — 신규 실제 Moving L2 실패의 최초 Clock300 경계

- [실제 공개 Gazebo #44674827354](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44674827354): 한 cycle 실제 CLEAR/SLOW/STOP 및 Goal CANCELED 확인 후, 동일 세션 오라클에서 메시지 주기 위반으로 FAIL (다른 cycle 성공은 이 실패를 덮지 못함).
- **최초 증거**: `/clock` host callback `465.863223669 → 466.197405698` = **334.182029ms > Clock300**. 동일 프로세스의 관측 최대 `pre_guard CM=369.606081ms`, `supervised source=369.591385ms`, `Guard status=361.675863ms`, `/odom=340.649158ms`, `/scan=369.681761ms`, Supervisor=369.628101ms. 다른 토픽의 정확한 최초 쌍이 로그에 없으므로 공통 퍼블리셔 중단 vs DDS/RMW vs Observer callback starvation 중 **원인 UNDETERMINED**.
- 첫 Guard 안전 Latch 관측 없음; Guard가 정상 수신한 상태에서 **독립 Observer만 0.3초 지연된 것인지** 알 수 없음. 단일 실패를 근거로 Guard TTL 변경·Observer 판정값 무시 금지.
- 최소 재현 RED `a453f03eb1c200cd70084f4a7e9be5c282dc4e90` [공개 CI #44675344294](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44675344294): 새 read-only 분석기 import 실패. 중간 RED [#44675433563](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44675433563): 파생 fixture 미존재. GREEN `4a5cbda6f30f444747ec828840c9c4a17704bcd8` [공개 #44675464705](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44675464705): **229 PASS, 3 SKIP**.
- 새 파일 `d06/diagnostic/g07_first_actual_delivery_gap.py` + `tests/test_g07_cross_stream_first_gap.py` + 공개 파생 fixture `tests/fixtures/g07_44674827354_cycle2_first_gap.json`. 원본 이벤트가 같은 Host Monotonic 기반으로 제공될 때 최초 Clock/CM/Scan/Odom/Guard 수신 쌍과 상관 시각을 **읽기 전용** 추출하며 `root_cause=UNDETERMINED, release=HOLD` 고정.
- 실제 기존 L2 workflow `.github/workflows/axia-g07-fv17-owner-evidence-parity-native-l2.yml`에 종료 후 **`if: always()`** bounded numeric `first_delivery_actual_pairs.json` 기록을 연결. 원본 rosbag, Goal UUID, 메시지 본문 공개 저장 금지. **본 진단기 연계 이후 L2 통합 결과는 별도로 확인해야 하며, L0 GREEN으로 L2 PASS 주장 금지**.
- D08 별도 PR [#202](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/202)에서 ROS witness 콜백 내 디스크 기록을 줄인 사례를 먼저 재사용 조사함. 보고서 자체가 root cause 미확정으로 표시하고 있으므로 G07 Observer의 실제 I/O 정체를 입증하기 전 수정 복사 금지.

### P1 — #185·#163 Ordered Shutdown: 기존 검증 재사용 / 서버 원인 미확정

- PR [#177](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/177) 기존 `d06/tests/test_d06_g07_nogoal_ordered_cm_shutdown.py`, `test_d06_c07_navigation_manager_service_liveness.py`, `test_d06_localization_manager_callback_probe.py` 확인.
- 공식 [Nav2 Jazzy LifecycleManager](https://api.nav2.org/nav2-jazzy/html/lifecycle__manager_8cpp_source.html)는 `manage_nodes`와 `is_active`를 같은 MutuallyExclusive Callback Group에서 생성. `/get_parameters` 정상만으로 manager callback ACK를 판정하지 않음. 기존 read-only 동일 그룹 `/is_active` 진단은 별도 server callback 정체를 구분하는 관측이고 실제 `shutdown` ACK 대체 불가.
- 실제 #44491751936 Localization 30.000493s TIMEOUT, #44073078458 Navigation 40.000372s TIMEOUT 독립 최초 경계 보존. 기존 GREEN L0 #44502886416/#44504764400, 실제 Nav/Loc ACK·CM/Gz exit0 [#44503070174](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44503070174) 재사용. 신규 종료 관리자, retry, Timeout 증가, 공식 Nav2 포크 없음. 최초 서버 Callback enter/finish와 RMW 응답 원본이 없으므로 intermittent root **HOLD**.

### P2 — D07 ROS Context: 정확한 예외만 보호 / 경고 원인 미확정

- 기존 Student `p2_shutdown_context.py::is_context_waitset_shutdown()`을 그대로 import해 실제 조건 `RCLError` + `context_ok=False` + 정확한 WaitSet 오류 문자열에서만 True를 반환하도록 시험.
- RED `6664446c9c407ca14355c4a424b32808691347d5` [공개 CI #44675725871](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44675725871): 신규 검사 파일 부재. GREEN `acc92fc6c7cd21df13e2717120bb8b306672e1e5` [#44675770130](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44675770130): 4개 신규 TEST PASS (기존 실 Guard 4개도 PASS).
- 별도 `cannot use Destroyable because destruction was requested` 경고, 활성 Context 오류, 다른 RCLError는 기존 함수가 **숨기지 않음**. 해당 미래 객체/Task 진짜 발생 위치는 미확인 → Student 런타임 코드 **NO_CHANGE**.

### P3 — #186 NVIDIA WSLg

- 기존 PR #177 `d06/scripts/axia_d06_g3_independent_wslg_nogoal_once.sh` 및 `d06/tools/d06_g3_wslg_gpu_capability.py`, `d06/scripts/axia_d06_g07_wslg_existing_core_once.sh` 등 기존 C11~C17 검증기 확인. 기존 독립 GPU 호스트가 없고 최초 실제 Gazebo server SIGSEGV / native witness SIGABRT 코어 스택도 미확보.
- 기존 C17 실제 합성 CLI/분류 검증은 실 NVIDIA WSLg 충돌 스택을 대신하지 않으며 강사 WSL2 반복 실행 금지. 새 GPU/렌더러/LD_PRELOAD 변경, 신규 WSL2 최종 인수 스크립트 출고 없음. `FIRST_SIGSEGV_STACK=NOT_CAPTURED`, `FIRST_SIGABRT_STACK=NOT_CAPTURED`, `ROOT_CAUSE=UNDETERMINED`.

### 현 상태

`AXIA_G07_EDUCATIONAL_BASELINE=ACCEPTED`  
`G07_CM_STOP_REAL_GUARD_L0=PASS`  
`G07_D07_EXACT_CONTEXT_L0=PASS`  
`G07_FIRST_CLOCK300_L0=PASS_ROOT_UNDETERMINED`  
`G07_SHUTDOWN_STABILIZATION=HOLD`  
`G07_CM_GUARD_TIMING=HOLD`  
`G07_NVIDIA_WSLG_CRASH=HOLD`  
`MAIN_MERGED=false`  
`CERTIFIED_ESTOP=false`


## 10. Moving Goal 종료 진단의 검증된 D06 구현 재사용 (브랜치 전용)

### 최초 원인과 코드 차이

- 현재 Student `main` `p2_g07_ordered_shutdown.py` SHA `181c31b20b9745ba69935c197aef503c7678c516`는 Nav/Loc를 동일 임시 ROS 노드에서 한 번씩 `call_native_manage`로 요청하며, SERVICE_TIMEOUT 뒤 서버 callback group probe가 없다. 2026-11-20 최신 Moving L2 [#44675580481](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44675580481)의 2개 실제 Gazebo/Goal 시연 모두 교육용 CLEAR/SLOW/STOP과 엄격 Guard 내부 TTL 정상(각각 **21.106801ms / 30.872261ms**), 실제 CM/Guard 종료 정상인 반면 원샷 결과 `runner_rc=3`, `MVP_VISUAL_L2_PASS_FORMAL_LOCALIZATION_SHUTDOWN_HOLD`를 기록. **이 workflow의 job SUCCESS는 정식 Nav/Loc ACK 전체 검증 PASS가 아니며, Formal L2는 HOLD**.
- 다른 Student Draft [PR #62](https://github.com/silverbjin/axia-robot-safety-student/pull/62)의 소스 SHA `0565e580f5b7c80d719960a6046de3e45c8ea477`에는 이미 정확히 같은 오류를 대상으로 독립 서비스 클라이언트와 `/get_parameters` 및 `/is_active` read-only probe가 존재했고, 공개 D06 Draft [PR #177](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/177)에서 기존 NO_GOAL 실제 Gazebo 정상 ACK와 첫 무응답 회귀를 검증했음.
- 그러나 PR #62 전체 파일을 새 Moving 환경에 그대로 교체하면 새로 검증된 `parameter_discovery_budget()` (8초 Navigation read-only 탐색) 등이 구버전으로 되돌아갈 위험이 있음. 따라서 **필요한 함수만 부분 이식**, Moving Goal 원본과 교육용 Accepted Baseline SHA는 보존.

### RED → GREEN → REVIEW → COMMIT

- Student 새 개발 브랜치 `diag/g07-moving-shutdown-server-first-20261120`는 Student main SHA `be92d8bf13a2b547cac49cbe4696a71264dae57f`에서 파생. **Student Draft PR #71**, 신규 파일·로봇 기능 추가 없이 `block_B/day07/h01_runtime/tools/p2_g07_ordered_shutdown.py` 하나 변경.
- **RED public CI #44676576718**, public workflow `.github/workflows/axia-g07-moving-shutdown-reuse-l0.yml`의 정확한 기존 D06 `test_d06_localization_manager_callback_probe.py` (3개)와 `test_d06_c07_navigation_manager_service_liveness.py` (3개)를 현재 Moving source에 실행: 초기 시험에서 신규 `probe_localization_manage_callback_group` 미구현으로 **1 FAIL/2 ERROR** (예상).
- **GREEN Student commit `0f6e6bd47e03f01cb55e43e19a20ea31f65feb99`**, 기존 D06의 `_call_isolated_stage()`, Localization `get_parameters` read-only probe, Nav/Loc `is_active` 같은 Callback Group probe, RMW identifier 기록을 Moving 종료 파일에 필요한 범위만 이식. `parameter_discovery_budget()`과 `shutdown_stage_budget()` 및 60s global deadline, Nav→Loc 순서, 단일 SHUTDOWN 요청, `ACK` 없으면 HOLD, CM 관리 확인을 그대로 유지. sensor/CM/Guard TTL, Nav2/Collision Monitor, Goal/속도 로직 변화 없음.
- **GREEN public CI #44676701168**: 같은 D06 기존 테스트 **3/3 + 3/3 PASS**; source pin exact Student `0f6e6bd...`. 수동 승인·Goal 테스트 없는 L0 계약이므로 실제 Gazebo ACK를 주장할 수 없음.
- [학생 PR #71](https://github.com/silverbjin/axia-robot-safety-student/pull/71)은 **Draft**, Student main 미병합. 최초 서버 Callback 진입 여부를 증명할 코어·RCL/RMW 송수신 trace는 여전히 없으며, `is_active` 응답/무응답이 SHUTDOWN ACK를 증명하지 않음.
- 공개 Moving L2 workflow는 최종 교육용 Student SHA를 변경하지 않고 PR #199 **개발 브랜치에서만** exact candidate `0f6e6bd...`로 검증. 후속 실증 실패 시 최초 단계 원본 보존, L2 결과를 따로 기록할 것.

`P1_SHUTDOWN_REUSE_DEVELOPMENT_BRANCHED=true`  
`P1_SHUTDOWN_EXISTING_REGRESSION_L0=PASS_6_OF_6`  
`P1_REAL_MOVING_GAZEBO_L2=NOT_YET_VERIFIED`  
`P1_SERVER_CALLBACK_ROOT_CAUSE=UNDETERMINED`  
`STUDENT_MAIN_MERGED=false`


## 11. RMW 최초 source→receive→callback 진단 재개 (2026-11-20, CI-first)

### 재개 직전의 실제 최초 실패

- Student Draft PR #71의 종료 후보 SHA `0f6e6bd47e03f01cb55e43e19a20ea31f65feb99`로 실제 Moving Goal [공개 L2 #44676844639](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44676844639)를 수행. Cycle 1 전체 native Moving GUI PASS, Cycle 2는 **최초 `/odom` callback gap 342.757876ms > 300ms**로 L2 FAIL. 같은 실제 Observer 프로세스의 7개 스트림 마지막 callback 재개 시각은 `211.315680928–211.317267471` (폭 **1.586543ms**)로 집중됨. 한 관측자의 광범위한 callback 처리 지연 후보이지 CM 퍼블리셔·DDS·Gazebo host 지연 중 어느 쪽도 **입증하지 못함**.
- 실패 원본의 정확한 7개 첫 수신 쌍을 공개 허용 numeric fixture `tests/fixtures/g07_44676844639_cycle2_first_7_stream_pairs.json`에 고정. RED [#44677423036](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44677423036), GREEN [#44677529230](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44677529230), **230 PASS / 3 SKIP**. Guard의 실제 최초 `latched`를 이 원본에서 직접 발견한 것은 아님.

### RMW MessageInfo source, receipt, Observer callback 원인 분리

- 기존 Student `p2_l3_live_session.py::Observer`가 실제 두 토픽 `/cmd_vel_pre_guard`, `/cmd_vel_supervised`에 Jazzy rclpy `MessageInfo`를 이미 요청하고, `p2_g07_ci_moving_goal_oracle.py::normalize_cm_rmw_info`에서 발행시각·수신시각·publication seq를 저장하는 것을 확인. 새 ROS 노드·구독·QoS 변경 없이 **기존 경로 재사용**.
- RED commit `8255f6bd26cb9a97afc93da522844fc91345ef29`, [공개 L0 #44677723671](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44677723671): 테스트 `tests/test_g07_rmw_first_gap_pair.py`의 신규 함수 부재. GREEN commit `1c30d09d183ef1ea6167ad335eba83589b8bceb9`, [공개 #44679712191](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44679712191): **236 PASS/3 SKIP**.
- `d06/diagnostic/g07_first_actual_delivery_gap.py::classify_rmw_first_pair`는 **정확한 최초 Observer callback 쌍**의 동일 CM 메시지 `rmw_source_ns`, `rmw_received_ns`와 `publication_sequence_number`가 둘 다 있고 sequence가 **연속 1 증가**할 때만 source/received/callback interval을 비교. ROS/system nano timestamps의 절대값과 host-monotonic 초의 절대값을 서로 뺄 수 없으므로 각각 내부 간격만 비교.
- status `RMW_SOURCE_PERIOD_GAP_CANDIDATE`, `RMW_RECEIPT_GAP_CANDIDATE`, `OBSERVER_CALLBACK_GAP_CANDIDATE`, `RMW_SEQUENCE_DISCONTINUITY_HOLD`, `RMW_TIMEBASE_REGRESSION_HOLD`, `RMW_FIRST_PAIR_UNVERIFIED`이며 **모두 root_cause_proven=false, release=HOLD, TTL 변경 없음**. sequence가 점프하면 메시지 유실·선별 수신을 구분하지 못하므로 원인을 강제 판정하지 않음.
- 준비 조건 자체의 확인도 필요하므로 `tests/test_g07_rmw_readiness.py` 신규 RED [#44680248970](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44680248970), `summarize_rmw_readiness` GREEN commit `94c9a611fb3ffe45a9a230e699b201ddfa2df7bd` [#44680354689](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44680354689) **240 PASS, 3 SKIP**. 계측은 두 기존 토픽에서 MessageInfo count·valid 연속 seq pair count·누락 카운트만 공개, 원본 메시지·GID는 공개하지 않음. Metadata READY 판정도 안전 PASS 아님.
- [실제 Moving L2 #44679704946](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44679704946)의 **cycle2**는 native Goal·GUI·엄격 TTL PASS, Guard 내부 CM age 최대 **18.209976ms**, 첫 Guard latch 및 공통 수신 breach **재현되지 않음**. 이때 `cm_rmw_first_pair=RMW_FIRST_PAIR_UNVERIFIED`는 **이번 세션에서 결함 발생 안 함**을 뜻하고 영구 해결이나 메타데이터 결함을 증명하지 않음. Cycle1은 작업 중 점검 시 **아직 진행 중**이므로 run 전체 PASS로 표기 금지.
- 준비 상태 보고기 추가 버전 [실제 L2 #44680346981](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44680346981)은 문서 작성 시 **pending**; 실제 CI 결과 확인 전 `L2=NOT_VERIFIED`.
- 현재 첫 안전/센서 수신 위반은 실증되었지만 **CM 원본 source timestamp와 Observer callback 지연이 하나의 실패 세션에서 함께 분류된 증거가 없어 근본 원인 미확정**. 퍼블리셔 재설계, Guard 래치 완화, Scan300/CM120/Guard150/Clock300/Odom300 변경, 임의 멀티스레드 Executor 교체 금지.

### 현재 작업 기준 및 출고 범위

- Public Branch `docs/g07-185-163-157-186-stabilization-recheck-20261120` / Draft PR #199, Student Draft PR #71 SHA `0f6e6bd...`. 공개 `main` 및 학생용 `main` 병합 **없음**.
- 유효 범위는 신규 L0 진단 함수 및 **이미 성공이 확인된** 별도 실제 L2 cycle의 해당 성공 조건뿐. 동일 원본에서 재발했을 때만 첫 RMW pair의 분류를 증거로 사용. 실제 GPU WSLg #186, Nav/Loc 서버 최초 Callback #185/#163은 독립 HOLD 유지.
- `AXIA_G07_EDUCATIONAL_BASELINE=ACCEPTED`; `G07_RMW_FIRST_GAP_DIAGNOSTIC_L0=PASS`; `G07_RMW_ROOT_CAUSE=UNDETERMINED`; `G07_NEW_OWNER_WSL2=NOT_RUN`; `CERTIFIED_ESTOP=false`; `MAIN_MERGED=false`.


## 12. 2026-11-20 strict WSL2 출고 및 최초 RMW 수신 경계

### 기존 원인·최소 변경

- 기존 Student Moving Goal source에서 실제 #44679704946는 Navigation/Localization ACK 및 Collision Monitor exit0 후 runner 외부 1000초 타임아웃(rc124). scripts/p2_no_goal_smoke_ci.sh의 두 소유 GUI process-group에 SIGINT 후 제한 없는 wait가 있어 별도로 재현 가능한 정체 결함. Student PR #71 수정 후보 148635b40c69a40feb8174306cacba6755c88c92는 **자신의 setsid RViz/Gazebo GUI**에 대해서만 bounded SIGINT→TERM→KILL 및 zombie 상태 점검 후 wait. 센서·Guard TTL, Nav2 ACK와 Goal 검증은 무변경.
- RED 공개 CI [#44682844977](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44682844977), GREEN [#44683181819](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44683181819), 기존 GUI 종료 순서 검사 보존 후 [#44683528218](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44683528218) GREEN. 최초 GUI 문제의 근본 원인 확정은 아님.
- 새 공개 strict L2 workflow는 visual demonstration HOLD를 전체 CI PASS로 승격시키던 기존 exit0 예외 경로를 exit3으로 변경 (SHA 310c8932bde167a1a63ad6305a72057d070d4fb1). RED [#44683671614](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44683671614), GREEN [#44683748090](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44683748090).

### 실제 최초 수신 위반 / 원인 범위

- **실제 strict Gazebo L2 #44683741133 = FAIL (2/2)**. Cycle1 실제 Goal 이전 NAVIGATION_START lifecycle rejected, 창 탐색 0/0, Goal 미발행. Cycle2 실제 Goal 도중 최초 Odom 간격 **361.484255ms > Odom300**, 7개 Observer 토픽 동시 수신 공백.
- 같은 Cycle2 정확한 CM pre-guard 연속 발행 seq gap=1, RMW publisher source gap **48.499371ms**, RMW received timestamp gap **356.887562ms**, Observer callback gap **362.069145ms**. 이 최초 pair는 CM publisher 5초 ZERO timeout 가설과 맞지 않으며, 발행 이후 RMW 수신 또는 Observer 실행 경계의 문제 후보. RMW 수신 timestamp만으로 DDS transport vs host scheduling root가 증명되는 것은 아님. 실제 Guard FIRST latch 여부도 미증명.
- 숫자 고정 테스트: tests/test_g07_rmw_first_gap_pair.py와 tests/fixtures/g07_44683741133_first_rmw_receipt.json. RED [#44684409420](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44684409420), GREEN 후속 CI로 검증. raw bag/UUID/GID 공개 없음.

### WSL2 최종 인수 원샷의 상태

- 공개 파일 scripts/axia_g07_stabilization_wsl2_final_once.sh, 정확한 Student 148635b40c69a40feb8174306cacba6755c88c92, reviewer 362da68e31dd163a8d321601e191069c0d0a438b, strict L2 run #44683741133 및 workflow SHA 310c8932bde167a1a63ad6305a72057d070d4fb1 고정. 기존 실제 Owner 단일 Moving Goal, 수동 TTY 동의, WSLg/Ubuntu/Jazzy/Gazebo 검사, 증거 보존 및 소형 ZIP 재사용.
- CLI: --self-check (ROS/Gazebo 없음), --ci-check (공개 GH API에서 strict run 완료/성공 및 2 matrix job 각각 성공 확인), --run (앞의 CI gate가 성공한 경우에만 실제 WSL2 세션 시작). CI 실패/잘못된 SHA/원격 불가 시 **Goal 전 exit3**, 절대 시연 PASS 주장 금지.
- 공개 workflow .github/workflows/axia-g07-stabilization-wsl2-release-l0.yml [#44684045295](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44684045295) 실제 L0 PASS. tests/test_g07_stabilization_wsl2_release.py에서 fake CI 두 job PASS/한 job FAIL/허위 SHA를 검증. 구동 대상 ROS/Gazebo/WSLg L3는 미실행.
- 현 시점 strict L2 #44683741133는 FAIL이므로 소스는 출고 준비됐으나 **WSL2 --run 승인 상태는 HOLD**. CI-first 원칙에 따라 실제 최종 시연 인수 성공·스크립트 완전 릴리스라고 보고하지 않음.

### 분리 HOLD

- #185/#163 Nav2 첫 callback 서비스 실패는 독립 원인 미확정, #186 GPU NVIDIA WSLg native SIGABRT/SIGSEGV 원본 스택 없음; 별도 C11-C17 수집기는 기존 성공 보존. D07 Context 제한된 WaitSet 경계 L0 PASS, 다른 Destroyable 경고 스택 동일성 미확정.
- SW Stop ≠ 인증된 E-Stop. Guard150/CM120/Scan300/Odom300/Clock300 엄격 기준 유지. 공개·학생 main 미병합.

## 13. Fast DDS 333ms RMW + Navigation no-ACK 재개 인수상태 (2026-11-20)

**별도 근거 보고서**: [AXIA G07 FastDDS SHM333ms 원인 가설·정확한 TDD 및 WSL2 인수 가이드](AXIA_G07_FASTDDS_SHM_333MS_RMW_FIRST_RECEIPT_RCA_20261120_KO.md).

- 초기 실제 #44683741133 `source 48.499371ms / FastDDS receive 356.887562ms / Observer 362.069145ms` 최초 CM 메시지 쌍. 공식 [Fast DDS #6535](https://github.com/eProsima/Fast-DDS/issues/6535) SHM 333ms 건강 포트 지연 / [#6559](https://github.com/eProsima/Fast-DDS/pull/6559) master 수정 참조. **이 원본 사건의 native SHM stack은 아직 없으므로 causal root stack 미확정**.
- 전체 실 Gazebo graph에만 `FASTDDS_BUILTIN_TRANSPORTS=UDPv4` 적용한 실제 [#44697383450](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44697383450) **2/2 full L2 PASS**. 분리 독립 재검 [#44698698767](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44698698767) Cycle1 Navigation service 40s no-ACK, Cycle2 PASS; 센서/CM/Guard 최초 수신 TTL 위반 없음.
- 신규 [Fast DDS #6630](https://github.com/eProsima/Fast-DDS/issues/6630) 늦게 새로 참여한 DDS discovery 경계 가설에 따라 Navigation 한 번의 종료 요청만 **이미 read-only parameter ACK를 받은 동일 ROS participant**에서 전송하도록 CI 한정 A/B. 실제 [#44705873381](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44705873381) **2/2 strict Moving Goal L2 PASS**.
- CI와 Owner 별도 authority test RED #44706515418 → GREEN #44706713615. 최종 Student 정확 SHA `4f4d07f6daf878dd8076f89669698f61f52a802b`에 대해 실제 [#44706879509](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44706879509), workflow SHA `fe2e4b2599c2fe3e136ffbd06899733a5ba17906`, **2/2 strict L2 PASS**: real Goal/Cancel/ZERO/Nav+Loc ACK/CM clean/GUI/Guard internal age; 안전 TTL 무변경.
- 공개 WSL2 최종 원샷 `scripts/axia_g07_stabilization_wsl2_final_once.sh` (GitHub pinned file SHA `29fb906d294aa6bcb13490a108dacd5596dd5779`)는 Student/CI SHA 정확 고정, 실제 Owner `AXIA_G07_NAV_WARM_PARTICIPANT_OWNER=1`, Fast DDS UDPv4. 부트스트랩 및 GitHub 실시간 strict 2/2 판정 공개 [#44707589554](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44707589554) **8/8 PASS, 실제 GitHub API 확인**, ROS/Gazebo 미실행.
- **PUBLIC_GAZEBO_STRICT_L2=PASS_SCOPED; OWNER_WSL2_L3=NOT_RUN; FASTDDS_NATIVE_SHM_ROOT_PROVEN=false; NVIDIA_WSLG_G3=#186_HOLD; CERTIFIED_ESTOP=false; MAIN_MERGED=false.** 이 두 개의 누적 성공을 현장 NVIDIA 최종 인수 PASS로 승격하지 않음. Owner에서 새로운 첫 실패 발생 시, 재실행보다 public CI RED 회귀 편입 먼저.
