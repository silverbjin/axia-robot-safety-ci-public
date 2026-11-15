# AXIA G07 Cycle 17 — 실제 L2 성공 SHA 기반 Owner WSL2 1회 원샷 준비

- 작성일: 2026-11-16
- **결론: RELEASE_PACKAGE_READY_FOR_ONE_OWNER_WSL2_TRIAL; 실제 WSLg/Owner L3 NOT_RUN, `AXIA_MVP_DEMO_ACCEPTED=HOLD`.**
- 범위: ROS 2 Jazzy, Gazebo Harmonic, 공식 Nav2, TB3 Waffle, G07 simulation-only.
- 비공개 Instructor SHA: `01d45d46b6eb6a05b1bd313d73f1fc3549575545`; Git tree `38de92dda3c17221b337f140bbc1b2aecd805da4`
- 실제 Gazebo GUI/RViz L2: 공개 Actions Run [43727149856](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43727149856), public workflow SHA `fa05a437db3b55d3e5e242322a4b66b7f71ae601`, conclusion `success`.
- 기존 공개 소스·뷰어 `d06/scripts/g07_shared_gui_clients.sh` Git blob `5962cefbe5cb771c09873ae0ae139948b37ae81b`는 실제 L2에서 사용한 `70f9d4ece5c405cff0fb2d17843391856f3d8c08`과 이번 Owner 릴리스의 것과 **byte-identical**.
- **Owner가 GitHub에서 받아 사용하는 불변 공개 release:** `dd425003b9a8c6891330744f33330f6a206eb2e8`; tree `bdf887e169127f3ebb704aef885cacd926d3b554`. Bootstrap은 공개 `release/g07-cycle16-owner-wsl2-20261116`의 커밋 `09f856a42c97783b0f376ed57900ee673dc79fd3`부터 제공.
- `main` 미병합, instructor 정답/ROS 원본/Goal raw 비공개, 학생 TODO 분리.

## 1. 기준선 재사용 (성공 재실행 없음)

Cycle16 실제 한 Goal + Gazebo physics/official Nav2/WSLg가 아닌 Xvfb GUI L2 Run `43727149856`: CLEAR `2.03965m`, SLOWDOWN `0.73865m`, STOP `0.38667m`; Native STOP `0.102232s`; 실제 pre-STOP CM age `0.536519ms`; Odom stop dwell >=1.0s. 정확 UUID `b0e0f442c3e44cee94799b530caa4a8b` CANCELED, navigation/localization shutdown ACK, CM exit0, S02 native contact 0.
실제 7채널 최대 interarrival(ms): source `67.902004`, supervisor `67.303836`, CM `110.964002`, Guard `51.892001`, Scan `199.431146`, Odom `134.078028`, Clock `103.039317`. **CM 150ms HARD와 독립 출고 여유 목표 120ms 모두 충족.** 이것은 Owner WSLg 시연의 검증이 아님.

## 2. RED→GREEN→REFACTOR→REVIEW→COMMIT

추가 안전제어 개발 없음. 첫 공개 Owner v2는 `bc270e...` 실패한 출고에 고정돼 있고 Owner 홈의 잠금 `~/.axia_g07_final_owner_attempts/bc270e...-43693480829`이 보존된다는 점에서, **기존 lock을 삭제하지 않는 새 버전**만 작성.

- RED `d06/tests/test_g07_cycle16_owner_release_v4.py` (처음 구현 파일 부재): [Run 43767630969](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43767630969) FAIL.
- GREEN `d06/live/g07_cycle16_owner_ci_gate_v4.py`: immutable CI Run/HEAD/private SHA/tree, 7채널 120/240ms 출고 여유, Guard 최초 latch 없음, S02 native contacts=0, 14topic bag/Goal canceled/ordered shutdown/CM exit0를 모두 엄격하게 재검증하는 **no-ROS/no-Goal** 불변 데이터 검증기. 실제 GitHub Actions API `status=completed`, `conclusion=success`, `head_sha` 고정 여부를 WSL2 wrapper에서 다시 조회.
- `scripts/axia_g07_cycle16_p4_owner_once.sh`: 기존 검증된 P4/G11 개인 원본 custody 및 소스 검증·동일 private `p2_owner_l3_wsl2.sh --case G07 --mvp-relocated-obstacle` 재사용, 강사 TTY 동의를 자동 입력하지 않음. Goal·CM/Guard TTL·Nav2 소스 불변. `LOCALIZATION_START`과 `NAVIGATION_START` 최초 실패를 모두 인식.
- `d06/scripts/g07_cycle16_owner_wsl2_once.sh`: 공개 같은 GUI sidecar/RViz/Gazebo 클라이언트, 원본 bundle, 최초 Guard/CM 분석기 재사용. 이전 Owner 원본과 이전 실패 lock 삭제 없음. `~/.axia_g07_final_owner_attempts/<newSHA>-43727149856`을 **원자적 mkdir 1회**로 기록하며 동일 출고 재주행 자동 차단. 종료 후에도 실제 Owner 7채널 120/240ms를 추가 확인; 미확인 시 HOLD.
- `scripts/axia_g07_cycle16_owner_wsl2_bootstrap.sh`: public release SHA 및 tree 재검증, ROS 시작 전 CI gate 검사, 반드시 물리 터미널에서 수동 `YES-P2-G07-GOAL` 동의를 받는 기존 private runner 호출.
- Public workflow `.github/workflows/axia-g07-cycle16-owner-release-l0.yml`: 공개 L0 no ROS/no Goal; 누락·변조된 CI gate, 잘못된 SHA/원본, 120ms 경계 초과, 과거 재시도 기록 삭제/자동 동의, bootstrap 출고 SHA/tree 및 $HOME 부작용을 7개 테스트로 점검.
- [최종 공개 Owner L0 Run 43768317778](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43768317778) **success**. 실제 로그: `Ran 7 tests in 0.116s`; `AXIA_G07_CYCLE16_OWNER_RELEASE_PUBLIC_L0_PASS_NO_ROS_NO_GOAL_OWNER_L3_NOT_RUN`. 세 shell 스크립트 bash syntax PASS.

