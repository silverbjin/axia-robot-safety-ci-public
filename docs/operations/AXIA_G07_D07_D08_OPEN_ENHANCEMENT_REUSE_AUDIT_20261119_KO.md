# AXIA G07 Post-MVP — 실제 OPEN 이슈와 D07/D08 재사용 가능성 감사

- 작성: 2026-11-19
- 조사 저장소: `silverbjin/axia-robot-safety-ci-public`, `silverbjin/axia-robot-safety-student`, Instructor 이슈 목록 (코드 비공개 유지)
- 기준 공개 CI main: `7a7fbc85139adcaf05b26e693b5335ac59953493`
- Student 시연 baseline main: `b458ea5645b72878ae4aed5314b69feb8af8deb8`
- **이번 감사는 READ-ONLY 소스/이슈/CI 로그 진단**입니다. 수정·반복 Gazebo·WSL2 재인수·main 병합하지 않음.
- 인수 범위: `AXIA_G07_TASK04_DEMO_BASELINE=ACCEPTED` 그대로. `FORMAL_SAFETY_TIMING_ACCEPTANCE=NOT_CLAIMED` / `CERTIFIED_ESTOP=false`. 관측된 339.177ms는 안전감시 교육 근거로 보존.

## 1. OPEN 사실 (공개 CI)

