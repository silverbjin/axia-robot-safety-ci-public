# D06 G07 첫 안전 전이 및 Native Guard 수신 경계 인계 (2026-11-14)

현재 판정: **HOLD_CI_REAL_G07_L2**. Owner WSL2 최종 시연은 아직 승인되지 않았다. 실제 SW Stop은 인증된 물리 E-Stop과 다르다.

## 관찰된 원본 경계

- Owner: 첫 Scan 콜백 364.642ms > 300ms, 이후 Guard 내부 CM age 153.018ms > 150ms와 UPSTREAM_STALE_AFTER_MOTION. 인과관계 미입증.
- 공개 실제 Gazebo #43592074676: CM RMW 발행 자체 170.929ms > 150ms, Guard CM age 156.957ms. rosbag nice+10은 반복 안정성을 보장하지 못함.
- 공개 Gazebo #43596963732의 3회 독립 cold-start는 PASS, PASS, FAIL. 3회차 Observer odom 309.208ms, RMW 수신 307.696ms, 발행 140.388ms, Scan 302.840ms.
- 공개 Gazebo #43601466787: Observer Scan 372.183ms이지만 Supervisor 내부 Scan gap 증가 0건. Observer CM callback 368.869ms, 해당 RMW 발행 30.001ms·수신 30.126ms. 다른 구간 CM source 171.215ms > 150ms. 서로 다른 원인 경계로 취급한다.
- 공개 Gazebo #43603054244: 실제 Guard CM age 179.652ms로 최초 래치 UPSTREAM_STALE_AFTER_MOTION. 그 실행에서 CM source >150ms 미관찰. Observer만의 지연으로 실제 Guard 래치를 설명할 수 없음.
- 공개 Gazebo #43602726243: Native Guard 계측 추가 후 실제 L2 전체 PASS 1회. 전체 안정성을 입증하지는 않음.

## RED → GREEN 변경

- 공개 d06/live/d06_supervisor_scan_vs_observer_first_gap.py 및 테스트: 별도 Safety Supervisor Scan callback counter와 Observer 간격 분리. CI #43601188863에서 L0 62 PASS, 실제 ROS/RViz L1 PASS.
- 비공개 Instructor ros2_ws/src/axia_safety_supervisor/axia_safety_supervisor/p2_guard_input_timing.py 및 p2_base_guard_node.py: G07에서만 기존 /axia/p2/base_guard 상태에 Guard의 CM·Supervisor 실제 입력 콜백 간격 및 150ms 초과 횟수를 기록. Safety TTL·Goal·Guard 정책·QoS 불변. CI RED #43602043818, 이후 Green 및 실제 L2 #43602726243.
- 공개 d06/live/d06_native_guard_vs_observer.py 및 테스트: Guard 첫 래치 시에도 실제 수신 카운터와 CM 수신 나이를 보존하도록 RED #43603408966 → GREEN #43603503755, L0 69 PASS, ROS/RViz L1 PASS.
- 공개 실제 G07 L2 workflow 경로: .github/workflows/d06-g07-real-moving-timing-l2.yml, 브랜치 release/p2-g06-cm-ttl-20261110. 새 Native Guard 수신 경계 CI #43603675174는 별도 판정 필요.

## 다음 진단과 판정 기준

1. 기존 G07 Observer의 scan/odom과 Supervisor health_diagnostics.scan_callback_gaps_over_timeout은 서로 다른 수신 지점이므로 분리한다.
2. Guard 첫 래치 시 first_latch_trace.cm_age_sec, native_input_timing.cm_last_receive_age_sec, CM 콜백 150ms 초과 횟수의 Goal 전후 차이를 검토한다.
3. RMW source/received와 publication sequence를 같은 구간에서 비교한다. 누락된 시퀀스가 있으면 발행 중단으로 단정하지 않는다.
4. 실제 STOP은 같은 Goal의 odom dwell >=1초, Lifecycle Manager native ACK, CM 정상 종료, 원본 rosbag 무결성으로 검증한다. 0 Twist와 Action 종료만으로 판정하지 않는다.
5. 어느 안전 주기라도 위반·미확인이면 전체 HOLD. 이미 성공한 G00~G04A 및 G05/G06은 반복하지 않는다.

## 배포 제한

- 공개 CI는 고정 Docker digest와 보호 환경에서만 시뮬레이션 Goal을 1회 수행한다. 비공개 Instructor 코드·원본 rosbag·Goal UUID를 공개 업로드하지 않는다.
- 강사용 D06 WSL2 원샷은 아직 이전 P4 G11 공개 릴리스 및 Instructor SHA를 고정하고 있으므로, 정확히 검증된 CI 원본과 동일하도록 업데이트하기 전에는 최종 인수 실행을 안내하지 않는다.
- 본 단계에서 새 WSLg Gazebo GUI + RViz2 동시 렌더링은 NOT_RUN. CI 성공의 검증 범위와 GUI Owner L3는 다르며 main 병합은 사용자 승인 전까지 진행하지 않는다.
