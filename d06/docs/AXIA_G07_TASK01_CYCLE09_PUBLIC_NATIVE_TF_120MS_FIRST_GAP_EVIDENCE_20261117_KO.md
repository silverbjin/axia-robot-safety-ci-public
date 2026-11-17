# AXIA G07 — Task 01 Cycle 09: 첫 CM source 지연과 동일 native TF polling 증거 직접 보존

작성: 2026-11-17 KST. 범위: 기존 G07 1 Goal, Jazzy/Harmonic, 공개 CI만. 출고 판단: **HOLD**.

## 1. 최초 실패 경계 및 소스 고정

- 공개 Actions: https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44101521543 (workflow 전체 FAIL은 의도된 tracer-ON 진단 HOLD).
- 공개 진단 workflow 소스 SHA: **02ad6c63f3c16ee8e0526e6f176db92e5639d84a**.
- 실제 공개 ROS 주행 소스: **silverbjin/axia-robot-safety-student@6a3047b5aa219687f5fc918e467cea5115d3d482**, block_B/day07/h01_runtime.
- 실행 이미지: ghcr.io/silverbjin/axia-g07-runtime@sha256:861ae1df0560f991698d8967193380b1619589ba7770b5e2ca91ea4ef31f0c8e. 실제 ROS Jazzy/Nav2 25 packages / 5 official files parity PASS; Ubuntu 24.04, Gazebo Harmonic 8.15.0, RMW Fast DDS.
- **원시 증거 직접 회수**: 공개 Actions artifact ID **14335962966**, 3파일 ZIP. 8,693바이트 numeric-only first_gap_sanitized.json의 실제 SHA256 **b71afac1ad0a8615f4d407745956aca53089814eb338d755a32ddbecc75a2c36**. ZIP 내부 SHA256SUMS.txt의 해시와 일치; 원본 ZIP SHA256 **360c753b1c2655a98b7b39146afa4283e0fc32217423bdcd8a078d0b2a567518**. 원본 PID/TID, 원시 LTTng, rosbag/개인정보는 공개하지 않음.
- 보존된 공개 숫자형 파생 결과: d06/evidence/g07_cm120_task01/run_44101521543_native_tf_budget_summary.json (원본 artifact ID/해시/실제 두 메시지 및 TF 수치의 정확한 provenance). 숫자 파생은 전체 8,693바이트 원본을 대체하는 행위가 아니며 원본 Run과 해시로 대조해야 한다.
- 이 실행의 **최초 CM publisher RMW source 간격 = 132.917326ms >120ms**, 같은 연속 publication seq의 Observer 간격 = **131.903275ms >120ms**. 후속 예외가 아니라 최초 발행/관찰 안전 경계가 진단 대상.

## 2. 같은 CM 최초 Observer 창에 직접 속하는 official TF 호출

이번에는 이전 Cycle 08의 'EXACT_SOURCE_TF_ALLOWLIST_JOIN 실패'와 달리 실제 sanitizer status가 **FIRST_RMW_SOURCE_GAP_SELECTED_CAUSE_UNPROVEN**으로 정상 종료했다. 첫 pair±200ms의 official CM cmd_vel 구독 callback **동일 원본 PID/TID** 조건으로 파싱한 주변 TF 호출은 10개; 실제 첫 Observer 창 [0,131.903275ms] **안에 완전히 포함되는 TF 호출은 1개**.

| 정확한 native CM Advanced TF 한 호출 | 실측 |
|---|---:|
| Observer first pair 내 TF 진입/종료 | +2.371825ms / +124.985671ms |
| TF 함수 벽시계 소요 | 122.613846ms |
| 해당 호출의 nested libc sleep | 12회, 누락 0 |
| 실제 sleep **요청** 합 | 120.000000ms |
| nested sleep **실제 wall** 합 | 121.830939ms |
| 그 native thread CPU | 0.961205ms |
| 호출 벽시계 중 최소 실제 sleep 요청 몫 | 97.8682% |
| 첫 RMW source 간격 중 실제 sleep 요청 몫(수치 비교) | 90.2817% |
| sleep 제외 가능한 TF 전체 시간 **상계** | 2.613846ms |
| 같은 호출의 zero-timeout TF 가용성 | entry=false, exit=true |
| 같은 호출의 sleep count/containment | coverage_complete=true |

