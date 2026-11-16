# AXIA G07 — Owner WSLg GUI 실패 원본 증거·검증된 구형 표시 구조·회귀 복구 보고서

**일자:** 2026-11-16 KST  
**최종 상태:** 공개 L0 GREEN, 실제 Gazebo+RViz2 Xvfb GUI-only L2 PASS, Owner WSLg 실제 픽셀 렌더링 **NOT_VERIFIED**, G07 Goal **NOT_RUN**. `AXIA_MVP_DEMO_ACCEPTED=HOLD`. **인증된 E-Stop 아님.**

## 1. Owner 업로드 실제 원본 및 무결성

- 입력: 강사 WSL2 원본 `axia_g07_rollback_gui_evidence_5aAPfVy9.zip`, SHA256 `4eab5f40dfec0e1ce0f44810aea57cd74362364444d89097bf0bd3eb2434ce3c`.
- ZIP 내 `SHA256SUMS`: **42개 파일 해시 42/42 일치**, missing=0, mismatch=0. 비공개 원본을 공개 GitHub에 올리지 않음.
- 주요 원본:
  - `visual/gz_services.txt`: `/world/default/control`, `/world/default/model/turtlebot3_waffle/link/camera_link/sensor/intel_realsense_r200_depth/depth_image/set_rate` 존재.
  - `visual/monitor.log`: 실제 LiDAR `front_m` 0.5155~0.5300m, Odometry 약 0 수신. `/safety/scan` 센서 전달 중.
  - `G07/startup_verdict.json`: `SMOKE_READY`, `NAV2_ACTION_READY`, `CM_ACTIVE`, 모든 스타트업 단계 PASS, `goal_sent=false`.
  - `visual/gz_models.txt`: **`Service call to [/world/default/state] timed out`** — `gz model --list` 단일 명령 실패, 실제 World 없음의 증거 아님.
  - `visual/gz_gui.log`: `MESA-EGL: warning: Not allowed to force software rendering when API explicitly selects a hardware device.` — 렌더링 강제 정책 충돌 **후보**, GPU 자체 결함/실제 GUI 렌더 실패의 단독 증명은 아님.
  - `visual/rviz.log`: OpenGL 4.6 컨텍스트 초기화. 약 9초 뒤 `SIGTERM`. 스크립트의 8초 `gz model --list` 실패 후 정리와 시간상 일치.
  - `visual/windows.txt`: Xwayland root의 `Weston WM` 등만 기록; 화면에 양쪽 창이 실제 표시됐다는 증거 없음. X11 목록은 Wayland 창을 모두 열거하지 못할 수 있음.
- **근본 원인 분류:**
  1. **증명된 종료 오판**: GUI 스크립트가 `gz model --list` 단독 state RPC 타임아웃을 `WORLD_OR_WAFFLE_TRANSPORT_MISSING`으로 바꾸고 GUI 세션을 즉시 종료. 동시 수집한 World/Waffle 서비스 및 실제 LiDAR와 모순됨.
  2. **렌더링 구성 오류 후보**: 구형 `g07_shared_gui_clients.sh`가 WSLg에도 `LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe`를 강제. 실제 Mesa EGL 장치 선택 경고와 부합하나 변경 후 Owner 화면은 미검증.
  3. **별개 최초 주행 전 이슈**: 과거 Owner `OWNER_PREGOAL_NOT_CLEAR_BEFORE_FIXTURE`는 `front<=.75` 또는 `side<=1.2` 실제 LiDAR 기준 차단. 이번 ZIP의 front 0.52m는 **전방 조건 위반 가능성**을 강하게 지지하나, 이 ZIP은 별도 GUI 전용 시도로 주행 인수 데이터와 합산하지 않는다. 안전 기준 완화 금지.

## 2. 이전 실제 성공 기준선 검색 결과

