# AXIA G07 Task04 Owner n7 — CM·Guard 엄격 인수 실패 최초 경계 / WSL2 CLOCK_REALTIME 진단 (2026-11-19)

## 0. 이 보고서의 범위

- 공개 CI 저장소: `silverbjin/axia-robot-safety-ci-public`, 브랜치 `fix/g07-task04-owner-timing-evidence-20261119`
- Student 공개 저장소: `silverbjin/axia-robot-safety-student`, 브랜치 `fix/g07-task04-owner-timing-evidence-20261119`
- 원본 Owner 입력: `owner-moving-n7FChbnn.tar.gz` SHA256 `bdf1514bf79d79d3d99b80564d1ce4ea3aebbbc759ea1a416e0371412cdc2a91`
- 원본 진단 ZIP: SHA256 `c42c4bc15d8b1fa291291d9042da2c3399deaec20e11b55e6a72ab677ab38c6c`
- 이 문서는 비식별 수치와 코드 근거만 포함하며 원본 rosbag, 개인 경로, 컴퓨터 이름 및 전체 이벤트를 공개 저장소에 복사하지 않는다.
- 목표: 기존 주행·정지·목표 취소 성공을 보존하고 **최초 엄격 안전 증거 실패**만 좁힌다. Goal/CM/Guard/TTL 변경 및 main 병합 금지.

## 1. 현장 실측 최초 실패

```text
FIRST_FAILURE=NATIVE_NUMERICAL_REVIEW_BLOCKED
NUMERIC_FIRST_FAILURE=cm_source_and_observer_120ms
CM_STATUS=TASK02_ACTUAL_GOAL_OR_GUARD_UNVERIFIED_HOLD
GUARD_INTERNAL_CM_AGE_MAX_MS=null
OWNER_L3=HOLD
```

실제 동일 Owner 세션은 PREGOAL front=1.4146229m, side=2.5235329m로 CLEAR, 실제 odom 이동 0.2237095765m, 정지 dwell=1.0341270040s, 충돌=0, 목표 UUID `b79512e8b2d84f1cad6c62aa5bae608b` terminal CANCELED, Nav/Loc ACK 및 Collision Monitor 종료 clean, 14개 rosbag 토픽과 정확한 SHA256. 21개의 엄격 검사 중 19개만 성공. CM/Guard callbacks 각각 최대 92.21ms/91.85ms, Scan 197.12ms, Odom 133.12ms, Clock 70.09ms는 별도 host monotonic Observer 범위의 수치. 이 결과로 **CM RMW source 120ms와 Guard 내부 150ms를 자동 PASS 처리할 수는 없다.**

## 2. 원인 A — CI 전용 상태 검사와 Owner 후보의 계약 불일치

`d06/diagnostic/g07_task02_strict_gate.py::assess()`는 `CI_GAZEBO_MOVING_GOAL_CANDIDATE`만 받아 실제 RMW 메시지를 계산하기 전 반환했다. 실제 Owner 실행은 `NUMERICAL_CANDIDATE`, `shared_execution_mode=owner`, `owner_authority_verified=true`, `common_g07_ci_oracle_status=CI_GAZEBO_MOVING_GOAL_CANDIDATE`이다.

수정: 네 조건을 전부 검증한 Owner만 같은 엄격 검증을 수행하게 한다. CI/Owner 판정 이름은 구별하고, `owner_wsl2_accepted=false` 및 `certified_estop=false` 유지.

## 3. 원인 B — Guard 내부 age 필드의 CI 전용 게이트

`ros2_ws/src/axia_safety_supervisor/axia_safety_supervisor/p2_base_guard_node.py`는 `GITHUB_ACTIONS=true`, `AXIA_G07_TASK03_FORMAL_CI=1`인 경우에만 기존 20Hz 상태 토픽에 `cm_age_sec`, `supervisor_age_sec`, `guard_ever_moved`를 덧붙였다. Owner는 고의로 두 환경변수를 제거하므로 실제 Guard 상태 이벤트 490개 모두 해당 필드가 없다.

수정: 기존 CI 조건 OR 명시적 `AXIA_P0_SIM_ONLY=1`, `AXIA_G07_TASK04_OWNER_MOVING_L3=1`, `AXIA_G07_OWNER_STARTUP_PARITY=1`, `GITHUB_ACTIONS!=true`로 제한한다. 읽기 전용 필드 추가만 수행하며 Guard State.step(), 정지/취소, CM_TTL_SEC=0.15, ROS QoS는 그대로.

## 4. 원인 C — RMW 송신·수신의 wall-clock 점프와 monotonic 전달 구간 혼동

