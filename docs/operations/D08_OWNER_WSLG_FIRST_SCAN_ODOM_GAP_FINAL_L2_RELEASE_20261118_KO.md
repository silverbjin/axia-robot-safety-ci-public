# AXIA D08 — Owner WSLg 첫 Scan/Odom 수신 공백 최종 공개 CI·출고 후보 보고서

날짜: 2026-11-18 (KST) / 작성 언어: 한국어 / 범위: **D08 NO_GOAL 실제 Gazebo + 공식 Nav2 읽기 전용 Path**.

## 1. 변경 범위와 원본 증거

강사 WSL2 원본 Bundle SHA256: `78163b10cafad23338610cefcbe8e1c9516c829c2fff86ee0166e825b5477721`, 내부 `SHA256SUMS` **12/12 OK**. 비공개 원본은 공개 저장소에 업로드하지 않았다.

구버전 `a83629edd71ce51567e184451f2a76bafcf1318b`의 현장 NO_GOAL 실패:
- 처음 Scan callback 공백 `0.819491s` 및 Odom `0.752105s`가 기존 0.5s 상한을 초과했다.
- 직후 실물 ROS 메시지 age는 Scan `0.004799s`, Odom `0.000381s`. 실제 `map→base_link` TF2 stamp `2.808s`와 AMCL post-SetInitialPose Map Pose를 얻었지만 **첫 공백 기록 때문에** `D08_AMCL_REAL_MAP_BASE_TF_NOT_READY:D08_FIRST_LIVE_SCAN_ODOM_GAP`로 계속 차단했다.
- Nav2 로그의 초기 map TF 미발견·extrapolation 및 종료 RViz SIGABRT/임시 Gazebo SDF 삭제 실패는 구별한다. 당시 가장 이른 실제 위반은 Scan/Odom **ROS 수신 공백**이다. 근본 원인이 발행자 중단인지 DDS 지연인지 WSLg 렌더링·스케줄링인지는 이 원본만으로 확정하지 않는다.
- 실제 Gazebo RGB/Depth 640×480 및 0ms timestamp skew는 확인. 주행 Goal, robot cmd_vel, 인증 E-Stop은 실행한 적 없다.

관련 상세 인과관계 RED→GREEN 기록: `d08/docs/reports/D08_OWNER_WSLG_FIRST_SCAN_ODOM_GAP_RCA_20261118_KO.md`.

## 2. 시니어 개발자의 가설 → 최소 구현

가설: 기존 `d08/harness/d08_amcl_initial_pose.py`가 초기 read-only localization의 **역사적 첫 공백**과 그 후 실제 수신이 안정화된 **현재 readiness**를 구별하지 못한다. 첫 공백 자체를 지워서 '안전하다'라고 처리하는 것은 금지.

최소 조치:
1. 구독자에서 실제 ROS `/scan`, `/odom`, `/clock` callback의 **host monotonic 수신 시각 + ROS sim source stamp**를 bounded history로 저장한다.
2. 기록된 최초 공백을 그대로 유지한다. NO_GOAL, cmd_vel 미발행 상태에서만 **이후 새 실제 메시지가 1.0초 이상 연속 수신**되고, 각 수신 간격 `<0.5s`, 최신 age `<=0.5s`, Clock과 Scan/Odom source stamp 정합이 성립하면 read-only Path 전 Localization readiness를 인정한다.
3. 신규 공백·Clock 정체·비연속 stamp·현재 stale이면 기존처럼 FAIL-CLOSED한다. ROS QoS, 공식 Nav2/AMCL, Scan 10Hz SDF, CM/Guard 안전 TTL, 시뮬레이션 update rate는 수정하지 않았다.
4. `startup_gap_not_l3_safety_pass=true`를 남긴다. 이 정착 경계는 실제 주행의 안전성 증명이 아니다.

## 3. 실제 RED → GREEN과 오류 추적 (가짜 PASS 금지)

| 사이클 | 정확한 Git SHA / CI Run | 확인된 사실 |
|---|---|---|
| RED 계약 | `94f04443c58bc70045bed301d6bcc6af966210d0`, CI `#44268455861` | 최초 Scan 819ms/Odom 752ms 테스트: 복구 검사 함수 import 실패 |
| RED 워크플로 | `2f9863a50580858c01891d9272dd8697a5562ab4` | 최소 공개 CI L0 확보 |
| 최초 GREEN 구현 중 오류 | `4cf1a8fbc8a55b87792bb3cbce1cedb9fcbed02c`, CI `#44268795841` | Python `SyntaxError: '(' was never closed` + 기존 age 루프 누락, 실제 실패를 숨기지 않음 |
| GREEN 수정 | `3b329e912182bfa1a3b67f290312a17e877d9b87`, CI `#44268920802` | **19/19 PASS**, ROS-free L0만 |
| 공식 Nav2 건너뛰기 수정 | `a4dbb714f74d31ac410b1504f2b5087df3a4ec64` | 해당 PR의 `gazebo-official-nav2-oneworld` job을 실제 실행하고, NO_GOAL 후속 검증 추가 |

소스는 비공개 Instructor로 이전하지 않고 **공개 CI PR #166 개발 브랜치에만** 기록했다. Student TODO/강사 정답 정책은 변경하지 않았다.

## 4. 실제 Gazebo·공식 Nav2 L2 검증 확정

