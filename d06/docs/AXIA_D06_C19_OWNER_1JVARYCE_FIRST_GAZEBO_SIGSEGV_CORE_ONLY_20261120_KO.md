# AXIA D06 C19 — WSL2 NO_GOAL 1jvaRyCE: Gazebo server exit -11, 기존 코어만 단일 회수

작성일: 2026-11-20(KST). 공개 PR #177, 개발 브랜치 `fix/d06-wslg-lidar-vs-rtf-ci-20261118`. **main 미병합 / Moving Goal 실행 금지 / 전체 인수 HOLD**.

## 1. 강사 원본 증거 및 무결성

- 원본 수신 파일 `d06-forensic-ab-no-goal-1jvaRyCE.tar.gz` / `.sha256`; TAR SHA256 `541c47638528dbefc0258b51ff23d88e2406bb8e4b78be5e1f1812bd477bdb38` 실제 검사 일치.
- 검사 원본: `forensic/summary.json`, `owner_verdict_excerpt.txt`, `shutdown_context.txt`, `d06_g07_scan_delivery_layer.json`, `native_nav2_ordered_shutdown.json`, `native_cm_shutdown_audit.json`, `renderer_excerpt.txt`, `first_stop_and_timing.txt`.
- `source_archive_sha256_verified=true`는 현장 측 기존 raw archive에 대한 내부 검증 상태. 원본 raw archive 자체는 **첨부된 forensic TAR에 포함되지 않음**, 원본 memory core 및 GDB backtrace **없음**.
- 강사 실제 Renderer: WSLg D3D12 (NVIDIA GeForce RTX 2060 with Max-Q Design), Ogre2 GL_RENDERER도 D3D12 NVIDIA.
- 고정 학생 원본 `0565e580f5b7c80d719960a6046de3e45c8ea477`; `goal_sent=false`, `fixture_moved=false`.

## 2. 최초 실패 경계와 분리 판정

### NO_GOAL 준비 / 20초 Scan 창

- `native_startup_verdict.json`: clock/localization/map/AMCL TF/Navigation/CM ACTIVE/P2 graph/NAV2_ACTION_READY 모두 STARTUP PASS. Nav2 READY host monotonic `4705.324`.
- 두 토픽 활성화 이후 관측 `20.161초` (설정 20초); raw 최대 callback gap `271.130ms`, Safety 최대 `237.858ms` (Scan TTL300ms 이내). Safety CLEAR `165/165`, front median `1.415471m`, side median `2.520154m`. 해당 NO_GOAL safety 관측 **성공 후보**.
- 글로벌 최초 독립 ROS raw 수신 gap `423.494ms`, safety `418.905ms`. 동일 source stamp `7.200→7.302초`와 native `123.617ms`; 독립 ROS 최초 수신 `4666.857002→4667.280496`, Nav2 READY(`4705.324`) **이전**의 다른 타이밍 범위. `candidate=AFTER_NATIVE_TRANSPORT_RX`는 독립 관찰자 후보이며 **Student 실제 첫 TTL pair 일치 미확인**, bridge DDS 송신 시각 미계측, 근본 원인 미확정.
- RViz TF queue drop은 별도 GUI 참고 현상. Scan TTL 우회나 ROS root cause 확정 근거 아님.

### 종료 — 최초 안전상태 변화와 최초 native 오류

