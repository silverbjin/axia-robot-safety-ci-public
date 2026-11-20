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
