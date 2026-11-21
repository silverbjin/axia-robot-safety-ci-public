# AXIA G07 G40 — 정확 SHA 고정 강사 WSL2 한 번 최종 인수 실행기 출고 준비 보고

**날짜:** 2026-11-21. **상태: PUBLIC_STRICT_NATIVE_2_OF_2_PASS / OWNER_RUNNER_BOOTSTRAP_CI_GREEN / OWNER_WSL2_L3_NOT_RUN / MAIN_NOT_MERGED / CERTIFIED_ESTOP=false.**

## 1. 기준과 인수 범위

- 기준 문서 `AXIA_Robot_Safety_MVP_Baseline_Scenario_Acceptance_v1_KO.md`의 기존 G07 시연. 공식 ROS 2 Jazzy/Gazebo Harmonic/TB3 Waffle/Nav2/Collision Monitor, 원래 MultiThreadedExecutor 2-worker 재사용. CM120ms/Guard150ms/Scan·Odom·Clock300ms 불변.
- Public runtime/reviewer **정확 SHA `0711e583f3c0c546a64c687edd8e280c2ae8e776`**, Student runtime **정확 SHA `fb1aae6cbde54ff0ed4e78317f403aa5cef4d550`**. Public Draft PR #215, Student Draft PR #89. Instructor 정답 Private, Student TODO 패키지 별도. GitHub main 병합 없음.
- **실제 ROS Jazzy/Harmonic Moving Goal** Native Public Run [#44878063103](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44878063103) `AXIA G07 Original Multi First Scan RMW Exact Pair Diagnostic Native L2` `event=push`, `status=completed`, `conclusion=success`, `head_sha=0711e583...`; 독립 matrix jobs:
  - Cycle1 job **136767083787** `success`, native runner rc0 Gazebo/RViz GUI=1/1, Guard+Supervisor children exit0, Guard internal CM age 123 samples max38.596342ms.
  - Cycle2 job **136767083533** `success`, native runner rc0, Gazebo/RViz GUI=1/1, both child exit0; 실제 물리 SLOW 정렬 후 CLEAR→SLOW→STOP 완료, Nav/Loc ACK, same Goal UUID Cancel, 실제 1초 odom zero dwell; 14-topic rosbag cwd custody는 native workflow original check 통과.
- **첫 TTL 위반 양쪽 모두 null** (Observer postGoal): Cycle1 최대 Clock100.832467ms, Guard66.004042ms, Odom137.500127ms, CM preGuard70.036140ms, Scan209.009104ms, Supervisor69.688938ms; Cycle2 Clock98.705441ms, Guard74.900914ms, Odom142.444037ms, CM97.634351ms, Scan204.448616ms, Supervisor98.776865ms. 기존 120/150/300ms 이내.
- ZIP custody (공개 숫자 evidence, 원본 private raw bag 미공개):
  - Cycle1 artifact **14696538580**, ZIP SHA256 **63adee9b3e1c916359b40179c471afb6d3df60b430226857582ff702112651ba**, 파일 내부 SHA sidecars **8/8 PASS**.
  - Cycle2 artifact **14696233235**, ZIP SHA256 **b35000e43737115da606d447d63fb6518e426ea529dab14c7bbc5d6f1f3a85da**, 내부 sidecars **8/8 PASS**.
- 성공한 2/2 이전의 **후속 간헐적 장애 가능성 제거/근본 원인 입증을 주장하지 않음**. #44876964129 원 Observer first CM received380.607ms vs independent48.571ms, #44877524595 wake A/B 0/2 및 earlier shutdown HOLD는 실제 남은 위험. G40은 **동일 SHA에서 scoped 실증된 시연 인수 실행기**만 출고하며 영구 안전성 보증 아님.

## 2. 재사용한 원샷 (복제 개발 없음)

- **파일:** `scripts/axia_g07_stabilization_wsl2_final_once.sh` (기존 owner 원샷 최소 PIN/출고 게이트만 갱신).
- PIN: `STUDENT_SHA=fb1aae6cbde54ff0ed4e78317f403aa5cef4d550`, `REVIEW_SHA=0711e583f3c0c546a64c687edd8e280c2ae8e776`, `CI_L2_HEAD=0711e583f3c0c546a64c687edd8e280c2ae8e776`, `CI_L2_RUN=44878063103`. 정확 workflow 이름과 matrix Cycle1+2 완료/성공 검증.
- `--self-check`: 실제 ROS/Gazebo/Goal 없이 pinned values와 기초 계약 검증.
- `--ci-check`: GitHub API Run exact SHA, name, completed-success, **두 job** completed-success 아닌 경우 **NO_GOAL_HOLD(rc=3)**. 서버 403, 잘못된 SHA, 한 Cycle 실패 모두 차단.
- `--run`: 반드시 `--ci-check` 통과 후, Owner WSL2 Ubuntu24.04/Jazzy/WSLg 및 `/dev/tty` controlling TTY 확인. 공식 Gazebo/RViz GUI, 25 Debian package + 5 official file hash, Student/Public exact git SHA, ROS_DOMAIN/GZ_PARTITION 분리, 실제 LiDAR/CM/Guard와 **Goal 단 한 번 수동 TTY `YES-P2-G07-GOAL` 승인**. 새 ROS 노드/Planner/안전 TTL 변경 없음. 기각된 Executor guard wake, 20ms bounded spin, Single/EventsExecutor 환경 모두 제거/Owner 비활성.
- 실패 시 최초 오류·타이밍·FSM·shutdown과 필수 숫자만 ZIP ≤8MiB+SHA256으로 custody. 전체 raw bag/private paths/해답은 Public에 업로드 안 함.
- Owner의 실제 localization shutdown ACK 또는 formal RMW TTL HOLD로 바뀌어도 시각적 성공만으로 rc0 승격하지 않도록 **rc=3**로 수정. 정상 실행 중 `HOLD_RAW_REVIEW_AND_VISUAL_PENDING`은 숫자 후보 상태이며 강사 현장 증거 리뷰 전에는 `OWNER_L3_ACCEPTED` 표시 금지.

## 3. RED→GREEN→REFACTOR→REVIEW→COMMIT 실제 테스트

- RED Public commit `1db43c2947eced1799173700aa56a3cd03f863e7`; [실제 Python RED CI #44878439518](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44878439518): **5 FAILED, 327 PASSED, 3 SKIPPED**. 원인: 이전 Owner script PIN/Run, formal shutdown exit0, 미제거 실험 모드.
- GREEN 원샷 수정 commit `313565e54dadb38945b32498783a8966765f1e3c`; 기존 Legacy Owner wrapper 정적 contract PIN 갱신 + 안전 실험 제거 테스트: Public `abd12a4aa83eecf6583a558f6cfc8a7aaad978e0`, `d2fd50f58b21c8d56aca3861ff824591c69f8f4b`. [실제 전체 CI #44878630445](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44878630445): **332 PASSED, 3 SKIPPED**, Runner Canary SUCCESS.
- **추가 부정 테스트:** GitHub API는 정확히 2/2 성공을 돌려주지만 Owner `--run`에 controlling TTY 또는 CI 권한이 없는 상황은 **Goal 전에 거절**한다. `tests/test_g07_stabilization_wsl2_release.py` in Public commit `c4d049ca7a473c99c2038a3205a8968054e8476d`; [실제 전체 CI #44878766533](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44878766533): **333 PASSED, 3 SKIPPED**. 기존 shell `bash -n`, `--self-check`, positive+negative `--ci-check` fixtures 포함.
- CLI 실제 현장 `--run`은 **강사 WSL2에서 아직 미실행**. 이 문서 및 공개 CI는 형식 검증/Ubuntu actual native L2이지, WSL2 GPU/WSLg 동작 검증이나 인증된 하드웨어 E-Stop 테스트가 아니다.

## 4. 강사 WSL2 한 번 최종 실행, 후속 판정

1. 사용자 WSL2 실제 **TTY가 있는 터미널**에서 정확 release Public SHA로 git fetch/checkout→`git rev-parse HEAD` 확인. `bash -n`→`--self-check`→`--ci-check`→`--run` 순서로 **한 번 실행** (GitHub 공개 계정 접근 필요). 단일 쉘 명령 전체는 검증된 release SHA로 사용자에게 별도 전달.
2. GUI Gazebo/RViz가 양쪽 열리고 정확한 하나의 Goal을 승인. PreGoal Scan/Clock/Odom, 실제 CLEAR/SLOW/STOP 속도, 14-topic 원본 bag, Goal/Cancel UUID 동일, odom zero dwell ≥1초, Nav/Loc ACK, Guard/CM child exit0 및 최초 120/150/300ms TTL raw review 필요.
3. 성공적 candidate 출력은 `AXIA_G07_TASK04_OWNER_SINGLE_NATIVE_NUMERICAL_CANDIDATE_PASS_SCOPED`와 `AXIA_G07_TASK04_OWNER_VISUAL_AND_RAW_REVIEW_PENDING`. 이때도 아직 `AXIA_MVP_DEMO_ACCEPTED=HOLD` (원본 raw·화면/인수 담당 검수 전).
4. 수치/GUI/최초 safety transition·모든 TTL과 종료 evidence를 실제 검수했을 때만 Owner L3 인수 완료. 현장 오류시 해당 **최초** 실패를 CI 재현 RED→GREEN에 먼저 편입하고 새 SHA의 실제 native 2/2 후 다시 인수; 동일 현장 재실행 반복 금지.
5. 본 release와 Owner 검수는 `main` 병합과 무관. 사용자 별도 승인 없이는 main 병합하지 않음. **SW STOP은 인증된 물리 E-Stop 아님.**

**지금:** `G00=EVIDENCE_PASS`, `G10=FIRST_RMW_CLASSIFIED_ROOT_UNPROVEN`, `G20=ACTUAL_L2_2OF2_PASS`, `G25=LATEST_L2_SHUTDOWN_CLEAN_PASS`, `G30=PUBLIC_L2_2OF2_PASS_EXACT_SHA`, `G40=PUBLIC_OWNER_RELEASE_CI_GREEN`, `G50=OWNER_WSL2_NOT_RUN`, `G60=MAIN_NOT_MERGED`.