## 3. Owner WSL2 최종 인수 원샷 — 실제 실행은 아직 하지 않음

WSL2 Ubuntu 24.04 터미널, ROS Jazzy + Harmonic + WSLg, `gh auth login` 완료 상태에서 다음 **한 번만** 실행한다. Bash 다운로드 SHA `09f856a42c97783b0f376ed57900ee673dc79fd3`을 반드시 그대로 사용한다:

```bash
(
  set -Eeuo pipefail
  SHA="09f856a42c97783b0f376ed57900ee673dc79fd3"
  FILE="$(mktemp)"
  trap 'rm -f -- "$FILE"' EXIT
  curl -fL --retry 3 -sS \
    "https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public/${SHA}/scripts/axia_g07_cycle16_owner_wsl2_bootstrap.sh" \
    -o "$FILE"
  bash -n "$FILE"
  bash "$FILE"
)
```

- 정상 **출고 적격** 초반 메시지: `AXIA_G07_CYCLE16_CI_REAL_GUI_L2_PASS_RUN=43727149856`, `AXIA_G07_CYCLE16_REAL_GUI_L2_CI_RUN_SUCCESS_VERIFIED_NO_GOAL`, `G07_OWNER_FINAL_SINGLE_ATTEMPT_RESERVED`. 이 메시지 자체는 움직임/Owner 성공 보증이 아니다.
- 최종 정상 숫자 후보: `AXIA_G07_CYCLE16_OWNER_120MS_7_CHANNEL_NUMERICAL_CANDIDATE_RAW_REVIEW_REQUIRED`. 이후 `AXIA_MVP_DEMO_ACCEPTED=HOLD` 출력은 **설계된 기본값**, 원본 검토 전 자동 `ACCEPTED` 없음.
- 첫 Guard latch, TTL 위반, 노드 종료 ACK, WSLg 실패, 원본/rosbag 무결성 문제는 첫 실패로 보존. 같은 잠금의 재실행은 `AXIA_G07_FINAL_OWNER_REPEAT_BLOCKED`; 현장 반복 재시도 대신 최초 실패를 공개 CI RED→GREEN 회귀에 반영.
- 예상 원본: `~/axia_p2_private_evidence/p2-l3-owner-*/G07/`, `~/axia_d06_gazebo_rviz_owner_*/`, `~/.axia_g07_owner_support/`, G11 session custody. 공개 업로드 금지.

## 4. 검증 수준·미검증·남은 인수

1. 완료: Instructor 정확 SHA sealed L0 42개, 공개 CI 실제 Gazebo GUI/RViz L2 한 Goal PASS, 별도 공개 Owner 출고 L0 7개 PASS.
2. 미검증: 실제 강사 WSL2에서 이번 SHA의 WSLg Gazebo/RViz 시작, Nav2 단일 Goal, Node 간 데이터 경계/CM release margin, 실제 종료/원본 custody. 실제 WSL2 실행하지 않고 Owner PASS라고 보고하지 않음.
3. 이 성공은 **소프트웨어 시뮬레이션 STOP**이며 인증된 물리 E-Stop이 아니다. 재현 시 현장 단발 후보에 대해 첫 실패/타이밍을 확인하고 **추가 계층 회귀 미확인 시 전체 시연 안정성 미검증**.
4. `main` 병합은 사용자 별도 승인 전 금지.
