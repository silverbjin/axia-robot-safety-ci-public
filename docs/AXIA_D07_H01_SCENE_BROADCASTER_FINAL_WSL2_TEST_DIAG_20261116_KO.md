# AXIA Block B D07-H01 — SceneBroadcaster 수정 후 WSL2 최종 검수·증거 진단

작성일: 2026-11-16 · **ROS 2 Jazzy + Gazebo Harmonic + 공식 Nav2**, 정지 TurtleBot3 Waffle. 이동 Goal·`cmd_vel` 없음.

## 왜 이 스크립트인가?

이전 Owner `hzsMGW9l`은 ROS·LiDAR·Costmap·공식 Path Before→Intrusion→Restored 모두 성공했으나 **Gazebo 3D와 Entity Tree가 비어 있었음**. 기존 official world의 `<xacro:unless value="$(arg headless)">`가 `SceneBroadcaster`를 감싸는데, 시연은 `headless:=True`로 서버를 시작한 뒤 GUI 전용 `gz sim -g`를 연결하였음.

D07-only 임시 world `d07_gui_scene_world.sdf.xacro`에서 조건부 wrapper만 제거하여 **한 개의** `SceneBroadcaster`를 headless 상태에서도 로딩하도록 수정. Gazebo는 server scene/pose 토픽을 발행; ROS Path/Baseline 복원 동작 유지. 기존 world와 다른 G07/moving Goal, Safety Supervisor/Collision Monitor/Guard, sensor/TTL 변경 없음.

## 공개 CI 검증 완료

