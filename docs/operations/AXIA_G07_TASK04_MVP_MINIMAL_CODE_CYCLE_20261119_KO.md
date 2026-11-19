# AXIA G07 Task04 — MVP 최소 수정 구현 사이클 (2026-11-19)

## 판정 시점

**코드 커밋 완료 / 공개 CI L0 GREEN / 실제 Gazebo L2 SCOPED PASS / Owner 원샷 Bootstrap L0 PASS / 강사 WSL2 L3 미실행(HOLD).** 형식적 인증 E-Stop과 현장 L3는 별도입니다.

## 기준 증거

강사 `owner-moving-KwcTfR01` 원본: 실제 CLEAR/SLOW/STOP과 약 1.028초 Odometry ZERO, 전진 0.085359m. 첫 `/scan` 공백 402.019ms (300ms 기준 위반); `/safety/scan` 약 396.857ms. 동일 구간 Odometry/Clock 정상. 장애물 SLOW 위치 전환과 시간상 겹치지만 `set_pose` CLI가 공백의 직접 원인이라고 단정하지 않는다.

이전 정상 기능: 공식 Nav2 Goal 전송, TB3 Waffle 이동, 기존 Collision Monitor 30% 감속 및 물리 STOP. 이 기능의 알고리즘·기존 Goal·CM 설정·Safety TTL은 변경하지 않는다.

## 실제 RED → GREEN → REFACTOR → REVIEW → COMMIT

