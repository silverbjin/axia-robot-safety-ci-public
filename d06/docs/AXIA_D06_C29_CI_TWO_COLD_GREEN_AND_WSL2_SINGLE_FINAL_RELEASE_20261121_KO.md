# AXIA D06 C29 — 공개 CI 전체 NO_GOAL 실 Gazebo L2 2/2 PASS 및 강사 WSL2 단일 최종 인수 출고

**날짜:** 2026-11-21 KST · **MVP 범위:** Windows WSL2 Ubuntu24.04 / WSLg D3D12 NVIDIA RTX2060 Max-Q / ROS2 Jazzy / Gazebo Harmonic / TurtleBot3 Waffle / 공식 Nav2 / Collision Monitor. **상태:** C29 native Linux CI 준비 완료; 강사 WSL2 L3 NOT_RUN; 전체 MVP ACCEPTED=HOLD; main 미병합.

## 1. C29-01 불변 기준선/출고 전 원본 보존

- `d06/ci/c29_source_manifest.json`: 최초 Fast DDS 기준선 및 검증되지 않은 `2cycles=NOT_RUN` 상태를 **그대로 보존**하여 실패 이력과 의사결정을 재현 가능하게 한다.
- Source Student C27 SHA `6c79c09d91f13c81961492eb30e66d99d307831c`, smoke blob `cc3c64f7ae769a11d9daad4acdbdb48141253f7c`, Gazebo child exit guard blob `72a117d9a1b22748ffd16171d213916c095a623e`.
- 공개 C28 EOF evidence compactor SHA `ffe0d467e159efcf1b60da6263203d3cee86f9d5` / Git blob `cefe00b6304c7bab0265b7b5d660cfb9a909a3a3`.
- 공개 L0 매니페스트 테스트: [RED #44875931488](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44875931488) 1 ERROR absent manifest → [GREEN #44875995319](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44875995319) PASS.
- 이전 실제 WSL2 [C28](https://github.com/silverbjin/axia-robot-safety-ci-public/blob/4fd31b87de381b3c72d2cde02bebf309ce683f63/d06/docs/AXIA_D06_C28_WSL2_C27_FIRST_SCAN_TTL_NAV_SHUTDOWN_FORCED_TEARDOWN_AND_EOF_RECOMPACT_20261121_KO.md): RAW 첫 316.032ms >300, Safety 첫 357.472ms >300, CM bond loss와 후행 navigation SERVICE_TIMEOUT 40.000851s, 강제 종료. 과거 Gazebo `exit -11` 원인은 미확정. 기존 증거/테스트는 재개발하지 않음.

## 2. C29-03 Fast DDS 실제 2회 RED — 최초 실패가 서로 다름

[실제 Ubuntu24.04 Jazzy/Harmonic TB3/Nav2/CM 동일 월드 L2 Run #44876262211](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44876262211) / 2개 독립 cold-run, 동일 C27 Student SHA, `rmw_fastrtps_cpp`:

| 조건 | Cycle 1 | Cycle 2 |
|---|---|---|
| 최초 실패 | RAW Scan300 400.895ms, Safety400.202ms | Navigation 시작 중 `collision_monitor/get_state service client: async_send_request failed` |
| 평균 RTF | 1.015548 | Nav2 startup 실패로 센서 창 미진입 |
| Nav2 shutdown ACK | True/True | True/True |
| CM child exit code | 0 | 0 |
| Gazebo child exit0 | True | True |
| 전체 통합 PASS | **FAIL** | **FAIL** |

정확한 원본:
- Cycle1 job `136761694090`, artifact `14695609898`: `startup_verdict=SMOKE_READY`, sensor `NO_GOAL_SENSOR_UNSAFE_HOLD`, first RAW gap0.400895s, Safety max0.400202s. 종료가 정상이어도 300ms 안전 주기 실패는 HOLD.
- Cycle2 job `136761694262`, artifact `14695893770`: `startup_verdict.NAVIGATION_START BLOCKED`, `collision_monitor/get_state` async 요청 실패가 최초. Native/ROS Scan witnesses native=0, ros=0으로 정상 종료한 후 handoff marker가 없는 것은 후속 현상. **종료 마커 부재/최종 실패를 근본 원인으로 오인 금지.**
- Nav2 공식 LifecycleServiceClient get_state는 service request 및 응답을 관리하며, 2초 제한이 관여할 수 있으나 실제 RMW/스케줄링 근본 원인 확정은 아님: https://api.nav2.org/nav2-jazzy/html/lifecycle__service__client_8cpp_source.html.
- Safety300ms/CM120ms/Guard150ms 설정이나 Nav2 공식 코드는 수정하지 않았으며, 동일 Fast DDS 시연 현장 재시도 금지. 해당 실증 workflow는 수동 진단으로 보존.

## 3. C29-04 CycloneDDS 실제 통합 2/2 GREEN

**선택 원칙:** 같은 Student C27 SHA, 같은 RTF/스캔/Goal 권한/실 세계/공식 Nav2 및 CM, `RMW_IMPLEMENTATION`만 `rmw_cyclonedds_cpp`로 바꾼 A/B. 이 실증은 **동일 source의 실제 CycloneDDS 구성 성공**이며 Fast DDS 실패의 단독 인과관계 확정이 아니다.

[공개 실제 통합 L2 #44876761417](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44876761417) **2/2 PASS**, 테스트 커밋 `162d231cd464464297bd8b220bf1a8419b193265`, workflow blob `1ff854d3c42d2186db61b22738c11143889d3d9e`.

| 증거 | Cycle 1 | Cycle 2 |
|---|---:|---:|
| GitHub job ID | `136763048082` | `136763047927` |
| Artifact ID | `14695819912` | `14695889571` |
| ZIP SHA256 | `7cdb97a2438ea7117c7ae79ff9389a5eb55aabf871ee2325b5ca006d9fcda6c4` | `6adacdde47e4f4f1802200a25210dd8f9c63b8934c1fc5428baf1495c81c6e5` |
| 독립 ROS Scan 세션 | 20.115s | 20.118s |
| Raw Scan 최대 Host 수신 gap | **114.793ms** | **120.614ms** |
| Safety Scan 최대 Host 수신 gap | **116.094ms** | **120.912ms** |
| RTF | 0.999412 | 0.998932 |
| 최초/최대 Scan300 위반 | **없음** | **없음** |
| Nav/Localization shutdown | **ACK/ACK** | **ACK/ACK** |
| CM native exit | **0** | **0** |
| Gazebo native child exit | **exit0** | **exit0** |
| Goal/Fault | **없음** | **없음** |
| 판정 | **PASS** | **PASS** |

두 Artifact ZIP을 다운로드해 각각 `g07_wslg_sensor_truth.json`, `d06_g07_scan_delivery_layer.json`, `g07_ordered_shutdown.json`, `g07_shutdown_audit.json`, `launch.log`을 직접 열어 검증함. `post_ready_proxy.candidate=NO_ROS_TTL_VIOLATION_WITNESSED`; 원본 source-pair 위반이 관측되지 않아 별도 RMW 지연 인과 분석은 불필요.
단, WSL2 WSLg NVIDIA GPU가 없는 Xvfb/software renderer CI이며, 강사 WSL2 L3 성공으로 **승격 금지**.

## 4. C29-05 새 릴리스 실행기 / Fail-Closed Scenario Verifier

이전 Fast DDS baseline 매니페스트는 유지하고, **선택 결과를 별도** `d06/ci/c29_selected_cyclonedds_release.json`으로 기록:
- `ci_two_cold_status=PASS_2_OF_2_LINUX_CYCLONEDDS`
- `owner_wsl2_l3=NOT_RUN`
- `cm120_moving_e2e=NOT_VERIFIED`, `guard150_moving_e2e=NOT_VERIFIED`, `certified_estop=false`, `main_merged=false`.
- 실제 Owner WSL2의 기본 RMW는 아직 실측하지 않았으므로 **CycloneDDS만 선택해 단일 실행 트리에 적용**하고 WSL2에서 실제 ID를 `g07_ordered_shutdown.json`으로 검증한다. 시스템 전역 설정이나 드라이버 변경 없음.

**C29 구현 파일**
- `d06/scripts/axia_d06_c29_owner_final_no_goal_once.sh`: `--self-check` 또는 `--run`. WSL2 Ubuntu24.04/WSLg NVIDIA D3D12 사전검사 → CycloneDDS 설치되어 있지 않으면 **공식 ROS Jazzy Debian 패키지만 sudo apt install** → 정확한 C28 owner/verification helper Blob 체크 → 기존 C27 raw가 있으면 자동 `--compact-only` 기존 종료 EOF 재분석 → **새 실제 NO_GOAL 단 1회** → 작은 TAR+SHA → 검증기 통과시 해당 NO_GOAL 후보 PASS. 사용자 반복 수동 진단 불필요.
- `d06/tools/d06_c29_no_goal_compact_gate.py`: 로컬 사전 생성 TAR SHA256, NVIDIA GLX, 실제 native Gazebo exit0, 20s Raw/Safety max300ms, Goal/Fault 미발행, Nav2/Localization ACK, CM child0, 실제 CycloneDDS RMW, READY 후 독립 ROS witness 정상, Forced teardown 없음 검증. 로봇 구동/신호 기능 없음.
- `d06/tests/test_d06_c29_owner_final_compact_gate.py`: 정상 synthetic TAR도 실제 WSL2 PASS로 승격하지 않음, Scan316/400ms·Nav ACK 누락·CM code None·wrong RMW·Goal 허가·강제 종료·Gz-11·Intel GPU·필수 witness 누락 모두 HOLD.

**RED→GREEN→REFACTOR→REVIEW→COMMIT**
- 초기 새 release 실행기/검증기 부재 RED, 신규 C29 tests.
- 첫 코드 후보 L0 [#44877271763](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44877271763): 신규 5개 중 **4 PASS/1 FAIL**, Bash `\${...}` 잘못된 escape로 `--self-check` 인자를 거부한 사실 발견. 현장 배포 차단.
- 최소 Bash parameter expansion 수정 commit `4836ae241c262c89547a67757cc7cea2143a81dc`, Owner script Git blob `eae5f70bd45179f02000ccd75ecedf57e1a29619`.
- [최종 L0 #44877347474](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44877347474): **신규 5/5 PASS, 기존 전체 D06 L0 PASS**, 실제 `C29CompactAcceptance...ok`; WSL2 실 Gazebo/GUI 미실행.
- 변경 파일 감사: 이번 C29 변경은 신규 CI, tests, manifest, 소형 verifier 및 Owner wrapper만 추가. 기존 ROS/Nav2/Gazebo/CM/Safety Supervisor/Scan TTL 변경 없음.

## 5. 강사 WSL2 최종 **단일 원샷** 명령

공개 CI 실증·릴리스 가드 완료로 이 단계만 사용자 WSL2 실행. 코드 SHA+Git Blob 검증 후 `--self-check` 다음 `--run` 1회. 새 Goal, Fault, Moving 없음.

```bash
(
  set -Eeuo pipefail
  SHA="4836ae241c262c89547a67757cc7cea2143a81dc"
  BLOB="eae5f70bd45179f02000ccd75ecedf57e1a29619"
  SCRIPT="$(mktemp --suffix=.sh)"
  trap 'rm -f "$SCRIPT"' EXIT
  curl -fLsS --retry 3 --max-time 90 \
    "https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public/$SHA/d06/scripts/axia_d06_c29_owner_final_no_goal_once.sh" \
    -o "$SCRIPT"
  test "$(git hash-object "$SCRIPT")" = "$BLOB"
  bash -n "$SCRIPT"
  bash "$SCRIPT" --self-check
  bash "$SCRIPT" --run
)
```

스크립트 내부 CycloneDDS 공식 ROS 패키지가 없으면 `sudo` 비밀번호 입력이 한 번 필요할 수 있으나 **추가 수동 개발/진단 실행을 요청하지 않는다**. NVIDIA GLX 또는 소스 blob 불일치면 ROS/Gazebo 시작 **전** 중단.

**성공 문자열 (NO_GOAL 범위만):**
```text
C29_OWNER_SELF_CHECK_L0_PASS_NO_ROS_NO_GAZEBO_NO_GOAL
C29_OWNER_RMW_SELECTED=rmw_cyclonedds_cpp
C29_OWNER_RAW_ONCE_RC=0
C29_NO_GOAL_EVIDENCE_CONTRACT_PASS_NEEDS_ACTUAL_WSL2_PROVENANCE
C29_OWNER_WSL2_NO_GOAL_L3_CANDIDATE_PASS
C29_OWNER_REQUIRED_SAFETY_CM120_GUARD150_MOVING_NOT_VERIFIED
AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false
```

반드시 `C29_OWNER_FINAL_COMPACT_ARCHIVE=...`, `C29_OWNER_FINAL_COMPACT_SHA256=...` 경로 **두 개만** 제출. 이들이 생성되지 않았다면 `C29_OWNER_EVIDENCE_ROOT=...`의 `owner_no_goal.log`에서 발생한 최초 실패 주변 메시지와 간단한 원인 정보만 선별 제출; 전체 core/bag/private user logs 업로드 금지. 실패 시 **같은 현장 run 반복하지 않고 해당 오류를 공개 CI 회귀 RED→GREEN 후 재출고**.

## 6. 공개 CI와 실제 WSL2 조건의 정확한 경계

**이번에 검증:** 동일 Student C27 SHA의 실제 Gazebo Harmonic Waffle/공식 Nav2/CM, Nav/Loc ACK, 20초 Raw/Safety Scan 300ms, CM child exit0/Gz native exit0, CycloneDDS RMW, no Goal/Fault, 2개의 독립 CI Linux cold-runs. Fast DDS 부적합 후보 0/2는 폐기하지 않고 실패 이력으로 보존.

**미검증:** Windows NVIDIA GPU→WSLg Mesa D3D12 실제 시뮬레이션 RTF/scan 전달 주기, OS kernel/journald core, WSL2 실제 NO_GOAL 종료 회복, Moving Goal 안전 `CM120ms`, `Guard150ms` *E2E*, 전체 시연 안정성, 인증된 실제 하드웨어 E-Stop. 다른 G07 이동 L2 PASS를 이번 C29 소스/설정과 동일한 결과로 병합하지 않는다.

```text
C29_SOURCE_MANIFEST_L0=PASS
C29_FASTDDS_FULL_NO_GOAL_L2=FAIL_0_OF_2
C29_CYCLONEDDS_FULL_NO_GOAL_L2=PASS_2_OF_2
C29_NO_GOAL_LINUX_SCOPE=GAZEBO_WAFFLE_NAV2_CM_SCAN300_NATIVE_EXIT0
C29_RELEASE_GUARD_L0=PASS_5_OF_5
C29_OWNER_WSL2_L3=NOT_RUN
C29_MOVING_CM120_GUARD150_E2E=NOT_VERIFIED
C29_ESTOP_CERTIFIED=false
AXIA_MVP_DEMO_ACCEPTED=HOLD
MAIN_MERGED=false
```
