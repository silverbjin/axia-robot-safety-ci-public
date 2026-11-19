# AXIA G07 Task04 — 강사 WSL2 교육용 시연 기준선 / 공개 CI 인수 기록

**기준선 ID:** `AXIA-G07-T04-DEMO-BASELINE-20261119-CZObXAdP`

**2026-11-19 교육용 MVP 시연 판정: ACCEPTED (범위 한정).** 학습 목표는 TurtleBot3 Waffle의 실제 Gazebo/Nav2 주행과 장애물 감속·정지, 해당 Goal 취소를 학생에게 시연하는 것입니다. **정식 안전/실물 E-Stop 인증 판정과 분리합니다.**

## 인수된 실제 강사 WSL2 실행

- 제출 `owner-moving-CZObXAdP.tar.gz` SHA256: `7fd07eb7b60330b3940d5501f2fc6629c1be8cff709dadd8acf396fdcbd5cd5b`
- 진단 ZIP SHA256: `016b18799adaf4525d810cda564a3d367908c383e2f2e43b2ff68a49db039c53`
- 원본 TAR/ZIP 및 manifest 모두 일치, SQLite rosbag 14토픽 quick_check=ok. 원본 rosbag과 민감한 호스트 로그는 공개 저장소에 업로드하지 않음
- 실제 실행 소스 Student `954fc2f054c50df783bc81c4d0835a6ee6f8645d`; Public CI 실제 Gazebo+RViz/Xvfb [#44478344652](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44478344652) **SUCCESS** / Owner 원샷 [Bootstrap #44480154746](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44480154746) **9/9 PASS**
- 실제 WSL2 Gazebo·RViz GUI 창 각 1개 검출, 단일 Nav2 EXECUTING Goal
- 실제 CLEAR Odometry 0.120313m 후 SLOW 장애물 이동, 전체 이동 0.128216m
- LiDAR front 0.684568m에서 CM 출력 0.003212m/s, Supervisor 명령 0.010706m/s, 기존 비율 약 30%로 감속 확인
- LiDAR front 0.391334m에서 CM/Guard 최종 Twist 0.0m/s, 실제 Odometry ZERO 1.038867s
- 동일 Goal UUID ActionStatus 5(CANCELED), `goal_cancel_ack=true`, Guard Latch 없음

## 고도화로 분리한 안전 시간 경계 — 교육용 관찰 이벤트

현장 Observer/Oracle은 STOP 장애물 전환 구간 `/scan` 메시지 간격 **339.177ms**를 측정했습니다(운영 검증 기준 300ms). rosbag `/safety/scan`에서도 약 335.783ms 공백이 독립 기록되어 있습니다. 이 시간 경계 검출을 **안전 계층의 모니터링/사후 검증을 설명하는 교육용 근거**로 보존하고, 교육용 시연 인수 조건에서는 제외합니다.

**정확한 역할 설명:** 이 339ms 사실은 시나리오 `Observer/Oracle`의 사후 간격 검증이 확인한 것입니다. Guard는 별도로 `AWAITING_CM_RECONCILIATION_ZERO`에 잠시 진입 후 복귀했으며 **Latch가 없었으므로**, Guard가 Scan 339ms에 대해 자체 Latch를 했다고 표현해서는 안 됩니다.

- 안전 주기·TTL/Guard Latch·검증기 원본 판정·원본 진단 정보는 **변경·삭제·완화하지 않습니다**.
- 이전 스크립트의 strict 시나리오 `status=BLOCKED` 및 Owner wrapper `status=HOLD`는 **정식 안전 경계의 원본 기록**으로 그대로 보존합니다. 교육용 MVP 시연 인수와 혼동하지 않습니다.
- STOP `set_pose` 구간 벽시계 공백의 인과관계는 미확정이며 고도화에서 조사합니다.
- 종료 후 Guard ROS Context 경고 및 화면 감속의 교육용 체감도 점검도 고도화/운영 개선으로 분리합니다.

## 교실에서 사용할 판정 용어

- **`AXIA_G07_TASK04_DEMO_BASELINE=ACCEPTED`** — 이번 강사 WSL2 실제 시연에서 주행→감속→정지→취소의 증거가 확인된 교육용 기준선
- **`FORMAL_SAFETY_TIMING_ACCEPTANCE=NOT_CLAIMED`** — 시연 목적에서 제외한 별도 안전 엔지니어링 트랙 (기존 300ms 임계값 유지)
- **`CERTIFIED_ESTOP=false`** — 인증된 하드웨어 E-Stop이 아닌 시뮬레이션 소프트웨어 정지

## 공개 통합 원칙

- 기존 Student 코드/Goal/Planner/Collision Monitor/Supervisor/Guard의 운영 안전 판단을 변경하지 않습니다. 강사 정답은 별도 비공개 저장소에 유지합니다.
- 공개 CI `main`에는 본 시연의 **8개 제한된 Git blob 파일과 이 문서 및 최소 정적 통합 테스트**만 포팅합니다. 기존 Draft PR #169의 100개 이상 누적 커밋을 `main`에 직접 병합하지 않습니다.
- 독립적 검증: 원래의 실제 Gazebo L2와 WSL2 현장 raw evidence 그대로 보존, 통합 PR에서는 빠른 L0 계약만 재확인 (이미 성공한 L2 반복하지 않음).
- [Student baseline](https://github.com/silverbjin/axia-robot-safety-student/pull/64)과 연결하여 향후 강의 자료 기준 SHA를 고정합니다.
