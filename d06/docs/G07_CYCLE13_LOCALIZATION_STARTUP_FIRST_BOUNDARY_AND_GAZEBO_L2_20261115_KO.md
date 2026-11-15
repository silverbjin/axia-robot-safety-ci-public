# AXIA G07 Cycle 13 — 첫 LOCALIZATION_START 실패 분류 및 실제 Gazebo 시연 결과

- 작성일: 2026-11-15 / 교육용 RED→GREEN→REFACTOR→REVIEW→COMMIT 근거
- **총괄 판정: PUBLIC SEALED L0 GREEN 33개, 실제 GUI Gazebo L2 시연 범위 PASS, 120ms 출고 여유 FAIL, WSL2 L3 NOT_RUN, AXIA_MVP_DEMO_ACCEPTED=HOLD**
- Instructor 후보 브랜치: `fix/g07-field-cm-delivery-cpu-headroom-20261115`, SHA `b0b8f202aa5d671f8739dd2e926d107f83918795` (비공개 유지)
- Public runner: `release/p2-g06-cm-ttl-20261110`, Gazebo workflow SHA `80d637ad00237a16a40142c7dd955c0809c069c9` (main 미병합)
- RED [Run 43724244298](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43724244298); GREEN [Run 43724426509](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43724426509); 실제 L2 [Run 43724525115](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43724525115).

## 1. 최초 실패 및 RED 경계

선행 Cycle12 실제 L2 [43721027380](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43721027380)에서 **Goal 전** `LOCALIZATION_START: G07_NATIVE_LIFECYCLE_STARTUP_SERVICE_TIMEOUT:request_sent=True`; 후속 `rclpy ... publisher's context is invalid`는 cleanup 예외로서 최초 실패가 아니다. 원래 `tools/p4_g07_startup_failure.py`는 NAVIGATION_START만 분류해 `FIRST_STARTUP_GATE_UNVERIFIED`라고 잘못 보고했다.

신규 `tests/unit/test_g07_cycle13_first_localization_startup_20261115.py` 4개 계약: 서비스 요청 전송 후 응답 타임아웃은 `LOCALIZATION_STARTUP_REQUEST_SENT_ACK_TIMEOUT`; 잘못된/없는 원본은 정확한 타임아웃이라고 주장하지 않음; 기존 NAVIGATION 최초 실패 유지; 공개 CI 실제 Goal 허가 모드에서도 PRE_GOAL 실패 시에만 읽기 전용 Native ACK/state 검사 후 재시도 없이 차단.

RED Run 43724244298 출력: `TEST_FIRST_LOCALIZATION_RC=1`; 신규 분류·CI 실제 Goal 모드 read-only probe 기대 2건 FAIL. 같은 실행에서 `TEST_STOP_CM_ALIGNMENT_RC=1`은 CI workflow 출력 파일명 치환 실수(`>sealed-test-7.log sealed-test-8.log`)로 발생했으며 **runtime 코드 회귀는 아님**. Runner 오타를 수정한 원본 변경을 보존하고 기존 시험이 다시 통과하는지 검증함.

## 2. GREEN·리뷰 및 커밋

- `tools/p4_g07_startup_failure.py`: 최초 LOCALIZATION_START 식별, 원본 `localization_start.native.json`의 manager/command/status/request_sent/elapsed 검증, 불확실성은 명시하고 NAVIGATION/Goal은 하위 미검증 유지. Owner에는 CI acceptance 권한이 없음.
- `scripts/p2_no_goal_smoke_ci.sh`: CI에서 **실제 GUI Goal 허가 환경이지만 아직 Goal은 발행하지 않은 실패**에 한해 원본 Native receipt와 map_server/amcl 상태 두 개만 bounded `ros2 lifecycle get`으로 수집. Goal 재전송·restart·Guard TTL 우회·Owner에서 동일 CI용 probe 실행 없음.
- `.github/workflows/axia-g07-field-sealed-authorized-l0.yml`: 기존 Cycle12 테스트 로그 redirect 구문 수정; 신규 Cycle13 테스트 분리, 모든 RC 합산.
- GREEN Run 43724426509: `TEST_FIRST_LOCALIZATION_RC=0; TEST_STOP_CM_ALIGNMENT_RC=0; BASH_CI_RC=0; BASH_OWNER_RC=0; COMPILE_RC=0`. 기존 29개+신규 4개 = **33/33 테스트 PASS**. 이 L0는 ROS/Gazebo Goal 미포함.
- 검토: 실제 Goal 시도 횟수 추가하지 않고, 기존 원본 보존 및 변화한 진단기와 동일 검증 출처 사용. `main` 미병합.

