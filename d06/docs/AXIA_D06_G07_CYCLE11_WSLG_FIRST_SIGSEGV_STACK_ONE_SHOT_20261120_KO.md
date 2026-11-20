# AXIA D06/G07 Cycle 11 — WSLg Gazebo SIGSEGV 최초 코어 스택: 제한적 단일 진단

작성: 2026-11-20 KST | 공개 Draft PR #177 | 강사 WSL2 L3 최종 인수 **NOT_RUN** | 배포 HOLD

## 1. 원본과 미확정 원인

- 기존 강사 WSL2 NVIDIA D3D12 NO_GOAL 원본 d06-forensic-ab-no-goal-r6YhIvPx.tar.gz SHA256 db6c130218bddbe19bec42a6cde7d46476e404b057e1b66b012beb621a574c98.
- 원본에서 Nav2 Navigation/Localization ACK, CM exit0, Gazebo server exit-11(SIGSEGV) 확인. 최초 충돌 스택 **NOT_CAPTURED**. parent graceful marker만으로 전체 종료 PASS 불가.
- 가설 B1: WSLg D3D12 TLS destructor/libraries early unload, 참고 https://github.com/microsoft/wslg/issues/1533 및 https://github.com/microsoft/wslg/issues/1497. B2: Gazebo server/renderer 종료 순서 충돌, 참고 https://github.com/gazebosim/gz-sim/issues/3335. 해당 보고서들이 AXIA 원본 root 원인이라는 증거 **없음**.
- 최근 C10 실제 Linux Xvfb/CycloneDDS Nav2+Gazebo NO_GOAL L2 Run #44568745545 성공 (raw/safety/native <300ms, Nav/Loc ACK, CM/Gazebo exit0). 이는 강사 NVIDIA WSLg/Gazebo exit-11 해결 증거가 아님.

## 2. 설계된 최소 진단

사용자 현장 오류를 반복 재시도하지 않고 **기존 코어가 있는지 먼저 확인**합니다.

- 진단 스크립트: d06/scripts/axia_d06_g07_wslg_sigsegv_capture_once.sh
- 순수 PID 검색 helper: d06/tools/d06_wslg_latest_gz_sigsegv_core.py
- 기존 프로세스 코어 분석 재사용: d06/scripts/axia_d06_g07_wslg_existing_core_once.sh
- 기존 owner NVIDIA NO_GOAL 진단 그대로 재사용: d06/scripts/axia_d06_g07_wslg_gpu_rtf_compare_once.sh --nvidia-causal
- 기존 코어 목록에서 gz/gz-sim-server SIGSEGV 11 기록을 찾으면 **실제 Gazebo 재실행 없이** 같은 PID를 GDB batch로 분석합니다.
- 기존 기록이 없는 경우에 한해 **WSL2 NVIDIA NO_GOAL 한 번만** 시작합니다. systemd-coredump 수집 경로, coredumpctl, GDB, NVIDIA WSLg/GUI 환경이 확인되지 않으면 아예 시작하지 않고 HOLD.
- 모든 외부 진단 소스는 exact commit SHA 및 Git blob으로 검증. 다른 기존 Gazebo 세션이 있으면 HOLD. 시스템 전역 core_pattern·GPU/Mesa·RMW 설정 변경, sudo/apt 설치, Goal/Twist/Fault/Move, pkill 없음.
- core soft limit 524288 KiB로 제한하여 새 코어 폭증 위험을 낮춤. 실제 OS coredump handler가 파일 크기 제한 및 저장 정책을 다르게 처리할 가능성은 있으며 자동 용량 보증은 아님.
- GDB에서 첫 SIGSEGV, all-thread backtrace(각 최대15 frames), shared-library maps 보존. 원본 process-memory core는 압축 forensic에 **포함하지 않음**. 작은 local TAR/SHA256과 성공/미확정 구분 결과만 저장.
- 캡처 문자열 D06_WSLG_CORE_STACK_CAPTURED_NOT_RESOLVED은 스택이 존재한다는 사실만 의미하며 **근본 원인 수정/WSL2 acceptance 성공 아님**.
- 기존 coredumpctl이 없다면 FAI L-CLOSED: 단일 재실행을 시도하지 않음. 원인 진단을 위한 현장 실행은 1번이지만, 실행기 자체는 아직 WSLg에서 직접 실행된 적 없음.

## 3. RED → GREEN → REFACTOR → REVIEW → COMMIT

