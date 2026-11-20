# AXIA D06 C24 — Native Linux가 아닌 Windows WSL2 Ubuntu 24.04 / WSLg D3D12 전용 디버깅 기준선

작성일: 2026-11-21(KST) · 공개 PR #177 · `fix/d06-wslg-lidar-vs-rtf-ci-20261118` · **main 미병합**.

## 1. 사용자 정책 확정

사용자의 실제 운영 환경은 **Windows 호스트 + WSL2 Ubuntu 24.04 + systemd + WSLg GPU D3D12 NVIDIA RTX2060 Max-Q + ROS2 Jazzy + Gazebo Harmonic + Nav2**다.

Native Linux/Ubuntu 또는 GitHub-hosted Linux/Xvfb에서 성공한 결과를 해당 Windows WSL2 환경 전체의 Gazebo/CM/Guard/Scan 안전 인수로 보고하지 않는다. 별도 독립 GPU G3 호스트는 C18에 따라 필수 게이트에서 제외하되 **실제 강사 WSL2**는 생략하지 않는다.

구별해야 할 최소 시스템 경계:
1. Windows 호스트 GPU 드라이버 / WSLg 시스템 배포판의 Wayland/X11 렌더링 서비스 / Mesa D3D12 NVIDIA
2. WSL2 사용자 Ubuntu 24.04의 `/dev/dxg`, WSL kernel, PID1 systemd, `core_pattern` → Ubuntu `systemd-coredump.socket` → journald → `coredumpctl`
3. ROS2 Jazzy / Gazebo Harmonic server `gz sim -s` 종료 / Nav2 lifecycle ACK / CM native exit0 / 실제 Scan TTL300ms 및 이후 CM120ms, Guard150ms.

WSLg 시스템 배포판과 사용자 Ubuntu 배포판은 GUI 서비스/수집 위치가 달라, 어느 한쪽의 진단 기록만으로 다른 쪽 프로세스 실패를 증명하지 못한다. `glxinfo -B`는 렌더러 확인용이고 특정 `gz sim -s` 프로세스 종료 성공 증명은 아니다.

## 2. 공식 문서 근거

- Microsoft 공식 WSL2 가상화 구조: https://learn.microsoft.com/en-us/windows/wsl/wsl2-about
- Windows/WSL distro 설정 분리 및 systemd: https://learn.microsoft.com/en-us/windows/wsl/wsl-config , https://learn.microsoft.com/en-us/windows/wsl/systemd/
- WSLg 시스템 배포판 / D3D12 Mesa 가속 경로: https://github.com/microsoft/wslg/blob/main/README.md
- WSLg GPU 선택 / `glxinfo` 해석: https://github.com/microsoft/wslg/wiki/GPU-selection-in-WSLg
- Ubuntu에서의 systemd-coredump 저널/별도 저장 구조: https://www.freedesktop.org/software/systemd/man/255/systemd-coredump.html
- Linux `core_pattern` 파이프 핸들러와 RLIMIT_CORE: https://man7.org/linux/man-pages/man5/core.5.html

## 3. 기존 C22 현장 원본과 잘못될 수 있는 판정

현장 SHA 검증 TAR `probe-AuFytJyR.tar.gz`:
- `synthetic_child_rc=139` / PID `1424`; 프로세스가 SIGSEGV 종료한 후보는 확보.
- `stage=CORE_INDEX`, `D06_C22_SYSTEMD_CORE_RETRIEVAL_NOT_PROVEN_HOLD_NO_GAZEBO`.
- `/proc/sys/kernel/core_pattern`은 systemd-coredump pipe였지만, 실제 journald/외부 core 저장 경로는 **미확인**.
- C22는 당시 boot UUID를 저장하지 않았으므로 이후 WSL distro 재시작 또는 VM 종료가 있었는지 알 수 없다. 따라서 현재 `journalctl --boot`에서 PID 1424가 없다고 해서 **WSL2 코어 저장소가 고장 났다는 결론을 내릴 수 없다**.
- parent `ulimit -c 0`은 파이프형 core handler가 적용되는 경우 단독 원인으로 단정할 수 없다.

이와 별개로 이전 `1jvaRyCE` 실제 NO_GOAL: Nav2 Nav/Loc ACK, CM exit0, 후반 Raw/Safety Scan300ms 충족 후보였으나 **Gazebo server PID19280 exit -11** 원인은 현재도 미해결. 최초 서버 스택 미확보. 성공한 Linux Xvfb Gazebo L2를 WSLg NVIDIA의 서버 종료 성공으로 승격 금지.

## 4. C24 최소 수정과 회귀 결과

