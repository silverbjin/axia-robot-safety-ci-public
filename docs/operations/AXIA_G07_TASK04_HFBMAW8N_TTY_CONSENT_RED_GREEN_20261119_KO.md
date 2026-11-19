# AXIA G07 Task04 HFbmAW8N — Owner TTY 승인 실패 원인·재현·디버깅·출고 보고서

작성일: 2026-11-19 KST. 공개 CI 브랜치 `fix/g07-task04-owner-timing-evidence-20261119`. 원본 강사 WSL2 증거는 비공개 보존. 인증된 하드웨어 E-Stop과 소프트웨어 Stop은 구별한다.

## 1. 불변 현장 원본 증거와 최초 실패

- `owner-moving-HFbmAW8N.tar.gz`: SHA256 `a7d8b83c3a86c77dc47bdbd3dbebf76188669c656a0992dbe1c72df7aa1623e1`. 업로드 바이트 SHA256 직접 재검증 일치.
- `owner-moving-HFbmAW8N.diagnostics.zip`: SHA256 `68d55a7f752dbeb81d3457d0294a4b929a186faa08455953c0ae47edd8d1dcd3`. 직접 재검증 일치.
- 기존 정확한 Owner 원샷: `1816fbbbfdb972e52c5168ade26c768167998556`; Student `6579e2eef7e99691da558cd2de1964fd26a04621`, 실물 Gazebo L2 [#44449459417](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44449459417) 21/21 PASS.
- `native_runner.log` 핵심 원문:
```text
P2_NO_GOAL_STATIC_AND_RUNTIME_READINESS_OBSERVED
AXIA_G07_TASK04_GAZEBO_SERVER_SINGLE_GUI_CLIENTS_ATTACHED
AXIA_G07_CI_MOVING_GOAL_PREG0AL_NATIVE_FIXTURE_BEGIN
AXIA_G07_OWNER_PREGOAL_PHYSICAL_L2_PASS_NO_GOAL front_m=2.045 side_m=0.711
G07_TASK04_OWNER_TTY_APPROVAL_TIMEOUT_OR_EOF_NO_GOAL
P2_L2_SMOKE_RC=2
```
- 반면 원본 `first_failure.txt`에는 포괄적 `NATIVE_RUNNER_FAILED_REVIEW_RAW`만 남음. 최초 실패와 outer wrapper verdict를 혼동해서는 안 된다.
- 공식 World/Xacro·Clock·Scan/Odom·CM·Guard 준비는 성공, Goal 발행 없음, /cmd_vel 0, 가드 latch 없음, Contact 0. Gazebo RTF 90%대 증거는 있었으나 이 실패는 렌더러/물리 성능 원인이 아님.
- 기존 Owner 승인 Reader는 Gazebo/RViz 실행 후 `/dev/tty`에 정확한 승인 문자열을 요구하나, `read -r -t 180` 실패 시 EOF와 시간 초과를 하나의 코드로 합침. Owner의 stderr/stdout은 `native_runner.log`로 전환되고 실제 승인 프롬프트는 터미널만으로 보내져, 나중에 최초 사용자 요청 시점·응답 상태를 로그로 재구성하기 어려움.
- 원본 시간 간격은 실제 180초 제한과 부합하지만 화면이 가려졌는지, 입력이 없었는지, 터미널 EOF였는지는 원본만으로 최종 단정 불가. 따라서 RED는 네 경우를 PTY로 독립 재현.

## 2. RED — 공개 CI에서 실물 터미널 동작 재현

- Student `block_B/day07/h01_runtime/tools/test_g07_task04_owner_tty_pty.py`, CI `tests/test_g07_task04_owner_tty_first_failure.py`. Python 표준 `pty.fork()`의 실제 Linux controlling PTY에서 정확 승인·오답·Ctrl-D EOF·시간 만료·TTY 없음·approval 이후 safety data stale·최초 오류 문자열을 재현. **실제 ROS/Gazebo/Goal 미실행**.
- 최초 [#44454692288](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44454692288)은 테스트 **12개 실패에도 워크플로가 SUCCESS인 가짜 GREEN**이었다. 원인: `test "$CI_RC" -eq 0 && test "$STUDENT_RC" -eq 0`가 실패해도 다음 `echo`가 계속 실행되어 최종 종료 코드 0. Green으로 인정하지 않았다.
- 워크플로 종료 조건을 `if (( CI_RC != 0 || STUDENT_RC != 0 ));then exit 1;fi`로 변경 후 공개 [#44454786009](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44454786009) **RED**: CI 5개 FAIL, Student 7개 FAIL, `ci_rc=1 student_rc=1`, Actions 결과 FAILURE. 최초 실패가 제대로 재현됨.

## 3. GREEN — 가장 작은 변경

- Student `block_B/day07/h01_runtime/tools/p2_g07_owner_tty_consent.sh` 읽기 전용 인터랙티브 헬퍼: 기존 정확한 `YES-P2-G07-GOAL` 문자열을 controlling `/dev/tty`에서 **한 번만** 입력, production 180초 제한 유지. 터미널 종소리·구분선·WSL2 터미널 포커스 안내를 표시하고, 개인 `native_runner.log`에는 승인 문자열이 아닌 `OWNER_GOAL_CONSENT_PENDING`·최종 **상태 코드 및 경과 시간만** 기록. 임의 CI 권한·자동 승인 없음.
- 실패 코드를 `OWNER_GOAL_CONSENT_TIMEOUT`, `OWNER_GOAL_CONSENT_EOF_OR_TTY_ERROR`, `OWNER_GOAL_CONSENT_DENIED`, `OWNER_GOAL_CONSENT_TTY_UNAVAILABLE`로 분리하고 모두 Goal 0으로 fail-closed.
- Student `block_B/day07/h01_runtime/scripts/p2_no_goal_smoke_ci.sh`: 기존 Owner-only read 블록을 헬퍼 `source` 및 `axia_owner_tty_consent 180` 호출로만 교체. 기존 Scope·권한·source SHA·`--owner-launch-pid`·Goal 1개 제한 유지.
- Student `block_B/day07/h01_runtime/tools/p2_g07_ci_moving_goal.py`: 새 Observer의 실제 최근 Scan/Odom/Guard/Clock 수신 주기 `<=300ms`, Clock 증분, Guard latch false, 전방 유효 거리 검사를 승인 후 START 직전과 Goal 발행 직전에 각각 실행. **기존 CM 120ms·Guard age 150ms·안전 FSM/TTL·센서 주파수 변경 없음**.
- 공개 CI Owner `scripts/axia_g07_task04_owner_moving_l3_once.sh`: `native_runner.log`에서 확인된 최초 승인 오류를 원본 `first_failure.txt` 및 작은 ZIP verdict에 전달. 기존 PREGOAL 오류 우선권을 보존하고 오답 문자열은 읽거나 보존하지 않음.

## 4. 공개 PTY 회귀 GREEN

- 실제 성공한 공개 [#44455220286](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44455220286) **13/13 PASS**, CI 5개 + Student 8개:
```text
Ran 5 tests ... OK
Ran 8 tests ... OK
AXIA_G07_HFBM_PTY_L0_TEST_RESULTS ci_rc=0 student_rc=0
AXIA_G07_HFBM_PTY_L0_GREEN_REAL_PTY_NO_ROS_NO_GOAL
```
- Post-consent safety fixture에서 각 Scan/Odom/Guard/Clock timestamp를 >300ms stale 처리하거나 Guard latch=true, Clock 무진행, Scan invalid 시 모두 Goal 차단 조건 반환 확인.
- 별개 공개 Python contracts [#44455226154](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44455226154), Runner Canary [#44455226074](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44455226074), 기존 Clock/Guard L0 [#44455226149](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44455226149) 성공. 소프트웨어 계약 검증만으로 현장 WSL2 성공을 선언하지 않는다.

## 5. 실제 Gazebo L2 및 출고 판정

- 실제 Gazebo Harmonic + ROS 2 Jazzy + 공식 Nav2 + TB3 Waffle + Gazebo/RViz Xvfb의 **동일 21개 안전/물리/종료 게이트**를 검증하기 위해 기존 `.github/workflows/axia-g07-task04-owner-n7-parity-native-l2-20261119.yml` 재사용. Student 최종 소스 정확한 SHA `efff0fb8bf941de74572336d1988dfb0005e11f7` 고정.
- 네이티브 Contact 빌드용 임시 컨테이너와 실제 `libgz-transport13=13.6.0` Gazebo 런타임 분리 유지.
- 첫 새 L2 [#44455342926](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44455342926)은 실제 Gazebo를 실행하기 전에 구형 정적 테스트가 여전히 `YES-P2-G07-GOAL`/`read -r` 문구를 **실행기 파일 내부에만** 요구해 1/5 FAIL. 실행기와 새 helper를 **함께 검사**하도록 테스트를 강화·갱신했으며 기존 수동 승인의 기능을 삭제/완화하지 않음. 최종 Student SHA `efff0fb8bf941de74572336d1988dfb0005e11f7`에서 공개 [#44455880013](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44455880013) **18/18 PASS** (CI 5 + PTY 8 + 기존 shell 5).
- 최종 Student SHA `efff0fb8bf941de74572336d1988dfb0005e11f7` 공개 실제 Gazebo/Nav2 Moving+Gazebo/RViz L2 [#44455960504](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44455960504) **SUCCESS**. 출력 `AXIA_G07_TASK04_NATIVE_ONE_MOVING_RUNNER_RC=0 RVIZ_X11=1 GAZEBO_X11=1`, 판정 `{first_failure: NONE, source_sha: efff0fb8..., status: TASK04_REAL_GAZEBO_MOVING_GUI_L2_SCOPED_PASS}`. 원래 21개 strict gate가 같은 세션에서 모두 true; Collision Monitor/Guard/Scan/Odom/Clock, odom zero dwell, native Contact0, Goal 정확 취소, Nav/Localization shutdown ACK 및 CM clean exit 포함. PUBLIC CI 성공 ≠ Owner WSL2 L3 성공.
- 별도 native Contact witness 빌드 + Gazebo Transport 13.6 고정 런타임 구성 유지. L2 숫자·SHA256 allowlist artifact [#14497697039](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44455960504/artifacts/14497697039), artifact digest `sha256:da11a3f030f27be8b5cf37a930157531cc11dcd2c950c759a70f537a9a38b453`. 원본 민감 로그 및 rosbag은 공개 아티팩트에 포함하지 않음.
- 성공해야 하는 조건: World/SDF/Clock/Scan/Odom/TF, 실제 Moving Goal CLEAR→SLOW→STOP, 정확 Goal UUID 취소, Native Contact 0, CM source+observer 120ms, Guard 내부 150ms, Scan/Odom/Clock 300ms, zero odom dwell >=1sec, Navigation/Localization ACK, Collision Monitor 종료, SQLite14, GUI2, **21/21 strict**.
- Owner WSL2 실제 L3 원본 타이밍·TTY 화면 포커스·실제 Goal 승인은 공개 CI로 증명할 수 없으며, 출고 후 현장 1회 원본 TAR·ZIP으로 별도 인수.

```ini
HFBM_PTY_RED=REPRODUCED_12_FAILURES
HFBM_PTY_GREEN=PASS_13_OF_13
PUBLIC_NATIVE_GAZEBO_L2_NEW_STUDENT_SHA=PASS_21_OF_21_RUN_44455960504
OWNER_BOOTSTRAP_NEW_PIN_L0=PASS_8_OF_8_RUN_44456593223
OWNER_WSL2_L3=NOT_RUN
AXIA_MVP_DEMO_ACCEPTED=HOLD
CERTIFIED_ESTOP=false
MAIN_MERGED=false
```

## 6. 리뷰·MVP 범위

변경 목적은 기존 인간 통제 요구를 화면과 로그 양쪽에 명확히 노출하고 거부 시 안전 무주행으로 복귀하는 것. 사용자 승인 없이 Goal을 보내는 자동화/스킵 또는 환경변수 기반 CI 승인 우회는 포함하지 않는다. Xacro·Nav2·Guard·CM·Fault Injector·Stop/Cancel·World는 그대로. 매 사이클의 GitHub PR/커밋/실제 Run은 이 보고서에 갱신한다. `main` 병합 금지.

## 7. 최종 REVIEW→COMMIT→출고 정보

- Student 최종 소스 `efff0fb8bf941de74572336d1988dfb0005e11f7`: 승인 흐름 최소 수정 + 기개발 H01/G07/CM/Guard/주행 알고리즘 재사용. 한 번 더 발견한 오래된 `test_g07_task04_owner_shell_contract.py`의 파일 위치 의존 테스트를 단일 helper와 호출자의 **양쪽 모두를 검사하는 강화된 계약**으로 고쳤고, 원래 TTY 실물 보안 계약을 삭제하지 않았다. [#44455880013](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44455880013) 18/18 GREEN.
- 공개 CI 실제 L2 source workflow SHA `fb1746613c8d0697e5a54e9687c90c93ed5706bb`; 실제 Run `44455960504` SUCCESS.
- 공개 Owner 한 파일 immutable 출고 SHA `cd8c23c52588f5efd6295b6904e15b1aa54496e7`: 내부 `STUDENT_SHA=efff0fb8...`, `REVIEW_SHA=71b85c42...`(기존 검증기 불변), `CI_L2_RUN=44455960504` 고정. Student TTY helper 존재·Bash syntax를 WSL2에서 Goal 전에 사전검사한다.
- [Owner Bootstrap #44456593223](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44456593223) `Ran 8 tests ... OK`, 스크립트 `bash -n` PASS. 수동 승인을 우회하지 않고 `--self-check`에선 ROS/Gazebo/Goal을 시작하지 않는다.
- 실패 시 원본 저장: `$HOME/axia_g07_task04_owner_moving/owner-moving-XXXXXXXX/first_failure.txt`, `native_runner.log`, 원본 TAR/SHA256, 별도 작은 diagnostics ZIP/SHA256. Goal 승인이 입력되지 않으면 소프트웨어 BOOT_SAFE/STOP 경로, Goal 0이어야 함.
- 기존 성공을 불필요하게 반복하지 않았으며 Goal 21개 strict, 실제 새 Owner WSLg 화면·사용자 본인 승인·Windows/WSL2 스케줄러 타이밍·15초 Guardian 안정성 인수는 현장 L3에서만 확인한다.
- 새 한 줄 실행기는 사용자에게 먼저 `--self-check`, 이어 동일 스크립트 `--run`을 수행하는 단일 명령 블록으로 제공한다. `YES-P2-G07-GOAL`은 실제 WSL2 터미널에만 직접 입력하고, CI/스크립트에서 자동 입력하지 않는다. `main`은 사용자 승인 전 병합하지 않는다.

```ini
HFBM_PUBLIC_PTY_L0=PASS_18_OF_18
PUBLIC_NATIVE_GAZEBO_L2=PASS_21_OF_21_RUN_44455960504
OWNER_BOOTSTRAP_L0=PASS_8_OF_8_RUN_44456593223
OWNER_WSL2_L3=NOT_RUN
AXIA_MVP_DEMO_ACCEPTED=HOLD
CERTIFIED_ESTOP=false
MAIN_MERGED=false
```
