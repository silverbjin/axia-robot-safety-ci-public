# AXIA D06 C20 — 강사 WSL2 missing coredumpctl: 최소 패키지 복구 및 최초 서버 코어 재실행 없는 조회

작성 2026-11-20 · 공개 PR #177 · main 미병합 · NO_GOAL 인수 **HOLD** · 인증된 E-Stop 아님

## 1. 입력 로그 및 판단

강사 WSL2 원본 출력:

```
D06_WSLG_CORE_ONCE_L0_PASS_NO_ROS_NO_GAZEBO
D06_WSLG_CORE_ONCE_HOST_DEPENDENCIES_NOT_TESTED
AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false
D06_WSLG_CORE_ONCE_HOLD_MISSING_TOOL=coredumpctl
D06_WSLG_CORE_ONCE_MISSING_UBUNTU_PACKAGE=systemd-coredump
D06_WSLG_CORE_ONCE_HOLD_PRECONDITION_NOT_MET_NO_GAZEBO_RUN
```

이는 C19 `--existing-only` 실행이 **Gazebo 재시도 이전** CLI preflight에서 차단되었음을 의미한다. 센서 또는 Gazebo의 새 오류가 아니다. 과거 원본 `d06-forensic-ab-no-goal-1jvaRyCE.tar.gz` SHA256 `541c47638528dbefc0258b51ff23d88e2406bb8e4b78be5e1f1812bd477bdb38`, 당시 Gazebo server `gz sim -r -s` PID `19280` exit `-11`. 당시에 systemd-coredump backend가 실행 중이었는지는 **미확정**이다.

**기술적 한계:** 시스템 코어 캡처 서비스가 당시 없었다면, 나중에 `systemd-coredump`를 설치해도 이미 끝난 PID 19280의 memory core를 생성할 수 없다. 과거 코어가 존재할 가능성만 재검사한다. 코어가 없다면 재시뮬레이션하지 않고 HOLD를 남긴다.

## 2. 기존 CI를 재사용한 최소 C20 수정

- 기존 C12 테스트 `d06/tests/test_d06_c12_field_missing_coredumpctl.py`에서 누락 CLI를 이미 RED/그 후 GREEN 처리했다.
- 기존 C13 실환경 Docker Ubuntu 24.04 CLI 검증은 `.github/workflows/axia-d06-c12-coredump-cli-compat-ubuntu2404.yml`에서 `systemd-coredump gdb mesa-utils` 등 설치 후 `--check-tools` 실행. [기존 확인 #44728396850](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44728396850) PASS.
- 신규 현장 편의 래퍼 **단 하나** 추가: `d06/scripts/axia_d06_c20_coredumpctl_existing_only_repair.sh`.
- 신규 회귀: `d06/tests/test_d06_c20_missing_coredumpctl_host_repair.py` 3개. CI L0 workflow에 경로와 실행 등록.
- **RED** [#44733368809](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44733368809): 테스트 3 ERROR, C20 래퍼 부재 FileNotFoundError.
- **GREEN** C20 소스 commit `d4cd2a42cd2d5273ca780d3e809fe9dc3091858c`, blob `4089aa7ecc4c97be3ead6e6d323732198ca257c2`. [L0 #44733717528](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44733717528) 새 3/3 `ok`, 전체 workflow SUCCESS; [Ubuntu 24.04 CLI #44733717555](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44733717555) SUCCESS; [Canary #44733717546](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44733717546) SUCCESS.
- **REFACTOR/REVIEW**: 기존 C19 원본 `--existing-only` 분석기는 수정하지 않음. wrapper는 OS/WSL2 사전검사 후 누락 시 Ubuntu 공식 패키지 하나만 `sudo apt-get`으로 설치; 권한 요청은 실제 로컬 사용자 sudo, 사용자에게서 명령 실행 시 발생. 시스템 `sysctl`, RMW, CUDA/Mesa, ROS/Nav2/CM/Guard/TTL과 소스 설정을 변경하지 않음. **패키지 설치 자체가 systemd core handler 구성에 영향을 줄 수 있으므로 적용 전후 `core_pattern`을 출력**.
- **검증 범위**: 실제 CI는 합성 CLI/Ubuntu container + 새 L0 테스트만 포함. 대상 강사 WSL2에서 apt 설치, PID 19280 코어 존재 또는 GDB 첫 프레임 확인 **NOT_RUN**.

## 3. 강사 WSL2 한 블록 (Gazebo·Goal 재실행 없음)

```bash
(
  set -Eeuo pipefail
  SHA="d4cd2a42cd2d5273ca780d3e809fe9dc3091858c"
  BLOB="4089aa7ecc4c97be3ead6e6d323732198ca257c2"
  SCRIPT="$(mktemp --suffix=.sh)"
  trap 'rm -f "$SCRIPT"' EXIT
  curl -fLsS --retry 3 --max-time 90 \
    "https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public/$SHA/d06/scripts/axia_d06_c20_coredumpctl_existing_only_repair.sh" \
    -o "$SCRIPT"
  test "$(git hash-object "$SCRIPT")" = "$BLOB"
  bash -n "$SCRIPT"
  bash "$SCRIPT" --self-check
  bash "$SCRIPT" --run
)
```

이 명령을 실행하면 필요 시 `sudo` 암호를 **한 번** 요구할 수 있으며, `sudo apt-get update`와 `systemd-coredump` 패키지 설치가 **시스템 변경 작업**으로 수행된다. 수업 운영 환경에서 패키지 설치가 허용되는 경우에만 실행.

출력:
- `D06_C20_COREDUMPCTL_CLI_PRESENT_BACKEND_NOT_PROVEN`: CLI 설치 확인, 과거 core가 있다는 뜻이 아님.
- `D06_WSLG_CORE_ONCE_EXISTING_ONLY_MISSING_CORE_NO_REPLAY`: PID 19280 core 없음; **동일 오류 현장 재실행하지 않음**.
- `D06_WSLG_CORE_ONCE_EXISTING_ONLY_TARGET_PID_MISMATCH_NO_REPLAY`: 다른 실행의 코어를 잘못 선택하는 것 방지.
- `D06_WSLG_CORE_STACK_CAPTURED_NOT_RESOLVED`: 첫 stack 보존, 근본 원인 **미확정**; 별도 증거 검토 필요.
- `D06_WSLG_CORE_ONCE_FORENSIC_ARCHIVE`, `D06_WSLG_CORE_ONCE_SHA256`: 분석에 필요한 작은 TAR+sha256만 제출. raw core는 업로드하지 않음.

## 4. 게이트

```
INDEPENDENT_WSLG_G3_REQUIRED=false
C20_PUBLIC_L0=PASS
C20_UBUNTU2404_CLI=PASS (CONTAINER)
C20_REAL_WSL2_PACKAGE_REPAIR=NOT_RUN
C20_PAST_PID_19280_CORE_RECOVERY=NOT_RUN
OWNER_WSL2_NO_GOAL=FAIL_PREVIOUS_GAZEBO_SERVER_EXIT_MINUS11
MOVING_GOAL_ALLOWED=false
AXIA_MVP_DEMO_ACCEPTED=HOLD
D06_GAZEBO_LIVE_RELEASE=HOLD
CERTIFIED_ESTOP=false
MAIN_MERGED=false
```
