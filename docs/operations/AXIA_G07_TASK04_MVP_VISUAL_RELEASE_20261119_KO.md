# AXIA G07 Task04 — 교육용 MVP 이동·감속·정지 실증과 WSL2 원샷 출고 기록

## 결정 및 범위

- 우선 목표: 강사 WSL2에서 Gazebo/RViz를 열고 **실제 TurtleBot3 Waffle이 CLEAR → SLOW → STOP**을 보여주는 한 번의 시연
- 재사용: 기존 공식 Nav2 Goal 전송, Collision Monitor 속도 감소/정지, Gazebo 실물 장애물, Task03 Goal UUID 취소
- 유지: CM 감속 0.75m, STOP 0.40m, slowdown_ratio 0.30, Safety Supervisor와 Guard 및 TTL 불변
- 유예: 사후 Localization Lifecycle 종료 ACK와 장기 안정성 인수. 단, 기능 시연 완료와 안전 인수는 반드시 구분
- 인증 E-Stop이 아닌 시뮬레이션 소프트웨어 정지. **CERTIFIED_ESTOP=false**

## 1. 최초 현장 장애 — 원본 증거

강사 WSL2 `owner-moving-3MKlJSN1`:

- 실제 `Goal` 전송, Nav2 주행, AMCL 및 PREGOAL PASS
- 약 1.97초 지연된 ActionStatus EXECUTING 관측 전에 로봇이 실제 전진하고 물리 SLOW 구간에 진입
- 이후 기존 CLEAR 단계에서 CM 속도 >0.03m/s를 요구하지만 이미 실제 CM 속도는 최대 약 0.0195m/s
- 최초 예외: `CI_MOVING_GOAL_TIMEOUT_CLEAR`
- 따라서 Nav2, Goal 전달 또는 CM 감속 알고리즘을 새로 개발할 문제가 아니라 시연 단계 전환의 시점 불일치

## 2. RED → GREEN → 실제 Gazebo 현장 조건

Student PR #46 (`fix/g07-task03-public-proof-20261118`):

- RED 범위 테스트 신규 커밋 `b434dae7c28b5a776c63571ba00d5f1f22480c55`; 해당 커밋의 CI RED 실행은 없음 (사전 코드에 해당 함수/단계 부재 확인)
- 최초 GREEN `494aece35ea1380e665dbfb0042b24e08e795976`: CLEAR 물리 속도를 ActionStatus보다 먼저 기록하고 나중에 같은 Goal이 EXECUTING임을 확인. 기존 `move_ci_verified`와 `obstacle_world_pose`로 원통을 실제 SLOW 약 0.62m 위치로 이동; 기존 `plan_stop_fixture`로 STOP 약 0.34m 이동
- 후속 GREEN `2ca257c80fa12f35d801ca525cb16bebbaaa0c8f`: 실물 STOP + 1초 Odometry ZERO 후 **기존 Goal UUID 취소를 즉시 실행**. 사후 15초 Observer soak만 MVP 한정 생략. Guard TTL/CM/AMCL/Nav2 수정 없음

