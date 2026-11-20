# AXIA D06/G07 C18 — 독립 NVIDIA WSLg G3 필수 출고 게이트 폐지 및 강사 WSL2 직접 최종 인수

작성: 2026-11-20 KST · 공개 PR #177 · 사용자 무료 인프라 제약에 따라 **독립 G3 호스트 검증 필수 조건 제외**
이 문서는 기존 C15/C16/C17의 과거 이력과 증거를 삭제하지 않고 **현재 유효한 인수 정책**을 대체 정의합니다.

## 1. 현재 유효한 게이트

```text
INDEPENDENT_WSLG_G3_REQUIRED=false
OWNER_WSL2_NO_GOAL_REQUIRED=true
OWNER_WSL2_NATIVE_EXIT0_REQUIRED=true
OWNER_WSL2_SCAN300_REQUIRED=true
NO_FIELD_REPEAT_ON_SAME_FAILURE=true
MOVING_GOAL_ALLOWED=false
D06_GAZEBO_LIVE_RELEASE=HOLD
AXIA_MVP_DEMO_ACCEPTED=HOLD
CERTIFIED_ESTOP=false
MAIN_MERGED=false
```

**독립 NVIDIA WSLg G3 환경을 별도로 확보하지 않아도 강사 WSL2 최종 NO_GOAL 인수를 직접 진행합니다.**
C16 capability probe/C17 독립 호스트 스크립트는 과거 검증 코드 및 선택적 진단 도구로 보존하며, 강사 인수의 선행조건으로 요구하거나 별도 GPU를 구매/임대하지 않습니다.
**면제되는 것은 별도 호스트뿐**이며, 실제 WSLg GPU·Gazebo·ROS2 안전조건 검증은 면제하지 않습니다.

- 공개 사전검증: 기존 엄격 Linux Xvfb + Jazzy/Harmonic/Waffle/Nav2 NO_GOAL L2 성공 #44568745545 (해당 SHA의 Linux/CycloneDDS 범위만 유효); 기존 L0 계약 및 Ubuntu24.04 CLI 성공 보존. 소스 런타임 변경이 없으면 무의미한 이전 성공 재실행 금지.
- 강사 WSL2 직접 NO_GOAL 단일 실제 실행: NVIDIA D3D12 Ogre2/renderer 확인, 동일 world·학생 소스 pin, 두 Scan 토픽 20초 실제 동시 수신, Raw/Safety **Scan300ms**, 안전 거리/모든 CLEAR; Nav2 Navigation/Localization SHUTDOWN ACK; 독립 read-only ROS 및 gz witness 종료 handoff; **CM 및 Gazebo server 자식 process exit0**. Clock/RTF는 별도 측정하며 RTF 정상만으로 Scan TTL을 통과시키지 않습니다.
- 기존 이동 및 실제 SW STOP 시연을 위한 **CM120ms, Guard150ms** 안전 전달 주기와 stop/cancel/odom dwell은 NO_GOAL 이후 별도 실제 검증 대상으로 유지합니다.
- NO_GOAL 미통과 상태에서는 Goal/Twist/Fault/Moving Goal을 절대로 실행하지 않습니다. SW 정지는 인증된 물리 E-Stop이 아닙니다.
- 최초 실패는 첫 안전 상태 전이와 첫 수신/타이밍 위반을 기준으로 분류합니다. `witness exit134`, `Gazebo server SIGSEGV exit-11`, `Localization 관리 서비스 최초 30초 무응답`은 서로 별개 경계입니다. shutdown parent marker나 센서 CLEAR만으로 네이티브 종료 성공 처리 금지.

## 2. 강사 WSL2 원샷 — 현재 기준 출력 및 source pin

`NO_GOAL_ONLY` / 고정 **공개** 소스 `silverbjin/axia-robot-safety-ci-public` commit
`86c68a121bedffbf1d2bb91e1efac6a40b88c798` 경로 `d06/scripts/axia_d06_g07_wslg_gpu_rtf_compare_once.sh`,
Git blob `0592044ade101dfdff7682e127953c976778e6fc`, 내부 학생 소스
`0565e580f5b7c80d719960a6046de3e45c8ea477`. 공개 CI 검증 이후 Owner runtime 및 TTL 설정은 수정하지 않습니다.

**강사 PC의 WSL2 Ubuntu24.04 / WSLg NVIDIA GUI 세션에서** 이미 실행 중인 해당 프로젝트 시뮬레이션이 없는 것을 확인하고 다음 한 블록만 실행합니다. 원샷 자체에 evidence trap과 SHA256 압축이 포함됩니다.

```bash
(
  set -Eeuo pipefail
  SHA="86c68a121bedffbf1d2bb91e1efac6a40b88c798"
  BLOB="0592044ade101dfdff7682e127953c976778e6fc"
  SCRIPT="$(mktemp --suffix=.sh)"
  trap 'rm -f "$SCRIPT"' EXIT
  curl -fLsS --retry 3 --max-time 90 \
    "https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public/$SHA/d06/scripts/axia_d06_g07_wslg_gpu_rtf_compare_once.sh" \
    -o "$SCRIPT"
  test "$(git hash-object "$SCRIPT")" = "$BLOB"
  bash -n "$SCRIPT"
  bash "$SCRIPT" --self-check
  bash "$SCRIPT" --nvidia-causal
)
```

