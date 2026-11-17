# AXIA G07 — S1 공식 Nav2 문서·Issue 기반 단일 Moving Goal 원인 진단

## 0. 목적과 현재 인수 판정
- 사용자가 **S1** 진행을 승인하면서 공식 Collision Monitor 설정·이슈 리서치를 **진단보다 먼저 수행**하도록 요청. 원래 C05/C37 official Nav2, Waffle, Gazebo Harmonic 재사용.
- CM120 source·Observer <=120ms, Guard hard age<=150ms, Scan/Odom/Clock<=300ms 등 본래 경계를 유지. SW STOP과 인증 E-Stop 구분. CM120 `CAUSE_UNPROVEN`, `AXIA_MVP_DEMO_ACCEPTED=HOLD`, Owner WSL2 NOT_RUN. `main` 병합 별도 승인.

## 1. 조사한 공식 문서 (Jazzy 버전 고정)
1. Nav2 Jazzy Configuration: https://docs.nav2.org/jazzy/configuration_and_development/configuration_guide/core_servers/collision_monitor/configuring_collision_monitor_node/
   - `base_shift_correction` default **true**: source time과 현재 base 이동 차이를 Advanced TF transform으로 보정. 저속 로봇에도 정확도와 성능 절충; 공식 설명 평균 비용 대략 `1/(2*odom_rate)`, 빠른 로봇 비활성화 권고하지 않음.
   - `transform_tolerance` default **0.1s**: lookup/transform 허용 시각·대기와 관련; **AXIA 실제 runtime 0.02s** (Cycle07 installed source vs live CM readback #43999183495). 공식 기본값과 현장 overlay 값을 혼동하지 않음.
   - `source_timeout` default **2.0s**: 관측 센서 데이터 신선도, source별 override 가능, 0이면 검사가 비활성화되므로 사용 금지. **AXIA 실제 installed+runtime 1.0s** (same #43999183495), 임의 0.3/0.5초 변경 금지.
   - `stop_pub_timeout` default **1.0s**: 지속 ZERO 상태 후 발행을 멈출 수 있음. **AXIA runtime 값은 이번 연구에서 별도 실측하지 않음**. 최초 MOVING 구간 120~139ms 출력 공백과 장시간 STOP ZERO suppression을 동일 현상으로 오인 금지.
   - `cmd_vel_in_topic` default **cmd_vel_smoothed**; AXIA actual CM subscribed **/cmd_vel_supervised** (Cycle04 exact callback topic handle). `enable_stamped_cmd_vel` Jazzy default false; stamped vs unstamped 처리와 Header/MessageInfo로 입력·출력 메시지의 정확한 대응을 추정하지 않음.
2. Nav2 Jazzy source code:
   - https://github.com/ros-navigation/navigation2/blob/jazzy/nav2_collision_monitor/src/collision_monitor_node.cpp
   - https://github.com/ros-navigation/navigation2/blob/jazzy/nav2_collision_monitor/src/source.cpp
   - https://github.com/ros-navigation/navigation2/blob/jazzy/nav2_collision_monitor/src/scan.cpp
   - `cmdVelInCallbackStamped→process→source->getData→Scan::getData→Source::getTransform→nav2_util::getTransform(Advanced)`; 별도 고정 출력 주파수 timer가 아니라 입력 callback에 의존. STOP 지속 시 `publishVelocity`가 ZERO publish를 생략할 수 있음.
   - Original source `getTransform`: `base_shift_correction_ true` → source header stamp→now advanced TF, false→simple TF. 이 옵션은 단순 속도 스위치가 아니라 센서 좌표 시각 보정 정책.
3. Official Nav2 Jazzy package README: https://github.com/ros-navigation/navigation2/blob/jazzy/nav2_collision_monitor/README.md
   - LaserScan360 points Stop/Slowdown/Limit benchmark 약 **4.45ms**. 원래 하드웨어·input rate·장애물 수·tf readiness·Executor 조건이 달라 AXIA C05 81.973ms 콜백 elapsed와 직접 동일 벤치마크 비교는 불가능. LTTng tracer overhead도 분리.
   - CPU level software stop은 hard real-time certified E-Stop이 아님.

## 2. 공식 Issue/PR에 따른 인과 가설
- https://github.com/ros-navigation/navigation2/issues/3402 (**Closed**): Advanced lookupTransform에서 fixed frame→base transform 대기, 한 사례의 fixed-frame TF 30Hz에서 최대 ~33ms 추가 지연 가능. **원래 사용자 보고에 한정**된 내용, AXIA의 확인된 원인으로 확장 금지.
- https://github.com/ros-navigation/navigation2/pull/3412 (**Merged**): simple vs advanced TF lookup 선택 옵션 `base_shift_correction`. 당시 TB3 Gazebo와 테스트 수행, simple 모드는 낮은 정확도/성능 절충. 이미 Jazzy 설치 코드에 존재하므로 새로운 기능 구현 불필요.
- AXIA 다른 실행에서 odom 100Hz overlay를 사용. 공식 평균 보정대기 추산 ~5ms는 worst-case가 아니며, C05 콜백 wall=81.973ms나 별도 S1 최초 CM source138.611ms의 설명 증명이 아님.
- **이번 S1의 단일 가설 시험:** TF 함수 wall clock 및 thread CPU 시간, 공식 C05 cmd_vel 콜백 포인터/동일 CM PID·TID, 최초 CM RMW publisher source gap (source SYSTEM 내 비교)과 observer host MONOTONIC을 각자 정합. TF wall이 지연 대부분이라도 TF blocking vs CPU 선점/스케줄링은 `CAUSE_UNPROVEN` 유지.

## 3. S0 완료 증거와 S1 사전 진입 게이트
- S0 public source branch `fix/g07-cm120-s0-no-goal-diagnostic-regression-20261117` HEAD `904904df2ddd12c3f6cc2149945f0178face8eb1`; report `d06/docs/AXIA_G07_CM120_S0_READINESS_AND_LOCALIZATION_REGRESSION_20261117_KO.md`.
- Public real S0 L0 [#44009950139](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44009950139): bounded exact CM filter GREEN4, C05 TF interval join3, future inline diagnostic static compile2, old source RED. No Goal.
- Public actual official S0 NO_GOAL L2 [#44009454224](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44009454224): exact original private `966886c4627deb2bb3b37111fe336eeee6b9ebb4`, CM mapped test-only TF shim & `TF_ADV` calls **337**, Navigation+Localization shutdown both ACK, runtime rc0 and goal_sent=false. This proves actual loader/function invocation **only in NO_GOAL**, not moving temporal root.
- Last actual diagnostic Moving Goal [#44007105539](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44007105539): source first gap **138.610710ms**, TF proof failed old trace >100k, Localization shutdown 25.000396s timeout. Its result preserved as FAIL. No rerun of same source.
- S1 candidate uses S0 test-proven bounded **exact topic→callback** stream collector; child-only LD_PRELOAD already tested NO_GOAL; existing original pinned private Goal/Guard/CANCEL/S02 contact/Nav2 ordered shutdown unmodified. Diagnostic tracer-ON never release benchmark.
- **No other speculative tunings**: `base_shift_correction=true`, `source_timeout=1.0`, `transform_tolerance=0.02`, CM120/Guard150/ScanOdomClock300, STOP/SLOW polygons, CPU affinity as original unmodified.

## 4. S1 진단 단 한 번의 실제 시뮬레이션 Goal 계약
1. 먼저 공개 CI pre-Goal strict source and public test bindings, actual Jazzy TF ABI, C05/CM callback pretrace setup, simulation-only conditions fail-closed GREEN. Any preGoal failure => NO Goal.
2. 그 후에만 exact **one** bounded original Waffle/Nav2/Gazebo Moving Goal, first CM source gap & observer, safety first states, same PID·TID TF function interval. S02 contact0, STOP, odom>=1s, Goal Cancel and Navigation/Localization ACK are independent same-run gates, not override.
3. `TF_ADV` intervals missing, raw trace >bounds, mapping/clock ambiguous or RMW first gap not reproduced ⇒ `CAUSE_UNPROVEN`. TF dominant elapsed ≠ proven TF blocking. **Gate C unauthorized** without direct actionable cause proof.
4. After single actual run (PASS/FAIL), retire **only temporary S1 workflow trigger** on public release branch. Never re-trigger same diagnostic Goal automatically, never run on Owner WSL2. Preserve exact Actions URL/output, CI SHA, first failed boundary in this report and public Draft PR.

## 5. 교육용 사례 문제
- 공식 30Hz TF 사례 최대 33ms를 100Hz AXIA 실제 138ms 공백의 원인으로 곧바로 치환하면 왜 오류인가?
- `source_timeout=1.0` vs Guard TTL0.15, Scan TTL0.3과 `stop_pub_timeout`는 어떤 서로 다른 계층인가?
- TF 함수 내부 `thread_cpu < wall`이 실제 `lookupTransform` 대기인지 scheduler preemption인지 구분하려면 무엇이 더 필요한가?
- 한 진단 run에서 Localization Shutdown FAIL이면 왜 CM output latency 원인도 localization이라고 할 수 없는가?

## 6. 결과 기록 (S1 preflight/actual Goal 이후 채움)
```text
S1_OFFICIAL_RESEARCH=VERIFIED_NAV2_JAZZY_DOC_SOURCE_ISSUE3402_PR3412
S1_MOVING_GOAL=NOT_YET_EXECUTED
S1_ROOT_CAUSE=UNPROVEN
GATE_C=BLOCKED_CAUSE_UNPROVEN
AXIA_MVP_DEMO_ACCEPTED=HOLD
CERTIFIED_ESTOP=false
OWNER_WSL2_L3=NOT_RUN
MAIN_MERGED=false
```
