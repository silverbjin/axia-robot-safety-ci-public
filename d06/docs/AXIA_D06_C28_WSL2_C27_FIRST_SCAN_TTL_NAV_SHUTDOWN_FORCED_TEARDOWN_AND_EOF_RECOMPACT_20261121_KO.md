# AXIA D06 C28 — 강사 WSL2 C27 실측: 최초 Scan300 위반 → Nav Lifecycle 40초 타임아웃 → 강제 종료; 기존 TAR만 재압축

기록: 2026-11-21 KST. **실제 인수 OS: Windows WSL2 Ubuntu 24.04 / WSLg D3D12 NVIDIA GeForce RTX2060 Max-Q / ROS2 Jazzy / Gazebo Harmonic / 공식 Nav2.** 공개 CI/학생 분리, main 미병합. 전송 파일 SHA 검증 완료; raw 원본 개인 WSL2 보존.

## 1. 원본 무결성 및 실제 콘텐츠

업로드 `compact-20261121T042832Z-3465.tar.gz` SHA256 **`6ecc04c081ca975f73585a9b0b18cbd489a785f8f33792371b93384dadab778b`**. 함께 제출된 sidecar의 digest와 실제 다운로드 파일 digest 일치. Sidecar는 WSL2 로컬 절대 경로를 지시하므로 외부 컨테이너에서 `sha256sum -c` 실행 시 파일을 찾을 수 없음; SHA값을 같은 파일 바이트로 직접 계산·비교한 것이 검증 방식.

9개 내부 파일: `cm_shutdown_audit.json`, `gz_world_pause.log`, `launch_tail.log`, `ordered_shutdown.json`, `renderer.txt`, `scan_delivery.json`, `sensor_truth.json`, `summary.txt`, `teardown.txt`. **`gz_server_stop.log`와 원본 전체 `owner_no_goal.log`는 이번 compact에 존재하지 않음**. 전체 native `launch.log`는 WSL2 raw 원본 TAR에만 남음.

GPU 환경 실제 `renderer.txt`: `OpenGL renderer string: D3D12 (NVIDIA GeForce RTX 2060 with Max-Q Design)`, Microsoft vendor, Mesa 26.2.6 kisak-mesa PPA, `REQUESTED_MESA_D3D12_ADAPTER=NVIDIA`. 이 정보는 GLX 클라이언트 환경이고 실제 `gz sim -s`의 내부 thread stack/adapter 경로를 확증하는 자료는 아님.

## 2. 최초 안전 수신 타이밍 위반 (명확히 구분)

`sensor_truth.json`: `status=NO_GOAL_SENSOR_UNSAFE_HOLD`, Goal false / fixture false / fault false, 진단 관찰 20.006s.
- **RAW 최초 Scan300 위반:** Host mono 1969.666745→1969.982777, **316.032ms**, sim header 54.402→54.501s(**99ms**). RAW 전체 관찰 최대 **358.830ms**, first breach index69.
- **Safety 최초 Scan300 위반:** Host mono 1976.217830→1976.575302, **357.472ms**, header58.302→58.401s(**99ms**), first breach index108. Safety CLEAR122/122, front median1.413665m, side2.520244m. **안전 상태는 주기 실패 때문에 HOLD**이며 CLEAR 거리가 TTL FAIL을 지우지 않음.
- RTF average `ros_clock_rtf=0.604076`, `safety_source_hz=10.000827` **sim-time**, `safety_wall_hz=6.050556`. RTF 저하와 수신 지터가 동시에 관측됐으나 GPU/Mesa 원인 단정 금지.

`scan_delivery.json`의 **원본 학생 RAW 최초 Scan쌍과 동일 Stamp pair**:
- `student_first_stamp_pair_verified=true`, `student_first_ros_peer_pair_verified=true`; header [54402000000,54501000000].
- 학생 callback gap316.032ms, Gazebo native transport gap286.837ms, 별도 OS ROS peer gap305.729ms, peer→student after14.046ms. 후보 분류 `AFTER_NATIVE_TRANSPORT_RX`, **`cause=UNDETERMINED`**. native send/bridge DDS publish timestamp 미측정; ROS callback delay 하나만 원인으로 단정할 수 없음.
- **별개의 POST_NAV2_READY_PROXY 최초 쌍**: raw405.396ms, safety420.560ms, **Gazebo native314.483ms**, local clock RTF **0.268223**. 이 구간은 AT_OR_BEFORE_NATIVE_TRANSPORT_RX 후보이며 학생 최초 Scan쌍과는 다른 시간 창. **최초 downstream 후보와 이후 upstream 지연을 하나의 원인으로 합치지 말 것**.