정상 후보 출력:
- `D06_OWNER_NO_GOAL_NATIVE_COMPLETE_CANDIDATE SCAN300_DUAL_20S_PASS NAV2_ACK_PASS CM_CHILD_EXIT0 GZ_CHILD_EXIT0 ... NO_MOVING_L3 CERTIFIED_ESTOP=false`
- `D06_GPU_RTF_NVIDIA_ONLY_FIRST_BLOCK=NONE` 및 `D06_GPU_RTF_NVIDIA_NO_GOAL_EVIDENCE=<run_dir>` (추가 로그 검사)
- 안전 정책상 최종 `D06_GAZEBO_LIVE_RELEASE=HOLD CERTIFIED_ESTOP=false`은 정상이며 **Moving L3 미승인**을 의미합니다. 첫 NO_GOAL 단일 성공 ≠ 전체 MVP PASS.

실패도 자동 기록됨. 출력된 `D06_FORENSIC_ARCHIVE=<...>.tar.gz`와
`D06_FORENSIC_SHA256=<...>.tar.gz.sha256` **두 파일만** 보존/전달합니다.
`sha256sum -c "<출력된 .sha256 절대경로>"` 확인 후 증거 분석.
최초 네이티브 크래시의 raw core 파일은 공개 업로드 금지.

## 3. 실패 시 재개 정책

1. **초기 preflight/다운로드 실패**: 원샷에 기록된 `attempt_state.txt` 및 최초 관련 메시지를 재사용; 로컬 반복 없이 누락 의존성/핀 검사를 공개 CI에 회귀로 먼저 편입.
2. **Scan300ms 위반**: `summary.json`의 두 토픽 최초 gap, 진짜 20초 관측 구간/READY 이전 구간 구분, native→독립 ROS→학생 callback 동일 메시지 stamp pair 및 /clock RTF 확인. 개별 센서 정상만으로 CM/Guard 전체 안정성 주장 금지.
3. **Lifecycle ACK 실패**: Navigation/Localization별 최초 관리 서비스 요청/응답을 별도로 분류. 단일 요청 30초 타임아웃은 전역 TTL 완화나 무조건 반복 명령으로 회피 금지.
4. **witness134 또는 Gazebo server -11**: 각각 다른 프로세스의 최초 native 종료 코드 분류. 기존 core가 있으면 read-only GDB 분석; core 미확보는 원인 미확정으로 표기. `D06_OWNER_NO_GOAL_NATIVE_GATE_BLOCKED`를 숫자 결과로 포함하고 parent graceful marker로 PASS 승격 금지.
5. 재현 가능한 최초 오류를 공개 CI에 RED로 편입 → 최소 수정 GREEN → 코드 리뷰 → 커밋 → 필요한 경우 실제 Gazebo L2 검증 → 그때에만 강사 WSL2 **새 단일 인수**. **NO_FIELD_REPEAT_ON_SAME_FAILURE=true**.

## 4. NO_GOAL 후에만 수행할 별도 단계

- 동일 기준선/인수 기록을 사용하여 기존 승인된 Moving Goal 실행기의 적합성을 **새 코드 개발 없이** 검수.
- CM120ms / Guard150ms 노드 간 전달 주기, SW STOP, Goal 취소 및 odom dwell을 실제 조건에서 검증하며 해당 범위의 공개 CI L2 증거와 강사 WSL2 최종 L3 증거를 구분.
- Goal 권한은 이후 검증·승인 시점까지 `MOVING_GOAL_ALLOWED=false`. E-Stop 인증 주장 금지.
- 인수 보고에는 파일 경로, 실제 명령, 원본 출력, 검증 수준/미검증, branch/commit을 기재하며 사용자의 명시적 승인 없이는 main에 병합하지 않습니다.

## 5. 이전 성공 근거 / 새 정책이 증명하지 않는 것

- 기존 공개 L0 #44504764400 103/103, 실제 Jazzy/Gazebo L2 #44503070174 NO_GOAL PASS 보존.
- C10 실제 Linux/CycloneDDS G2 [#44568745545](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44568745545) NO_GOAL PASS. 이는 RTX2060 WSLg 최종 현장 PASS가 아님.
- C17 독립 GPU 준비 계약 [#44661719974](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44661719974) L0 PASS는 **필수 게이트에서 제외**, 과거 감사 증거로만 유지.
- C18은 인수 **정책 문서/테스트만** 변경하며 ROS2/Gazebo/Nav2/학생 runtime·안전 TTL·RMW 설정과 인증 E-Stop에 아무 변경 없음.

**현재 상태:** `INDEPENDENT_WSLG_G3_REQUIRED=false`, `OWNER_WSL2_NO_GOAL=NOT_RUN`,
`D06_GAZEBO_LIVE_RELEASE=HOLD`, `AXIA_MVP_DEMO_ACCEPTED=HOLD`,
`MAIN_MERGED=false`, `CERTIFIED_ESTOP=false`.
