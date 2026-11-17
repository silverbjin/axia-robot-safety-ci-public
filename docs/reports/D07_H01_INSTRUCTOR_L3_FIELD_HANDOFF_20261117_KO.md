# D07-H01 강사 WSL2/WSLg L3 현장 인수 — 공개 CI 인계

- 작성일: 2026-11-17
- 범위: ROS 2 Jazzy / Gazebo Harmonic / 공식 Nav2 / TurtleBot3 Waffle / RViz2 / rqt_graph
- 원칙: 강사용 새로운 ROS 구현 없이 학생용 공개 H01 반복 시연 재사용, 현장 증거 한 번에 수집
- 공개 CI 저장소: silverbjin/axia-robot-safety-ci-public
- 개발 브랜치: feat/d07-h01-instructor-wsl2-l3-field-20261117
- 인수 실행 파일: scripts/axia_d07_h01_instructor_l3_wsl2_once.sh
- 검증 시험: tests/test_d07_h01_instructor_l3_field.py
- 워크플로: .github/workflows/d07-h01-instructor-wsl2-l3-field-l0.yml
- 입력 학생용 공개 main 고정 SHA: 6a3047b5aa219687f5fc918e467cea5115d3d482
- 강사 가이드 main SHA: f46874470a814be8f6976b6adbcaa1e43a1fe681
- 전체 AXIA 안전 MVP: AXIA_MVP_DEMO_ACCEPTED=HOLD

## 배경 및 재사용한 성공 근거

학생 공개 main의 실제 Jazzy/Harmonic Gazebo+RViz2+rqt_graph L2 Run #44072468003 PASS. 고정 학생 main의 실제 업로드 ZIP Artifact #14323298203의 외부 63/63, 내부 61/61 SHA256 일치. 실제 Gazebo native pose ACK, /scan, /global_costmap/costmap, 공식 ComputePathToPose Path, RViz 구독을 확인. 한 개 CI 한정 반복(Free→Intrusion→Lateral→Restored), 계획 Path 52→52→49→52, goal_sent=false, robot_moved=false, 정상 teardown. 이것은 강사 WSLg 화면 픽셀이나 실제 Ctrl+C 인수가 아니다.

비공개 강사 정답·hidden_tests는 재배포하지 않는다. 본 원샷은 동일한 학생 공개 소스를 고정 SHA로 별도 경로에 clone한 뒤 기존 강의 모드를 호출한다.

## L3의 최소 범위

1. WSL2 Ubuntu 24.04 + Jazzy + WSLg 화면 준비, 공개 학생 소스 SHA 정확히 pin.
2. **터미널 A**가 Gazebo+RViz만 실행하고, **터미널 B**가 `rqt_graph`를 독립 실행한다. 동일 `ROS_DOMAIN_ID=95`를 사용하며 GUI 생성/종료 소유권은 서로 분리한다. 그래프 3계층 필터는 강사 가이드 A-2절을 따른다.
3. 진짜 Gazebo 물리 4단계(Free→Intrusion→Lateral→Restored)를 두 사이클 이상 반복한 뒤 운영자 Ctrl+C 한 번으로 종료.
4. 원본 3단계 실물 H01, 공식 Action Path, 두 사이클 실측 JSONL, 무주행·무E-stop, Graceful teardown을 별개로 검사.
5. 명령 로그·GPU glxinfo·창 목록·가능한 경우 개별 XWD 캡처·원본 Native Evidence·최종 SHA256SUMS를 한 개의 tar.gz와 SHA256 파일로 보존.
6. **사람이 실제 화면의 Waffle/원통/경로 변화를 확인하지 않았다면 L3는 HOLD**, 증거상 DATA_VERIFIED도 전체 AXIA 승인 아님.

## RED → GREEN → REVIEW

