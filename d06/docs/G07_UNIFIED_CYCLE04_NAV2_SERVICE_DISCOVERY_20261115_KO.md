# AXIA G07 — Cycle 04 Nav2 초기 lifecycle 서비스 발견 실패 (교육용 중간 보고서)

날짜: 2026-11-15 KST. **상태: L0 GREEN, 수정된 실제 GUI L2 검증 중, Owner HOLD**

## 최초 실패 경계와 근거

실제 CI Xvfb+Gazebo+RViz 단일 Goal Run [#43690412617](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43690412617)은 최초 Guard latch가 없고 STOP/odom dwell=1.01119초, CancelGoal ACK=CANCELED, seven-channel 최대 간격 CM=134.324ms, Guard=61.796ms, Scan=206.808ms로 안전 조건은 해당 Goal 창에서 통과했다.

하지만 **Nav2 원본 종료 프로토콜의 첫 실패**가 `/lifecycle_manager_navigation/get_parameters`에서 3초 wait_for_service 종료 `SERVICE_MISSING`이었다. 이 시점에 Native Navigation/Localization shutdown ACK는 **없다**. 같은 CI 작업의 강제 launch teardown에 Collision Monitor exit=-11이 나왔지만 **이 후속 상태를 최초 실패의 원인이라고 단정하지 않는다**. lifecycle manager가 실제로 종료했는지, DDS service discovery만 지연됐는지 **미확정**.

## RED→GREEN→REFACTOR→REVIEW→COMMIT

1. **RED** sealed 공개 CI [#43690809187](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43690809187), private 테스트 `tests/unit/test_p4_g07_nav_manager_service_discovery_20261115.py`: 총 종료 budget 60초 내에서 초기 발견 기회를 8초로 독립 검증하는 함수/진단 마커 부재 확인.
2. **GREEN** sealed 공개 CI [#43690882253](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43690882253), Instructor SHA `36ce8e6909193413181fad965d6f63b06c187fb2`. `tools/p2_g07_ordered_shutdown.py`의 첫 `get_parameters`/native service discovery만 `min(8s, 남은 60s)` 내에서 대기, 실패 시 읽기 전용 노드·서비스 이름의 존재 여부를 `AXIA_G07_SHUTDOWN_FIRST_SERVICE_DISCOVERY`로 보존. 성공으로 가정하지 않고 없으면 BLOCKED.
3. **REFACTOR/REVIEW:** 공통 `p2_g07_ci_moving_goal.run()`, 공식 Nav2, Guard/Twist/TTL, CancelGoal, 14-topic 원본·S02 조건 그대로. cleanup 명령만 제한적 변경. 사용자 WSL2 새 Goal 없이 실제 CI L2 우선.
4. **COMMIT:** private RED `81ce842b`, GREEN `36ce8e69`; 공개 sealed 실행 workflow RED `3c96e6b2`, GREEN `bb64d5b6`.

## 남은 검증 및 교육 포인트

새 실제 GUI L2 [#43690918618](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43690918618) 결과를 **완료 후 판정**한다. 서비스 발견 8초 초과 또는 manager 미존재면 실제 Goal 이후 clean shutdown은 FAIL/HOLD 유지. 원인 불확실성을 탐지/관측 가능하게 만드는 것과 실제 성공을 확인하는 것은 별개 단계다. 아직 WSL2로 재시도하지 않는다.