공개 Actions: https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44269396804
- 실행 결과: **completed / success**, 원본 실행 HEAD `a4dbb714f74d31ac410b1504f2b5087df3a4ec64`.
- 실제 4개 job: `l0-human-proxy-red-green`, `gazebo-contact-positive-once`, `gazebo-official-nav2-oneworld`, `real-gazebo-rgb-pinned-upstream-yolo-ros` = **전부 success**.
- 기존 공개 CI #44263690201/#44248098353의 같은-world Nav2 job은 skipped였으므로 이전 전체 workflow GREEN을 Nav2 L2로 오인하지 않는다.
- 이번 실제 L2 로그: `D08_AMCL_REAL_FIRST_POSE_PLUS_LIVE_TF_READY`; `D08_LIVE_NAV2_PATH_CANDIDATE` (실제 path 14 points / 0.4m), `D08_OFFICIAL_SAME_WORLD_THREE_PHASE_PATHS_L2_PASS_NO_GOAL`, `D08_REAL_GAZEBO_WAFFLE_RGBD_NO_GOAL_PASS`.
- **동일 L2 실행 3단계**: before / intrusion / restored; 진짜 Gazebo set_pose ACK + Costmap/scan/odom + 공식 ComputePathToPose 결과.
- 실제 `real_amcl_and_tf`: SetInitialPose ACK=true, localization_verified=true, map→base_link TF2 최신 실측, Scan age `0.010298s`, Odom age `0.000179s`.
- 이 CI 성공 경로에서는 `scan_first_gap_over_500ms=null`, `odom_first_gap_over_500ms=null`. 즉 **현장의 0.819/0.752s 최초 공백을 그대로 실제 L2 재현한 것이 아니다**. 해당 오류 복구 로직은 RED→GREEN **L0 범위**, 실제 Nav2 경로와 인접 센서는 정상 스트림 **L2 범위**로 분리한다.
- 실제 Nav2 evidence artifact ID `14412530104`: https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44269396804/artifacts/14412530104
- artifact ZIP SHA256 `ef30d8254eec91bdb608e53356bee3d799b268a7b8965edb4523be24acef260a`, 내부 `SHA256SUMS` **11/11 OK**. 이는 공개 CI 원본이지 개인 WSL2 원본이 아니다.

## 5. 리뷰 결과와 남은 한 단계

- **최초 실제 위반**(819ms/752ms)은 증거로 남긴다. 500ms 상한 완화, 주행 안전 TTL 우회, fake map TF, synthetic Scan/Odom, 별도 Nav2 엔진은 추가하지 않았다.
- 상호 영향 범위: 실제 AMCL–TF–Scan/Odom–Clock 및 Path를 연동 검증했다. CM/Guard **이동 중 L3 안전 TTL**은 이번 D08 NO_GOAL 시연 범위가 아니므로 PASS 주장 금지.
- 이전 동일 SHA의 성공은 보존. 불필요한 Task01~03 재시험 및 Main 자동 병합 금지.
- 공개 Ubuntu/Gazebo L2와 WSL2/WSLg Intel D3D12 GPU 렌더링은 동등하지 않다. **현장 WSL2 L3 재검증을 완료하기 전에는 D08_OWNER_GUI_L3=HOLD**. 반복 실패 시 추가 현장 재실행보다 최초 Scan/Odom/Clock 원시 수신 타임라인을 공개 CI 최소 회귀로 편입해야 한다.
- 인증된 E-Stop 아님, Moving Goal/Control 미발행, 개인정보 포함 원본 증거는 로컬에만 저장.

## 6. 강사용 정확한 고정 SHA 다운로드·단일 실행 (WSL2)

**이번 수정본의 출고 후보는 CI GREEN을 얻은 아래 `a4db...` SHA 하나**다. `main`이나 임의 최신 HEAD를 사용하지 않는다.

```bash
(
  set -Eeuo pipefail
  SHA='a4dbb714f74d31ac410b1504f2b5087df3a4ec64'
  SCRIPT="$(mktemp --suffix=.sh)"
  trap 'rm -f -- "$SCRIPT"' EXIT

  curl -fLsS --retry 3 --max-time 90 \
    "https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public/$SHA/d08/scripts/d08_owner_no_goal_bootstrap.sh" \
    -o "$SCRIPT"
  bash -n "$SCRIPT"
  export AXIA_D08_PUBLIC_SHA="$SHA"
  bash "$SCRIPT" --self-check
  bash "$SCRIPT" --run
)
```

진짜 Gazebo GUI와 RViz는 Owner 실행기에서 동시 구동되며, 교육용 live loop는 Ctrl+C로 종료한다. 실제 ROS/Gazebo 센서가 처음 0.5초를 초과하더라도 자동 허용이 아니라 **실제 1초 연속 수신 회복 확인**이 필요하다.

기대 출력(아직 해당 Owner SHA의 실측이 아님):

```text
D08_OWNER_EXACT_SOURCE_SHA_VERIFIED=a4dbb714f74d31ac410b1504f2b5087df3a4ec64
D08_AMCL_REAL_FIRST_POSE_PLUS_LIVE_TF_READY
D08_OFFICIAL_SAME_WORLD_THREE_PHASE_PATHS_L2_PASS_NO_GOAL
D08_OWNER_GUI_REPLAN_LOOP_READY Ctrl+C TO_STOP
```

수신 공백이 회복되지 않으면 `D08_NO_GOAL_RX_NOT_STABLE`를 포함한 BLOCKED가 정상 fail-closed 결과다. 현장 원본 archive + SHA256과 실제 화면을 확인한 후에만 L3 GUI 합격을 검토한다.

```text
D08_PUBLIC_OFFICIAL_NAV2_L2=PASS_SCOPED
D08_OWNER_WSLG_REAL_GUI_L3=HOLD
AXIA_MVP_DEMO_ACCEPTED=HOLD
CERTIFIED_ESTOP=false
MAIN_MERGED=false
```