실제 ROS 2 Jazzy + Gazebo Harmonic + Waffle + Nav2 + RViz 공개 CI Run [#44468919246](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44468919246):

| 물리 단계 | LiDAR 전방(m) | Supervisor(m/s) | CM(m/s) | 증거 |
|---|---:|---:|---:|---|
| CLEAR | 2.023373 | 0.036928 | 0.036928 | 실물 전진 |
| SLOW | 0.630976 | 0.117723 | 0.035317 | Native world [-1.31,-0.50] set_pose ACK, 30% 감속 |
| STOP | 0.384134 | -0.059183 | 0 | Native world [-1.540828,-0.487720] set_pose ACK |

- Odometry ZERO 유지 1.021초
- 실제 **Goal UUID `97ba4023ca77438da0ef5d2d55b44a48` CANCELED PASS**
- Gazebo/RViz 두 GUI 창 관측, 실물 LiDAR Scan과 CM 명령 근거
- 검사 당시 Source/CM/Guard/Scan/Odom/Clock의 관측 간격 정상 (CM 약 56.1ms, Guard 약 61.2ms, Scan 약 213.7ms)
- **이 Run의 전체 CI 결과는 FAIL**: Navigation Lifecycle ACK 이후 Localization 서비스가 30초 안에 응답하지 않음. 따라서 정식 L2 인수 FAIL/HOLD. 실제 시연 단계 성공을 전체 통합 PASS로 오인하지 않음
- 별도 Run [#44470006649](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44470006649)은 시연 시작 전 `LOCALIZATION_START ... SERVICE_MISSING`으로 실패. 동일 현장 재시도를 무조건 반복하지 않음

## 3. 교육용 시연 결과와 정식 종료 결과 분리

공개 CI PR #169:

- `scripts/axia_g07_mvp_visual_verdict.py`: **원본 Goal·Scan·CM·Odom·정확 UUID 취소·양 GUI 창**과 사후 Localization SERVICE_TIMEOUT이 모두 확인됐을 때만 교육용 물리 시연 후보를 인정
- 안전 TTL, CM 설정, Nav2 코드 및 실제 Goal 승인 과정은 변동 없음
- 교육용 표시: `MVP_VISUAL_L2_PASS_FORMAL_SHUTDOWN_HOLD` 또는 `MVP_OWNER_NUMERICAL_CANDIDATE_FORMAL_SHUTDOWN_HOLD`
- 모든 출력에서 `formal_l2_accepted=false`, `owner_wsl2_l3_accepted=false`, `certified_estop=false`
- 이는 **정식 시연 인수의 대체가 아니며**, 미확인 화면 내용도 자동 PASS로 표시하지 않음

## 4. 공개 CI의 출고 사전검증

- Student 고정 SHA: `2ca257c80fa12f35d801ca525cb16bebbaaa0c8f`
- 공개 Reviewer/진단 소스 SHA: `d60beed5e18d8104b254f17476d47f1d1917a7eb`
- Owner 원샷/Bootstrap 테스트 포함 공개 소스 SHA: **`9be07591470356401b038b3b000302947e9451f2`**
- 공개 Owner Bootstrap [#44470842058](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44470842058): **9/9 L0 PASS**, Bash -n 성공. ROS/Gazebo/WSLg 현장 동작까지 의미하지는 않음
- CI witness 빌드에 설치된 Gazebo dev 패키지가 libgz-transport13 13.6 → 13.7을 변경하는 문제는 빌드 이전 원래 25+5 core parity 검사로 분리했으며, 이를 WSL2의 정확한 런타임 동등성으로 주장하지 않음

## 5. 강사 WSL2 Ubuntu 24.04 — 하나의 실행 명령

WSL2 Ubuntu 터미널에서 아래 블록을 한 번 실행. 설치된 ROS2 Jazzy, Gazebo Harmonic, Nav2 공식 overlay 재사용. 다운로드 뒤 `--self-check` 후 같은 소스 `--run` 실행:

```bash
(
  set -Eeuo pipefail
  PIN='9be07591470356401b038b3b000302947e9451f2'
  SCRIPT="$(mktemp --suffix=.sh)"
  trap 'rm -f "$SCRIPT"' EXIT
  curl -fL --retry 3 --max-time 90 \
    "https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public/$PIN/scripts/axia_g07_task04_owner_moving_l3_once.sh" \
    -o "$SCRIPT"
  bash -n "$SCRIPT"
  bash "$SCRIPT" --self-check
  bash "$SCRIPT" --run
)
```

- Gazebo·RViz GUI와 실제 시연 전용 Goal은 기존 Owner 프로세스가 관리
- 전송 전 실제 터미널에서 `YES-P2-G07-GOAL` 승인 1회 필요, 자동 동의하지 않음
- 실제 CLEAR → SLOW → STOP을 관찰하고, 오류 시 기존 원본 TAR/SHA256 및 소형 `.diagnostics.zip`을 보존
- **정식 Localization 종료 ACK가 실패해도** 위 물리 조건과 정확 UUID CANCELED가 확인된 경우에만 `AXIA_G07_TASK04_OWNER_MVP_CLEAR_SLOW_STOP_GOAL_CANCEL_CANDIDATE` 표시 (교육용 후보, 화면 인수 미완료)
- `AXIA_G07_TASK04_OWNER_MOVING_L3=HOLD`, `AXIA_MVP_DEMO_ACCEPTED=HOLD`, `CERTIFIED_ESTOP=false` 유지. 강사 화면에서 실제로 관측한 후 교육용 시연 가능 여부 별도 판단

## 6. 소스·검증과 남은 작업

수정 파일:

- Student `block_B/day07/h01_runtime/tools/p2_g07_ci_moving_goal.py`
- Student `block_B/day07/h01_runtime/tools/p2_g07_ci_moving_goal_oracle.py`
- Student `block_B/day07/h01_runtime/tools/test_g07_task04_mvp_stage_sequence.py`
- CI `.github/workflows/axia-g07-task04-owner-moving-native-l2-20261118.yml`
- CI `scripts/axia_g07_mvp_visual_verdict.py`
- CI `scripts/axia_g07_task04_owner_moving_l3_once.sh`
- CI `tests/test_g07_task04_owner_moving_bootstrap.py`

미검증: 사용자 WSL2/WSLg 실제 GUI L3, 교육 현장 화면 관찰, 후속 Localization 종료 정상성, 정식 전체 21/21 통합 인수. **main 미병합**, PR #46·#169 유지. 기능 시연 재개에 불필요한 안정화 개발은 유예.
