# AXIA G07 — 2026-11-15 정상 GUI 구조 롤백 및 현장 최초 오류 분리 보고서

작성: 2026-11-16 KST. 범위: **Gazebo·RViz2 GUI 복구 최우선, NO_GOAL 진단만**. TurtleBot3 Waffle, ROS 2 Jazzy, Gazebo Harmonic, 공식 Nav2 유지. 기존 Safety Supervisor/CM/Guard/150ms TTL, 인증 E-Stop 불변. `AXIA_MVP_DEMO_ACCEPTED=HOLD`. main 병합 **금지**.

## 1. 임의 SHA가 아닌 마지막 양쪽 GUI *실행 근거*

- 공개 GitHub Actions **Run [43727149856](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43727149856)**, 2026-11-15, completed/success.
- 검증된 Instructor `01d45d46b6eb6a05b1bd313d73f1fc3549575545`. 공개 workflow `fa05a437db3b55d3e5e242322a4b66b7f71ae601`. 공개 분리형 GUI 실행기 `70f9d4ece5c405cff0fb2d17843391856f3d8c08`. RViz/Marker 시각화 소스 `0f66059d9110f8e667200bbca22396bd0c78c02e`.
- 당시 Xvfb에서 실제 Gazebo GUI와 RViz2 **두 윈도우가 동시에 표시**, 동일 Goal 구간 Marker·Scan 수신. `CLEAR→SLOW→STOP`, `ODOM_DWELL=1.011s`, source 최대 67.902ms, CM 110.964ms, guard 51.892ms, scan 199.431ms, 정상 Nav2/CM 종료.
- **이 증거는 Ubuntu GitHub Actions/Xvfb**이다. 강사 **WSL2/WSLg 실제 픽셀 렌더링이 정상적이었다는 원본 캡처는 찾지 못했다**. 따라서 `WSLG_VERIFIED=false`를 변경하지 않는다.

## 2. GUI 두 프로세스 구조의 정확한 차이

**구형 실제 CI PASS 소스:**
```text
official Nav2/Gazebo server (headless:=True, GZ_PARTITION isolated)
  ├─ official world + TurtleBot3 Waffle + ROS safety graph
  ├─ separate display-only gz sim -g (nice19, taskset renderer CPU)
  ├─ separate display-only rviz2 -d d06_safety_bubble.rviz (nice19)
  └─ read-only MarkerArray monitor (nice15)
```

**Cycle36 현장 실패 소스** private `2b59c1a74513ac5a5b80c5bd424001a625c07617` / public GUI `132d8c64def534061d3467f3e1a339fbb44e3e68`:
- `axia_g07_shared_launch mode=owner-gui headless=False`, 통합 공식 Gazebo GUI 한 개.
- `G07_CYCLE36_INTEGRATED_GUI_NO_EXTERNAL_GZ`, 이후 `D06_RVIZ_STARTED ... gz_pid=`(빈 값)은 코드가 **의도적으로 외부 GUI를 띄우지 않았기 때문**. 이것만으로 내부 Gazebo GUI의 WSLg 렌더링 성공도 실패도 증명하지 못한다.
- `G07_CYCLE36_WORLD_ENTITY_REAL_GAZEBO_PASS`는 transport 세계·Waffle 존재 확인일 뿐 GUI 픽셀 증거가 아니다.
- Cycle36 CI Run [43863443121](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43863443121) **실제 시뮬레이션**과 7채널은 PASS였지만 사용자 WSLg 렌더링이 정상일지는 검증하지 않았다.
- 따라서 최근 CPU affinity, GUI PID matcher, world-position 수정의 원인 추측을 더 늘리기보다 **GUI 실행 토폴로지를 분리형 구버전으로 롤백**한다.

## 3. 현장 최초 실패: GUI와 독립된 NO_GOAL LiDAR 문제

2026-11-16 현장:
```text
AXIA_G07_OWNER_PREGOAL_PHYSICAL_L2_BLOCKED RuntimeError:OWNER_PREGOAL_NOT_CLEAR_BEFORE_FIXTURE
P2_L3_OWNER_STATUS=BLOCKED_G07_COMMON_PREG0AL_NO_GOAL
```
원본 private `tools/p2_g07_owner_pregoal_l2.py`는 이동 전 실제 `/safety/scan`의 `front_m>0.75` **그리고** `side_m>1.20` 모두를 요구한다. 두 값 중 하나가 이하이면 이동 전 차단한다. 이 지점 이전에 G07 Goal은 전송되지 않았다.

현장 로그에는 두 값이 **출력되지 않아**, 최초 실패 조건을 아직 특정할 수 없다. 이는 새 장애물 위치 `(-2.12,0.24)`로 이동한 뒤의 문제가 아니라 **이동 이전 기준선**의 실제 관측 실패다. `0.75/1.2m` 기준을 낮추거나 테스트 성공을 조작하지 않는다.

