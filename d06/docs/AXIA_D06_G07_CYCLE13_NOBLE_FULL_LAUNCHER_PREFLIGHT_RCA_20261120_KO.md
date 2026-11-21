# AXIA D06/G07 C13 — 실제 Ubuntu 24.04 전체 원샷 의존성 CI 검증 중간 보고

작성 2026-11-20 KST. 공개 Draft PR #177, main 미병합. 사용자 WSL2 최종 인수 미실행.

## 1. 기존 오류와 검증 결함

강사 WSL2 원본 `D06_WSLG_CORE_ONCE_HOLD_MISSING_TOOL=coredumpctl`, `RC=3`. 이 로그는 Gazebo 또는 GDB 크래시가 아닌 사전 의존성 누락. C12는 shell mock와 실제 Ubuntu 24.04에서 **coredumpctl 설치/CLI 옵션**을 검증했으나, `gdb`/`glxinfo`/`git`/프로세스 도구 등 **배포 스크립트 전체** 의존성 종단 검증은 없었음.

C13 목표: 사용자 WSL2를 테스트 머신으로 사용하지 않고 공개 CI 일회성 clean Noble에서 **같은 GitHub SHA로 체크아웃한 진짜 C11/C12 배포 스크립트 자체**의 `--self-check`와 `--check-tools`를 실제 바이너리로 검증. 코어 handler 및 WSLg GPU 크래시는 별도 Gate.

## 2. TDD RED → GREEN / 원본 출력

**RED:**
- 새 `d06/tests/test_d06_c13_full_cli_noble_smoke.py`: `actions/checkout`, `$GITHUB_SHA` 확인, read-only bind-mount, 필수 CLI 전체 설치, 실제 원샷 `bash -n`/`--self-check`/`--check-tools`, 명확한 제한 메시지 요구.
- 공개 L0 [#44650089635](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44650089635): 2개 실패, 실제 컨테이너 워크플로에 read-only source mount와 `gdb` 등 전체 도구 설치 부재.
- 최초 코드 수정 후 실제 CI [#44650235852](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44650235852) 실패: Ubuntu 패키지 설치 자체는 성공했으나 `bash: /workspace/d06/scripts/axia_d06_g07_wslg_sigsegv_capture_once.sh: No such file or directory` rc127. 원인은 **GitHub Action workflow에서 checkout을 하지 않고 Docker mount**했기 때문. 사용자 WSL2가 아니라 CI에서 이 오류를 확인.
- 이어 기존 C12 테스트가 한 줄 Docker/apt 명령을 기대한 stale 문자열 계약으로 실패. 테스트 범위를 실제 설치/바인드 마운트 조건 중심으로 좁혀 정정. 제품 런타임/안전 제한 변경 없음.

**GREEN:**
- `.github/workflows/axia-d06-c12-coredump-cli-compat-ubuntu2404.yml`에서 SHA pinned `actions/checkout`, `git rev-parse HEAD == GITHUB_SHA`, 원본 스크립트 파일 존재 사전 확인, read-only bind mount를 거쳐 `ubuntu:24.04` 일회성 컨테이너 안에서 Ubuntu 공식 패키지 `systemd-coredump gdb mesa-utils curl git python3 procps coreutils grep sed tar` 설치.
- 실제 설치 후 `dpkg-query` 버전, `Status: install ok installed`, `coredumpctl --help`의 `--json` 옵션 확인.
- **실제 스크립트** `bash -n`, `--self-check`→`HOST_DEPENDENCIES_NOT_TESTED`, `--check-tools`→`D06_WSLG_CORE_ONCE_TOOLCHAIN_L0_OK_BACKEND_NOT_VERIFIED` 출력까지 확인. GUI/Gazebo/WSLg 실행·전역 설정 변경 없음.
- 공개 동일 SHA `5f0e0e47a404ae04fced6bde4772b1cd9d52a12b` [L0 #44650542812](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44650542812) **152/152 PASS**.
- [실제 Noble container #44650542929](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44650542929) **PASS**, 실제 `systemd-coredump 255.4-1ubuntu8.19`, `D06_C13_ACTUAL_NOBLE_PINNED_LAUNCHER_CLI_GREEN`, `D06_C13_NOT_WSLG_GPU_NOT_REAL_CORE_NOT_GAZEBO` 출력. Public runner Canary [#44650542823](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44650542823) PASS.

## 3. 최소 변경 / 검증 한계 / 다음 Gate

변경 파일:
- `d06/tests/test_d06_c13_full_cli_noble_smoke.py`
- `d06/tests/test_d06_c12_field_missing_coredumpctl.py` (기존 계약 stale 문자열만 정정)
- `.github/workflows/axia-d06-c12-coredump-cli-compat-ubuntu2404.yml` (source checkout + official packages + 실제 script 실행)
- `.github/workflows/axia-d06-g07-wslg-lidar-rtf-isolation-l0-20261118.yml` (L0 연결)

실제 CI **CLI 전제조건은 PASS**이나, `coredumpctl`의 실제 systemd socket/journal 접근 및 대상 서버 SIGSEGV core 유무는 아직 확인되지 않음. WSL2 NVIDIA WSLg 그래픽 라이브러리 crash root cause/실제 종료/Moving Goal CM120·Guard150 실증도 미검증. 이전 C10 `Linux Xvfb+CycloneDDS` 실제 Nav2/Gazebo NO_GOAL L2 [#44568745545](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44568745545) 증거는 유지하며, C13에서 실제 Gazebo를 재실행했다고 보고하지 않음.

**다음 단위**: 사용자 WSL2 의존성 문제를 이전하기 전에, 실제 `GDB`가 생성한 **작고 합성된 SIGSEGV core**를 CI Ubuntu에서 기존 `--core --exe` 진단기에 넣어 최초 스택과 SHA256 압축 증거가 생성되는지 검증. 코어 수집 backend와 NVIDIA WSLg 동등 환경은 그 결과로 대체하지 말 것.

C13_PUBLIC_L0=PASS
C13_NOBLE_ACTUAL_DEPENDENCY_CLI=PASS
C13_REAL_GAZEBO_L2=NOT_RUN (C10 PROVEN SOURCE PRESERVED)
C13_SYSTEMD_CORE_BACKEND=NOT_VERIFIED
C13_WSLG_GPU_NATIVE_SHUTDOWN=NOT_VERIFIED
D06_GAZEBO_LIVE_RELEASE=HOLD
AXIA_MVP_DEMO_ACCEPTED=HOLD
CERTIFIED_ESTOP=false
MAIN_MERGED=false
