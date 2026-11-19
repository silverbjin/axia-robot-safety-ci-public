# AXIA D06/G07 Cycle 02 — Nav2 Localization 관리 콜백 경계 분리 중간 보고 (2026-11-19)

## 1. 최초 오류와 구분
- 원본 공개 실제 Gazebo L2 [#44528260284](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44528260284): Navigation shutdown ACK 2.135663s, Localization manage_nodes SHUTDOWN request 전송 후 30.000372s 무응답, 같은 manager get_parameters 0.026005s 응답, CM/Gazebo exit0. 이는 SHUTDOWN ACK가 아님.
- 다음 실제 L2 [#44531611496](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44531611496): Navigation manage_nodes SHUTDOWN 40.000576s timeout, CM -11; 관리자 TIMEOUT이 Localization에만 고정된 오류는 아님.

## 2. 공식 코드 조사·가설
Nav2 Jazzy LifecycleManager `src/lifecycle_manager.cpp`의 `create_service<ManageLifecycleNodes>` 및 `create_service<Trigger>`는 같은 `callback_group_`을 사용하지만, `get_parameters` 서비스는 기본 executor에서 응답할 수 있음.
출처: https://api.nav2.org/nav2-jazzy/html/lifecycle__manager_8cpp_source.html
가설: 전체 노드 단절이 아니라 관리 전용 callback group 또는 service thread 문제가 있을 수 있음. 다른 원인(특정 manager shutdown 콜백 실행 중 정체, DDS 응답 누락)은 배제되지 않음.

## 3. RED→GREEN→REFACTOR→REVIEW→COMMIT
- **RED** [#44531919670](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44531919670): `d06/tests/test_d06_localization_manager_callback_probe.py`에서 기존 Student 런타임에 same-group `/lifecycle_manager_localization/is_active` read-only 단일 probe 부재를 확인.
- **GREEN L0** [#44532674063](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44532674063): **115/115 PASS**, 공용 Nav2 service의 단일 SHUTDOWN 요청을 재시도하지 않으며 false-ACK 판정 불가.
- **Student 소스** `block_B/day07/h01_runtime/tools/p2_g07_ordered_shutdown.py` commit `50464f39b2c37dd631768c4ea98c9bdad2d1127c`; probe method `probe_localization_manage_callback_group`는 `/is_active` Trigger를 읽기만 함. 응답이 있어도 shutdown ACK로 승격하지 않음. 기존 60s global deadline 내에서만 추가 확인하며 Goal/Scan300/CM120/Guard150 불변.
- **Public Owner immutable Student pin** 및 `d06/scripts/axia_d06_g07_wslg_gpu_rtf_compare_once.sh` blob 검증 갱신. 학생 PR #62 공개 PR #177 양쪽 Draft, main 미병합.
- **Review:** 클라이언트가 get_parameters에 응답했다고 manage_nodes 자체 콜백 실행이 보장되지 않음. 장애 최초 관찰 시 같은 callback group /is_active 응답을 기록하고 timeout 지연/원인 분리. 실제 서버 스택 조사 전 근본원인 확정 금지.

## 4. 관련 실제 L2 증거와 검증 수준
새 Student SHA에 대한 최초 공개 실제 Jazzy/Harmonic/Nav2/Waffle L2 [#44532801974](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44532801974):
- Navigation ACK + Localization ACK 모두 확인, CM exit0, 부모 shutdown GRACEFUL.
- 하지만 같은 세션 **READY 이후** Safety 300.282ms > Scan TTL 300ms; native gap 299.140ms. Student qualified 20s 또한 Raw/Safety TTL 위반. 전체 통합 L2 FAIL.
- 따라서 이번 실행에서는 새 `localization_manage_group_probe`가 **NOT_TRIGGERED**(manager 정상 ACK)로, 이전 30초 timeout의 원인 판정에 필요한 대상 실제 데이터는 아직 없음.
- 이 실행에서 L2 관리 종료가 정상임은 scoped GREEN이지 **반복 안정성 증명**은 아님. WSLg native Gazebo SIGSEGV -11 최초 core stack 미확보.

## 5. 결론
이번 사이클은 **서로 다른 Lifecycle 서비스 callback group의 최초 실패 진단 기능만 GREEN**입니다. 기존 오류의 해결·배포는 미완료입니다. 학생의 별도 read-only 센서 executor 정체 (L2 #44531611496에서 340.542ms late) 를 다음 단일 후보로 분리 검증합니다.

`AXIA_MVP_DEMO_ACCEPTED=HOLD`; `D06_GAZEBO_LIVE_RELEASE=HOLD`; `CERTIFIED_ESTOP=false`; `OWNER_WSLG_L3_NOT_RUN`.
