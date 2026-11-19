# AXIA G07 Task04 — MVP 최소 수정 구현 사이클 (2026-11-19)

## 판정 시점

**코드 커밋 완료 / 공개 CI L0 GREEN / 실제 Gazebo L2 진행 중 / 강사 WSL2 L3 미실행(HOLD).** 이 보고서는 미완성 상태를 PASS로 승격하지 않는다. CI가 종료된 경우 별도 최종 결과를 추가 커밋한다.

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
| 공개 CI 재검증 | Public SHA `c362738794ccbd40b21a90b4e6e3409fa9f90892`, [#44478344652](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44478344652) | 신규/기존 L0 계약 GREEN, CI 이미지 정합성 GREEN; Gazebo 네이티브 플러그인 준비 단계 진행 중, **L2 PASS 주장 금지** |

## 최소 변경 파일

Student `fix/g07-task03-public-proof-20261118`:

- `block_B/day07/h01_runtime/tools/p2_g07_ci_moving_goal.py`: 실제 Odom 0.12m 주행·신선한 Scan/Guard/ActionStatus 후 SLOW 기존 `move_ci_verified`; SLOW 서비스 시작·ACK 단조시계 기록; STOP + 1초 ZERO 후 **타이밍 오라클 이전** 정확한 기존 UUID CancelGoal; 예외 상황에서 활성·비래치·미시도 Goal만 1회 취소하고 첫 오류 보존.
- `block_B/day07/h01_runtime/tools/test_g07_task04_mvp_minimal_fix.py`: 3건 최소 RED 회귀.
- `block_B/day07/h01_runtime/tools/test_g07_task04_owner_moving_entry.py`: 실제 최대 1회의 정상/예외 취소 코드 계약.

Public CI `fix/g07-task04-owner-wsl2-public-pregate-20261118`:

- `.github/workflows/axia-g07-task04-owner-moving-native-l2-20261118.yml`: 정확한 Student SHA 핀, 원래의 Nav2·Gazebo·GUI·실물 Scan/CM/Guard 검사 1회.
- 정식 L2 보고서·다른 안전 계층 수정 없음.

## 현장 및 출고 지침

- 기존 Owner 원샷 `scripts/axia_g07_task04_owner_moving_l3_once.sh`는 **이전** Student SHA `2ca257c80fa12f35d801ca525cb16bebbaaa0c8f`에 고정되어 있어 신규 코드를 실행하지 않는다.
- 새로운 Owner pin 갱신 요청은 GitHub 쓰기 안전 검사에서 차단되었으므로 **출고하지 않는다**. 이 제한을 우회하여 우발적으로 미검증 코드를 WSL2에서 실행하지 않는다.
- 실제 Gazebo L2가 성공하고 새로운 고정 SHA Owner 원샷 및 공개 Bootstrap L0를 검증한 경우에만 강사 WSL2에서 한 번 수동 Goal 승인 `YES-P2-G07-GOAL` 후 실행한다.
- 미검증: 신규 코드의 실제 Gazebo CLEAR 0.12m, SLOW/STOP 수치, 300ms Scan TTL, 정확 UUID 취소, Localization 종료, 강사 WSL2 L3, GUI 실제 화면. `AXIA_MVP_DEMO_ACCEPTED=HOLD` `CERTIFIED_ESTOP=false`.
- `main` 병합하지 않음. 정식 E-Stop과 시뮬레이션 SW 정지를 혼동하지 않음.
