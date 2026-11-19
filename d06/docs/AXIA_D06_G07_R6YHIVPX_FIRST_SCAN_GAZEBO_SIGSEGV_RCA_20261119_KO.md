# AXIA D06/G07 — r6YhIvPx WSLg 최초 Scan300 및 Gazebo SIGSEGV 원본 RCA / 출고 HOLD

- 기준: 2026-11-19, ROS 2 Jazzy / Gazebo Harmonic / TurtleBot3 Waffle / 공식 Nav2 / **NVIDIA RTX 2060 Max-Q WSLg D3D12**
- 수집한 강사 원본: `d06-forensic-ab-no-goal-r6YhIvPx.tar.gz`; SHA256 `db6c130218bddbe19bec42a6cde7d46476e404b057e1b66b012beb621a574c98` (동봉 sidecar와 실제 바이트 일치)
- 원본 내부에는 실제 20초 Scan/Clock 수신 쌍과 종료 증거가 있지만 **Gazebo core backtrace와 원본 전체 Owner 로그는 없음**.
- 안전 범위: **NO_GOAL**, Goal/Fault/Velocity 금지, Scan TTL **300ms 불변**, CM120/Guard150 불변.
- 결과: `D06_GAZEBO_LIVE_RELEASE=HOLD`, `AXIA_MVP_DEMO_ACCEPTED=HOLD`, `CERTIFIED_ESTOP=false`, main 미병합.

## 1. 동일 WSLg 세션의 실제 판정

| 항목 | 실측 | 판정 |
|---|---|---|
| dual-topic 센서 관측 | 20.008초 | 완료 |
| Raw `/scan` | 151개 / 최대 수신 297.708ms | 해당 창 PASS |
| Safety `/safety/scan` | 150개 / 최대 수신 **303.153ms** | **Scan300 FAIL** |
| 안전 거리 | CLEAR150/150, front1.414288m / side2.519014m | 거리 CLEAR, TTL와 별개 |
| Nav2 Navigation / Localization | ACK 3.080136s / ACK 0.325651s | PASS |
| Collision Monitor | 실제 child exit0 | PASS |
| native Gazebo / ROS read-only witness | exit0/exit0, unsubscribe 및 handoff ACK | PASS |
| **Gazebo server `gz sim -r -s`** | 원본 launch 483행, **exit -11 SIGSEGV** | **독립 FAIL** |
| Parent `P2_L2_GRACEFUL_TEARDOWN` | 실제 gz child -11을 덮지 못함 | 전체 종료 HOLD |
| Moving Goal / CM120→Guard150 | 미실행 | NOT_VERIFIED |

### 최초 학생 Safety Scan 위반의 **정확히 동일한 source-stamp pair**

실제 `forensic/scan_receipts_compact.json`의 Student Safety 최초 위반 index129:
- sensor source stamp: **68.901s → 69.000s** (sim 99ms)
- native Gazebo transport `/scan`: **287.568ms** host receive gap
- 독립 ROS raw: **290.480ms** host receive gap
- 독립 ROS safety: **305.529ms** host receive gap
- Student ROS safety: **303.153ms** host receive gap
- 원본 native `/clock` 동일 sim stamp의 host 수신: 7963.970236s → 7964.248479s = 278.243ms, **같은 source stamp 경계의 순간 관측 RTF 후보 0.099/0.278243≈0.3558**. Clock·LiDAR 수신기의 처리 시각은 다르므로, publisher 실제 발행 간격의 확정값으로 다루지 않음.
- 독립 후단 전달 지연과 native upstream 지연이 **함께** 존재하는 후보. 어떤 OS 스케줄러/DDS 렌더러가 최초 인과 원인인지는 **UNDETERMINED**.
- 전체 ROS Clock RTF **0.752343** 및 별도 READY proxy 구간 국소 RTF **0.556483**은 최초 학생 위반과 다른 집계 경계. 혼용 금지.
- `first_failure_stage=NATIVE_ARCHIVE_VALIDATION`은 Owner 래퍼의 나중 수집 단계일 뿐 최초 안전 위반 아님.

## 2. 기존 브랜치·공개 L2 재사용 검토

1. **D06 기존 Draft PR #177** `fix/d06-wslg-lidar-vs-rtf-ci-20261118`. 실제 Xvfb Gazebo/Nav2 **NO_GOAL** L2 [#44503070174](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44503070174)에서는 Scan 20.007s / Raw126.182ms / Safety125.575ms, Nav/Loc ACK, CM0/Gazebo0로 성공. 이것은 Linux 소프트웨어 렌더링 조건이며 **NVIDIA WSLg D3D12의 성공 증명이 아님**.
2. **학생 성능 Draft PR #47** `perf/d08-wslg-rtf-sensor-profile-20261118`: D08 RGBD 30→10Hz와 WSLg GPU 경로 연구, RTF 개선 후보. D06 원래 **10Hz LiDAR**나 CM/Guard/Scan TTL 변경에 이 결과를 이식하지 않음. 현재 r6 원본의 실제 NVIDIA Ogre2 증거를 보존.
3. **G07 WSLg 복원 브랜치** `rollback/g07-dual-gui-20261115-proven-xvfb`: Ubuntu Xvfb llvmpipe와 WSLg GPU native EGL 분리 규칙을 재사용. GPU 센서에 강제 llvmpipe 주입하지 않음.
4. **공개 이슈 #185 / #186**: Collision Monitor -11, Gazebo -11은 서로 다른 실패 도메인. r6에서 CM은 clean exit0, Gazebo만 -11.

