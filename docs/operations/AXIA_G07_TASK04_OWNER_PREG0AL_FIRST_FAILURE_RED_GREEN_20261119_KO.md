# AXIA G07 Task04 — Owner PREGOAL 최초 실패: 증거 보존 RED→GREEN 및 Gazebo 초기화 진단

- 작성일: 2026-11-19 (KST)
- 공개 CI: `silverbjin/axia-robot-safety-ci-public` PR [#169](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/169), 브랜치 `fix/g07-task04-owner-wsl2-public-pregate-20261118`
- Student: `silverbjin/axia-robot-safety-student` PR [#46](https://github.com/silverbjin/axia-robot-safety-student/pull/46), 브랜치 `fix/g07-task03-public-proof-20261118`
- 현재 수정된 Student 소스 SHA: `ef6ffe58ddacb89ed37b225279f8e86453cf82b7`
- 종전 성공 보존: 실제 Task03 Goal [#44223320904](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44223320904), Task04 Moving+GUI [#44268914763](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44268914763) — *다른 소스 SHA 성공을 현재 SHA의 L2 PASS로 대체하지 않음*
- 소유자 제출 tar SHA256(사용자 제공, 이번 작업 환경에서 원본 재계산 못함): `bda0fa30ed2c0956811d9cfef9f3197e7a564427d9656e1a27d39b4dc6602c0f`
- 최종 판정: **HOLD** (실제 현장 L3 및 전체 계층 TTL 미검증)

## 1. 증거와 최초 경계

현장 원본 제공 수치: `/safety/scan` 372개, 정면 중앙값 0.527m, 측면 0.630m, 움직임/Goal 없음, 30~35 sim 초 지속. 최초 예외는 `OWNER_PREGOAL_NOT_CLEAR_BEFORE_FIXTURE`; `NATIVE_RUNNER_FAILED_REVIEW_RAW`는 후속 예외다. 해당 거리 값은 실제 수신 데이터의 사용자 검증 결과로서 보존하나, 이번 환경에 tar 원본이 없어 자체 rosbag 재생·SHA 재검증은 **NOT_VERIFIED**다.

소스 경계: `block_B/day07/h01_runtime/tools/p2_g07_owner_pregoal_l2.py`의 정면 `>0.75` 및 측면 `>1.20` 초기 조건을 만족하지 않아, 기존 `admit_preloaded_fixture`의 Gazebo `set_pose`와 Nav2 Goal **이전**에 멈춘다. 안전 정지는 정상적인 fail-closed 동작이며 이 조건은 변경하지 않았다.

World overlay `p2_l3_world_overlay.py`은 원통을 최초 `(-0.58,-0.50)`에 삽입한다. 공식 Waffle Spawn 계약은 `(-2.00,-0.50,yaw=0)`이다. 두 중심 간 거리는 **1.42m**로 0.527m의 설명이 되지 않는다. 공식 `tb3_sandbox`에는 추가 `turtlebot3_world`의 고정 원통 여러 개와 벽 메시가 있으므로 해당 원통만 근거로 좌표오류를 확정할 수 없다. 실제 Gazebo 엔티티 Pose, ROS LaserScan의 frame/angle, 두 topic의 publisher/QoS와 DDS 격리를 같은 세션에서 대조해야 한다.

추가로 `DEMO_WORLD_POSE=(-1.81,0.25)`, `BEARING_RAD=atan2(0.75,0.19)`가 기존 소스에 존재하지만, 현장 측면 0.630m이 이전 배치의 잔류인지 다른 물체인지는 확인되지 않았다. **원인 가설로만 보존**한다.

## 2. L0 RED→GREEN #1 — 사전검사 예외 직전 측정값 유실

- RED 테스트 커밋 `9dbbb742ce39bc2533cd68879496f201706e97be`, CI 연결 `7eb071d4dbdf5bc8a2fb7f35c1a580250a603504`
- RED 실제 CI [#44339636294](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44339636294): `ImportError: cannot import name 'build_pregoal_baseline'`
- GREEN Student `23c0598e51c38eef4144f97f73e125504934f3a9`, 공개 CI 핀 `a537839013cd7043d3c1bd4c867440f5e6cf5eeb`
- GREEN 실제 CI [#44340065833](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44340065833): dedicated L0 성공
- 수정을 통한 관측값: 최초 비교 전에 `pregoal_baseline.json`에 `status`, `first_failure`, `front_m`, `side_m`, 요구 임계값, `goal_sent=false` 등을 기록. 실제 미확인 World Pose는 `null`로 기록.

## 3. L0 RED→GREEN #2 — 원본 엔티티 좌표/데이터 출처 추적

- RED CI 테스트 변경 `2f3221822198bd17ea7c6c8ef230d8d51dfaea9d`
- RED 실제 CI [#44340881230](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44340881230): `parse_gz_model_pose` 미구현 import 오류
- GREEN Student `ef6ffe58ddacb89ed37b225279f8e86453cf82b7`, CI 고정 `6c7978ca219c1c8ec64efa3da58194ccb840f4aa`
- GREEN 실제 CI [#44341275422](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44341275422) dedicated L0 성공; 범용 public Python [#44341292987](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44341292987) 성공
- 최소 수정: 실제 `/safety/scan`의 frame_id, source stamp, host 수신시각, 실제 LaserScan 각도 범위; 실제 `/scan` 별도 수신 값 및 두 topic의 publisher GID/QoS를 보존한다. 단, ROS graph 조회만으로 원본 물체를 특정했다고 주장하지 않는다.
- **초기 BLOCKED 상태에서만** 최대 5초씩 `gz model -m ... --pose` 읽기 전용 CLI로 Gazebo Waffle과 원통 좌표를 시도하며, 응답 부재/형식 불명은 `null`. 원본 명령/센서/안전 로직은 건드리지 않았다.
- `tests/test_g07_task04_pregoal_first_failure_contract.py`는 현장 반올림 중앙값 L0 입력만 재현하며 ROS/Gazebo L2가 아니다.

## 4. 새 실제 Gazebo L2 — 최초 초기화 실패와 최소 수리

- 새 공개 no-Goal 워크플로: `.github/workflows/axia-g07-task04-pregoal-physical-l2-20261119.yml` (최초 커밋 `3ee6123bb79e7024d76b8da199102285695a0d8e`)
- 실제 L2 [#44341901545](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44341901545): `CLOCK_READY: CLOCK_MISSING`; LiDAR 이전 fail, Goal 0
- 진단 증거 확대 커밋 `c9888b6dd592db8b7f261282489c83c815f4ca4a`, 실제 L2 [#44342786005](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44342786005): `launch.log` **첫 오류** `G07_TASK02_SIMPLE_TF_SIM_ONLY_AUTHORITY_DENIED`, 다음 `/tmp/nav2_m_*.sdf` 파일 부재, 후속 `CLOCK_MISSING`. 이 오류의 최초 원인은 실제 현장 근거리 장애물 오류와 **별개**다.
- 원인 확정 범위: 새 no-Goal 워크플로가 Moving 전용 Simple TF 권한 플래그를 실수로 포함했다. `AXIA_G07_TASK02_SIMPLE_TF_CANDIDATE` 플래그를 **no-Goal 워크플로에서만 제거**: `594de36540ba8808cde55e5471a6be5370eb9c26`.
- 이어진 `/tmp/nav2_m_*.sdf` 임시 World 파일 부재가 위 launch 예외의 후속인지 별도 Gazebo start 순서 경쟁인지 아직 분리되지 않았다. 그럴듯한 원인만으로 World 또는 TTL을 임의 수정하지 않는다.
- 수정 후 실제 L2: [#44343312599](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44343312599) **completed/success**, 실제 runner `rc=0`.
- 해당 단일 실제 센서 관측: `status=CLEAR`, `first_failure=NONE`, `/safety/scan frame_id=base_scan`, sim stamp `38.802`, `front_m=1.4095721244812012`, `side_m=2.5160880088806152`, Goal 0. `P2_G07_OWNER_PREGOAL_L2_READY_NO_GOAL`와 preloaded set_pose ACK 후 LiDAR 2개 검증에 대한 기존 runner 결과는 성공. 이 수치는 원본 현장 0.527/0.630m와 **불일치**함. 해당 사실은 현장 원인 규명 **미완료**로 분류한다.
- 주의: 해당 baseline의 `raw_scan=null`, `gazebo_robot_world_pose=null`, `initial_obstacle_world_pose=null`. 추가된 읽기 전용 좌표 조회는 초기 BLOCKED에서만 실행하도록 한 상태이므로, 이번 CLEAR 회차는 실제 Gazebo Pose 출처를 증명하지 않는다. 정상/오염 세션 비교를 완료했다고 주장하지 않는다.

## 5. REVIEW / 명령 / 판정

소스 파일:
- Student: `block_B/day07/h01_runtime/tools/p2_g07_owner_pregoal_l2.py`
- CI: `tests/test_g07_task04_pregoal_first_failure_contract.py`
- CI: `.github/workflows/axia-g07-task04-owner-moving-l0-l2-20261118.yml`
- CI: `.github/workflows/axia-g07-task04-pregoal-physical-l2-20261119.yml`

공개 CI 전용 L0 명령(정확한 Student SHA 체크아웃 뒤):
```bash
cd student/block_B/day07/h01_runtime
AXIA_G07_STUDENT_RUNTIME="$PWD" PYTHONDONTWRITEBYTECODE=1 \
  python3 "$GITHUB_WORKSPACE/ci/tests/test_g07_task04_pregoal_first_failure_contract.py" -v
```

보안·품질 리뷰:
- 정면 `>0.75m`, 측면 `>1.20m` 초기 CLEAR 조건 **불변**
- Supervisor/CM/Guard/Scan/Odom/Clock 운영 TTL 및 Zone **불변**
- 공식 Nav2/TB3의 원본 패키지 **불변**
- synthetic ROS LaserScan, 임의 Goal, CI를 Owner TTY로 위장하는 실행 **없음**
- 강사 원본 14-topic SQLite 전체를 공개 CI artifact에 업로드하지 않음
- 공개 CI 성공은 동일 GPU/WSLg/WSL2/원본 물리 인수와 동치 아님
- 전문 E-Stop 인증 **주장 불가**
- **main 미병합** (Owner 승인 전 병합 금지)

## 6. 아직 인수할 수 없는 사항

1. 실제 Gazebo 초기 실제 Waffle/원통 Pose와 각 모델 world frame readback, 현장 0.527/0.630m 출처
2. 실제 `/scan` → `/safety/scan` 헤더와 source stamp 일치 및 DDS 세션 혼입 여부
3. 고정 월드 장애물 중 실제 LiDAR 검출 물체 식별
4. 사용자 현장 3초 Host 기록 공백: Gazebo 물리/Recorder/ROS bridge/DDS/WSL2 scheduling 구분
5. Supervisor→CM→Guard 각 주기, CM/Observer 120ms 및 Guard 150ms, Scan/Odom/Clock 300ms의 **동일 세션** 실제 타이밍
6. 새 Student SHA의 한 번의 실제 Moving Goal+GUI, STOP dwell, 0 contact, 정확 Goal UUID status 5, Lifecycle ACK, Owner GPU L3 원본 검수

```ini
G07_PREG0AL_REAL_CLEAR=PASS_CI_NO_GOAL_ONLY
G07_SENSOR_AND_SAFETY_TTL=NOT_VERIFIED
G07_MOVING_GOAL_GUI_NEW_SHA=NOT_RUN
OWNER_WSL2_L3=HOLD
AXIA_MVP_DEMO_ACCEPTED=HOLD
CERTIFIED_ESTOP=false
MAIN_MERGED=false
```