2026-11-15 public Xvfb **Run [43727149856](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43727149856)**, completed/success:
- private Instructor `01d45d46b6eb6a05b1bd313d73f1fc3549575545`
- public GUI `70f9d4ece5c405cff0fb2d17843391856f3d8c08`
- public RViz/Marker `0f66059d9110f8e667200bbca22396bd0c78c02e`
- Headless Gazebo server, 별도 `gz sim -g`, 별도 `rviz2`, read-only Marker/Scan, 실제 한 Goal CLEAR→SLOW→STOP, Cancel/Shutdown 모두 CI PASS.
- **WSL2/WSLg에서 Gazebo와 RViz2 두 화면이 동시에 보였다는 사용자 캡처 또는 검증된 로그는 이전 GitHub·대화 기록에서 확인되지 않음.** Xvfb를 Owner 화면 성공으로 승격하지 않는다.
- D04 이전 WSLg 렌더링 복구 기록 `training/block_B/reports/D04_OBSERVABLE_PERSON_SCENE_DEBUG_FIX_20261109_KO.md`에서 WSLg 소프트웨어 강제 해제·헤드리스 CI llvmpipe 유지라는 유사 해결 원칙 확인. Gazebo 공식 WSLg/Harmonic 자료 역시 최신 버전에서 강제 소프트웨어 렌더링이 불필요할 수 있다고 설명.

## 3. 롤백·수정 범위 (최소 변경)

- private Instructor 롤백 브랜치 `rollback/g07-gui-20261115-proven-xvfb`: HEAD 정확히 `01d45d46b6eb6a05b1bd313d73f1fc3549575545`, **private 안전 코드 수정 없음**.
- 공개 `rollback/g07-dual-gui-20261115-proven-xvfb`: 2026-11-15 기존 분리 표시 소스에서 새 단위/진단/원샷만 수정. **Cycle36 단일 Gazebo GUI `headless=False` 경로로 되돌리지 않음.**
- `d06/scripts/g07_shared_gui_clients.sh`: **ci/Xvfb일 때에만** `LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe` 유지, Owner WSLg에서 해당 강제 변수를 해제. 기존 `gz sim -g`·`rviz2`·Monitor PID와 `taskset`·`nice` 동일.
- `scripts/axia_g07_rollback_dual_gui_wsl2_no_goal_once.sh`: state CLI 타임아웃으로 GUI를 종료하지 않음. 현재 World 서비스/Waffle 센서 서비스와 ROS scan 수신을 별도 판정, 가시성은 WSLg 실제 확인까지 `UNVERIFIED`. 기존 90초 시각 검증 시간 유지.
- `d06/live/g07_wslg_actual_evidence_contract.py`: 사용자 실제 ZIP의 최소 비민감 관측 정보에 대한 fail-closed 판정기. `--output`은 기존 파일을 덮어쓰지 않음.
- `d06/tests/test_g07_rollback_wslg_actual_evidence_20261116.py`: Owner ZIP 실제 패턴(강제 EGL, 실세계 서비스, LiDAR와 state RPC timeout 동시) 5개 회귀 시험.
- **변경하지 않은 기능:** 공식 Nav2/WAFFLE, Safety Supervisor, Collision Monitor, Base Guard, Guard TTL 150ms, Scan TTL 300ms, 목표 속도, Goal 권한, Fault Injector, G11 custody, 학생용 TODO.

## 4. 공개 CI — RED→GREEN→실제 L2

| 검증 수준 | Run | 결과 | 범위 |
|---|---|---|---|
| 구버전 display rollback L0 | [43869863010](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43869863010) | PASS | 4개 구형 GUI 계약, NO_ROS_NO_GOAL |
| 사용자 업로드 ZIP 회귀 RED | [43879783930](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43879783930) | FAIL 의도 | 새 판정기 없음 + WSLg 강제 소프트웨어 변수 |
| 수정 GREEN L0 | [43880289745](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43880289745) | PASS | 이전 계약 4 + 실제 실패 패턴 5 = **9개**, NO_ROS_NO_GOAL |
| 기존 전체 Goal 재사용 시도 | [43880584904](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43880584904) | FAIL | **`NAVIGATION_STARTUP_UNCLASSIFIED_FAILURE`**, Goal 미전송. GUI 렌더링 전 실패; GUI 성공/실패로 사용 금지 |
| **구형 GUI만 실제 Gazebo 검증** | **[43881687744](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43881687744)** | **PASS** | 실제 `gz sim` World + Waffle 서비스; **별도 Gazebo GUI와 RViz2 두 창 Xvfb 실 표시**, NO_GOAL. 소스 정확한 SHA 고정 |

