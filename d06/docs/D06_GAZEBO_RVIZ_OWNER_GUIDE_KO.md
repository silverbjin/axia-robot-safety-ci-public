# AXIA D06 — Gazebo GUI + RViz2 강사 Live Demo

> **2026-11-14 FINAL OWNER ADMISSION: HOLD.** 실제 공개 Gazebo L2 [#43587404886](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43587404886)에서 CM RMW publication source gap=172.153ms >150ms가 재현되어 정식 CLEAR→SLOW→STOP+종료 전체 인수가 실패했다. **현재 WSL2 Owner 재실행 금지.** 최신 D06 원샷은 `d06/acceptance/d06_g07_final_owner_ci_gate.json`의 CI 승인 없이는 ROS/Gazebo/Goal 전에 자동 차단된다. 구형 SHA/구형 원샷은 이 차단을 제공하지 않으므로 사용하지 않는다.
>
> 공통 진단·원인 대조·RED→GREEN은 공개 CI에서 수행한다. 실제 전체 시연 조건(Scan<=300ms, CM/Supervisor/Guard<=150ms, odom STOP>=1초, 원본 bag/정상 종료)이 검증된 뒤에만 공개 CI 고정 SHA를 강사에게 최종 검수용으로 배포한다. 현재 수업에는 **공식 격리 CM ROS L1**을 대신 사용하며 기존 G07 성공 증거는 과거 증거로만 설명한다.


## 목적과 범위
- 일정: 2026-11-16 19:00–22:00, 이론 60분·실습 120분. 21:25–21:40 강사 Live Demo에 사용.
- 목표 1: **거리 구간별 속도 제한 및 감속ㆍ정지 규칙 이해** — 실제 Waffle의 CLEAR→SLOWDOWN→STOP에서 CM 전 속도, CM 이후 속도, 최종 Guard 속도, odom 관측값을 비교한다.
- 목표 2: **Safety Bubble 기반 안전제어 로직 설계 실습** — 학생 Python 정책(Stop 0.40m, Slow 0.75m, ratio=0.30, UNKNOWN)을 설명하고 공식 LaserScan+CM Zone/min_points=4 동작과 비교한다.
- 새 ROS 안전 제어 코드, Goal·/cmd_vel publisher 및 TTL 변경은 **0**. 최신 P4 G11 공개 Release SHA d1769b8675c85e7ee564966637cef9113435904a를 호출한다. 해당 Release는 비공개 Instructor SHA afe4e9ae3f6542ef7b2bd3097ce5c15ae5a5ddcc 및 Git tree 580dec5be1988b26d5189616b1b01559a0f1f9a5를 검증하고 원본 RMW 진단·raw custody를 보존한다. 과거 eb984b7 G07 고정은 사용하지 않는다.
- RViz marker의 원은 **교육용 표시**이지 공식 CM action 증거가 아니다. 실험은 SIMULATION ONLY. SW Stop과 실제 인증 E-Stop을 혼동하지 않는다.

## 검증 현황

| 근거 | 수준 |
|---|---|
| D06 공식 CM 기존 공개 Actions #42656227824 | 실제 ROS L1 PASS, 합성 LaserScan 0.20/0.06/0.00m/s |
| G07 기존 공개 Actions #43339521667 및 Owner ynAuVvkf | 실제 Gazebo L2/Owner L3 범위 한정 CLEAR→SLOW→STOP, odom dwell 약 1.032초 |
| **새 D06 Gazebo GUI + RViz2 sidecar** | 공개 CI L0 계약과 WSL2 창 실측 별도. 새 GUI/ROS 통합은 아직 NOT_RUN |
| 물리 충돌 없음 인증 또는 hardware E-Stop | NOT_RUN / NOT_CLAIMED |

기존 G07 PASS를 이 신규 GUI의 PASS로 승격하지 않는다. 실제 Nav2 cmd 입력은 계속 달라질 수 있으므로 D06 합성 시험의 0.20→0.06m/s를 실제 모든 순간에 강요하지 않는다.

## 강사 WSL2 원샷: 터미널 A

사전 조건은 WSL2 Ubuntu 24.04, WSLg DISPLAY, ROS 2 Jazzy/Gazebo Harmonic, gh auth login(private Instructor). 복사 명령의 PUBLIC_SHA에는 **공개 CI GREEN이 검증한 정확한 40자리 HEAD**를 넣는다. 구동 전 WSL2의 다른 Gazebo 수업은 종료한다. 기존 학생·강사 작업 폴더는 보존한다.

    (
      set -Eeuo pipefail
      PUBLIC_SHA="c74f37bb7af8f31afcfae842f3d7eddc3f0d849f"
      LAB="$(mktemp -d "$HOME/axia_d06_gazebo_rviz_public_XXXXXXXX")"
      git -C "$LAB" init -q
      git -C "$LAB" remote add origin https://github.com/silverbjin/axia-robot-safety-ci-public.git
      git -C "$LAB" fetch -q --depth 1 origin "$PUBLIC_SHA"
      git -C "$LAB" checkout -q --detach FETCH_HEAD
      test "$(git -C "$LAB" rev-parse HEAD)" = "$PUBLIC_SHA"
      bash "$LAB/d06/scripts/d06_gazebo_rviz_owner_wsl2_once.sh" --self-check
      bash "$LAB/d06/scripts/d06_gazebo_rviz_owner_wsl2_once.sh"
    )

**안전:** 원본 G07 Owner가 실제 /dev/tty에 YES-P2-G07-GOAL을 요청한다. 강사가 직접 입력해야 한다. 자동 동의 스크립트, 파이프 tee, CI용 Goal 권한 우회는 금지한다.

예상 출력(실제 신규 ROS·WSL2 실행 출력 아님). **D06_RVIZ_STARTED 및 D06_EDU_OBSERVATION_ZONE은 sidecar.log / readonly_monitor.log에 저장되며, 강사 A의 포그라운드 G07 stdout에 직접 나타나지 않을 수 있다.**

    D06_OWNER_RVIZ_STATIC_PASS ... GAZEBO_NOT_RUN RVIZ_NOT_RUN
    Case G07 ... Type YES-P2-G07-GOAL:
    AXIA_G07_OWNER_GUI_LAUNCH_SELECTED WSLG_RENDER_REQUIRES_LIVE_CONFIRMATION
    D06_RVIZ_STARTED domain=<domain> rviz_pid=<pid> monitor_pid=<pid>
    D06_EDU_OBSERVATION_ZONE {"zone":"CLEAR","evidence_only":true,...}
    D06_EDU_OBSERVATION_ZONE {"zone":"SLOWDOWN","evidence_only":true,...}
    D06_EDU_OBSERVATION_ZONE {"zone":"STOP","evidence_only":true,...}
    D06_GAZEBO_GUI_NOT_YET_VERIFIED ...

## 화면과 터미널 분리

- **Gazebo GUI:** 공식 TurtleBot3 Waffle, 실제 G07 물리 장애물, 실제 로봇 이동·감속·정지를 관찰한다. 원형 장애물 모델이며 사람형 외형·YOLO와의 통합은 이번 MVP 범위 밖.
- **RViz2 (rviz2):** Fixed Frame: odom, RobotModel, TF, 원본 LaserScan /scan, Odometry /odom, 노랑 0.75m/빨강 0.40m 교육용 MarkerArray /axia/d06/rviz/bubble. 원형 표시는 공식 CM polygon 신호가 아니다.
- **강사 터미널 A:** 원샷과 실제 Owner 수동 Goal 승인; 완료 후 G07 EVIDENCE=... 및 D06_GUI_EVIDENCE=... 출력 확인.
- **강사 터미널 B (선택):** 현장 강사 A의 **정확한** D06_GUI_EVIDENCE 경로와 새 session_attachment.txt에서 ROS_DOMAIN_ID를 읽은 후 읽기 전용 구독. /cmd_vel을 publish하거나 Goal을 보내지 않는다.
- **학생 터미널 S:** 기존 D06 Python TODO의 RED→GREEN 확인 후 화면 결과와 비교한다.

터미널 B 예시:

    source /opt/ros/jazzy/setup.bash
    EVIDENCE="<강사-A가-출력한-D06_GUI_EVIDENCE-경로>"
    cat "$EVIDENCE/session_attachment.txt"
    export ROS_DOMAIN_ID="$(sed -n 's/^ROS_DOMAIN_ID=//p' "$EVIDENCE/session_attachment.txt")"
    export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
    ros2 topic info /scan
    ros2 topic info /odom
    ros2 topic echo /cmd_vel_pre_guard

터미널 B Ctrl+C는 B의 조회만 중단한다. 터미널 A Ctrl+C는 원본 G07 Owner의 종료 경로를 요청한다. 원본은 Nav2 Lifecycle 정상 종료를 시도하고 D06 sidecar는 자신이 시작한 RViz2와 MarkerArray 관찰기만 종료한다. killall, pkill -f, wsl --shutdown으로 다른 수업 프로세스를 종료하지 않는다.

## 증거 / 오류 인수 경계

강사 A 완료 후 D06_GUI_EVIDENCE 아래 SHA256SUMS, sidecar.log, rviz.log, readonly_monitor.log, readonly_samples.jsonl, session_attachment.txt 및 first_failure_triage.json(있는 경우)을 확인한다. 최신 P4 G11의 비공개 RMW 발행/수신 진단 및 원본 보관 증거와 동일 Goal인지 별도로 대조한다. 원본 Owner EVIDENCE의 summary.json, G07/live, 14-topic rosbag2, launch.log와 **같은 세션**인지 대조한다.

- **Gazebo GUI와 RViz 두 창이 실제로 보이는지** 사람 눈으로 확인한다. D06_RVIZ_STARTED는 단지 프로세스가 생성됐다는 뜻이다.
- **공식 CM의 실제 STOP**은 G07의 실제 /scan→CM→Guard→/cmd_vel 및 /odom 증거로 확인한다. D06_EDU_OBSERVATION_ZONE은 단순 전방 scan 기반 교육용 라벨로 CM 판정이 아니다.
- 최초 안전 상태 전이, 최초 Scan/CM/Guard 타이밍 위반, 사용자 Goal 승인, 강제 종료 여부를 확인한다. 입력 소실은 UNKNOWN으로 다룬다.
- 새 WSL2 오류 발생 시 현장에서 같은 동작을 반복하지 않는다. 재현 가능한 최초 실패를 공개 CI에 편입한 뒤 RED→GREEN 회귀 검증한다.
- 새 GUI 통합 검증 전에 D06_GAZEBO_LIVE_PASS를 주장하지 않는다.

## 공개 CI 선검증 및 출고

RED→GREEN→REFACTOR→REVIEW→COMMIT. 학생 공개 TODO와 Instructor private 정답/Hidden Tests는 분리한다. 본 공개 저장소는 원본 비공개 G07 소스를 포함하지 않는다.

새 PUBLIC CI L0 PASS는 정적 소스 계약이며 **ROS/Gazebo L2나 WSL2 GUI 성공을 뜻하지 않는다.** 관련 실제 L2 검증 범위를 명시한 뒤 인수 여부를 별도 판정한다. main 병합은 반드시 사용자 승인 후에만 진행한다.


## 2026-11-14 현장 문제의 최초 실패 경계와 P4 최소 수정

- 과거 G07 Owner L3 scoped PASS는 실제였으나, 이후 간헐적 CM/Guard 150ms 타이밍 오류가 재발하여 최신 통합 스테이징에서도 Owner 정식 인수는 HOLD.
- 이번 G07 Owner 최초 /cmd_vel_pre_guard 관측 공백 **172.739ms > 150ms**, Guard 내부 마지막 CM 수신 나이 **181.552ms > 150ms**, Supervisor 나이 56.141ms로 정상. 동시 관찰기의 더 최신 CM 샘플은 Guard 수신 지연 *가능성*이며 CM 발행 정상 증명은 아님.
- 실제 launch.log에는 Controller 20Hz 루프가 약 5.46Hz로 떨어지는 경고도 있음. WSL2 GUI CPU 경합 가설은 있어도 **인과 확정은 아직 불가**.
- D06 UI만 nice 15, RViz2 frame rate 8, 교육용 MarkerArray 1Hz로 하향. 이 조치는 CPU 부하 완화 **후보**로 실제 Guard TTL 문제의 영구 수정이 입증된 것은 아님. Supervisor/CM/Guard/Goal/공식 Nav2 안전 TTL은 전혀 변경하지 않는다.
- 신규 실패가 반복되면 D06_GUI_EVIDENCE/sidecar.log와 private P4 G11 원본 첫 RMW gap/Guard latch를 결합한다. 가장 마지막 Python exception이 아니라 최초 안전 상태 전이와 첫 CM source/receive 위반을 우선하고, 원본은 공개 업로드하지 않는다.
- D06_G07_POSTRUN_TRIAGE는 비식별 경계 분류로 언제나 safety_pass=false. 실제 Gazebo GUI+RViz WSL2 인수 전 새 Live PASS를 선언하지 않는다.


## Owner cold-start 이후 읽기 전용 위치 진단 (2026-11-14)

제공된 WSL2 원본 G07의 `STATUS=STARTUP_READY_NO_GOAL` 및 `LAST_COMPLETED=NAV2_ACTION_READY`는 Nav2 사전 준비가 성공했다는 뜻이다. 최초 Clock 5.426초, Localization Lifecycle 4.297629초 ACK, Navigation Lifecycle 8.319897초 ACK이다. 이 근거만으로 실제 G07 Goal이나 Safety STOP 완료를 주장하지 않는다.

**이전 검사기의 `ELAPSED_SINCE_START_LOG_SEC=587.3`은 로그 파일의 마지막 수정 시각부터 587.3초가 흐른 값이지, 480초짜리 startup 실행 시간이나 timeout이 아니다.** 최신 검사기는 `STARTUP_LOG_LAST_WRITE_AGE_SEC`로 명칭을 교정하고 원본 이후 단계 `POST_STARTUP_PHASE`를 추가했다.

기존 Gazebo·Owner를 재시작하거나 터미널 A를 종료하지 말고, 새 터미널 B에서 최신 공개 읽기 전용 검사기만 실행한다.

~~~bash
(
  set -Eeuo pipefail
  SHA="3fd0ba58debab9bae8621d86cc513fab63f015e4"
  SCRIPT="$(mktemp "$HOME/axia_d06_phase_check.XXXXXXXX")"
  trap 'rm -f -- "$SCRIPT"' EXIT
  curl -fsSL --retry 3 \
    "https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public/$SHA/d06/live/d06_owner_startup_inspect.py" \
    -o "$SCRIPT"
  python3 "$SCRIPT" \
    --run-root "$HOME/axia_p2_private_evidence/p2-l3-owner-Nfb3pALe/G07"
)
~~~

`NAV2_READY_NEXT_STAGE_NOT_YET_OBSERVED`는 후속 로그 미관찰, `CORRIDOR_CHECK_STARTED_OR_FAILED`는 지도 검증 시작/실패, `PHYSICAL_PREG0AL_STARTED_OR_FAILED` 또는 `PHYSICAL_PREG0AL_READY_NO_GOAL`은 Goal 이전 실제 장애물·LiDAR 검사, `LIVE_OBSERVER_STARTED_GOAL_UNVERIFIED`는 Live 실행 시작만 관찰, `LIVE_GOAL_SENT_BLOCKED_SAFETY_REVIEW`는 기존 결과에 Goal 후 실패 기록, `OWNER_EXIT_RECORDED_REVIEW_REQUIRED`는 Owner 종료 summary가 저장됐다는 뜻이다.

이 상태값은 **파일에 남은 기록을 해석한 것**이지 현재 ROS 프로세스 생존이나 실제 주행 완료를 증명하지 않는다. 이후 안전 문제를 발견하면 최초 Guard 안전 전이/최초 CM RMW 150ms·Scan 300ms 위반을 먼저 검토한다. Owner 원본은 읽기 전용으로 보존하고 공개 CI에는 비식별 데이터만 사용한다. 기존 Owner 수동 Goal 승인은 유지한다.