| 단계 | 실제 대상 | 결과 |
|---|---|---|
| 사전 기준선 | student main c25d63d9, 실제 공개 Gazebo L2 Run #44072468003 | 해당 시연 범위 PASS, WSLg L3 NOT_RUN |
| 초기 계약 GREEN | 공개 CI Run #44075364121, 5개 fixture/정적 테스트 | PASS, NO_ROS/NO_GAZEBO |
| RED | 공개 CI Run #44075522184, 새 WSL2 셸에서 Jazzy source가 ros2 명령 확인보다 늦다는 순서 오류 | 의도적 FAIL (AssertionError: 4687 not less than 4198) |
| GREEN | 초기 진단 순서를 수정한 소스 130282d08cc6e05c485494462fea832a92e2de9d, CI Run #44075622097 | PASS, L0 전용 |
| REVIEW | 강사용/학생용 런타임, TTL, moving Goal 코드 변경하지 않음 | 현장 WSLg L3 실행 대기 |

## 현장 실행

공개 CI L0가 검증한 정확한 파일을 해당 Git commit SHA로 내려받는다. PR의 최종 SHA를 명령의 PIN 자리에 넣는다. 다른 리포지토리 코드를 재작성할 필요는 없다.

~~~bash
(
  set -Eeuo pipefail
  PIN='<PUBLIC_CI_L0_GREEN_COMMIT_SHA>'
  F="$(mktemp --suffix=.sh)"
  trap 'rm -f "$F"' EXIT
  curl -fL --retry 3 --silent --show-error \
    "https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public/$PIN/scripts/axia_d07_h01_instructor_l3_wsl2_once.sh" -o "$F"
  bash -n "$F"
  bash "$F" --self-check
  bash "$F" --run
)
~~~

운영: 터미널 A의 원샷은 Gazebo·RViz **두 창만 자동 실행**한다. rqt_graph는 터미널 B에서 아래처럼 **별도 시작**하며 A의 Ctrl+C가 B의 rqt_graph를 강제로 종료하지 않는다. rqt_graph 상단 노드/토픽 필터를 단계적으로 변경한다. 연속 2회 네 위치 반복을 확인한 뒤 **실행 터미널에서 Ctrl+C 단 한 번** 누른다. 모든 원본 및 종료 증거를 자동으로 압축하며 별도의 기존 ROS 프로세스에 무차별 pkill을 하지 않는다. 창 XWD는 가능할 때만 캡처하므로 화면 검수는 Owner 육안 및 사진 3장을 별도 제출해야 한다. 화면이 보이지 않으면 실패 원본과 첫 위반을 보존하고 동일 현장 시도를 반복하지 않는다.

산출물:
- ~/axia_d07_h01_instructor_l3/session-*/native/evidence/ (H01 원본 실측·종료)
- ~/axia_d07_h01_instructor_l3/session-*/l3_structural_verdict.txt (L3 DATA 전용 판정)
- ~/axia_d07_h01_instructor_l3/session-*.tar.gz 및 .sha256
- 창 목록 `windows-gazebo-rviz.txt`, glxinfo 및 캡처된 경우 window_Gazebo.xwd, window_RViz.xwd; rqt_graph 별도 창 캡처는 운영자 증거로 별도 제출
- 별도 Owner 화면 육안 승인(3개 rqt_graph 필터 단계 및 Gazebo/RViz 장면)

## 기대 출력 및 최종 판정 기준

필요한 사실:
- 고정 student SHA 출력, --self-check/--doctor 성공
- D07_H01_TEACHING_CYCLE 원본 JSONL의 두 개 **완전한** 4단계 반복
- 원본 geometry.json real_nav2=true, real_laser_scan=true, goal_sent=false, motion_admitted=false; 반복 teaching_cycle_evidence.jsonl 모든 행 robot_moved=false
- OPERATOR Ctrl+C 기록, 최초 `D07_H01_TEACHING_BLOCKED_FIRST_BOUNDARY` 없음, P2_L2_GRACEFUL_TEARDOWN, 동일 세션 Gazebo/RViz 창 목록
- AXIA_D07_H01_L3_DATA_VERDICT=READY_FOR_OWNER_PIXEL_REVIEW (전제 충족 시)
- AXIA_D07_H01_L3_VISUAL_ACCEPTANCE=HOLD_USER_SCREEN_REVIEW_REQUIRED (자동 화면 인수는 하지 않음)

