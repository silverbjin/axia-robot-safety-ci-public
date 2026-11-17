# D07-H01 검증 기준선 및 Owner WSL2 L3 남은 경계 (2026-11-17)

## CURRENT_HEADS — 원격 main 실조회
| 저장소 | SHA | 상태 |
|---|---|---|
| `silverbjin/axia-robot-safety-ci-public` | `62e366b51c64da25ad0216328fe1e019b78e0bef` | 사용자 기준과 일치 |
| `silverbjin/axia-robot-safety-student` | `6a3047b5aa219687f5fc918e467cea5115d3d482` | 사용자 기준과 일치 |
| `silverbjin/axia-robot-safety-instructor` | `f46874470a814be8f6976b6adbcaa1e43a1fe681` | 사용자 기준과 일치 |

기준 설계 원본은 비공개 Instructor `docs/baselines/AXIA_Robot_Safety_MVP_Baseline_Scenario_Acceptance_v1_KO.md`에서 조회했다(원격 파일 blob `8a2d8b51975a89d5e87aca1f52d8a1326e40417c`). 해당 문서는 실행 인수의 직접 증거가 아니라 전체 AXIA MVP의 설계·인수 후보안이다. D07-H01은 별도의 **정지 로봇에 대한 교육용 경로 재계획** 인수이다.

