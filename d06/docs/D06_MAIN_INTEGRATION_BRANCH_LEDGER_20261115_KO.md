# AXIA D06 공개 CI main 통합 인계 (2026-11-15)

**검증 원칙:** ROS 2 Jazzy의 **공식 Nav2 Collision Monitor**를 격리 토픽에서 재사용한다. 새 D06 관찰기는 `/scan`, `/odom`, `/cmd_vel_supervised`, `/cmd_vel_pre_guard`, `/cmd_vel`를 구독해 **교육용 MarkerArray만 게시**한다. 이는 정지 제어기가 아니며 **실제 Guard/CM 안전 상태를 인증하지 않는다**.

## D06 브랜치별 역할·병합 처리

| D06 브랜치 | PR / 상태 | 역할 | main 통합 판단 |
|---|---|---|---|
| `feature/d06-safety-bubble-20261110` | [#34](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/34) MERGED | 공식 `nav2_collision_monitor`격리 L0/L1 및 WSL2 원샷 | 이미 main 포함(behind only, ahead=0), 재병합 불필요 |
| `feature/d06-gazebo-rviz-owner-20261114` | [#108](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/108) DRAFT/HOLD | 강사 G07 실제 이동 Goal과 연동한 Gazebo+RViz2, CM/Guard/Scan 타이밍·정상 종료·Owner 현장 실패 회귀를 함께 포함 | **전체 병합 금지**: L3 첫 CM 송수신 150ms 위반 및 Goal 원본 증거 부족. 이 브랜치에서 검증된 read-only `d06_readonly_monitor.py`·`d06_ros_l1_visual_probe.py`·RViz 표시는 별도 추출 |
| `release/d06-g07-observer-owner-20261115`, `release/d06-g07-owner-g11-pinned-20261115` | G07/P4 인수 후보 | 실운행·Owner source pin·안전 TTL/선행 gate가 한 브랜치에 혼재 | 최신 main 대비 400+ commits diverged 및 G07/P4 혼입. D06 교육 릴리스에서 **제외**, P4 formal Gate로 위임 |
| `release/d06-readonly-observer-main-20261115` | 별도 공개 CI 인수 PR | 위 #108에서 **읽기 전용 ROS L1 모듈 2개 + RViz 설정 1개**만 최신 main으로 이식하고 공개 Actions 실제 Jazzy L1에 재검증 | L0/L1 통과 후 main 병합, Owner script/Goal 및 private source 미포함 |

## main에 이미 있는 공식 CM 격리 테스트

- `d06/params/collision_monitor_d06.yaml`, `d06/scripts/d06_cm_live_gate.py`, `d06/scripts/d06_owner_wsl2_once.sh`: 기존 #34의 공식 Nav2 CM 분리된 테스트 토픽. 로봇 실제 `/cmd_vel` publisher=0.
- [실제 공식 CM 격리 ROS L1 #42656227824](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/42656227824): 1.20/0.65/0.30m synthetic LaserScan → 입력 0.20m/s에 대하여 출력 0.20/0.06/0.00m/s. 이는 실제 Gazebo 물리 접촉, STOP 이후 odom, 이동 Nav2 Goal 또는 하드웨어 E-Stop 검증이 아님.

## 신규 이식한 D06 read-only 모듈 및 CI

- `d06/live/d06_readonly_monitor.py`: 실제 ROS LaserScan·Odometry·Twist subscriber; `/axia/d06/rviz/bubble` MarkerArray 1개 publisher만 생성. 거리에 따른 CLEAR/SLOWDOWN/STOP/UNKNOWN 교육용 annotation이며 **실제 CM verdict가 아님**.
- `d06/live/d06_ros_l1_visual_probe.py`: 실제 ROS 노드로 1.20/0.65/0.30m LaserScan을 주입해 구독·MarkerArray 수신과 `/cmd_vel` publisher=0을 확인. L1에서는 실물/Gazebo/Goal 없음.
- `d06/rviz/d06_safety_bubble.rviz`: RViz 설정 파일. 현재 main에서 소스 보존만 완료; **WSLg 렌더/동시 G07 GUI는 미검증**. G07 Owner Wrapper/Sidecar는 검증되지 않은 범위로서 이번 main에 추가하지 않는다.
- `.github/workflows/d06-readonly-observer-main-ci.yml`, `d06/tests/test_d06_readonly_public_contract.py`: 공개 Actions에서 소스 L0 + 실제 ROS Jazzy L1만 확인. 비공개 체크아웃·보호 환경·Goal·안전 ROS publisher 없음.
- [공개 신규 L0 + 실제 ROS L1 #43672843751](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43672843751): **모든 단계 SUCCESS**. `D06_PUBLIC_READONLY_ROS_L1_PASS NO_GOAL NO_CMD_VEL`. 기존 원본 #108의 격리 L1 성적을 최신 main으로 이식해 확인한 것임.

## 미검증·차단 중인 안전 경계

- 최근 D06/G07 Owner L3: 최초 `/cmd_vel_pre_guard` CM source-gap **184.415ms > 150ms**, Guard CM age **169.168ms > 150ms**, `UPSTREAM_STALE_AFTER_MOTION`. Guard fail-closed는 보호 동작이지만 **정상 CLEAR→SLOW→STOP 주행 완료가 아님**.
- 동시에 이동 Goal을 실행할 G07/Gazebo GUI+RViz2 Sidecar, 실제 WSL2 화면, RMW 데이터 흐름 주기와 Guard 150ms, STOP 이후 odom 1초, native lifecycle 종료 **완전 인수 HOLD**.
- 이전 다른 SHA의 부분/독립 L2 성공을 이 문제의 수정 증거로 승격하지 않는다. 추가 검증은 P4/G07 별도 CI-first 절차에서 최초 위반 경계부터 진행한다.
- SW 보호정지는 인증된 hardware E-Stop이 아니다.

## 후속 개발 진입점

```bash
git fetch origin main
git switch main
git pull --ff-only origin main
git switch -c feature/d06-next
```

**이번 D06 main 릴리스는 read-only 교육용 L1과 문서에 한정한다.** 공식 Nav2/Collision Monitor YAML·Supervisor·Fault Injector·G07 Owner/Goal·TTL·강사 정답·비공개 GitHub Actions에 변경 없음.