| 이슈 | 원본 첫 경계 | 다른 브랜치 재사용 | 즉시 종료 가능? |
|---|---|---|---|
| [#157](https://github.com/silverbjin/axia-robot-safety-ci-public/issues/157) | CM publisher 169.524ms vs Supervisor 50ms, 또 다른 주행에선 Odom355.187ms + CM observer354.356ms/CM source41.775ms | D08 독립 ROS 프로세스 + Gazebo Transport 원본 + executor spin_once 계측은 **원인 분리 진단**에 사용 가능 | **아니오** (반복 안정성 미검증) |
| [#163](https://github.com/silverbjin/axia-robot-safety-ci-public/issues/163) | 실제 Nav2 Navigation ManageLifecycleNodes 응답 40.000372s timeout; service advertisement != ACK | G07 main `p2_g07_ordered_shutdown.py`와 D07 lifecycle 순서 재사용, Task04 실제 public Moving L2 #44478344652에서 Nav/Loc ACK+CM clean 21개 검사 성공 | **과거 특정 실행은 해소**, 재발 근거가 있어 **최종 종결 보류** |
| [#185](https://github.com/silverbjin/axia-robot-safety-ci-public/issues/185) | Owner WSL2 NO_GOAL CM exit -11; 센서 주기 위반은 별개 | D06 Student source `8e19742fd7bd80db73a37dc7b1d798768dc33e2a`의 `SENSOR_NO_GOAL && NO_GOAL_ORDERED` 분기에서 기존 G07 lifecycle shutdown을 호출; 진단 관찰 프로세스 stop/join 후 Nav2 종료. Public L2 #44461092763/#44461627846 PASS. **현재 Student main**에는 같은 NO_GOAL 분기가 없음 | **부분 포팅 후보이나 즉시 해결 보장 불가** |
| [#186](https://github.com/silverbjin/axia-robot-safety-ci-public/issues/186) | NVIDIA WSL2 종료: Gazebo server -11, 별도 경우 native Python gz.transport witness -134, Guard/Supervisor exit1; sensor gap/RTF와 인과 별개 | D07 #147은 GPU/GUI 조합 진단·첫 SIGSEGV 분류, D08 Student PR #49는 NO_GOAL Gazebo **GUI** Ogre1 우회 렌더링 성공; 둘 다 native `gz sim -s` shutdown SIGSEGV/abort 직접 수정 증거 아님 | **아니오** (native backtrace 부족) |

이슈 #185와 #186은 후속 진단에서 겹쳐 보일 수 있으나 **CM 프로세스 종료 vs Gazebo 서버 종료의 별도 오류**. `P2_L2_GRACEFUL_TEARDOWN` 단일 마커는 자식 0 종료/ACK를 대체하지 않음.

## 2. 확인한 이미 해결된 소스 및 적용 경계

### D07 — ROS Context 중복 shutdown (실제 해결 기록)

- Student [PR #39](https://github.com/silverbjin/axia-robot-safety-student/pull/39) **merged main**; RED `#44082892074` → 실제 ROS Jazzy Gazebo+RViz L2 GREEN [#44082984762](https://github.com/silverbjin/axia-robot-safety-student/actions/runs/44082984762).
- `block_B/day07/h01_runtime/tools/d07_h01_teaching_loop.py`의 `shutdown_rclpy_once(rclpy)`: 이미 종료된 Context에서 `rclpy.shutdown()` 중복 호출 금지, 먼저 executor 중지/join 확인.
- 별도 `block_B/day07/h01_runtime/tools/p2_g07_ci_moving_goal.py`의 `finally`에는 아직 무조건 `rclpy.shutdown()`가 있음. **사용 가능 패턴은 존재**하지만 시연 후 Guard ROS Context 경고가 정확히 이 호출에서 발생했다고 아직 증명되지 않음. 해당 경고의 최초 stack source 비교 후 **G07 파일 한 곳**에 같은 가드를 적용하고 L0 RED→GREEN, 실제 필요시 L2. D07 코드를 중복 구현하거나 G07 Moving Goal을 재설계하지 않음.

### D07 — G07 Nav2 shutdown ACK/정확 종료 분류

- Public D07 [PR #144](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/144) 실제 Nav/Loc ACK와 4개 child exit0 [#43994275942](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43994275942). D07 [PR #151](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/151) 첫 자식 종료 실패를 우선하는 L0 GREEN, D07 [PR #164](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/164) 부모 `GRACEFUL` 마커만으로 PASS하지 않는 검사.
- 기존 G07 `p2_g07_ordered_shutdown.py`는 Nav→Loc 순서와 실제 ACK를 이미 확인하며 `rclpy.try_shutdown()`도 사용함. G07 Task04 native Moving L2 [#44478344652](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44478344652) reviewer는 `nav_lifecycle_ack`, `loc_lifecycle_ack`, `collision_monitor_child_clean`, `cm_source_and_observer_120ms`, `guard_internal_150ms`, `first_timing_violation_none`, `scan_300ms`를 모두 검사한 scoped PASS. 이것은 과거 #163 타임아웃이 항상 사라졌다는 장기 안정성 보증은 아님.

### D08 — 원본 Gazebo Scan vs ROS callback 분리 (원인 진단 성공, 치료 아님)

- Public [PR #179](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/179)~[#188](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/188) 계열: 독립 `gz.transport13` native receiver, 같은 process vs 별도 process ROS scan 수신, `spin_once` 벽시계/CPU, bounded rcl_publish/rcl_take trace, pinned WSL2 Owner source.
- [PR #181](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/181) 실제 같은 cycle parent ROS 493.470ms, same-process ROS491.950ms vs native Gazebo236.643ms: Gazebo GPU 센서 전체 중단으로 단정 금지, 두 ROS executor가 같은 PID였으므로 GIL/구독/브리지 분리 미완료.
- [PR #184](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/184): 다른 cycle native140.871ms / separate ROS341.956ms / same-Python ROS347.729ms. **post-native 지연 후보**이며 DDS 원인 확정 아님.
- 실제 D08 고유 검증 경계는 500ms, G07 formal Scan은 300ms: **숫자/판정을 통합하거나 완화해서는 안 됨**. G07에는 이벤트 시각 및 source-pair 분리의 **원리/읽기 전용 계측만** 필요한 경우 재사용. D08 그래프·Action·LiDAR 설정을 복사하지 않음.
- D08 학생 [PR #49](https://github.com/silverbjin/axia-robot-safety-student/pull/49) Ogre1 GUI fallback은 이미 `main` 병합·Owner NO_GOAL GUI 관찰됨. **G07 native server -11의 수정이라고 오인 금지**.

## 3. 최신 반례 — 이슈 즉시 CLOSE·코드 복사 금지

**최신 공개 D06/G07 Native L2 [#44491751936](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44491751936) FAIL**. 원본 Job 135448846748 실제 stdout:

```text
AXIA_D06_G07_WITNESS_EXIT native=0 ros=0
AXIA_D06_L2_FIRST_SENSOR_STATUS=NO_GOAL_SENSOR_WINDOW_CLEAR_CANDIDATE reasons=[]
AXIA_D06_L2_NAV2_SHUTDOWN=BLOCKED_LIFECYCLE_LOCALIZATION_SERVICE_TIMEOUT nav_ack=True loc_ack=False
AXIA_D06_L2_CM_PROCESS_AUDIT=SHUTDOWN_CLEAN_CANDIDATE cm_exit_code=0
AXIA_D06_G07_NATIVE_SHUTDOWN_SMOKE_RC=3 RVIZ=1 GAZEBO=1
```

**첫 실제 종료 경계는 Localization ACK 미수신**, 후속 Parent 종료 마커가 아님. 이 실행은 동시에 #163 재발 유형 및 #185 종료 수정의 정식 전계층 인수 한계를 입증함. 동일 브랜치 L0 성공(#44491756398)으로 L2 실패를 PASS 승격 금지.

이전 NO_GOAL L2 x2 성공 [#44461092763](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44461092763), [#44461627846](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44461627846)은 유효하고 보존하지만, 서로 다른 소스/실행에서 성공 수치를 합산하여 재발 안정화했다고 주장하지 않음.

## 4. MVP 보호 하에 후속 적용 우선순위

| 순위 | 타깃 및 파일 | 필요한 최소 작업 | 검증·출고 |
|---|---|---|---|
| P1 | #185 + #163, Student `scripts/p2_no_goal_smoke_ci.sh`, 기존 `tools/p2_g07_ordered_shutdown.py` | 기존 D06 NO_GOAL ordered branch만 소규모 이식 검토. **먼저 #44491751936 Localization timeout의 최초 서비스 request/ACK 경계**를 회귀 분리하고, 이미 존재하는 witness stop/join 순서 유지. 총 1~2파일 범위 | ROS-free L0 RED→GREEN → 공개 실제 NO_GOAL Gazebo 동일 실행 L2(센서/ordered Nav&Loc ACK/CM exit0/Gz server exit0). NVIDIA WSL2 증거 없으면 L3 미검증 |
| P2 | #186, Public `d06/tools/d06_gz_native_scan_probe_safe.py` 및 Observer handoff | SIGABRT exit134/Gazebo -11 실제 최초 child stack/provenance 확보, ROS witness와 native witness 수명주기 분리. D07 GUI 우회 코드 **무조건 복사 금지** | WSL2 최초 재발 구간의 재현 가능한 부분만 CI로. Backtrace 원인 없으면 원인 미확정·HOLD |
| P3 | #157, D08 PR #181~#188 독립 원본·RMW 계측 | G07 기수집 첫 339.177ms 이벤트와 source-native / raw ROS / safety ROS callback host clock을 읽기 전용으로 대응; D08 진단 전체 복사 금지 | 첫 수신 경계 및 7채널 유지, 300/120/150 TTL 불변; 단일 공개 L2 후 WSL2는 필요시만 |
| P4 | D07 Context warning, Student `tools/p2_g07_ci_moving_goal.py` | 경고 최초 stack이 G07 finally에서 발생한 경우에만 기존 `rclpy.ok()` shutdown guard 패턴 재사용 | L0 최소 회귀, 필요한 경우 시연 L2 한 번. D07 완료 코드 재개발 금지 |

**이번 요청은 이슈·소스·CI 실증 비교에 한정했습니다. 신규 ROS/Gazebo 실행, 수정/merge, Issue CLOSE는 수행하지 않았습니다.** 교육용 baseline `ACCEPTED`를 되돌리지 않으며, 새로운 개발은 별도 브랜치에서 진행해야 합니다.
