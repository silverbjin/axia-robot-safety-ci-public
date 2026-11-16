# AXIA G07 Cycle36 — 최초 안전 타이밍 위반 분석, CPU 격리 GREEN, Owner WSL2 최종 인계

기록일: 2026-11-16 (KST)  
상태: **PUBLIC_REAL_GAZEBO_L2_PASS / OWNER_WSL2_NOT_RUN / AXIA_MVP_DEMO_ACCEPTED=HOLD**  
목표: 공식 ROS 2 Jazzy / Gazebo Harmonic / Nav2 / TurtleBot3 Waffle 재사용, G07 교육용 물리 원통 장애물 CLEAR→SLOW→STOP 시연. **SW 정지는 인증 E-Stop 아님.**

## 1. 정확한 소스·브랜치·원격 SHA

| 소스 | 고정 커밋 | 역할 |
|---|---|---|
| Instructor private `silverbjin/axia-robot-safety-instructor` | `2b59c1a74513ac5a5b80c5bd424001a625c07617` (tree `5e0a464e97a9d3104303052e2bfaa68f8f0bb1ec`) | 기존 공식 Nav2 + 정확한 owned CM/GUI/Gazebo 서버 CPU 역할·Goal/STOP/증거 |
| Private 개발 브랜치 | `fix/g07-cycle36-integrated-gui-restoration-20261116` | main 미병합 |
| Public D06 visual | `132d8c64def534061d3467f3e1a339fbb44e3e68` (tree `e285470ef153202fcc7b3e178a0720249bd12870`) | 외부 RViz·Marker read-only Sidecar, integrated Gazebo GUI 중복 방지 |
| Public 실제 L2 workflow | `8bacc46801d7150bb35e3d0f6656afbe91c2ff9d` | 실제 Xvfb GUI·Gazebo·Nav2 한 Goal 재현 |
| Public Owner read-only 판정기 | `3e9343066625605a09fb9edf2e14132c410ae5cb` (tree `3b39b48a501079cb85368637526ce9ac9af5a3b0`) | Owner 원본의 7채널 및 네이티브 RMW source/receive 120ms 필수 증명 |
| Public Owner 다운로드 스크립트 | `a1f7b338b9ee05d15c84d39cb52c3549ff436cd6` | 단일 수동 TTY Goal/원본 custody/HOLD |
| Public 작업 브랜치 | `release/p2-g06-cm-ttl-20261110` | main과 별개. 이 브랜치의 HEAD가 바뀌어도 위 정확한 커밋으로 원샷 다운로드 |

**main 병합 수행하지 않음.** 비공개 강사 원본·학생 정답은 공개하지 않으며, 공개 CI는 실행 계약과 수치 요약만 취급한다.

## 2. RED: 실패를 마지막 RuntimeError 대신 최초 경계에서 확인

직전 실제 CI **Run [43855652408](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43855652408)**, private `4954d43737d5e6575abef97d8669b48790825039`:

- 실제 CLEAR/SLOW/STOP, GUI World/Waffle, Marker Scan 구간은 관찰됨.
- 실제 CM RMW source **120ms 초과 첫 공백 미발견**. 그러나 ROS Observer 7채널 전부 거의 동시에 멈춤:
  - Clock 346.42ms, CM 364.26ms, Guard 364.54ms
  - Odom 340.69ms, Scan 346.64ms, Source 364.39ms, Supervisor 364.43ms
  - 최초 타이밍 위반: **Odom 340.69ms** (`206.941960365 → 207.282651388` host monotonic)
- 정확한 CPU readback: **CM {1,2}, Gazebo 서버 {0,3}, Goal Observer {0,3}, GUI {0} nice19**. CM을 보호하려다 시뮬레이터 물리 서버와 Observer가 같은 두 코어에서 직접 경쟁할 수 있었음.
- 최초 Guard latch는 관찰되지 않았으나 안전 전달 주기 Oracle FAIL. 마지막 `ACTUAL_MOVING_GOAL_CI_ORACLE...` 문자열만으로 CM 자체의 150ms 전달 위반을 단정하지 않는다.
- 판정: **L2 FAIL / 원인 가설=Gazebo 물리 서버와 Observer CPU 충돌**. 단일 실행으로 내부 스케줄러 인과가 확정된 것은 아님.

## 3. GREEN: 시연에 필요한 최소 CPU 역할 분리

변경은 비공개 Instructor의 다음 두 파일뿐:
- `tools/p4_g07_sim_server_cm_core_separation.py`
- `tests/unit/test_g07_cycle36_sim_server_cm_cpu_separation_20261116.py`

4코어 CI: GUI(낮은 우선순위) CPU0, **Goal Observer 기존 {0,3}**, CM 기존 {1,2}, Gazebo 물리 서버만 **{3}**으로 제한. 8코어 후보에서는 CM {1,6}, 물리 서버 {2,3,4,5,7}로 CPU0만 추가 보호. 공식 Nav2/CM/Guard/CM 감속비율/Guard 150ms TTL/Scan 300ms TTL/수동 Goal 승인 **변경 없음**.

- **공개 L0 RED Run [43863165468](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43863165468)**: 기존 서버 CPU {0,3}과 새 예상 {3} 불일치로 실패.
- **공개 L0 GREEN Run [43863326328](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43863326328)**: 정확한 비공개 소스 `2b59c1a...`의 단위·셸 계약 PASS. **NO_ROS_NO_GOAL**.

## 4. 실제 통합 L2 — 같은 SHA에서 모든 필수 층 통과

**Run [43863443121](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43863443121)** = GitHub Actions `completed/success`, source `2b59c1a...`.

