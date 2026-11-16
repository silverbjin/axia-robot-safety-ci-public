# AXIA D07-H01 — WSL2 CPU·RAM·GPU·Gazebo 서버/GUI 원샷 진단 가이드

작성일: 2026-11-16 · 대상 WSL2 Ubuntu 24.04 / ROS 2 Jazzy / Gazebo Harmonic / RViz2 · **읽기 전용, NO MOVING GOAL**

## 목적과 기준

Owner GUI 사진에서 RViz2의 Costmap이 표시되지만 Gazebo Sim의 3D 화면과 Entity Tree는 비어 있다. D07 H01은 **stationary Waffle + official ComputePathToPose 읽기 전용 경로 3단계**이므로 로봇이 이동하지 않는 것은 설계에 부합한다. Gazebo GUI 화면이 비어 있는 것은 별도 원인 분석 대상이다. ROS 서버와 실제 Scan·Costmap이 실행되었다는 이전 증거만으로 렌더링 정상 판정을 내리지 않는다.

Microsoft 문서의 기본 WSL2 RAM 상한은 별도 `.wslconfig`가 없으면 호스트 메모리 50%. Windows 32GB이면 기본 약 16GB이며 **최종 판정은 실제 WSL2 계측**으로 확인한다. `/dev/dxg` 존재는 GPU 전달 장치가 있음을 뜻할 뿐 앱이 GPU 가속을 실제 사용한다는 증거는 아니다. `LIBGL_ALWAYS_SOFTWARE=1`은 기존 AXIA GUI 스크립트가 설정해 CPU OpenGL 렌더링을 강제할 수 있다. 이 파일은 **설정을 변경하지 않는다**.

## 1. WSL2 두 번째 터미널에서 단일 원샷

**Gazebo·RViz2가 실행된 동안** 또는 시연 직전에 아래 명령 실행. 원래 데모는 첫 번째 터미널에 두며, 모니터는 두 번째 터미널에서만 수행한다.

```bash
(
  set -Eeuo pipefail
  SHA='27d9ee5bb486f3de5846fccd8cfb29efb007a8fa'
  SCRIPT="$(mktemp --suffix=.py)"
  trap 'rm -f -- "$SCRIPT"' EXIT
  curl -fL --retry 3 -sS \
    "https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public/${SHA}/scripts/axia_wsl2_gui_resource_monitor.py" -o "$SCRIPT"
  python3 "$SCRIPT" --self-check
  python3 "$SCRIPT" --duration 150 --interval 2
)
```

150초간 2초 간격으로 읽기 전용 샘플을 수집한다. Ctrl+C는 새 샘플링을 멈추고 이미 확보한 원본을 정리·압축한다. 사용자 PC의 WSL CPU·RAM과 앱 PID를 읽으며 루트/관리자 권한, `ros2 topic pub`, 주행 Goal, Gazebo 물체 변경, `wsl --shutdown`을 사용하지 않는다.

시연이 이미 종료된 상태에서 실행하면 WSL 자원 정보는 기록되지만, `target_process_observed=false`일 수 있으므로 Gazebo GUI 사용량 또는 연결 상태를 평가할 수 없다.

## 2. 출력과 검증

터미널 예시 (숫자는 **임의 예시**, 실제 PC 측정값 아님):

```text
AXIA_WSL2_MONITOR_L0_PASS_NO_ROS_NO_GUI
AXIA_SAMPLE n=1 WSL_RAM_GiB=... AVAILABLE_GiB=... CPU=warming% GazeboServer=1 GazeboGUI=1 RViz=1 PARTITION=MATCH_NOT_CONNECTION_PROOF
AXIA_WSL2_MONITOR_SUMMARY=<경로>/summary.json
AXIA_WSL2_RESOURCE_MONITOR_BUNDLE=<경로>.tar.gz
AXIA_WSL2_RESOURCE_MONITOR_SHA256=<경로>.tar.gz.sha256
AXIA_WSL2_RESOURCE_MONITOR_HOST_ONLY_L3_GUI_NOT_PROVEN
```

결과 폴더: `~/axia_wsl2_monitor/axia-wsl2-monitor-<UTC>-XXXXXXXX/`

