# D08 Cycle 06 — 최초 실제 Guard TTL 위반 계층 구분·압축 증거 회귀 (RED→GREEN L0, L2 HOLD)

일자: 2026-11-19 KST. **이번 Cycle은 안전 로직·TTL 수정이 아닌 원인 경계 계측이며, 실제 Gazebo STOP PASS 아님.**

## 기존 현장/공개 CI RED 원본
- D08 사람 Mesh+RGB-D 단일 G07 Moving World 실 L2 [#44483897411](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44483897411): 최초 Guard `UPSTREAM_STALE_AFTER_MOTION` 내부 CM age **169.429ms > 150ms**, 독립 Observer age **167.195ms**, skew **2.234ms**. D06 CLEAR·SLOW 실제 통과, STOP은 차단.
- 카메라 `always_on=false` 이후 [#44485688526](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44485688526): 최초 Guard **186.991ms**, 독립 Observer **181.809ms**, skew **5.183ms**. 미구독 RGB-D 상시 렌더 후보만으로 해결되지 않음; 그 수정은 실제 시연 통합 PASS 근거가 아님.
- 각 원본 `AXIA_G07_PUBLIC_CI_FIRST_GUARD_LATCH_INTERNAL`을 최종 `GUARD_LATCH_DURING_STOP` 예외보다 먼저 본다. Supervisor는 해당 시각에 정상 상태와 freshness 유지.

## 수정 가설 및 RED→GREEN
- 가설: Guard 고유 처리 지연이라면 독립 Observer의 CM 수신 age는 보통 더 짧을 수 있다. 실제 두 수신자가 모두 150ms를 비슷한 시각에 넘겼으므로 **공통 CM 발행 지연 또는 DDS/호스트 스케줄링 공통 장애가 후보**다. *이 원인 중 하나를 직접 증명한 것은 아니다*.
- 신규 `d08/scripts/d08_g07_first_guard_ttl_review.py`: 기존 G07 stdout의 최초 두 JSON 이벤트(`FIRST_CM_GUARD_RECEIPT_SKEW`, `FIRST_GUARD_LATCH_INTERNAL`)만 읽고 **원래 150ms 절대 경계**, monotonic diff, independent Observer age/Guard age, skew를 검수. 실제 publish timestamp와 RMW take가 없으면 `cause=UNDETERMINED`; L2는 항상 HOLD. 입력 크기 12MB, 아티팩트 1KB 단위, O(1) 출력.
- 신규 `d08/tests/test_d08_g07_first_guard_ttl_review.py`: 두 실제 RED 숫자 fixture의 최초 Guard age와 공통 구간 후보, 독립 Observer만 정상인 별도 후보, Guard 비차단/불완전 로그의 FAIL-CLOSED 검사.
- 신규 `d08/tests/test_d08_g07_readonly_pregoal.py`: D04·D05 실제 2 VALID+1 UNKNOWN과 공식 D07 path 3상 연결, 새 Goal/Twist 미발행, 잘못된 SHA 차단. Public workflow 테스트 선택 목록에 두 파일을 명시하고 **실제 실행 여부를 별도로 확인**. 최초 워크플로 목록 누락을 방치하지 않음.
- `.github/workflows/d08-single-session-moving-l2.yml`: Moving L2 실패시 기존 `g07_ci_moving.log`를 읽어 최초 Guard 수신 경계의 **숫자 JSON+SHA256**만 allowlist 업로드; 원본 rosbag, 개인 파일, CTF, 대용량 raw log는 업로드하지 않음. 별개 L2 성공 증거와 혼용 금지.
- 기존 G07 Student Safety Supervisor·Collision Monitor·Guard·기본 수동 TTY 승인, 300ms Scan/150ms Guard/120ms CM는 모두 수정하지 않음.

## 실제 공개 GREEN 테스트와 후속 실제 RED
- Public exact CI source `ea91441698f133dec5cd6593a6f8320ac525d947`.
- [#44491362197](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44491362197): **L0 240 passed in 1.20s**, 독립 Student 4/4, 공식 Jazzy/G07 SDF SOURCE L1 PASS.
- **실제 Native G07 one-world Moving L2 [#44491362187](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44491362187)**:
  - Contact witness build SUCCESS, exact G07 13.6 Transport parity, Gazebo/RViz X11 실제 GUI 두 창, REAL Nav2 Goal→CLEAR/SLOW PASS.
  - STOP 중 최초 Guard internal CM age **184.290ms**, 독립 Observer **183.278ms**, age skew **1.012ms**, 초과 **34.290ms**. Guard SW 차단은 정상 안전 대응이며, 시연 정상 STOP 판정 **FAIL**.
  - 수집 `D08_G07_FIRST_GUARD_CAUSAL_HOLD {status:FIRST_SAFETY_TRANSITION_PROVEN_MOVING_L2_HOLD,candidate:COMMON_CM_SOURCE_OR_SHARED_DISPATCH_GAP_CANDIDATE,cause:UNDETERMINED,cm_age_ms:184.29}`.
  - 증거 ZIP artifact #14512813078, 업로드 SHA256 `310657450343e5471d5395945934acea7983f8590395e0619f02ff8f2b56d404`, ZIP CRC PASS. 단 **5개 allowlisted 파일**, 그중 최초 타이밍 JSON 694 bytes. Goal·UUID·원본 bag/영상 미공개.
  - 신규 safety report `moving_l2_accepted=false`, `publisher_timestamp_or_lttng_proven=false`, `cm_guard_150ms_safety_contract_pass=false`.
  - 기존 CI raw `GUARD_RECEIPT_LAG_CANDIDATE`라는 문자열은 Guard만의 원인을 증명하지 못한다. two-receiver 공통 지연 후보가 더 적합하되 원인 미확정 유지.

## 외부 공식 Nav2 소스 검토
- Jazzy `CollisionMonitor::cmdVelInCallbackStamped`는 유효한 Twist 입력에서 `process()` 호출; `process()`는 source/TF 자료, Polygon STOP/Slowdown 계산 후 `publishVelocity()` 수행.
- `publishVelocity()`가 0 명령을 장시간 중단하는 `stop_pub_timeout`은 별도 계약으로, 현재 Native readback 5.0s. **184ms의 누락을 이 파라미터만으로 설명할 수 없음.**
- 출처: https://api.nav2.org/nav2-jazzy/html/collision__monitor__node_8cpp_source.html (cmdVelInCallbackStamped / process / publishVelocity); https://docs.nav2.org/jazzy/configuration_and_development/configuration_guide/core_servers/collision_monitor/configuring_collision_monitor_node/ .
- 이 검토는 인과증명 아님. 호스트/TF 콜백 실행시간과 CM 실제 RMW publish timestamp가 필요.

## 재개 지점 및 인수 수준
- 기존 G07 `d06/live/g07_cycle29_first_cm_callback_trace.py`, `g07_cycle30_bounded_cm_trace.py`, `g07_cycle31_cm_topic_callback_identity.py` 공개 구현을 조사·재사용 가능한 코드로 확인. **새 LTTng 기반 추적기 자체 개발 금지**. 필요하면 이 기존 도구에 현재 184ms 사례를 연결해 source→publish→Guard take 간 최초 한 구간만 검증. Trace 없는 현재 원인 진단은 HOLD.
- D04 YOLO C++ real + D05 2 VALID/UNKNOWN + 공식 Path 3상은 G07 Goal 전 옵트인 source 경로까지 연결됐으나 **실제 공통 세션 시연 L2 미실행**, NO_GOAL 별개 PASS와 합산 금지.
- 가장 작은 원인 검증 후보: STOP set_pose 시 **TF lookup/CM callback duration**과 CM publisher RMW timestamp를 동일 monotonic 타임라인으로 결합하고 L2 첫 실패 범위를 좁힌다. 새 안전 알고리즘/Guardian 재작성 금지; 150ms TTL 완화 금지. 실제 CM/RMW를 조사하기 전 성능 튜닝 무작위 반복 금지.
- Public Draft PR #189 및 Student Draft PR #63 유지, main 미병합, instructor 답안 비공개, Owner WSL2 L3 **NOT RUN**, SW Stop은 인증 E-Stop 아님. D08 전체 `D08_SINGLE_SESSION_MOVING_E2E_ACCEPTED=HOLD`.
