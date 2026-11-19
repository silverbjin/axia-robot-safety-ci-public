# AXIA G07 Task04 — Owner oZGSnDD1 Gazebo 임시 SDF 경쟁 조건 분석·교육용 RED→GREEN 보고서 (2026-11-19)

## 0. 소스 및 불변 원본 custody

- 원본 강사 WSL2 증거: `owner-moving-oZGSnDD1.tar.gz` SHA256 `316183965070fab7ffdf0c1621d4cacc9fe4d6d5f674aa125791908a90a19569`.
- 원본 소형 진단: `owner-moving-oZGSnDD1.diagnostics.zip` SHA256 `28c96154ebfb618e37e77adaab0f25a26ad6a9b0d43fa3f1043f5e4180260890`.
- 두 파일의 실제 바이트 SHA256을 재계산해 각각 일치 확인. 비공개 원본 rosbag/WSL2 호스트 경로는 공개 저장소에 올리지 않았다.
- 기준 기존 Student `dcd1299c03bf702712631dc025b868335cadd1c6`, 공개 CI 엄격 review `71b85c42ea474276fedd9f345521317b8c348b4e`, 기존 성공 공개 native L2 `44433206283`, 원샷 `4cd36853358bb088263a0b73a0cfa6c8d5ec2d55`.
- 새 개발 브랜치: Student와 공개 CI 공통 `fix/g07-task04-owner-timing-evidence-20261119`. 기존 성공 증거 보존, main 병합 안 함.

## 1. 처음으로 안전 시나리오를 막은 원인은 Gazebo 서버 시작 실패

실제 `native/launch.log` 사건 순서:

```text
[INFO] [xacro-1]: process started ...
[INFO] [gz-4]: process started ...
[gz-4] Unable to find or download file
[ERROR] [gz-4]: process has died [... exit code 255, cmd 'gz sim -r -s /tmp/nav2_bivgh_gk.sdf']
[INFO] [xacro-1]: process has finished cleanly
```

`native/clock_diagnostics.json`의 `CLOCK_MISSING` (45.002s, samples=0), `P2_L2_SMOKE_RC=3`, 최종 `NATIVE_RUNNER_FAILED_REVIEW_RAW`는 **Gazebo 서버 부팅 실패 이후 결과**이며 독립 원인이 아니다. 원본 /clock, /scan, /odom 0건. Supervisor는 BOOT_SAFE, Guard는 NO_FRESH_PAIR, cmd_vel은 0, Goal 미발행으로 안전 정지됨. Env 25개 package/5개 digest 패리티는 정상이므로 환경 드리프트 또는 GPU RTF 오류로 판단하지 않는다.

## 2. 공식 코드와 재사용되는 기존 H01 코드