새 실제 L2 출력 (원본):
```text
Ran 4 tests in 0.001s
Ran 5 tests in 0.003s
AXIA_G07_ROLLBACK_L2_TEST_CONTRACT_9_PASS_NO_ROS_NO_GOAL
AXIA_G07_SHARED_LAUNCH_EXECUTED mode=owner-gui headless=True gui_client_external=1 one_process_group=true goal_not_sent=true
AXIA_G07_ROLLBACK_REAL_GAZEBO_WORLD_WAFFLE_SERVICES_PASS_NO_GOAL
AXIA_G07_ROLLBACK_REAL_TWO_GUI_XVFB_L2_PASS_OWNER_WSLG_NOT_VERIFIED_NO_GOAL
AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false
AXIA_G07_ROLLBACK_GUI_ONLY_L2_CLEANUP_DISPLAY_ONLY_NO_GOAL
```

**검증 한계:** 이 L2는 Ubuntu24 GitHub CI Xvfb로, WSLg/Windows GPU/QT 플랫폼과 동일하지 않음. CI PASS만으로 Owner WSLg 화면이 보인다고 보고 금지. Xvfb 동적 확인과 WSLg 설정 코드/회귀 간 안전 관점의 범위는 명확히 구별.

## 5. 한 번만 Owner WSLg 확인 (Goal 없음)

**정확한 공개 소스 커밋 고정:** `8a43b8ea5c437cb526f940b5b2f08fc6f57eca9c`. 내부에는 native-Wslg display SHA `48d473070d201f4f0a6c9b22510c0ac64c8f59ba`, read-only 진단 SHA `34a122fa1e6e03de45c31864806cd3837226366f`, 실제 private 원본 `01d45d46b6eb6a05b1bd313d73f1fc3549575545`가 고정되어 있다. 유동 main 사용하지 않음.

```bash
(
  set -Eeuo pipefail
  SHA='8a43b8ea5c437cb526f940b5b2f08fc6f57eca9c'
  SCRIPT="$(mktemp)"
  trap 'rm -f -- "$SCRIPT"' EXIT
  curl -fL --retry 3 -sS \
    "https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public/${SHA}/scripts/axia_g07_rollback_dual_gui_wsl2_no_goal_once.sh" \
    -o "$SCRIPT"
  bash -n "$SCRIPT"
  bash "$SCRIPT" --self-check
  bash "$SCRIPT"
)
```

WSL2에서 직접 보이는 두 창 및 렌더링 품질은 사용자 현장 한 번의 시각 검수만으로 확인. `AXIA_G07_ROLLBACK_OWNER_NATIVE_WSLG_RENDERER_ENV_NO_SOFTWARE_FORCE`는 새로운 환경 설정 경로의 적용 증거이지 화면 픽셀 성공이 아니다.

현장 원본: `~/axia_g07_rollback_gui_evidence_*/visual/gz_gui.log`, `rviz.log`, `sidecar.log`, `gazebo_transport_review.json`, `gz_services.txt`, `gz_models.txt`, `initial_scan_before_fixture.json`, `SHA256SUMS`. 첫 타이밍 위반과 최초 GUI 프로세스/렌더러 오류만 검토, 무의미한 재시도 금지.

## 6. 후속 개발 복구 계획

구형 GUI 정상화가 Owner WSLg에서 시각적으로 입증되기 전에는 G07 새 Goal·G11 확대·새 CM/Guard/CPU 최적화 금지. GUI 인수 시 이후 단계에서만 Cycle36의 검증된 안전·주행 코드를 **별도 feature 브랜치에서 필요한 부분만 선택 재사용**, 최소 공개 CI 재검증 후 Owner L3 단일 검수. `main` 병합은 사용자 승인 전 금지.
