# AXIA D06/G07 Cycle 12 — WSL2 coredumpctl 누락의 CI 사전검출·출고 게이트 개선

작성일: 2026-11-20 KST | 저장소: silverbjin/axia-robot-safety-ci-public | Draft PR #177

## 1. 사용자가 제출한 실제 현장 오류

```text
D06_WSLG_CORE_ONCE_L0_PASS_NO_ROS_NO_GAZEBO
AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false
D06_WSLG_CORE_ONCE_HOLD_MISSING_TOOL=coredumpctl
AXIA_D06_CORE_DIAGNOSTIC_RC=3
AXIA_MVP_DEMO_ACCEPTED=HOLD
```

**관측 사실**: 다운로드한 SHA-pinned 진단 스크립트의 static `--self-check`는 성공했고, `--run-once`에서는 `for exe in ... coredumpctl ...` 검사에서 `command -v coredumpctl`이 실패하여 **Gazebo/GDB/코어 조회 이전에 rc=3(HOLD)** 로 종료됨. 이 메시지는 SIGSEGV 재발 또는 GPU/렌더링 오류가 아니며, 시스템 의존성이 누락된 **현장 실행기 준비 결함**이다. 코어가 수집/존재하는지는 해당 로그에서 결정할 수 없다.

Ubuntu 24.04 Noble 공식 `coredumpctl` 제공 패키지는 `systemd-coredump`(universe). CLI 설치, systemd PID1 사용, `kernel.core_pattern` handler 설정, journal/core 접근권한, 실제 SIGSEGV 기록은 **별개의 증거 Gate**이다.

공식 근거:
- https://packages.ubuntu.com/noble/systemd-coredump
- https://manpages.ubuntu.com/manpages/noble/man1/coredumpctl.1.html
- https://github.com/systemd/systemd/blob/main/docs/COREDUMP.md

## 2. 실패가 CI를 통과했던 구조적 원인

원래 `d06/scripts/axia_d06_g07_wslg_sigsegv_capture_once.sh --self-check`는 시작 즉시 `L0_PASS_NO_ROS_NO_GAZEBO`를 반환하고 종료했다. 의존성 확인은 `--run-once` 안의 WSL2/GUI gate 통과 **이후**였다. Public L0는 `bash -n`, `--self-check`와 코드 문자열 계약만 통과했으며 **CLI가 없는 Ubuntu 24.04 clean-room**에서 실제 의존성 실패 경로를 실행하지 않았다.

따라서 기존의 L0 PASS는 설계대로 **정적 계약 PASS**였지만, 결과 안내/배포 의사결정에서 이를 runtime preflight PASS로 해석한 것이 근본적인 작업 흐름 결함이다. 현장에 처음 전달한 원샷이 이 조건을 발견한 것은 검증 책임이 사용자 WSL2로 전가된 사례.

## 3. 최소 변경과 검증 범위

수정한 파일:
1. `d06/scripts/axia_d06_g07_wslg_sigsegv_capture_once.sh`: `--self-check`에 `HOST_DEPENDENCIES_NOT_TESTED` 명시. 실제 WSL2 `--run-once`와 공개 CI에 공통인 `check_required_tools` 추가. `--check-tools`는 ROS/Gazebo/WSL2 우회가 아닌 **순수 CLI 도구 계약 검사**이며 WSL2 acceptance를 뜻하지 않음. `coredumpctl` 누락 시 `HOLD_MISSING_TOOL=coredumpctl`, `MISSING_UBUNTU_PACKAGE=systemd-coredump`, no Gazebo, rc3. CLI 도움말에 `--json`이 없으면 독립적으로 HOLD.
2. `d06/tests/test_d06_c12_field_missing_coredumpctl.py`: 실제 bash를 **격리된 PATH**에서 6개 시나리오로 실행. 필수 `coredumpctl` 누락/다른 필수 `gdb` 누락/JSON 옵션 미지원/모의 도구 존재/정적 selfcheck 범위/패키지 매니페스트 비어있으면 FAIL 회귀. 시스템/GPU/ROS 변경 없음.
3. `.github/workflows/axia-d06-g07-wslg-lidar-rtf-isolation-l0-20261118.yml`: 위 회귀를 기존 공개 L0에 연결.
4. `.github/workflows/axia-d06-c12-coredump-cli-compat-ubuntu2404.yml`: 별도의 실제 **ubuntu:24.04 일회성 Docker 컨테이너**에 systemd-coredump 정식 패키지 설치, CLI와 --json, 패키지 이름/버전 및 'install ok installed'를 확인. 설치는 호스티드 runner나 강사 WSL2 시스템을 변경하지 않음. Docker PID1에 systemd가 구동된 것은 아니므로 코어 handler 검증으로 오판하지 않음.

**안전 범위**: WSL2 Owner RMW/메사/GPU 환경변수 수정 없음, sudo/apt 자동 설치 없음, Goal/velocity/fault 미전송, Scan300/CM120/Guard150 불변, 원본 forensic 미수정, main 미병합.

## 4. RED → GREEN → REFACTOR → REVIEW → COMMIT 증거

