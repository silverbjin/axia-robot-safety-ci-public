# AXIA D06/G07 C16 — 별도 WSLg NVIDIA G3 검증 호스트 도입 사전 검수 및 안전 게이트

작성일: 2026-11-20(KST) | 공개 CI Draft PR #177 | 출고 HOLD | main 미병합

## 1. 승인과 작업 목표

사용자는 강사 WSL2를 개발 중 반복 디버깅 머신으로 쓰지 않고 **별도 Windows/WSL2+WSLg NVIDIA GPU 검증 환경을 준비**하는 방향을 승인. 본 C16에서 실제 GPU 하드웨어를 새로 구입·대여·등록하거나 운영체제를 변경할 수 있는 외부 인프라/러너 관리 연결은 없음. 따라서 러너가 이미 존재한다고 가정하거나 실제 G3를 PASS로 기록하지 않음.

## 2. 현재 GitHub 소유·지원 범위 확인

- 공개 repo `silverbjin/axia-robot-safety-ci-public`의 GitHub API `owner.type=User`, 공개 개인 계정 소유. GitHub GPU larger runners는 **Team/Enterprise 조직/엔터프라이즈** 대상이므로 현재 repo에서 자동 사용할 수 있는 GPU 풀은 확인되지 않음.
- GitHub GPU Windows larger runner가 Tesla T4라고 하더라도 이는 강사 NVIDIA RTX 2060 Max-Q의 **동일 GPU/WSLg 렌더러**가 아님. GitHub-hosted VM의 중첩 가상화는 공식 지원되지 않으므로 실제 WSL2 부팅 가능성과 OpenGL D3D12 렌더러 사용 여부를 증거 없이 인정하지 않음.
- GitHub 공식 보안 가이드에 따라 **공개 PR이 접근 가능한 self-hosted Windows GPU runner를 공개 repo에 연결하지 않음**. PR/fork의 임의 코드가 GPU 머신을 제어하지 못하도록 **별도 격리 호스트의 pull-only 고정 SHA 실행**을 우선 검토. 안전한 신뢰 경계, 증거 전달 방식과 호스트 접근권한이 준비되기 전까지 자동 실행하지 않음.

공식 근거:
- https://docs.github.com/en/actions/how-tos/manage-runners/larger-runners/manage-larger-runners
- https://docs.github.com/en/actions/concepts/runners/github-hosted-runners
- https://docs.github.com/en/actions/reference/security/secure-use
- https://docs.github.com/en/actions/reference/runners/larger-runners

## 3. RED → GREEN → REVIEW → COMMIT