실제 `pre_guard` 연속 메시지 sequence **483→484**:
- RMW 송신 시각 차이: **2964.068703ms**
- RMW 수신 시각 차이: **2964.056604ms**
- 독립 Observer `time.monotonic()` 콜백 간격: **38.417685ms**
- 동일 양의 wall-clock 오프셋 증가, sequence 정상 +1, RMW 송신-수신 나이: 약 0.242ms→0.230ms
- 수정 전 원본 strict gate가 Owner 상태 허용 후 실행된다면 이 pair는 120ms 초과로 실패했을 것.

14-topic rosbag의 `/clock` SQLite 수신 timestamp에는 약 2.939/2.935/4.321/2.946/2.936초 gap이 있고, 각 양옆 CDR ROS `Clock` 값은 약 3ms만 증가했다. 이는 시스템 시계 오프셋 이동과 부합하지만 **게스트 내부에서 VM 전체 일시정지/외부 Windows 호스트 시간 공백을 확정 배제할 수 없다.** 따라서 원본 wall-clock 간격을 임의 삭제하거나 일반 source 120ms pass로 보고하지 않는다.

수정: Owner에서만 (1) RMW source 및 received 두 시계에 공통 큰 점프, (2) 양쪽 source→received delay 각각 10ms 이내 및 동일 상대 변화 2ms 이내, (3) 단조 증가, (4) publication seq 정확히 +1, (5) 별도 `time.monotonic()` Observer 구간 120ms 이내를 **동시에** 만족하면 그 pair를 `OWNER_MONOTONIC_CLOCK_STEP_NUMERICAL_CANDIDATE`로 표기하며 raw 2964ms와 보정된 delivery envelope를 둘 다 보존한다. 이때에도 기존 CM 120ms·Guard 150ms·Scan 300ms 숫자는 변경하지 않으며 읽기 전용 판정만 한다.

**중요 한계**: 이 판정은 게스트 monotonic 기준의 한정된 수치 후보일 뿐 실제 Windows 호스트에서 일시정지가 없었다는 보증이나 안전 인증이 아니다. `host_external_clock_verified=false`·`owner_wsl2_accepted=false`를 보존한다. 실제 151ms callback 지연, sequence 유실, 불일치하는 RMW timestamps, Owner 권한 누락은 HOLD.

## 5. RED→GREEN 검증 증거

- 공개 RED [#44430334562](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44430334562): Owner status & common timestamp step 검증 실패 2개.
- 공개 중간 RED [#44430603061](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44430603061): Public strict 관련 검증 GREEN, Student guard Owner 계측 함수 및 scope 부재 FAIL.
- 공개 L0 GREEN [#44430776985](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44430776985): 기존 strict 5개 + 신규 공개 6개 + Student Guard/Review 2개 성공.
- 변경된 CI 검증 코드: `tests/test_g07_task04_owner_n7_timing_regression.py`; Student `tools/test_g07_task04_owner_n7_timing_regression.py`. 원본 사용자 데이터는 public fixture에서 숫자·구조만 비식별 복제.
- 실제 native Gazebo/Nav2 Moving Goal+Gazebo/RViz L2는 별도 공개 CI가 성공할 때에만 통합 GREEN으로 판정. 독립 Owner WSL2 L3 재인수는 아직 수행하지 않았다.

## 6. 미검증과 릴리스 조건

```ini
OWNER_N7_ORIGINAL_GAZEBO_GOAL_MOTION=NUMERICAL_CANDIDATE_19_21
OWNER_N7_GUARD_NATIVE_150MS=UNVERIFIED_NOT_PUBLISHED
OWNER_N7_RMW_SOURCE_RAW_WALL_GAP_MS=2964.068703
PUBLIC_L0_OWNER_CLOCK_PARITY=PASS
PUBLIC_L2_FINAL_NEW_SOURCE=NOT_RECORDED_IN_THIS_REPORT
OWNER_WSL2_NEW_L3=NOT_RUN
CERTIFIED_ESTOP=false
AXIA_MVP_DEMO_ACCEPTED=HOLD
MAIN_MERGED=false
```

Main 병합은 별도 승인 전 금지. Owner는 새 L2 성공 및 정확한 Student/CI commit pin 이후 한 번만 실행하며, 실패 시 현장 재시작 대신 첫 Guard 나이와 최초 wall/steady clock divergence를 공개 회귀 테스트에 재편입한다.

## 외부 기술 참고
- Microsoft WSL host-side guest freeze / wall vs monotonic 관찰: https://github.com/microsoft/WSL/issues/40745
- Microsoft WSL 시계 불연속 문제: https://github.com/microsoft/WSL/issues/11790
- ROS 2 RMW source / receive timestamps: https://github.com/ros2/rosbag2/issues/2023
