> **2026-11-19 최신 출고 판정 — D06 Moving Goal HOLD / NO_GOAL ONLY.** 강사 WSLg 원본 Safety Scan 819.175ms > 300ms, 최근 공개 native NO_GOAL #44325953833의 첫 Safety Scan 356.136ms >300ms, Moving #44325984617의 Nav2 lifecycle `SERVICE_MISSING`은 각각 독립적인 신규 안전·종료 실패입니다. 아래에 보존된 과거 `--live` 예시를 **실행하지 마십시오.** 현재 D06 launcher는 `--live`를 네트워크/ROS/Goal 이전에 `D06_G07_OWNER_MOVING_RELEASE_HOLD_SCAN300_NAV2_SHUTDOWN`으로 차단합니다. 기존 G07 동일 소스 L2 성공은 역사적 증거로 유지하되, 최신 전체 시연을 PASS로 승격하지 않습니다. NO_GOAL 측정은 공개 SHA `e0c7502bb7acd3bd1f59e8a712bb3f4ed9bcdff8`의 `d06/scripts/axia_d06_g07_wslg_sensor_no_goal_once.sh --run`만 사용하십시오. 구체적 원인·RED→GREEN/CI 증거: [최신 보고서](AXIA_D06_G07_TASK04_WSLG_PIN_REFRESH_RED_GREEN_REPORT_20261119_KO.md). `AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false`, main 미병합.

> **2026-11-19 최신 갱신(기존 아래 기록을 대체하는 별도 결과):** D06 Owner `--live`는 G07 PR #169의 최신 실제 L2 성공 [#44268914763](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44268914763) / Student `d7ffec1ce73f0c4e672ea0fc51a1678139dc5a6f`로 갱신되었습니다. WSLg D3D12은 원본 G07 Gazebo/RViz GUI 자식에만 적용하며 물리/센서/안전 노드에는 전역 주입하지 않습니다. 새 공개 L0 [#44338101552](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44338101552) 15/15 PASS, 실제 D06 Wrapper WSL2 L3 NOT_RUN, MVP HOLD, main 미병합. 교육용 전체 RED→GREEN 보고서는 [AXIA_D06_G07_TASK04_WSLG_PIN_REFRESH_RED_GREEN_REPORT_20261119_KO.md](AXIA_D06_G07_TASK04_WSLG_PIN_REFRESH_RED_GREEN_REPORT_20261119_KO.md)를 참고하십시오.

# 2026-11-18 D06 최신 인계 — G07 Task04 실제 통합 CI GREEN 재발견 및 Owner 후보 연결

> 이 섹션은 아래 과거 D06 실험/출고 HOLD 기록보다 최신입니다. **G07 Task04의 실제 성공한 소스를 찾아 D06에 연결했지만, 강사 WSL2 Goal L3는 아직 실행되지 않았습니다.** ROS-free L0와 과거 동일 SHA 실제 L2 근거를 혼합하지 않습니다.

## 1. 실증한 G07 GREEN — 이미 성공한 작업을 다시 만들지 않음

