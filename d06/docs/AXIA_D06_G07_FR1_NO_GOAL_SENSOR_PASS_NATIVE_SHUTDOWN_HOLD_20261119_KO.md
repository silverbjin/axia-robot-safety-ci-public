# AXIA D06/G07 — fr1FN4YJ 실제 WSL2 NO_GOAL 인수 결과 및 최소 회귀

**작성:** 2026-11-19. **목표:** 공개 CI 성공과 강사 NVIDIA WSL2 실제 인수를 분리하고, 첫 실패 경계를 재현 가능한 회귀로 고정.

## 1. 원본·무결성

- 사용자 업로드: `d06-forensic-ab-no-goal-fr1FN4YJ.tar.gz` 및 `.sha256`.
- 원본 SHA256 **`65fef7814cf9d76f2167eaab28dfa548515cec320c6d8537707f6acd68b1b03a`**, 사이드카 일치. 44KB 압축, native 수신·ROS 수신 JSONL 포함.
- 학생 SHA `8e19742fd7bd80db73a37dc7b1d798768dc33e2a`. 이전 `TCljt2Qc`의 Probe Git blob 불일치가 해소된 후 실제 ROS/Gazebo 구동이 수행됨.
- NVIDIA WSLg D3D12 GPU 렌더러 확인. **Goal 미전송**, fixture 이동 없음. 인증 E-Stop 아님.

## 2. 검증 범위·실측

| 항목 | 원본 수치 | 판정 |
|---|---|---|
| 두 Scan topic READY 후 관찰 | 20.003s | PASS |
| Raw Scan host receipt 최대 gap | 255.948ms / 171개 | 300ms 범위 PASS |
| Safety Scan host receipt 최대 gap | 256.287ms / 171개 | 300ms 범위 PASS |
| Safety CLEAR | 171/171 | PASS |
| 전방/측면 median | 1.414668m / 2.521118m | PASS |
| Navigation/Localization Lifecycle shutdown ACK | true/true | PASS |
| Collision Monitor 자식 종료 | exit0 | PASS |
| read-only ROS witness 종료 | exit0 | PASS |
| read-only Gazebo Transport Python native witness 종료 | **exit134 (SIGABRT)** | FAIL |
| witness handoff ACK | 없음 | FAIL |
| Gazebo Sim 서버 자식 종료 | **exit -11 (SIGSEGV)** | FAIL |
| Guard / Supervisor 자식 종료 | exit1 / exit1 | FAIL |
| Owner 실행 RC, 인수 결과 | 3, `no_goal_acceptance=false` | HOLD |

**최초 실패:** `D06_G07_WSLG_WITNESS_NONCLEAN_HANDOFF_HOLD`, Owner 원본 로그 4행에서 D08-reused `d08_gz_native_scan_probe.py` 프로세스 PID1480이 `Aborted (core dumped)`로 종료. 원본 native stdout/stderr excerpt에 **`terminate called without an active exception`**. ROS read-only observer는 exit0. `G07_READONLY_WITNESSES_STOPPED` ACK는 없으며, 그 뒤에야 Nav2 ACK true 및 Gazebo 서버 exit -11이 별도 기록됨. 이는 NO_GOAL 센서 20초 검사 성공을 전체 인수로 승격할 수 없게 만드는 실제 native/teardown 실패.

**별도 타이밍 사실:** startup 전체 최초 ROS Safety callback gap418.185ms는 native gap114.160ms 이후, `NAV2_ACTION_READY` 이후 PROXY 첫 native gap424.091ms와 local Clock RTF0.346은 *Student strict 20초 관찰창 시작 시각보다 전*. 학생 20초 관찰 결과에 첫 TTL 위반은 없음. 다른 계층의 PROXY 지연을 Student 실제 안전창 첫 실패로 혼동하면 안 됨. 그러나 실제 Moving Goal 동안 Scan300/CM120/Guard150 주기 안정성은 미검증.

