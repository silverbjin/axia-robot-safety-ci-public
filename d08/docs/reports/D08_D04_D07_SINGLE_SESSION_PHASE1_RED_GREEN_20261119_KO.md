# AXIA D08 D04~D07 단일 Gazebo Live 통합 — Phase 1 재사용·RED/GREEN 보고서

기준: 2026-11-19 KST. **NO_GOAL D08와 G07 Moving Goal의 별개 증거를 한 시연으로 합산 금지**. 보고 범위는 Source Adapter L0/공식 소스 L1만이며 실제 통합 Gazebo L2, Owner WSL2 L3는 아직 HOLD입니다.

## 1. 사용자 승인 목표 및 완료선

- D04: 기존 pinned C++ `yolo_ros`, 실제 Gazebo RGB에서 `DetectionArray`.
- D05: 기존 `d08_live_person_range_session.py`의 실제 RGB-D Depth ROI median 2 VALID + 1 UNKNOWN. UNKNOWN은 CLEAR/이동허가가 아님.
- D06: **G07 소유** Safety Supervisor → 공식 Collision Monitor → Base Guard에서 LiDAR 실제 감속·정지, 150ms 전달·Guard TTL 경계 검증; SW Stop은 인증 E-Stop이 아님.
- D07: **G07 소유** 공식 Nav2 Moving Goal + 기존 D08 official `ComputePathToPose` three-phase replan 관측.
- **단일 Gazebo world/default**, Waffle 1개, 동일 물리 사람형 Collision/Contact Proxy `axia_p2_g07_obstacle`, 단일 ROS_DOMAIN_ID/GZ_PARTITION, 동일 session evidence, 중복 Gazebo/Goal 노드 없음.
- D08 D04/D05는 안전 결정/제어를 하지 않고 read-only 수업 관찰만 수행. YOLO가 CM을 직접 정지시킨다는 오해 금지.
- 기존 Task04 WSL2 최초 실제 Goal: 0.225m 이동, 1.026초 정지 확인, Scan callback 최대 **317.863ms>300ms** 및 별도 bag **311.495ms**. 최종 안전 타이밍 인수 **HOLD**, 단순 오류 코드 2 무시 금지.

## 2. 기존 구현 재사용 조사와 단일 런타임 소유권

| 기존 파일 | 재사용 방법 | 변경 경계 |
|---|---|---|
| Public `d08/harness/d08_live_world.py` | 동일 물리 G07 모델에 사람 Mesh, 640×480 등록 RGBD 추가 | G07 이미 설정된 10Hz LiDAR 보존 명시 opt-in |
| Public `d08/harness/d08_live_person_range_session.py` | D04/D05 두 VALID·UNKNOWN 실제 read-only 측정 | ROS 제어 없음 |
| Public `d08/harness/d08_same_world_replan.py` | D07 공식 `ComputePathToPose` before/intrusion/restored | Nav2 Planner 신설 금지 |
| Student pinned `efff0fb8bf941de74572336d1988dfb0005e11f7` G07 `p2_no_goal_smoke_ci.sh` + `p2_g07_ci_moving_goal.py` | 공식 Nav2+Supervisor+CM+Guard 소유권 및 한 Goal | 별도 Gazebo 금지, 소스 핀 갱신 필요 |
| Student `p2_l3_world_overlay.py`, `d07_h01_scene_broadcaster_overlay.py`, `p2_g07_demo_lidar_overlay.py` | Contact+GUI Scene+10Hz 공식 Waffle 원본 overlay 순서 재사용 | 원본 /opt/ros, safety TTL 미변경 |

**선택:** G07의 주행 안전 런타임이 Gazebo 서버와 Goal을 소유. D08은 세션 시작 전 물리 World/카메라 Source Adapter를 만들고, 주행 승인 전에 실제 read-only YOLO/D05/Path 구간을 관찰한다. 원본 G07 안전 계층은 수정하지 않는다.

## 3. 개발·테스트 사이클