## D07_H01_VERIFIED_BASELINE
- 학생 정확한 main SHA의 공개 L2 [Run 44086340466](https://github.com/silverbjin/axia-robot-safety-student/actions/runs/44086340466): workflow **completed/success**, `actual-gazebo-physical-rviz-l2` Job success. 실제 로그의 `D07_H01_TEACHING_CYCLE_ACTUAL_GAZEBO_SCAN_COSTMAP_PATH_NO_GOAL_PASS`, `D07_H01_STUDENT_REAL_GAZEBO_RVIZ_XVFB_L2_PASS_NO_GOAL`, `D07_H01_STUDENT_WSLG_GPU_L3_NOT_RUN`. 네 단계 Path pose 길이는 기존 검수 보고서 52→52→49→52. 현장 WSLg의 렌더 증거가 아님.
- L2 Artifact #14329513093, 기존 원본 검수의 외부 SHA256 63/63, 내부 61/61 기록. 이번 문서 작업에서 ZIP을 새로 다운로드·재해시하지 않았으므로 기존 검수 기록을 재사용한다.
- 공개 CI main 정확한 SHA [Run 44087332744](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44087332744): 실제 테스트 로그 **183 passed, 3 skipped**. 2개 private Instructor 전용·1개 D04 의존성 테스트 SKIP; 모두 L3가 아니다.
- L3 실행기 전용 공개 L0 [Run 44086439903](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44086439903): PR head `842036187a77c60fa51e38f309c1415d21e4e6f6`, 10 unit tests PASS 및 `AXIA_D07_H01_INSTRUCTOR_L3_FIELD_L0_PASS_NO_ROS_NO_GAZEBO_NO_WSLG`. 병합된 main은 상기 183/3 테스트로 구별.
- 공개 CI `scripts/axia_d07_h01_instructor_l3_wsl2_once.sh`에 학생 pin SHA 정확히 일치. `--self-check`(L0), 내부 student `--doctor`(사전환경), `--run`(실제 L3), 별도 터미널 `--rqt`(수동)을 지원한다. **wrapper 자체 `--doctor` 옵션은 없다.**
- `block_B/day07/h01_runtime/tools/d07_h01_teaching_loop.py`에는 `shutdown_rclpy_once`의 `rclpy.ok()` guard가 포함되어 있다.
- `block_B/day07/h01_runtime/ros2_ws/src/axia_safety_bringup/launch/axia_tb3_p2.launch.py`의 H01 전용 조건부 `OnProcessExit`로 world Xacro 완료 다음 Gazebo server 시작. 해당 병합 SHA의 L2에서 검증.
- 터미널 A는 rqt PID를 생성/종료하지 않으며 `ROS_DOMAIN_ID=95`, `ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST`. 터미널 B는 같은 discovery 설정으로 수동 rqt_graph 실행.
- 안전기능·정책·Moving Goal·인증 Hardware E-Stop 변경 없음. `AXIA_MVP_DEMO_ACCEPTED=HOLD`.

## D07_H01_REMAINING_GAPS
1. **FIRST_UNVERIFIED_BOUNDARY:** 최신 고정 소스로 Owner WSL2/WSLg의 Gazebo 실제 월드·Waffle·장애물 픽셀 렌더링 및 RViz Scan/Costmap/Path 확인 (`NOT_RUN`).
2. 독립 rqt_graph 3계층 필터와 `ros2 topic info`/`ros2 action info` 동일 그래프 교차 확인 (`NOT_RUN`).
3. 물리 장애물 `free,intrusion,lateral,restored` 완전한 4단계 2회 이상, JSONL 각 행 native ACK/scan/costmap/official Path/ROS Publisher/무주행 플래그 (`NOT_RUN`).
4. 터미널 A 운영자 Ctrl+C 단 한 번, 동일 세션 Graceful teardown, 프로세스 소유권, B 그래프 독립 생존 (`NOT_RUN`).
5. 해당 세션 원본·아카이브 SHA256 검증, Owner 육안 화면 승인 (`NOT_RUN`).
6. Scan→Supervisor→CM/Guard 데이터 주기·TTL, 실제 주행 안전성, 인증 Hardware E-Stop은 **이 교육용 H01 인수 범위 밖**. 전체 AXIA 안전 MVP는 별도 HOLD.

## 과거 실패 경계 (새 오류 아님)
- Owner `session-20261117-uX8uxx0z`: geometry 원본은 `motion_admitted=false`, 반복행은 `robot_moved=false`; 기존 L3 verifier가 geometry에 없는 키를 요구했던 스키마 오류 수정 완료. 당시 실제 반복 2행뿐이고 `D07_H01_TEACHING_BLOCKED_FIRST_BOUNDARY RCLError: failed to shutdown: rcl_shutdown already called`가 첫 teardown 오류. 현재 학생 main은 rclpy shutdown guard 포함. 이전 Owner 실패 세션은 절대 PASS 승격하지 않는다.
- 학생 L2 이전 `Run 44084070517`: Gazebo `gz sim -s /tmp/nav2_*.sdf` exit255가 `/clock` 누락보다 먼저 발생; 조건부 Xacro→Gazebo 순서 수정 후 정확한 학생 main L2 GREEN.
- 근거: [Nav2 공식 Issue #5350](https://github.com/ros-navigation/navigation2/issues/5350) (2025-07-11 생성, 2025-07-14 closed, Jazzy 1.3.7에서 유사 tempfile 오류). Issue의 해결이 자동으로 현재 코드의 성공을 의미하지 않으며, 실제 해당 SHA L2가 별도 증거. ROS 2 Jazzy event handler 공식 문서도 별도 참고.

## MINIMAL_ACTION_PLAN
새 소스 결함 확인 전 코드 수정 없이 pin된 공개 원샷 사용. 별도 터미널 B에서 rqt_graph, WSLg 화면 관찰, 두 사이클 후 A Ctrl+C, 원본 SHA 및 데이터 verdict 확인. 새 오류 발생 시 동일 소스 재시도 대신 최초 오류와 시간 경계부터 분석하고 공개 CI 최소 회귀 RED→GREEN→REVIEW→COMMIT. 전체 MVP와 별개.

### OWNER_WSL2_SINGLE_RUN_COMMAND — 터미널 A
```bash
(
  set -Eeuo pipefail
  CI_SHA=62e366b51c64da25ad0216328fe1e019b78e0bef
  F="$(mktemp --suffix=.sh)"
  trap 'rm -f "$F"' EXIT
  curl -fsSL --retry 3 "https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public/$CI_SHA/scripts/axia_d07_h01_instructor_l3_wsl2_once.sh" -o "$F"
  bash -n "$F"
  bash "$F" --self-check
  bash "$F" --run
)
```
터미널 A 실행 중 별도 터미널 B:
```bash
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=95
export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
ros2 run rqt_graph rqt_graph
```
이 A 실행은 실제 Owner가 직접 수행해야 한다. API/CI의 L0/L2를 Owner L3 성공으로 대체하지 않는다.

## EXPECTED_SUCCESS_MARKERS
- `AXIA_D07_H01_INSTRUCTOR_L3_WRAPPER_L0_PASS WSL2_NOT_RUN GAZEBO_NOT_RUN`
- `AXIA_D07_H01_L3_SOURCE_PIN=6a3047b5aa219687f5fc918e467cea5115d3d482`
- `AXIA_D07_H01_L3_PUBLIC_PIN_AND_DOCTOR_PASS`
- `D07_H01_TEACHING_LIVE_REPEAT_STARTED NO_GOAL CTRL_C_TO_STOP` (원본 runtime 로그; 외부 터미널에 실시간 노출된다고 가정 금지)
- 두 개의 완전한 `free,intrusion,lateral,restored` JSONL cycle와 `D07_H01_TEACHING_CTRL_C_STOP OPERATOR`
- `P2_L2_GRACEFUL_TEARDOWN`
- `AXIA_D07_H01_L3_COMPLETE_PHYSICAL_CYCLES=2` 이상
- `AXIA_D07_H01_L3_DATA_VERDICT=READY_FOR_OWNER_PIXEL_REVIEW`
- `AXIA_D07_H01_L3_VISUAL_ACCEPTANCE=HOLD_USER_SCREEN_REVIEW_REQUIRED` — 자동 판정기 설계상 정상 출력. Owner의 화면 승인 전 `AXIA_D07_H01_EDUCATIONAL_L3_ACCEPTED=HOLD`.

## EVIDENCE_COLLECTION_PLAN
원샷이 `~/axia_d07_h01_instructor_l3/session-YYYYMMDD-*/`에 native ROS/Gazebo log, JSONL, `preflight.log`, `gpu_glxinfo.txt`, `windows-gazebo-rviz.txt`, `exit_status.txt`, `l3_structural_verdict.txt`, `SHA256SUMS`를 보존하고 같은 이름 `.tar.gz`와 `.sha256`를 생성. 아카이브 검사는 출력된 정확한 경로를 사용하여 `sha256sum -c <archive>.sha256`; 원본 내역은 `(cd <session-dir> && sha256sum -c SHA256SUMS)`. Native는 `native/evidence/SHA256SUMS` 별도. rqt 독립 실행 화면 3장 + Gazebo/RViz 장면은 Owner 별도 육안 관찰/캡처; 자동 XWD가 있는 경우도 화면 승인으로 승격 금지.

## 판정 및 변경 기록
- 새 코드 변경: 없음. 새 RED/GREEN 사이클: 없음. 기존 성공 증거 재사용.
- 본 브랜치는 **문서 인계만**, main 미병합. 새 CI 실행 및 Owner WSL2 L3 시도 없음.
- `AXIA_D07_H01_EDUCATIONAL_L3_ACCEPTED=HOLD`
- `AXIA_MVP_DEMO_ACCEPTED=HOLD`
