# AXIA D06 C26 — 강사 WSL2 `readonly-41k2b1jj` 심층 분석: GPU 식별·부트/저널 경계 분리

**작성일:** 2026-11-21 KST. **환경:** Windows + WSL2 Ubuntu 24.04, ROS 2 Jazzy, Gazebo Harmonic, WSLg D3D12, NVIDIA RTX2060 Max-Q 기종. **프로젝트 범위:** MVP NO_GOAL 안전 인수 문제의 RCA 및 진단기 최소 수정. **전체 인수: HOLD**, main 미병합.

## A. 첨부된 단일 원본 및 실제 검증

사용자 제공 파일은 `readonly-41k2b1jj.tar.gz` 및 `.sha256`이다. SHA256 `f2b07e1bcd33a1de29685b2cb08e2b63536dc439f2b452105f757e2f790111f8`은 측정값과 첨부 검증 파일 내용이 정확히 일치. 원본에 `summary.txt`(155 B), `preflight.txt`(366 B), `observation.json`(781 B) 3개만 포함됨. 메모리 코어, 전체 Journal, raw glxinfo, Gazebo 런타임 로그는 **없다**.

```text
D06_C24_WSL2_PREVIOUS_EVENT_BOOT_UNVERIFIED_HOLD
D06_C23_NO_NEW_SIGSEGV_NO_GAZEBO
kernel_core_pattern=|/usr/lib/systemd/systemd-coredump %P %u %g %s %t 9223372036854775808 %h %d
boot_id=258e0071-2816-4b1c-893b-5622a181ef91
systemd_socket_load=loaded
systemd_socket_active=True
storage_config=DEFAULT_OR_UNAVAILABLE
```

`observation.json` 주요 값:
- `kernel_release=6.18.40.1-microsoft-standard-wsl2\n`, `environment=WSL2_UBUNTU2404`, `pid1_systemd=true`.
- `dxg_present=true`, `wslg_visible=true`, `renderer_class=D3D12_OTHER`.
- `journal_storage_class=PERSISTENT_DIR_PRESENT`, `core_capture_proven=false`, `gazebo_exit0_proven=false`.
- `journal_access=true`, `journal_exact_pid_rows=0`, `journal_exact_segv_bash_rows=0`, `coredumpctl_exact_info=false`, `event_boot_known=false`, `root_cause=UNCONFIRMED`.

**C24 실제 장비 실증 수준**은 WSL2 코어 색인/현재 GLX 레이어에 대한 **읽기 전용 관측**이다. Gazebo, Nav2, CM120/Guard150 및 Scan300 실제 재실행 증거가 아니다.

## B. 최초 실패 경계 3개 — 서로 독립

### B1. Windows/WSL2 부트 경계

C23 이전 제출 `readonly-nxj6poaa` 및 `readonly-gnwhry3r`의 boot ID는 `3f362cbb-3d40-468e-9f77-01a5243b3fa6`. 이번 `258e0071-2816-4b1c-893b-5622a181ef91`와 명백히 **다름**. 두 관측 사이에 새 WSL2 Linux 부트가 있었음은 확인. 그러나 C22 합성 Bash SIGSEGV 당시 boot ID를 기록하지 않아 C22→C23과 C22→C24의 동일 부트 여부는 확정할 수 없음. 따라서 PID1424에 대한 현재 부트 조회 0건을 과거 저장소 손상, kernel SIGSEGV 전달 실패, 혹은 core retention 이슈로 승격하지 않음.

**C26 조치:** 과거 PID 검색 반복 금지. 별도 새로운 실행이 필요해지면 당시 boot ID + PID + signal + mono/real time을 같은 증거로 보존해야 함.

### B2. WSLg GPU 어댑터 경계 — 새로운 중요한 불확실성

과거 NVIDIA 실 Gazebo NO_GOAL 증거에서는 GL/Ogre2 renderer `D3D12 (NVIDIA GeForce RTX 2060 with Max-Q Design)`이었다. 이번 읽기 전용 `glxinfo -B` 분류는 **`D3D12_OTHER`**. 이 레이블은 프로그램상 renderer 문자열에 `d3d12`는 있지만 `nvidia`가 없다는 뜻이지 Intel GPU 확정이 아니다.

Microsoft WSLg GPU 선택 문서는 Mesa D3D12에서 실제로 Intel iGPU와 NVIDIA dGPU가 다르게 선택될 수 있음을 예제로 보여줌:
- https://github.com/microsoft/wslg/wiki/GPU-selection-in-WSLg
- https://github.com/microsoft/wslg/blob/main/README.md

