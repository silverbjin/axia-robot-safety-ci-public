# AXIA G07 Cycle 27 — 첫 120ms CM 원본 발행 공백과 Native STOP RPC 실제 L2 관계

- 날짜: 2026-11-16
- 공개 브랜치: `fix/g07-cycle27-first120-rpc-classifier-20261116`
- 상태: **L0 GREEN 10/10, 실제 Gazebo L2 FAIL, Owner WSL2 NOT_RUN, AXIA_MVP_DEMO_ACCEPTED=HOLD**.
- 안전: Guard CM hard TTL **150ms**, CM 출고 목표 **120ms** 그대로. 이번 작업은 읽기 전용 진단뿐; 공식 Nav2, Guard, CM, Supervisor, E-Stop 의미를 변경하지 않음.
- private Instructor 기준 SHA: `57b553b1b9a8cdfa68de0d5a58a20881bac99478`. 현장 원본 G11 보존, 다른 private solution 공개 금지.

## 1. 왜 이 사이클이 필요했는가

기존 CI 및 Owner 현장 원본에서 RMW CM source gap 120~150ms가 반복됐다. 기존 native STOP RPC 진단은 150ms 이상만 보았으므로 실제 인수 준비를 막는 **120ms 출고 초과**의 시간 원인을 분류하지 못했다. 기존 WSL2 현장 첫 186.714207ms source gap은 Native STOP RPC **종료 후 435.347732ms**로, RPC 직접 중첩 없었음. 반면 최근 CI는 140ms gap이 반복돼 같은 가설을 유효하게 검사할 필요가 있었다.

## 2. RED→GREEN→REFACTOR→REVIEW→COMMIT

- 새 순수 분석기 `d06/live/g07_cycle27_first120_rpc_relation.py`: 원본 ROS Observer JSONL의 CM RMW source/receive/publication sequence와 upstream Supervisor 발행, native STOP RPC monotonic 시각. SYSTEM RMW source는 같은 시계끼리 차이만, callback/RPC는 host MONOTONIC끼리만 비교. 출력은 숫자 및 판정 JSON만, 원본 Goal UUID·bag 비공개.
- 원본 단위 회귀 `d06/tests/test_g07_cycle27_first_120ms_rpc_relation.py`.
- 처음 RED [43803144865](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43803144865) 신설 모듈 없음.
- GREEN [43803276791](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43803276791): 7개 L0 PASS.
- 첫 실제 L2 [43803407128](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43803407128): Goal 실물 시뮬레이션 CLEAR/SLOW/STOP·CM source **136.532700ms**, Observer **138.311126ms**, CM 120ms 출고 FAIL. 진단기에 Goal 시작 전/종료 후 RMW metadata가 혼재하여 `RMW_METADATA_MISSING_OR_INVALID_HOLD` 반환, 이를 원인으로 오분류하지 않음.
- 추가 RED [43804026468](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43804026468): Goal 시작 전과 종료 후 metadata 필터 및 **private 원본 Goal 구간의 기존 `cm_first_120ms_rmw_release_margin` 값과 숫자가 정확하게 일치**해야 한다는 시험.
- 추가 GREEN [43804220000](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43804220000): **10개 L0 PASS**, 원본 유효 목표 구간의 120ms first gap 판별을 CI 및 사용자 스크립트와 동일 구현으로 검증.
- 두 번째 실제 L2 [43804314391](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43804314391): 실제 Gazebo Harmonic / TB3 Waffle / 공식 Nav2 Goal 중 CLEAR→SLOW→물리 STOP 관찰, **이후 최초 CM 원본 gap 163.532665ms, Observer callback gap 178.395157ms, Guard hard/120ms margin 모두 FAIL**. G07 actual CI runner는 `ACTUAL_MOVING_GOAL_CI_ORACLE_SAFETY_DELIVERY_TTL_BOUNDARY_max_cm_interval_sec`로 안전하게 차단함. Native gz STOP RPC duration **155.148057ms**, 첫 CM gap과 **monotonic 관측 구간 중첩 TRUE**, upstream Supervisor RMW 원본 3개(최대 발행 gap 50.73089ms), CM publication sequence delta 1.
- 새 진단 출력 `AXIA_G07_CYCLE27_FIRST_CM_120MS_SOURCE_RPC`: `status=CM_SOURCE_120MS_GAP_OVERLAPS_RPC_HOLD`, `scoped_original_oracle_gap_matched=true`, `skipped_pregoal_rows=68`, `skipped_incomplete_rmw_rows=0`, `rpc_caused_cm_gap_proven=false`.
- 최초 CM gap 주변 read-only /proc CM scheduler: sampling span 104.282ms, run 2.698ms, wait 23.626ms, thread count 16. **CM 내부 TF lookup과 input subscriber callback 직접 관측한 것은 아님**, CPU 스케줄러 원인도 입증되지 않음.
- 후속 RCL `context not valid` 예외는 Gate 차단 이후 launcher cleanup에서 발생했으므로 **첫 실패 원인 아님**.

## 3. 확정된 사실과 미확정 원인

1. 이번 실제 CI run의 첫 163.533ms CM source gap과 Native STOP RPC의 monotonic window는 겹쳤다. 단순 시간 중첩이지 원인 입증이 아니다.
2. 과거 Owner WSL2 186.714ms 첫 gap은 STOP RPC 435.348ms **이후**이므로 RPC만 고쳐도 현장 전체 문제가 해결됐다고 판단할 수 없다.
3. CM output source gap 동안 Supervisor는 계속 발행했고, 같은 publication sequence 검증상 CM 자체의 연속 출력 공백이다.
4. Ubuntu 24.04 Jazzy/Harmonic 권장 조합은 문제 자체가 아니며, 4-core CI Xvfb와 8-core Owner WSLg의 스케줄러·GPU 차이는 **현장 L3에서 미검증**이다.
5. 실제 Gazebo L2 **FAIL**이므로 새 WSL2 moving Goal 원샷 출고 금지. 안전 기준 완화, 완료되지 않은 UI 지원 증거 합성, 과거 lock 삭제 또는 자동 재시도 금지.

## 4. 최소 다음 후보

Native Gazebo STOP helper는 `tools/p4_g07_prearmed_stop.py`에서 Goal 전에 컴파일·기동되어 기존 `nice +19, 마지막 CPU`에 위치한다. CI 4-core에서는 GUI/Marker/Goal/14-topic recorder와 리소스가 겹친다. 실제 STOP RPC가 155ms 걸렸으며 첫 CM 163ms gap과 중첩됐으므로, 안전 프로세스와 Guard는 그대로 두고 **STOP 보조 프로세스의 상대 우선순위만 소폭 개선**하는 후보가 논리적으로 가능하다. 단, 이것은 원인 확정이 아니므로 새로운 사이클에서 최소 RED→GREEN L0, 실제 L2의 CM source <120ms/Guard150ms/scan, odom, clock TTL/S02 contact0/cancel ACK/shutdown까지 재검증하기 전에는 인수 준비 완료로 승격하지 않는다.

**`AXIA_MVP_DEMO_ACCEPTED=HOLD`, `OWNER_GOAL_RELEASE=BLOCKED`. `main` 미병합.**
