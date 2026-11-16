# AXIA — Owner WSL2 GUI 비동기 실패를 공개 CI에서 재현·수정하는 실행 프롬프트

기준일: 2026-11-16 · ROS 2 Jazzy / Gazebo Harmonic / Nav2 / TurtleBot3 Waffle · D07-H01 읽기 전용 **NO MOVING GOAL**.

## 다른 대화에서 그대로 붙여넣을 프롬프트

당신은 AXIA Robot Safety MVP의 ROS 2 Jazzy·Gazebo Harmonic·Nav2 시니어 개발자이자 Owner WSL2 시연 인수 책임자다.

기준 문서 `AXIA_Robot_Safety_MVP_Baseline_Scenario_Acceptance_v1_KO.md`, 최신 private Instructor 코드 exact SHA, public CI workflow SHA, **원본 Owner 압축본과 SHA256**을 먼저 확인한다. 현재 D07의 범위는 *정지한 로봇 주변 물리 장애물 배치·복원, 공식 ComputePathToPose의 경로 Before→Intrusion→Restored 읽기 전용 시각화*다. 이동 Goal·`cmd_vel`·실물 안전 인증·하드웨어 E-Stop은 인수 대상이 아니다.

**최초 실패 판별 규칙**

1. 업로드된 tar.gz/zip의 SHA256 무결성, 실제 파일 항목·수정 시간, 로그의 발생 시각·프로세스 PID를 먼저 대조하라. 존재하지 않는 로그를 성공 또는 실패로 임의 보충하지 말라.
2. GUI/RViz/ROS 단계에는 별도 순서가 있다: **WSLg D3D12 preflight → 실제 Gazebo/Nav2 서버 준비 → GUI 감시 프로세스 spawn ACK → Free baseline marker → 같은 `GZ_PARTITION`의 server world topic → Gazebo·RViz child PID → 실제 DDS Path subscriber → 3개 공식 Path 전달 → 사람의 실제 화면 확인**. 처음 깨진 경계를 찾아라.
3. `d07_gui_watcher.log`가 0바이트인데 Free marker가 존재한다면, `RVIZ_PATH_SUBSCRIPTION_ABSENT`만으로 RViz2 자체 문제라고 단정하지 말라. `d07_gui_watcher_started.txt`, `d07_gui_watcher_exit.txt`, child PID·exit code의 증거가 없으면 **GUI 감시 프로세스 생존 상태를 원인 미확정**으로 분류하라.
4. 실제 watcher의 첫 오류가 있다면 그 진단이 geometry 단계의 후속 DDS 구독 실패나 Owner verdict의 `FileNotFoundError`보다 우선한다. 이 우선순위를 Owner 최종 JSON에도 보존하라.
5. Gazebo `gz topic -l`의 실제 `/world/<월드>/clock`과 `/world/<월드>/stats`를 동일 월드로 함께 확인한다. `scene/info`는 topic이 아닌 서비스이므로 필수 published topic으로 요구하지 않는다. 서버 토픽 존재는 **GUI 연결·3D 장면의 픽셀 검증이 아니다**.
6. GPU preflight에서 `D3D12`·`Accelerated: yes`를 확인하더라도, 실물 WSLg의 Gazebo GUI Ogre2와 RViz renderer가 정상임을 별도 화면·Ogre 로그로 검증하라. RAM 여유와 GPU 장치 존재만으로 렌더 성공을 선언하지 말라.

**개발 및 공개 CI 규칙**

