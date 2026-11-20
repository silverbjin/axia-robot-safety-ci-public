# AXIA G07 — WSL2 e96rL7BT Scan300 최초 위반·공개 회귀·출고 HOLD (2026-11-21 KST)

## 0. 범위와 기본 결론

- **교육용 기준선 보존:** 이전 Student `4f4d07f6daf878dd8076f89669698f61f52a802b` / [실제 Gazebo strict L2 2/2 #44706879509](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44706879509) / [공개 Owner 입장 L0 #44707589554](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44707589554). 해당 Run의 성공을 새 SHA로 소급 적용하지 않는다.
- **원래 Owner e96rL7BT의 Scan300 위반은 확정:** Oracle 최초 317.942691ms, 최대 378.410075ms, 실제 동일 LaserScan.header Sim 137.400→137.502=102ms, 독립 rosbag `/scan` 수신 약322.262ms, `/safety/scan` 약320.522ms, 해당 구간 RTF 추정 약0.41, `/clock`와 `/odom`은 수신됨. Goal cancel ACK/1.019466s ZERO/Guard no latch/CM max 89.020ms를 Scan PASS로 승격 금지.
- 이번 실행 도구에는 사용자 원본 `owner-moving-e96rL7BT.tar.gz`와 `*.diagnostics.zip`이 **마운트되어 있지 않음**. 따라서 숫자 fixture는 **사용자가 앞서 SHA256 검증·원본 측정한 공개 가능한 수치의 전사**임. 원본 TAR을 본 실행에서 새로 재추출/검증했다고 주장하지 않음.
- Gazebo-native LiDAR publish Host Monotonic pair, bridge-to-ROS 첫 수신 pair, SHM/GPU native stack 없음. 원인 `UNDETERMINED`. Oracle만 정체된 가설은 독립 ROS bag Scan/Safety Scan 공백과 맞지 않지만 DDS/host/render 부하는 아직 분리되지 않았다.
- 공식 [Gazebo Harmonic Sensors](https://gazebosim.org/docs/harmonic/sensors/)의 SDF `update_rate=10Hz`는 **sim time** 0.1초 간격이므로 WSL2에서 같은 Wall Time 100ms를 보증하지 않는다. [Harmonic GUI RTF](https://gazebosim.org/docs/harmonic/gui/), [Harmonic troubleshooting](https://gazebosim.org/docs/harmonic/troubleshooting/), 관련 WSLg [gz-sim#3335](https://github.com/gazebosim/gz-sim/issues/3335)를 참고했으나 AXIA 원본의 직접 근본 원인으로 귀속하지 않음.
- D08 [PR#201](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/201) / [#202](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/202)의 독립 ROS 증거와 buffered IO, G07 [PR#199](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/199)의 첫 수신 pair 분류를 재사용. Observer 동기 I/O 원인이라고 증명하지 못했으므로 성급히 런타임 Observer를 교체하지 않음.

## 1. RED→GREEN, 실제 실행 출력

| 사이클 | RED 공개 CI | GREEN 공개 CI | 실제 GREEN 범위 |
|---|---|---|---|
| WSL2 최초 Wall/Sim Gap 수치 회귀 | [#44762376515](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44762376515) `ModuleNotFoundError` | [#44762793950](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44762793950) | `Ran 5 tests ... OK`, ROS-free, 항상 Scan300 HOLD |
| Student NO_GOAL 12s Scan Preflight | [#44763520688](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44763520688) 새 모듈 부재 | [#44763773006](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44763773006) | 5/5 컴포넌트 계약 |
| 기존 Moving 러너 TTY/Goal **이전** 사전검사 결선 | [#44763868480](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44763868480) 연결부 누락 | [#44764041083](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44764041083) | 6/6 Student NO_GOAL 계약 |
| 최초 위반 수치 ZIP 6개 생성 | [#44764759005](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44764759005) 분석기 부재 | [#44765047325](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44765047325) | 2/2 원본 미존재·실패 기록 HOLD |
| 미출고 WSL2 후보 입장·ZIP 크기·SHA | [#44765972879](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44765972879) 이전 pin 불일치 | [#44766139667](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44766139667) | 3/3 통과, 현장 미실행 |
| 기존 L0 재연결 및 실제 failed 2-cycle 인가 거부 | [#44766380307](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44766380307) GitHub API HTTP403 / fail-closed | [#44766613244](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44766613244) | 3/3+9/9, 실제 failed CI 1/2 응답을 **offline mock**으로 재현, `HOLD_NO_NEW_WSL2_MOVING_RELEASE` |

- 검증 명령: `python3 -m unittest discover -s tests -p 'test_g07_scan_sim_wall_gap_regression.py' -v`
- 검증 명령: `python3 -m unittest discover -s tests -p 'test_g07_scan_compact_bundle.py' -v`
- 검증 명령: `python3 -m unittest discover -s tests -p 'test_g07_scan300_owner_wrapper.py' -v`
- 검증 명령: `python3 -m unittest discover -s tests -p 'test_g07_stabilization_wsl2_release.py' -v`
- Student 검증 명령: `cd block_B/day07/h01_runtime && python3 -m unittest discover -s tools -p 'test_g07_scan_wall_pregoal.py' -v`
- 실제 CI 사용자 환경 구분: Python L0=PASS, CI Xvfb 실 Gazebo L2는 아래 FAIL, **NVIDIA WSLg/Owner 새 L3 NOT_RUN**.

## 2. 실제 ROS2 Jazzy/Gazebo Harmonic/Nav2 L2

[**새 실제 L2 #44764186378**](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44764186378), Student candidate `803cdd99fa0f781998442fbc37be9f59fde82364`, workflow commit `57b70acbc1e6a549d64cf5508b199634ac2cd4cd`.

| 측정값 | Cycle1 | Cycle2 |
|---|---:|---:|
| 같은 세션 12s NO_GOAL Scan Preflight | PASS | PASS |
| CLEAR/SLOW/STOP 및 정확한 Goal Cancel | PASS | PASS |
| Moving Scan Observer 최대 | 219.289ms | 213.186ms |
| Moving CM Observer 최대 | 86.992ms | 66.326ms |
| Moving Guard Observer 최대 | 86.651ms | 72.669ms |
| Odom 최대 | 142.247ms | 136.102ms |
| Clock 최대 | 100.794ms | 102.971ms |
| Nav + Localization Native ACK | **FAIL** | PASS |
| 전체 strict L2 | **FAIL** | PASS |

- Cycle1 **독립 첫 종료 경계:** Navigation `manage_nodes/shutdown` 단일 요청 `SERVICE_TIMEOUT=40.001275s`, `navigation_ack=false`, 따라서 Localization 요청은 ACK 근거 없음. 같은 callback group의 `/is_active`가 90.408ms 응답했지만 이는 Navigation SHUTDOWN ACK가 아니다. 실제 Goal은 안전하게 취소했고 ZERO dwell 1.020643s, Scan/Guard/CM TTL 위반 없음. 기존 [#163](https://github.com/silverbjin/axia-robot-safety-ci-public/issues/163)과 같은 독립 미해결 실패 도메인.
- Cycle2 실제 Goal·GUI 2창·실 TTL·Nav/Loc ACK·CM/Guard clean exit0 PASS. 그러나 **한 주기의 성공이 실패를 덮지 못하므로 공개 strict 2/2 FAIL**.
- 현재는 RTF 0.41 및 native publication first pair를 실제 L2에서 재현한 게 아님. 따라서 WSL2 Scan 성능 원인을 수정했다는 성능 개선 수치 **미확보**.

## 3. 실제 변경 범위

**Student 개발 브랜치:** `fix/g07-scan300-owner-pregoal-20261121`, Student source SHA `803cdd99fa0f781998442fbc37be9f59fde82364`.

- `block_B/day07/h01_runtime/tools/p2_g07_scan_wall_pregoal.py` — 읽기 전용 기존 graph 내 12초 /scan, /safety/scan Wall/Sim 및 /clock·/odom 수신, 최초 300ms 위반 시 NO_GOAL HOLD. Gazebo publish 지연 인과분류는 `NOT_MEASURED`.
- `block_B/day07/h01_runtime/tools/test_g07_scan_wall_pregoal.py` — 6개 L0 계약.
- `block_B/day07/h01_runtime/scripts/p2_no_goal_smoke_ci.sh` — 새 옵트인 `AXIA_G07_SCAN_PREFLIGHT_STRICT=1`에서만 기존 TTY consent/Goal 바로 이전 검사 추가, 실패 시 Goal 불허. 기존 정상 시연·TTL/FSM/ROS Goal 소유권 무변경.

**Public 개발 브랜치:** `fix/g07-wsl2-first-scan300-20261121`.

- `tests/fixtures/g07_wsl2_first_scan_wall_gap_20261120.json`, `tests/test_g07_scan_sim_wall_gap_regression.py`, `d06/diagnostic/g07_scan_sim_wall_gap.py`.
- `d06/diagnostic/g07_scan_compact_bundle.py`, `tests/test_g07_scan_compact_bundle.py`.
- `scripts/axia_g07_stabilization_wsl2_final_once.sh` — **CI가 실패한 2/2 Run #44764186378을 정확히 pin한 개발용 HOLD 후보**. 외부 GitHub API 실패/CI 실패이면 `--run`의 어떠한 Gazebo/Goal 전에도 exit3. 12sec Owner 옵트인과 6개 bounded JSON ZIP + SHA256 및 ZIP 8MiB 제한만 추가. **사용자에게 실제 실행 명령으로 배포하지 않는다.**
- `tests/test_g07_scan300_owner_wrapper.py`, `tests/test_g07_stabilization_wsl2_release.py`, 4개 공개 L0 workflow 및 기존 strict Gazebo workflow (모두 브랜치 전용).
- 원본 TAR 및 rosbag은 원래 강사 WSL2에서만 보존, 공개는 숫자 fixture/허용 필드만.

## 4. 남은 미검증/위험 및 다음 단일 작업

1. **#163 첫 Navigation callback enter/finish와 RMW request/response**를 같은 실제 실패 세션에서 관측해, `is_active` 응답이 있어도 `manage_nodes/shutdown`가 ACK되지 않는 원인을 분리. 기존 D06 L0 회귀·진단기 재사용, 무조건 재시도/Timeout 변경/공식 Nav2 포크 금지.
2. 새로운 실제 L2에서 정상 경계뿐 아니라 **RTF 저하를 동반하는 Scan300 회귀**를 최초 source stamp와 함께 실증하고, 모든 Scan300/Guard150/CM120/Odom300/Clock300 및 종료코드·Action ACK를 같은 세션에서 검증한 2/2 PASS 필요.
3. 그때만 기존 WSL2 원샷을 새로 성공한 strict L2의 immutable Run+workflow SHA에 고정 후 사용자 강사 NVIDIA WSLg에서 **한 번** 최종 L3 인수. 최초 현장 오류는 숫자 회귀 RED→GREEN을 먼저 진행.
4. NVIDIA WSLg 서버 SIGSEGV #186, 원본 최초 core stack 미확보 → 독립 HOLD. 이번 성능 패치에서 GPU/Mesa/Ogre2/CPU affinity/LiDAR Hz 임의 변경 없음.

```text
PUBLIC_CI_L0=PASS_SCOPED
PUBLIC_CI_L2=FAIL_NEW_1_OF_2
WSL2_PERFORMANCE_PREFLIGHT=NOT_RUN_ON_OWNER_NEW_SOURCE
OWNER_WSL2_L3=NOT_RUN_NEW_SOURCE
FIRST_SCAN_ROOT_CAUSE=CAUSE_UNDETERMINED
G07_EDUCATIONAL_MVP_BASELINE=ACCEPTED_HISTORICAL
G07_STABILIZATION_RELEASE=HOLD
CERTIFIED_ESTOP=false
MAIN_MERGED=false
```
