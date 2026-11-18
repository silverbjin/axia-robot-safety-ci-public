# AXIA D06 — G07 Task03/Task04 성공 재사용 강사용 Live Demo 개발 보고서

작성 2026-11-18 KST · **현재 범위: 신규 D06 실행기 L0 및 실제 G07 GUI 연결(Goal 없음)**

## 사용자가 원하는 강의 장면

Gazebo Harmonic 3D Waffle이 기존 공식 Nav2의 단일 승인 Goal로 실제 움직이고, CLEAR → SLOWDOWN → STOP을 수행하는 동안 RViz2에서 /scan, /odom, Costmap/Path와 교육용 Safety Bubble을 설명한다. 새 Nav2/CM/Safety Supervisor/Guard 구현 없음. G07 CM/Guard root cause 연구는 D06에서 반복하지 않는다.

## 재사용 원본(서로 다른 검증 세션을 합산하지 않음)

- **주행:** [G07 Task03 실제 Gazebo L2 #44223320904](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44223320904), exact Student runtime `01752add2e30c90c4d3286ef3a450f97746ecb55`, workflow `6bc8b0711ab056e63e100f3eede2c5f06cdf3856`. 공식 Jazzy/Harmonic/Nav2/Waffle, CM 56.642455ms/120ms, Guard CM age 53.971531ms/150ms, displacement 0.2111m, CLEAR/SLOWDOWN/STOP, odom stopped dwell 1.013s, native obstacle Contact0, Cancel status5, Nav2 ACK, CM exit0, SQLite 14/14. 오직 CI 시뮬레이션 범위 한정.
- **시각:** [G07 Task04 실제 Gazebo+RViz Xvfb #44238643061](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44238643061), SHA `5bb0cd72086f2f1a057f382649b773fff106f1f9`. 실제 Owner WSLg NO_GOAL GUI VISUAL [#169](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/169) PASS_SCOPED (Gazebo 물리월드와 RViz Costmap/Path 화면). 해당 코드의 `scripts/axia_g07_task04_public_owner_wsl2_pregate_once.sh` blob `a15cf37e1a1d2a0253029c0a1dd8e2530e307c25`를 고정.
- **이전 D06 통합 근거:** [#43667573251](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43667573251) 실제 Xvfb moving Goal+RViz 성공. 이후 WSL2 Owner에서 Guard CM age 169.168ms와 CM RMW source 184.415ms로 안전 래치 발생했으므로 구 Owner 스크립트 재실행 금지.
- G07 Task02의 official Simple TF `base_shift_correction=false`는 저속 Gazebo 단일 시나리오의 CI-전용 검증 프로파일이다. TF motion time-shift correction을 생략하므로 하드웨어·범용 주행 안전 검증이 아님.

## 신규 구현 범위

- `d06/scripts/axia_d06_g07_classroom_once.sh`: Task03/04 원본 run/source SHA 검증, Task04 검증된 GUI 스크립트의 git blob hash 검증 후 WSL2에서 실제 Gazebo+RViz GUI 원샷을 **그대로 위임**. `--self-check`(오프라인), `--ci-status`(GitHub Actions 동일 SHA·success 조회), `--doctor`(Owner preflight), `--gui-only`(실제 NO_GOAL Gazebo+RViz), `--live`(실제 Moving Owner 출고 전 **명시적 HOLD**).
- `d06/tests/test_d06_g07_classroom_reuse.py`: 계약 테스트 6개, GitHub Actions에서 GUI/Goal 권한 위장 및 불법 publisher 금지.
- `.github/workflows/axia-d06-g07-classroom-reuse-public-l0-20261118.yml`: 공개 Ubuntu L0만, 외부 앱 인증·ROS/Gazebo 없이 6개 회귀 실행.
- 공식 Nav2, Student 원본, CM/Guard TTL, /cmd_vel publisher, 물리 Collision Monitor를 변경하지 않음. **새 Owner Moving Goal 실행기는 이 커밋에 포함되지 않는다.** 기존 G07 Task04가 실제 WSL2 Moving Goal을 아직 배포하지 않았기 때문이다.

## RED → GREEN → REFACTOR → REVIEW → COMMIT (실제 출력)

1. RED: 신규 실행기가 없는 상태에서 `python3 -m unittest discover -s d06/tests -p 'test_d06_g07_classroom_reuse.py' -v` → `FAILED (failures=4, errors=2)`.
2. 초기 GREEN 후보: 테스트 5/6; CI 환경 차단에서 `GH_CLI_REQUIRED`가 먼저 발생해 `test_owner_gui_path_rejects_github_actions_before_download`가 실패.
3. 최소 수정: GUI 모드는 `GITHUB_ACTIONS` 검사 후 `gh`/네트워크 검사하도록 순서 교정.
4. GREEN (local Python3, ROS 미실행):

```text
Ran 6 tests in 0.012s
OK
```

5. REFACTOR/REVIEW: 강사용 wrapper는 새 Goal 발행 0, CI-only `GITHUB_ACTIONS=true` 위장 0, 후속 task가 Owner Moving 인수되지 않았을 때 `D06_G07_CLASSROOM_MOVING_OWNER_NOT_RELEASED`로 즉시 실패. 소스 tree SHA/CI run pin은 기존 성공 증거를 재사용. 공개 CI Actions의 실제 실행 결과는 별도로 확인한다.

## 사용 명령

검증된 D06 공개 SHA로 checkout한 뒤:

```bash
bash d06/scripts/axia_d06_g07_classroom_once.sh --self-check
bash d06/scripts/axia_d06_g07_classroom_once.sh --ci-status
# WSL2 Owner에서만: 기존 Task04 실제 GUI-only Gazebo + RViz 실행
bash d06/scripts/axia_d06_g07_classroom_once.sh --gui-only
```

`--live`는 **아직 사용하지 않는다**. 공개 Student의 기존 단일 Goal은 `GITHUB_ACTIONS=true`를 요구하므로 Owner WSL2에서 이를 위조할 수 없다. G07 Task04의 정식 single-owner-Goal runner가 release되면 그 정확 SHA만 얇게 D06 wrapper에 연결한다. D06 자체의 120ms CM 튜닝, LTTng 연구, ROS 안전제어 확장 금지.

## 판정 경계와 후속 필요 작업

- 과거 Task03 **진짜 Gazebo 주행 L2 PASS**, Task04 강사 **WSLg NO_GOAL GUI PASS_SCOPED**: 각각 유효하나 하나의 통합 Moving Goal L3로 승격 금지.
- 신규 D06 실행기 L0: 로컬 6/6 PASS, 공개 CI 결과 별도 확인. 이번 턴에 새 Gazebo/WSL2 수행 없음.
- **D06 같은 세션의 Gazebo+RViz Moving L2 및 강사 Moving Owner WSL2 L3: NOT_RUN / BLOCKED_WAITING_G07_OWNER_MOVING_RELEASE.**
- Fail-closed: Guard 150ms, Scan 300ms, 최초 안전 상태 전이, Stop odom ≥1s, Contact 0, 동일 Goal Cancel ACK를 유지. 오류 발생하면 현장 재시도 대신 기존 G07 공개 CI 회귀로 인계.
- 전체 `AXIA_MVP_DEMO_ACCEPTED=HOLD`, `CERTIFIED_ESTOP=false`, 사용자 승인 없는 main 병합 금지. SW stop을 인증된 E-Stop으로 주장하지 않음.

## 공개 CI 최종 결과 — 2026-11-18

- **실제 신규 D06 공개 CI L0:** [Actions #44249143480](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44249143480), commit `952e14bbf2c7f371de1bf57b4e5c7be84764088f`, job `134615261209`, **completed/success**.
- 실제 GitHub Actions stdout: `Ran 6 tests in 0.008s` → `OK` → `D06_G07_CLASSROOM_PUBLIC_L0_PASS SIX_TESTS NO_ROS_NO_GAZEBO_NO_GOAL`. `D06_G07_CLASSROOM_OWNER_MOVING_L3=NOT_RUN` 및 `AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false`.
- 로컬 `git hash-object` vs GitHub 원본 새 실행기 blob 동일 `f3098e2b667473a79903069b7e62d1a6cd2f4c50`; 단위 테스트 파일 blob `0b4fce8e6216394f0d7969751cd119b4158fde65`.
- 실제 `--live` 로컬 fail-closed 확인: `RC=3`, `D06_G07_CLASSROOM_HOLD=D06_G07_CLASSROOM_MOVING_OWNER_NOT_RELEASED`; 실제 ROS/Gazebo/Goal 미실행.
- 공개 Draft [PR #170](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/170) 기반 브랜치 `feat/d06-g07-classroom-reuse-20261118`. 개인 RAW, private Instructor, 학생 정답 업로드 없음. main 병합 미승인.

**본 최종 CI는 Python/Bash L0입니다.** G07 Task03 Moving L2 #44223320904와 Task04 Owner GUI PASS는 별도 원본 증거로 **재사용**했지만, 신규 D06 동일 세션 Moving+GUI L2나 WSL2 Moving L3는 수행하지 않았습니다.

## 2026-11-18 추가 개발 — 실제 **같은 세션** Gazebo+RViz+Goal CI RED/부분 성공, 최종 출고 HOLD

### 실패 원본과 원인별 RED→GREEN 기록

1. [#44252599540](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44252599540) **FAIL/RED L0**: 새 Student 테스트가 원래 스크립트의 *주석* `GITHUB_ACTIONS=true`까지 권한 위장으로 오인. 원래 코드·ROS 미수정, 테스트를 실제 `export GITHUB_ACTIONS=true` 금지로 좁힘. Student commit `8d1fb87df3eb9f0661700b8e1f03fc57bcce7454`.
2. [#44252849158](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44252849158) **RED after native NO_GOAL positive Contact witness**: apt Xvfb·rviz2 설치 정상, 단독 셸이 `/opt/ros/jazzy/setup.bash` 소싱 전 `command -v rviz2`를 확인해 `exit 1`. 환경 소싱만 추가한 public CI commit `3009d7ed86a24c9e64e7690a680ca3420b957971`.
3. [#44253212332](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44253212332) **신규 실물 CI 검증/FAIL(종료 게이트)**: Student `8d1fb87df3eb9f0661700b8e1f03fc57bcce7454`, public workflow `3009d7ed86a24c9e64e7690a680ca3420b957971`. Native NO_GOAL Contact positive calibration, 실제 `D06_G07_CI_GAZEBO_RVIZ_X11_READY_BEFORE_REAL_GOAL`, `D06_G07_REAL_GAZEBO_AND_RVIZ_WINDOWS_VISIBLE_DURING_ACTUAL_GOAL` 성공. 한 개의 실제 Nav2 Goal UUID `4a90420572dd4e08a67d750b54ee3a46`로 CLEAR→SLOW→STOP, native STOP pose ACK(1.528788s), 실제 이동 **0.2193m**, odom ZERO dwell **1.046229s**, exact Goal CANCEL ACK/status5는 성공.
   - 같은 세션 실제 ROS Observer inter-node max: clock 97.351306ms, CM 87.708626ms, Guard 110.082238ms, odom 132.649514ms, Scan 248.196120ms, Supervisor 87.738993ms, source 85.481123ms. 기존 Guard 150ms/Scan 300ms **관찰 주기** 안에 있음. Guard 내부 `cm_age` 정식 사후 리뷰는 CI failure 전에 미실행 → **미검증**이며 CM RMW source 120ms 마진도 이 실행의 정식 checker output 미확보 → **미검증** (observer max를 RMW proof라고 보고하지 않음).
   - **최초 실제 차단:** `G07_MOVING_GOAL_ORDERED_SHUTDOWN_BLOCKED`; `g07_ordered_shutdown.json` status `BLOCKED_LIFECYCLE_NAVIGATION_SERVICE_TIMEOUT`, `navigation_ack=false`, `localization_ack=false`, `cm_clean_process_exit_verified=false`. 이 실패 때문에 runner rc3/Actions failure. 로봇이 정지했다고 정상 종료된 것이 아니다. `D06_G07_REAL_GOAL_RUNNER_FAILED_RC=3`, 인수/출고 HOLD 유지.
   - 이번 Run에서 GUI 창·Goal·정지까지 실제 성공했지만 **그렇다고 강사 Owner WSL2 라이브 주행 PASS는 아님**. Xvfb ≠ WSLg, Guard 내부 age/CM RMW 정식 증거·정상 Nav2 종료 누락.

### 중복 개발 중단 및 G07 인계

- G07 Task04에는 이미 자체 `AXIA_G07_TASK04_CI_GUI_MOVING` 및 `AXIA_G07_TASK04_OWNER_MOVING_L3` 보호 경로가 존재함을 뒤늦게 확인. 따라서 D06 신규 Student PR [#51](https://github.com/silverbjin/axia-robot-safety-student/pull/51)은 **진단용/NO MERGE**, Owner Goal 경로로 사용하지 않는다.
- 최초 Navigation Lifecycle manager 서비스 타임아웃과 동일 Run UI/RViz 종료 부하의 인과는 **미확정**. 기존 G07 Task04 issue/CI에 첫 경계 회귀·read-only 로그 계측을 이관; D06에서 재시작/TTL 완화, 공식 Nav2 lifecycle 포크, 반복 현장 재시도 없음.
- D06 공개 실행기의 `--self-check`와 `--ci-status`는 원래부터 **ROS/Gazebo를 시작하지 않는 검증 전용**. 수정 branch에서는 `D06_G07_CLASSROOM_VERIFICATION_ONLY_NO_GAZEBO_NO_RVIZ`를 명시적으로 출력함 (public L0 [#44253023036](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44253023036) PASS). **과거 SHA `e9ccdfab...`는 실제 GUI/Goal 실행용 릴리스 아님**.
- 이 단계 결과: `D06_SAME_SESSION_MOVING_CI=HOLD_SHUTDOWN`, `D06_OWNER_MOVING_WSL2=NOT_RUN`, `AXIA_MVP_DEMO_ACCEPTED=HOLD`, `CERTIFIED_ESTOP=false`. **출고 승인 전 실제 Moving Goal 명령 배포 금지.** 모든 개발 브랜치 Draft, main 미병합.

### 다시 시도할 경우 필요한 최소 회귀 계약(G07 소유)

- ROS-free L0에서 `Navigation` 서비스가 사라짐/응답 지연(기존 60s 전체 예산)을 **최초 실패로 판정**하고 종료 ACK=false 시 PASS로 승격하지 않는 테스트. 기존 `p2_g07_ordered_shutdown.py` 계약을 우선 재사용.
- 같은 실제 L2에서 `Goal UUID CANCELED` 후 GUI client lifecycle과 Navigation/Localization service health를 **읽기 전용**으로 먼저 기록, 확정된 단일 간섭 경계만 수정.
- L0 GREEN 뒤 **한 번** 실제 Gazebo+RViz+Goal/CM120/Guard150/S02 Contact0/SQLite14/Cancel+두 Lifecycle ACK/CM clean exit가 모두 통과하면 D06 얇은 wrapper가 해당 G07 승인 Owner release를 연결. 본 CI와 다른 SHA의 옛 PASS를 합산 금지.
