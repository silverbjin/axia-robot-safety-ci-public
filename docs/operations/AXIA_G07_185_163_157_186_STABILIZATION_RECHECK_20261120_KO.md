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