**근본 원인 한계:** Gazebo Transport Python binding/native Node 종료 중 C++ `std::terminate`를 시사하는 문자열과 signal 134는 직접 증거이지만, 최초 C++ stack/backtrace가 원본 압축에 없으므로 native witness 자체의 내부 자원 해제 순서가 원인인지는 미확정. Gazebo server -11 역시 별도 core stack이 없음. 외부 WSLg GPU 렌더러의 인과성은 입증되지 않음. 공식 Gazebo Transport 13 Python API는 C++ binding 및 callback 경쟁 위험을 문서화함: https://gazebosim.org/api/transport/13/python.html. 이는 재현 가능성을 안내하는 배경이지 해당 현장 crash의 원인 확정이 아님.

## 3. RED→GREEN→REFACTOR→REVIEW→COMMIT

1. 동일한 공개 CI 브랜치 `fix/d06-wslg-lidar-vs-rtf-ci-20261118`에서 별도 시뮬레이션 없이 `d06/tests/test_d06_forensic_bundle_once.py::test_fr1_fresh_scan_clear_but_native_witness_134_gazebo_minus11_stays_hold`를 추가. 같은 원본 값(sensor CLEAR20.003s, native witness134, ROS witness0, Gazebo-11, Guard/Supervisor1)을 fixture로 재현. **RED:** [Run #44471217962](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44471217962), forensic summary에서 witness exit 필드가 누락되어 KeyError.
2. 기존 실행기의 최소 read-only 요약에 `native_ros_witness_exit_code`, `native_gz_witness_exit_code`, `native_gz_witness_first_error`, `native_witness_clean` 필드 추가. 원본 log 및 gz render excerpt를 **중복 시뮬레이션 없이 재사용**. 스캔 TTL/부하 변경 없음.
3. 초기 GREEN에서 정규식 이스케이프 결함 발견 [#44471378811](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44471378811) → 회귀 수정.
4. **GREEN L0 89/89** [Run #44471595910](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44471595910), canary [#44471595810](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44471595810). 실제 ROS/Gazebo L2는 이번 코드 변경에 대해 NOT_RUN. 새 증거 게이트는 정확히 현장 NO_GOAL HOLD를 유지.
5. 공개 Issue #186에 현장 원본 수치와 별도 최초 native 에러·서버 종료 실패를 기록. 기존 [NO_GOAL strict 실제 L2 두 세션 #44461092763](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44461092763), [#44461627846](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44461627846)의 성공 기록은 그대로 보존하되, 사용자 WSL2 NVIDIA L3와 동일한 검증으로 승격하지 않음.

## 4. 다음 시연 인수 게이트

- **Moving Goal 주행 허가 금지:** `AXIA_MVP_DEMO_ACCEPTED=HOLD`, `D06_GAZEBO_LIVE_RELEASE=HOLD`, `CERTIFIED_ESTOP=false`.
- 우선 공개 CI/기존 확보 증거에서 종료 실패를 재현 가능한 최소 구성으로 좁힘: Native Gazebo Transport `SIGTERM→SIGABRT` 중단, 공식 Gazebo server 종료 SIGSEGV는 별도 테스트/코어 증거로 분리. Guard/Supervisor exit1의 최초 원인도 종료 문맥과 별개로 분석할 것.
- 수정 후 실제 Gazebo L2에서 sensor20s Scan300/Navigation+Localization ACK/CM child0/Gazebo child0/관찰기0을 **같은 세션**에 증명해야 NVIDIA 현장 NO_GOAL 단일 재인수 후보가 됨.
- 현장 NO_GOAL 성공 후에만 기존 승인된 G07 Moving Goal 실행기를 재사용하여 CM120ms·Guard150ms 노드 간 주기, 최초 안전 전이, 실물리 정지·Goal cancel을 검증. 새 Planner/Supervisor/Fault Injector 개발 금지.
- 학생/강사 정답과 학생 TODO 분리 정책 유지. main 병합은 사용자 승인 전 수행하지 않음.
