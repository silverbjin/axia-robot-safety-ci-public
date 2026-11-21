# AXIA D06 C27 — WSL2 Gazebo 종료 `exit -11`: native exit0 확인 후 SIGINT 변경·공개 CI L2·현장 인수 가이드

작성: 2026-11-21 KST. **실제 인수 OS = Windows WSL2 Ubuntu24.04, WSLg NVIDIA RTX2060 Max-Q D3D12, Jazzy/Harmonic/Nav2.** Main 미병합. Safety/Goal/TTL 변경 없음.

## 1. 사용자 재제출 원본과 최초 실패 사실을 구분

사용자 재첨부 `readonly-41k2b1jj.tar(1).gz` SHA256 `f2b07e1bcd33a1de29685b2cb08e2b63536dc439f2b452105f757e2f790111f8`; 함께 첨부한 `.sha256`과 **일치**, 이전 C26에 첨부한 원본과 동일한 SHA. 내부 3개 파일:
- `summary.txt` 155 B — `D06_C24_WSL2_PREVIOUS_EVENT_BOOT_UNVERIFIED_HOLD`, `D06_C23_NO_NEW_SIGSEGV_NO_GAZEBO`;
- `preflight.txt` 366 B — WSL2 boot UUID `258e0071-2816-4b1c-893b-5622a181ef91`, 현재 coredump socket 활성;
- `observation.json` 781 B — 커널 `6.18.40.1-microsoft-standard-wsl2`, PID1 systemd, `/dev/dxg`·`/mnt/wslg` 있음, `D3D12_OTHER`, `root_cause=UNCONFIRMED`, `gazebo_not_run=true`.

**이번 파일에는 Gazebo launch.log, server SIGSEGV backtrace, 실제 WSLg GPU 서버 종료가 없다.** 따라서 이번 파일 단독으로 기존 `exit -11`을 재현하거나 근본 원인을 확인할 수 없음.

이전 실제 Owner `d06-forensic-ab-no-goal-1jvaRyCE`에서만:
- Gazebo server `gz sim -r -s` PID 19280 exit `-11`이 최초 네이티브 종료 실패.
- 공식 Nav2 navigation/localization ACK, Collision Monitor child exit0, witness exit0.
- 준비 이후 dual Scan 20.161s, Raw 최대271.130ms / safety237.858ms (해당 READY 이후 관측 창만 PASS 후보).
- 전체 세션 pre-READY ROS raw423.494ms/safety418.905ms는 별도 타이밍 경계. Moving CM120/Guard150은 미검증.
- 과거 코어 `sudo coredumpctl info 19280` 조회 결과 `No coredumps found.`. 첫 GDB 스택 없음. OS/WSLg/OGRE root cause **UNCONFIRMED**.

## 2. 새로 발견한 코드상 종료 순서의 위험

고정 학생 원본 `0565e580f5b7c80d719960a6046de3e45c8ea477`의
`block_B/day07/h01_runtime/scripts/p2_no_goal_smoke_ci.sh`는
(1) Nav2 lifecycle ACK → (2) `/world/.../control pause: true` ACK → (3) `/server_control stop: true` ACK → (4) **고정 sleep 0.7초** → (5) `kill -INT -- "-$LAUNCH_PID"`로 **서버를 포함한 launch 그룹**에 중복 종료 신호를 보낼 수 있었음.

Gazebo 8 API의 `ServerControl.stop=true` 서비스 응답은 서비스 처리 ACK이고, **서버 프로세스의 네이티브 exit0가 아니다**. NVIDIA WSLg Ogre2/GPU LiDAR teardown 도중 두 종료 경로가 겹치는 **경합 가능성**이 존재하지만, 당시 GDB stack 미확보로 이 경합이 실제 `exit -11`의 근본 원인이라고 확정할 수 없음.

공식 참고:
- https://gazebosim.org/api/sim/8/classgz_1_1sim_1_1Server.html
- https://gazebosim.org/api/gui/8/layout.html
- 유사 WSLg OGRE 충돌 https://github.com/gazebosim/gz-sim/issues/3335 (동일 원인 증거 아님).

## 3. MVP 최소 수정 — 원본과 후보 격리

