# AXIA G07 Cycle 12 — Fresh CM STOP-RPC 정렬과 사전 기동 실패

- 날짜: 2026-11-15 / 시뮬레이션 전용 / 교육용 증거와 검증 범위를 분리
- **판정: L0 GREEN 29/29, 실제 Gazebo L2 PRE-GOAL FAIL, STOP 정렬 L2 미검증, Owner WSL2 NOT_RUN, AXIA_MVP_DEMO_ACCEPTED=HOLD.**
- Instructor 소스: `baf527c16522d4b689d2b270bbf3bd858908e9e5`.
- Public L0 RED: [Run 43720679620](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43720679620), GREEN: [Run 43720955072](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43720955072), 실제 Gazebo L2: [Run 43721027380](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43721027380) FAIL, public workflow SHA `8386b8ebfe9a331d0f4b12391eeda79dab1a042f`.

## 1. 최초 원본 실패와 최소 가설

이전 Run `43719502735`의 첫 위반은 물리 STOP RPC 약 `109.766ms`와 STOP 직전 실제 CM age `47.897961ms`가 겹친 `161.609079ms` CM RMW 발행 공백, Guard 내부 `155.829854ms >150ms`. TF .02s로 좁혀도 재현돼 가설을 기각하고 .05s로 복구했다.

새 가설: 기존 Observer가 실제 `/cmd_vel_pre_guard`를 수신한 직후에만 한 번의 Gazebo 동적 물리 장애물 `set_pose` RPC를 발행하면, 동일 RPC 구간의 150ms CM TTL 소진을 줄일 수 있다. 새 발행자/타이머/가짜 LaserScan 없이 실행 시점만 정렬한다.

## 2. RED→GREEN→REFACTOR→REVIEW→COMMIT

- `tools/p2_g07_ci_stop_stage.py`: `wait_for_fresh_cm_before_native_stop` 추가. 같은 Goal UUID의 EXECUTING, Guard latch false, **기존 실측 CM 수신시각이 이후로 진전되고 age <=8ms**, 실제 Scan/Odom/Clock/Supervisor 입력의 신선도를 검증. 제한 시간 0.45s를 초과하면 STOP RPC 자체 미발행. 안전 TTL은 변경하지 않음.
- `tools/p2_g07_ci_moving_goal.py`: 동일 CI/Owner 공유 Goal runner에서 유일한 native STOP RPC **이전**에 해당 검사 호출. 기존 명령·안전 계층 불변.
- `tests/unit/test_g07_cycle12_stop_rpc_cm_fresh_alignment_20261115.py`: stale/no CM/Guard latch/Goal terminal/UUID mismatch/시간초과 차단과 실제 fresh CM의 통과 검사.
- RED `43720679620`: `TEST_STOP_CM_ALIGNMENT_RC=1`, 4 신규 테스트 실패/미구현. GREEN `43720955072`: `TEST_STOP_CM_ALIGNMENT_RC=0`, 기존 회귀 포함 29 테스트 PASS, CI/Owner bash·Python 검사 PASS.
- 변경 코드가 실제 CM 120ms 여유나 WSLg 안정성을 확보했는지는 GREEN으로 **입증할 수 없음**.

## 3. 실제 L2 실행 — 최초 실패 지점 확인

Run `43721027380`은 실제 ROS 2 Jazzy, Gazebo Harmonic, 공식 Nav2, GUI Xvfb, S02 native Contact 계측기의 준비 과정까지 진입했으나 **Goal 이전**에:

```text
P2_STAGED_NO_GOAL_BLOCKED: LOCALIZATION_START: G07_NATIVE_LIFECYCLE_STARTUP_SERVICE_TIMEOUT:request_sent=True
FIRST_G07_STARTUP_BOUNDARY_CI_PREGOAL_NO_RETRY
AXIA_P4_G07_FIRST_G07_STARTUP_BOUNDARY {"first_failure":"FIRST_STARTUP_GATE_UNVERIFIED", ...}
P2_L2_SMOKE_RC=3
AXIA_G07_CI_MOVING_GOAL_REAL_GAZEBO_BLOCKED
```

기존 분류기는 `NAVIGATION_START`만 처리해 실제 최초 실패 `LOCALIZATION_START`를 `FIRST_STARTUP_GATE_UNVERIFIED`로 잘못 낮춰서 보고함. `rclpy._rclpy_pybind11.RCLError: publisher's context is invalid`는 **cleanup 도중 발생한 후속 오류**, 최초 실패가 아니다.

- `startup_verdict.localization_start.native.json`는 Native STARTUP `SERVICE_TIMEOUT` / `request_sent=True`를 보존한다. 증거상 정확히 Nav2 localization 매니저 자체가 응답하지 않았는지, 응답 전달이 누락됐는지는 미규명.
- 실제 Goal `NOT_SENT`; STOP RPC 정렬 로직 `NOT_REACHED`; 7채널 실측·S02·exact Cancel·Shutdown 인수 증거 `UNVERIFIED`.
- 동일 오류를 Owner WSL2에서 재시도하거나, 무조건 CI 재시도해서 PASS로 승격하면 안 됨.

## 4. Cycle 13에 넘기는 최소 회귀

1. `p4_g07_startup_failure.classify()`에서 `LOCALIZATION_START: SERVICE_TIMEOUT/request_sent=True`를 최초 실패로 명확히 분류, 원래 manager/command/callback/readback 구간을 잘못 추측하지 않음.
2. 새 public CI 실제 Goal 모드에서도 **Goal 이전에 실패한 경우에만** 정확한 Native localization receipt 및 기존 launch 원본으로 진단. 기존 no-Goal-only 툴을 위험하게 우회하지 않는다.
3. RED→GREEN sealed L0 후 동일 private SHA로 **실제 GUI Gazebo L2 1회**. startup이 다시 막히면 해당 최초 failure를 CI 원본으로 좁히고 무작정 현장 재주행 금지.
4. Goal에 도달하면 기존 CM 150ms TTL / 권고 운영 120ms / 7채널 / Native Contact 0 / exact Cancel / Nav2 shutdown/CM exit0 전부 확인.

## 5. 보존·출고 정책

- Instructor 강사 정답·개인 Owner rosbag 공개 금지, student 독립 TODO 불변.
- Main 병합 사용자 승인 전 금지; 오래된 Owner 실패 예약 디렉터리/원본 삭제 금지.
- CI Xvfb != Owner WSLg, CI PASS != Owner L3 PASS.
- 인증된 하드웨어 E-Stop 아님. `AXIA_MVP_DEMO_ACCEPTED=HOLD`.