- ROS/Gz read-only witness 각각 `exit 0`; marker `G07_READONLY_WITNESSES_STOPPED` 확인.
- Nav2 Navigation lifecycle SHUTDOWN ACK `2.876610s`, Localization ACK `0.343867s`; 관리 서비스 `rmw_fastrtps_cpp`. 이전 30초 무응답 이 회차에 **재발하지 않음**.
- CM status `SHUTDOWN_CLEAN_CANDIDATE`, **CM child exit0**. Supervisor `HEALTH_BAD_DIAGNOSTIC` 최초 확인 시각은 Navigation deactivation 중 `cm_active=false`, `scan_ok=true`/`scan_age_sec=.0725`; 이 로그만으로 첫 Scan timeout으로 분류하면 안 됨.
- `forensic/shutdown_context.txt` original launch line **480**: `[ERROR] [gz-21]: process has died [pid 19280, exit code -11, cmd 'gz sim -r -s /tmp/nav2_u8hkoi9r.sdf'].` **서버 SIGSEGV 실제 현장 재발**.
- 원본 진단 `owner_rc=0` (센서 원샷), `outer_rc=3` (전체 종료 검증), `phase=NATIVE_ARCHIVE_VALIDATION`. `P2_L2_GRACEFUL_TEARDOWN` 부모 마커는 자식 exit-11을 덮지 못함.
- `forensic/summary.json`: `native_no_goal_whole_teardown_clean=false`; `gazebo_server_crash_stack=NOT_CAPTURED`, `no_goal_acceptance=false`. **최종 판정 HOLD, 원인 미확정**.
- 기존 G07 이슈 [#186](https://github.com/silverbjin/axia-robot-safety-ci-public/issues/186)와 같은 실패 계열. 이전 문제 해결을 성공으로 과장하지 않음.

### 공식 유사 사례 참고 — 원인 단정 금지

- [Microsoft WSLg #1533](https://github.com/microsoft/wslg/issues/1533), [#1497](https://github.com/microsoft/wslg/issues/1497): D3D12/TLS destructor + unload 순서에서 SIGSEGV가 발생한다는 외부 보고. **실제 AXIA core의 #0 프레임과 라이브러리 경로가 확인되지 않아 가설만 유지**.
- [Gazebo Sim #3335](https://github.com/gazebosim/gz-sim/issues/3335): WSLg NVIDIA/Ogre GUI 충돌 및 libd3d12core 프레임 예. 원본 AXIA는 **server `gz sim -s`의 종료 크래시**이므로 GUI 사례와 동일하다고 주장하지 않음.
- 해결책으로 임의 `LD_PRELOAD`, Mesa 변경, RMW 교체, TTL 증가, 프로세스 exit-11 무시를 시도하지 않음.

## 3. RED → GREEN → REFACTOR → REVIEW → COMMIT

- 기존 첫 단계: C11의 `d06/scripts/axia_d06_g07_wslg_sigsegv_capture_once.sh --run-once`는 코어가 없다면 **새 Gazebo를 시작할 수 있어 같은 오류의 현장 반복 금지 원칙과 맞지 않음**.
- **RED** 새 `d06/tests/test_d06_c11_wslg_core_once.py::test_existing_only_requires_exact_gazebo_server_pid_and_never_replays` 등록한 공개 CI [Run #44727749956](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44727749956) FAIL: `AssertionError: '"$MODE" == --existing-only' not found ...`; commit `ac5487face547ea68c02636644a0212cd4f2b6d6`.
- **GREEN** C11 스크립트에 `--existing-only` 지원, 기존 `--run-once`는 보존. `AXIA_D06_EXPECTED_GAZEBO_PID` 필수 숫자/현장 PID 일치 여부 확인, **기존 서버 코어 없는 경우 HOLD 후 종료**, 새 Owner/Gazebo 시작하는 분기 진입 금지. 공개 CI [Run #44727931833](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44727931833) completed SUCCESS; 해당 신규 테스트 `... ok`, 전체 L0 성공. [Noble CLI #44727931885](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44727931885), [Runner Canary #44727931836](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44727931836) SUCCESS.
- 녹색 코드 commit `1f0c5e9fffd0d40d151129dd72b6eb840266655a`, 신규 source blob `3ba68b695c91d058604b9cfc9c37e4a3cd0d257d`. 정확히 **1개 기존 진단 스크립트와 1개 기존 테스트 파일** 변경; 실제 Nav2/CM/Guard/학생/Scan TTL 코드 변경 없음.
- **REFACTOR/REVIEW**: 기존 finder/triage/GDB·작은 TXT TAR/SHA 경로 재사용. `--existing-only`의 누락 코어·대상 PID 불일치는 NO_GOAL 시뮬레이션을 시작하지 않고 비영 종료. 로컬 WSL2 실제 `coredumpctl` 코어 회수 테스트는 하지 않음.
- 정책 C18 `INDEPENDENT_WSLG_G3_REQUIRED=false` 유지, 필수 강사 WSL2 실제 NO_GOAL 종료 검증을 삭제하지 않음.

## 4. 강사 WSL2에서 *Gazebo 재실행 없는* 한 번의 기존 코어 회수

실행하는 것은 **기존 코어 조회와 GDB 첫 프레임 텍스트 회수만**. 새로운 Goal/ROS/Gazebo/센서 시연은 시작하지 않습니다.

```bash
(
  set -Eeuo pipefail
  SHA="1f0c5e9fffd0d40d151129dd72b6eb840266655a"
  BLOB="3ba68b695c91d058604b9cfc9c37e4a3cd0d257d"
  SCRIPT="$(mktemp --suffix=.sh)"
  trap 'rm -f "$SCRIPT"' EXIT
  curl -fLsS --retry 3 --max-time 90 \
    "https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public/$SHA/d06/scripts/axia_d06_g07_wslg_sigsegv_capture_once.sh" -o "$SCRIPT"
  test "$(git hash-object "$SCRIPT")" = "$BLOB"
  bash -n "$SCRIPT"
  bash "$SCRIPT" --self-check
  AXIA_D06_EXPECTED_GAZEBO_PID=19280 bash "$SCRIPT" --existing-only
)
```

출력된 `D06_WSLG_CORE_ONCE_FORENSIC_ARCHIVE=<...>.tar.gz` 및 `D06_WSLG_CORE_ONCE_SHA256=<...>.sha256` **2개만** SHA 검증 후 제출. 원본 메모리 core 업로드 금지. `D06_WSLG_CORE_ONCE_EXISTING_ONLY_MISSING_CORE_NO_REPLAY`, `...TARGET_PID_MISMATCH_NO_REPLAY` 또는 `...MISSING_TOOL=coredumpctl`은 **원인 미확정 HOLD**이자 **Gazebo 재실행 없음**을 의미. 실제 코어를 얻어도 첫 GDB stack과 공유 라이브러리 경로로 원인이 확정되기 전 PASS 아님.

## 5. 최종 게이트

```text
C19_PUBLIC_L0=PASS (same new regression; NO_ROS_NO_GAZEBO)
C19_NOBLE_CLI=PASS (existing capability, not real systemd core)
C19_OWNER_WSL2_1JVARYCE=FAIL (ACTUAL GAZEBO SERVER -11)
C19_NATIVE_WITNESSES=EXIT0
C19_NAV2_ACK=PASS
C19_CM_EXIT0=PASS
C19_STUDENT_NO_GOAL_20S_SCAN300=CANDIDATE_PASS
C19_WSLG_GAZEBO_FIRST_STACK=NOT_CAPTURED
C19_EXISTING_ONLY_CORE_TRIAGE=NOT_RUN_ON_WSL2
MOVING_GOAL_ALLOWED=false
AXIA_MVP_DEMO_ACCEPTED=HOLD
D06_GAZEBO_LIVE_RELEASE=HOLD
CERTIFIED_ESTOP=false
MAIN_MERGED=false
```
