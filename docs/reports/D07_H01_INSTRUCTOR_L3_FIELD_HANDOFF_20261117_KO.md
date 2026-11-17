# D07-H01 강사 WSL2/WSLg L3 현장 인수 — 공개 CI 인계

- 작성일: 2026-11-17
- 범위: ROS 2 Jazzy / Gazebo Harmonic / 공식 Nav2 / TurtleBot3 Waffle / RViz2 / rqt_graph
- 원칙: 강사용 새로운 ROS 구현 없이 학생용 공개 H01 반복 시연 재사용, 현장 증거 한 번에 수집
- 공개 CI 저장소: silverbjin/axia-robot-safety-ci-public
- 개발 브랜치: feat/d07-h01-instructor-wsl2-l3-field-20261117
- 인수 실행 파일: scripts/axia_d07_h01_instructor_l3_wsl2_once.sh
- 검증 시험: tests/test_d07_h01_instructor_l3_field.py
- 워크플로: .github/workflows/d07-h01-instructor-wsl2-l3-field-l0.yml
- 입력 학생용 공개 main 고정 SHA: c25d63d928da0cfb6513b191e582742fd2f0a6bb
- 강사 가이드 main SHA: f46874470a814be8f6976b6adbcaa1e43a1fe681
- 전체 AXIA 안전 MVP: AXIA_MVP_DEMO_ACCEPTED=HOLD

## 배경 및 재사용한 성공 근거

학생 공개 main의 실제 Jazzy/Harmonic Gazebo+RViz2+rqt_graph L2 Run #44072468003 PASS. 고정 학생 main의 실제 업로드 ZIP Artifact #14323298203의 외부 63/63, 내부 61/61 SHA256 일치. 실제 Gazebo native pose ACK, /scan, /global_costmap/costmap, 공식 ComputePathToPose Path, RViz 구독을 확인. 한 개 CI 한정 반복(Free→Intrusion→Lateral→Restored), 계획 Path 52→52→49→52, goal_sent=false, robot_moved=false, 정상 teardown. 이것은 강사 WSLg 화면 픽셀이나 실제 Ctrl+C 인수가 아니다.

비공개 강사 정답·hidden_tests는 재배포하지 않는다. 본 원샷은 동일한 학생 공개 소스를 고정 SHA로 별도 경로에 clone한 뒤 기존 강의 모드를 호출한다.

## L3의 최소 범위

1. WSL2 Ubuntu 24.04 + Jazzy + WSLg 화면 준비, 공개 학생 소스 SHA 정확히 pin.
2. Gazebo, RViz2, rqt_graph GUI 3개를 동일 ROS_DOMAIN_ID=95에서 관찰. 그래프 3계층 필터는 강사 가이드 A-2절을 따른다.
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

운영: 스크립트가 실제 Jazzy 환경을 스스로 source한다. Gazebo/RViz/rqt_graph 창과 실제 경로를 관찰하며 rqt_graph 상단 노드/토픽 필터를 단계적으로 변경한다. 연속 2회 네 위치 반복을 확인한 뒤 **실행 터미널에서 Ctrl+C 단 한 번** 누른다. 모든 원본 및 종료 증거를 자동으로 압축하며 별도의 기존 ROS 프로세스에 무차별 pkill을 하지 않는다. 창 XWD는 가능할 때만 캡처하므로 화면 검수는 Owner 육안 및 사진 3장을 별도 제출해야 한다. 화면이 보이지 않으면 실패 원본과 첫 위반을 보존하고 동일 현장 시도를 반복하지 않는다.

산출물:
- ~/axia_d07_h01_instructor_l3/session-*/native/evidence/ (H01 원본 실측·종료)
- ~/axia_d07_h01_instructor_l3/session-*/l3_structural_verdict.txt (L3 DATA 전용 판정)
- ~/axia_d07_h01_instructor_l3/session-*.tar.gz 및 .sha256
- 창 목록, glxinfo 및 캡처된 경우 window_Gazebo.xwd, window_RViz.xwd, window_rqt_graph.xwd
- 별도 Owner 화면 육안 승인(3개 rqt_graph 필터 단계 및 Gazebo/RViz 장면)

## 기대 출력 및 최종 판정 기준

필요한 사실:
- 고정 student SHA 출력, --self-check/--doctor 성공
- D07_H01_TEACHING_CYCLE 원본 JSONL의 두 개 **완전한** 4단계 반복
- 원본 geometry.json real_nav2=true, real_laser_scan=true, goal_sent=false, robot_moved=false
- OPERATOR Ctrl+C 기록, P2_L2_GRACEFUL_TEARDOWN, 동일 세션 Gazebo/RViz/rqt 창 목록
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

원샷은 공개 CI 브랜치에서 검증 후 SHA-pinned raw 다운로드로 바로 사용할 수 있다. **main 병합은 별도 사용자 승인 전 수행하지 않는다.** 비공개 강사 정답 저장소와 학생 공개 main은 변경하지 않는다.
