# AXIA G07 개발 사이클 04 — 첫 Nav2 Lifecycle 서비스 오류와 후속 수신 간격 위반

- 결론: **L0 PASS / 실제 L2 2회 FAIL (서로 다른 최초 실패 경계) / Owner HOLD**.
- 비공개 Instructor 후보 `fix/g07-ci-owner-runtime-parity-20261115`; P4 성공 `db1eec05` 보존.

## 1. 실제 통합 L2: Goal 자체는 정상, 종료 전 서비스 발견 FAIL
CI [#43690412617](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43690412617):
- 동일 headless Gazebo + GUI + RViz2, CI/Owner 공통 Goal 실행기, 정해진 CPU 출력 역할, GUI 전 사전승인.
- 실측 `CLEAR` → `SLOWDOWN` → `STOP`, 1.01119초 odom 정지, 진짜 `NavigateToPose` exact CancelGoal ACK. 7개 관측 주기 해당 실행 안에서는 PASS.
- **첫 실패**: `SERVICE_MISSING:/lifecycle_manager_navigation/get_parameters` (당시 3초 discovery limit), 원본 Nav2 Navigation/Localization shutdown ACK 없음. 이후 launch SIGINT에서 Collision Monitor exit code `-11`은 결과지만 **그 이전 서비스 미발견**부터 분석해야 한다.
- 범위 밖 조치 금지: 성공적인 Goal/CM/Guard를 재작성하지 않고 shutdown discovery만 제한된 budget을 제공. 새로운 `lifecycle_service_discovery_budget`은 총 cleanup **60초 한도 내 최대 8초**, 서비스 미발견시 ROS graph 첫 상태를 기록하고 fail-closed. TTL·속도/STOP·Goal 수/인수 권한 불변.

## 2. RED → GREEN
- Private RED `81ce842bbc6285aadd09236f178a4eb9e2c08db2`, sealed CI [#43690809187](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43690809187) FAIL.
- Private GREEN `36ce8e6909193413181fad965d6f63b06c187fb2`; sealed CI [#43690882253](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43690882253) PASS. 수정 파일 `tools/p2_g07_ordered_shutdown.py`, 테스트 `tests/unit/test_p4_g07_nav_manager_service_discovery_20261115.py`. **새 실제 shutdown 성공은 입증 안 됨**.

## 3. 후속 실제 L2에서 드러난 선행 타이밍 결함
재검 [#43690918618](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43690918618):
- 첫 위반 **Odom 355.881974ms**, `PRE_STOP` (300ms 한계); 동일 7채널 관측 최대 간격 약 339~383ms, Guard 내부 첫 래치는 기록되지 않음.
- 결정적 차이: CM source RMW 첫 gap **70.891726ms**, receive **377.049077ms**, 관측 콜백 **383.109139ms**, publication seq +1. 전 구간 CM RMW source 최대 131.984ms (150ms 미만).
- `RMW_RECEIVE_OR_OBSERVER_SCHEDULING_CANDIDATE`이지 `CM_PUBLISHER_STOP_PROVEN`이 아니다. RMW/Observer 쪽 공통 중단 가능성을 우선 분리해야 한다. 이후 lifecycle shutdown은 해당 실행에서 도달하지 않았으므로 이 변경 전체의 성공 여부 **미검증**.

## 4. REVIEW/다음 작업
- 위반 관측 주기를 안전 통과로 승격하거나 TTL을 변경하지 않는다.
- 새 first-timing fixture로 L0 재현 후, ROS/CM/Guard를 움직이지 않는 최소한의 Goal observer CPU 역할 분리 후보를 검증한다.
- 실제 CI L2 통과 전 Owner 배포 금지, main 병합 금지, 인증된 E-Stop 주장 금지.
- 교육 교훈: **한 수정의 L0 GREEN은 end-to-end GREEN이 아니다**. 이전보다 앞선 safety data boundary가 드러나면 최초 경계를 다시 재정의한다.
