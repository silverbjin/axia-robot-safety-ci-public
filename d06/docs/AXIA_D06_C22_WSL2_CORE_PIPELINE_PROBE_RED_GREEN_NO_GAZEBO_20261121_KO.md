# AXIA D06 C22 — PID 19280 코어 추적 종료, WSL2 systemd-coredump 실제 수집 경로 사전검사

작성: 2026-11-21 KST · 공개 PR #177 · **Goal/ROS/Gazebo 실행하지 않는 사전검사** · main 미병합

## 1. 사용자 최종 결과와 첫 미해결 경계

강사 WSL2에서 직접 명령 `sudo coredumpctl --no-pager info 19280` 실행 결과:

```text
No coredumps found.
```

- 기존 `trace-svstYuu9.tar.gz`의 `D06_WSLG_CORE_ONCE_EXISTING_ONLY_MISSING_CORE_NO_REPLAY`를 root 권한 조회에서도 재확인함. **과거 서버 코어 재구성 불가능**하며 더는 과거 PID에 대한 반복 조회를 요구하지 않음.
- 과거 실 Gazebo NO_GOAL 원본 `1jvaRyCE`: 후반 정상 dual Scan20.161초(최대 Raw271.130ms, Safety237.858ms < 300ms), Nav/Loc lifecycle ACK, CM exit0, **Gazebo `gz sim -s` PID19280 exit -11**. 별도 READY 이전 전체 세션 독립 ROS 수신 Raw423.494ms/Safety418.905ms는 학생 실제 첫 TTL 위반 소스쌍이 아님.
- 과거 SIGSEGV 첫 스택 **NOT_CAPTURED**. Ogre2/D3D12/NVIDIA 또는 shutdown 원인 미확정.
- 과거 C19/C20 코드에서 core 검색이 없으면 실패 판정으로 종료한 것은 올바른 동작. C19/C20 재실행으로 코어가 생기지 않음.

## 2. 정책 및 공식 근거

- 사용자 승인 C18: **독립 NVIDIA WSLg G3 필수 게이트 제외**. 실제 강사 WSL2 Scan300ms/Nav2 ACK/CM0/Gazebo0 종료, Moving CM120/Guard150ms 안전 타이밍은 필수 유지.
- 공식 `systemd-coredump` 문서는 프로세스 코어가 `core_pattern`에서 파이프 처리되고 journald/외부 저장소에 남는 구조를 설명함. `coredumpctl` CLI 설치·도움말 출력만으로 실제 crash→core→dump가 동작한다고 주장할 수 없음.
  - https://www.freedesktop.org/software/systemd/man/latest/systemd-coredump.html
  - https://www.freedesktop.org/software/systemd/man/latest/coredumpctl.html
  - https://man7.org/linux/man-pages/man5/core.5.html (파이프형 core_pattern과 RLIMIT_CORE의 커널 동작)
- Gazebo Sim WSLg NVIDIA GUI 유사 사례 https://github.com/gazebosim/gz-sim/issues/3335 는 D3D12/OGRE 연관성 참고만 가능. AXIA의 **서버 종료 -11**과 동일한 원인이라는 증거는 아님.
- 추가 드라이버, sysctl, Mesa, RMW, TTL 값 변경하지 않음.

## 3. 필요한 최소 새 작업: C22 작은 충돌 수집 사전검사

- 신규 실스크립트 `d06/scripts/axia_d06_c22_wsl2_core_pipeline_probe_once.sh`
- 신규 L0 회귀 `d06/tests/test_d06_c22_wsl2_core_pipeline_preflight.py`
- 기존 공개 workflow `.github/workflows/axia-d06-g07-wslg-lidar-rtf-isolation-l0-20261118.yml`에 파일 변경 트리거/4개 unittest 추가.
- `--self-check`: 파일과 정적 계약만 확인, WSL2/ROS/Gazebo/프로세스 충돌 없음.
- `--probe-once`: **Ubuntu24.04 WSL2에서만** 허용. 설정 읽기(`core_pattern`/RLIMIT), **하위 Bash 프로세스 단 한 개에만** soft core limit 65536KiB 적용, 하위 프로세스 자체에 SIGSEGV 신호 1회 전달. 실제 생성된 PID로 `coredumpctl info`의 SIGSEGV/Bash 메타데이터 확인 → `coredumpctl dump`로 사용자 비공개 임시 파일 확인 → `gdb bt`의 #0 프레임 확인. 개인 private core는 즉시 삭제하며 작은 텍스트 TAR+SHA256만 출력. systemd의 별도 저장소 보존 정책은 변경하지 않음.
- 위 각 단계 중 하나라도 실패하면 `D06_C22_...HOLD_NO_GAZEBO`. **Gazebo를 시작하지 않음**, 핵심 원인 미확정 유지.
- 이 작은 Bash core 성공은 **Gazebo 크기의 코어 수집 가능성, NVIDIA WSLg 서버 종료 정상, 스캔/CM/Guard 안전 타이밍을 증명하지 않음**.

