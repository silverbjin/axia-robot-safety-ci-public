# AXIA D07-H01 — 공개 CI 2단계 통과 후 Owner WSL2 최종 1회 검수 가이드

작성: 2026-11-16 · **정지 Waffle / Gazebo Harmonic / Nav2 공식 Path Before→Intrusion→Restored / NO MOVING GOAL**

## 공개 CI 인수 전제 — 증거 원본

- **L0** 실질 동일 watcher 코드의 모의 `gz`·`rviz2`, world topic fixture, marker, subprocess/ACK, Owner provenance 검사: [실제 공개 Run #43818700568](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43818700568) PASS, public workflow SHA `b4696b675f983b7f695152c8de202a5859a8cbcf`.
- **L2** 정확히 같은 강사 private code SHA `a9f0d2b6ae1f0dcf2e8f92b263d9b66480924c4e`, 실제 ROS 2 Jazzy / Gazebo Harmonic + native robot/obstacle + official Nav2 / RViz2: [실제 공개 Run #43817527534](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43817527534) PASS, public workflow SHA `973cbcdb004c7c6d3c6b4cdc15747544836e8f13`. 실제 GUI X11 RVIZ=1 GAZEBO=1, GUI watcher PID/Free marker/world topics/children 검증. `ComputePathToPose` 3단계 모두 **52 poses**, 각 RViz DDS subscriber 1, robot_moved=false.
- **중요 제한**: L2의 GUI renderer는 GitHub Actions Xvfb `LIBGL_ALWAYS_SOFTWARE=1`, **WSLg NVIDIA D3D12 렌더링·실제 3D 화면 속도/프레임은 미검증**. L0/L2 성공을 Owner WSL2 GPU 성공으로 표시하지 않는다.

## Owner가 수행할 작업 — 단 한 번, 터미널 하나

실제 WSL2 Ubuntu 24.04에서 기존 Gazebo·RViz2 시연을 중복 실행하지 않은 상태에서 아래 원샷 **한 번만** 실행한다. `~/.bashrc`에 `GALLIUM_DRIVER`, `MESA_D3D12_DEFAULT_ADAPTER_NAME`, `LIBGL_ALWAYS_SOFTWARE=0`, `OGRE_RTT_DISABLE`을 추가할 필요는 없다.

```bash
(
  set -Eeuo pipefail
  SHA='36d5604d9ce4c2c41c3bd309e0482255f8e23612'
  SCRIPT="$(mktemp)"
  trap 'rm -f -- "$SCRIPT"' EXIT
  curl -fL --retry 3 -sS \
    "https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public/${SHA}/scripts/axia_d07_h01_gpu_gui_owner_wsl2_once.sh" -o "$SCRIPT"
  bash -n "$SCRIPT"
  bash "$SCRIPT" --self-check
  bash "$SCRIPT" --run
)
```

이 공개 script는 이미 성공한 강사 private SHA `a9f0d2b6ae1f0dcf2e8f92b263d9b66480924c4e`를 직접 pin하여 체크아웃하고 실제 원샷을 구동한다. 브랜치 최신 HEAD를 동적으로 따르지 않는다. server에는 기존 software/안전 환경, **Gazebo·RViz2 GUI 자식 프로세스에만 `GALLIUM_DRIVER=d3d12` + NVIDIA**; 이전 사용자 `~/.bashrc`의 전역 값은 서버 시작 전에 분리한다. 공개 CI 전용 `AXIA_D07_H01_CI_SOFTWARE_GUI`는 Owner 측에서 강제 해제한다.

## 꼭 봐야 할 터미널 로그

사전 검사:

```text
AXIA_D07_H01_OWNER_PY_VERDICT_STATIC_COMPILE_PASS
AXIA_D07_H01_WATCH_SENTINEL_LIFECYCLE_L0_PASS
AXIA_D07_H01_RENDER_RESOURCE_PROBE_L0_PASS_NO_DISPLAY
AXIA_D07_H01_FAILURE_BUNDLE_L0_PASS
AXIA_D07_H01_OWNER_BOOTSTRAP_STATIC_L0_PASS pinned_private=a9f0d2b6ae1f0dcf2e8f92b263d9b66480924c4e public_l2=43817527534
```

실제 시연 중 기대:

```text
AXIA_D07_GUI_GPU_PREFLIGHT_D3D12_ACCELERATED adapter=NVIDIA
AXIA_D07_GPU_GUI_SERVER_RENDER_ENV_ISOLATED
D07_H01_GUI_WATCHER_SPAWN_ACK_VERIFIED pid=...
D07_H01_GUI_OFFICIAL_PATH_PHASE {... "stage": "before", ...}
D07_H01_GUI_OFFICIAL_PATH_PHASE {... "stage": "intrusion", ...}
D07_H01_GUI_OFFICIAL_PATH_PHASE {... "stage": "restored", ...}
D07_H01_GUI_H01_GEOMETRY_RETURNED_NO_GOAL
```

반드시 눈으로 **Gazebo의 3D 월드·로봇이 실제로 그려지는지**, RViz2 Path가 장애물 삽입 시 바뀌고 복원 후 돌아오는지 확인해야 한다. **로봇은 움직이지 않아야 정상**, 이 데모는 주행이 아니라 `ComputePathToPose` 시각화다.

## 실패나 정상적인 시각 검수 보류

최초 실패는 1) GPU D3D12 사전검사, 2) Gazebo server/official Nav2 준비, 3) GUI watcher spawn ACK, 4) Free marker, 5) `GZ_PARTITION` world topic, 6) GUI 자식 PID/첫 종료, 7) RViz DDS Path subscriber, 8) official Path 3 phase, 9) **화면 픽셀** 순서로 분석한다. 마지막 `FileNotFoundError` 또는 shutdown SIGSEGV는 최초 문제를 가리지 못한다.