| 파일 | 계측 내용 |
|---|---|
| `summary.json` | 샘플 수, 최고 WSL CPU %, 최소 RAM 여유 GiB, 대상 앱 RSS 합계 최대, Gazebo 프로세스 발견/파티션 불일치 여부 |
| `samples.jsonl` | 시간별 WSL 메모리, 총 CPU 사용률, Gazebo GUI/서버, RViz2 PID·CPU%·RSS, 프로세스별 `GZ_PARTITION`, `ROS_DOMAIN_ID`, `LIBGL_ALWAYS_SOFTWARE` |
| `renderer_glxinfo_B.txt` | OpenGL Renderer. `llvmpipe`는 CPU software, `D3D12`는 WSLg GPU 가속 경로 후보 |
| `wsl_status.txt` | `/dev/dxg`, WSLg mount, DISPLAY |
| `nvidia_gpu.txt` | NVIDIA 도구가 있을 때 GPU 사용률·VRAM; AMD/Intel/일부 WSL2에서는 지원하지 않으며 없다고 GPU=0이라 단정하면 안 됨 |
| `windows_host_readonly.txt` | Windows 총/가용 RAM, GPU 어댑터 이름, `.wslconfig`에서 memory/processors/swap만 |
| `gazebo_topic_discovery.txt` | 기존 서버 `GZ_PARTITION`을 사용한 `gz topic -l`의 실제 발견 목록 (실패·미발견도 원본 기록) |
| `kernel.txt` / `wslg_versions.txt` | WSL 커널과 WSLg 버전 |

모니터는 현재 사용자의 환경 및 실행 중 프로세스에서 **소수의 허용된 필드만** 읽는다. `gh` 토큰, 비공개 Instructor 소스, 사용자 전체 환경변수, Wi-Fi 암호, 홈 파일 전체를 압축하지 않는다.

## 3. 데이터 해석

- `ram_total_gib`: WSL2 VM 안에서 보이는 RAM (Windows 32GB 전체와 다를 수 있음). `ram_available_gib`와 최고 프로세스 `rss_mib`을 함께 본다.
- `ram_available_gib`가 매우 낮거나 swap 사용량 증가·CPU 과부하가 지속되면 실제 시연 중 메모리/CPU 병목 후보.
- `gazebo_gui` 및 `gazebo_server` PID가 모두 있는데 `gz_partition_alignment.status=MISMATCH`이면 **최우선 Gazebo Transport 분리 원인 후보**. `MATCH_NOT_CONNECTION_PROOF`도 GUI 실제 3D 렌더 성공을 의미하지 않는다.
- `renderer_glxinfo_B.txt`에서 `llvmpipe`면 CPU software GL. `D3D12`로 나와도 실행 중 GUI 프로세스의 `libgl_always_software=1`이면 **앱은 별도로 CPU 렌더링 강제** 상태일 수 있다.
- NVIDIA GPU 사용률이 N/A이면 사용하지 않는다는 뜻이 아니라 도구의 WSL2 지원 범위일 수 있다. Windows 작업 관리자 → 성능 → GPU를 병행 확인하면 AMD/Intel의 실측 보완에 도움이 된다.
- Gazebo 공식 문서상 `gz sim -g` 독립 클라이언트가 서버에 연결하지 못하면 빈 창 상태일 수 있다. 분리 진단을 위해 서버/GUI `GZ_PARTITION`와 `gz topic -l`를 우선 확인한다.

**권장 작업 순서:** 모니터 150초 실행 → 첫 번째 터미널에서 기존 D07 GUI 시연 1회 → 결과 두 파일 첨부 → 샘플의 최초 분기 (파티션, renderer, RAM, CPU) 분석. 스크립트로 프로그램을 재시작하거나 자원을 임의 증설하지 않는다.

## 4. 공개 CI 근거 / 검증 수준

- 소스: `scripts/axia_wsl2_gui_resource_monitor.py` SHA `27d9ee5bb486f3de5846fccd8cfb29efb007a8fa`.
- 테스트: `tests/test_axia_wsl2_gpu_resource_monitor.py` 5개. 메모리 파싱, Gazebo GUI/server 역할·파티션 불일치, GLX/GPU 미검증 처리, CPU delta, 1초 **실제 Linux /proc 샘플과 결과 tar.gz + SHA256**.
- 공개 RED: [Run #43802260439](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43802260439) — 모니터 모듈 미구현으로 5건 실패.
- 공개 GREEN: [Run #43802495802](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43802495802) — D07 기존 45, Owner 9, Monitor 5 = 총 **59 L0 PASS**.
- `--self-check`는 NO ROS·NO GUI. CI의 짧은 Linux 샘플도 **WSL2 실제 GPU·Gazebo 렌더 테스트가 아님**. Owner 진짜 결과를 첨부받기 전 리소스 충분·가속 사용·GUI 정상이라고 보고하지 않는다.
- 공식 Nav2·Gazebo 코드, D07 Instructor private source SHA, 안전 TTL, ROS Goal, 학생 TODO, 기존 Owner runner, main 브랜치 모두 변경하지 않음.

## 참고
- Microsoft WSL 설정: https://learn.microsoft.com/en-us/windows/wsl/wsl-config
- Gazebo Harmonic Getting Started: https://gazebosim.org/docs/harmonic/