## 4. RED → GREEN → REFACTOR → REVIEW → COMMIT / 실제 출력

- **RED** `b575899f878565dd3434e4ca189be6c22f68c02a`, 공개 [Run #44764218584](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44764218584) 실제 **1 FAIL+3 ERROR**, 신규 스크립트가 없는 예상 상태에서 테스트 실패.
- **GREEN** 코드 commit `60c56ed3244bc7e07f41c462dc2fe525ca431586`, script Git blob `622b5db08910b44bd8c828bc977c845030cb6ab6`. 공개 [L0 #44764571827](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44764571827) 전체 성공. 신규 C22 4 tests 모두 `... ok` `Ran 4 tests in 0.004s`.
- 같은 소스 [Ubuntu 24.04 package CLI #44764574458](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44764574458) success 및 [runner canary #44764571874](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44764571874) success.
- **독립 격리 Linux 기초 실행**: `bash -c 'kill -s SEGV "$BASHPID"'`가 실제 `rc=139`와 PID 기록을 생성. `ulimit -c 0`으로 해당 독립 테스트 코어 파일은 저장하지 않음. 이 실행은 **systemd-coredump backend를 테스트하지 않음**.
- REVIEW: 트리거가 CI 러너이면 실제 probe 금지; 새로운 Gazebo/ROS/Goal/Velocity/Fault 없음; 시스템 전체 core_pattern/드라이버/환경 변수 override 없음; private core는 업로드하지 않으며 자동 정리.
- **미검증**: 강사 WSL2 실제 `--probe-once`, systemd-coredump back-end 수집, Gazebo WSLg shutdown 정상화, Moving Goal TTL E2E.

## 5. 강사 WSL2에서 사용할 유일한 다음 명령

다음은 새 Gazebo나 로봇 시뮬레이션을 실행하지 않음. **대신 고립된 Bash 자식 프로세스 1개에 의도적으로 SIGSEGV를 일으키며**, OS journal/systemd-coredump에 기록을 남길 수 있음.

```bash
(
  set -Eeuo pipefail
  SHA="60c56ed3244bc7e07f41c462dc2fe525ca431586"
  BLOB="622b5db08910b44bd8c828bc977c845030cb6ab6"
  SCRIPT="$(mktemp --suffix=.sh)"
  trap 'rm -f "$SCRIPT"' EXIT
  curl -fLsS --retry 3 --max-time 90 \
    "https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public/$SHA/d06/scripts/axia_d06_c22_wsl2_core_pipeline_probe_once.sh" -o "$SCRIPT"
  test "$(git hash-object "$SCRIPT")" = "$BLOB"
  bash -n "$SCRIPT"
  bash "$SCRIPT" --self-check
  bash "$SCRIPT" --probe-once
)
```

예상 결과:
- `D06_C22_SYNTHETIC_COREDUMP_PIPELINE_PASS_NOT_GAZEBO`: WSL2 *작은 Bash* 실 core 수집→GDB 연결 성공. **새 Gazebo 실행 허가나 전체 MVP PASS는 아님**. 다음 단계는 공개 CI 및 동일 소스 런타임 검수 후 **새 증거 가치가 있는 단 1회 계획된 NO_GOAL 실증**으로 한정.
- `D06_C22_SYSTEMD_CORE_RETRIEVAL_NOT_PROVEN_HOLD_NO_GAZEBO`: SIGSEGV 프로세스 자체는 발생했으나 색인/추출 실패. 해당 원인을 분리하기 전 Gazebo 실행 중지.
- `D06_C22_NO_SYSTEMD_CORE_PIPE_NO_CRASH`: systemd handler 비활성. crash 테스트 자체를 수행하지 않음.
- `D06_C22_SYNTHETIC_CRASH_NOT_CONFIRMED_HOLD_NO_GAZEBO`: child core limit/프로세스 종료 경계 실패. 재시도보다 원본 메시지 분석 우선.
- 항상 `D06_C22_FORENSIC_ARCHIVE`와 `D06_C22_FORENSIC_SHA256` **두 파일만** 검증·제출, raw core 비공개. `AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false`.

## 6. 판정

```text
INDEPENDENT_G3_REQUIRED=false
OLD_GAZEBO_PID_19280_CORE=NO_RECORD_WITH_SUDO
C22_PUBLIC_L0=PASS (4/4 NEW; NO_ROS_NO_GAZEBO)
C22_PUBLIC_UBUNTU2404_CLI=PASS (EXISTING PACKAGE/CORE CONTRACT)
C22_REAL_WSL2_SYSTEMD_CORE_BACKEND=NOT_RUN
C22_REAL_GAZEBO=NOT_RUN
D06_OWNER_WSL2_NO_GOAL=HOLD_GAZEBO_SERVER_EXIT_MINUS11
MOVING_GOAL_ALLOWED=false
AXIA_MVP_DEMO_ACCEPTED=HOLD
CERTIFIED_ESTOP=false
MAIN_MERGED=false
```
