# AXIA G07 — Owner WSL2 최종 1회 인수 가이드

> **시연 범위**: ROS 2 Jazzy + Gazebo Harmonic + 공식 TB3 Waffle/Nav2, 실 Gazebo GUI와 read-only RViz2. **소프트웨어 정지는 인증된 하드웨어 E-Stop이 아니다.**

## 선행 검증 (이미 공개 CI 완료)

- P4 기본 실 Gazebo L2 [#43674784552](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43674784552) scoped PASS
- GUI+RViz Xvfb 동시 실 Gazebo L2 [#43685818018](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43685818018) scoped PASS
- Owner 원샷 고정 Release CI [#43686905395](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43686905395) no-ROS/no-Goal PASS
- Private Instructor SHA `db1eec05e01e1db0d0d2e0c05610806ef4e499f9` Tree `005cc352d63067beb9d34397e51b51f7974ce7ef`
- 실제 WSLg Gazebo+RViz/Guard 안전 주기 및 인증: **아직 미검증**

## 실행 방법 — WSL2 Ubuntu 24.04 터미널에서 1회

다음 블록을 한 번에 붙여 넣는다. 스크립트는 공개 GitHub에서 고정 소스를 내려받고 검증한다. 본인의 `gh auth login` 연결 및 Jazzy/Harmonic 설치, WSLg `DISPLAY`는 기존 환경을 사용한다.

```bash
(
  set -Eeuo pipefail
  SHA="91e033a39da2e1295416d2c8d55deb52e10c2469"
  SCRIPT="$(mktemp)"
  trap 'rm -f -- "$SCRIPT"' EXIT

  curl -fL --retry 3 -sS \
    "https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public/${SHA}/scripts/axia_g07_final_owner_wsl2_bootstrap.sh" \
    -o "$SCRIPT"

  bash -n "$SCRIPT"
  bash "$SCRIPT"
)
```

- 실행 전에 **TTY가 있는 실제 WSL2 터미널**과 유효한 비공개 Instructor GitHub 인증이 필요하다.
- 스크립트는 해당 소스가 과거 통과한 CI/고정 Tree와 일치하는지 확인한 뒤에만 실행한다.
- 최종 로봇 Goal은 비공개 원본 P4 실행기가 요구하는 **`YES-P2-G07-GOAL`을 사용자가 직접 입력**해야 실행된다. 스크립트는 이를 자동 입력하지 않는다.
- 일단 시도가 등록되면 재시도가 차단된다. 실패 원인은 공개 CI 회귀 RED→GREEN 후 새 인수에서 처리한다.

## 핵심 출력 판독

| 출력 또는 증거 | 의미 |
|---|---|
| `AXIA_G07_FINAL_PUBLIC_SHA_VERIFIED` | 공개 실행기 SHA 및 Tree 고정 |
| `AXIA_G07_FINAL_OWNER_GATE` / `ADMITTED_ONE_FINAL_WSLG_OWNER_ONLY` | CI 근거로 WSLg 수동 **1회 시도 허가**, Owner PASS 의미 아님 |
| `G07_OWNER_FINAL_SINGLE_ATTEMPT_RESERVED` | 원본 1회 시도 기록, 자동 재시도 불가 |
| `D06_RVIZ_STARTED` | read-only RViz 프로세스 시작, 실제 화면 표시와 주행 안전 별도 |
| `AXIA_G11_G07_JOINED_REVIEW_EXIT_CODE=0` / 원본 RMW 결과 | 기존 P4 원본 정지·안전 데이터 검토 결과 |
| `D06_GUI_OWNER_WRAPPER_RC=0` | wrapper 종료 코드 성공, 원본 및 화면 최종 확인 필요 |
| `UPSTREAM_STALE_AFTER_MOTION`, `HOLD`, `RC!=0` | 최초 Guard/데이터 TTL을 우선 조사; 현장 재실행 중단 |

## 강사가 확인할 화면 및 원본

1. WSLg의 Gazebo GUI에 Waffle과 실 장애물 시연, RViz2에 read-only 경계(비인증 교육용)가 보이는가.
2. 실제 Goal 동안 CLEAR → SLOWDOWN → STOP, Odom 속도 0 유지 ≥1초, Guard latch 없음, 150ms CM/Guard와 300ms Scan/Odom/Clock 한계가 같은 원본 증거에서 확인되는가.
3. P4 원본 14-topic SQLite/해시 보관과 정확한 Goal Cancel ACK, Nav2 Navigation/Localization shutdown ACK 및 CM exit0을 증명하는가.

종료 시 출력되는 `D06_GUI_EVIDENCE` 및 `AXIA_G11_G07_PRIVATE_ORIGINAL` 경로를 보존한다. 공개 GitHub에는 원본 rosbag, 사설 소스, Goal UUID를 업로드하지 않는다. 사용자에게는 원본 증거 아카이브와 Gazebo/RViz 스크린샷을 한 번에 제출하도록 안내한다.

## 합격선

**CI PASS는 인수 준비만 의미한다.** 강사의 최종 WSL2 증거 확인 이전에는 `owner_l3_accepted=false`, `AXIA_MVP_DEMO_ACCEPTED=HOLD`로 유지한다. main 병합에는 별도 사용자 승인이 필요하다.