- **정확히 한 세션의 네이티브 L2:** [공개 GitHub Actions #44249348860](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44249348860), workflow HEAD `6b98a18fa7abc80401a129f715ace7703ab54286`, 공개 Student SHA `1129cd8804954fd6481d1b6b4ebf0e0b98c68c3c`, job `134615932217`, 녹색 `success`, 실제 결과 `TASK04_REAL_GAZEBO_MOVING_GUI_L2_SCOPED_PASS`, `first_failure=NONE`, 실제 Gazebo 및 RViz X11 창 2개. 원본 allowlisted CI numeric artifact ID `14403685546`.
- 해당 SHA의 **실제 검증기**는 `block_B/day07/h01_runtime/tools/p2_g07_task04_moving_review.py`에 있으며, 단일 Goal/동일 UUID 취소, SQLite14, **실제 CM RMW source/observer 120ms**, **Guard 내부 CM age 150ms**, Native S02 Contact0, Guard latch 없음, 최초 타이밍 위반 없음, 실제 이동·odom zero dwell, CM/Guard/Scan/Odom/Clock 주기, **Navigation + Localization lifecycle ACK**, CM child exit0, GUI 창 2개, 정확한 소스 SHA 등 **21개 불변 조건**을 검사하고 모두 통과해야만 결과 PASS를 출력합니다. CI Xvfb가 Owner WSLg GUI 픽셀 인수와 같다는 뜻은 아닙니다.
- 이 GREEN의 핵심 실행 구성: **공식 Gazebo 물리 서버는 headless 유지**, 기존 Student G07 런타임에서 공식 Nav2 준비 후 `gz sim -g` 및 RViz 클라이언트만 별도로 붙임. D06 진단 후보의 `headless:=False` 변경을 공식 릴리스 경로로 **병합하지 않음**.
- 차후 최신 다른 Student SHA `09b2c7cf54ff1074ff4439008a3cb1a6fb1355de`를 사용한 [#44250223189](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44250223189)는 pre-Goal AssertionError로 실패. 그러나 1129/09b의 Goal 엔진, ordered shutdown 및 공통 smoke 스크립트 Git blob은 서로 동일하므로 단정적인 소스 회귀 원인은 미확정. **최신/HEAD 사용 금지, 정확한 이전 GREEN SHA 고정**.
- D06 실험 [#44253212332](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44253212332)은 별도 headless=False 후보에서 GUI+Goal·CLEAR/SLOW/STOP·취소까지 실제 성공했지만 `BLOCKED_LIFECYCLE_NAVIGATION_SERVICE_TIMEOUT`로 CI FAIL. 이 실패 원본 보존, 일회성 "shutdown_timeout 상향"이나 Nav2/CM/Guard 포크 대신 성공한 G07 Task04 통합 구조를 재사용.
- 검증 결론: **당시 Navigation/Localization 및 CM 정상 종료를 통과한 G07 소스/세션은 확인됨**. 실패를 확률적으로 영구 제거했다는 증거는 아니므로 한 번의 Owner L3 원본이 필요합니다.

## 2. 최소 연결 구현 — 공개 D06 Owner 실행기

- 파일 `d06/scripts/axia_d06_g07_classroom_once.sh`: 기존 `--self-check`, `--ci-status`, `--doctor`, `--gui-only` 보존, `--live`를 **G07 Task04가 이미 구현한 Student 공용 Owner Goal 엔진**으로 연결. G07 소스 Git commit `1129cd...`과 핵심 3개 Git blob을 재검사한 뒤에만 실행.
- **기존 Owner 진입점 재사용:** `block_B/day07/h01_runtime/scripts/p2_no_goal_smoke_ci.sh` 자체의 `AXIA_G07_TASK04_OWNER_MOVING_L3=1`과 `AXIA_G07_TASK04_EXPECTED_STUDENT_SHA`. 원본 Bash에서 controlling TTY로 `YES-P2-G07-GOAL`을 직접 읽고, 공식 Supervisor·Collision Monitor·Guard 소유 3 PID/ROS partition/출처 SHA를 다시 검증한 후 원래 Python 단일 Goal 실행기 `tools/p2_g07_ci_moving_goal.py`만 호출합니다. D06은 새로운 Goal/Twist publisher, 자동 동의, CI Actions 환경 위조를 생성하지 않습니다.
- **Goal 전에 원샷 사전점검:** 공개 Task03 L2·Task04 GUI L2·Task04 Moving 통합 L2의 정확한 workflow SHA/Run/Success, WSL2 Ubuntu24.04, ROS2 Jazzy + official packages, WSLg GLX D3D12, 실제 TTY, 네이티브 S02 C++ witness 빌드, 서로 다른 DDS/GZ 파티션, 셸 문법/immutable blob. 실패 시 **NO_GOAL**, 정확한 첫 실패 출력 및 원본 보존.
- 원본 G07 실행기에 already implemented: 실제 /scan/Nav2·CM/Guard, CLEAR→SLOW→STOP, strict Guard TTL150ms/CM120ms/Scan300ms, 실제 odom ≥1s, exact CancelGoal UUID5, 공식 Navigation/Localization shutdown ACK 및 CM clean exit, 14-topic SQLite. S02 네이티브 witness도 같은 binary build 방법 재사용.
- Goal 후에는 작은 read-only **Owner 후보 사후 게이트**: 기존 `audit_guard_internal_cm_age` (최초 실제 이동 이후 Guard 내부 CM age 150ms) 및 S02 witness 완결성/누락 0프레임을 포함하고, `NUMERICAL_CANDIDATE`, Owner PID/TTY authorized, Guard latch 없음, 최초 시간 위반 없음, 이동/정지, Goal exact cancel, 실제 S02 Contact0, native Nav2 두 ACK, CM exit0, SQLite14, Observer 주기를 검사합니다. **Owner 내부 RMW source provenance/WSLg 픽셀/독립 원본 리뷰는 추가 확인 필요**이므로 결과가 수치적으로 정상이어도 `OWNER_L3=RAW_REVIEW_REQUIRED_NOT_ACCEPTED`.
- 작업 결과는 항상 강사 WSL2의 `~/axia_d06_g07_owner_evidence/d06-moving-XXXXXXXX.tar.gz` 및 `.sha256`로 보존. 코드와 데이터의 repo/custody 경계 분리. SW stop ≠ 인증된 E-Stop.

## 3. RED → GREEN → REFACTOR → REVIEW → COMMIT

- D06 과거 실패 #44253212332 원본 보존. 새 연결 TDD RED: [공개 #44256060251](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44256060251), **9개 테스트 중 2개 FAIL**, 원인 `44249348860` 소스 고정 및 `run_verified_owner` 실행기 연결 미구현.
- 최소 구현: 성공 SHA 핀 + 원래 G07 공용 Owner 수동 TTY 경로 호출. CI 권한 spoofing/안전 TTL 변경 0. 중간 GREEN [#44256819327](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44256819327) **13/13 PASS** (정확 Run 영수증 모의, stale SHA/HOLD, TTY 거부, 원본 아카이브 EXIT trap, Owner 내부 Guard age 후검증 Python 문법 검증 포함).
- REFACTOR: 비동기(EXIT) 아카이브 trap이 함수 지역 변수 해제 후 경로를 잃는 것을 수정하고 전역 `D06_OWNER_OUT`/BASE에 안전하게 보존. 자동 GH CI L0, 실제 G07 native L2 소스는 불변. 새로운 Moving Goal 실전 CI는 되풀이하지 않음(정확 SHA의 #44249348860 이미 완료).
- REVIEW: 최초 실패/첫 타이밍 위반, official Nav2/CM/Guard 수정 0, Goal 권한 원래 Bash 수동 approval 그대로, 학생 정답/private 데이터 노출 없음, main 병합 금지, 모든 PASS의 L0/L2/L3 범위 별도 표기.
- **공개 D06 L0 GREEN:** [#44257489273](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44257489273), 정확 SHA `06a9b9225f2de3c78cc3cb1973357261334179fb`, 실제 `Ran 13 tests in 0.019s`, `OK`. 이후 본 문서/CI marker만 바뀌면 같은 L0 재검증하며 Go/No-Go는 실제 최신 HEAD Run 기준으로 최종 응답에 표시합니다. 강사 WSL2 실행은 GitHub 공개 CI 성공 후 사용자 한 번 수행. 실제 로봇+WSLg 라이브 주행을 이 문서에서 미리 PASS로 표시하지 않는다.

## 4. 실행 방법과 기대 로그

실행기 `--self-check`는 NO_ROS/NO_GOAL, `--ci-status`는 기존 세 GitHub Run의 정확한 SHA/성공과 `VERIFICATION_ONLY_NO_GAZEBO_NO_RVIZ`를 확인하는 **검증 전용**입니다. **실제 시연은 다운로드한 파일에 `--live` 인수를 붙여 실행해야 합니다.** 실행기 공개 변경 SHA를 고정한 단일 명령을 최종 답변에 제공합니다.

사전 요구 사항: Ubuntu24.04 WSL2/WSLg, ROS2 Jazzy, 공식 Nav2/TB3, `gh` 인증, `glxinfo`, `xwininfo`, `cmake`, C++ compiler, `libgz-sim8-dev` headers. 필요한 패키지가 없을 때 자동으로 임의 설치하거나 수동 승인 없이 Goal을 내지 않고, 정확한 첫 진단으로 HOLD합니다.

```text
D06_G07_CLASSROOM_TASK04_MOVING_HISTORICAL_CI_PASS run=44249348860 ...
D06_G07_OWNER_PIN_VERIFIED=1129cd8804954fd6481d1b6b4ebf0e0b98c68c3c
D06_G07_OWNER_REAL_GAZEBO_RVIZ_MOVING_CANDIDATE_START
D06_G07_OWNER_CONSENT_IS_MANUAL_TTY_ONLY=YES-P2-G07-GOAL
# Original Student shell: 강사가 실제 제어 터미널에 YES-P2-G07-GOAL을 직접 입력해야만 한 Goal 전송
D06_G07_OWNER_READONLY_FIRST_FAILURE=NONE
D06_G07_OWNER_READONLY_STATUS=OWNER_NUMERICAL_CANDIDATE_REVIEW_REQUIRED
D06_G07_OWNER_RAW_ARCHIVE=/home/.../d06-moving-XXXXXXXX.tar.gz
D06_G07_OWNER_L3=RAW_REVIEW_REQUIRED_NOT_ACCEPTED
AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false
```

**기대 출력은 실제 WSL2 시험 출력이 아닙니다.** 영상/화면, 내부 CM RMW source 간격, 최종 원본 증거를 리뷰하기 전 공식 인수 승격 금지. 중간 실패가 발생하면 Field에서 재실행하지 않고 해당 최초 경계를 공개 CI 회귀로 편입합니다.

---

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