1. **RED** 공개 CI [#44476418499](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44476418499), 정확한 SHA `a6898057dd5f8d2553183704daebdce5ad6b44b1`. 신규 테스트가 `ModuleNotFoundError: No module named 'd08_g07_same_world_adapter'`로 실패. 기존 Gazebo 독립 L2 중복 실행은 scope 밖으로 SKIP.
2. **GREEN** 공개 CI [#44476928065](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44476928065), SHA `8539b101db1380baa52bdf4a985f49e03353ba84`: **226 passed in 1.20s**; no real Gazebo.
3. 공식 원본 Jazzy/G07 소스 결합 CI 추가 후 기존 `test_same_exact_source_sha_in_public_pr_ci_and_owner_checkout`가 4개 job checkout을 가정해 **1 failed, 225 passed**, [#44477591155](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44477591155). 새 job도 exact SHA가 필요하므로 기대치를 **5개 exact-head checkout**으로 엄격하게 변경; 검사를 제거하거나 느슨하게 완화하지 않음.
4. 이 수정의 공개 CI [#44477735046](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44477735046)은 L0 **226/226 PASS**, 공식 `g07-official-source-sdf-adapter-l1` 별도 job으로 검증. 해당 job 최종 결론은 run 원본 확인 후 별도 갱신.
5. 테스트는 G07 5Hz/8Hz/12Hz를 D08 overlay가 자동 변경하지 못하도록 차단, 단일 World·Collision·Contact·기존 G07 witness, 등록 RGBD, 소스 불변성을 확인. ROS/Gazebo 실행·CM 내부 수신·Goal 이동 성공을 이 단계에서 주장하지 않음.

## 4. 실제 수정 경로

- `d08/harness/d08_live_world.py`: 기본 D08 5Hz→10Hz 조정은 유지, `g07_lidar_preconfigured=True`일 때 **이미 10Hz인 원본 G07 sensor를 그대로 보존**, 그 외 구성 거절.
- `d08/harness/d08_g07_same_world_adapter.py`: 신규 공용 Source Adapter/CLI, G07 물리 person/Contact·10Hz source 검증, 재사용 카메라 Mesh overlay, SHA custody, 정적/실시간 증거 구분, 실패시 rc=2.
- `d08/tests/test_d08_g07_same_world_adapter.py`: 작은 핵심 RED/GREEN 테스트 5개.
- `d08/tests/test_d08_task04_exact_sha_and_failclosed.py`: 새 CI job 포함 정확한 checkout 5곳 증명.
- `.github/workflows/d08-main-no-goal-real-gazebo-l2.yml`: 기존 L0 226 테스트, 실제 공식 xacro/Student source만 검사하는 별도 job. 이 PR에서는 **완료된 독립 Gazebo job을 재검증하지 않음**, 진짜 Moving E2E L2는 별도 선행 요건.
- Public Draft [PR #189](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/189): `feat/d08-d04-d07-single-session-20261119`, base `fix/d08-owner-rmw-one-shot-20261119`, **main 미병합**.

### G07 원본 Source Adapter 명령 구조 (ROS/Gazebo 주행 명령 아님)

```bash
python3 d08/harness/d08_g07_same_world_adapter.py \
  --world "$G07_SCENE_WORLD_XACRO" \
  --robot "$G07_10HZ_WAFFLE_XACRO" \
  --actor "$PINNED_HUMAN_DAE" \
  --out "$SESSION_ROOT/d08_unified" \
  --student-sha "$PINNED_G07_STUDENT_SHA"
```

출력 `D08_G07_SINGLE_WORLD_STATIC_OVERLAY_READY_NOT_GAZEBO_NO_GOAL`은 SDF Source Adapter 성공일 뿐 ROS2 노드·센서·Nav2 안전 동작 PASS가 아닙니다.

## 5. 다음 두 작업만 남긴다 (MVP, 개발 범위 제한)

1. G07 Student 시나리오의 existing `ros2 launch`에 정확한 D08 overlay World/Robot SDF 2개를 명시적으로 전달한다. 두 번째 Gazebo 실행 금지. 원래 G07 소스·안전 소유권/Goal 승인 변조 금지.
2. 같은 G07 Launch 내부에서 original pinned YOLO+D05 실제 상태·UNKNOWN, 공식 Nav2 three-phase 경로, **그 다음** G07 한 Moving Goal CLEAR→SLOW→STOP·Goal terminal·CM/Guard 주기를 연결하고, 동일 ROS_DOMAIN_ID/GZ_PARTITION 및 native event timeline 한 묶음으로 증명한다. 기존 D08 500ms 독립 한계가 아닌 G07 실제 주행 300ms Scan 상한과 CM/Guard 150ms 등 원래 계약을 유지한다.

통합 실행 이전에는 `D08_SINGLE_SESSION_MOVING_E2E_ACCEPTED=HOLD`. Public CI 실제 Gazebo L2에서 위 통합이 검증된 뒤에만 Owner WSL2 원샷을 배포. WSL2 실패는 최초 안전 전이/타이밍 위반을 PUBLIC CI RED로 수용, 현장 반복 재시도 금지. 강사 정답은 비공개, Student TODO 별도 유지. main 병합 사용자 승인 전 금지.

검증 수준: 현재 Public **L0 GREEN** / 기존 개별 D08 NO_GOAL L2 및 G07 moving L2는 재사용 자료 / NEW combined source L1 원본 CI 확인중 / **combined Gazebo L2 NOT_RUN**, **Owner WSL2 L3 NOT_RUN** / real robot, hardware certified E-Stop 제외.
