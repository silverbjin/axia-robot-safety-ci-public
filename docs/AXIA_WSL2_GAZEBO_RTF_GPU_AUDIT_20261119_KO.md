# AXIA WSL2 Gazebo Harmonic GPU / RTF read-only audit (2026-11-19)

대상: 강사 WSL2 DESKTOP-4B51LPI, ROS 2 Jazzy, Gazebo Harmonic / WSLg.
목표: Gazebo RTF가 약 90%인 실행기와 약 20%인 실행기의 GPU/센서/CPU 환경을 같은 방법으로 기록하고 차이를 좁힌다.

## 기존에 확인된 사실

- Intel Iris Xe / D3D12 / OpenGL 4.1 (기본 WSLg).
- NVIDIA RTX 2060 Max-Q / D3D12 / OpenGL 4.6 (명시적 NVIDIA 선택).
- D07 Owner는 Gazebo 서버의 GPU 환경을 분리하고 GUI 자식에 NVIDIA를 부여한다.
- D08 staged GUI는 Gazebo GUI와 RViz2 자식에만 D3D12 NVIDIA 설정을 부여하며, Nav2가 실행한 Gazebo 서버의 GPU 설정은 명시적으로 바꾸지 않는다.
- D08 RGB-D: 기본 30Hz, 선택형 10Hz. D04/D05와 다른 프로필이다.
- 기수집 현장 데이터의 6.81%→15.04%, 그리고 별도 프로필의 약 91.86%는 비교 조건이 달라 GPU 단독 원인으로 확정할 수 없다.

## 라이브 시연 실행 중 두 번째 터미널에서 그대로 실행

Gazebo / Nav2 / RViz를 종료하지 말고 다음 블록을 실행한다.
실행은 공개 GitHub의 정확한 스크립트 커밋 SHA 9c03b0eb05a1f0047aebbaad53101b24750d9960을 사용한다.
Python 3 기본 라이브러리만 사용하며 ROS/GPU/OS 설정을 수정하지 않는다.

~~~bash
(
  set -Eeuo pipefail
  BIN="$HOME/axia_gpu_rtf_diagnostics/bin"
  mkdir -p "$BIN"
  DIAG="$BIN/axia_wsl2_gazebo_rtf_gpu_audit_9c03b0eb.py"
  if [[ ! -s "$DIAG" ]]; then
    TMP="$(mktemp "$BIN/.gpu_audit.XXXXXXXX.py")"
    trap 'rm -f -- "$TMP"' EXIT
    curl -fLsS --retry 3 --max-time 60 \
      "https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public/9c03b0eb05a1f0047aebbaad53101b24750d9960/scripts/axia_wsl2_gazebo_rtf_gpu_audit.py" \
      -o "$TMP"
    python3 -m py_compile "$TMP"
    mv -- "$TMP" "$DIAG"
  fi
  python3 "$DIAG" --self-check
  python3 "$DIAG" --seconds 20
)
~~~

예상 로그 형식 (실제 GPU/RTF 성공값이 아닌 출력 스키마):

~~~text
AXIA_RTF_GPU_AUDIT_SELF_CHECK_PASS ROS_NOT_RUN GAZEBO_NOT_RUN
AXIA_RTF_GPU_AUDIT_CAPTURE_STATUS=CAPTURED
AXIA_RTF_GPU_AUDIT_GAZEBO_PARTITION=<running partition>
AXIA_RTF_GPU_AUDIT_SERVER_GPU_ENV=<running server process env>
AXIA_GAZEBO_INTERVAL_RTF_PERCENT=<actual measurement>
AXIA_RTF_GPU_AUDIT_ZIP=/home/.../axia_gpu_rtf_diagnostics/audit_.../axia_wsl2_gazebo_rtf_gpu_audit.zip
AXIA_RTF_GPU_AUDIT_REPORT=/home/.../summary.txt
~~~

라이브 세션이 없거나 GZ_PARTITION이 모호하면 CAPTURED가 아니라
NO_UNIQUE_GAZEBO_PARTITION 등으로 기록된다. 이때 summary.json을 확인한 뒤
실제 Gazebo 서버 PID로 --server-pid <PID> 또는 --partition <PARTITION>을 지정해 재실행한다.

## 두 실행기 A/B 비교

1. 실행기 A로 Gazebo를 시작하고 안정화한 뒤 위 명령 1회. ZIP 보존.
2. A를 정상 종료하고 실행기 B로 Gazebo를 시작한다. 동일 조건으로 위 명령 1회.
3. ZIP 두 개를 같은 진단 Python 파일로 비교한다. 두 Gazebo를 동시에 시작하지 않는다.

~~~bash
python3 "$HOME/axia_gpu_rtf_diagnostics/bin/axia_wsl2_gazebo_rtf_gpu_audit_9c03b0eb.py" --compare \
  "/path/to/90percent.zip" "/path/to/20percent.zip"
~~~

비교는 interval_rtf_percent = delta(sim_time) / delta(real_time) × 100,
server.gpu_env, gui.gpu_env, glxinfo 자식 렌더러, RGB-D 디스크 설정 후보를 나란히 본다.
rtf_field_median은 보조 통계이며 구간 RTF와 혼동하지 않는다.
changed_conditions는 원인 후보이지 root_cause_confirmed는 false이다.

## 안전성과 검증 경계

- 스크립트는 Gazebo/ROS 노드를 생성, 종료, 일시 정지하지 않는다. 필요시 자체 glxinfo와 gz topic 읽기 전용 구독 프로세스만 종료한다.
- GPU 환경변수는 프로세스별 수집하고 전역 .bashrc나 Mesa·GPU 드라이버를 변경하지 않는다.
- glxinfo 자식의 GPU는 Gazebo 서버 Ogre2 렌더러의 직접 증명이 아니다. Ogre2 로그는 이전 세션일 수 있다.
- nvidia-smi에 프로세스가 나타나지 않아도 WSLg OpenGL이 GPU를 사용하지 않는다고 결론낼 수 없다.
- 최신 디스크 SDF에서 읽은 센서 주기는 현재 Gazebo 월드와 일치하는지 별도 검증이 필요하다.
- 원본 world stats는 마지막 200 KB만 저장하고, 보고서+SHA256SUMS를 ZIP으로 압축한다.
- ROS 메시지 TTL, CM / Guard 120/150ms 경계, Nav2 Goal, 움직임, 실제 HW E-Stop 및 GUI 픽셀 증거는 NOT_RUN.
- L0 검사: python3 -m pytest -q tests/test_axia_wsl2_gazebo_rtf_gpu_audit.py
- main 병합은 사용자 승인 전 수행하지 않는다.

참고: WSLg GPU selection (https://github.com/microsoft/wslg/wiki/GPU-selection-in-WSLg),
Gazebo Harmonic troubleshooting (https://gazebosim.org/docs/harmonic/troubleshooting/),
Gazebo GUI RTF (https://gazebosim.org/docs/harmonic/gui/),
Gazebo sensors update_rate (https://gazebosim.org/docs/harmonic/sensors/).