| 레벨 | 정확한 근거 | 판정 |
|---|---|---|
| RED 원인 재현 | [#43863710042](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43863710042) | 이전 코드에서 신규 scene world overlay 계약 FAIL |
| L0 GREEN | [#43864349909](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43864349909) | 원본 headless Xacro 조건부 해제·안전 스코프 테스트 3개 PASS |
| 실제 Gazebo·ROS/Nav2/RViz2 L2 | **[#43866354976](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43866354976)** (workflow SHA `6b409a59dbd7c030efab5bac0a896a60f680d66e`) | **PASS**: `headless:=True` 최종 확장 SDF의 SceneBroadcaster 1개, 실제 `/world/default/scene/info`·`pose/info` 토픽, 3단계 공식 Nav2 Path |
| 최종 Owner script·압축 진단 L0 | [#43867151072](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43867151072) (workflow SHA `c8b81783a992dbc33e9300884e8e6dcbc4b163b0`) | **PASS**; checksum·토픽 누락·첫 GUI failure failclosed 포함 |

L2에서 확인된 실제 메시지:

```text
D07_H01_GUI_RUNTIME_RC=0 RVIZ_X11=1 GAZEBO_X11=1
D07_H01_REAL_XACRO_HEADLESS_SCENE_BROADCASTER_CONFIRMED
D07_H01_REAL_GAZEBO_RUNTIME_SCENE_TOPICS_CONFIRMED
D07_H01_GUI_NO_MOVING_GOAL_L2_PASS
```

**CI의 Xvfb 소프트웨어 렌더링은 WSLg NVIDIA D3D12의 실제 GUI 픽셀 합격이 아님.** 사용자는 마지막 WSL2 육안 확인 1회만 수행.

## 1) Owner WSL2 실제 인수 테스트 — 터미널 하나에 전체 붙여넣기

Ubuntu 24.04, WSL2/WSLg, NVIDIA D3D12를 사용하는 기존 PC에서 이전 시연을 종료한 뒤 **한 번만 실행**.

```bash
(
  set -Eeuo pipefail
  SHA="1b252d4a06330a64c13370bdc82b25c94d3ac0de"
  SCRIPT="$(mktemp)"
  trap 'rm -f -- "$SCRIPT"' EXIT
  curl -fL --retry 3 -sS \
    "https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public/${SHA}/scripts/axia_d07_h01_gpu_gui_owner_wsl2_once.sh" \
    -o "$SCRIPT"
  bash -n "$SCRIPT"
  bash "$SCRIPT" --self-check
  bash "$SCRIPT" --run
)
```

실행 코드는 private source **`c069052cc491117006f63b499577ef766a30f7ea`**, Gazebo L2 Run **`43866354976`**로 고정되어 있음. WSL2 셸에서 `~/.bashrc`에 GPU 변수를 다시 추가할 필요 없음. 기존 공개 CI와 같은 서버·Nav2·Watcher 구현을 실행하고 **WSLg GUI 프로세스에만** D3D12 NVIDIA 설정. `AXIA_D07_H01_CI_SOFTWARE_GUI` 값은 Owner에서 강제로 제거.

기대되는 주요 로그:

```text
AXIA_D07_H01_OWNER_BOOTSTRAP_STATIC_L0_PASS pinned_private=c069052cc491117006f63b499577ef766a30f7ea public_l2=43866354976
AXIA_D07_GUI_GPU_PREFLIGHT_D3D12_ACCELERATED adapter=NVIDIA
D07_H01_SCENE_BROADCASTER_WORLD_READY_NO_GOAL overlay_sha256=<SHA256>
D07_H01_GUI_WATCHER_SPAWN_ACK_VERIFIED pid=<PID>
D07_H01_GUI_SERVER_WORLD_DISCOVERED_NOT_GUI_RENDER_PROOF world=default
D07_H01_GUI_OFFICIAL_PATH_PHASE {"stage":"before", ...}
D07_H01_GUI_OFFICIAL_PATH_PHASE {"stage":"intrusion", ...}
D07_H01_GUI_OFFICIAL_PATH_PHASE {"stage":"restored", ...}
D07_H01_GUI_H01_GEOMETRY_RETURNED_NO_GOAL
```

**육안 인수 기준**: Gazebo **Entity Tree에 world/robot이 실제로 나오는지**, Gazebo 3D에 TurtleBot3 Waffle·장애물·환경이 실제로 보이는지 확인. RViz2는 공식 Path가 Intrusion에서 바뀌고 Restored에서 돌아오는지 확인. 로봇은 **움직이지 않아야 정상**(자율주행 시연이 아니라 경로 재계획 가시화). 사용자가 화면을 확인해야 하는 이유는 X11 창 제목/장면 토픽/임의 XWD 파일만으로 Gazebo 3D 픽셀 정상임을 입증할 수 없기 때문.

**`D07_H01_OWNER_GUI_VISUAL_HOLD`는 정상적인 안전한 검수 보류 판정**. Path·토픽이 모두 성공해도 자동 L3 합격으로 처리하지 않으며, 실제 화면이 비었다면 그대로 HOLD로 남긴다. 실행 종료시 `AXIA_D07_H01_OWNER_FIRST_FAILURE_ARCHIVE=<...>.tar.gz`와 같은 경로의 `.tar.gz.sha256`를 자동 생성.

## 2) 자동 수집된 원본 압축자료의 읽기 전용 진단 — ROS/Gazebo 재실행 없음

원샷 출력에 나온 tar.gz의 경로를 `ARCHIVE`에 입력하고 실행한다. 이 도구는 **읽기만 하며** Xacro·토픽·SHA256·XWD 유무를 판별, Nav2/Gazebo·Goal을 절대 실행하지 않는다.

```bash
(
  set -Eeuo pipefail
  SHA="1b252d4a06330a64c13370bdc82b25c94d3ac0de"
  ARCHIVE="$HOME/.axia_d07_h01_owner_evidence/여기에_실제_d07-h01-owner-XXXX.tar.gz"
  SCRIPT="$(mktemp --suffix=.py)"
  trap 'rm -f -- "$SCRIPT"' EXIT
  curl -fL --retry 3 -sS \
    "https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public/${SHA}/scripts/axia_d07_h01_scene_archive_diagnose.py" \
    -o "$SCRIPT"
  python3 "$SCRIPT" --archive "$ARCHIVE"
)
```

결과의 의미:

- `D07_H01_SCENE_SOURCE_AND_TRANSPORT_VERIFIED`: 해당 source의 SceneBroadcaster와 실제 서버 publishers 및 watcher, XWD 수집을 **증거로 확인**. 그러나 `gazebo_3d_scene_render_proven=false`·`owner_wsl2_gui_l3_accepted=false` 유지.
- `SCENE_BROADCASTER_RUNTIME_TOPICS_MISSING`: 소스에 플러그인이 있지만 실제 서버에서 scene/pose 퍼블리셔가 발견되지 않음. GUI/WSLg GPU의 잘못이라고 조기에 단정하지 않음.
- `FINAL_D07_SCENE_WORLD_NOT_PROVEN`: 임시 world·manifest/SHA256 계약 불일치.
- `GAZEBO_GUI_CHILDREN_NOT_PROVEN`, `GUI_XWD_CAPTURE_ABSENT`, `SHA256_SIDECAR_MISSING_OR_MISMATCH`: 최초 증거 경계 별도.
- `OWNER_GUI_SCENE_PIXEL_REVIEW_PENDING`: 유효한 ROS·장면 데이터 증거 뒤 **실제 WSLg 3D 시각 검수만 남음**.

증거: `real-l2/d07_gui_scene_world.sdf.xacro`, `d07_gui_scene_world_manifest.json`, `d07_gui_transport_topics.txt`, `d07_gui_watcher.log`, `gui_diagnostics/ogre2_gui.log`, `gazebo_scene_late.xwd`, `rviz_scene_late.xwd`, `owner_l3_verdict.json`.

## 3) 추가 결함이 나오면

현장 동일 실행을 반복하지 않는다. 생성된 tar.gz + `.sha256`만 제출하면 다음 **최초 실패 경계**를 기준으로 CI RED→GREEN:

1. 실제 임시 world Xacro 최종 확장과 SceneBroadcaster 하나
2. 실제 Gazebo SceneBroker publisher, world/robot entity 여부
3. GUI watcher PID/child exit·동일 GZ_PARTITION
4. Ogre2 D3D12 GL 셰이더 / GUI scene pixels / RViz GLSL / WSLg CPU·GPU
5. 공식 Path before/intrusion/restored 및 ROS `/scan` 주기; 다른 Safety TTL은 별도 증거로 검증

만약 scene topics까지 확인됐는데 GPU GUI가 비면, 그때만 **WSLg NVIDIA D3D12 Ogre2 렌더링 호환성** 가설을 별도로 검증한다. 사용자에게 불필요한 드라이버 재설치나 `~/.bashrc` 전역 설정 변경을 요구하지 않는다.

## 4) 판정과 Git

L0 PASS, 실제 Gazebo SceneBroadcaster+Nav2 L2 PASS, **WSL2 NVIDIA GPU UI 픽셀 L3 NOT_RUN/HOLD**, 전체 `AXIA_MVP_DEMO_ACCEPTED=HOLD`. 기존 Safety Supervisor/CollisionMonitor CM→Guard 150ms·Scan/Odom 300ms 종단 간 TTL, 실제 E-Stop 및 Moving Goal은 이번 D07에서는 검증하지 않았다. SW 정지와 인증된 E-Stop은 다르다.

강사 정답은 비공개 `silverbjin/axia-robot-safety-instructor`; 학생 TODO는 별도 `silverbjin/axia-robot-safety-student`; **main 병합 없음**. 교육용 개발 보고서 `training/block_B/instructor/reports/D07_H01_CYCLE18_HEADLESS_SCENE_BROADCASTER_RED_GREEN_L2_20261116_KO.md` (private commit `2026b514002e7b2290fa7f1716ab103fcc5d75a2`).