| 단계 | 실행/출력 | 결과 |
|---|---|---|
| RED 작성 | Student SHA `bb54245a8a57b01452ee4c950db0ec6f1afc8b22`, `tools/test_g07_task04_mvp_minimal_fix.py` | 신규 3개 회귀 경계 |
| RED 공개 CI | [#44477264332](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44477264332) | `Ran 3 tests ... FAILED (failures=2, errors=1)`, Gazebo SKIPPED (의도된 RED) |
| 첫 GREEN | Student SHA `d086cc419fde7328f4c54e314a4e5ac8a52e22f3` | 새 회귀는 PASS, 기존 Owner AST 계약 1건 FAIL |
| 첫 GREEN CI | [#44477731546](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44477731546) | 기존 `test_owner_uses_same_exact_goal_cancel_after_stop` 실패로 Gazebo SKIPPED |
| REFACTOR | Student `28d24c0256ab00f98f113720650c384a2b180760` | 정상/예외 경로간 정확 UUID 취소 시도 최대 한 번 |
| REVIEW 계약 | Student `954fc2f054c50df783bc81c4d0835a6ee6f8645d` | 기존 Owner 계약을 정상 취소 및 예외 취소 **상호 배타**로 수정 |
| 공개 CI 재검증 | Public SHA `c362738794ccbd40b21a90b4e6e3409fa9f90892`, [#44478344652](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44478344652) | **SUCCESS**: `AXIA_G07_TASK04_NATIVE_ONE_MOVING_RUNNER_RC=0 RVIZ_X11=1 GAZEBO_X11=1`, `status=TASK04_REAL_GAZEBO_MOVING_GUI_L2_SCOPED_PASS`, `first_failure=NONE`. 실제 Gazebo·RViz·Goal·Scan/CM/Guard·Stop/Cancel·정상 종료 시나리오 Scoped L2 증거 |

## 최소 변경 파일

Student `fix/g07-task03-public-proof-20261118`:

- `block_B/day07/h01_runtime/tools/p2_g07_ci_moving_goal.py`: 실제 Odom 0.12m 주행·신선한 Scan/Guard/ActionStatus 후 SLOW 기존 `move_ci_verified`; SLOW 서비스 시작·ACK 단조시계 기록; STOP + 1초 ZERO 후 **타이밍 오라클 이전** 정확한 기존 UUID CancelGoal; 예외 상황에서 활성·비래치·미시도 Goal만 1회 취소하고 첫 오류 보존.
- `block_B/day07/h01_runtime/tools/test_g07_task04_mvp_minimal_fix.py`: 3건 최소 RED 회귀.
- `block_B/day07/h01_runtime/tools/test_g07_task04_owner_moving_entry.py`: 실제 최대 1회의 정상/예외 취소 코드 계약.

Public CI `fix/g07-task04-owner-wsl2-public-pregate-20261118`:

- `.github/workflows/axia-g07-task04-owner-moving-native-l2-20261118.yml`: 정확한 Student SHA 핀, 원래의 Nav2·Gazebo·GUI·실물 Scan/CM/Guard 검사 1회.
- 정식 L2 보고서·다른 안전 계층 수정 없음.

## 현장 및 출고 지침

- Owner 원샷 `scripts/axia_g07_task04_owner_moving_l3_once.sh`는 실제 Gazebo L2 성공 후 Student `954fc2f054c50df783bc81c4d0835a6ee6f8645d`, CI Run `44478344652`, 기존 read-only reviewer `d60beed5e18d8104b254f17476d47f1d1917a7eb`를 정확히 핀했습니다.
- 원샷 소스 커밋 `2415be83fef52a15fd5fe8c3635463931df6d0b6`; 공개 Bootstrap 테스트 수정 `3f0e1310fa42594bf2d3c021370dad82581214d8`, [#44480154746](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44480154746) **9/9 PASS + bash -n PASS**. 원샷 배포 고정 공개 SHA `3f0e1310fa42594bf2d3c021370dad82581214d8`.
- 공개 Gazebo L2와 Bootstrap L0가 PASS했으므로 강사 WSL2에서 동일 원샷을 한 번 실행할 차례입니다. 단, 실제 WSL2 터미널은 이 연결 도구에서 실행할 수 없으므로 원격으로 L3 PASS를 주장하지 않습니다. 실제 수동 Goal 승인 `YES-P2-G07-GOAL`은 강사가 직접 입력합니다.
- CI L2 검증됨: 동일 세션 실제 Gazebo, 두 GUI 창, 정확한 소스 SHA, native Moving Goal reviewer `first_failure=NONE` 및 `status=TASK04_REAL_GAZEBO_MOVING_GUI_L2_SCOPED_PASS`. CI 숫자 아티팩트 [#14508665070](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44478344652/artifacts/14508665070)를 보존합니다.
- 미검증: **강사 WSL2/WSLg L3 실제 GUI 시연과 현장 Scan TTL**. 공개 Xvfb L2 성공이 강사 GPU/WSLg에서의 동일 성능을 증명하지는 않음. `AXIA_MVP_DEMO_ACCEPTED=HOLD` `CERTIFIED_ESTOP=false`.
- `main` 병합하지 않음. 정식 E-Stop과 시뮬레이션 SW 정지를 혼동하지 않음.


## 강사 WSL2 Ubuntu 24.04 — 단일 현장 실행 (최종 L3 미인수)

아래는 공개 Owner Bootstrap **9/9 PASS**가 확인된 불변 SHA의 GitHub 스크립트입니다. WSL2 Ubuntu 터미널에 한 번 붙여 넣으십시오.

```bash
(
  set -Eeuo pipefail
  PIN='3f0e1310fa42594bf2d3c021370dad82581214d8'
  SCRIPT="$(mktemp --suffix=.sh)"
  trap 'rm -f "$SCRIPT"' EXIT
  curl -fL --retry 3 --max-time 90 \
    "https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public/$PIN/scripts/axia_g07_task04_owner_moving_l3_once.sh" \
    -o "$SCRIPT"
  bash -n "$SCRIPT"
  bash "$SCRIPT" --self-check
  bash "$SCRIPT" --run
)
```

- Goal 발행 전 한 번 `YES-P2-G07-GOAL` 수동 입력.
- Gazebo·RViz에 로봇 이동→SLOW→STOP 관측, 터미널 `AXIA_G07_TASK03_EXACT_GOAL_UUID_CANCELED_NATIVE_ACTION_PASS` 또는 Owner 수치 후보 메시지 확인.
- 출력 `AXIA_G07_TASK04_DIAGNOSTIC_ZIP` 및 `AXIA_G07_TASK04_DIAGNOSTIC_SHA256` 파일만 재전달하십시오. 전체 원본 TAR/rosbag은 WSL2에 보존.
- 새 오류 발생 시 동일 현장 재시도 반복하지 않음. 최초 `first_failure`와 최초 안전 TTL 위반을 분석하고 재현 가능한 오류는 공개 CI 회귀에 넣습니다.
- 현장 화면/숫자 검수 전 `AXIA_G07_TASK04_OWNER_MOVING_L3=HOLD`, `AXIA_MVP_DEMO_ACCEPTED=HOLD`, `CERTIFIED_ESTOP=false`.