별도 읽기 전용 `d06/live/g07_precycle36_readonly_preclear_probe.py`는 동일한 원래 LiDAR bearing `atan2(.75,.19)`, 전방 ±0.18rad, 측면 ±0.12rad에서 **fixture 이동 전에 실제 최소값**을 기록하고, `GOAL=false, gazebo_entity_moved=false`로 표기한다. 이 값은 UI 렌더링 판정에 영향을 주지 않는다. 카메라/그래픽 장애로 오진하지 않는다.

## 4. 손대지 않은 코드를 가리키는 독립 롤백 브랜치

- 비공개 Instructor **`rollback/g07-gui-20261115-proven-xvfb`**, HEAD `01d45d46b6eb6a05b1bd313d73f1fc3549575545`. 당시 검증된 원본 소스 그대로, **Goal/Guard/CM 코드 변경 없음**.
- 공개 CI **`rollback/g07-dual-gui-20261115-proven-xvfb`**, 출발 HEAD `70f9d4ece5c405cff0fb2d17843391856f3d8c08`. 새로운 **NO_GOAL 진단·시작 스크립트·단위 시험·보고서만 추가**, 기존 `d06/scripts/g07_shared_gui_clients.sh` 수정 없음.
- 본 테스트에서 절대 `main`이나 기존 `release/p2-g06-cm-ttl-20261110`의 구현 경로를 롤백하지 않는다. 구형 정상 인수 SHA를 새로운 통합 SHA로 덮어쓰지 않는다.

## 5. 공개 CI RED→GREEN 및 실제 검증 범위

- 기존 구조의 왜곡 후보: Cycle36 integrated GUI와 별도 GUI 중복 제거를 하나로 취급함. 구형 baseline의 **분리 GUI 계약**은 현재 소스에는 존재하지 않는다.
- 새 순수 계약 `d06/tests/test_g07_precycle36_dual_gui_rollback_contract.py`는 구형 `setsid ... gz sim -g` + `setsid ... rviz2` + `headless_server_required=true`를 동시에 요구한다. Cycle36 클라이언트의 `AXIA_G07_CYCLE36_INTEGRATED_GUI` 경로를 허용하지 않는다.
- 공개 CI Run **[43869221772](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43869221772)**: 4 unit tests `Ran 4 tests ... OK`, old Instructor `AXIA_G07_UNIFIED_GUI_SIDECAR=1 → headless=True` 계약, Bash 문법, 과거 Run `43727149856` 성공 head_sha 검증 **PASS**.
- 이 CI는 **L0 NO_ROS_NO_GOAL**이다. 실제 두 GUI 동시 렌더링의 동적 ROS/Gazebo 인수는 이전 Run `43727149856`을 재사용한다. 강사 WSLg GUI 화면은 **미검증**.

## 6. Owner GUI 한 번 진단 — Goal 없이만 실행

공개 독립 복구 스크립트 `scripts/axia_g07_rollback_dual_gui_wsl2_no_goal_once.sh`는 아래 시도에서 SHA별로 고정 clone, ROS Jazzy/Gazebo official world/waffle 재사용, headless server + **별도 `gz sim -g`와 RViz2**를 실행한다. `YES-P2-G07-GOAL` 요구·전송이 없고, rosbag 14-topic/G11 custody나 Crash 기능도 건드리지 않는다.

```bash
(
  set -Eeuo pipefail
  SHA='3b8bc1ed4554c2d7d3a5c8d0caee9baa73a662a7'
  SCRIPT="$(mktemp)"
  trap 'rm -f "$SCRIPT"' EXIT
  curl -fL --retry 3 -sS \
    "https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public/${SHA}/scripts/axia_g07_rollback_dual_gui_wsl2_no_goal_once.sh" -o "$SCRIPT"
  bash -n "$SCRIPT"
  bash "$SCRIPT" --self-check
  bash "$SCRIPT"
)
```

강사 WSLg 실제 화면에서 **Gazebo와 RViz2가 각각 표시되는지** 확인할 필요가 있다. `AXIA_G07_GUI_OBSERVE_SEC=90` 기본 자동 표시·종료 구간이며 원본 로그를 삭제하지 않는다. 화면 캡처는 CI에서 대체하지 않는다.

증거: `~/axia_g07_rollback_gui_evidence_*/visual/rviz.log`, `gz_gui.log`, `windows.txt`, `display_attestation.json`, `initial_scan_before_fixture.json`, `G07/launch.log`, `SHA256SUMS`.

아직 확인되지 않은 결과를 성공이라고 표기하지 않는다. **새 원샷은 실제 /world/control 서비스 및 Waffle 모델 목록을 GUI와 별개로 확인하며, `gz_services.txt`·`gz_models.txt`도 원본에 남긴다. WSLg 픽셀 확인이 빠졌다면 transport 성공만으로 GUI PASS라고 하지 않는다.\n\nGUI 원복 검증이 완료되기 전에는 G07 Goal 주행 재시도·CPU 추가 튜닝·acceptance gate 완화·main 병합 금지**.