관련 upstream 리서치: [microsoft/wslg #1533](https://github.com/microsoft/wslg/issues/1533), [#1497](https://github.com/microsoft/wslg/issues/1497)는 WSLg D3D12 / EGL 종료 중 libd3d12core TLS destructor 및 SIGSEGV 재현 보고를 포함함. [gazebosim/gz-sim #3335](https://github.com/gazebosim/gz-sim/issues/3335)는 WSLg Harmonic crash 보고. **r6에는 Gazebo backtrace가 없으므로 이들과 동일 원인이라고 주장하거나 LD_PRELOAD 같은 우회 패치를 즉시 출고하면 안 됨.**

## 3. RED→GREEN (범위: 정확한 첫 실패 분류 / 원본 보존)

- 원본 기준 SHA `b7f417b448ebf8e5cff07d9dd7902baed23959a6`.
- 대상 경로: `d06/tests/test_d06_forensic_bundle_once.py`; `d06/scripts/axia_d06_g07_wslg_gpu_rtf_compare_once.sh`.
- 검증 명령(공개 CI Linux runner): `python3 -m unittest discover -s d06/tests -p 'test_d06_forensic_bundle_once.py' -v` 및 `bash -n d06/scripts/axia_d06_g07_wslg_gpu_rtf_compare_once.sh`. 정적 계약 전체는 `.github/workflows/axia-d06-g07-wslg-lidar-rtf-isolation-l0-20261118.yml`의 `six-independent-axes`.
- **의도한 RED** [#44522677801](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44522677801): 신규 r6 fixture에서 `KeyError: first_actionable_safety_gate`. 초기 fixture의 문자 그대로 `\\n` 오류는 별도 수정하여 정상 RED와 구분.
- **GREEN 및 REFACTOR** [#44523019624](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44523019624): **104/104 L0 PASS**, `AXIA_D06_G07_LIDAR_RTF_ISOLATION_L0_PASS_NO_ROS_NO_GAZEBO_NO_GOAL`. Runner canary [#44523019679](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44523019679) **success**.
- 최종 검증 코드 HEAD **`4882f6a219ffe999d4d4db6ca7a40415341bd476`**. 기준 HEAD 대비 변경 파일 정확히 2개(코드 13행 추가 / 테스트 54행 추가). **학생 Waffle/official Nav2/Gazebo, 300/120/150ms TTL, Goal·Fault·runtime·shutdown 제어 불변**.
- 새 forensic 키: `first_actionable_safety_gate`, `native_shutdown_first_crash`, `gazebo_server_crash_stack=NOT_CAPTURED`, `causal_root_confirmed=false`.
- 이 수정은 **오진·증거 누락 문제의 GREEN**이지 실제 WSL2 GPU Scan 지연 또는 Gazebo SIGSEGV를 해소한 증거가 아님.

## 4. 남은 최초 실제 실패의 해결 절차와 출고 게이트

### A. Scan300
원본 동일 pair (LiDAR native287.568ms, ROS safety305.529ms, Student303.153ms, Clock≈RTF0.3558)에서 Gazebo 서버/렌더 작업·CPU 사용/콜백 대기 중 어느 부분이 시간을 쓰는지 좁혀야 함. 현장 반복 재시도 전에 **공개 CI에서 특정 재현 가능한 시간 경계가 fail-closed하는지 RED→GREEN**으로 검증하고, 수정이 실제 노드 간 안전 TTL을 개선하는지 **실제 Gazebo L2**로 검증.

### B. Gazebo server SIGSEGV
원본에 core stack이 없으므로 실제 첫 SIGSEGV 진입 주소와 라이브러리를 확인해야 함. 기존 Gazebo ServerControl stop ACK/ordered lifecycle/observer unsubscribe 경로는 보존. 단순 `exit -11`만으로 WSLg TLS bug·GPU driver 결함을 판정하거나 `LD_PRELOAD`를 적용하지 않음. 새로운 원인 후보가 확인되면 **재현 가능한 최소 종료 사례**를 CI에 편입하고 같은 프로세스의 실제 exit0을 L2로 확인.

### C. 출고
- **공개 L0 104/104 PASS** = 증거 분류·회귀 검증만.
- 기존 real **Gazebo L2 PASS** = 다른 GPU/조건의 이전 고정 runtime에 한정.
- **WSL2 L3 = 아직 실패**(r6 Owner Scan303.153ms + gz-11). 새 physical 변경, 효과 A/B, 정상 종료의 **새 WSL2 L3 결과 없음**.
- NO_GOAL이 모두 통과한 후에만 Moving G07의 **CM120ms→Guard150ms→Scan300ms** 노드 간 주기, Stop·Cancel·odom dwell을 인수. 인증 E-Stop 아님.
- **원본 SHA 보존**, 큰 로그 재수집 지양; core나 최초 위반 주변 작은 압축 증거만 유지. 사용자 승인 전 main 병합 및 학생 배포 금지.
