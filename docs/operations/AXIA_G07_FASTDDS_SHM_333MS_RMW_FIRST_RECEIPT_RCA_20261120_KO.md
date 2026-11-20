# AXIA G07 — Fast DDS SHM 333ms·RMW 최초 수신 지연: 공식 Issue 기반 실증·MVP 최소 조치

2026-11-20 KST. **원본 사건의 네이티브 스택 미확보, 원인 귀속 확정 금지.**  안전 TTL 유지. SW Stop은 인증 E-Stop이 아닙니다. 개인 WSL2 NVIDIA 환경은 공개 CI Xvfb와 동일하지 않습니다.

## 1. 처음 증명한 오류 (증거 > 추측)

- 최초 현장 유사 실제 공개 Moving Goal [#44683741133](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44683741133), 정확한 현재 Student 기본 원본 SHA `148635b40c69a40feb8174306cacba6755c88c92` 전 단계 기반에서 /odom 최초 **361.484255ms > 300ms**. Observer callback에서 7개 주요 토픽의 수신 중단이 같은 세션에서 발생.
- 동일 CM writer publication sequence **1 증가**. FastDDS `source_timestamp` 간격 **48.499371ms**, `received_timestamp` 간격 **356.887562ms**, Python Observer callback 간격 **362.069145ms**. 소스 시간과 Host monotonic 절대 Epoch는 직접 비교하지 않음.
- 공개 파생 fixture `tests/fixtures/g07_44683741133_first_rmw_receipt.json`와 회귀 `tests/test_g07_rmw_first_gap_pair.py`: RED [#44684409420](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44684409420) / GREEN [#44684485100](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44684485100).
- **따라서 해당 단일 최초 CM pair의 5초 ZERO 발행 중단 가설은 지지되지 않음**. Fast DDS RMW 수신 이전 또는 RMW 수신 처리 경계 후보이며, 원본 publisher-side SHM mutex stack은 관측하지 못함.

## 2. 먼저 살펴본 기존 해결 사례

- [G07 공용 Draft PR #161](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/161): CM120 기존 TF/nanosleep 부하 분석 증거. 이번 정상 publisher source 간격과 다른 사건이므로 그대로 가져오지 않음.
- [D08 Draft PR #201](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/201)·[#202](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/202): independent ROS DDS participant와 callback-IO free bounded evidence, source-vs-take-vs-dispatch 분리. 본 G07의 `d06/diagnostic/g07_independent_cm_rmw_witness.py`에 최소 재사용.
- [Student Draft PR #73](https://github.com/silverbjin/axia-robot-safety-student/pull/73): ROS2 Jazzy `MultiThreadedExecutor` → opt-in `SingleThreadedExecutor` A/B. 실 Gazebo [#44694882272](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44694882272)에서 CM source52.837645ms/receive379.059445ms/callback381.682159ms로 **동일 최초 수신 지연 재발**, 다른 cycle Navigation shutdown 40s timeout. Python executor만 교체해 해결한다는 가설 기각. 기본 Student 실행기 모드는 유지.
- 독립 DDS read-only witness와 원본 2-worker Observer 조합 [공개 Gazebo #44696306274](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44696306274): 두 cycle 실제 Moving Goal L2 성공. 첫 결함은 해당 실행들에서 재발하지 않아서 exact independent first pair는 `INDEPENDENT_CM_EXACT_PAIR_NOT_VERIFIED_HOLD`. **성공 자체로 기존 SHM 원인 해소라고 판정하지 않음**.

## 3. 추가 발견한 공식 upstream SHM 원인 후보

- [Fast-DDS Issue #6535](https://github.com/eProsima/Fast-DDS/issues/6535), 2026-09-14 접수/2026-10-30 종료: Fast DDS **2.14.7**에서 정상 idle SHM 포트를 열 때 `healthy_check_timeout_ms / 3` 기본값 때문에 **333ms** 대기. 관련 송신 잠금에서 다른 Writer까지 정체될 수 있음. 실제 Jazzy/Gazebo `/clock` stall에서도 FastDDS `SharedMemTransport::healthy_check` → `nanosleep` native stack이 보고됨.
- [Fast-DDS PR #6559](https://github.com/eProsima/Fast-DDS/pull/6559) 2026-10-30 **master 병합**: 리스너 heartbeat 통지와 counter 갱신, 건강 포트 확인 대기 333ms → 1–2ms로 낮춤. 이 시점 [PR #6605](https://github.com/eProsima/Fast-DDS/pull/6605)는 **3.2.x** 대상의 아직 열린 backport. 2.14.x 배포 바이너리에 적용됐다고 **가정하지 않음**. 공식 FastDDS/CMake 포크 빌드는 MVP에서 진행하지 않음.
- 정확한 `CM source 48.499ms → RMW receive 356.888ms`와 실제 여러 토픽 동시 340–380ms 지연은 upstream 병목과 **매우 유사**하나, AXIA의 *동일 런타임 native stack*이나 사용 중인 FastDDS shared-lib 패치 포함 여부가 확보되지 않았으므로 `ROOT_CAUSE_PROVEN=false`.
- [Fast-DDS 2.14 공식 환경변수 문서](https://fast-rtps.docs.eprosima.com/en/2.14.x/fastdds/env_vars/env_vars.html): `FASTDDS_BUILTIN_TRANSPORTS=UDPv4`는 내장 SHM 대신 UDPv4만 초기화. 단 `use_builtin_transports=true` 조건이 필요하며 XML이 사용자 지정 전송으로 덮어쓸 수 있어 CI는 환경변수와 외부 XML Override 부재를 점검.

## 4. 시연 범위 내 최소 우회 (DDS 계층)

- 공개 Draft PR #199 전용 `.github/workflows/axia-g07-fv17-owner-evidence-parity-native-l2.yml` 환경변수만 `FASTDDS_BUILTIN_TRANSPORTS: UDPv4`. 해당 **전체** ROS graph/bridge/CM/Guard/Observer/Native startup에 상속. Student 런타임 소스·Nav2 공식/CM 파라미터·QoS·센서 주기·로봇 Goal·SW Stop·TTL은 변경 없음.
- 공개 regression `tests/test_g07_fastdds_shm_333ms_mitigation.py`: RED [#44697236122](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44697236122) / GREEN [#44697391983](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44697391983).
- **실제 Gazebo Moving Goal 2-cycle 공개 [#44697383450](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44697383450) 2/2 PASS** (전송 UDPv4, 기존 Student `148635...` 및 independent read-only witness):
  - Cycle1: runner_rc0, Guard 내부 max CM age **58.491699ms**, pre_guard callback max **71.635458ms**, scan230.530546ms, odom138.074429ms, clock102.526056ms, exact Goal+Nav/Loc ACK+CM clean.
  - Cycle2: runner_rc0, Guard 내부 max CM age **55.012906ms**, pre_guard max **68.421757ms**, scan205.500603ms, odom136.159335ms, clock104.826567ms. Goal/exit0.
- 독립 UDPv4 추가 2-cycle [#44697450829](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44697450829)에서 **두 cycle 모두 RMW 첫 300ms+ gap 재현 없음**. 다만 전체 strict L2는 다음 별도 정지 실패로 **0/2 FAIL**:
  - Cycle1: 실제 Goal·Guard TTL 정상, 그러나 Nav2 shutdown ACK HOLD (runner_rc3). 시각 시연 PASS를 Formal L2로 승격 금지.
  - Cycle2: 실제 Goal/터미널/주기 모두 정상, runner_rc0, **P2 Supervisor ROS SIGINT context invalid `_state_pub.publish` RCLError**로 child exit1. CI가 올바르게 exit3 판정.
- 즉 **UDPv4 4개 실제 Moving 세션에서 최초 안전 수신 350ms 장애는 재발하지 않았으나, formal 종료 안정화는 여전히 미인수**. 이는 SHM 원인 가설의 실증 지지이지 native stack 증명 아님.

## 5. 후속 안전 종료 수정 분리

- Student 기존 개발 Draft [PR #71](https://github.com/silverbjin/axia-robot-safety-student/pull/71)에서 위 실제 P2 타이머 종료 스택만 TDD로 수정, default Supervisor 본체의 FSM·명령·Watchdog 로직은 건드리지 않음.
- `p2_shutdown_context.py::is_context_publish_shutdown()`는 `context_ok is False` + 정확한 rclpy `RCLError` + `Failed to publish: publisher's context is invalid` 시작 문자열인 경우에만 True. 실제 Context가 살아있거나 다른 발행 실패는 무조건 Raise.
- 실제 P2 entrypoint `p2_supervisor_node.py`에서 기존 `is_context_waitset_shutdown` OR 정확한 publish-shutdown 분류만 허용. Student SHA `edd805e84f15a7eae9b14454803fc0912ec0ccf8`, RED [#44698463587](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44698463587) / GREEN [#44698597366](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44698597366), 기존 Nav/Loc·GUI 후속 L0도 GREEN.
- 정확 Student Source로 새 실 Gazebo UDP-only 2-cycle [#44698698767](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44698698767) **진행 중/결과 별도 갱신**. 성공 전 WSL2 출고금지.
- NVIDIA WSLg G3 최초 SIGSEGV/SIGABRT native stack 없음, 독립 HOLD. 사용자 WSL2 L3 실행하지 않음. 인증 E-Stop 아님, 교육용 Baseline Accepted 보존.

## 6. 회귀 실행 및 현재 가드

```bash
python3 -m pytest -q tests/test_g07_fastdds_shm_333ms_mitigation.py tests/test_g07_rmw_first_gap_pair.py tests/test_g07_isolated_cm_witness.py
# Student pinned branch:
python3 -m unittest discover -s block_B/day07/h01_runtime/tools -p 'test_g07_context_publish_shutdown.py' -v
```

실제 Gazebo L2는 별도 공개 workflow `AXIA G07 FV17 Independent 2-cycle Real Moving Goal Guard TTL L2`에서만 증거로 인정하고, 오류 첫 시각과 실제 CM+Guard age 및 Lifecycle ACK·자식 exit0를 전부 검사한다.

- **프로젝트 범위**: 기존 TB3 Waffle/공식 Nav2/공식 CM 유지, 새 Planner·새 Safety Supervisor·Fault Injector 변경 없음.
- **main 병합**: 공개/학생 main 모두 미병합, Student PR #73 A/B 후보 별도 Draft, PR #71 기존 Shutdown 후보 별도 Draft.
- **근본 원인 판정**: SHM 333ms 잠금과 유사하고 UDP 4세션 주기 정상 → `FASTDDS_SHM_HEALTH_CHECK_CAUSE=HIGH_CONFIDENCE_CANDIDATE_NOT_NATIVE_STACK_PROVEN`.
- **새 WSL2 인수**: 실제 동일 UDPv4 + 새 Student의 exact public 2-cycle strict PASS 확보 전 `WSL2_RELEASE=HOLD`. 기존 고정 Owner 원샷은 실패 CI를 참조하여 필드 Goal 진입 전에 차단함.
- **안전**: CM120ms, Guard150ms, Scan300ms, Clock300ms, Odom300ms, goal cancel/odom dwell/출력 ZERO 유지, 인증 E-Stop false.
