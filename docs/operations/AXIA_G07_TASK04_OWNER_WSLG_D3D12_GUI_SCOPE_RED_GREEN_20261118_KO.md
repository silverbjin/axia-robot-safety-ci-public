# AXIA G07 Task04 — WSLg D3D12 환경변수 범위 격리 교육용 원인 분석 보고서

- 작성일: 2026-11-18 KST
- 목적: Task04 Owner Moving Goal L3 출고 전, 실제 WSLg 렌더링 분리 기준과 현재 원샷 소스의 차이를 점검한다.
- **확인된 사실과 가설의 구분:** 기존 Owner 원샷의 `GALLIUM_DRIVER=d3d12` 전역 export는 소스상 확인되었다. 이것이 실제 CM/Scan 타이밍 위반을 일으켰다는 **현장 실패 증거는 없다.** 이번 수정은 검증된 기존 D07 GUI 실행 경계와 일치시키는 예방적 최소 조치다.
- 마지막 실제 L2 성공 기준: 공개 CI [#44264236859](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44264236859), Student SHA `486ec02e8e0762e9abefd3063b5d25b2ff5f1fb8`. 해당 SHA의 성공을 새 수정 SHA에 임의 승격하지 않는다.

## 1. 시니어 소스 감사: 첫 번째 위험 경계

기존 공개 CI Owner 스크립트 `scripts/axia_g07_task04_owner_moving_l3_once.sh`의 GLX 검증 직후 다음 설정이 전역 export돼, 그 뒤 **Gazebo 서버를 포함한** 자식 프로세스에 상속될 가능성이 있었다.

```bash
export GALLIUM_DRIVER=d3d12 MESA_D3D12_DEFAULT_ADAPTER_NAME="$GPU"
```

반면 이미 개발돼 있던 Student `block_B/day07/h01_runtime/scripts/p2_no_goal_smoke_ci.sh`의 `AXIA_D07_H01_GPU_GUI_TRIAL` 분기는 `env -u LIBGL_ALWAYS_SOFTWARE GALLIUM_DRIVER=d3d12 MESA_D3D12_DEFAULT_ADAPTER_NAME=...`를 `gz sim -g`/RViz2 GUI **자식에게만** 전달한다. Gazebo 서버·LiDAR·공식 Nav2의 전체 실행 환경은 그대로 유지한다.

- Gazebo Harmonic 공식 서버/GUI 분리 근거: https://gazebosim.org/docs/harmonic/architecture/ 및 https://gazebosim.org/docs/harmonic/getstarted/
- Mesa 공식 환경변수: https://docs.mesa3d.org/envvars.html
- Mesa D3D12 드라이버 어댑터 선택: https://kusma.pages.freedesktop.org/mesa/drivers/d3d12.html

**가설:** 기존 NO_GOAL GUI에서 검증했던 자식 프로세스 범위를 Owner Moving Goal에도 동일하게 적용하면, WSLg D3D12 선택이 물리 엔진·GPU LiDAR·안전노드의 렌더링 환경까지 간섭할 위험을 줄일 수 있다. 이것은 스케줄링 성능 향상을 입증한 주장이 아니다.

## 2. 최소 RED

- Student 최초 회귀 테스트 커밋: `b8b9536c3461e1086bdd1c388414e4e331d39a3e`
- Python 테스트: `block_B/day07/h01_runtime/tools/test_g07_task04_owner_gui_d3d12_isolation.py`
- 공개 CI RED: [Run #44268569294](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44268569294)
- 실측 결과: 두 테스트 중 **Owner GUI 자식 전용 D3D12 경로 부재로 1 FAIL**, 기존 CI GUI 경로 유지 1 PASS.
- 별도 Owner 원샷 RED: 공개 CI 테스트 `tests/test_g07_task04_owner_moving_bootstrap.py`에 환경변수 하위 프로세스 범위 검사 추가.
- 공개 Bootstrap [Run #44268578301](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44268578301): 6개 중 새 분리 검사 1 FAIL.
- RED는 ROS/Gazebo를 실행하지 않는 L0 계약 검사이며, WSLg 타이밍 장애가 실제로 발생했다는 증거로 해석하면 안 된다.

## 3. GREEN — 최소 연결부만 수정

- Student 수정 커밋: `d7ffec1ce73f0c4e672ea0fc51a1678139dc5a6f`
- 수정 파일: `block_B/day07/h01_runtime/scripts/p2_no_goal_smoke_ci.sh`
- Owner에서만 이미 GLX 확인된 어댑터가 NVIDIA/Intel인지 제한하고, `gz sim -g` 및 `rviz2` 자식 실행 시 `env -u LIBGL_ALWAYS_SOFTWARE GALLIUM_DRIVER=d3d12 MESA_D3D12_DEFAULT_ADAPTER_NAME=...`를 각각 적용한다. 이미 L2 성공한 CI/Xvfb 소프트웨어 GUI의 `setsid nice -n 10` 경로는 그대로 보존한다.
- 공개 Owner 실행기 수정 커밋: `043c83c8ecae6c4c47f766dd6c29c1f4aec9152b`
- 수정 파일: `scripts/axia_g07_task04_owner_moving_l3_once.sh`
- GLX 어댑터 검증 후 전역 `GALLIUM_DRIVER`·`MESA_D3D12_DEFAULT_ADAPTER_NAME`을 제거하고 `AXIA_G07_TASK04_GUI_D3D12_ADAPTER`만 자식 실행기에 전달한다. 강사의 TTY 수동 승인, PID 소유권, Goal UUID, Contact/SQLite/Lifecycle 원본 판정은 손대지 않는다.
- 공개 Bootstrap [Run #44268777835](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44268777835): **6/6 L0 GREEN**.
- 공개 Student [Run #44268806680](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44268806680): GUI 전용 2/2 포함 기존 필수 계약 **L0 GREEN**.

## 4. REFACTOR·REVIEW

기존 렌더러 설정 위치만 최소 변경했다. 공식 ROS 2 Jazzy/Nav2/TB3, Gazebo SDF, Supervisor/CM/Guard 제어 코드, 센서 publish rate, CM 120ms, Guard 150ms, Scan/Odom/Clock 300ms, Action UUID 취소, SQLite 토픽, Lifecycle ACK를 수정하지 않는다. 실제 Gazebo 서버는 여전히 하나이며 클라이언트는 `gz sim -g` 하나다. `GITHUB_ACTIONS=true` 위조·자동 TTY 응답·전역 프로세스 종료를 추가하지 않았다.

### 잔여 검증 및 출고 게이트

- 새 Student SHA 실제 Gazebo/Xvfb Moving Goal L2 공개 CI: [Run #44268914763](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44268914763). **이 문서 최초 작성 시 진행 중. PASS 미선언.**
- 기존 성공 SHA `486ec02e...`는 과거 유효 L2 증거로 보존하며, 새 Student SHA L2 성공 전까지 Owner 원샷 고정 SHA 및 현장 사용 안내는 갱신/배포하지 않는다.
- Owner WSL2/WSLg D3D12 실제 화면·센서 주기·Goal·원본 TAR/SHA256 인수는 **NOT_RUN**. 실제 Owner 단일 실행 원본을 확인한 이후에만 L3 승인한다.
- 사용자 별도 승인 전 main 병합 없음. 인증 E-Stop 아님.

```text
AXIA_G07_TASK04_OWNER_MOVING_L3=HOLD
AXIA_MVP_DEMO_ACCEPTED=HOLD
CERTIFIED_ESTOP=false
MAIN_MERGED=false
```

## 5. 주니어 개발자용 문제 해결 프롬프트

> 기존 WSLg NO_GOAL GUI 성공 실행기와 새로운 Moving Goal Owner 스크립트가 D3D12 환경변수를 어느 프로세스에 주입하는지 소스 기준으로 비교하라. 새 오류가 발생했다는 추측을 사실로 보고하지 말고, Gazebo 서버·LiDAR·Nav2 안전노드에 GPU GUI 전용 환경변수를 불필요하게 상속시키지 않도록 최소 RED 계약을 작성하라. GREEN에서는 기존 CI GUI와 Owner PID/TTY·Goal 경로를 재구현하지 말라. 동일 Student SHA로 공개 CI 실제 Gazebo L2를 확인한 뒤 출고 후보를 고정하고, WSL2 화면과 원본 증거 없이는 L3 PASS라고 보고하지 말라.