- 실제 강사 official `/opt/ros/jazzy/share/nav2_bringup/launch/tb3_simulation_launch.py` SHA256 `cb65906827c9897100512d64ee1ac7537fe859e3fc29fcc96aec8119bd7bebf2`.
- 공식 Jazzy Nav2는 `tempfile.mktemp(prefix='nav2_',suffix='.sdf')` → world `ExecuteProcess(cmd=['xacro','-o',...])`와 Gazebo `ExecuteProcess(cmd=['gz','sim','-r','-s',...])`를 별도 순차 등록한다. 등록 순서가 프로세스 완료의 보장은 아니다.
- 기존 Student `block_B/day07/h01_runtime/ros2_ws/src/axia_safety_bringup/launch/axia_tb3_p2.launch.py`의 `_order_h01_world_xacro_before_gazebo`는 H01 NO_GOAL에만 적용. G07 Owner 및 실제 공개 Moving CI에는 적용되지 않았다.
- 공식 Nav2 설치 트리는 수정하지 않고 기존 `OnProcessExit` Launch action 의존 관계를 H01·G07 Owner·공개 Moving CI에만 재사용.
- 참고: [Nav2 Issue #5350](https://github.com/ros-navigation/navigation2/issues/5350) 유사 `Unable to find or download file`, `/tmp/nav2_*.sdf`, exit 255. 외부 Issue는 확증이 아니라 보조 근거.
- 원본 로그만으로 임시 파일이 순간적으로 없었던 정확한 타이밍은 독립 계측되지 않았으므로 **Xacro 완료 전 Gazebo 시작 경합 = 가장 유력한 가설**로 취급.

## 3. RED

- Student 최소 회귀: `block_B/tests/test_g07_task04_world_xacro_order.py`.
- 공개 CI [RED #44439674602](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44439674602)에서 4개 실패. 오류 `G07_TASK04_XACRO_WORLD_SYNC_HELPER_MISSING`, Owner/CI 실행 순서 보호 부재를 정적 계약으로 재현.
- 초기 CI `#44439608201`은 `unittest discover` 인자 순서 오타로 테스트가 실행되지 않은 **하네스 오류**이며 RED 증거로 집계하지 않는다.
- 추가 동결 fixture: 테스트 내부 지연 Writer(0.08s)로 파일 생성 전에는 `GAZEBO_WORLD_SDF_MISSING`, 생성 완료 후에만 `WORLD_SDF_READY`를 확인한다. 실제 런타임은 `sleep`이나 재시도 루프를 추가하지 않는다.

## 4. GREEN — 최소 수정

Student `block_B/day07/h01_runtime/ros2_ws/src/axia_safety_bringup/launch/axia_tb3_p2.launch.py`:

1. `_world_xacro_sync_scope`: 정확히 하나의 승인된 H01 NO_GOAL, Task04 Owner, Task04 public Moving CI 시뮬레이션 모드에만 적용. 비허가 환경 무변경.
2. `_check_world_sdf_after_xacro_exit`: ROS `ProcessExited.returncode` 확인 → xacro 출력 인수 `-o` 및 임시 절대 `.sdf` 경로 확인 → 파일 존재·내용·SDF XML world 요소 확인 → 바이트 SHA256 로깅. 실패 시 `GAZEBO_WORLD_XACRO_FAILED` / `GAZEBO_WORLD_SDF_MISSING` / `GAZEBO_WORLD_SDF_INVALID` / `GAZEBO_WORLD_XACRO_COMMAND_CHANGED`로 구분.
3. `_order_world_xacro_before_gazebo`: 원래 Gazebo action을 최초 LaunchDescription에서 제거하고, world Xacro의 OnProcessExit 처리에서 성공·유효 SDF일 때 **그 Gazebo action을 한 번** 반환. 실패하면 `Shutdown`을 emit해 fail-closed, 추가 Gazebo 서버 없음.
4. Gazebo/CM/Guard/Nav2 임계값, Goal, 월드 물리 배치, LiDAR 10Hz, GPU GUI는 변경하지 않음.

## 5. 실제 실행된 L0·L1

| 범위 | 공개 실행 | 실제 결과 |
| --- | --- | --- |
| 정적 최초 GREEN | [#44439919232](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44439919232) | 4/4 PASS, ROS/Gazebo 미기동 |
| 추가 delayed writer 포함 최종 L0 | [#44440787429](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44440787429) | 5/5 PASS |
| 실제 ROS Jazzy Launch event L1 최초 | [#44440434125](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44440434125) | 3/3 PASS, Gazebo/Goal 미기동 |
| 최종 Student 동일 SHA의 L1 | [#44440794690](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44440794690) | 3/3 PASS |
| 기존 Guard/CM 회귀 L0 | [#44440802392](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44440802392) | SUCCESS |

첫 L1 시도 [#44440259349](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44440259349)는 ROS `setup.bash` 전에 `set -u`를 활성화한 CI 하네스 문제(`AMENT_TRACE_SETUP_FILES: unbound variable`)로 실패했고, ROS 설정을 먼저 source하도록 최소 수정해 GREEN 확인. 본문 GREEN은 Xacro 실제 파일 상태와 Launch event 대응만 검증하며 **Gazebo 실기동으로 보고하지 않는다.**

## 6. 실제 Gazebo L2 및 출고

- 최종 Student 소스: `bcebc5d1f3a7d00860a541507e263dd05b27a9a3`.
- 첫 2-Job 실제 L2 [#44440932197](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44440932197)는 **주행·감속·STOP·정확한 Goal UUID 취소까지 성공**했지만 Localization Shutdown service 30.001s TIMEOUT으로 **FAIL**했다. 진단 포함 두 번째 [#44442176276](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44442176276)도 Localization 30.003s TIMEOUT. 원래 `libgz-transport13=13.6.0` 런타임은 그대로, 별도 Native Witness 빌드 재사용.
- 이전 Owner SHA `4cd368...`는 **새 Xacro 순서 수정 전 배포본**이며 재사용 금지. 후속 Localization 종료 ACK 이슈의 별도 RED→GREEN과 최종 실제 21/21 L2 후 원샷 SHA `1816fbbbfdb972e52c5168ade26c768167998556` 확정.
- 이 보고서의 구현/정적 테스트 사실이 `OWNER_WSL2_L3=PASS`를 의미하지 않는다. 실물 인증 E-Stop 아님.

## 7. 인수 경계

```ini
PUBLIC_CI_L0_WORLD_XACRO_ORDER=PASS
PUBLIC_CI_L1_ROS_JAZZY_LAUNCH_EVENT=PASS_NO_GAZEBO
PUBLIC_CI_L2_XACRO_ONLY=BLOCKED_LOCALIZATION_ACK_30S
PUBLIC_CI_L2_XACRO_PLUS_ACK_CLIENT=PASS_21_OF_21_RUN_44449459417
OWNER_WSL2_NEW_L3=NOT_RUN
AXIA_MVP_DEMO_ACCEPTED=HOLD
CERTIFIED_ESTOP=false
MAIN_MERGED=false
```

현장 새 오류 발생 시에는 최초 Gazebo/Xacro 이벤트와 최초 Safety FSM 전이·최초 주기 위반을 원본 TAR/진단 ZIP으로 확인한 뒤 공개 CI 회귀 RED→GREEN으로 재편입한다. 다른 안전 계층 타이밍을 확인하지 못했다면 전체 인수 미검증 표시.

## 8. 최초 SDF 경쟁 조건 수정 뒤의 후속 Localization ACK 및 최종 시연 통합 인수

Xacro 완료 뒤에만 Gazebo를 실행하도록 한 변경은 실제 시뮬레이션에서 World·Clock·센서 준비, Clear→Slow→Stop, 실제 odom 이동, Goal 취소까지 실증했지만, 첫 두 공개 CI 실행에서 Nav2 Localization 관리 서비스 종료 ACK가 30초 만료됐다. 이를 별개의 실패 경계로 남기고 신규 테스트 RED [#44443257191](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44443257191) → 6/6 GREEN [#44443374979](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44443374979)으로 처리했다.

- 최종 Student `6579e2eef7e99691da558cd2de1964fd26a04621`.
- 실제 Gazebo/Nav2 Moving Goal+Gazebo/RViz Xvfb CI [#44449459417](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44449459417) **SUCCESS**. 기존 21개 엄격 gate, runner rc0, GUI2, Goal cancel, native Contact0, Navigation/Localization 종료 ACK 및 CM clean exit, `first_failure=NONE`.
- CI의 read-only 엄격 판정 commit `71b85c42ea474276fedd9f345521317b8c348b4e`; 이번 L2와 앞선 n7 실제 주행 증거에 설정된 safety TTL과 기준선 변경 없음.
- 현장 실행기 코드 source `1816fbbbfdb972e52c5168ade26c768167998556`. 공개 ROS 미실행 bootstrap [#44450173850](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44450173850) 8/8 PASS.
- 별도 교육용 종료 문제 해결 보고서: `docs/operations/AXIA_G07_TASK04_OZG_LOCALIZATION_SHUTDOWN_ACK_RED_GREEN_20261119_KO.md`.

```ini
PUBLIC_CI_L0_XACRO_RACE=PASS_5_OF_5
PUBLIC_CI_L1_ROS_LAUNCH=PASS_3_OF_3_NO_GAZEBO
PUBLIC_CI_L0_LOCALIZATION_ACK=PASS_6_OF_6
PUBLIC_CI_REAL_GAZEBO_MOVING_L2=PASS_21_OF_21
OWNER_BOOTSTRAP_L0=PASS_8_OF_8
OWNER_WSL2_L3=NOT_RUN
AXIA_MVP_DEMO_ACCEPTED=HOLD
CERTIFIED_ESTOP=false
MAIN_MERGED=false
```
