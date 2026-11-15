# AXIA G07 — 최종 Owner WSL2 v2 단일 실행 가이드

## 기준
- CI 동일 실행기 실제 Gazebo Harmonic+공식 Nav2+Gazebo GUI/RViz Xvfb: [#43693480829](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43693480829) **PASS_SCOPED** (2026-11-15).
- 소스 Instructor `bc270e28620c1909fcb34669e6036504b5cae951` / Tree `59c35abb651cdce18d3131b28497a500ca692cc2`.
- Public v2 source `8b9e44f4b622210831dd68055dad3efe8a293c92` / Tree `9e33400972463d42627c37a35f02f5a3dcb87be8`.
- 검증된 final Bootstrap Release `e0ecb7abe7a0ddc8beb38f706f5094024e1083c5`; CI [#43694440201](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43694440201) **NO ROS/NO Goal PASS**.

**주의:** 이전의 `91e033a39...` v1 실행기는 과거 P4 SHA를 재사용하므로 다시 실행하지 않는다. 이제 새로운 v2 기준선에서 Owner 1회 최종 인수만 수행한다. 실제 Gazebo/WSLg 시연과 TTY 주행은 사용자가 직접 확인한다.

## 사용자 WSL2 단일 명령
WSL2 Ubuntu 24.04 실제 터미널에서, 기존 Jazzy·Harmonic·Nav2·WSLg 설치와 `gh auth status` 비공개 Instructor 인증이 된 상태로 다음 전체를 한 번에 실행한다.

```bash
(
  set -Eeuo pipefail
  SHA="e0ecb7abe7a0ddc8beb38f706f5094024e1083c5"
  SCRIPT="$(mktemp)"
  trap 'rm -f -- "$SCRIPT"' EXIT

  curl -fL --retry 3 -sS \
    "https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public/${SHA}/scripts/axia_g07_final_owner_v2_wsl2_bootstrap.sh" \
    -o "$SCRIPT"

  bash -n "$SCRIPT"
  bash "$SCRIPT"
)
```

- Bootstrap이 Public source SHA/Tree를 검증하고 새 Owner v2 스크립트로 진입한다.
- 새 Private Instructor 후보 SHA/Tree, CI Run/7채널/ACK/CM exit0 게이트를 확인한다.
- 동일 공통 `gz sim -g`/RViz/Marker 읽기전용 표시를 Nav2 startup 후 시작한다.
- **주행 Goal은 사용자가 TTY에서 `YES-P2-G07-GOAL`을 직접 입력해야 실행**한다. 스크립트가 이 입력을 자동 전송하지 않는다.
- 최초 Guard latch나 safety TTL 위반은 곧바로 실패. CPU/표시 문제로 Goal 전 실패하더라도 자동 재시도하지 않는다. 인증된 E-Stop 기능이 아닌 simulation SW STOP 데모다.

## 출력·원본 확인
| 필수 출력 | 의미 |
|---|---|
| `AXIA_G07_FINAL_PUBLIC_SHA_VERIFIED=8b9e44...` | 새 공용 소스 정확한 커밋/트리 |
| `AXIA_G07_FINAL_PRIVATE_SHA_EXPECTED=bc270e...` | 동일 Instructor 코드 사용 |
| `AXIA_G07_FINAL_OWNER_GATE` / `ADMITTED_ONE_FINAL_WSLG_OWNER_ONLY` | **시도 승인만**; 실제 Owner PASS 아님 |
| `G07_OWNER_FINAL_SINGLE_ATTEMPT_RESERVED` | new v2 SHA/Run 조합 1회 attempt 원장 기록 |
| `G07_GUI_READY_ATTESTED_PRE_GOAL mode=owner` | Goal 이전 GUI 프로세스 준비 계약. WSLg 실화면 품질과 별도 |
| `D06_RVIZ_STARTED` | read-only Marker RViz 실행, 실제 Gazebo GUI와 실시간 시각 확인 필요 |
| `AXIA_G11_G07_JOINED_REVIEW_EXIT_CODE=0` | 기존 원본 custody join 리뷰, 단독 합격 의미 아님 |
| `AXIA_G07_OWNER_SUPPORT_BUNDLE=/home/.../.axia_g07_owner_support/g07-...` | 실패/성공 시 로컬 사설 자료 압축 보관 디렉터리 |
| `D06_GUI_OWNER_WRAPPER_RC=0` | wrapper 종료 코드. 원본 속도·안전 TTL·14-topic·Nav2 shutdown을 별도 검토할 것 |

## 추가 분석 자료 자동 수집
`~/.axia_g07_owner_support/g07-<UTC>-<random>/`이 자동으로 생성된다.

- `support_evidence.tar.gz`: 원본 Owner tar.gz/해시, 중요한 live JSONL·rosbag, GUI sidecar/rviz/gz GUI/관측 로그, G11 custody manifests/reviews.
- `manifest.json`: 수집된 파일별 SHA256/크기, 성공/불완전과 Owner 종료 코드.
- `SHA256SUMS`: 묶음 및 manifest SHA256.

**분석이 필요할 때는 이 디렉터리의 `support_evidence.tar.gz`와 `manifest.json` 및 `SHA256SUMS`를 함께 제공한다.** 원본 ROS 로그와 private Goal UUID 등을 공개 GitHub/학생 저장소에 올리지 않는다. 자동 업로드는 하지 않는다.

## 인수 기준
사용자 WSLg의 두 창을 육안으로 확인하고, 실제 주행 CLEAR→SLOWDOWN→STOP, Odom 0속도 ≥1초, no Guard latch, 7채널/CM RMW 주기, Nav2 CancelGoal ACK 및 Navigation/Localization 종료 ACK, CM exit0, S02 contact0, 14-topic rosbag 원본 증거가 **한 Goal**에 귀속하는지 검토한다.

CI L2와 NO-Goal static CI의 PASS는 Owner 준비만 뜻한다. 실제 WSL2 미실행 현재 `AXIA_MVP_DEMO_ACCEPTED=HOLD`, 인증된 E-Stop 주장 없음, main 병합 금지.