**가능한 가설:** Intel/AMD 어댑터가 선택되었거나, 드라이버 표기 변경 또는 선택 환경이 달라졌을 수 있음. 실제 renderer 원문이 TAR에 없으므로 어느 가설도 확정하지 않음. `/dev/dxg`와 `/mnt/wslg`가 존재한다는 것만으로 NVIDIA GLX 선택이나 Gazebo 서버 GPU 선택을 증명할 수 없음. 현재 `glxinfo`는 읽기 전용 보조 프로세스이고, 원래 `gz sim -s`와 환경/어댑터가 동일했는지도 아직 모른다.

**시연 위험:** GPU가 바뀌면 Gazebo Harmonic GPU LiDAR 및 RTF/Scan 전달 주기, 종료 시 GL 해제 경로가 달라질 수 있어 기존 두 런의 비교가 무효화됨. 그러나 GPU 선택 차이를 과거 Gazebo SIGSEGV의 원인으로 단정하지 않으며, scan/CM/Guard TTL을 늘리지 않는다.

**C26 조치:** 기존 C23/C24 진단기의 `glxinfo -B` 실제 `Device:` 및 `OpenGL renderer string:`에서 장치 모델명만 최대 160글자로 보존. `D3D12_NVIDIA`, `D3D12_INTEL`, `D3D12_AMD`, `D3D12_OTHER`, `SOFTWARE_LLVMPIPE`를 구분. `MESA_D3D12_DEFAULT_ADAPTER_NAME` 환경 변수 사용 여부(불리언만)도 기록. 자동 GPU 변경 및 모든 Mesa/Windows 드라이버 수정 금지. GLX 정상도 `gazebo_renderer_proven=false`, `gazebo_exit0_proven=false`.

### B3. Ubuntu systemd 코어 저장 경계

`systemd-coredump.socket`이 현재 active이고 `core_pattern`이 파이프형이라는 것은 **현재 코어 수집 경로의 구성**을 보여 줄 뿐, 이전 사건에서 journal metadata + 외부 core가 저장되었다는 증거가 아님.

`PERSISTENT_DIR_PRESENT`는 기존 C24 구현이 단순히 `/var/log/journal` 디렉터리 존재를 본 결과. 실제 `Storage=`, journald flush, 과거 boot journal 유지 및 해당 crash event 존재는 확인하지 않음. `storage_config=DEFAULT_OR_UNAVAILABLE`은 유효 기본 저장설정이라는 검증이 아닌 미확인값. Linux piped core handler와 `ulimit -c`에 대한 동일 오류 추측은 금지.

공식 문서:
- https://www.freedesktop.org/software/systemd/man/latest/systemd-journald.html
- https://www.freedesktop.org/software/systemd/man/255/journald.conf.html
- https://www.freedesktop.org/software/systemd/man/latest/systemd-coredump.html
- https://man7.org/linux/man-pages/man5/core.5.html

**C26 조치:** `journal_persistence_proven=false`를 명시하고 기존 `core_capture_proven=false` 유지. 코어 덤프를 새로 만들거나 systemd 서비스를 재설정하지 않음.

## C. 미해결 실제 Gazebo NO_GOAL 인수

이전 별도 원본 `d06-forensic-ab-no-goal-1jvaRyCE.tar.gz`에서 관찰: READY 이후 20.161초 dual Scan 최대 raw271.130ms / safety237.858ms, Nav/Loc Lifecycle ACK, Collision Monitor exit0, 그러나 Gazebo server `gz sim -r -s` **PID19280 exit -11(SIGSEGV)**. 전체 인수 **HOLD**. 준비 이전 독립 ROS 전체 세션 gap raw423.494ms/safety418.905ms는 학생의 실제 첫 TTL source pair와 동일하다고 입증되지 않음.

**이번 C24 RAW에는 해당 Gazebo 실행 자체가 없다.** renderer `D3D12_OTHER`만 보고 이전 종료 SIGSEGV나 타이밍 위반 원인을 해결했다고 보고하지 않음. 독립 G3 실 GPU 호스트 검증 필수 제거(C18)는 유지하지만, owner WSL2 실제 안전/종료 검증 생략을 뜻하지 않는다.

## D. RED→GREEN→REFACTOR→REVIEW→COMMIT