**RED** 공개 L0 [#44653354588](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44653354588), SHA `051db135b2b68b30e7ddc8fb2f8f5cc8881e88ef`:
- `d06/tests/test_d06_c16_wslg_gpu_runner_capability.py`에서 6개 read-only GPU/WSLg 환경 후보 계약 추가.
- 실제 출력 `FileNotFoundError: .../d06/tools/d06_g3_wslg_gpu_capability.py`, 6개 의도된 ERROR.
- Linux Xvfb, D3D12 Intel renderer/NVIDIA CUDA 혼합, RTX2060 모델 불일치, Jazzy·coredumpctl·core pattern 누락은 G3 부적격이어야 함. 공개 repo에서 `runs-on: self-hosted` 및 `pull_request_target` 사용 불가 계약 유지.

**GREEN** 공개 L0 [#44653495316](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44653495316), code SHA `32c9448b92eb7b50427d9c47b41aa2e07b17588c`, **161/161 PASS**, runner canary [#44653495267](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44653495267) SUCCESS.
- 신규 실제 파일 `d06/tools/d06_g3_wslg_gpu_capability.py`, Git blob `eea3f6582eb184d9b61d0ac525d368793d11d271`.
- 실행해도 **ROS/Gazebo/Goal/Fault를 시작하지 않고** `/proc/sys/kernel/osrelease`, `/etc/os-release`, WSLg DISPLAY/WAYLAND, `glxinfo -B` D3D12 NVIDIA renderer, `nvidia-smi`, Jazzy 파일 및 gz/ros2/GDB/coredumpctl 도구, systemd core_pattern 설정을 *읽기 전용*으로 평가.
- 정확한 환경이 모두 맞아도 `G3_HOST_CANDIDATE_NOT_ACCEPTED`만 출력. `gazebo_l2_executed=false`, `wslg_sigsegv_resolved=false`, `core_backend_real_crash_tested=false`, `certified_estop=false`; 곧바로 L3 인수 PASS를 출력하는 경로 없음.
- 핵심 테스트: `test_matched_gpu_only_candidate_never_l3_pass`, `test_standard_linux_xvfb_is_not_wslg`, `test_wslg_intel_renderer_with_nvidia_cuda_is_rejected`, `test_gpu_model_drift_or_missing_core_handler_hold`, `test_missing_jazzy_and_coredumpctl_hold`, `test_public_repo_remains_hosted_only`.
- 기존 공식 Nav2/Scan/CM/Guard/GOAL/RMW 설정 변경 없음. 작업 시 안전 TTL 300ms/120ms/150ms 불변.

## 4. 별도 호스트가 공급되었을 때의 유일한 사전확인 명령(독립 호스트 전용)

다음은 **현재 강사 WSL2용 명령이 아님**. 별도 격리된 GPU 호스트에 ROS2 Jazzy/Gazebo Harmonic/Ubuntu24.04/WSLg가 이미 설치되어 있을 때 그 호스트에서만 실행할 프로세스 입장 계약이다.

```bash
(
  set -Eeuo pipefail
  SHA="32c9448b92eb7b50427d9c47b41aa2e07b17588c"
  BLOB="eea3f6582eb184d9b61d0ac525d368793d11d271"
  FILE="$(mktemp --suffix=.py)"
  trap 'rm -f "$FILE"' EXIT
  curl -fLsS --retry 3 --max-time 90 "https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public/$SHA/d06/tools/d06_g3_wslg_gpu_capability.py" -o "$FILE"
  test "$(git hash-object "$FILE")" = "$BLOB"
  python3 "$FILE"
)
```

출력 `D06_G3_HOST_CANDIDATE_NOT_ACCEPTED`는 **환경 후보 자격**만 통과, 반드시 뒤의 실제 Gazebo server 종료 및 Scan300 인수가 필요. `D06_G3_CAPABILITY_HOLD`는 호스트 또는 준비 조건 불충족이며 실제 Gazebo를 시작하지 않는다. 한 번의 명령을 수행하기 전 대상 Windows/WSLg 독립 GPU 호스트를 등록 또는 확보해야 하며, **현 시점에는 이 명령도 대상 호스트에서 실행하지 않았다**.

## 5. 이후 실행 가능한 실제 G3 검증 조건

1. 공개 PR에 직접 연결하지 않는 **독립적·격리된 Windows 11/WSL2+WSLg NVIDIA 테스트 호스트** 확보, GPU/도구 접근권한 확인.
2. C16 호스트 입장 결과 및 `glxinfo -B` D3D12 NVIDIA/실제 RTX2060 비교 기록. CPU/메모리/GPU 모델 불일치면 동등성 제한 기록.
3. 코어 backend 실제 SIGSEGV 수집이 가능한지 외부 호스트에서 **안전한 합성 core 테스트**로 확인 (기존 C14 순수 분석 성공을 GPU host의 core journaling 성공으로 오인 금지).
4. 특정 GitHub public SHA/blob으로 고정된 기존 NO_GOAL Gazebo/Nav2 실행기를 독립 GPU 호스트에서만 1회 실행; native `/scan`·독립 ROS·학생 Safety 20초+300ms TTL, /clock 국소 RTF, 최초 안전상태, Nav/Loc ACK, CM/Guard/Supervisor/Gazebo child exit0 동시에 검사.
5. Gazebo server exit-11 발생 시 첫 실제 core/GDB 스택으로 D3D12 TLS vs Ogre2 renderer vs process-order 경계를 특정하여 공개 CI RED→GREEN 최소 수정.
6. 실제 동등 G3가 정상 종료 검증 후에만 강사 WSL2 최종 단일 인수(NO_GOAL 먼저, 이후 기존 승인 Moving Goal). 인증 E-Stop이 아닌 SW stop임을 유지.

## 6. 현 검증 매트릭스 및 다음 사용자 의사결정

`C16_PUBLIC_L0=PASS (161/161)`  
`C16_GPU_HOST_CAPABILITY_CLASSIFIER=PASS_FIXTURE_ONLY`  
`C13_NOBLE_FULL_CLI_L1=PASS`  
`C14_REAL_SYNTHETIC_GDB_CORE_L1=PASS`  
`C10_REAL_LINUX_GAZEBO_NO_GOAL_L2=PASS (SOURCE UNCHANGED)`  
`C16_INDEPENDENT_WINDOWS_WSLG_NVIDIA_HOST=NOT_PROVISIONED`  
`C16_ACTUAL_G3_HARDWARE_PROBE=NOT_RUN`  
`WSLG_GAZEBO_SIGSEGV_ROOT_CAUSE=UNDETERMINED`  
`OWNER_WSL2_L3=NOT_RUN`  
`D06_GAZEBO_LIVE_RELEASE=HOLD`  
`AXIA_MVP_DEMO_ACCEPTED=HOLD`  
`CERTIFIED_ESTOP=false`  
`MAIN_MERGED=false`

**막힌 외부 전제**: 공개 GitHub CI에서 실제 GPU 러너를 프로비저닝할 연결/계정 권한 및 사용할 별도 GPU 장비의 식별자가 확인되지 않음. GitHub larger GPU 러너를 임의 결제하거나 조직을 새로 만들거나 사용자의 기존 강사 WSL2를 검증 머신으로 사용하지 않음. 별도 GPU 검증 호스트의 제공/접근 방법이 확인되면 G3 1회 실증부터 재개 가능.