## 3. Nav2 / CM / 종료 실패, 첫 원인과 후행 실패 분리

`launch_tail.log`에 실제 출력:
- `[p2_supervisor_node-19] HEALTH_BAD_DIAGNOSTIC`: `scan_fault_code=SCAN_TIMEOUT`, `scan_age_sec=0.5525`, `scan_callback_max_gap_sec=0.529404`. 이후 재발 `scan_age_sec=0.5214`, `scan_callback_max_gap_sec=0.577847`. 최초 Safety Scan TTL300 위반과 호환되지만 이 Supervisor 경고를 최초 위반 시각으로 승격하지 않음.
- lifecycle manager: `Have not received a heartbeat from collision_monitor` → `CRITICAL FAILURE: SERVER collision_monitor IS DOWN after not receiving a heartbeat for 4000 ms. Shutting down related nodes.`
- `ordered_shutdown.json`: navigation_manage_group_probe is_active true / 응답0.080222s, 그러나 navigation shutdown `SERVICE_TIMEOUT` after **40.000851s**, `navigation_ack=false`, `localization_ack=false`. Active 상태 탐색이 곧 종료 서비스 응답성 증거는 아님.
- `cm_shutdown_audit.json`: `BLOCKED_CM_SHUTDOWN_UNVERIFIED`, `cm_exit_code=null`, 정상 종료 PASS 불가.
- `gz_world_pause.log`: `data:true` (World pause 요청 ACK). 이는 Gazebo native exit0 또는 ServerControl stop ACK 자체가 아님.
- `teardown.txt`: **`P2_L2_FORCED_TEARDOWN`**. C27의 native gz exit0 guard가 실행됐다는 증거 없음. C27 Student 코드는 Nav ACK 없으면 ServerControl stop 단계에서 Fail-Closed 하므로 이번 자료는 stop-drain 완화 패치의 성공/실패를 판단하지 못함.
- `summary.txt`: `native_gz_died_marker=false`, `native_gz_exit0_marker=false`, `gazebo_crash_root_cause=UNCONFIRMED`, 전체 HOLD. 이는 **Gazebo exit -11 부정 증거가 아님**.

**엄격한 최초 실패 우선순위**: ① 학생 RAW receipt 316.032ms TTL 최초 위반 (안전 HOLD), ② 이후 별도 Safety300 위반, ③ CM 4초 bond loss 및 Navigation 40초 timeout/ACK 실패, ④ 강제 teardown, ⑤ Gazebo child 네이티브 종료 상태 미확정. 서로 인과관계는 입증되지 않음.

## 4. 확정된 C27 압축기 결함 및 공개 CI 회귀

기존 `d06/scripts/axia_d06_c27_owner_wsl2_nogoal_once.sh --compact-only`는 전체 `launch.log`의 **첫 100001바이트만** 읽은 후 그 부분의 마지막 400줄을 `launch_tail.log`라고 저장했다. 100KB 초과 원본이면 **실제 종료 직전 끝부분이 잘리는 결함**이다. 이번 압축에서 로그가 `Deactivating collision_monitor` 중간에 끝나고 native exit/stop 로그가 없는 이유가 이 결함일 수 있으나, 원본 전체 EOF 없이 **실제로 원인이 그 결함이었는지는 미확정**.

**C28 최소 수정: 런타임·Nav2·safety TTL·GPU 변경 0**
- 원본 TAR 내 `launch.log`를 최대 32MB까지 읽되, **실제 끝부분 마지막 400줄, 최대 100KB**만 기록. native `gz` 자식 종료 행은 전체 파일에서 찾아 12줄/6KB 이내로 따로 보존. 초과 크기/미발견은 HOLD, 임의 PASS 금지.
- `owner_no_goal.log`, `g07_ordered_shutdown.log`의 마지막 각각 최대16KB 기록. raw rosbag / 전체 메모리 core 보존은 **WSL2 로컬만**, 공개 TAR에 포함하지 않음.
- 같은 host-monotonic clock의 RAW/Safety 최초 위반 쌍 비교. 서로 다른 topic index 비교 금지. `forced_teardown`, `navigation_service_status`, `cm_exit_code`, native exit0/died 및 `release_authorized=false`를 원본 값으로 요약.
- 기존 C27 실제 시뮬레이션 재실행 필요 없음: **`--compact-only`로 원본 TAR를 동일 환경에서 재분석**.