**직접 검증된 사실:** 동일 CM 공식 subscription callback의 Advanced TF 함수가 실제 10ms sleep 12회를 요청하여 최소 120ms를 소모했고, 진입 시 변환은 불가능하다가 호출 종료 후 가능했다. 해당 native 함수의 지배적 지연은 사용자가 명시적으로 요청한 sleep이며, 단순히 C++ CPU 실행이나 계측기 마지막 예외가 아니다. 별도 Kernel runnable wait / 스케줄러 기여가 0으로 증명된 것은 아니다. sched_schedstats가 꺼진 경우 runqueue 지표는 UNAVAILABLE.

다만 실제 **CM sender의 RMW SYSTEM source 출처와 동일 native CM MONOTONIC 호출 사이의 인과 완전 입증은 여전히 HOLD**한다. 첫 Observer pair 안에 실제 TF sleep이 들어 있다는 사실과 그 뒤 publish가 이어진다는 공식 코드 흐름은 매우 강한 근거지만, source publication 단위와 native callback 단위의 *정확한 시간영역 동기화/귀속*을 임의로 PASS 처리하지 않는다.

### 동일 런 cross-clock 후보 계산 — 증명값과 가정 구분

- REALTIME↔MONOTONIC 구간 시작/끝 host anchor offset 차 = **30ns** 관찰됨. 이는 양 끝점의 정합성이지, 시뮬레이션 내내 CLOCK_REALTIME step이 없었다는 독립 증명은 아님.
- RMW source→RMW receive SYSTEM 구간: 첫 메시지 **0.385532ms**, 둘째 **0.133433ms**. RMW received→observer MONOTONIC 상대기준 투영값: **7.328706ms**, **6.566754ms**. 해당 수치에서 DDS 수신 전송지연이 first source132.917ms를 설명하지 않는다는 강한 근거는 있으나 정식 clock-domain causal proof는 별개.
- **동일 host CLOCK_REALTIME source stamp를 양쪽 anchor로 MONOTONIC에 변환할 수 있다고 *조건부 가정*할 때**, 두 번째 output source는 첫 Observer 수신 이후 약125.203088ms에 기록됐으며 위 TF 함수 종료(+124.985671ms) 약 **0.217417ms 뒤**이다. 실제 publisher timestamp→CM callback의 절대 정합 허용오차에 대한 검증이 없으므로 **이 0.217417ms는 참고용 정렬 후보이며 인과 증명·Task02 승인값이 아니다**.
- Internal TF Buffer Clock 직접 샘플은 이 artifact에 저장되지 않았으며, kernel runqueue delta도 없다. 따라서 'TF 변환 가용성 polling sleep'은 same-call 관측 사실, 'TF2 내부 clock이 진행하지 않아서 재시도했다' 또는 'Scheduler wait이 0이다'는 미증명이다.

## 3. 공식 출처 및 코드 경로 Research

| 공식 소스 | 확인 사실 | AXIA 판정 |
|---|---|---|
| https://api.nav2.org/nav2-jazzy/html/collision__monitor__node_8cpp_source.html | Jazzy CollisionMonitor::cmdVelInCallbackStamped → process(); process()는 source->getData() 호출 후 publishVelocity(); publishVelocity()에서 cmd_vel_out_pub_->publish() 호출 | **원본 공식 C++ 동기 실행 순서**는 확인. 다만 public 수치 artifact는 최종 source seq↔특정 publish C++ tracepoint 전체를 보존하지 않아 인과 정식 PASS 미선언 |
| https://github.com/ros-navigation/navigation2/blob/jazzy/nav2_collision_monitor/src/source.cpp | base_shift_correction=true이면 센서 header stamp, 현재시각, global fixed frame 사용하는 Advanced getTransform() | 시간 보정 정확도 위험 때문에 false로 임의 변경 금지 |
| https://github.com/ros2/geometry2/blob/jazzy/tf2_ros/src/buffer.cpp | TF2 canTransform()은 timeout동안 약10ms sleep을 폴링할 수 있음 | 실제 native 호출 내 12회×10ms와 동일 실행 형태. TF availability false→true 확인 |
| https://github.com/ros2/rosbag2/issues/2023 | rosbag2 maintainer는 RMW publication timestamp가 주로 DDS가 제공하는 local UNIX time이고, RMW별 시계 의미를 구분해야 한다고 설명 | 이 공식 논의만으로 현재 Fast DDS 8.4.4 설치 바이너리의 source SYSTEM↔MONO 완전 정합을 승인하지 않음 |
| https://github.com/ros-navigation/navigation2/issues/3402 및 https://github.com/ros-navigation/navigation2/pull/3412 | Advanced/Simple TF 동작과 성능-정확도 트레이드오프 | simple TF 또는 base_shift_correction=false 채택은 이동중 오차 상계·STOP0.40m 여유 및 Guard 검증 전 HOLD |

