# AXIA D06/G07 C17 — 독립 NVIDIA WSLg G3 최초 서버 SIGSEGV 또는 정상 종료 단일 판정

작성: 2026-11-20 KST · 공개 PR #177 · **L0 PASS / 실제 G3 NOT_RUN / 강사 WSL2 L3 NOT_RUN / main 미병합**

## 1. 범위와 최초 미해결 경계

C16 (공개 HEAD `ac07c811cfa00659c296e30709f36387014cf2d6`)까지 검증된 것:
- 공개 Linux Xvfb/CycloneDDS 실제 Gazebo+Nav2 NO_GOAL L2: [#44568745545](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44568745545), 완료/성공, 해당 SHA에서만 유효.
- C14 실제 Ubuntu24.04 합성 SIGSEGV→GDB 최초 프레임→작은 SHA256 TAR: [#44651428861](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44651428861) PASS.
- C16 읽기 전용 WSLg/D3D12 NVIDIA RTX2060 후보 판별: [#44653495316](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44653495316) L0 161/161 PASS, **실제 GPU에 실행된 적 없음**.

원본 현장 Gazebo server SIGSEGV(-11)의 최초 스택은 여전히 미확보. 기존 C11 `--run-once`는 core 수집 진단 목적상 정상 종료에도 코어가 없으면 HOLD를 출력함. **그 HOLD가 실제 native SIGSEGV인지, 충돌 없이 exit0여서 코어가 없는지**를 추가 물리 재시도 없이 원본 하나로 구분하는 판정이 필요함.

## 2. 최소 수정: 신규 배포 스크립트 하나, 공개 L0 5개

- 새 파일: `d06/scripts/axia_d06_g3_independent_wslg_nogoal_once.sh`
- 새 회귀: `d06/tests/test_d06_c17_g3_clean_or_core_verdict.py`
- CI 연결: `.github/workflows/axia-d06-g07-wslg-lidar-rtf-isolation-l0-20261118.yml`
- 재사용하는 **불변** 구현: C16 `d06_g3_wslg_gpu_capability.py` SHA `32c9448b92eb7b50427d9c47b41aa2e07b17588c`, blob `eea3f6582eb184d9b61d0ac525d368793d11d271`; C11 `axia_d06_g07_wslg_sigsegv_capture_once.sh` SHA `ac07c811cfa00659c296e30709f36387014cf2d6`, blob `c7b3e9f5372a78e6373fce086cb7ab5a65475657`.
- C16 판별이 성공하고 별도 호스트 소유자가 명시적으로 `AXIA_G3_ISOLATED_HOST_ACK=YES-INDEPENDENT-G3`을 제공할 때만 C11 한 번 실행. 이 문자열은 **독립성을 입증하는 암호학적 증거가 아니며 단순 오실행 방지**.
- C11이 기존 SIGSEGV core를 발견하면 **Gazebo를 다시 실행하지 않고** 해당 core를 검사. 없다면 기존 Owner의 `--nvidia-causal` NO_GOAL 1회만 이용.
- 본 C17은 C11의 작고 SHA256 검증 가능한 `trace-*.tar.gz`를 읽어 판정하며, 메모리 코어를 업로드하거나 시스템 전역 설정을 변경하지 않음.
- `--classify-bundle`는 임의 합성 TAR에 대해서도 실행할 수 있으므로 **반드시 OFFLINE_BUNDLE...HARDWARE_NOT_PROVEN만 출력**. 실제 호스트 입장과 C11 단일 실행 경로가 확인된 `--run-once`에서만 `D06_G3_NATIVE_NO_GOAL_CLEAN_CANDIDATE_NOT_MOVING_L3`을 출력. 이 성공도 Moving/전체 인수 아님.

## 3. 공개 CI RED → GREEN → REVIEW → COMMIT

- **RED** 신규 실행기가 없는 공개 workflow commit `d9256c6dcd7fadd86b201a8e0a6d04908da51a21`, [Run #44661376370](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44661376370) FAIL. 신규 5개 검사 중 **4 FAIL+1 ERROR**, 실제 첫 에러 `FileNotFoundError: .../d06/scripts/axia_d06_g3_independent_wslg_nogoal_once.sh`. 다른 기존 Gazebo 기능의 실패가 아님.
- **GREEN** 신규 wrapper commit `9c2f9a590cc7acd410cb4f1e7f4f92b87a5cb49f`, 안전한 host ACK 테스트 보강 HEAD `682eb75e457585bd644388528d0a4b685ae8431b`.
- [공개 L0 GREEN #44661719974](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44661719974) completed/success: 신규 5/5 `ok`, 전체 D06 L0 스위트 PASS, `AXIA_D06_G07_LIDAR_RTF_ISOLATION_L0_PASS_NO_ROS_NO_GAZEBO_NO_GOAL`.
- [동일 HEAD Ubuntu 24.04 의존성 CI #44661719818](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44661719818) completed/success; [Runner Canary #44661719854](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44661719854) completed/success.
- 이번 C17 추가 파일은 ROS/Gazebo/Nav2/CM/Guard/Student runtime을 변경하지 않음. 원래 300/120/150ms TTL 완화 없음. 기존 실제 L2 PASS는 원래 tested SHA에 한정하여 보존. C17에서 새 실제 Gazebo L2나 NVIDIA G3를 실행했다고 주장하지 않음.

## 4. **별도 격리 호스트 전용** SHA 고정 원샷

**강사 최종 인수 WSL2에서 실행하지 마세요.** 실제 별도의 격리된 Windows/WSL2 Ubuntu24.04 + WSLg NVIDIA RTX 2060 동등 호스트가 준비된 경우에만 아래 블록 사용. 명령은 첫 호스트 입장 → 기존 core 재사용 또는 NO_GOAL 1회 → 작은 원본 forensic TAR+SHA 출력을 수행합니다.

```bash
(
  set -Eeuo pipefail
  PIN="682eb75e457585bd644388528d0a4b685ae8431b"
  BLOB="85d4aacc8f55f7d93d4578e12cf725f9270a1388"
  SCRIPT="$(mktemp --suffix=.sh)"
  trap 'rm -f "$SCRIPT"' EXIT
  curl -fLsS --retry 3 --max-time 90 \
    "https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public/$PIN/d06/scripts/axia_d06_g3_independent_wslg_nogoal_once.sh" -o "$SCRIPT"
  test "$(git hash-object "$SCRIPT")" = "$BLOB"
  bash -n "$SCRIPT"
  bash "$SCRIPT" --self-check
  AXIA_G3_ISOLATED_HOST_ACK=YES-INDEPENDENT-G3 bash "$SCRIPT" --run-once
)
```

- **HOST HOLD**: `D06_G3_INDEPENDENT_WSLG_GPU_ADMISSION_HOLD_NO_GAZEBO` — Gazebo 시작하지 않음.
- **FIRST CRASH STACK HOLD**: `D06_G3_FIRST_SERVER_SIGSEGV_STACK_CAPTURED_HOLD` — 이 TAR의 첫 GDB stack을 원본으로 GPU/서버 종료의 공개 CI 회귀 최소 수정 후 재검증.
- **NO CLEAN EVIDENCE HOLD**: `D06_G3_NO_GOAL_NATIVE_PROOF_MISSING_HOLD` — 기존 실행기 최초 failure와 sensor/native 증거 검수. 동일 원인으로 현장 재실행 금지.
- **G3 NO_GOAL clean candidate**: `D06_G3_NATIVE_NO_GOAL_CLEAN_CANDIDATE_NOT_MOVING_L3` — 실제 독립 호스트 해당 세션의 NO_GOAL 정지 상태, Scan300 dual-20s, Nav2 ACK, CM/Gazebo child exit0만 후보. Moving CM120/Guard150 및 강사 Owner WSL2 L3는 미실행.
- 전달할 파일: `D06_G3_FIRST_RUN_ARCHIVE=/home/.../trace-....tar.gz`, `D06_G3_FIRST_RUN_SHA256=<...>.sha256` **두 개만**. `sha256sum -c "<sidecar>"` 후 전달. 원본 memory core는 외부 공유하지 않음.

## 5. 인수 및 미검증 경계

```text
C17_PUBLIC_L0=PASS (5/5 NEW; NO_ROS_NO_GAZEBO)
C17_NOBLE_CLI=PASS (SAME HEAD; NOT WSLg)
C10_REAL_GAZEBO_L2=PASS (PRIOR SOURCE/ENV ONLY)
INDEPENDENT_WSLG_NVIDIA_G3=NOT_RUN
REAL_GAZEBO_SIGSEGV_FIRST_STACK=NOT_CAPTURED
OWNER_WSL2_L3=NOT_RUN
MOVING_CM120_GUARD150_E2E=NOT_RUN
D06_GAZEBO_LIVE_RELEASE=HOLD
AXIA_MVP_DEMO_ACCEPTED=HOLD
CERTIFIED_ESTOP=false
MAIN_MERGED=false
```

**외부 차단조건**: 현재 GitHub 연결은 공개 코드·Actions 실행/열람이 가능하지만, 별도 Windows/WSL2 NVIDIA GPU 호스트에 접속하거나 이를 프로비저닝할 수 있는 실행 경로가 확인되지 않음. 소유자가 격리된 GPU 호스트를 준비하기 전 G3/강사 L3를 실제로 통과했다고 주장할 수 없음. 공개 PR에 무차별 self-hosted runner를 연결하지 않음.