**최소 변경**
- 기존 도구 `d06/tools/d06_c23_core_index_readonly_doctor.py`의 읽기 전용 `--doctor` 진단 범위를 WSL2/WSLg 계층별로 확장.
- WSL2 커널 식별(`/proc/sys/kernel/osrelease`), PID1 systemd, `/dev/dxg`, `/mnt/wslg`, 선택적 `glxinfo -B` NVIDIA D3D12 vs llvmpipe 및 현재 `/var/log/journal` / `/run/log/journal` 디렉터리 구분. **수집/저널 지속성의 증명은 아님**.
- `event_boot_known=false`를 기록. 이전 C22 boot ID가 없고 PID 기록도 발견되지 않을 때 `D06_C24_WSL2_PREVIOUS_EVENT_BOOT_UNVERIFIED_HOLD`로 분류하여, 현재 부트 기록 부재를 과거 수집 실패로 오판하는 것을 방지.
- WSLg 디버깅 정보와 코어 수집 결과를 섞지 않음: `core_capture_proven=false`, `gazebo_exit0_proven=false` 유지.
- **ROS2/Gazebo/Nav2/CM/Guard/학생 런타임/안전 TTL 변경 0건**. `sudo sysctl`, `wsl --shutdown`, Mesa/드라이버 및 RMW override 없음.

**RED → GREEN → REFACTOR → REVIEW → COMMIT**
- RED 신규 회귀 `d06/tests/test_d06_c24_wsl2_wslg_layer_parity.py` 4개 + 공개 L0 등록 후 commit `99e1e2ee6a6bde08a4d9e960ce164b4850248e2c`, 공개 [Run #44768027525](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44768027525): **2 FAIL·2 ERROR**, WSL2 계층 판별 함수 부재 및 부트 경계 해석이 미구현됨을 확인.
- GREEN source commit `b6cb297e4a7c54b5d7e2d07c732a4b528084c8c2`, Git blob `aa60806e50973a9d7d997caa319afc5066bb8926`.
- [공개 L0 #44768278710](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44768278710): completed/success; 신규 4/4 `... ok`, 전체 D06 L0 성공, `AXIA_D06_G07_LIDAR_RTF_ISOLATION_L0_PASS_NO_ROS_NO_GAZEBO_NO_GOAL`.
- [같은 SHA Ubuntu 24.04 CLI #44768278702](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44768278702) SUCCESS; [Canary #44768278636](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44768278636) SUCCESS.
- REVIEW: pure offline fixtures only; CI에서는 현장 WSL2 조회/새 코어/새 Gazebo를 수행하지 않음. 환경 경계가 확인되지 않으면 HOLD를 유지. 전체 시연 인수로 승격 금지.

## 5. 기존 WSL2에서 단 1회 읽기 전용 조회 명령

다음은 **WSL2 사용자 Ubuntu 24.04**에서 실행. 기존 C23 조사와 동일하지만 C24 GREEN에 고정해 WSL2 계층과 부트 경계를 출력. `--doctor`의 비영 종료 코드 3은 **예상된 HOLD**, Gazebo 재실행 실패가 아님.

```bash
(
  set -Eeuo pipefail
  SHA="b6cb297e4a7c54b5d7e2d07c732a4b528084c8c2"
  BLOB="aa60806e50973a9d7d997caa319afc5066bb8926"
  SCRIPT="$(mktemp --suffix=.py)"
  trap 'rm -f "$SCRIPT"' EXIT
  curl -fLsS --retry 3 --max-time 90 \
    "https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public/$SHA/d06/tools/d06_c23_core_index_readonly_doctor.py" -o "$SCRIPT"
  test "$(git hash-object "$SCRIPT")" = "$BLOB"
  python3 -m py_compile "$SCRIPT"
  python3 "$SCRIPT" --self-check
  rc=0
  python3 "$SCRIPT" --doctor || rc=$?
  test "$rc" -eq 3
)
```

주의: `sudo -v`로 인증을 요청할 수 있으나, 뒤의 `sudo -n journalctl/coredumpctl`은 읽기 전용. `glxinfo -B`도 화면 환경이 있을 때만 상태를 조회한다. Goal/ROS/Gazebo/코어 생성 없음.

현장 출력 중 `D06_C24_WSL2_KERNEL`, `D06_C24_WSL2_PID1_SYSTEMD`, `D06_C24_WSLG_RENDERER_CLASS`, `D06_C24_WSL2_JOURNAL_STORAGE_DIR`, `D06_C24_WSL2_PREVIOUS_EVENT_BOOT_UNVERIFIED_HOLD`을 구분한다. 실제 검사 결과가 코어 없음을 보여도 현재 부트에 대한 부분 관찰일 뿐 과거 이벤트 수집 실패 확정 불가. 압축 forensic TAR + SHA256만 제출; raw memory core, 전체 journal 공유 금지.

## 6. 검증 수준 / 미검증 항목

```text
ENVIRONMENT_REQUIRED=WINDOWS_WSL2_UBUNTU_24_04_WSLG_D3D12
NATIVE_LINUX_CI_NOT_EQUIVALENT_TO_WSLG=true
C24_PUBLIC_L0=PASS
C24_NOBLE_CLI=PASS (NOT WSL2)
C24_WSL2_OWNER_DOCTOR=NOT_RUN
C22_OLD_BOOT_ID=NOT_RECORDED
C22_SYSTEMD_CORE_PIPELINE=NOT_PROVEN
GAZEBO_SIGSEGV_FIRST_STACK=NOT_CAPTURED
OWNER_WSL2_NO_GOAL=HOLD_GAZEBO_SERVER_EXIT_MINUS11
MOVING_CM120_GUARD150_E2E=NOT_RUN
AXIA_MVP_DEMO_ACCEPTED=HOLD
CERTIFIED_ESTOP=false
MAIN_MERGED=false
```
