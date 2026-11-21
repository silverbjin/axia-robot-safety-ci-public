# AXIA D06/G07 C14 — 실제 GDB SIGSEGV 코어부터 첫 스택·SHA256 증거 TAR까지 검증

작성일: 2026-11-20 KST | 공개 PR #177 Draft / main 미병합 / 사용자 WSL2 실행 요청 없음

## 1. 목표와 범위

실제 NVIDIA WSLg의 Gazebo server -11(SIGSEGV) 코어가 **아직 확보되지 않았기 때문에**, 코어가 확보되었을 때 기존 진단기가 올바른 최초 GDB 스택을 얻고 메모리 코어를 빼고 압축·해시 검증 가능한지 **공개 CI의 진짜 Ubuntu 24.04 GDB 실행**으로 미리 검증한다. 이 과정은 WSLg GPU 충돌 자체의 재현/해결이 아니다.

전제 성공:
- C10 실제 Linux Xvfb/CycloneDDS/Jazzy/Harmonic/Nav2/Waffle NO_GOAL L2 [#44568745545](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44568745545) PASS.
- C12 실제 systemd-coredump CLI 설치 확인 및 누락 회귀.
- C13 일회성 Ubuntu 24.04 컨테이너에서 실제 Owner `--check-tools` 경로를 실행하여 도구 의존성 증명.

## 2. TDD RED → GREEN: 최초 실패 경계

- 신규 테스트 `d06/tests/test_d06_c14_native_core_evidence_pipeline.py`, 정확히 테스트하는 범위: **실제 SIGSEGV signal** → `gdb generate-core-file` → 기존 `d06/scripts/axia_d06_g07_wslg_existing_core_once.sh --core ... --exe ...` → 처음 스택과 안전한 SHA256 TAR.
- L0 **RED** [#44651053003](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44651053003): 실제 워크플로에 `gcc`, 합성 SIGSEGV core 생성, `sha256sum -c`, `tar -xOzf`와 원본 메모리 미포함 증거 없음.
- 최초 구현 실패: YAML `run: |` 내부 here-document 들여쓰기 불일치 [#44651213417](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44651213417), 텍스트 YAML 구문 검증 단계에서 차단. 최소 들여쓰기 정정.
- 다음 실제 CI 실패: `/tmp/axia-c14-synthetic-sigsegv.c: fatal error: signal.h: No such file or directory` [#44651287729](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44651287729). Ubuntu 최소 이미지에는 gcc 바이너리만으로 C 헤더 사용 가능하다고 볼 수 없으며 `libc6-dev`가 필요함. 오직 일회성 Linux CI 컨테이너 패키지 목록에 `libc6-dev`를 추가하고 정적 계약에 다시 편입; WSL2에 설치하지 않음.
- **GREEN 공개 L0** [#44651428863](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44651428863) **155/155 PASS**, exact tested SHA `4e5a410a60cf1bcace4ceaf884c41ca84620081c`, Runner Canary [#44651428891](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44651428891) PASS.

## 3. 실제 Ubuntu 24.04 GDB 증거 체인 GREEN

[**Run #44651428861**](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44651428861), 같은 SHA, 공개 GitHub 호스티드 Ubuntu-24.04 runner의 일회성 `ubuntu:24.04` Docker 컨테이너.

실행한 경계:
1. 서명 검증된 Ubuntu 패키지 설치 (`systemd-coredump gdb mesa-utils curl git python3 procps coreutils grep sed tar gcc libc6-dev`).
2. 저장소 체크아웃 SHA가 `GITHUB_SHA`와 같고, read-only mount된 실제 Owner의 `bash -n` → `--self-check` → `--check-tools` GREEN.
3. 작은 C 프로그램 `#include <signal.h>`, `raise(SIGSEGV)`를 `gcc -g -O0`로 컴파일.
4. **실제 GDB로 프로그램을 실행**하고 SIGSEGV에 중단된 프로세스의 `generate-core-file /tmp/axia-c14-synthetic.core` 실행, 실제 코어 파일 `test -s`로 검사.
5. 기존 실제 `axia_d06_g07_wslg_existing_core_once.sh --core /tmp/axia-c14-synthetic.core --exe /tmp/axia-c14-synthetic-sigsegv` 실행.
6. 실제 로그에 `D06_WSLG_CORE_TRIAGE_STACK=CAPTURED`, `Program terminated with signal SIGSEGV, Segmentation fault.`, 최초 GDB `#0` 프레임을 검사.
7. 실제 `core-XXXXXXXX.tar.gz` SHA256 `sha256sum -c` GREEN, `tar -tzf`에 `gdb_backtrace.log` 존재, `summary.txt`에 `core_not_archived=true`, raw `private.core`/합성 core 미포함. 출력 `D06_C14_REAL_GDB_SIGSEGV_CORE_AND_TEXT_TAR_GREEN`.

이 합성 GDB 스택은 사용자 WSL2와 관계 없으며 원본 시스템/Gazebo 라이브러리의 크래시 원인을 뜻하지 않는다.

## 4. 변경 파일 및 검증 경계

- `d06/tests/test_d06_c14_native_core_evidence_pipeline.py` (실제 C14 계약 및 중간 false dependency 검출)
- `.github/workflows/axia-d06-g07-wslg-lidar-rtf-isolation-l0-20261118.yml` (L0 테스트 연결)
- `.github/workflows/axia-d06-c12-coredump-cli-compat-ubuntu2404.yml` (실제 합성 코어 및 기존 분석기 통합 CI)

강사 WSL2 설정, 설치 패키지, GPU, CUDA, Mesa/OGRE2, ROS2, Nav2, TurtleBot3, Safety/Guard/CM 코드, Goal/fault 제어, TTL300/120/150 모두 변경 없음. `GDB --core` 모드만 L1에서 검증한 것이며 `coredumpctl` **실제 systemd handler/journal에서 코어 생성·조회**와 `Gazebo server -11 WSLg root cause`는 미검증.

### 기존 C10 실제 L2 코드 재사용 근거

GitHub compare `26a3a1b299e404d6e0fe9e69312578db356081ab...4e5a410a60cf1bcace4ceaf884c41ca84620081c` 기준 변경은 공개 L0/L1 workflow, C11–C14 진단 스크립트·테스트·문서 및 코어 PID parser뿐. **실제 ROS/Nav2/학생 Scan 런타임 코드와 원본 시나리오/기존 C10 NO_GOAL L2 실행 워크플로는 변경되지 않았음**. C10 L2 기존 성공 증거를 보존하고 C14에서 같은 Gazebo를 무의미하게 재실행하지 않음.

## 5. 남은 인수 Gate

- `C14_PUBLIC_L0=PASS (155/155)`
- `C14_REAL_NOBLE_GDB_CORE_TO_TAR_L1=PASS`
- `C10_PUBLIC_REAL_GAZEBO_NO_GOAL_L2=PASS (UNCHANGED runtime)`
- `SYSTEMD_COREDUMP_JOURNAL_BACKEND=NOT_VERIFIED`
- `NVIDIA_WSLG_GPU_GAZEBO_FIRST_SIGSEGV_STACK=NOT_CAPTURED`
- `WSLG_NVIDIA_NATIVE_SERVER_SHUTDOWN=NOT_VERIFIED`
- `OWNER_WSL2_NO_GOAL_L3=NOT_RUN`
- `MOVING_GOAL_CM120_GUARD150_L3=NOT_RUN`
- `D06_GAZEBO_LIVE_RELEASE=HOLD`
- `AXIA_MVP_DEMO_ACCEPTED=HOLD`
- `CERTIFIED_ESTOP=false`
- `MAIN_MERGED=false`

WSLg GPU 종료 크래시까지 CI에서 검증하려면 **진짜 Windows/WSL2+WSLg NVIDIA 대상 동등 러너** 또는 그 동등한 실제 렌더링 환경의 검증 실행권이 필요함. 일반 Linux Xvfb, 코어 합성, 파일 문자열 검사로는 이를 대체할 수 없음. 사용자의 WSL2는 최종 인수까지 건드리지 않는다.
