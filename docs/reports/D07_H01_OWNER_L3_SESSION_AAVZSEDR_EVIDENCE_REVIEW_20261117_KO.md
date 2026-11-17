# AXIA D07-H01 Owner L3 증거 검수 — session-20261117-aaVzSeDR

- 검수일: 2026-11-17
- 강사 현장 원본: `session-20261117-aaVzSeDR.tar.gz` 및 SHA256 sidecar (원본 ZIP은 공개 저장소에 배포하지 않음)
- 정확한 student main source: `6a3047b5aa219687f5fc918e467cea5115d3d482`
- 인수 판정: **`AXIA_D07_H01_EDUCATIONAL_L3_ACCEPTED=HOLD`** / **`AXIA_MVP_DEMO_ACCEPTED=HOLD`**
- 이번 작업은 사용자가 제공한 원본 증거만 로컬 검수. 코드 수정/신규 CI/Gazebo 재실행 없음.

## 무결성

- 압축 SHA256: `3d832f47db410f8ce89ca19f68d57021fd18bf99b295aa23c2a99b056a7b9f20` (업로드 sidecar와 재계산 일치)
- 외부 `SHA256SUMS` **72/72 PASS**, 내부 `native/evidence/SHA256SUMS` **61/61 PASS**

## 원본 반복 시연과 판정

| Cycle | Free | Intrusion | Lateral | Restored |
|---|---:|---:|---:|---:|
| 1 | 52 | 52 | 49 | 52 |
| 2 | 52 | 52 | NOT_RUN | NOT_RUN |

- `teaching_cycle_evidence.jsonl` **6행**, 각 행 실제 native set_pose ACK, Scan/Costmap stamp, official `ComputePathToPose`, RViz Path 구독자=1 기록. `goal_sent=false`, `cmd_vel_sent=false`, `robot_moved=false`는 이 런타임의 주장으로 독립 물리/안전 시계열 검증은 아니다.
- `D07_H01_TEACHING_CTRL_C_STOP REQUESTED` → `D07_H01_TEACHING_CTRL_C_STOP OPERATOR` → `D07_H01_TEACHING_OBSTACLE_RESTORED_AWAY` → `P2_L2_GRACEFUL_TEARDOWN`
- `exit_status.txt`: `runner_rc=130`, `operator_signal=INT`, `verifier_rc=3`. 실제 판정 `D07_H01_L3_COMPLETE_PHYSICAL_CYCLES=1` / `AXIA_D07_H01_L3_DATA_VERDICT=HOLD TWO_COMPLETE_REAL_PHYSICAL_REPEAT_CYCLES_NOT_PROVEN`.
- 2회차 Intrusion 이후 운영자 SIGINT가 입력되어 교육용 **2회 반복 완료 미달**. 원본에 없는 2행은 보간하거나 성공으로 주장하지 않는다.

## GUI 및 독립 rqt 미검증

- 원본 창 목록에 `Gazebo Sim` (1200×1000)과 `rviz2` (400×287) 존재.
- `gpu_glxinfo.txt`: `Microsoft D3D12 (Intel Iris Xe Graphics)`, accelerated=yes, Mesa 26.2.6. NVIDIA 사용 증거가 아니다.
- `window_Gazebo.xwd`, `window_RViz.xwd`: 정상 XWD 구조지만 실제 32bit 데이터 디코드 결과 **모든 픽셀 RGB(0,0,0)**. 스냅샷은 반복 시나리오 이전 14:06:44Z 획득. XWD의 WSLg/GL 캡처 한계인지 실제 블랙스크린인지 **ROOT_CAUSE_UNCONFIRMED**. Owner 실제 픽셀 화면 승인 없음.
- 독립 `rqt_graph` 실행/3계층 필터/터미널 A 종료 후 B 생존의 아카이브 증거 없음. 미실행으로 단정하지 않고 **NOT_VERIFIED**.

## 최초 비정상 경계 및 연쇄 구분

1. 첫 안전 진단 이상: `launch.log` 307행, 1794924400.084s, Supervisor `HEALTH_BAD_DIAGNOSTIC` / `SCAN_TIMEOUT` / `scan_age_sec=0.5078` / `cm_last_success_age_sec=0.5293`. 단일 진단 필드와 다른 CM/Guard 계층 TTL을 혼동하지 않는다. 안전 통합 안정성 **NOT_VERIFIED**.
2. RViz watcher의 GL 셰이더 오류 (1794924406.808s): `active samplers with a different type refer to the same texture image unit`. 비슷한 [ros2/rviz #463](https://github.com/ros2/rviz/issues/463) OPEN (맵 렌더는 가능했던 사례) 및 [#1309](https://github.com/ros2/rviz/issues/1309) CLOSED (Jazzy/24.04) 참조. 동일 원인/현재 실제 렌더 실패 **미확정**.
3. `native/student_live_stdout.log`에는 geometry 노드의 `D07_H01_GEOMETRY_ROS_CONTEXT_CLEAN_EXIT` **이후** `The following exception was never retrieved: cannot use Destroyable because destruction was requested`가 2회. 관련 [ros2/rclpy #1142](https://github.com/ros2/rclpy/issues/1142)는 Humble/22.04 유사 사례, OPEN. 현재 Jazzy ROOT_CAUSE_UNCONFIRMED; 네이티브 정상 종료 한 줄로 예외를 무시하지 않는다.
4. 두 번째 cycle이 Intrusion 다음 종료된 직접 경계는 **운영자 Ctrl+C**, 후속 `P2_L2_GRACEFUL_TEARDOWN`. `d07_gui_watcher_exit.txt`는 rc=3이며 내부 `D07_H01_GUI_CHILD_TERMINATED_BEFORE_PHASE_COMPLETE`는 종료 시점의 watcher 후속 증상으로 분리한다.

## 최소 후속 결정

- **코드 수정 없음**: 이번 L3 HOLD의 직접 자동 판정 경계는 운영자 조기 종료에 의한 2회 미완료. 근거 없는 Planner/TTL/GUI 리팩터 금지.
- Owner 실제 Windows 화면에서 Gazebo Waffle/장애물과 RViz Scan/Costmap/Path 변화를 관찰하여 캡처. XWD 검정 파일로 화면 PASS 증명하지 않음.
- 기존 pin 공개 원샷으로 필요한 미검증 현장 경계만 완료할 경우 두 번째 `cycle=2,stage=restored` 행을 확인하고 A Ctrl+C; B rqt_graph는 별도 실행/별도 종료를 관찰.
- rclpy async 예외 및 최초 `SCAN_TIMEOUT`은 증거/재현 가능 부분을 나누어 단일 가설로 접근; 공개 CI에 재현 가능한 최소 회귀가 필요한 때만 RED→GREEN→REFACTOR→REVIEW→COMMIT. 코드 변경 없는 본 검수에는 RED/GREEN 신규 결과가 없음.
- 교육용 H01 경로 계산은 움직이는 로봇 충돌 회피 안전성/Hardware E-Stop 검증이 아님. 전체 안전 MVP 별도 HOLD.

## Git

- 저장소: `silverbjin/axia-robot-safety-ci-public`
- 브랜치: `docs/d07-h01-l3-verified-baseline-20261117`
- 새 파일: `docs/reports/D07_H01_OWNER_L3_SESSION_AAVZSEDR_EVIDENCE_REVIEW_20261117_KO.md`
- 사용자 승인 전 `main` 병합 없음. 새 CI 실행 없음. Source / runtime 변경 없음.
