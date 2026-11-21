# AXIA G07 — WSL2 Owner 1ibYCGPg 최초 CM120 시간축 불연속·콜백 공백 RCA 및 공개 CI 회귀 (2026-11-21)

## 0. 인수 판정

```text
OWNER_ARCHIVE_SHA256=PASS
OWNER_DIAGNOSTIC_ZIP_SHA256=PASS
OWNER_DIAGNOSTIC_ZIP_INTERNAL_33_OF_33=PASS
OWNER_FUNCTIONAL_MOVING_GOAL=PASS_SCOPED_NUMERICAL_CANDIDATE
OWNER_SCAN300=PASS_IN_12S_PREG0AL_AND_MOVING_WINDOW
OWNER_GUARD_150=PASS_MEASURED_INTERNAL_AGE
OWNER_NAV_LOCALIZATION_SHUTDOWN=ACK
OWNER_CM120=HOLD
OWNER_WSL2_L3=HOLD
FIRST_CM_SOURCE_CAUSE=RMW_FORWARD_TIMEBASE_OFFSET_STEP_CANDIDATE_OS_CAUSE_UNPROVEN
FIRST_CM_OBSERVER_CAUSE=POST_RECEIPT_CALLBACK_DELIVERY_GAP_OR_SCHEDULING_UNDETERMINED
PUBLIC_NATIVE_L2=HISTORICAL_PASS_2_OF_2_44830956042_UNCHANGED_RUNTIME
NEW_NATIVE_L2=NOT_RUN_DIAGNOSTIC_ONLY
CERTIFIED_ESTOP=false
MAIN_MERGED=false
```

### 입력 무결성
- 원본 WSL2 TAR SHA-256 `47f930d67e064e0bca8116f4db6e88eac11b97cfaeda411f56facb7b53429808` — 로컬 재계산과 제공된 sidecar **일치**.
- 소형 진단 ZIP SHA-256 `180876cdf3468e2c379b667bd9ae073d56c958d4b7fc19ba54e3358282d5a69d` — 일치.
- ZIP `SHA256SUMS`의 개별 **33/33 파일** 재검증 PASS.
- ROS bag 원본·Goal UUID·로컬 사용자 경로를 공개 GitHub에 업로드하지 않음. 최소 수치 fixture만 공개함.

## 1. 원래 Goal·Safety·Scan 증거

실제 같은 Gazebo/Owner run:
- 12초 NO_GOAL Scan: `/scan` 최대273.140844ms, `/safety/scan` 최대284.502559ms, 둘 다 300ms 이하. LaserScan.header Sim 간격 최대102ms, 전체 preflight `/clock` RTF 0.763519. 이 평균은 순간 위반 부재를 일반화하지 못함.
- Moving oracle: Scan 최대271.170908ms, Clock108.642822ms, Odom153.280517ms, Guard85.392462ms, CM111.912750ms, Source111.863284ms. `first_timing_violation=null`은 **이 oracle의 유한한 측정 구간 한정**.
- 실제 CLEAR→SLOW→STOP, 장애물 native ACK, Odom 이동0.135770716m, STOP ZERO 유지1.092702188s, 단일 Action Cancel ACK 및 terminal CANCELED, Guard latch false. Guard 내부 CM age 최대62.715465ms (150ms 안전 TTL 이내).
- Nav2 Navigation SHUTDOWN ACK 3.888127s, Localization ACK 0.306591s, Collision Monitor child exit0, Gazebo/RViz GUI 각각 1창.
- 그러나 별도의 Task02 raw strict reviewer는 **`cm_source_and_observer_120ms=false`**; `cm120.source_gap_max_ms=2815.517569`, `observer_gap_max_ms=124.069382`; 따라서 전체 L3는 명백한 **HOLD**.
- Launch startup 중 Supervisor `HEALTH_BAD_DIAGNOSTIC` `SCAN_TIMEOUT` scan age 약0.503s와 callback max0.546s가 Moving Goal **이전** 두 차례 관측됨. 후속 12초 사전검사 구간의 Scan300 PASS와 혼동하거나 startup scan fault가 없었다고 주장하지 않음. 원시 Guard 최초 안전 전이 전체는 추가 분석 없이 PASS로 승격하지 않음.

