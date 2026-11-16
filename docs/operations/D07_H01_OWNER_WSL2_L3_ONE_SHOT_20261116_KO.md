# Block B D07-H01 — 실제 WSL2 Owner WSLg GUI 인수 원샷

기준일: 2026-11-16. 공개 CI L2 성공 [Run #43793585641](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43793585641), public code source SHA `ab2ebf98ab50f35f926daf25be559870d5f0a2d5`, private Instructor source SHA **`0e16c3781cdee603518a653f120a3be352e5f7b2`**. 학생 정답은 이 공개 실행기에 들어있지 않다.

## 1. Owner WSL2 단일 터미널, 한 번에 수행

Windows 10/11 WSL2 Ubuntu 24.04, ROS 2 Jazzy, Gazebo Harmonic, RViz2, WSLg DISPLAY와 Instructor 비공개 저장소 Git 접근 권한이 기존에 준비되어 있어야 한다. 기존 Owner 전용 Nav2 overlay 경로 `$HOME/axia_p1_abc_verification/results/p1-nav2-official-overlay/install/setup.bash`가 존재하면 자동으로 source한다. 다른 overlay를 사용하면 환경변수 `AXIA_NAV2_OVERLAY_SETUP`에 전체 파일 경로를 지정한다.

```bash
(
  set -Eeuo pipefail
  SHA='6de2cf873550196777416c43b179ff9815e38691'
  SCRIPT="$(mktemp --suffix=.sh)"
  trap 'rm -f -- "$SCRIPT"' EXIT
  curl -fL --retry 3 --max-time 90 -sS "https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public/$SHA/scripts/d07_h01_owner_wsl2_gui_once.sh" -o "$SCRIPT"
  bash -n "$SCRIPT"
  bash "$SCRIPT" --self-check
  bash "$SCRIPT" --run
)
```

`SHA`는 공개 실행기 자체의 검증된 커밋이며, 내부 Instructor 소스는 별도로 40자리 SHA 고정한다. 공개 스크립트는 기존 private 강사 저장소 인증을 재사용해 정확한 소스만 체크아웃한다. 인증 실패 시 비밀번호를 요청하며 무기한 대기하지 않고 `D07_H01_OWNER_PRIVATE_CLONE_DENIED_AUTH_OR_NETWORK`로 중단한다. 그 경우 `gh auth login` 또는 기존 Git 자격 증명 연결을 한 번 점검해야 한다.

실행 터미널의 로그를 줄줄이 출력하는 대신 `$HOME/axia_d07_h01_wsl2_acceptance/d07-h01-<UTC>-<PID>/owner_stdout.log`에 보존한다. 화면에는 Gazebo Harmonic 및 RViz2가 열리며 `Before → Intrusion → Restored`를 확인한다. `Ctrl+C`로 중단 시 이 실행의 프로세스 그룹만 정리한다. `pkill`, `wsl --shutdown` 실행 금지. 기본 ROS_DOMAIN_ID=65이며 `AXIA_D07_OWNER_ROS_DOMAIN_ID`로 변경 가능.

## 2. 성공 패턴 / 실패 시 제출할 단일 원본

```text
D07_H01_OWNER_PUBLIC_BOOTSTRAP_L0_PASS PRIVATE_SHA=0e16c3781cdee603518a653f120a3be352e5f7b2 NO_ROS_NO_GAZEBO_NO_GOAL
D07_H01_OWNER_WSL2_START source_sha=0e16c3781cdee603518a653f120a3be352e5f7b2 ...
D07_H01_OWNER_RUNTIME_RC=0 RVIZ_X11=1 GAZEBO_X11=1 XWININFO_AVAILABLE=1
D07_H01_OWNER_PHASES ... before/intrusion/restored ...
D07_H01_OWNER_WSL2_AUTOMATED_L3_CANDIDATE_PASS_VISUAL_CONFIRMATION_PENDING
D07_H01_OWNER_EVIDENCE_ARCHIVE=/home/.../d07-h01-*.tar.gz
D07_H01_OWNER_WSL2_AUTOMATED_CANDIDATE_PASS_USER_GUI_VISUAL_REVIEW_PENDING
```

Owner L3 최종 정식 인수는 현장에서 **WSLg에 두 실제 GUI가 표시되고 Path 변경·복원, 종료 시 두 화면 닫힘**을 직접 확인한 후 판정한다. 위 자동 검사는 외부 GUI 실제 내용까지 픽셀 판독한 것은 아니므로 반드시 visual confirmation 단계가 남는다. public CI L2 PASS만으로 Owner L3 PASS라 쓰지 않는다.

실패한 경우 다시 Gazebo를 반복 실행하지 말고 스크립트가 출력한 `D07_H01_OWNER_EVIDENCE_ARCHIVE=/home/...tar.gz` 한 파일과 `*.sha256` 값을 제출한다. 원본의 **최초 안전 상태 전이와 최초 타이밍 위반**을 우선 분석하고, 재현 가능 부분을 공개 CI 회귀 RED→GREEN으로 편입한다. 장비를 바꾸거나 TTL/Costmap 허용 조건을 우회하지 않는다.

## 3. 검증 범위

- L0: 공개 GitHub Actions [#43794649548](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43794649548)에서 Instructor 45개 단위/계약 PASS, 공개 Owner one-shot shell syntax + `--self-check` PASS. **NO ROS / NO Gazebo / NO WSL2**.
- L2: 공개 [#43793585641](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43793585641), 실제 Gazebo/RViz2 X11 창 2개, 공식 Nav2 Before/Intrusion/Restored 원본 Path와 DDS 구독, no-moving-Goal 범위 PASS.
- Owner L3: WSL2/WSLg **NOT_RUN**, 사용자 실행 로그·화면 확인이 필요.
- 이번 L2는 D07 교육용 **SIM noise-free LiDAR** 임시 SDF 프로파일에 한정. 원본 noisy sensor, Controller 주행 Goal, collision-free, CM→Guard 150ms, Scan/Odom 300ms 등 전체 안전 계층과 인증 E-Stop은 **NOT_VERIFIED**.
- 사용자 승인 전 Instructor/Student/Public 어느 저장소도 `main` 병합하지 않는다.