- 공개 RED 회귀 d06/tests/test_d06_c11_wslg_core_once.py, source-only first-core scanner 및 one-shot contract, 첫 실제 failing public L0 Run #44571078383: helper/script 파일 미존재.
- HELPER commit 801e6b7be271da55a86101d25924edcafc98deb6, blob 04cc7cab351f4542dba754262912900cd258ec25. parser 테스트는 gz(SIGSEGV11) 중 최신 기록만 PID로 선택하고 다른 SIGABRT 또는 다른 프로세스를 제외.
- NVIDIA capture runner commit a587789e535c5884bf3c1380be65d524218740d4, reviewed finish commit 48c181b6d2a1ec85509d67a8bd8fe5738c6d71c1, blob 05816ad275a6523b32f4ff0738c6994839f20633.
- 공개 GREEN L0 [Run #44571572354](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44571572354): **140/140 PASS**, independent public canary #44571572533 PASS. Static parser fixtures + bash -n + --self-check (no ROS, no Gazebo, no local files) + no-motion/no-global-change contract.
- 코드 리뷰: owner/TRIAGE/helper 세 파일 모두 immutable source blob 검증 후 사용. 진단 실패는 HOLD 판정, 사용자 실행으로 main 병합하지 않음.

## 4. CI/현장 범위 및 인수 게이트

C11: **L0=PASS (ROS/Gazebo/WSLg 실행하지 않음)**.
C10: **actual Linux Xvfb CycloneDDS NO_GOAL L2=PASS** (별도 SHA 26a3a1b299e404d6e0fe9e69312578db356081ab).
C11: **NVIDIA WSLg SIGSEGV first-stack L3-diagnostic=NOT_RUN**, 원본 GPU 원인 B1/B2/B3=UNDETERMINED.

이 스크립트는 승인/배포용이 아닌 **필수 root cause 증거 단일 수집**입니다. 수집 후 최초 실패 stack에 맞춰 최소 수정→공개 CI L0/실 Gazebo L2→강사 WSL2 단일 L3 인수 순서. L2 GREEN을 WSLg GPU 종료 PASS로 승격하면 안 됩니다.

D06_GAZEBO_LIVE_RELEASE=HOLD
AXIA_MVP_DEMO_ACCEPTED=HOLD
CERTIFIED_ESTOP=false
MAIN_MERGED=false

## 5. 최종 사전 검수: GUI 충돌 오인 방지 + 스택 증거 원샷 통합

- Gazebo 공식 headless server 명령은 `gz sim -s`입니다(https://gazebosim.org/docs/harmonic/getstarted/). 기존 최초 크래시가 server -11이므로, `gz` CLI의 SIGSEGV만으로 이를 server core로 승격하는 것은 부정확합니다.
- **수정 1, 서버 전용 원본 식별**: `d06/tools/d06_wslg_latest_gz_sigsegv_core.py`의 `server_only=True`는 실제 `gz-sim-server` executable 또는 `gz` 실행의 `-s`/server-only 명령행을 요구합니다. `gz sim -g` GUI와 불명확한 `gz` wrapper 코어는 제외합니다. C11 스크립트는 오직 `--server-only` 결과만 재사용/추가 수집합니다.
- **RED1** [Run #44645300077](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44645300077): `TypeError: latest_gazebo_sigsegv_pid() got an unexpected keyword argument 'server_only'` 및 WSLg 단일 스크립트의 `--server-only` 부재. **GREEN1** [Run #44645457786](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44645457786) 142/142 L0 PASS, SHA `0846c939336eb812345f7d1018ddc91add17139d`.
- **수정 2, 하나의 TAR로 최초 스택 회수**: 원래 existing-core triage는 사용자의 `~/axia_d06_g07_core_triage/`에 별도 GDB 텍스트 TAR를 만들고, parent one-shot은 그 경로만 기록했습니다. 이는 상위 파일 하나를 전달하면 실제 첫 스택이 빠지는 증거 유실 위험입니다. 검증된 별도 triage TAR의 **SHA256을 확인한 후** `gdb_backtrace.log` 텍스트 최대 160KiB만 추출해 상위 `trace-*.tar.gz`에 함께 보존합니다. 전체 메모리 코어, `before_cores.json`, `after_cores.json`은 포함하지 않습니다.
- **RED2** [Run #44645630350](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44645630350): 단일 아카이브의 `gdb_backtrace.log` 및 nested SHA 검증 경로 부재. **GREEN2** [Run #44645744583](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44645744583) **143/143 L0 PASS**, Runner Canary [#44645744464](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44645744464) SUCCESS. tested code SHA `d603a8520906d2b52f3bfaf0d131e2fd0d312157`.
- 검토 파일 3개: `d06/tests/test_d06_c11_wslg_core_once.py`, `d06/tools/d06_wslg_latest_gz_sigsegv_core.py`, `d06/scripts/axia_d06_g07_wslg_sigsegv_capture_once.sh`. 테스트의 합격 범위는 fixture·구문·자체검사 **L0만**입니다.
- Ubuntu Noble `coredumpctl`은 `--json=short` 조회 및 코어 `dump`를 지원합니다(https://manpages.ubuntu.com/manpages/noble/man1/coredumpctl.1.html). 다만 대상 WSL2가 실제 `systemd-coredump`로 코어를 남기는지, 특정 서버 -11 첫 프레임을 수집할 수 있는지는 **아직 대상 환경에서 측정하지 않았습니다**.
- 공개 CI 실제 L2 기준선은 다른 코드 SHA `26a3a1b299e404d6e0fe9e69312578db356081ab`, Linux Xvfb/CycloneDDS [#44568745545](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44568745545) PASS 그대로 보존. 이번 C11 검수로 Gazebo live L2를 다시 실행했다고 주장하지 않습니다.

### 현장 코어 진단 Gate

코어가 이미 있으면 GDB만 실행하고 Gazebo는 **재실행하지 않습니다**. 코어가 없고 WSLg·GDB·coredumpctl·systemd handler 조건이 충족될 때만 NVIDIA NO_GOAL 정확히 1회 진단합니다. 진행 결과는 하나의 작은 TAR + SHA256로 전달하며, `D06_WSLG_CORE_STACK_CAPTURED_NOT_RESOLVED`는 Stack 확보이지 문제 해결이 아닙니다. 코어/스택 비포착 시 `HOLD`, 동일 오류 현장 재시도 금지.

`D06_GAZEBO_LIVE_RELEASE=HOLD`, `AXIA_MVP_DEMO_ACCEPTED=HOLD`, `CERTIFIED_ESTOP=false`, `WSLG_CORE_STACK=NOT_CAPTURED`, `OWNER_L3=NOT_RUN`.
