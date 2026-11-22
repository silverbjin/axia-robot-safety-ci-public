# AXIA G07 — 마지막 실증 2/2 프로필 재사용, 종료 오류 최소 수정 및 WSL2 Owner 출고 (2026-11-22)

## 1. 최종 판정

- **Public actual Gazebo L2 2/2 PASS — 새로운 정확 SHA에서 재검증됨**. 실제 native CI: https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44965035965
- 정확한 Native Public **`64ba0161e66126b4743b4b12a859f4a5349ae58a`**, Student checkout **`f7edb2d126502eeeed58ae014adadc7a2096d41b`**. 2개 독립 Ubuntu24.04 ROS2 Jazzy/Gazebo Harmonic 실제 Waffle+공식 Nav2/CM Moving Goal 실행, Guard/Supervisor child exit0. 
- 기존과 동일한 10Hz LiDAR, Depth OFF, 원본 Scan/Clock/Odom 300ms, CM120ms/Guard150ms, Goal/Cancel/odom dwell, Nav/Localization shutdown, 14-topic bag custody 및 GUI 진단. 임의 안전 TTL 완화·새 ROS 노드/Executor/Worker/Middleware 추가 없음. 각 Cycle의 Native job 실제 conclusion=success.
- **기존 간헐 FastDDS/rmw reception 장애 근본원인 증명은 NOT_PROVEN**. 2/2 PASS는 *해당 코드/시뮬레이션 범위*의 인수 성공, 향후 영구 무결함 보증 아님.
- **Owner WSL2 L3 NOT_RUN**. NVIDIA WSLg/GPU 및 사용자 호스트 내 로컬 인수는 실제 실행이 필요. 본 출고는 검증된 SHA를 강사 WSL2에서 **단 한 번** 시연할 수 있게 준비한 것. 사용자 승인 전 main 병합 금지. SW STOP은 인증된 물리 E-Stop이 아님.
- 기존 교육용 `jrCIgoGl` 수용 증거 그대로 보존.

## 2. 문제 분석 및 최소 수정 경계

기존 최근 리팩토링 이후 실제 Native #44914827138(0/2)와 새 SingleExecutor 후보 #44916662519(0/2)에서 최초 Scan/Clock/Odom 300ms 및 CM/Guard의 원본 Subscriber 수신 지연이 재발했다.

