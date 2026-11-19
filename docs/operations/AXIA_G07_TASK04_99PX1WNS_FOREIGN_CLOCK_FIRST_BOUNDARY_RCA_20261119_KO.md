# AXIA G07 Task04 — 99PX1WNS / 8ULG28b7 최초 실패 및 두 Clock 시간축 원인 분석

- 작성일: 2026-11-19
- 변경 범위: **Owner WSL2 진입 시 실행 세션의 ROS Domain 격리만**. Goal / ROS 2 Jazzy / 공식 Nav2 / Gazebo Harmonic / Collision Monitor / Safety Supervisor / Scan 300ms·CM 120ms·Guard 150ms 불변
- 교육용 시연 인수 기준선 `AXIA-G07-T04-DEMO-BASELINE-20261119-CZObXAdP` 유지: **ACCEPTED (교육용)**. 정식 safety timing acceptance는 `NOT_CLAIMED`, 인증 E-Stop 아님
- 현장 신규 TAR: `owner-moving-99PX1WNS.tar.gz` SHA256 `a0265ef04c1d79ac9d3a99f6525441b946421895a310ca8e0e8a9b0794839815`, 진단 ZIP SHA256 `74208dae34dea5ca78eb1ef6d66da92a02295cd13f455a4f3a2f4b10d1994923`; 첨부 sidecar 일치.
- 이전 TAR: `owner-moving-8ULG28b7.tar.gz` SHA256 `ebb651629f0ee5fb0b2352258b7a90bd808e10d6f2dd7935de7301d900d40a62`, 진단 ZIP SHA256 `354a4bfbf4bfb9dec4b48a3a6c55b27db194cc659f8276c7aab2971ed2c90d07`, 첨부 sidecar 일치.
- 성공 비교 기준: `owner-moving-CZObXAdP` 기존 SHA256 검증 원본 /clock 28,208 messages.

## 1. 최초 실패 경계 — 마지막 shell 오류 아님

| 항목 | 8ULG28b7 | 99PX1WNS |
|---|---|---|
| `ROS_DOMAIN_ID` | 86 | 86 |
| `GZ_PARTITION` | 고유 | 다른 고유 파티션 |
| CLOCK_READY | PASS | PASS |
| Navigation planner pre-state | unconfigured | unconfigured |
| LOCALIZATION_START | **REJECTED** | **REJECTED** |
| native request_sent | true | true |
| Native service elapsed | 0.650261s | 0.190248s |
| 실제 Goal | 발행 안 함 | 발행 안 함 |
| GUI | RViz=1, Gazebo=0 | RViz=1, Gazebo=0 |

99PX1WNS `native/launch.log` 최초 실패는:
```text
1795098874.761625 lifecycle_manager_localization Starting managed nodes bringup
1795098874.761695 lifecycle_manager_localization Configuring map_server
1795098874.762680 map_server Configuring
1795098874.763460 map_io Loading image_file: /opt/ros/jazzy/share/nav2_bringup/maps/tb3_sandbox.pgm
1795098874.773984 lifecycle_manager_localization ERROR Failed to change state for node: map_server
1795098874.774040 lifecycle_manager_localization ERROR Failed to bring up all requested nodes
1795098874.778480 map_io Read map ... 384 X 384 map
```

이를 원본 서비스 관측 결과 `G07_NATIVE_LIFECYCLE_STARTUP_REJECTED:request_sent=True`가 보증합니다. `NATIVE_RUNNER_FAILED_REVIEW_RAW`는 사후 요약 메시지이며, 후속 `p2_supervisor_node` ROS Context 오류는 종료 시점의 2차 예외입니다.

**단순한 YAML 파일 부재라고 판정할 근거는 없습니다**: 지도 YAML·이미지 읽기 로그 존재. 실패 지점은 Service/State 전환의 응답 및 상태 불일치입니다. Lifecycle Manager가 4.5ms 먼저 ERROR를 출력한 사실만으로 단일 Nav2 라이브러리 버그라고 단정하지 않습니다.

