# AXIA G07 Task04 — Owner Moving Goal L0 RED → GREEN 인과관계 보고서

- 작성: 2026-11-18 KST
- 상태: Stage A 최소 연결부 개발 및 **공개 CI L0 15/15 PASS**. 현장 L3 **HOLD**.
- 선행 실제 시뮬레이션 증거: Task03 Moving Goal CI [#44223320904](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44223320904), Task04 NO_GOAL GUI Xvfb L2 [#44238643061](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44238643061). **이 성공을 Task04 Moving Goal L3 성공으로 합산하지 않는다.**
- 기준: 공개 CI PR #169 시작 `efefd14c40bb652e20fad755271d4e8abd30913c`, Student PR #46 시작 `01752add2e30c90c4d3286ef3a450f97746ecb55`. 둘 다 main 미병합.

## 사이클 1 — 권한이 존재해도 Owner CLI 진입 및 종료 연결이 막힌 이유

**원본 첫 관찰:** Student `block_B/day07/h01_runtime/tools/p2_g07_ci_moving_goal.py`의 `run(args)`는 `owner_launch_pid`가 있으면 `admit_owner()`로 TTY, 세 프로세스 PID/세션, SHA를 확인한다. 그러나 `main()`의 argparse에 `--owner-launch-pid`가 없었다. 또한 실제 UUID 취소 함수 `_task03_exact_goal_terminal()`와 `task03_motion_window_end` 원본 마커는 `AXIA_G07_TASK03_FORMAL_CI` 조건에서만 실행되었다. **마지막 예외가 ROS/Nav2 실패라는 근거는 없었다. 최초 실패 경계는 CLI 진입점과 Owner 종료 계약이었다.**

**단일 가설:** 이미 구현된 Owner admission과 Task03 정확 UUID 취소 함수를 동일 엔진에서 연결하면, CI 전용 Goal 권한 위장 없이 기존 안전 상태와 결과 판정을 재사용할 수 있다.

- RED Student 테스트 커밋: `8a67993cb25fec776532c519c5f91b1d34e1c85b`.
- RED 공개 CI 워크플로 커밋: `18098959b33f4cc73bcdfecd1e7d8d999f07b564`.
- **실제 RED** [Run #44247187011](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44247187011): Owner CLI ERROR 1건, 취소 및 종료 경로 FAIL 2건, 기존 TTY/PID/SHA 거부 계약 1건 PASS.
- GREEN Student 수정: `72bee0bec79f07eb1332ee2f36532addd23b3877`. `main()`에 정수 `--owner-launch-pid`를 추가하고, `owner_mode`에서도 동일 UUID 취소와 종료 윈도 마커를 기록하도록 두 조건만 확장.
- **실제 GREEN** [Run #44247328046](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44247328046): **4/4 PASS**.

**반론과 안전 리뷰:** `--owner-launch-pid` 옵션 자체는 권한이 아니다. `run()`의 기존 `admit_owner`가 실제 `/dev/tty`, Git SHA, launch PID·동일 프로세스 세션·세 안전 노드 소유권, CI/Owner 자격 혼용을 차단한다. `_task03_exact_goal_terminal`은 `CancelGoal` 응답뿐 아니라 **동일 UUID의 ActionStatus=5**를 요구한다. 기존 Nav2·FSM·TTL·QoS를 변경하지 않았다.

## 사이클 2 — Owner 원샷이 CI 전용 Shell 경로로부터 분리되지 않은 이유

**원본 첫 관찰:** `scripts/p2_no_goal_smoke_ci.sh`는 기존 CI Goal과 공식 Nav2 종료, 실제 14-topic SQLite 증거를 이미 보유했지만, Goal 엔진 진입 및 bag/종료 승인 분기는 `GITHUB_ACTIONS=true`와 CI 플래그에 고정되어 있었다. 반면 성공한 기존 D07 GUI 원샷은 명시적으로 NO_GOAL만 허용했다. **마지막 실행 오류가 아니라 실행 경로 간 권한 계약의 단절을 최소 수정 대상으로 선택했다.**

- RED Student 테스트: `78db42c16369b69479be3fd560740eaf687a1c09`.
- **실제 RED** [Run #44247554353](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44247554353): Shell 5건 중 두 실패 — `AXIA_G07_TASK04_OWNER_MOVING_L3` 경로 부재와 `YES-P2-G07-GOAL` 수동 TTY 승인 미구현. 나머지 3개 PASS.
- GREEN 후보 코드: `8c64f721c781808bcec3b0adf4e3fae11718df08` → `f747535c404f16afe6c01f08fc75a902ec150de2`, 공식 CM Simple TF Owner 범위 수정 `8ddee740480c49e23eac1967032f51bd0ce3df04`, 회귀 계약 개선 `d95704b2600bcf461e266cf38407d6fa89161540`.
- **실제 GREEN** [Run #44248717847](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44248717847): Shell 5 + Owner CLI 4 + Simple TF 6 = **15/15 PASS**.

**수정의 핵심:** 기존 Gazebo 서버는 하나로 유지하고 GUI 클라이언트 `gz sim -g`와 RViz만 추가한다. Owner shell은 실제 controlling-TTY에서 정확 문자열을 입력받기 전 어떤 Goal 권한도 설정하지 않는다. 승인 후 기존 `admit_owner`가 다시 정확한 Student SHA·세 프로세스 PID·세션을 검증한다. `GITHUB_ACTIONS=true` 또는 CI Goal 권한을 Owner에서 설정하지 않는다. 기존 Scope 밖의 알고리즘·장애물·ROS 패키지·안전 TTL은 그대로 유지한다.

**공식 근거:**
- Gazebo Harmonic의 `gz sim -g`는 서버가 아닌 **GUI 클라이언트만** 실행한다: https://gazebosim.org/docs/harmonic/getstarted/
- ROS action `STATUS_CANCELED = 5`: https://github.com/ros2/rcl_interfaces/blob/rolling/action_msgs/msg/GoalStatus.msg
- Nav2 Lifecycle Manager가 정상화된 shutdown 전이를 관리한다: https://api.nav2.org/nav2-jazzy/html/md_nav2_lifecycle_manager_README.html
- 주의: WSLg D3D12 실제 스케줄링은 공개 CI Xvfb로 입증되지 않는다.

## 교육용 프롬프트 — 후배 개발자 실습

> 이미 안전 엔진의 `run()`에 Owner 인가 경로가 있다. `main()` CLI 인자와 Shell Goal 실행 권한만 비교하라. CI 권한을 복제하지 말고 실행 전에 TTY·SHA·PID 인가가 실효성 있게 적용되는지를 최소 RED 테스트로 증명하라. 정확 UUID 취소·ActionStatus 5·기존 Lifecycle 종료 코드를 재사용하고, 실제 CI 출력에서 GREEN을 확인한 범위만 성공으로 기록하라.

## 검증 범위 및 남은 작업

| 항목 | 실제 증거 | 판정 |
|---|---|---|
| 두 원격 PR HEAD 확인 | GitHub 원격 조회 | 완료 |
| Owner CLI / UUID 정확 취소 연결 | RED/GREEN 공개 L0 | PASS, ROS 미실행 |
| Owner Shell TTY/환경·GUI·종료 구조 | RED/GREEN 공개 L0 | PASS, 실제 TTY 입·출력 미실행 |
| 단일 실제 Gazebo Moving Goal + GUI + Contact + Action + SQLite | 별도 공개 CI 통합 실행 필수 | 미검증 |
| 강사 WSL2 GUI+D3D12 실제 주행 단일 인수 | 강사 원본 TAR/SHA256 필수 | NOT_RUN |
| SW 정지 / 인증 E-Stop | E-Stop 인증 범위 아님 | `CERTIFIED_ESTOP=false` |
| Git main | 병합 승인 필요 | `MAIN_MERGED=false` |

**최종 현재 판정:** `AXIA_G07_TASK04_OWNER_MOVING_L3=HOLD`, `AXIA_MVP_DEMO_ACCEPTED=HOLD`, `CERTIFIED_ESTOP=false`.

추가 개발 및 현장 오류 발생 시 Task01~03 과거 성공 테스트를 반복하지 않는다. **최초 안전 상태 전이·최초 타이밍 위반을 원본 로그에서 재구성 → 최소 CI RED → GREEN → 인접 TTL 영향 확인 → 별도 보고서 커밋**으로 이어간다.