## 4. 실제 RED→GREEN→REVIEW→COMMIT

**Cycle09-A: 이전 공개 exporter 실패의 정확한 고정 원인 코드**
- 파일: d06/scripts/g07_task01_extract_public_gap.py 및 d06/tests/test_g07_task01_public_evidence_adapter.py. 원본 TF/Clock/CTF를 public artifact로 유출하지 않고 fixed internal reason code만 허용.
- RED [Run #44101072261](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44101072261): 새로운 실패 가설 3건에서 KeyError failure_code.
- GREEN [Run #44101215292](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44101215292): 기존 원본 SHA256 OK + 40/40 ROS-free L0 PASS; adapter 수정 SHA **6804262ebbf3af12b09155b5e1ffe3974f4f82e9**.
- 실제 검증 [Run #44101521543](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44101521543): 기존 public student runtime에서 **한 번의 Gazebo Moving Goal**, 첫 source 위반과 exact TF spans export 성공. 진단은 tracer-ON, 전체 workflow FAIL-closed, root_cause_proven=false/CM120 release=false.

**Cycle09-B: 동일 세션 수치 증거의 공개 보존**
- 공개 source-pinned numeric fixture: d06/evidence/g07_cm120_task01/run_44101521543_native_tf_budget_summary.json.
- 공개 ROS-free unit: d06/tests/test_g07_task01_run44101521543_native_tf_budget.py (3 tests). 실제 first pair 132.917ms source +131.903ms observer, TF 12회 sleep120ms, availability entry false/exit true, Clock mapping 보류, safety flags=false를 동시에 검증.
- RED [Run #44104016325](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44104016325): 원본 수치 fixture absent 3개 에러. 수치 fixture 커밋 **1bfb90efa1d198163c89466f2d00748fbe7c9242**; 첫 L0 검사에는 test 기대문구 오타 1건, [Run #44104173401](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44104173401) 2/3 PASS, FIX 후 [GREEN #44104422640](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44104422640) **43/43 L0 PASS**. 최신 코드 SHA **23c2c5386b646e7f1fc492aee7987dcbfae5e639**.
- 정적 회귀 명령:
  - python3 -m unittest discover -s d06/tests -p test_g07_task01_public_evidence_adapter.py -v
  - python3 -m unittest discover -s d06/tests -p test_g07_task01_run44101521543_native_tf_budget.py -v
  - workflow .github/workflows/axia-g07-task01-real-firstgap-polling-bounds-l0-20261117.yml
- Review: 비공개 repo Action/환경/토큰 0, Docker/공식 Nav2/runtime source 변경 0, STOP0.40/SLOW0.75/Guard150/Scan-Odom-Clock300/Goal owner/TF tolerance0.02/source_timeout1s 그대로. 원본 native TF/Clock tracer 계측은 **진단 한정**이며 tracer-OFF 성능 근거가 아니다.

## 5. 같은 Gazebo 실제 주행에서 입증된 다른 범위

- 단일 Supervisor Goal 발행 및 Nav2 EXECUTING UUID **a63876332f9d45449ed861be50eae35a** 실제 확인; exact UUID terminal 최종 후속 검증은 이번 stdout 만으로 확인되지 않으므로 미검증으로 기록.
- CLEAR, SLOWDOWN, STOP 각각 실제 /scan·CM·최종 cmd_vel 증거 수집 PASS. 실제 이동0.227m, odom ZERO dwell **1.017s**.
- Scan 최대205.953ms, Odom132.147ms, Clock96.922ms, Guard 관찰 주기71.560ms, Supervisor77.278ms. 단, **Guard 내부 CM age 전체 세션 max≤150ms**와 14-topic 전수 custody, S02 Native Contact0 원본은 이번 숫자 summary에서 별도 인수 재검하지 않았다.
- Native navigation_ack=true/localization_ack=true, 공식 CM managed shutdown 후 clean exit 출력 **G07_REAL_SHUTDOWN_L2_CM_CLEAN_EXIT_AFTER_NAV2_ACK_PASS**. original moving runner P2_L2_SMOKE_RC=0, 공개 14-topic rosbag 기록 시작과 핵심 6토픽 실제 message count 확인. 이들은 *특정 run의 개별 통과*이지 전체 CM120 release PASS가 아니다.
- CI 전체는 **diagnostic step에서 의도적 exit 3**, FIRST_RMW_SOURCE_GAP_SELECTED_CAUSE_UNPROVEN, CM120_TRACER_OFF_RELEASE=HOLD. 제품 릴리스/Owner L3 아직 안 됨.

## 6. Task 01 최종 증거 경계 및 향후 한 가지 조건

**새로 PROVEN:** 최초 publisher>120ms와 Observer>120ms가 동시에 있었던 *그 실행*에서, 공식 CM 구독 callback의 한 TF 함수가 **실제 120ms libc polling sleep**을 요청했고, 진입시 가용성이 false→종료후 true로 변했다. TF 내부 wall 시간122.614ms 중 최소120ms를 요청한 sleep이 차지한다. 즉 TF 자체 구간을 'Scheduler 실행 대기 지배'로 설명할 수는 없다.

**계속 UNPROVEN:** 동일 두 publisher SYSTEM source timestamp를 실제 CM 함수 MONOTONIC publish event와 오차 상계가 검증된 형태로 직접 묶는 작업; installed RMW sender epoch의 정확한 시간원; 그 TF2 Buffer Clock의 호출시간대 진행상태; kernel runnable wait ns. Observer pair 겹침과 양단 anchor drift30ns, source1이 TF end 후0.217ms라는 조건부 투영은 **강한 인과 후보**이나, 엄격한 clock mapping과 동일 publication trace가 없으면 publisher SOURCE 최초 위반의 ROOT_CAUSE_PROVEN=true 판정은 보류.

**Task01의 기존 EVIDENCE_EXHAUSTED_HOLD는 실측 증거의 새로운 확보로 업데이트된다.** 경계는 '자료 없음'에서 **'동일 native 호출 120ms TF polling 확인, publisher causal clock alignment 미확정'**으로 좁혀졌다. 증거 확보만으로 Task02의 base_shift_correction=false·scheduler affinity·TTL 변경을 수행하지 않는다.

이후 필요한 딱 한 가지 결정적 증거는 **같은 CM publisher의 source SYSTEM ↔ native CM callback MONOTONIC clock-domain 및 정확한 publish event 귀속을 검증한 bounded 원본**이다. 이를 확보하지 않고 동일 Goal만 반복하는 것은 새로운 정보가 없으므로 금지. CI에서 가능한 NO_GOAL/기존 raw 정적 계약부터 확인할 것. Task02 성능 수정=BLOCKED, Task03 tracer-OFF Gazebo 통합 L2=NOT RUN, Task04 Owner WSL2 L3=NOT RUN. SW STOP ≠ 인증된 E-Stop.

~~~text
AXIA_G07_TASK01_PUBLIC_SAME_RUN_FIRST_SOURCE_BREACH=132.917326MS
AXIA_G07_TASK01_PUBLIC_SAME_RUN_OBSERVER_BREACH=131.903275MS
AXIA_G07_TASK01_SAME_NATIVE_CM_TF_POLL_REQUEST_PROVEN=120.000000MS
AXIA_G07_TASK01_SAME_NATIVE_CM_TF_ENTRY_AVAILABLE=false
AXIA_G07_TASK01_SAME_NATIVE_CM_TF_EXIT_AVAILABLE=true
AXIA_G07_TASK01_SAME_CALL_SLEEP_COVERAGE_PROVEN=true
AXIA_G07_TASK01_PUBLISHER_CLOCK_ALIGNMENT_PROVEN=false
AXIA_G07_TASK01_SCHEDULER_RUNQUEUE_WAIT_PROVEN=false
AXIA_G07_TASK01_ROOT_CAUSE_PROVEN=false
AXIA_G07_TASK01_PUBLIC_L0_REGRESSION=PASS_43
AXIA_G07_TASK01_PUBLIC_DIAGNOSTIC_ONE_GOAL=PERFORMED_FAIL_CLOSED_RELEASE_HOLD
AXIA_G07_TASK02=BLOCKED_CAUSAL_CLOCK_MAPPING
AXIA_G07_TASK03_TRACER_OFF_L2=NOT_RUN
AXIA_G07_TASK04_OWNER_WSL2_L3=NOT_RUN
CM120_TRACER_OFF_RELEASE=HOLD
AXIA_G07_PUBLIC_L2_ACCEPTED=false
AXIA_G07_OWNER_WSL2_L3_ACCEPTED=false
AXIA_MVP_DEMO_ACCEPTED=HOLD
CERTIFIED_ESTOP=false
MAIN_MERGED=false
~~~