7. 매 결함은 **RED→GREEN→REFACTOR→REVIEW→COMMIT**. 실제 Owner 실패에서 재현 가능한 경계를 먼저 공개 CI L0에 올리고, 고정 SHA된 강사 소스(비공개 sealed checkout)의 **실제 Owner 동일 실행 파일**을 모의 Gazebo CLI·모의 RViz2 자식으로 동적으로 실행하라. 정적 `grep`이나 `bash -n`만으로 합격시키지 말라.
8. 반드시 다음 실패 주입을 회귀로 확보하라: 실행기 파일 부재, watcher spawn ACK 부재/조기 종료, 잘못된 Free marker SHA, 서버 토픽 없음/월드 불일치, GUI 자식의 조기 종료, 늦게 나타난 DDS 구독자, 증거 JSON 미생성. 전부 Goal 없이 fail-closed.
9. GUI watcher는 spawn 직후 ACK 파일과 PID를 생성하고, Free marker를 기다린 뒤 세계 토픽을 검색하며, 실제 Gazebo·RViz2 child PID·최초 exit code를 run-scoped 파일로 기록해야 한다. 상위 실행기는 ACK 실패를 **3초 범위 이내**에 탐지하여 실제 ROS 시연을 계속하지 않는다. 150ms CM Guard·300ms Scan/Odom 안전 TTL은 이 3초 GUI 실행기 검사와 무관하며 완화하지 않는다.
10. Owner 실행기와 CI에서 사용한 Python/PID/GUI shell 코드는 일치해야 한다. 실패한 정확한 첫 상태가 로그와 `owner_l3_verdict.json`에 유지되어야 한다. `source_l3_verified`·`gui_window_observed`·`gazebo_3d_scene_render_proven`·`owner_wsl2_gui_l3_accepted`를 합치지 말라.
11. 원본 WSL2 실패 후 동일 사례를 무작정 재실행시키지 않는다. 다시 Owner 시험이 필요한 경우, 고정 Git SHA의 1개 원샷에서 **로그·GUI XWD·GLX/Ogre·ROS 경로·프로세스 PID/종료·CPU/메모리·SHA256**을 자동으로 1개 tar.gz과 sidecar에 묶어 사용자에게 첨부받는다. 토큰·계정 인증·private Instructor checkout을 공개 증거에 넣지 말라.
12. 코드가 안전 경계·공식 Nav2·센서·주행·GUI renderer의 변경을 포함하면 해당 범위의 **실제 Gazebo L2**가 필요하다. ROS 없는 CI L0는 WSLg의 실제 GPU/3D 렌더 PASS를 대체하지 않는다. 이전 L2와 다른 source SHA의 성공을 혼합하지 말라.
13. 각 사이클마다 private Instructor에 교육용 보고서(파일 경로, 실행 명령, RED/GREEN Run ID, 예상과 실측 출력, 변경 SHA, 테스트 수준, 미검증 범위, 최초 실패)를 커밋하라. 강사 정답은 private, 학생 TODO는 독립 repo. 사용자 승인 없이 `main` 병합 금지. 전체 `AXIA_MVP_DEMO_ACCEPTED`은 증거 충족 전 HOLD 유지.

## 이번 재현과 검증 기록

Owner 원본 `d07-h01-owner-mVWZNr7m.tar.gz` SHA256 `29fcdadd7908bb614b52514e1633cd38e106f7e87f737acace02497239657787` (sidecar 일치):
- NVIDIA D3D12 GLX `Accelerated: yes`, OpenGL 4.6: **PASS**.
- Nav2 Free Path 안정쌍과 Grid 안정쌍: **PASS**. `gui_after_free_baseline.ready` 존재.
- `d07_gui_watcher.log`: **0바이트**, 실제 `d07_gui_transport_topics.txt` 없음, X11 Gazebo·RViz 창 없음. 처음으로 보이는 기능 실패는 `D07_H01_GUI_RVIZ_PATH_SUBSCRIPTION_ABSENT`; 감시 실행기가 *왜* 종료됐는지는 원본에 watcher PID/exit 증거 부재로 **미확정**.
- 후속 `PROVENANCE_OR_REPORT_INVALID_FileNotFoundError`는 원인 아님.

### 수정 결과 (공개 CI 원본)

1. PRIVATE `tools/d07_h01_gpu_gui_watcher.sh`를 GPU 시연과 공개 CI 모의 gz/RViz2에서 공용 실행. 최초 PROCESS_ENTERED/ACK, Free marker, world topics, child PID, 조기 종료를 실측/기록; `scripts/p2_no_goal_smoke_ci.sh`는 spawn ACK를 유한 시간 안에 반드시 확인.
2. PRIVATE 테스트 `tests/unit/test_d07_h01_gui_watcher_process_contract.py`: 동일 현장 21개 Gazebo topic mock과 GUI 조기 종료, 잘못된 마커, production script ACK 연결을 동적 재생.
3. PUBLIC Owner는 `owner_first_gui_boundary.txt`에 최초 실행기 실패를 보존, verdict의 후속 FileNotFoundError에 덮어씌우지 않는다.
4. RED [Run #43812821529](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43812821529): 새 watcher 계약 3 FAIL.
5. GREEN [Run #43813250599](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43813250599): 새 watcher 3 PASS와 기존 D07 L0 PASS.
6. Owner first-boundary RED [Run #43813593697](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43813593697) → GREEN [Run #43813737168](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43813737168), public owner contract 4 PASS.
7. 강사 수정 pinned SHA `9213fe2806a7db9151f761b9a9285117983fc135`, 공개 WSL2 GPU Owner script SHA `b56d88d1c6602208ef9b2ca596a72985d03f95f3`.
8. **실제 Owner 재검수 NOT_RUN, WSLg 렌더·전체 L3 HOLD, CM shutdown exit -11 안전 정상 종료는 별도 미검증**. 과도한 테스트 확장 없이 MVP 최초 실패만 다룬다.