학생 **독립 작업 브랜치** `fix/d06-nogoal-gz-server-shutdown-drain-20261121`, 초안 [PR #87](https://github.com/silverbjin/axia-robot-safety-student/pull/87), HEAD `6c79c09d91f13c81961492eb30e66d99d307831c`:
1. 신규 읽기 전용 exit guard `block_B/day07/h01_runtime/tools/g07_gazebo_server_exit_guard.sh` — 실제 `launch.log`에서 `[INFO] [gz-N]: process has finished cleanly`를 **최대15초** 기다림. `[ERROR] [gz-N]: process has died ... exit code -11` 또는 timeout이면 즉시 HOLD. Goal/ROS/Gazebo/신호 실행 기능 자체 없음.
2. 고정 원본 `scripts/p2_no_goal_smoke_ci.sh`의 shutdown에서 `stop:true` ACK 다음 exit guard 사용. native exit0 입증 시에만 전체 group SIGINT; 실패 시에는 rc3/HOLD를 남기고 launch **관리자 PID**에만 INT를 보내도록 하여 자식 전체에 직접 중복 INT를 보내지 않음. 안전 TTL/CM/Guard/부트나 드라이버 설정 변경하지 않음.
3. 원본 학생 브랜치의 일반 학습 코드·TODO와 정답 분리 정책 불변. main 미병합. 학생 source Git blobs: smoke `cc3c64f7ae769a11d9daad4acdbdb48141253f7c`, guard `72a117d9a1b22748ffd16171d213916c095a623e`.

공개 CI 브랜치 `fix/d06-wslg-lidar-vs-rtf-ci-20261118` (PR #177):
- `d06/scripts/axia_d06_g07_wslg_sensor_no_goal_once.sh` 기본은 이전 학생 `0565...`/원본 blob 유지, **`AXIA_D06_GAZEBO_C27_CANDIDATE=1`일 때만** 새 학생 SHA와 smoke blob 사용, 실제 GLX NVIDIA D3D12 사전검사 필수. GPU 선택은 해당 프로세스의 `MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA`로만 제한하고 Windows/system-wide 설정은 변경하지 않음.
- `d06/scripts/axia_d06_c27_owner_wsl2_nogoal_once.sh` 단일 WSL2 NO_GOAL 실행기, SHA `65a279b3f8a802bacc619f122e4abe3fd1f55e62`, blob `2e5d8fe66f4c11570b4cd707f4a740514180765d`. `--self-check`, `--compact-only ABS_RAW_TAR`, `--run`만 지원. 정확한 GLX GPU 사전검사 후 단 1회 센서/독립 Scan witness/공식 Nav2/CM/Gz shutdown 실시. 원본 Raw TAR는 WSL2에 보존하되, 필요한 `launch_tail.log`/ordered_shutdown.json/CM audit/ServerControl STOP·pause/Scan truth/renderer만 작은 SHA256 TAR에 보존. **메모리 코어/전체 raw sensor/rosbag은 압축 업로드 대상에서 제외.**
- 최종 gate는 Owner 반환 0뿐 아니라 실제 `gz` exit0, exit-11 없음, Nav2 ack2, CM child0, GOAL_NOT_SENT, sensor clear 모두 입증돼야 후보. 전체 시연 인수 PASS로 자동 승격하지 않음.
- 신규 회귀 `d06/tests/test_d06_c27_gz_native_stop_drain.py`, `test_d06_c27_owner_candidate_pin.py`, `test_d06_c27_owner_compact_once.py`.

## 4. 실제 RED→GREEN→REFACTOR→REVIEW→COMMIT 및 증거

**실제 공개 RED**
- 원본 학생 SHA에는 새 guard가 없으므로 [L0 #44863722017](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44863722017) 신규 3/3 FAIL (raw HTTP 404, 코드 계약 미충족).
- Owner 후보 핀 연결 전 [#44864012476](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44864012476) 신규 필수 게이트 실패.
- 기존 핀 순서 회귀 [#44864043556](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44864043556)에서 원본 `SMOKE_BLOB` 검사 실패 1건을 발견했고 **원본 기본 SHA를 첫 선언으로 복원**하는 refactor로 GREEN 처리.
- 작은 TAR 발송/원본 장애 증거 보존 신규 테스트 [#44864209530](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44864209530) RED.

**GREEN / 실 출력**
- 학생 코드 출고 후보 `6c79c09d91f13c81961492eb30e66d99d307831c`에 고정한 공개 [L0 #44863764033](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44863764033): `test_immutable_student_sources...ok`, `test_real_log_fixture_exit0_vs_exit_minus11_and_ack_only...ok`, `test_no_side_effects_in_guard...ok`.
- 원본 핀 복원 이후 [L0 #44864111318](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44864111318) SUCCESS.
- 최종 스크립트/압축 회귀 [L0 #44864257662](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44864257662) SUCCESS — 신규 Owner 세 테스트/원본 abort fixture 녹색. CI 실제 `test_compact_synthetic_no_core_and_preserves_first_crash ... ok`.
- **실제 Gazebo Harmonic L2** (GitHub Ubuntu 24.04 `ros:jazzy-ros-base-noble`, 빈 월드, 실제 ROS launch / Gazebo `gz sim -s`): [#44863879635](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44863879635) SUCCESS, **실제 출력**:

```text
D06_C27_GAZEBO_SERVER_STOP_REPLY=data: true
G07_GAZEBO_SERVER_NATIVE_EXIT0_BEFORE_GROUP_SIGINT
D06_C27_REAL_HARMONIC_GZ_NATIVE_EXIT0_AFTER_SERVER_CONTROL_PASS
D06_C27_NOT_WSL2_NOT_WSLG_NOT_GPU_LIDAR_NOT_NAV2_NOT_MOVING
```

- 최신 최종 스크립트 SHA 기준 [L2 #44864257675](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44864257675) SUCCESS; [L0 #44864257662](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44864257662), [Ubuntu24 CLI #44864257669](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44864257669), [Canary #44864257664](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44864257664) 모두 SUCCESS.
- **REVIEW 결론:** L0 synthetic crash/timeout, exact student pin, noGoal authority, actual Gz server native exit0 L2, compact evidence 모두 확인. **아직 강사 WSL2 WSLg NVIDIA GPU LiDAR 서버 종료 PASS 검증은 아님.**

## 5. 강사 WSL2 단일 NO_GOAL 후보 검수 명령

원본 WSL2에서도 다음 한 블록만 사용하며 Goal, fault, moving authority 절대 없음. NVIDIA GLX preflight FAIL이면 **시뮬레이션 전 종료**. 성공해도 `AXIA_MVP_DEMO_ACCEPTED=HOLD` 유지.

```bash
(
  set -Eeuo pipefail
  SHA="65a279b3f8a802bacc619f122e4abe3fd1f55e62"
  BLOB="2e5d8fe66f4c11570b4cd707f4a740514180765d"
  SCRIPT="$(mktemp --suffix=.sh)"
  trap 'rm -f "$SCRIPT"' EXIT
  curl -fLsS --retry 3 --max-time 90 \
    "https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public/$SHA/d06/scripts/axia_d06_c27_owner_wsl2_nogoal_once.sh" -o "$SCRIPT"
  test "$(git hash-object "$SCRIPT")" = "$BLOB"
  bash -n "$SCRIPT"
  bash "$SCRIPT" --self-check
  bash "$SCRIPT" --run
)
```

기대 마커:
- `G07_GAZEBO_SERVER_NATIVE_EXIT0_BEFORE_GROUP_SIGINT` 및 `D06_C27_OWNER_GZ_NATIVE_EXIT0=true` + `D06_C27_OWNER_NO_GOAL_NATIVE_CANDIDATE=true` = **NO_GOAL 진단 후보**. 전체 P1/P2/Moving Goal 인수 아님.
- `G07_GAZEBO_SERVER_NATIVE_SIGSEGV_BEFORE_GROUP_SIGINT_HOLD` = stop 요청과 그룹 SIGINT 사이에 이미 gz가 SIGSEGV. 이는 종료 중복 경합 가설과 별도 layer.
- `G07_GAZEBO_SERVER_NATIVE_EXIT0_TIMEOUT_HOLD` = 서버가 정해진 15초 내 exit0 못 함. 서버/WSLg 자원 해제 정체 후보, 단독 원인 미확정.
- `D06_C27_NVIDIA_D3D12_PREFLIGHT_FAILED_NO_SIM` = 잘못된 GPU로 실행 차단, CUDA/Mesa/Windows 변경 필요 없음.
- `D06_C27_COMPACT_ARCHIVE=...`, `D06_C27_COMPACT_SHA256=...`의 **두 작은 파일만 제출**. 대용량 원본은 WSL2 `~/axia_d06_c27_owner_evidence` 아래 유지.

## 6. 검증 수준 / 미검증 항목

```text
C27_STUDENT_PUBLIC_BRANCH=fix/d06-nogoal-gz-server-shutdown-drain-20261121
C27_STUDENT_PR=87 DRAFT_NO_MAIN
C27_PUBLIC_CI_BRANCH=fix/d06-wslg-lidar-vs-rtf-ci-20261118
C27_PUBLIC_PR=177 NO_MAIN
C27_CI_STATIC_L0=PASS
C27_CI_REAL_HARMONIC_EMPTY_WORLD_L2=PASS
C27_CI_WSL2_WSLG_GPU_LIDAR=NOT_RUN
C27_OWNER_WSL2_REAL_GZ_EXIT0=NOT_RUN
C27_GAZEBO_EXIT_MINUS11_ROOT_CAUSE=NOT_PROVEN
C27_SCAN300_WSL2_FULL_DEMO=NOT_RETESTED
C27_CM120_GUARD150_MOVING_E2E=NOT_RUN
INDEPENDENT_GPU_G3_REQUIRED=false
AXIA_MVP_DEMO_ACCEPTED=HOLD
CERTIFIED_ESTOP=false
MAIN_MERGED=false
```

**따라서 C27은 최소 완화 및 근본 원인 분리 후보이지, 아직 사용자 WSL2 Gazebo 종료 오류의 최종 해결 증거가 아니다.** 실 WSL2 단일 NO_GOAL 결과에서 exit0가 확보되면 해당 환경의 종료 실패 건에 한해 인수 판정하며, 다른 안전 계층은 독립 검증 범위를 명시한다.
