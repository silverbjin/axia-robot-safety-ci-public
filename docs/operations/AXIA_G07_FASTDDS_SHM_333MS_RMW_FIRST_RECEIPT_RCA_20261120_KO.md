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


## 7. 2026-11-20 재개: 실패 #163 분리 → Owner 권한 통합 → 공개 인수 준비 PASS

### 7.1 이전 최신 L2의 정확한 종료 판정

- 이전 Student `edd805e84f15a7eae9b14454803fc0912ec0ccf8` / UDPv4 전체 그래프 실제 공개 [#44698698767](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44698698767)는 **Cycle1 FAIL / Cycle2 PASS**.
- Cycle1 실제 Navigation SHUTDOWN 한 번 발행 후 `SERVICE_TIMEOUT=40.000574s`. 직후 동일 공식 Nav2 callback group의 read-only `/lifecycle_manager_navigation/is_active`는 **79.579ms 안에 응답**, `is_active=true` (manager가 FINALIZED였다는 증거 없음). 실제 Moving Goal의 Scan/Odom/Clock/CM/Guard 수신 TTL 위반은 없었음. 서버의 원본 callback enter/finish 증거는 없음. 강제 SIGINT는 ACK가 아님.
- 공식 [Fast-DDS Issue #6630](https://github.com/eProsima/Fast-DDS/issues/6630) (2026-11-13, OPEN): Jazzy Fast DDS 2.14.7을 포함한 신규 participant의 최초 DATA(p) 처리 시점에 UDP receiver 미등록으로 발견 응답을 잃는 사례; endpoint 완전 매칭이 다음 periodic announcement까지 지연될 수 있음. 이는 **AXIA 새 서비스 참여자의 무응답과 부합하는 원인 가설**, 정확한 service request packet이 누락됐다는 증거는 아직 없음.
- 기존 `p2_g07_ordered_shutdown.py`는 `/get_parameters`에 응답한 ROS node를 이미 갖고 있으나 `_call_isolated_stage`에서 Navigation 종료 요청마다 **새 ROS participant**를 생성함. 새 구현은 **1회 Navigation 종료 요청에 한해 이미 응답을 받은 그 ROS node로 서비스 호출**; Localization 기존 격리 경로 보존. timeout 40/30, 전체 60, CCM120/Guard150/Scan300/Clock300/Odom300 불변. 가짜 ACK/재시도/ROS_DOMAIN 속임 없음.

### 7.2 RED → GREEN → REFACTOR → REVIEW → COMMIT

- CI 한정 A/B Student 개발 별도 Draft [#74](https://github.com/silverbjin/axia-robot-safety-student/pull/74). RED [#44705167014](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44705167014) 신규 `_call_shutdown_stage_for_ab` 부재로 예상 실패; GREEN [#44705607110](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44705607110) 기존 D06 종료·GUI·Context regression + 신규 A/B PASS. `test_d06_localization_manager_callback_probe.py`의 기존 정확한 `command="shutdown"` 코드 계약을 깨지 않도록 리팩터링하고 같은 검증 재확인. 실제 CI-only Student SHA `9d8afed4182d3997d77b3cfca04383d3dd6db74c`.
- 실제 Jazzy/Harmonic/Waffle/공식 Nav2·CM·Guard Moving [#44705873381](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44705873381) **2/2 full strict L2 SUCCESS** (UDPv4 전송, Navigation warmed participant CI A/B): Runner 0/0, Navigation+Localization ACK, child exit0, 실제 Xvfb Gazebo+RViz 2창, exact Goal/Guard internal. Guard 최대 CM age 64.072976/45.825974ms; CM Observer 최대 75.673720/69.461942ms; Scan 202.622720/201.905471ms; Odom140.726833/142.025832ms, Clock82.441076/100.411251ms. 원본 SHM first stack는 여전히 미증명.
- Owner 환경으로의 **위조 없는 별도 승인 분리**: Student source `4f4d07f6daf878dd8076f89669698f61f52a802b`, `AXIA_G07_NAV_WARM_PARTICIPANT_OWNER=1`은 `GITHUB_ACTIONS!=true`, `AXIA_G07_CI_SIM_GOAL_ALLOWED=0`, `AXIA_G07_TASK04_OWNER_MOVING_L3=1`, 기존 Jazzy·sim·실제 Owner parity·격리 GZ 조건에서만 허용. CI `AXIA_G07_NAV_WARM_PARTICIPANT_CI_AB=1`은 GitHub public scoped simulation에서만 허용. 두 모드 동시 선택 거부. 기본 모드는 원래 per-manager 분리. `tools/test_g07_nav_owner_warm_authority.py`: RED [#44706515418](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44706515418), GREEN [#44706713615](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44706713615).
- Owner 승인 조건까지 내장된 Student 최종 후보 `4f4d07f6daf878dd8076f89669698f61f52a802b`를 정확히 고정해 새 공개 실제 Gazebo [**#44706879509**](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44706879509), workflow SHA **`fe2e4b2599c2fe3e136ffbd06899733a5ba17906`**, **엄격 2/2 full L2 PASS**. Cycle1/2: runner_rc0, actual Nav/Loc ACK+Guard/Supervisor child exit0; Guard 실제 CM age max **33.631482/19.298836ms**. CM Observer 최대 **59.601117/65.384796ms**, Scan198.739757/210.503537ms, Odom136.290192/134.609856ms, Clock103.585142/107.675570ms. FIRST gap 없음; 7-topic TTL 경계 모두 유지.
- 새 Owner script `scripts/axia_g07_stabilization_wsl2_final_once.sh`는 이 exact Student SHA / Run ID / workflow head SHA에 고정됨. ROS 시작 전 `FASTDDS_BUILTIN_TRANSPORTS=UDPv4` 전역 상속(원본 공식 SHM 버그 회피), 외부 Fast DDS XML profile override는 fail-closed, 그리고 `AXIA_G07_NAV_WARM_PARTICIPANT_OWNER=1`을 사용하며 CI 전용 A/B는 **unset**. 실제 Owner controlling TTY·WSL2 Ubuntu24.04·WSLg·GPU·ROS_DOMAIN 분리·단일 Goal·small diagnostic ZIP 등의 기존 안전 게이트 보존.
- 실제 공개 원샷 RELEASE RED [#44707183260](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44707183260) (Owner 변수 누락), 이후 정확 SHA/Run 고정 및 GREEN [#44707540242](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44707540242), **최종 live API strict admission** [#44707589554](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44707589554): Python **8/8 PASS**, `--self-check` 실 ROS/Gazebo 없음, `--ci-check` GitHub REST에서 exact SHA 및 두 real matrix jobs 모두 SUCCESS 검사 후 `PASS_TWO_STRICT_REAL_GAZEBO_GOALS_OWNER_WSL2_NOT_RUN`. 공개 일반 Python CI [#44707599045](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44707599045) PASS.
- 사용자 WSL2 실제 시연 **L3 NOT_RUN**, 독립 NVIDIA WSLg G3 크래시 #186 **HOLD**. 실제 NVIDIA/WSLg renderer 예외나 native SIGABRT/SIGSEGV core가 없으므로 해당 부분을 PASS로 확대하지 않음.
- `G07_CM_RMW_350MS=MITIGATED_CI_ONLY_NOT_ROOT_STACK_PROVEN`, `NAV_SHUTDOWN_ACK=CI_2_OF_2_PASS_CAUSE_HYPOTHESIS`, `FORMAL_NATIVE_L2=2_OF_2_PASS`, `WSL2_FINAL_L3=NOT_RUN`, `CERTIFIED_ESTOP=false`, `MAIN_MERGED=false`.

### 7.3 강사 WSL2 최종 원샷: 단일 실행

공개 CI에서 해당 bash 원샷을 문법·Mock 성공/실패·실제 GitHub API 성공까지 검증했으나, **사용자 강사 WSL2 NVIDIA 환경에서 이 명령을 아직 실행하지 않았음**.

```bash
(
  set -Eeuo pipefail
  PIN="29fb906d294aa6bcb13490a108dacd5596dd5779"
  SCRIPT="$(mktemp --suffix=.sh)"
  trap 'rm -f -- "$SCRIPT"' EXIT
  curl -fLsS --retry 3 --max-time 90 \
    "https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public/$PIN/scripts/axia_g07_stabilization_wsl2_final_once.sh" \
    -o "$SCRIPT"
  bash -n "$SCRIPT"
  bash "$SCRIPT" --self-check
  bash "$SCRIPT" --ci-check
  bash "$SCRIPT" --run
)
```

예상 원샷 입구 신호:
- `AXIA_G07_STABILIZATION_WSL2_BOOTSTRAP_L0_PASS student_sha=4f4d07f6daf878dd8076f89669698f61f52a802b l2_run=44706879509 NO_ROS_NO_GAZEBO_NO_GOAL`
- `AXIA_G07_STABILIZATION_CI_L2=PASS_TWO_STRICT_REAL_GAZEBO_GOALS_OWNER_WSL2_NOT_RUN`
- `AXIA_G07_FASTDDS_BUILTIN_TRANSPORTS=UDPv4 OWNER_SHM_333MS_MITIGATION_CI_FIRST`
- `--run`에서 실제 ROS2/Gazebo/Goal/Stop/Cancel/Nav2 ACK/GUI 및 ZIP evidence는 **현장에서만** 결정됨. User TTY 수동 승인 보존, 가짜 성공 불가. 스크립트 출력의 현장 `...HOLD`는 임의로 PASS로 수정하지 않음.

### 7.4 출고 규칙과 보존

- CI_PASS는 위 **정확한 native 2-cycle 시연 범위만** 보증합니다. 최초 native SHM mutex stack, 신규 DDS 참여자 request drop stack, 독립 WSLg NVIDIA GPU/G3/Owner L3는 미검증입니다.
- 실패가 Owner WSL2에서 발생하면 최초 `first_failure.txt`, 첫 Guard 상태 전이 및 수신주기 위반, `*.diagnostics.zip`를 확보해 공개 CI에 재현 가능한 부분만 회귀 테스트 편입. 같은 현장 오류 반복 실행 금지.
- 공개 [Draft PR #199](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/199) / Student [Draft PR #74](https://github.com/silverbjin/axia-robot-safety-student/pull/74); main 병합은 승인 전까지 금지. 강사 비공개 정답은 별도 저장소 보존.