## 2. 더 최초 시스템 경계 — 실제 rosbag CDR /clock 역행

원본 rosbag2 SQLite `/clock`의 `rosgraph_msgs/msg/Clock` CDR을 timestamp 순서로 복원하였습니다. 뒤로 이동한 쌍의 수를 계산할 때 tolerance=1ms 사용.

| 실행 | /clock 메시지 수 | **실제 backwards pairs** | 두 시계 |
|---|---:|---:|---|
| 성공 Baseline CZObXAdP | 28,208 | **0** | 0.006s → 84.627s 단조 증가 |
| 실패 8ULG28b7 | 4,333 | **649** | 약 452s ↔ 0.01s |
| 실패 99PX1WNS | 6,421 | **1,617** | 약 1940s ↔ 0.04s |

99PX1WNS 원본의 첫 대표 교차:
```text
sim_time 1940.511 -> 0.075 -> 1940.514 -> 0.081 -> 1940.523
```

같은 구간 `robot_state_publisher`는 다수 `Moved backwards in time`을 기록했습니다. `CLOCK_READY` 검사는 3개 advancing 표본만 확보해 **두 스트림 간 왕복 교차를 탐지하지 못했습니다**.

GZ_PARTITION은 매번 달랐으나 ROS_DOMAIN_ID=86은 동일했습니다. Gazebo Transport 파티션은 ROS DDS domain을 분리하지 않습니다. **기존 ROS /clock 발행자나 Nav2 Lifecycle 서비스의 유입/중복**이 가장 강한 원인 후보입니다. 최초 8ULG28b7의 높은 시뮬레이션 시간축이 이후 99PX1WNS에서도 더 진행한 값으로 등장해 잔존 세션과 일치하지만, 원본 rosbag에는 publisher GID·PID가 없어 **같은 프로세스라고 확증하지 않습니다**. Nav2 MapServer 응답 실패가 해당 충돌로 직접 유발됐는지는 성공/실패 WSL2 A/B 확인 전까지 **인과 미검증**입니다.

관련 공식 문서: ROS 2 Jazzy environment guide — ROS_DOMAIN_ID는 다른 사용자/세션과 충돌하지 않는 값으로 지정하며 ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST는 로컬 통신을 허용하므로 동일 호스트 같은 Domain까지 격리하지 않습니다. 참조 https://docs.ros.org/en/jazzy/Tutorials/Beginner-CLI-Tools/Configuring-ROS2-Environment.html

## 3. 최소 수정 — Domain 86 고정 삭제 (기존 빌드 캐시 보존)

Public CI Owner 스크립트 `scripts/axia_g07_task04_owner_moving_l3_once.sh`:
- 원래 `AXIA_G07_TASK04_DOMAIN_ID:-86`를 기본값으로 강제했음. 이전 프로세스의 ROS Topic 및 Lifecycle Service가 동일 Domain에 생존해도 Gazebo를 바로 실행함.
- 변경 후 실제 `rclpy` DDS endpoint graph를 **Gazebo·Nav2 이전**에 조회. 랜덤 후보 (20~101; 오염 사례 86 기본 제외)에서 약 1.8초 조회 후 다른 node 또는 `/clock`, `/scan`, `/safety/scan` publisher가 있으면 반드시 다른 후보를 검색.
- 사용자 override `AXIA_G07_TASK04_DOMAIN_ID=86`를 지정했다면 86이 깨끗하지 않을 경우 **Goal 없이 즉시 BLOCKED**; 임의 우회나 파괴적 `pkill/killall` 사용 금지.
- 선택한 ROS_DOMAIN_ID에 맞춰 새 GZ_PARTITION 생성, 출력 `AXIA_G07_TASK04_ROS_DOMAIN_SELECTED=<id> CLOCK_PUBLISHERS_BEFORE_LAUNCH=0` 및 `domain_selection.json`을 private 증거·small diagnostics ZIP에 포함.
- 필드 다운로드는 별도 고정 Git commit `977d759e751c08d6d3d22b5c9b53e2d114ad58ae` + Git blob `8c8db2e361216ec34c1d7a5d19e0ddb436af7fa3`을 확인해 사용. 추후 변경시 pin 재승인 필요.
- 이미 공개 CI 성공한 **native plugin persistent cache**와 WSLg GUI 위치 계측은 변경하지 않음.

