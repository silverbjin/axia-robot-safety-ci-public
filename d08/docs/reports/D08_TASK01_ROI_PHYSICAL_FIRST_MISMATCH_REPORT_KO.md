# AXIA D08 Task01 — 실제 동일 World D05 물리 거리 불일치·원본 ROI 증거

## 작업 기준
- Public CI `silverbjin/axia-robot-safety-ci-public`; branch `feat/d08-unified-sensor-cm-path-20261118`; base main `62e366b51c64da25ad0216328fe1e019b78e0bef`; PR #166.
- 선행 실제 통합 HEAD `d06c00a3846b1fcdcc8a5f3532b54a523de78283`; [Run #44229304083](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44229304083): L0 75 PASS, 별도 센서 L2·YOLO replay L1 PASS. 한 World live YOLO+D05+공식 Nav2 3 Path 실제 수행, **최종 거리 품질 FAIL**.
- 실제 원본 artifact #14394487446 `d08-same-world-live-person-range-cm-nav2-evidence`, 작업자 ROS_DOMAIN_ID 69, GZ_PARTITION `axia_d08_ci_12493`, 실제 Actions checkout SHA `142f0c90fdb61a385e3c1ec954b83f09fe18ba5f`. Source HEAD와 CI merge SHA는 구분.

## PLAN → RED → GREEN → REFACTOR → REVIEW → COMMIT
- PLAN: master plan v1.8 `659144df98717c16d0795fa09a506e6da949ceb8`.
- 실제 최초 실패: `D08_TWO_ACTUAL_PERSON_DISTANCES_NOT_DISTINCT`, exit2. 사람은 더 가까워졌으나 RGB-D ROI 중앙값이 역증가, 너무 가까운 화면에서 bbox 높이 80px 부분 검출. 물리적 불일치 개선이 먼저 필요하므로 threshold 축소나 임의 PASS 금지.
- 실제 측정:
  - old slow native person world(-1.43,-0.5,.24): 실제 LaserScan 0.559762m, YOLO person score .254660, bbox [162,92,458,380] 높이288px, 11/16 Depth 유효, median **0.475343m**, RGB/Depth/Detection source stamp 18.801s.
  - stop(-1.63,-0.5,.24): 실제 LaserScan 0.362725m, person score .549731, bbox [116,25,499,105] 높이80px, 10/16 Depth 유효, median **0.534589m**, stamps 25.401s.
  - side unknown(-1.979119,0.171291,.24): 실제 4 RGBD + 4 DetectionArray, person class 유실로 `NO_PERSON_CLASS_IN_ACTUAL_YOLO`, stamp 30.402s. UNKNOWN은 CLEAR나 주행 허가가 아님.
  - Actual same-World official Nav2 3 Path before/intrusion/restored Costmap lethal 0→73→0, LiDAR first gap no violation, official CM 실제 /scan 구독자 확인, CM 내부 receiver age/Guard TTL 미계측. Actual /cmd_vel 및 Navigation Goal 미발행.
- 원인 단일 가설 (확정 아님): Stop person bbox가 상단 80px만 감싸고, 4x4 중심 Depth가 전신이 아닌 머리·배경의 경사 시선을 샘플링함. 카메라와 LiDAR 장착 위치 차이도 존재하므로 두 절대 거리 동일성을 전제하지 않지만 **물리적 근접 시 ROI 방향 역전**은 판정하지 않음.
- CI 실제 RED commit `b9a3947d35aaeb9f7e1525e08cec49c31170e8c4`, [Run #44231082387](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44231082387): L0 수집 `ImportError: cannot import name capture_actual_roi_source`, 실제 L2 SKIPPED. 추가 역전 방향 물리거리 회귀 및 CI 독립 반복 Gate 검증 준비.
- GREEN 최소 후보: 기존 public D05 read-only ROI16 샘플/Stamp/Host-age 정합 경계는 그대로 유지. `d08/harness/d08_live_person_range.py`에 실제 선택된 RGB 프레임 PPM과 원본 16개 32FC1 샘플·bbox·RGB/Depth 원본 SHA256 저장만 추가. `d08_live_person_range_session.py`는 `farther` 후보 x=-1.20,y=-.50,z=.24 (실측 LaserScan .70–.90m 허용)와 원래 Stop x=-1.63 및 side UNKNOWN을 순차 한 번씩만 관찰, `distance_far > distance_stop` 및 delta >=.12m 보존. 이 단계가 실패하면 ROI 증거로 다시 원인 분석하며 새로운 모델/일반 sweep 도입 금지.
- REFACTOR: 이전 `--official-nav2` 독립 첫 Path L2는 #44227457087에서 PASS했으며 신규 실시간 combined job에서도 실제 official Nav2 three Path PASS였음. 동일 기능을 별도 병렬 Gazebo job에서 무의미하게 재검증하다 `/controller_server/change_state` 응답 timeout 및 `D08_OFFICIAL_NAV2_PLANNER_UNAVAILABLE`이 발생했으므로 **independent first Path diagnostic은 manual workflow_dispatch에서만**. Mandatory combined CI job에는 실제 한 World official Nav2/Costmap/Scan/Path와 live YOLO/D05 게이트 유지. 새로운 결과를 다른 독립 job 증거로 보완해 E2E 주장하지 않음.
- REVIEW: 공식 Nav2/YOLO/CM 원본·Planner/Controller 불변, 인증 E-Stop 아님, 사람/로봇 임의 위치 조작은 CI 시연 중 동일 물리 Proxy만, no cmd_vel Publisher/No Moving Goal, 안전 스캔 freshness 0.5s/3층 TTL 상향 없음. 기존 학생 TODO/비공개 강사 정답 분리.
- 소스 파일 경로: `d08/harness/d08_live_person_range.py`, `d08/harness/d08_live_person_range_session.py`, `d08/tests/test_d08_roi_physical_trace.py`, `d08/tests/test_d08_live_person_range_session.py`, `.github/workflows/d08-main-no-goal-real-gazebo-l2.yml`.
- L0 실행 명령: `python -m pytest -q d08/tests/test_d08_roi_physical_trace.py d08/tests/test_d08_live_person_range_session.py d08/tests/test_d08_ci_single_world_priority.py`
- 실제 ROS/Gazebo L2: `python3 -u d08/scripts/d08_public_gazebo_l2.py --actor /tmp/axia-d08-live-assets/walk.dae --out results/d08-live-person-nav2-e2e --official-nav2 --official-path-phases --live-person-range` in source-pinned public workflow. 출판 새 SHA 결과 대기, 그 전 PASS 주장 금지.

## 검증·미검증 및 다음
- L0 새 HEAD pending; 실제 Gazebo new far/stop ROI two distinct actual VALID + UNKNOWN pending.
- G07 strict Moving HOLD, CM 공식 내부 수신 주기·Guard age NOT_VERIFIED, Owner WSLg 픽셀 NOT_RUN, 본 NO_GOAL 교육 MVP ACCEPTED=NO.
- Student PR #43 / Instructor PR #212 / Public #166 main 병합 미승인, NO. 원본 증거 CI 보존 7일.
- 동일 오류 현장에서 단순 재시도 금지. 새 RGB/Depth ROI 원본에서 최초 거리 증가 원인 분석한 뒤에만 새 최소 패치를 정한다.