미검증은 반드시 명시:
- 강사 로컬 WSL2의 GPU/GUI 픽셀 시연과 실물 반복은 실제 사용자 실행 전 NOT_RUN
- Gazebo GUI 단순 창 생성은 Waffle/장애물 3D 렌더링을 증명하지 않음
- Ctrl+C 종료의 실제 WSL2 신호 경로와 26초 shutdown grace는 현장 증거 전 NOT_RUN
- 안전 Scan→Supervisor→CM/Guard 전달 주기·150ms CM / 300ms Scan TTL은 본 H01만으로 인수하지 않음
- ROS Plan은 로봇 주행이 아니며, 인증된 Hardware E-Stop은 범위 밖
- 전체 AXIA_MVP_DEMO_ACCEPTED=HOLD 유지

현장 오류가 발견되면 최초 안전 상태 전이 및 최초 타이밍 위반을 원본에서 식별하여 공개 CI RED 회귀로 우선 편입하고, 새 패치 CI GREEN 후 인수를 재개한다. 기존 성공을 재실행하는 방식으로 추측하지 않는다.

## Git 릴리스 규칙

원샷은 공개 CI L0 및 전용 시나리오 계약을 통과한 뒤 공개 `main`에 병합한다. 사용자는 이번 요청에서 `main` 병합을 명시적으로 승인했다. 학생 공개 main은 Ctrl+C 중복 ROS shutdown 회귀를 최소 수정한 SHA d1a453d4로 갱신했으며, 비공개 강사 정답은 변경하지 않는다.


## 2026-11-17 신규 Owner 업로드 실측과 회귀 조치

- 수신 ZIP: `session-20261117-uX8uxx0z.tar.gz`, SHA256 `0bb02de1f2bca33d7f6c463f479059df09adda5b4eae7f70bf4d5795cb1b0d0b` (첨부 .sha256 일치).
- 압축 안의 `SHA256SUMS` 70/70, `native/evidence/SHA256SUMS` 61/61 일치.
- 실제 강사 WSLg `windows-last.txt`에 Gazebo Sim과 RViz2 확인. `rqt_graph.log`는 비어 있고 `windows-triple.txt` 없음. 이것은 rqt 실행/표시 미검증이지 Gazebo/Nav2 미실행이 아니다.
- 실제 `teaching_cycle_evidence.jsonl` 1회차 Free→Intrusion 두 행만 존재, 두 Path 각각 52개 포즈, 원본 `goal_sent=false`, `motion_admitted=false`; **2개 완전 반복은 NOT_RUN**.
- `runner_rc=130`, `operator_signal=INT`, `P2_L2_GRACEFUL_TEARDOWN`; 그러나 `d07_h01_teaching_loop.log`에 최초 `RCLError:failed to shutdown: rcl_shutdown already called`가 기록됨. 이 오류가 최초 후처리 결함이며 다른 판정기로 덮지 않는다.
- 기존 L3 판정기는 원본 `geometry.json`에 없는 `robot_moved` 키를 요구했다. 실제 원본의 `motion_admitted=false`와 각 반복 행의 `robot_moved=false`를 개별 검사하도록 수정. 최초 teaching shutdown 오류가 있으면 `READY_FOR_OWNER_PIXEL_REVIEW` 승격 금지.
- 새 L3 실행기는 `--rqt` 모드를 **별도 터미널**에서만 사용한다. 터미널 A는 rqt PID를 생성/종료하지 않고, Gazebo·RViz 두 창만 계측한다. rqt_graph 미실행은 A의 Gazebo/Nav2 물리 시나리오 성공을 차단하지 않는다.
- L3 데이터 판정이 HOLD면 원샷 종료 코드도 3으로 반환한다. Ctrl+C 및 깨끗한 네이티브 teardown만으로 데이터 인수를 성공으로 보고하지 않는다.
- 학생 공개 런타임 최초 오류는 새 순수 L0 회귀 RED → `rclpy.ok()` guard GREEN으로 수정. 메인 `6a3047b5aa219687f5fc918e467cea5115d3d482` 재사용, 안전 TTL·주행 명령 변경 없음.

### 터미널 B — rqt_graph 독립 실행

