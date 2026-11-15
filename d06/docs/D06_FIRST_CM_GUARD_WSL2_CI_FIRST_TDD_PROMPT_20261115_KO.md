# D06 Owner 최초 CM 발행 간격 초과 — CI 우선 TDD 디버깅 지침

> 이 지침은 공개 CI에서 WSL2 현장 오류를 선재현한 뒤에만 신규 Owner Goal을 허가하기 위한 실행 프롬프트다. Baseline v1, ROS 2 Jazzy, Gazebo Harmonic, 공식 Nav2/TB3 Waffle, Safety Supervisor/Guard 150ms, Scan 300ms 기준을 변경하지 않는다.

## 반드시 지킬 사실과 실패 경계

- 두 번째 실제 Owner WSL2의 첫 안전 상태 전이는 UPSTREAM_STALE_AFTER_MOTION이다. Guard 내부 CM age 169.168036ms > 150ms, 임계 crossing은 latch보다 19.168036ms 이르다. Supervisor age 약 0.576ms, FSM=NORMAL.
- 동일 CM 연속 sequence +1에 대한 RMW source 간격 184.414666ms, receive 184.358695ms, Observer callback 223.656034ms. 그 창에서 Supervisor 발행 4건, 최대 source-coverage gap 89.04962ms. CM publish scheduling 또는 CM post-input execution candidate이며 내부 콜백 지연이나 OS 원인은 아직 미입증.
- 두 번째 CM 메시지가 Guard latch 이후 관찰돼, pre-latch 원본의 first_timing_violation=null은 정상 신호가 아니라 right-censored 진단이다. 최초 TTL crossing과 이후 완성된 CM source pair를 같은 Goal 증거로 결합해야 한다.
- 기존 실제 Xvfb/Gazebo L2 #43667573251의 PASS와 headless 3/3은 역사적 성공이다. 현재 WSLg L3는 FAIL이며 공개 게이트 HOLD, 허가 0회다. 14-topic SQLite quick_check=ok는 Goal 정지/정상 종료 formal PASS를 뜻하지 않는다. CM process -11, RViz mesh 오류, 교육용 monitor 종료 예외는 첫 TTL 위반과 별도로 검증한다.

## 재사용 프롬프트

당신은 AXIA D06 공개 CI 우선 Robot Safety 디버거다. 다음 절차를 순서대로 반복하되 실제 Green 증거가 없으면 STOP/HOLD로 끝낸다.

1. **증거 동결:** Owner 원본 TAR/GUI ZIP은 읽기 전용으로 열고 SHA256/원본 출처를 검증한다. 공개 CI에는 UUID, 로컬 원본 경로, rosbag 데이터, Instructor 정답/비공개 코드가 아니라 비식별 첫 경계 수치만 전송한다.
2. **최초 상태:** 최종 exception/종료 코드가 아니라 첫 Guard 래치, cm_rx/age/threshold_crossing, 동일 시각 Supervisor FSM/age를 확인한다. SW Stop과 인증된 E-Stop을 혼동하지 않는다.
3. **서로 다른 시계:** RMW source/receive는 동일 system clock 내 delta만, Guard 및 Observer는 각각 monotonic clock 내 delta만 계산한다. wall과 monotonic의 절대 시각을 직접 빼지 않는다.
4. **우측 검열 해결:** pre-latch two-sample gap null을 정상으로 취급하지 않는다. first latch 뒤 수신된 같은 ROS 세션의 다음 CM packet과 연속 seq/source/received/callback pair를 결합하고, source 184ms와 Guard 내부 169ms를 별도 지표로 검사한다.
5. **원인 분리:** source >150ms면 CM 발행 간격 지연 후보, source 정상·receive >150ms면 DDS/RMW 수신 후보, source/receive 정상·Observer callback만 >150ms면 Observer 처리 후보. 결측은 UNVERIFIED. 상위 Supervisor input coverage와 native Guard receipt의 실제 증거도 함께 사용한다.
6. **RED:** 새 비식별 fixture로 184.414666ms source, sequence +1, 4 upstream messages, 최초 Guard TTL 및 right-censored 사례를 재현하고 공개 Actions FAIL 출력과 정확한 Commit을 기록한다.
7. **GREEN:** 허용된 원인에 한해 최소 수정한다. Safety Supervisor, Guard, 공식 Nav2/CM 안전 TTL, Goal 경로, G05/G06는 변경하지 않는다. 공개 source-only L0에서 실패 재현이 PASS되고, 별도 actual Gazebo+RViz Goal L2에서 node-to-node source/receive 주기 및 native Guard no-latch가 검증되기 전에는 runtime 안정화로 판정하지 않는다.
8. **필수 실제 L2 범위:** 신규 source SHA, 고정 Docker digest, REAL Gazebo/Nav2 single Goal, Scan<=300ms, CM/Guard<=150ms, CLEAR→SLOWDOWN→STOP, odom STOP dwell>=1s, native Lifecycle ACK, CM clean exit0, 원본 14-topic bag custody. CI Xvfb는 WSLg 인수가 아니다.
9. **환경 경계:** CI에 안전 노드 간 데이터 전달 주기의 adversarial/WSL2-like scheduling stress를 1회만 추가해 경계가 깨지는지 확인한다. 정상 L2 하나의 PASS로 WSL2 scheduler parity를 단정하지 않는다. 실패하면 같은 raw replay를 새 공개 비식별 RED로 기록한다.
10. **REFACTOR/REVIEW/COMMIT:** 파일경로, 테스트 커맨드/실제 로그, 검증 수준과 미검증 항목, 공개/비공개 Git 브랜치·커밋·Actions URL을 작성한다. 실패 assertion의 전체 비공개 소스 출력 금지.
11. **Owner:** 새로운 현장 오류가 생긴 즉시 allow_one_final_wsl2_owner=false, allowed_final_owner_attempts=0. 사용자 재시도는 금지한다. 새 전체 공개 CI L2와 실패 경계 회귀 GREEN 후에만 pinned SHA 한 번을 허가한다. Owner Goal은 물리 TTY 수동 YES-P2-G07-GOAL, main 병합은 사전 승인.

## 완료 판정

보고 형식: FIRST_GUARD_TRANSITION → FIRST_NATIVE_TTL_CROSSING → CM_SOURCE/RMW_RECEIVE/OBSERVER_GAP → UPSTREAM_COVERAGE → ROOT_CAUSE_PROVEN/UNVERIFIED → RED_RUN → CHANGE → GREEN_RUN → ACTUAL_GAZEBO_L2 → OWNER_WSLG_L3_STATUS → SOURCE_SHA/BRANCH/COMMIT → MAIN_NOT_MERGED. 성공 CI가 없는 항목은 반드시 HOLD로 남긴다.

관련: d06/tests/fixtures/g07_owner_20261115_second_cm_publication_gap_sanitized.json, d06/tests/test_d06_owner_second_cm_source_gap.py, d06/live/d06_guard_cm_first_latch_join.py.