## 2. 첫 CM RMW timestamp step — 발행 중단이 아닌 시계 불연속 후보

실제 `actual_ros_events.jsonl`에서 **동일 publisher 연속 `publication_sequence +1`** 쌍:

| 경계 | CM `pre_guard` | 독립 `supervised` |
|---|---:|---:|
| Observer Host Monotonic 간격 | **34.407404ms** | **34.462806ms** |
| RMW Source timestamp 간격 | 2815.517569ms | 2815.603594ms |
| RMW Received timestamp 간격 | 2813.345501ms | 2815.470742ms |
| Sequence gap | 1 | 1 |

최초 `pre_guard` 수신 Monotonic `254.459381067→254.493788471`. `supervised`는 거의 같은 시점 `254.459514295→254.493977101`.

**독립 14-topic 원본 rosbag SQLite의 `/clock` 수신 timestamp**도 이 시각대에서 **2783.797150ms** 도약하지만, 두 `rosgraph_msgs/msg/Clock` payload의 **Sim Time은 단 3.0ms** 진행. 해당 수치는 실제 DB의 CDR `sec,nanosec` 필드를 직접 파싱한 결과다. 즉 전체 시스템이 2.8초 동안 정지했다는 주장과 모순된다.

위 두 독립 Twist publisher의 source/received가 동시 순방향으로 변하고 Monotonic은 약34ms만 진행하므로 **시스템 Wall Clock 또는 DDS/RMW 타임스탬프 계층의 약2.78초 기준값 도약 후보**로 분류한다. 원인이 Windows↔WSL2 시각 재동기화인지, Fast DDS 구현 내부인지 구별할 원본 OS sync stack/커널 trace는 없으므로 **원인 `UNDETERMINED`**. 이는 기존 [PR #197](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/197)의 *RMW 역방향 시각 도약 HOLD* 원칙을 그대로 **순방향**으로 확장한 것.

공식 근거: [Fast DDS 2.14 Writer source timestamp](https://fast-dds.docs.eprosima.com/en/2.14.x/fastdds/api_reference/dds_pim/publisher/datawriter.html), [ROS2 rosbag send/receive clock-domain issue #2023](https://github.com/ros2/rosbag2/issues/2023).

## 3. 별도 **실제** CM120 Observer 공백 — 여전히 HOLD

**최초 Monotonic callback 위반 (동일 `pre_guard` publisher, sequence +1)**:
- `257.455672520→257.579741902` **124.069382ms > CM120ms**.
- 동일 쌍의 RMW Source 간격 **48.746752ms**, RMW Received 간격 **41.902093ms**.
- `supervised` 별도 subscriber 콜백도 동시 **123.971581ms**, 해당 쌍 Source49.054477ms / Received49.806923ms, sequence+1.
- 위 공백은 `task03_motion_window_end=257.490634790`를 가로지르며, 실제 Action terminal CANCELED 판정 직전이다. **시연 종료에 가까웠다는 이유로 TTL을 무시하지 않는다.**
- 이 동일 시스템 시각 부근의 원본 rosbag `/cmd_vel_pre_guard` 독립 수신 gap 최대 **66.794719ms**, `/cmd_vel_supervised` 최대66.838ms (해당 좁은 시스템시각 구간). 독립 수신과 Oracle에서 124ms 발행 중단을 증명하지 못하므로, **Observer 콜백 실행·executor scheduling 또는 계측 I/O 지연 후보**를 별도로 HOLD. 실행환경 OS/GPU 등 정확한 원인 미확정.
- Guard 내부 CM age 최대62.715465ms, Guard latch=false는 *그 시점에 다른 안전 계층이 동작했다는 증거*일 뿐 Observer 실제 124ms 위반을 PASS로 상쇄하지 않는다.

## 4. 최소 수정·실제 공개 CI

**기존 코드 재사용**: `d06/diagnostic/g07_task02_strict_gate.py` — 원래 역방향 불연속 경계 유지, 순방향 RMW source/received 양쪽 timestamp 도약이 동시에 발생하고 독립 `supervised` 연속 sequence +1로 교차 확인될 때만 **후보 HOLD**로 분류한다. 실제 120ms 초과 Observer gap은 별도 필드와 실패 상태로 필수 보존.

신규 공개 최소 fixture:
- `tests/fixtures/g07_owner_1ibycgpg_cm_first_timing_numeric_20261121.json`
- `tests/test_g07_owner_first_forward_clock_cm120.py`
- `.github/workflows/axia-g07-owner-first-cm120-clock-l0.yml`

실제 CI 명령:
```bash
python3 -m unittest discover -s tests -p 'test_g07_owner_first_forward_clock_cm120.py' -v
python3 -m unittest discover -s tests -p 'test_g07_task02_exact_clear_ack_contract.py' -v
python -m pytest -q -ra tests
```

실제 RED [#44849761368](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44849761368): 2건 FAIL; 기존 reviewer가 RMW Source max 2815ms를 단순 CM 발행간격과 합치고 Forward-timebase와 실제 Observer 지연을 분리하지 못함.

실제 GREEN [#44849847454](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44849847454): 신규4/4 + 기존5/5 PASS. 전체 기존 회귀 포함 [#44849968589](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44849968589): **293 passed, 3 skipped**.

`Nav2`, `Collision Monitor`, `Safety Supervisor`, `Fault Injector`, `Guard`, Goal / cancellation, ROS QoS, 120/150/300ms 제한 및 LiDAR Hz 전부 **변경 없음**.

## 5. 다음 단일 개발 항목 및 현장 배포 조건

**다음 단일 항목:** 재현된 **124.069382ms** callback 공백의 최초 node/Executor/I/O 경계 분리. 이미 기록 중인 두 ROS Twist subscriber의 같은 시각 source+received+Host Monotonic 값, `task03_motion_window_end` 전후의 Action status callback, 독립 rosbag 수신 간격을 사용한다. 별도 새 주행/안전 노드 개발 없이 기존 D08 read-only observer/배치 기록 기법을 재사용한다. 가능한 부분을 공개 CI에 고립된 스케줄링 회귀 RED→GREEN으로 추가하되, 원인이 입증되기 전 임의 스레드·LiDAR 주기·CM/Guard TTL 조정 금지.

**출고 HOLD**: 124.069382ms 실제 위반과 반복성 경계를 공개 CI에서 다루지 않은 상태에서는 **WSL2 신규 Goal 반복 명령을 배포하지 않음**. 변경된 reviewer를 Owner L3에 연결하려면 공개 정확한 SHA 검증·read-only 시계 경계 회귀·실제 Gazebo L2를 구분해 검증해야 한다. 기존 성공한 [실제 Gazebo 2/2 L2 #44830956042](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44830956042)는 보존하지만, 해당 Run이 이번 수정된 소스의 새 L2는 아니다.

```text
PUBLIC_CI_L0=PASS_CURRENT_DIAGNOSTIC
PUBLIC_CI_L2=PRIOR_PASS_2_OF_2_UNCHANGED_RUNTIME
OWNER_WSL2_L3=HOLD
FIRST_CM_TIMEBASE_STEP=CORRELATED_FORWARD_RMW_TIMESTAMP_STEP_CANDIDATE
FIRST_CM_OBSERVER_GAP=124.069382MS_GT_120MS_CONFIRMED
CLOCK_STEP_CAUSE=UNDETERMINED
OBSERVER_SCHEDULING_ROOT=UNDETERMINED
CERTIFIED_ESTOP=false
MAIN_MERGED=false
```