- **RED** [public L0 Run #44648256533](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44648256533): `--check-tools`가 없어 `USAGE`와 rc2를 반환. `self-check`가 HOST_DEPENDENCIES_NOT_TESTED를 표시하지 않음. 새 회귀 5/5 의도한 FAIL.
- **GREEN1** [public L0 Run #44648451552](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44648451552): **148/148 PASS**, source SHA `01cb9c5b8bd35ac33acc0bba073f239318aa5726`. 누락/모의 성공/CLI 옵션 미지원 회귀가 실제 셸 실행으로 통과.
- **패키지 공급 검증** [Run #44648659637](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44648659637): 컨테이너 내 /usr/bin/coredumpctl, --json CLI 지원 확인. 다만 첫 workflow에서 잘못된 변수 확장으로 `PACKAGE_NAME=`, `PACKAGE_VERSION=`가 비어도 녹색이 되는 **추가 검증 결함** 발견.
- **RED2** [public L0 Run #44648882772](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44648882772): 패키지 이름/버전이 비었을 때 PASS를 허용하지 않는 새 static contract 실패.
- **GREEN2** [public L0 Run #44648949764](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44648949764): **149/149 PASS**, source SHA `55d9f374146b7dcc848d0171093bbca48cca81ab`, Runner Canary [#44648949770](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44648949770) PASS.
- **진짜 Ubuntu package** [Run #44648949729](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44648949729): `systemd-coredump 255.4-1ubuntu8.19`, `Status: install ok installed`, `/usr/bin/coredumpctl`, `--json=pretty|short|off` 기록 후 PASS. 서버 코어가 실제 생기는지와 WSLg GPU는 **NOT_VERIFIED**.

수정 자체는 CI 원인 진단과 CLI 계약 개선만이므로, 지난 C10의 실제 Jazzy/Harmonic/Nav2 NO_GOAL L2 성공 #44568745545 (다른 SHA/Linux Xvfb+CycloneDDS)은 보존하되 C12에서 ROS/Gazebo L2를 새로 실행했다고 주장하지 않는다.

## 5. 작업 흐름 개선 — 환경 의존성 오류를 사용자 현장으로 넘기지 않는 Gate

1. **기존 증거/기준선 먼저 확인**: 성공한 동일 소스/토픽/종료 경계 유지, 실패한 외부 도구 의존성만 회귀 편입. `--self-check`는 오직 L0라고 명확히 표시.
2. **CI 계약 사전검사**: 스크립트의 외부 도구를 선언하고, 필수 도구 누락·오류 옵션·바이너리 이상·잘못된 패키지 증거를 각각 모의 실제 셸 실행으로 **의도한 RED→GREEN**. 도구 누락이면 Gazebo/Goal 실행 전 HOLD. 마지막 성공 메시지는 테스트/증거를 직접 확인한 경우에만 출력.
3. **Clean Ubuntu 24.04 실제 패키지 검증**: docker에서 정식 패키지 설치·버전·CLI 옵션 검증. 핵심 원칙은 `command -v`만으로는 실제 API/서비스 백엔드 준비가 보장되지 않는다는 것.
4. **동일 코드 공개 실제 Gazebo L2**: Nav2 READY부터 native/raw/safety 20초 gap≤300ms, Student 20초 gap≤300ms, Nav/Loc ACK, CM/Guard/Supervisor/Gazebo exit0, 증거 SHA256 검증. L0와 별도 verdict. 이전 C10 성공 소스를 변동 없이 재사용하면 성공 증거를 불필요하게 재실행하지 않아도 됨.
5. **WSLg 실환경 동등성 게이트**: public Linux Xvfb는 NVIDIA WSLg D3D12 크래시 증거가 될 수 없음. 본 문제까지 자동 검증하려면 GPU/WSLg를 갖춘 격리된 self-hosted Windows/WSL2 CI runner 같은 **실제 동등 환경**이 필요함. 현재 러너 확보/검증 안 됨. 없다면 `WSLG_NATIVE_SHUTDOWN=NOT_VERIFIED`를 공개하고 출고 HOLD. 고객 WSL2를 반복 디버깅 러너처럼 사용하지 않음.
6. **한 번의 Owner 현장 최종 확인**: 위 Gate를 모두 충족하고 SHA/blob 고정 뒤에만 한 명령 블록으로 실제 ROS2/Gazebo/WSLg + NO_GOAL → 기존 승인된 Moving Goal/CM120/Guard150 연결과 정상 종료를 검증. 실패하면 원본 압축·첫 실패 경계 기록 → CI 회귀 RED → GREEN, 현장 무작정 재시도 금지.

**현장 의존성 처리 방침**: WSL2 기본 이미지에 systemd-coredump가 없을 수 있음. 별도 권한으로 자동 apt 설치하거나 host `kernel.core_pattern`을 바꾸는 수정은 코어 관리 정책에 영향을 줄 수 있으므로 묵시적으로 도입하지 않는다. 최종 배포 전 **명시적 도구 계약/관리형 표준 이미지/실동등 CI** 중 검증 가능한 경로를 결정해야 한다. 또한 서버 코어 획득 자체가 필요 없다면 C11을 최종 시연 인수의 일반 필수 gate가 아니라 **충돌 회귀 진단용 조건부 gate**로 분리하여 불필요한 필수 종속성을 제거한다.

## 6. 인수 판정

- `C12_CI_MISSING_CLI_REGRESSION=PASS`
- `C12_CI_UBUNTU2404_CLI_PACKAGE=PASS`
- `C12_ACTUAL_ROS_GAZEBO_L2=NOT_RUN` (기존 C10 L2만 보존)
- `WSL2_SYSTEMD_CORE_BACKEND=NOT_VERIFIED`
- `WSLG_GPU_SIGSEGV_ROOT_CAUSE=UNDETERMINED`
- `WSLG_GPU_NATIVE_SHUTDOWN=NOT_VERIFIED`
- `OWNER_WSL2_FINAL_L3=NOT_RUN`
- `D06_GAZEBO_LIVE_RELEASE=HOLD`
- `AXIA_MVP_DEMO_ACCEPTED=HOLD`
- `CERTIFIED_ESTOP=false`
- `MAIN_MERGED=false`