**RED→GREEN→REFACTOR→REVIEW→COMMIT:**
- RED tests `d06/tests/test_d06_c28_actual_wsl2_compact_eof_and_safety.py`, WSL2 계측 수치(316.032ms/40.000851s)와 의도적 100KB 이상 합성 로그, 기존 Owner tail 재수집 3건: 공개 L0 [#44866577290](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44866577290) **1 FAIL, 2 ERROR** (EOF 잘림, first_failure 미구현, owner tail 누락).
- GREEN 변경 파일 `d06/scripts/axia_d06_c27_owner_wsl2_nogoal_once.sh` 및 테스트의 동일-clock 원본 fixture 보완. 구현 commit `ffe0d467e159efcf1b60da6263203d3cee86f9d5`, blob `cefe00b6304c7bab0265b7b5d660cfb9a909a3a3`.
- 공개 [GREEN L0 #44866661745](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44866661745) **신규 3/3 PASS + 기존 전체 성공**, 실제 로그 `test_native_gz_exit_last_100kb_not_first_100kb ... ok`, `test_actual_safe_ttl_first_failure_and_nav_shutdown_hold_both_preserved ... ok`, `test_original_owner_failure_tail_can_be_recovered_without_simulation ... ok`.
- 같은 source `Ubuntu24 CLI #44866661707` SUCCESS 및 `runner canary #44866661800` SUCCESS. Gazebo L2는 C27 native stop 구현의 기존 PASS 증거([#44864433199](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44864433199)); **새 C28 수정은 압축 전용**이며 실제 NVIDIA WSLg 검증이 아님.

## 5. 강사 WSL2: 기존 Raw TAR 한 번 읽기만 (Gazebo/ROS 절대 재실행 없음)

```bash
(
  set -Eeuo pipefail
  SHA="ffe0d467e159efcf1b60da6263203d3cee86f9d5"
  BLOB="cefe00b6304c7bab0265b7b5d660cfb9a909a3a3"
  SCRIPT="$(mktemp --suffix=.sh)"
  trap 'rm -f "$SCRIPT"' EXIT
  curl -fLsS --retry 3 --max-time 90 \
    "https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public/$SHA/d06/scripts/axia_d06_c27_owner_wsl2_nogoal_once.sh" -o "$SCRIPT"
  test "$(git hash-object "$SCRIPT")" = "$BLOB"
  bash -n "$SCRIPT"
  bash "$SCRIPT" --self-check
  BASE="$HOME/axia_d06_c27_owner_evidence"
  RAW="$(find "$BASE" -type f -name 'd06-wslg-sensor-*.tar.gz' -printf '%T@ %p\n' |
     sort -nr | sed -n '1s/^[^ ]* //p')"
  test -n "$RAW" && test -s "$RAW" && test -s "$RAW.sha256"
  echo "D06_C28_REUSING_OLD_RAW=$RAW NO_GAZEBO_RUN"
  bash "$SCRIPT" --compact-only "$RAW"
)
```

사용자 제출은 새 `D06_C27_COMPACT_ARCHIVE`와 `D06_C27_COMPACT_SHA256` 두 개 **또는** `D06_C28_COMPACT_LAUNCH_EOF_NOT_RECOVERABLE_HOLD`와 해당 콘솔 출력. 전체 원본 raw, 개인 홈 디렉터리 또는 coredump 공개 공유 금지.

## 6. 범위·인수·변경 통제

```text
C28_INPUT_TAR_SHA256=PASS
C28_WSL2_GPU=NVIDIA_RTX2060_MAXQ_D3D12_MESA26_2_6
C28_FIRST_RAW_SCAN_TTL=316.032ms > 300ms FAIL
C28_FIRST_SAFETY_SCAN_TTL=357.472ms > 300ms FAIL
C28_POST_READY_NATIVE_GAP=314.483ms > 300ms
C28_NAV_SHUTDOWN_SERVICE=TIMEOUT_40.000851s
C28_CM_EXIT0=UNVERIFIED
C28_GAZEBO_NATIVE_EXIT0_OR_MINUS11=NOT_OBSERVED_IN_TRUNCATED_COMPACT
C28_TEARDOWN=FORCED
C28_RUNTIME_CHANGE=NONE
C28_PUBLIC_STATIC_L0=PASS
C28_REAL_WSL2_GAZEBO_RERUN=NOT_RUN
C28_GAZEBO_ROOT_CAUSE=UNDETERMINED
C28_MOVING_CM120_GUARD150=NOT_RUN
AXIA_MVP_DEMO_ACCEPTED=HOLD
CERTIFIED_ESTOP=false
MAIN_MERGED=false
```

관련 작업 Public PR #177, Student PR #87 (draft), 기존 Issue #186. 원본 안전 타이밍 실패를 원인 확정 없이 RMW/Executor나 GPU 드라이버의 단독 문제로 고정하지 않는다. Scan300/CM120/Guard150을 완화하지 않으며 이전 성공 인수 증거를 보존하고 동일 현장 실패를 재실행하지 않는다.
