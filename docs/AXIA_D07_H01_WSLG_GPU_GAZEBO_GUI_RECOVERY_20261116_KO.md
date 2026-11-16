# AXIA D07-H01 — WSLg GPU 가속·Gazebo GUI 연결 문제 해결 가이드

작성: 2026-11-16 · ROS 2 Jazzy / Gazebo Harmonic / 공식 Nav2 · stationary TurtleBot3 Waffle · **NO MOVING GOAL**

## 결론과 제한

실제 Owner ZIP/cNAPf8A0에서 Gazebo 서버 `Entity creation successful`, Scan/Odom/Costmap 및 공식 Before/Intrusion/Restored Path 3단계는 PASS. 동시에 Ogre2 로그 `Device Name: llvmpipe`, CPU 평균 부하 높음, 사용자 화면의 Gazebo GUI/Entity Tree가 비었음을 확인했다. Windows RAM 32GB 중 WSL 15.48GiB/가용 13GiB 이상으로 RAM 병목 증거는 없다.

**시각적 실패 원인은 GPU 소프트웨어 렌더링과 Gazebo GUI↔서버 전송 문제를 분리해야 한다.** 기존 `scripts/p2_no_goal_smoke_ci.sh`의 GUI 경로는 `LIBGL_ALWAYS_SOFTWARE=1`을 설정하므로 WSL2 셸에서 `unset LIBGL_ALWAYS_SOFTWARE`만 실행해도 근본적 해결이 되지 않는다.

이번 변경은 강사용 private 기능 브랜치의 GUI 자식 프로세스에만 조건부 GPU 활성화를 추가했다. 기존 Gazebo 서버, Nav2, Scan QoS, Safety Supervisor, Guard, CM/TTL 및 공식 SDF는 불변. **가속 GPU 시각 PASS를 CI L0로 위조하지 않는다.**

## 1. GPU만 먼저 확인 (ROS/Gazebo 실행 전, WSL2)

Ubuntu 24.04 터미널에서 GPU가 NVIDIA RTX 2060으로 선택되는지 검사:

```bash
env -u LIBGL_ALWAYS_SOFTWARE \
  MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA \
  glxinfo -B | grep -E 'Device:|Accelerated:|OpenGL renderer string|OpenGL (core profile )?version string'
```

정상 후보 (실측 출력 아님):

```text
Device: D3D12 (NVIDIA GeForce RTX ...)
Accelerated: yes
OpenGL renderer string: D3D12 (NVIDIA GeForce RTX ...)
```

`llvmpipe`/Accelerated:no이면 기존처럼 CPU 렌더링이다. NVIDIA 선택이 불가한 경우 동일 명령의 `NVIDIA`만 `Intel`로 변경하여 Iris Xe 후보를 한 번 비교할 수 있다. **실제 GPU가 없다는 결론은 금지** (`/dev/dxg`와 Windows 어댑터가 이미 존재).

`glxinfo` 미설치 시 Ubuntu `sudo apt-get update && sudo apt-get install -y mesa-utils`로 진단 도구만 설치한다. Mesa D3D12가 안 되면 Windows NVIDIA/Intel 그래픽 드라이버 및 WSLg 업데이트를 먼저 검토한다. Windows에서 시연이 종료된 뒤에만 `wsl --update`, `wsl --shutdown` 후 새 셸에서 재검증한다. Linux용 NVIDIA 드라이버를 WSL에 임의 설치하거나 `~/.bashrc`에 GPU 변수를 영구 기록하지 않는다.

## 2. GPU·Gazebo 연결 통합 Owner 원샷 (새 GUI 후보)

새 GPU GUI 후보는 기존 read-only 강사 source와 **다른 SHA**이므로 기존 공개 L2 성공으로 승인하지 않는다. 실제 GUI 육안 인수 HOLD를 유지한다.

```bash
(
  set -Eeuo pipefail
  SHA='40a1712fed562dd93e98e8bf4952bde5938120dd'
  SCRIPT="$(mktemp)"
  trap 'rm -f -- "$SCRIPT"' EXIT
  curl -fL --retry 3 -sS \
    "https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public/${SHA}/scripts/axia_d07_h01_gpu_gui_owner_wsl2_once.sh" -o "$SCRIPT"
  bash -n "$SCRIPT"
  bash "$SCRIPT" --self-check
  bash "$SCRIPT" --run
)
```

기본 GPU 후보: NVIDIA. Windows Intel을 쓸 때에만 같은 스크립트 앞에 `AXIA_D07_H01_GPU_ADAPTER=Intel`을 지정한다. **하드웨어 GLX preflight가 D3D12·Accelerated yes를 동시에 만족하지 못하면 ROS/Gazebo 시작 전 fail-closed**. 이 상태에서는 반복 시연하지 않는다.

강사 pinned source: `8e9445315c5f503b628ca381b1152b35da1db1fa` (`feat/d07-h01-wslg-gpu-gui-trial-20261116`).

사용 범위: `AXIA_D07_H01_GPU_GUI_TRIAL=1`, `AXIA_D07_H01_GUI_NO_GOAL=1`, moving Goal 비허가, Gazebo Harmonic GUI-only `gz sim -g -v 4` 및 `rviz2`에만 `env -u LIBGL_ALWAYS_SOFTWARE MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA` 적용. 기존 Gazebo 서버 측 GPU-LiDAR/물리 시뮬레이션의 소프트웨어 설정은 변하지 않음. 이전 GUI-only 기본 분기는 여전히 `gz sim -g &` 그대로 유지.