- 기존 결과 보존: C24 공개 CI [#44768278710](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44768278710) PASS, 실제 WSL2 이번 TAR은 C24 관측/HOLD.
- **RED** C26 오프라인 fixture `d06/tests/test_d06_c26_wslg_gpu_identity_evidence.py` + 기존 workflow 연결: 커밋 `3d4f750db13fff023aa59525263e9bd002646525`, 공개 [#44850098858](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44850098858) **2 FAIL·3 ERROR**, 실제 GLX 모델·journal 지속성 판정 누락 확인.
- **GREEN/REFACTOR** 기존 `d06/tools/d06_c23_core_index_readonly_doctor.py`만 수정, 실제 `glxinfo -B`의 들여쓰기된 `Device:` 출력과 제어문자 제거도 검증. 최종 코드 `6e727c784ce43077fa8fd04ab5fcb6559bb6fbe3`, Git blob `11eab75ea623b97fe81ed12753d2d0a848044dce`.
- 새 테스트 6개: NVIDIA/Intel/unknown GLX class, indented Device, GLX 결과의 Gazebo 인수 오판 방지, journal directory != 실제 core 보존.
- **GREEN** [D06 공개 L0 #44850220898](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44850220898): **6/6 PASS**, 전체 워크플로 PASS, `NO_ROS_NO_GAZEBO_NO_GOAL`.
- 같은 코드의 [Ubuntu 24.04 CLI #44850220881](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44850220881) SUCCESS 및 [Runner Canary #44850220934](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44850220934) SUCCESS.
- REVIEW: 새 Gazebo, ROS, SIGSEGV, Goal, GPU 환경 변수 override, 시스템 설정 변경 **모두 없음**. 공개 CI의 mock/CLI 테스트로 WSL2 GPU 드라이버 동작이나 Gazebo 종료를 PASS 승격 금지.

## E. 다음 강사 WSL2 작업 — 새로운 정보만 확보하는 단일 읽기 전용 검사

이전 PID1424에 대한 `coredumpctl` 조회 결과를 다시 실패 원인으로 확대하지 않는다. C26은 기존 C23 진단기가 `--doctor`로 GPU 계층도 함께 읽는 방식이므로, **새 GPU 장치 모델이 필요할 때 단 한 번만** 수행하고 과거 PID 조회는 의미 없는 보조 정보로 취급한다.

```bash
(
  set -Eeuo pipefail
  SHA="6e727c784ce43077fa8fd04ab5fcb6559bb6fbe3"
  BLOB="11eab75ea623b97fe81ed12753d2d0a848044dce"
  SCRIPT="$(mktemp --suffix=.py)"
  trap 'rm -f "$SCRIPT"' EXIT
  curl -fLsS --retry 3 --max-time 90 \
    "https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public/$SHA/d06/tools/d06_c23_core_index_readonly_doctor.py" -o "$SCRIPT"
  test "$(git hash-object "$SCRIPT")" = "$BLOB"
  python3 "$SCRIPT" --self-check
  RC=0
  python3 "$SCRIPT" --doctor || RC=$?
  echo "D06_C26_DIAGNOSTIC_RC=$RC"
  test "$RC" -eq 3
)
```

기대 신규 출력을 실제로 확인해야 함: `D06_C26_GLX_RENDERER`, `D06_C26_GLX_DEVICE`, `D06_C26_NVIDIA_GLX_CONFIRMED`, `D06_C26_ADAPTER_OVERRIDE_PRESENT`, `D06_C26_JOURNAL_PERSISTENCE_PROVEN=false`. 출력한 작은 `D06_C23_FORENSIC_ARCHIVE` TAR + sidecar만 공유. `--doctor`가 조회하는 과거 PID1424에는 C22 boot ID가 없어 여전히 원인 미확정; 해당 항목 재실행은 **새로운 coredump 증명 아님**.

## F. Gate / 정확한 인수 상태

```text
INPUT_SHA256=PASS
INPUT_WSL2_KERNEL=6.18.40.1-microsoft-standard-wsl2
INPUT_BOOT_ID=258e0071-2816-4b1c-893b-5622a181ef91
INPUT_PREVIOUS_C23_BOOT_DIFFERENT=true
INPUT_C24_GLX_RENDERER_CLASS=D3D12_OTHER
INPUT_ACTUAL_ADAPTER_NAME=NOT_RECORDED
INPUT_JOURNAL_DIRECTORY_PRESENT=true
INPUT_JOURNAL_PERSISTENCE=NOT_PROVEN
INPUT_SYSTEMD_COREDUMP=NOT_PROVEN
C26_PUBLIC_CI_L0=PASS (6 NEW, NO ROS/GAZEBO)
C26_OWNER_WSL2_GLX_MODEL=NOT_RUN
G07_ACTUAL_GAZEBO_SERVER_EXIT0=FAIL_PREVIOUS_EXIT_MINUS11
G07_CM120_GUARD150_MOVING_END_TO_END=NOT_RUN
G07_OVERALL_DEMO_STABILITY=NOT_VERIFIED
INDEPENDENT_WSLG_G3_REQUIRED=false
MOVING_GOAL_ALLOWED=false
AXIA_MVP_DEMO_ACCEPTED=HOLD
CERTIFIED_ESTOP=false
MAIN_MERGED=false
```