Owner 검사기는 화면 장면의 의미를 **자동 확정하지 않도록 fail-closed** 설계돼 있다. 따라서 ROS 3단계 모두 정상이어도 `D07_H01_OWNER_ROS_PATH_L3_VERIFIED_GUI_VISUAL_HOLD`, `D07_H01_OWNER_GUI_VISUAL_HOLD`와 종료 코드 3이 발생할 수 있다. 이는 실제 GPU GUI 장면 승인 전 **정상적인 검수 보류**이며 소스·GUI 동작이 실패했다는 뜻으로 무조건 해석하지 않는다.

원샷에서 `AXIA_D07_H01_OWNER_FIRST_FAILURE_ARCHIVE=<경로>.tar.gz` 및 `<경로>.tar.gz.sha256`가 자동 생성된다. 가용한 원본 GUI XWD, OpenGL/CPU/메모리 진단, 첫 watcher 오류, native ROS/Gazebo/Nav2 소스 원본을 하나의 실행별 폴더로 묶는다. **같은 WSL2 시연을 다시 수행하지 말고 이 두 파일을 첨부**하라. 이후 분석 책임자는 실제 3D 장면과 Node/Evidence TTL을 검토해 인수할 수 있다.

## 검증 등급·Git 정책

- 공개 CI L0: **PASS**.
- 공개 CI 실제 Gazebo/ROS/Nav2/RViz2 + 소프트웨어 Xvfb L2: **PASS**.
- Owner WSL2 NVIDIA D3D12 성능·Gazebo GUI 실제 scene pixels L3: **NOT_RUN/HOLD**.
- CM→Guard 150ms, Scan/Odom 300ms 종단 간 안전 TTL, 주행 Goal, 접촉 안전 인증/하드웨어 E-Stop, Collision Monitor shutdown SIGSEGV: **이 D07 GUI 작업으로 입증되지 않음**.
- `AXIA_MVP_DEMO_ACCEPTED=HOLD`, 사용자 승인 전 instructor/public/student **main 병합 금지**.
- 교육용 보고서: 비공개 instructor의 `training/block_B/instructor/reports/D07_H01_CYCLE15_GPU_GUI_CI_LIFECYCLE_PARITY_RED_GREEN_20261116_KO.md` 및 `D07_H01_CYCLE16_REAL_GAZEBO_L2_OWNER_FINAL_HANDOFF_20261116_KO.md`.

참고: 이 지침은 **추가 GPU 성능 향상을 입증한 문서가 아니다**. 이미 가속 가능한 NVIDIA D3D12 GUI를 안정적으로 검증하기 위한 시연 준비다. 가속 전후 FPS 비교는 Owner 원본 GPU/RTF 계측이 있어야 한다.