## 3. GUI 서버 연결 선행 검증

Geometry가 실제 Free Path 안정쌍과 marker를 작성한 **후** `gz sim -g`를 실행하기 전에 다음이 자동 수행된다:

```bash
echo "D07_H01_GUI_TRANSPORT_PARTITION=$GZ_PARTITION"
timeout 10s gz topic -l > <RUN>/real-l2/d07_gui_transport_topics.txt
grep -E '^/world/[^/]+/(pose/info|dynamic_pose/info|scene/info|state)$' \
  <RUN>/real-l2/d07_gui_transport_topics.txt
```

실제 로그 기대:
- `D07_H01_GUI_SERVER_WORLD_DISCOVERED_NOT_GUI_RENDER_PROOF`: 서버/world 토픽 검색 성공. **GUI 장면 픽셀은 별도**.
- `D07_H01_GUI_TRANSPORT_NO_WORLD_DISCOVERED`: server/world 전송을 발견하지 못함. GUI 기동 전에 HOLD. `GZ_PARTITION`과 서버/GUI `/proc/PID/environ`의 값부터 대조해야 한다.
- 토픽은 발견되나 빈 GUI: Ogre2 렌더링/WSLg/scene GUI plugin 문제. `d07_gui_watcher.log`, XWD GUI 프레임, `~/.gz/rendering/ogre2.log`를 분석한다.

WSL2 테스트에서는 GUI 창이 보여도 `D07_H01_OWNER_GUI_VISUAL_HOLD`를 유지하고 자동 archive(<RUN>.tar.gz + .sha256)를 생성한다. 파일 내 `gpu_glxinfo_unforced.txt`, `d07_gui_transport_topics.txt`, `gui_diagnostics`의 XWD·자원/GLX/Ogre 로그와 원본 ROS 단계 결과를 동시에 제출한다. 실제 화면 확인 없이 GUI 인수 PASS로 승격하지 않는다.

## 4. D3D12는 정상인데 Gazebo가 여전히 비어 있을 때

1. 하드웨어 GLX에서 `D3D12`·`Accelerated: yes`와 core OpenGL 버전을 확인한다. Gazebo Ogre2는 공식적으로 OpenGL 3.3보다 높은 버전(가급적 4.3 이상)이 권장된다. D3D12가 3.3으로만 나타나면 Ogre2 호환성을 단정할 수 없다.
2. 별도로 Gazebo가 제공하는 단순 `shapes.sdf`를 **분리된 파티션**에서 검증하고 GUI 렌더링 실패가 AXIA launch에만 발생하는지 구분한다. 기존 AXIA 주행과 동시에 두 번째 Gazebo 서버를 시작하지 않는다.
3. 공식 Gazebo Harmonic 문제해결 문서의 Ogre1 fallback `gz sim shapes.sdf --render-engine ogre`를 **단일 별도 샘플**로 실험할 수 있다. 검증 전 AXIA 센서 서버나 Nav2에 Ogre1을 전역 적용하지 않는다.
4. 소프트웨어 렌더링 강제 해제 후 Nav2/Gazebo GUI 오류가 있으면 기존 안전한 기본 모드로 되돌리고, 첫 장면 실패를 CI 원인 재현 가능한 형태로 편입한다. 환경만 바꿔 무분별하게 시연을 반복하지 않는다.

## 5. 증거/CI 검증 범위와 Git

- Private RED test: `tests/unit/test_d07_h01_gpu_gui_trial.py` SHA `e24994efd563bf85320f425dede9ab477a89371b`.
- Private GREEN: `scripts/p2_no_goal_smoke_ci.sh` SHA `8e9445315c5f503b628ca381b1152b35da1db1fa`.
- PUBLIC owner GPU opt-in new runner: `scripts/axia_d07_h01_gpu_gui_owner_wsl2_once.sh` exact public source SHA `40a1712fed562dd93e98e8bf4952bde5938120dd`.
- 공개 GREEN 기존 sealed release [#43807844152](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43807844152): private opt-in GUI tests 3건, public pinned owner selfcheck 2건 포함 PASS; source pin 기존 release workflow commit `8f0c7bf483e0be8adaa5d0ae51d9c336d7d3a81e`.
- 새로운 feature-only 독립 workflow는 저장소 environment 권한 또는 runner 단계 문제를 명확히 읽지 못해 실패함. 성공했다고 보고하지 않으며, 이미 통과한 release L0를 검증 기준으로 사용한다.
- **WSLg GPU 가속 실측, Gazebo GUI 3D 실제 장면, GPU 모드 Gazebo L2/Owner L3는 NOT_RUN/NOT_VERIFIED.** 이전 #43793585641은 이전 software GL 인수로서 이번 GPU GUI 후보의 L2 성공이 아니다.
- `main` 병합 없음, 강사용 정답 private, 학생 TODO 별도 public. `AXIA_MVP_DEMO_ACCEPTED=HOLD` 유지.

공식 참고:
- https://github.com/microsoft/wslg/wiki/GPU-selection-in-WSLg
- https://gazebosim.org/docs/harmonic/
- https://gazebosim.org/docs/harmonic/troubleshooting
