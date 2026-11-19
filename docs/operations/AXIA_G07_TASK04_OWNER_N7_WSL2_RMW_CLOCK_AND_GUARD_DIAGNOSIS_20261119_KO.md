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
PUBLIC_L2_FINAL_NEW_SOURCE=PASS_21_OF_21_PUBLIC_CI_ONLY
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

## 7. 최신 공개 CI 통합 재검증 및 Owner 단일 인수 출고

### n7 판정 보존 추가 RED→GREEN
- Student report의 CM120 항목에서 정규화된 송신 간격만 표시하면 S75/n7의 실제 RMW wall-clock 2.964초 step이 최종 Owner 소형 ZIP에 남지 않는다.
- Student `test_g07_task04_owner_n7_timing_regression.py` RED `24bb8511a7550c452d3a13c14463bc9912fa991e`: 공개 [#44433055899](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44433055899)에서 단일 보존 테스트 FAIL.
- Student 최종 **`dcd1299c03bf702712631dc025b868335cadd1c6`**에서 `cm120.source_raw_gap_max_ms`, `clock_step_pairs`, `clock_step_evidence`, `host_external_clock_verified`를 숫자 판정 JSON에 전달. 그에 따라 **기존 Guard/CM 정책은 변경하지 않고 원본 측정 증거만 추가**.
- 공개 [#44433188501](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44433188501) 최종 L0 GREEN: n7 신규 CI 6 / 기존 CM strict 5 / Student Guard·JSON 보존 3, 총 14개 PASS. 일반 Python contracts 및 runner canary도 같은 브랜치에서 성공.

### CI Gazebo 환경 drift와 실제 완전 통합 L2
- 첫 수정 L2 [#44430959362](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44430959362)는 실제 Gazebo 전에 FAIL: 현재 OSRF apt `libgz-transport13-dev=13.7.0`이 설치된 `libgz-transport13=13.6.0`을 13.7로 올려 Owner 공식 패키지 패리티를 깨뜨림.
- 공개 의존성 [#44431621259](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44431621259) 진단 PASS. 원본 컨테이너 13.6 설치 확인; 현재 apt 13.7만 제공, 오래된 dev 13.6 후보 없음.
- 완화 없이 네이티브 증인 라이브러리는 별도 빌드 Job에서 컴파일하고, 실제 Moving Goal은 **변경되지 않은 13.6 런타임 컨테이너**에서 수행해 원본 안전 의존성 유지. 빌드한 파일의 SHA256 확인 후 실제 Gazebo plugin 로딩 성공.
- 중간 같은 구조 실제 [#44432235573](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44432235573) SUCCESS (이전 Student SHA `b1d1973...`). 
- **최종 Student `dcd1299c...` 실제** [#44433206283](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44433206283) **SUCCESS** (공개 CI HEAD `71b85c42ea474276fedd9f345521317b8c348b4e`). 실제 출력:
```text
G07_N7_PINNED_13_6_GAZEBO_RUNTIME_UNCHANGED
AXIA_G07_TASK04_NATIVE_ONE_MOVING_RUNNER_RC=0 RVIZ_X11=1 GAZEBO_X11=1
AXIA_G07_TASK04_NATIVE_MOVING_GUI_VERDICT {"first_failure":"NONE","gui_windows_seen":2,"source_sha":"dcd1299c03bf702712631dc025b868335cadd1c6","status":"TASK04_REAL_GAZEBO_MOVING_GUI_L2_SCOPED_PASS"}
AXIA_G07_TASK04_OWNER_MOVING_L3=NOT_RUN AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false
```
- 해당 verdict 코드는 모든 **21개 실제 Gate**가 참일 때에만 생성됨. 수치 JSON artifact [#14487965556](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44433206283/artifacts/14487965556); 공개 아티팩트에 실제 원본 rosbag/개인 경로 없음.
- Owner 공개 고정 실행기 코드 `scripts/axia_g07_task04_owner_moving_l3_once.sh`, 소스 commit **`4cd36853358bb088263a0b73a0cfa6c8d5ec2d55`**. 내부 Student `dcd1299...`, 공개 review `71b85c42...`, L2 `44433206283` exact pins. 실제 Owner WSLg L3는 현재 **NOT_RUN**.

```ini
PUBLIC_CI_L0_N7_CLOCK_GUARD=PASS_14_TESTS
PUBLIC_CI_NATIVE_MOVING_GUI_L2=PASS_21_OF_21
NEW_OWNER_WSL2_L3=NOT_RUN
WSL2_REALTIME_STEP_HOST_PHYSICAL_CAUSE=NOT_PROVEN
OWNER_NATIVE_GUARD_150MS=AWAIT_NEW_RUN
CERTIFIED_ESTOP=false
AXIA_MVP_DEMO_ACCEPTED=HOLD
MAIN_MERGED=false
```

검증 수준: CI의 Linux/Xvfb 실제 Gazebo/Nav2; 강사 WSL2의 WSLg/NVIDIA 화면·Guest/Windows 물리 스케줄링은 미검증. 권한 있는 Owner의 새 원본 Guard 내부 age와 CM raw+corrected clock step을 다시 검사한 뒤에만 정식 L3 판정.
