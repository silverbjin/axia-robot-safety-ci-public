# AXIA G07 Cycle07 — official simple TF와 센서 freshness 동시 안전 경계

## 최초 실패 기반 계획
- Cycle05 real diagnostic #43995793080: official cmdVel C++ callback81.972669ms under CM source120.172578ms gap; advanced TF 원인 미확정. Original nontrace CM source128.644/133.659ms >120 release FAIL.
- Cycle06 real #43997318717: original sim-only candidate denied before Goal. 최초 오류 G07_C06_SOURCE_TIMEOUT_UNVERIFIED; 뒤 CLOCK_MISSING/NO_REAL_GOAL은 cascade. 공식 Jazzy collision_monitor_node.cpp에는 CM source_timeout default2.0초, base_shift_correction default true, 실전 CM 원본 YAML의 source_timeout 검증 계약 불일치. 실제 runtime readback은 startup 실패로 없음. 기존 C06 RED→GREEN4 L0 PASS 자체는 보존.
- 위험: base_shift=false는 scan 시각과 현재 위치 간 움직임 보정을 생략하므로, 오래된 Scan를 허용한 상태에서 실행하면 위치 오차 발생. 사용자가 요구한 MVP 필수 Stop0.40/Slow0.75/Guard CM hard150ms/Scan TTL300ms와 함께 **CM sensor source_timeout <=0.300초**가 필요하다. 이는 기존 공식 default 2.0을 더 엄격하게 제한(완화 아님)하는 두 번째 필수 파라미터다.
- 이번 후보는 공식 CM 두 파라미터의 **결합된 하나의 안전 프로파일** (base_shift_correction=false, source_timeout=.3); public CI simulation one Goal에만 허용하고 Owner/WSL2, 학생/실로봇, main 적용 불가. 원래 CM/Guard/Supervisor/official Nav2 소스는 수정하지 않음.

## RED→GREEN→REFACTOR→REVIEW→COMMIT
1. RED: Cycle06 candidate 67664552d9283d24db25fadb329733f83dc27878에 엄격한 freshness-bounded test를 적용하면 source_timeout 기본이 명시되지 않아 G07_C06_SOURCE_TIMEOUT_UNVERIFIED 재현. 더 엄격한 원본 timeout 그대로면 pass, 2.0/absent만 0.3으로 축소, 0.35 등 알 수 없는 값은 BLOCK.
2. GREEN: 기존 private tools/p4_g07_cm_sim_simple_tf.py 내에 안전 동반변경 한 곳만 추가. 기존 public CI, zone geometry/TF0.02, Guard150ms 및 CM120ms Gate는 변경하지 않는다. 기존 tests/unit/test_g07_cycle06_sim_simple_tf_option.py를 Cycle07 회귀로 갱신; 신규 safety helper/ROS publisher를 만들지 않는다.
3. 공개 sealed RED→GREEN4 L0와 bash/launch param writer 정적 검증. 합격했을 때만 최초 실패한 exact C37 official one Goal CI를 **한 번만** 수행하며 실제 pre-Goal readback(base_shift false + source_timeout <=.3)을 확인.
4. 실제 public Gazebo/ROS2 single Goal: existing Contact0, CLEAR→SLOWDOWN→STOP, odom1s dwell, CancelGoal+Nav2 shutdown, 14-topic, CM RMW source+Observer <=120ms, Guard/CM<=150ms, Scan/Odom/Clock<=300ms 원래 계약을 모두 보존. 원본 2.0s를 감소시킨 source_timeout가 실제 Scan 조기 STOP을 발생시키면 그 첫 현상을 FAIL로 보고한다.
5. Safety caveat: scan header age vs velocity·angular rate와 zone clearance는 별도 검증 미완료. 실제 CI PASS라 해도 물리 인증이나 Owner 승인 아님. 본 CI에서 실제 max odom speed, w, 보수적 0.3s* (abs(v)+.75*abs(w)) <0.35m를 읽기 전용 산출하지만 header age 실측은 아니다. 증거 부족이면 전체 시연 stability=UNVERIFIED.
6. 결과에 따라 후보를 폐기/HOLD 또는 필요 최소 후속 인수 경계만 제시. CI FAIL이면 동일 구성 재주행 반복 금지. 매 Cycle 교육용 경과보고서+실제 Run+커밋 보존, release one-off 회수, private instructor sealed, main 승인 전 미병합.

현재 AXIA_MVP_DEMO_ACCEPTED=HOLD, CM_120MS_RELEASE=HOLD, OWNER_WSL2_MOVING_L3=NOT_RUN, CERTIFIED_ESTOP=false.