## 3. 실제 Gazebo L2 — 시연 동작은 성공, 출고 여유 미달

Run `43724525115`, ROS 2 Jazzy / Gazebo Harmonic / 공식 Nav2 / 공식 TB3 Waffle, 실제 Xvfb Gazebo GUI/RViz 외부 sidecar, 단일 실제 SIM Goal.

- 첫 LOCALIZATION_START 기동 장애 **이 실행에서는 재현되지 않음**; 기동 코드 변경 자체가 안정성을 증명한 것은 아님.
- 실제 Scan 거리 CLEAR `2.036163m`, SLOW `0.747387m`, STOP `0.397741m`.
- Native 물리 STOP RPC 시작 이전 CM fresh alignment `external_cm_age_sec=0.004920466`, 실제 신호 사용/가짜 Twist 없음.
- STOP 구간 Guard latch 없음; Odom dwell·액션 정지 및 Nav2 정확 UUID `ffbfb9c2bae14ff09e8498830b019431` `CANCELED`, CM exit0 / Shutdown clean.
- S02 native ECM 실제 동일 Goal positive contact = `0`, `CI_S02_SAME_GOAL_NATIVE_CONTACT_ZERO_CANDIDATE`. 이는 인증된 E-Stop이 아니며 Owner L3 증거도 아님.
- 7채널 최대 Observer interarrival (ms): source `121.442912`, supervisor `121.483616`, cm `143.508424`, guard `111.280435`, scan `195.080675`, odom `143.554544`, clock `106.145404`.
- 원래 Goal L2 `P2_L2_SMOKE_RC=0`, `AXIA_G07_CI_REAL_HARMONIC_NAV2_MOVING_GOAL_CLEAR_SLOW_STOP_L2_PASS_OWNER_L3_NOT_RUN`.
- **그러나 120ms 별도 출고 여유 게이트 실패**: `AssertionError: FIELD_CI_L2_PASS_LOW_MARGIN_OWNER_NOT_READY`; 실측 CM `143.508ms <150ms HARD` 이지만 `>120ms RELEASE`. 따라서 전체 Actions workflow `FAILURE`, Owner 배포 금지.

## 4. 다음 최초 경계 — Cycle 14 지침

첫 재현된 안전 latch는 Cycle12 이전과 동일 계층의 CM TTL 초과였으나, 이번 같은 SHA의 정상 STOP 동작에서도 **source/upstream 121.4ms, CM 143.5ms**가 함께 증가했다. `CM`을 120ms 이하로 만들려면, upstream 자체의 실제 121ms 공백을 무시하고 CM CPU/TF/Guard TTL만 변경해서는 안 된다.

새 센서/새 노드/소스 대규모 변경 금지. **기존 14토픽/실제 RMW MessageInfo를 사용하여 가장 큰 Supervisor 명령 간격과 CM 간격이 같은 창인지, 소스가 먼저 멈췄는지**를 우선 가려내는 순수 분석기 RED 테스트 1개를 추가. 첫 경계에 한정된 최소 수정만 허용. **120ms 출고 여유와 150ms 안전 HARD, 300ms 센서/500ms Supervisor TTL 불변**.

동일 원본을 반복 구동해 유리한 단발 숫자를 골라 PASS로 승격하지 말 것. 추가 안전 계층의 타이밍 교차검증 전에 전체 시연 안정성 확인 금지. Owner WSLg 실제 시연은 아직 미검증.

**Owner 원샷 NOT_RELEASED / AXIA_MVP_DEMO_ACCEPTED=HOLD.** 기존 Owner evidence / 1회 시도 lock 삭제 금지, 강사 솔루션 공개 금지, student/main 병합 승인 전 금지.