~~~bash
set +u
source /opt/ros/jazzy/setup.bash
set -u
export ROS_DOMAIN_ID=95
export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
ros2 run rqt_graph rqt_graph
# 이 터미널에서 Ctrl+C: rqt_graph만 종료
~~~

또는 터미널 A에서 받은 동일 L3 실행기를 별도 터미널에서 `--rqt` 옵션으로 실행한다. 두 방식 모두 ROS 노드·토픽을 **조회만** 한다.

**운영 순서:** A에서 `--run` → Gazebo/RViz 창 확인 → B에서 rqt_graph 실행 → 3계층 필터 수업 진행 → A에서 2번의 완전한 4단계 반복 확인 후 Ctrl+C → A가 ZIP 보존 → B에서 Ctrl+C로 rqt 종료. A와 B의 종료를 섞지 않는다. A의 압축 파일은 rqt 로그/화면 픽셀을 자동 포함한다고 주장하지 않는다.

### 검증 범위/미검증

- Public CI L0는 실행기 분리·판정기 로직·가짜 ROS evidence fixture까지만 검증한다. 새 실제 Gazebo 결과는 학생 `main` 물리 L2 별도 결과를 확인한다.
- 강사 WSLg 실제 리트라이 및 GUI 픽셀 변화·2회 반복·Ctrl+C 완전 종료는 **Owner WSL2 재인수 전 NOT_RUN**. 이전 실패 ZIP을 PASS로 격상하지 않는다.
- 공개 Python 전체 계약에서 Instructor 비공개 유틸리티 파일을 요구하는 2개 테스트는 sealed 환경에서만 수행한다. 공개 CI는 명시적 SKIP (다른 테스트 실행을 지우지 않음). 공개 PASS는 private-only 테스트 PASS를 뜻하지 않는다.
- AXIA 전체 MVP: `AXIA_MVP_DEMO_ACCEPTED=HOLD`. Hardware certified E-Stop, Scan→Supervisor→CM/Guard 안전 타이밍/TTL, 실제 움직이는 로봇 정지는 본 강의용 H01 검증 범위 밖이다.


## 2026-11-17 공식 Nav2 월드 Xacro→Gazebo 시작 경쟁 조건 회귀 기록

- 실패 증거: 학생 병합 main `d1a453d4` 실제 공개 Gazebo L2 [Run #44084070517](https://github.com/silverbjin/axia-robot-safety-student/actions/runs/44084070517), artifact #14328666838. 최초 원인은 Gazebo 서버의 `gz sim -s /tmp/nav2_ck_e2b1q.sdf` exit255(월드 파일 생성 이전 접근); 45초 뒤 `/clock CLOCK_MISSING`는 2차 증상. 이전 Ctrl+C 수정과 구분.
- RED: 학생 PR #40 [#44085109816](https://github.com/silverbjin/axia-robot-safety-student/actions/runs/44085109816)에서 공식 World Xacro 완료 대기 계약이 없는 상태 실패. 중간 L0 assertion 위치 오류 1회는 시험 자체의 오류로 분리 후 수정.
- GREEN: 학생 PR #40 [실제 L2 #44085392786](https://github.com/silverbjin/axia-robot-safety-student/actions/runs/44085392786) PASS. Artifact #14329581796 외부 63/63, 내부 61/61 SHA256 PASS. `launch.log`에서 `xacro-1 finished cleanly` 뒤 `gz-21 process started` 확인. Free→Intrusion→Lateral→Restored 실제 Path 52→52→49→52, `goal_sent=false`, `P2_L2_GRACEFUL_TEARDOWN`.
- 학생 main 병합 PR #40 SHA `6a3047b5aa219687f5fc918e467cea5115d3d482`. 수정은 `AXIA_D07_H01_GUI_NO_GOAL=1`, 시뮬레이션, 이동 Goal 불허 경로에만 적용. 공식 Nav2·Safety TTL·Controller 명령은 변경하지 않음.
- 새로운 **정확한** 학생 main source에 대한 실제 L2 재검은 별도 실행 결과로 판정하고, Owner WSL2/WSLg GUI L3 및 교육용 2회 Ctrl+C 현장 증거는 계속 NOT_RUN/HOLD로 둔다.
