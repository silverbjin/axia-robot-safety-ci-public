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