Source: `scripts/axia_g07_task04_select_free_domain.py`, `scripts/axia_g07_task04_owner_moving_l3_once.sh`; Regression: `tests/test_g07_task04_foreign_clock_domain.py`; L0/L1 workflows: `.github/workflows/axia-g07-task04-clock-domain-regression-l0.yml`, `.github/workflows/axia-g07-task04-clock-domain-real-ros-l1.yml`.

## 4. RED→GREEN→REFACTOR→REVIEW

- RED ROS-free [#44546939180](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44546939180) missing clean-domain helper and fixed-86 default, expected failure.
- GREEN ROS-free [#44548251505](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44548251505), 5 new foreign-clock + 5 startup-cache contract + 4 actual Bash cache stub + 9 original Owner L0: **23/23 PASS**.
- 초기 실제 Jazzy L1 [#44547586617](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44547586617), 진단 추가 [#44547906061](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44547906061)에서 custom rclpy Context와 global `spin_once` Executor 호환 문제로 TypeError 재현. 원본 첫 API 예외 `'NoneType' object does not support the context manager protocol`. 별도 custom Executor 신설 대신 **callbacks 없는 DDS graph discovery에서 단순 시간 대기**로 최소 수정.
- 실제 [ROS 2 Jazzy DDS L1 GREEN #44548198937](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44548198937) 및 최종 [#44548251395](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44548251395): `ROS_DOMAIN_ID=86`에 실제 /clock 발행자 작동 → 명시 86 **NO_FREE_DOMAIN BLOCKED**, 자동 모드 **새 깨끗한 Domain 68 선택** (`goal_sent=false`). 이는 fake 테스트가 아닌 실제 Jazzy/FastDDS endpoint discovery 입니다.
- User의 가속 실행 99PX1WNS는 신규 빌드 캐시 `MISS 101.306초`, 실제 GUI RViz1/Gazebo0, 총 `startup_timing.tsv` runner started at 108.750초, completed at 150.661초. **캐시 HIT의 로컬 WSL2 수치는 아직 실측하지 않음**.
- 이전 동일 Student SHA의 실제 Moving Goal Gazebo L2 [#44478344652](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44478344652) 유지. 이번 새 Domain selector 사용한 실제 WSLg·Gazebo·Nav2 Moving Goal L3 **NOT_RUN**. 따라서 성공했다고 승격하지 않음.

## 5. Owner 최종 검증

Owner는 다음에 **기존 교육용 시연 1회 실행**만 해주면 됨. 미확인 Localization 실패가 재발해도 원본 증거와 `domain_selection.json`이 보존됨. Domain 선택 이후 Robot/Pose/TF/Nav2/CM/Safety TTL 등은 원래 시연과 완전히 동일한 소스 SHA를 사용.

**목표:** `/clock` epoch 역행 0, MapServer/AMCL true lifecycle ACK, Gazebo+RViz2 2/2, 실제 CLEAR/SLOW/STOP/정확 Goal 취소. Scan300 관측 이벤트는 교육용 사례로 별도 보존하고 이 MVP 교육 인수의 실패로 재정의하지 않음.

**현재:** 원인 경계 CDR 및 real DDS L1까지 검증; **WSL2 최종 L3 미검증**, `main` 변경하지 않음. 인증 E-Stop 주장 안 함.