반면 기존 Student `5667575aac777c374735b1c351445bcc8f83140e` + Public `09ea6cbc8b9079532ef13c0962d193966e99a03b`는 실제 Native [#44902396373](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44902396373) **2/2 PASS**. 추가된 여러 계측·프로필 조정을 수정해 나가지 않고, 이 마지막 성공 기준선으로 되돌아가 정확히 **SIGINT 후 이미 종료한 ROS Context에서 `get_publishers_info_by_topic` RCLError**를 분류하는 기존 P2 Supervisor 2파일 수정만 이식했다.

이는 정확한 **종료 경쟁 조건 코드 결함 수정**이지만 Scan/DDS timing 원인 해결이라는 의미는 아니다. 보호 동작·FSM·QoS·메시지 타입·Scan Header·RMW Transport/CPU affinity 건드리지 않았음.

## 3. RED→GREEN→REFACTOR→REVIEW→COMMIT

Student Draft [PR #108](https://github.com/silverbjin/axia-robot-safety-student/pull/108), source branch `fix/g07-reuse-native2of2-clean-shutdown-20261122`, base baseline `5667575...`:
1. RED test `block_B/day07/h01_runtime/tools/test_g07_context_graph_shutdown.py`: commit `4de7cd53a128cff38aa20d8aa210743769b541ed`. Existing L0 workflow attaches test commit `24dfb126d858ff8c938d5f8b9374a07dbb3a71fe`.
2. Real RED [#44964868126](https://github.com/silverbjin/axia-robot-safety-student/actions/runs/44964868126): 4 tests **1 FAIL / 2 ERROR / 1 PASS**, graph classifier absent as expected.
3. GREEN: commit **`f7edb2d126502eeeed58ae014adadc7a2096d41b`**; only `p2_shutdown_context.py` and `p2_supervisor_node.py` code modified, `context_ok is False` + exact `RCLError`+message, all live-context/other error rethrows.
4. Student L0 [#44964949329](https://github.com/silverbjin/axia-robot-safety-student/actions/runs/44964949329) **4/4 new tests OK + 59 passed Block B**.

Public Draft [PR #231](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/231), branch `fix/g07-reuse-native2of2-shutdown-native-20261122`, base proven `09ea6cbc...`:
1. Native L2 workflow Student pin + branch + one new regression only: commit **`64ba0161e66126b4743b4b12a859f4a5349ae58a`**. Other Native 2-cycle stages, Xvfb, Guard CM age, CM120/Guard150/Scan300/Clock300/Odom300, Goal/Cancel/odom/ACK/child clean unmodified.
2. [#44965049625](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44965049625): public Python **331 passed, 3 skipped in 4.60s**.
3. [#44965035965](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44965035965): actual Gazebo strict 2/2 PASS.
4. Owner release admission RED [#44965368493](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44965368493) **4 FAIL, 8 PASS** — new source SHA/Run test against frozen prior Owner script. Owner one-shot now pins new immutable Student/Public/native Run in commit **`9a531d7ab8f5297ef0b2c52540ee3aa34707a619`**; conservative 12 tests initially 1 stale test still failed [#44965403303](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44965403303).
5. [#44965454024](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44965454024) **12/12 Owner L0 PASS**, actual GitHub REST `--ci-check` returned **`PASS_TWO_STRICT_REAL_GAZEBO_GOALS_OWNER_WSL2_NOT_RUN`**. Owner TTY/CI authority, bad result/wrong sha, SIGINT, zip size checks intact.
6. Public full Python CI [#44965458188](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44965458188) **2 FAIL** due stale older Owner pin tests. Same safety checks kept; exact new validated Run/SHA asserted in `tests/test_g07_scan300_owner_wrapper.py`; commit **`ed0b9202c7fcac791cc7800928a7c97579652140`**.
7. Final public Python [#44965552411](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44965552411) **331 passed / 3 skipped in 4.74s**, Canary #44965552412 success. Last release script content did NOT change after Owner L0 PASS; only test pin revised.
8. All edits in Draft PRs, **no main merge**; Student TODO, Instructor private answer unchanged.

## 4. 실제 L2 결과 — 7개 스트림 및 원본 보호 상태

| Native 실제 관측 (ms) | Cycle1 / job 137032019268 | Cycle2 / job 137032019011 | 기준 |
| --- | ---: | ---: | --- |
| /clock max callback | 103.119892 | 105.290128 | < 300 |
| /odom max callback | 135.857996 | 138.593921 | < 300 |
| /scan max callback | 206.310351 | 199.246129 | 300ms 경계, raw Sensor freshness/Scan Header |
| CM /cmd_vel_pre_guard max callback | 70.347005 | 64.111992 | < 120 |
| Guard /axia/p2/base_guard max callback | 64.454136 | 59.987399 | < 150 |
| Supervisor /axia/safety/state max callback | 70.331809 | 64.089113 | < 150 |
| Supervisor /cmd_vel_supervised max callback | 70.332253 | 64.091841 | < 150 |
| **실 Guard 내부 CM age max** | **41.753971** | **16.490316** | 엄격 내부 TTL 수치 |

두 Cycle `AXIA_G07_TASK04_NATIVE_ONE_MOVING_RUNNER_RC=0 RVIZ_X11=1 GAZEBO_X11=1`, `AXIA_G07_NATIVE_L2_GUARD_SUPERVISOR_ACTUAL_CHILD_EXIT0_PASS`, `AXIA_G07_TASK04_NATIVE_MOVING_HEADLESS_SAFETY_VERDICT status=TASK04_REAL_GAZEBO_MOVING_L2_SCOPED_PASS first_failure=NONE`, 실제 Navigation ACK true, Localization ACK와 exact Cancel 포함 Native job 성공.

둘 다 first observed safety transition `BOOT_SAFE→NORMAL`, Guard latch 발견되지 않음. 독립 RMW *첫 위반 쌍*은 발생하지 않아 `RMW_FIRST_PAIR_UNVERIFIED`로 남아 있다. 이는 이번 실제 안전 전달 최대값 7채널 모두 기준 이내인 시연 성공과 별개인 원인 분석 결과이며, **근본원인 PROVEN 표시 금지**. ROSbag/Gazebo 실제 Startup→Goal→Stop→Cancel→Shutdown 수행한 SHA만 인수.

## 5. Artifact custody

GitHub Action artifact API에서 검증된 압축 ZIP SHA256 (강사 WSL2 raw rosbag checksum이 아님):
- Cycle1 `14731705895`, `sha256:c15831c035efda82227bbd4c1efd5e4618c78645f36bd5fb280d3f8b5677031f`, 17,873 bytes.
- Cycle2 `14731396763`, `sha256:ec5e1554dfc2b67a52f4e618d51bcd8bda644fc9d7d837f14173ce701b144670`, 19,357 bytes.
- Retention until **2026-12-06 00:09 UTC**. 장기 원본 보존이 필요하면 저장소 증거 운영 정책을 이용, 공개 원본 영상/rosbag 전체 업로드는 하지 않는다.

## 6. 새 Owner 스크립트 (Public PR #231, main 아닌 독립 branch)

`scripts/axia_g07_stabilization_wsl2_final_once.sh`:
- `readonly STUDENT_SHA='f7edb2d126502eeeed58ae014adadc7a2096d41b'`
- `readonly REVIEW_SHA='64ba0161e66126b4743b4b12a859f4a5349ae58a'` (실제 Native에서 검증된 Public 코드)
- `readonly CI_L2_HEAD='64ba0161e66126b4743b4b12a859f4a5349ae58a'`
- `readonly CI_L2_RUN=44965035965`
- `--self-check`: `AXIA_G07_STABILIZATION_WSL2_BOOTSTRAP_L0_PASS ... NO_ROS_NO_GAZEBO_NO_GOAL`.
- `--ci-check`: GitHub REST run의 event=push/status=completed/head_sha 일치/name 정확 일치 및 실제 2개 matrix job 각각 success 확인, 하나라도 문제면 exit3 Goal 차단. 실제 CI #44965454024에서 `PASS_TWO_STRICT_REAL_GAZEBO_GOALS_OWNER_WSL2_NOT_RUN`.
- `--run`: CI PASS 확인 이후에만 Owner WSL2 Ubuntu24.04/Jazzy/Harmonic/WSLg/분리 ROS_DOMAIN/GZ_PARTITION 검사, ROS 및 Gazebo 물리 실제 1 Goal, TTY 명시 동의, 14-topic rosbag, 안전 제어 체인, Nav/Loc 및 자식 종료, ZIP<=8MiB·SHA256/원본 산출. CI Goal 권한 위장 금지; `CERTIFIED_ESTOP=false`.
- **Owner WSL2 실제 실행 L3 NOT_RUN**; 결과에 `OWNER_SINGLE_NATIVE_NUMERICAL_CANDIDATE_PASS_SCOPED`가 보이더라도 보고서는 현장 원본 검수 이후 최종 인수. 신규 현장 오류가 있으면 동일 오류의 최초 상태/TTL을 공개 회귀로 RED→GREEN; 무작정 반복하지 않는다.

## 7. 범위 검수 판정 및 재현 커맨드

| 수준 | 판정 |
| --- | --- |
| L0 Student RED→GREEN | PASS (실패 재현 1/2/1 → 신규 4/4 + 59) |
| L0 Public 전체 및 Owner | PASS (331/3 SKIP + Owner 12/12 + live GitHub REST gate) |
| L1 ROS2 Jazzy | Native 시뮬레이션 런타임에서 ROS/Launch/Node 실제 확인. 강사 PC 독립 L1 미검증 |
| L2 Native Gazebo Harmonic strict Moving Goal | **PASS 2/2, 정확한 Student f7ed... / Public 64ba...** |
| L3 User WSL2 NVIDIA WSLg | **NOT_RUN**; 이 문서는 사전 준비·출고 수준 |
| 원본 DDS 첫 333ms+ RMW 원인 | UNPROVEN; 성공한 두 Cycle에 재발 없음 |
| main | NOT_MERGED |

공개 코드의 **고정된 본 보고서 커밋**에서 Owner를 가져와 실행하되, user WSL2에서 실제 `--run` 완료 및 증거 검수 전 L3 PASS라고 선언하지 않는다.