- 정확한 owned Gazebo server PID, 30 threads, CPU **{3}** readback; owned CM {1,2}; 공식 통합 GUI CPU0 nice19 (26 threads) readback.
- 실제 Goal EXECUTING: CLEAR LiDAR~2.055m, SLOW~0.747m, STOP~0.377m; CM/Guard 최종 0.
- 실제 Odom 이동 **0.1918m**, STOP 후 0 속도 연속 유지 **1.012s**.
- **7개 호스트 모노토닉 callback 최대 간격**:

| 채널 | 최대 간격 (ms) | 릴리스 목표 |
|---|---:|---|
| Source | 110.549 | <120 |
| Collision Monitor | 99.989 | <120 |
| Guard | 99.946 | <120 |
| Supervisor FSM | 108.369 | <120 |
| Scan | 191.407 | <240 |
| Odom | 111.414 | <240 |
| Clock | 98.777 | <240 |

- Native CM RMW source 최대 **71.34ms**; 관측 창에서 첫 >120ms CM RMW gap 없음. 네이티브 Safety 단독 판정이 아니라 실제 ROS 7채널과 함께 확인.
- S02 native physics witness 같은 Goal UUID `74fe9490da7145dca6f17bfbe0dde182`, **28,828 iteration, contact positive=0**. CI 내 동적 시뮬레이션에 한정, 실제 물체 충돌 안전인증 아님.
- 원본 rosbag에 /clock, /scan, /odom, /cmd_vel_supervised, /cmd_vel_pre_guard, /axia/p2/base_guard 메시지 존재; 전체 14 topic 증거 게이트 PASS.
- 정확한 Goal Cancel ACK(취소 상태), Navigation/Localization lifecycle shutdown ACK, CM exit clean, Gazebo exit 정상; GUI Xvfb 실 창과 Goal 구간 Marker 실제 Scan 25회 관찰.
- 모든 필수 Github Actions job step **success**, `P2_L2_SMOKE_RC=0`. 이전 부분 성공을 다른 SHA로 합산하지 않았다.

**검증 한계:** CI Ubuntu 24.04와 Xvfb의 가상 4코어는 사용자 WSL2/WSLg GPU·스케줄링·커널/DD​​S와 동일한 환경이 아니다. 단일 L2 PASS는 시간 경계가 영구적으로 재현된다는 보증이 아님. WSLg GUI를 눈으로 확인하지 않았다. Owner L3은 **NOT_RUN**.

## 5. Owner WSL2 인수 원샷 공개 CI 계약

Public 스크립트: `scripts/axia_g07_cycle36_owner_once.sh` (immutable commit `a1f7b338b9ee05d15c84d39cb52c3549ff436cd6`). 선행 **공개 L0 Run [43865730514](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43865730514) PASS**:
- `bash -n` 및 `--self-check`
- 비TTY/공개 CI의 본실행은 `CONTROLLING_TTY_REQUIRED`로 차단, **NO_ROS_NO_GOAL**
- 원본 7채널/RMW source·receive/누락·Guard latch/시퀀스 회귀 단위 테스트 4개 PASS
- `--admission-check`: 공개 실제 L2의 정확한 `head_sha + completed success` 라이브 GitHub API 조회
- Instructor private SHA/tree, 공개 Sidecar SHA/tree, 원본 판정기 SHA/tree를 각각 분리하여 고정. 임의 main HEAD 의존 금지

### Owner Ubuntu 24.04 WSL2 터미널 A — 전체 한 번 실행

```bash
(
  set -Eeuo pipefail
  SHA='a1f7b338b9ee05d15c84d39cb52c3549ff436cd6'
  SCRIPT="$(mktemp)"
  trap 'rm -f -- "$SCRIPT"' EXIT
  curl -fL --retry 3 --retry-delay 2 -sS \
    "https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public/$SHA/scripts/axia_g07_cycle36_owner_once.sh" \
    -o "$SCRIPT"
  bash -n "$SCRIPT"
  bash "$SCRIPT" --admission-check
  bash "$SCRIPT"
)
```

전제: `gh auth status`가 private Instructor 접근 가능한 계정, WSLg `DISPLAY`와 ROS Jazzy·Gazebo Harmonic·Nav2·RViz2 설치, Ctrl-TTY 터미널. 실행기가 소스·증거를 고정 확인하고, 로봇 주행 전에 기존 방식으로 `YES-P2-G07-GOAL`을 **직접 입력**받는다. 자동 승인하지 않는다.

성공 후보 출력:
- `AXIA_G07_CYCLE36_REAL_GAZEBO_L2_PROVENANCE_VERIFIED`
- `G07_GUI_READY_ATTESTED_PRE_GOAL mode=owner`
- `P2_L3_G07_NUMERICAL_CANDIDATE` 및 Cancel/Shutdown 감사
- `AXIA_G07_CYCLE36_OWNER_NUMERICAL_CANDIDATE_RAW_REVIEW_REQUIRED`
- `AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false` (정상. 임의 승인 금지)

원본 보관 경로: `~/axia_p2_private_evidence/p2-l3-owner-*/`, `~/axia_g07_cycle36_owner_*/`, `~/.axia_p4_g11_session_custody/`. 정확한 SHA+Run에 대한 **1회 시도 잠금** `~/.axia_g07_cycle36_owner_attempts/`는 삭제하지 않는다. 현장 문제를 발견하면 원본 압축/SHA 보존 후 **해당 최초 실패 경계를 CI 회귀 RED에 먼저 편입**한다.

**최종 상태: 공개 CI 실제 L2 PASS, Owner WSL2 미검증, WSLg 실 시각 검수·원본 Raw review 필요, `AXIA_MVP_DEMO_ACCEPTED=HOLD`. main 병합 보류.**
