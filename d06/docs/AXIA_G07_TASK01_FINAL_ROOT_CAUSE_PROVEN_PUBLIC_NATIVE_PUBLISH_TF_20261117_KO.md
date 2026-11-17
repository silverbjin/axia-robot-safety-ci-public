# AXIA G07 Task 01 — 최종 원인 규명과 공개 CI 인계

2026-11-17 KST. **Task01 범위 완료: 최초 CM RMW 발행 공백의 TF polling 원인 입증. 전체 CM120 tracer-OFF 시연은 HOLD.**

## 1. 단일 최초 실패 경계와 엄격한 범위

공개 실제 Gazebo Run [#44109119429](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44109119429), job 134129577686, 실제 CI diagnostic SHA 28c5e41e3c13be3df7bd6bc83579a85a32a41927, 실제 로봇 소스 silverbjin/axia-robot-safety-student@6a3047b5aa219687f5fc918e467cea5115d3d482.

| 같은 실행의 실제 측정값 | 값 |
|---|---:|
| 첫 연속 CM publisher RMW source 간격 | **172.590315ms**, 허용120ms 위반 |
| 동일 출판 seq의 Observer 간격 | **173.162403ms**, 허용120ms 위반 |
| 정확히 동일 두 native Fast DDS rmw_publish tracepoint 간격 | 172.591647ms |
| Native timestamp→RMW SYSTEM source 일치 최대 잔차 | **3,295ns** |
| Native source publisher 간격과 관측 source 간격 차 | **1,332ns** |
| 두 native 발행 사건 사이, 동일 공식 CM callback의 Advanced TF 호출 | **122.282121ms** |
| TF 내부 libc sleep 요청 및 실제 경과 | **12회 × 10ms = 120.000000ms**, 실제121.275953ms |
| 동일 TF 스레드 CPU / TF 종료→둘째 native publish | 1.145286ms / **0.161663ms** |
| 첫 RMW source 공백에서 확인된 자발적 TF sleep 요청 비중 | **69.5288%** |
| 동일 TF 가용성 | 입력 전 false → 호출 후 true, per-call sleep coverage complete |
| 가장 먼저 관찰한 Guard 안전 래치 | UPSTREAM_STALE_AFTER_MOTION, CM age **156.944056ms >150ms** |

**원인 결론:** 해당 최초 publisher source 간격에서 공식 Advanced TF 변환의 실제 가용성 폴링이 최소120ms를 점유하므로, 단순한 Linux scheduler runnable 큐 대기가 아니라 실제 TF polling sleep이 첫 발행 공백의 지배 원인이다. 나머지 약52.590ms의 구성과 scheduler 실제 runnable wait ns는 **UNAVAILABLE**, 0ms라고 주장하지 않는다. 앞선 Guard 래치와 정확히 어떤 RMW 출판 seq가 시간상 맞물렸는지는 별도 원본 증거가 없어 **UNVERIFIED**, 다른 안전 경계 PASS로 승격 불가.

**주의:** 전체 원본 CI는 FAIL. 공식 주행은 Nav2 Goal EXECUTING UUID d1b951e8ec394f5aa130195545065158 이후 Guard가 실측 CM age 156.944ms에서 UPSTREAM_STALE_AFTER_MOTION으로 안전 래치했고, 원본 moving runner P2_L2_SMOKE_RC=2. 원래 CM120 동작이나 L2 시연은 합격하지 않았다.

## 2. Fast DDS / Nav2 Jazzy 공식 코드 및 Issue 검토

| 공식 근거 | 직접 확인한 계약 | 적용 판단 |
|---|---|---|
| [Jazzy rmw_fastrtps_shared_cpp rmw_publish.cpp](https://github.com/ros2/rmw_fastrtps/blob/jazzy/rmw_fastrtps_shared_cpp/src/rmw_publish.cpp) | Time_t::now(stamp)→TRACETOOLS_TRACEPOINT(rmw_publish, ..., stamp.to_ns())→write_w_timestamp(...,stamp). **같은 source timestamp가 tracer와 DDS DataWriter에 전달** | 기존 수신 MessageInfo의 source timestamp를 실제 네이티브 출판 tracepoint에 직접 대조 |
| [Jazzy ROS2 tracetools](https://github.com/ros2/ros2_tracing/blob/jazzy/tracetools/include/tracetools/tracetools.h) | rcl_publisher_init의 topic/rmw handle, rmw_publish의 handle/message/timestamp | CM input subscription→callback와 출력 /cmd_vel_pre_guard의 publisher handle을 유일성 검사 |
| [Jazzy CM standalone main](https://github.com/ros-navigation/navigation2/blob/jazzy/nav2_collision_monitor/src/collision_monitor_main.cpp) | 공식 독립 CM 실행 파일은 rclcpp::spin(node->get_node_base_interface()) | 공개 원본 student runner에서 실제 use_composition:=False로 실행, standalone 단일 executor 기본 경로 |
| [Jazzy CM node](https://github.com/ros-navigation/navigation2/blob/jazzy/nav2_collision_monitor/src/collision_monitor_node.cpp) | cmdVelInCallback → process → 센서 TF getData → publishVelocity | 같은 input callback에서 TF 폴링이 출판 전에 일어남 |
| [geometry2 Jazzy Buffer](https://github.com/ros2/geometry2/blob/jazzy/tf2_ros/src/buffer.cpp) | canTransform의 10ms 반복 sleep | 실제 12개×10ms native 요청과 동일 |
| [Nav2 Issue #3402](https://github.com/ros-navigation/navigation2/issues/3402), [병합 PR #3412](https://github.com/ros-navigation/navigation2/pull/3412) | Advanced TF 조회 지연 및 Simple TF 전환의 성능·시간보정 정확도 절충 | Task01에서 base_shift_correction=false로 임의 변경하지 않음; 안전 오차 검토 후 Task02에서만 수정 검토 |
| [Linux schedstats](https://www.kernel.org/doc/html/latest/scheduler/sched-stats.html) | runnable wait는 per-thread 커널 stats 필요 | 실제 구간 scheduler_wait=UNAVAILABLE, zero로 추정 금지 |

원본 publisher의 RMW SYSTEM epoch와 CM MONOTONIC을 단순 host anchor 차감하여 결합한 것이 아니다. **정확히 두 native rmw_publish timestamp와 동일 두 Subscriber source timestamps를 먼저 매칭**한 뒤 각 native publish CTF clock snapshot의 보정 잔차가 최대3.295us이고 source/native interval 차1.332us임을 검증했다. 그 후 callback 내 TF sleep120ms가 두 publish 사이에 포함됨을 확인했다. 따라서 Scheduler 실행 대기가 동일 첫 source gap의 지배 원인이라는 가설은 반증된다.

## 3. 원본 증거 SHA256 custody

- 직접 내려받아 검증한 GitHub Actions 공개 artifact ID **14339398674**, ZIP byte size **3,998**.
- ZIP SHA256: **f12edca803bcc3eb5377ff4b856afabf901cbbf588afd3c680b75b02f4e18c9f**.
- 원본 first_gap_sanitized.json **9,972 bytes**, SHA256: **383ce756a50e136eaeb2eab83e8c10d174f280bbbe2c43f4075d754df380f3bd**. ZIP 내부 SHA256SUMS.txt와 일치.
- 공개 숫자형 파생 증거: **d06/evidence/g07_cm120_task01/run_44109119429_publisher_causality.json**, artifact ID·해시·Goal runner status·Guard 최초 래치 포함. PID/TID, 포인터, 원시 /scan·TF message·bag·개인정보는 공개하지 않았다.
- 과거 별도 source gap129.299ms/TF sleep90ms Run #44049067368, 이전 Cycle09 132.917ms/TF sleep120ms Run #44101521543를 이번 원인의 새로운 시간 동기 인과로 합성하지 않는다. 이번 결론은 **Run #44109119429 하나의 실행**에 기반한다.

## 4. RED → GREEN → REFACTOR → REVIEW → COMMIT

| 단계 | 실제 공개 CI | 정확한 검증 |
|---|---|---|
| 첫 실제 publish-source causal join 최소 테스트 RED | [#44108297539](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44108297539) | source stamp→native RMW publisher→CM 콜백/TF 연결 검사기 부재 |
| publisher handle·stamp·callback·epoch 매칭 GREEN | [#44108733720](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44108733720) | 유효 입력 허용, 잘못된 timestamp/발행자/clock/스레드 거부 |
| 다른 CM worker TID 가능성 부정 RED | [#44109382155](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44109382155) | 여러 CM callback worker의 TF span을 같은 publisher thread로 잘못 판단할 위험 재현 |
| worker ownership fail-closed GREEN | [#44109552577](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44109552577) | classifier SHA **824a87a477c5e997f3ff37953cc7fa6f80d72e26**, 기존 **48/48 ROS-free PASS** |
| 실제 Gazebo tracepoint capture | [#44109119429](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44109119429) | source172.590ms / native172.592ms / TF sleep120ms, 동일 publisher exact match. **동적 Goal 실행 실제, 전체 L2 FAIL** |
| 실제 증거 고정 RED | [#44110472635](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44110472635) | 원본 SHA 고정 수치 원장 부재 |
| 실제 증거 고정 GREEN | [#44110623145](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44110623145) | 원장 commit **232072edcb67b05e5bb20b94e446d0bc69404db1**, **51/51 L0 PASS**, 이전 공개 숫자 JSON SHA256 체크 PASS |

**REVIEW:** 실제 Gazebo run은 multi-worker ambiguity negative regression을 넣기 전 SHA에서 수행했으므로 소스 SHA를 임의로 사후 변경하지 않는다. 별도 공식 Jazzy standalone main와 실제 public runtime use_composition:=False를 대조하여 해당 실행의 callback threading 계약을 확인했다. 모든 새 코드는 기존 public CI의 진단기·수치 exporter·단위테스트뿐. 새로운 ROS 노드/Goal publisher, Nav2 fork, 안전 TTL/QoS/STOP 설정 변경 **없음**. 추가 Moving Goal 재실행하지 않음.

변경 파일:
- **d06/diagnostic/classify_cm_rmw_publish_join.py**: 정확한 동일 CM native RMW source publish·TF poll 최초 공백 분류.
- **d06/scripts/g07_task01_extract_public_gap.py**: 기존 LTTng에서 rcl_publisher_init/rmw_publish 두 읽기 전용 이벤트를 추가해 원시 포인터 비공개 상태로 연계.
- **d06/tests/test_g07_task01_exact_rmw_native_pub_link.py**, **d06/tests/test_g07_task01_run44109119429_native_publisher_source_join.py**.
- **d06/evidence/g07_cm120_task01/run_44109119429_publisher_causality.json**.
- **.github/workflows/axia-g07-task01-public-only-one-diagnostic-l2-20261117.yml**, **.github/workflows/axia-g07-task01-real-firstgap-polling-bounds-l0-20261117.yml**.

공개 CI 실제 실행 명령: python3 -m unittest discover -s d06/tests -p test_g07_task01_exact_rmw_native_pub_link.py -v ; python3 -m unittest discover -s d06/tests -p test_g07_task01_run44109119429_native_publisher_source_join.py -v ; 기존 51개 ROS-free 회귀 workflow + 원본 SHA256 체크. 실제 ROS2 Jazzy/Gazebo single Goal은 해당 public workflow에서 timeout --signal=TERM --kill-after=10s 900s bash scripts/p2_no_goal_smoke_ci.sh (기존 student 원샷)로만 실행.

Git 작업 브랜치 **fix/g07-cm120-task01-clock-firstgap-causality-20261117**, Draft **PR #161**, main 병합 없음. private Instructor CI 사용 안 함.

## 5. Task별 종료 판정

**Task01 = COMPLETE_SCOPED_CAUSAL_PROOF:** 이 실제 최초 publisher 공백은 공식 Advanced TF 10ms polling이 직접 최소120ms 소모하여 지배함을 네이티브 발행 사건까지 증명했다. Linux runnable 스케줄러의 나머지 기여, 모든 실행에 동일 원인이 재발한다는 일반화는 미증명.

**Task02 = READY_FOR_ONE_MINIMAL_SAFETY_REVIEWED_FIX, NOT RUN:** 단 하나의 성능 수정안을 공식 Nav2 동작·시간 보정의 정확도 및 0.40m STOP/0.75m SLOW 여유와 함께 검토하고, 실제 공개 CI에서 CM publisher/Observer 120ms뿐 아니라 Guard150ms, Scan/Odom/Clock300ms, source→CM→Guard 연결 및 최초 Guard 래치 경계까지 동일 SHA로 RED→GREEN 검증한다. 근거 없는 base_shift_correction=false, affinity, TTL 완화 금지.

**Task03 = tracer-OFF real Gazebo L2 NOT RUN**, 동일 release SHA의 정확한 Goal UUID terminal, Navigation/Localization ACK, CM clean child exit0, 14-topic 원본 및 S02 Contact0, CLEAR/SLOW/STOP/odom dwell≥1s과 안전 TTL 확인이 필요.

**Task04 = Owner WSL2 L3 NOT RUN.** CI 51/51은 **L0만 PASS**이다. 실 Gazebo Task01 진단은 원인 증명에는 성공했어도 Guard 첫 stale 상태 전이로 **L2 전체 FAIL**. SW stop은 certified E-Stop이 아니다.

## 판정용 문자열

AXIA_G07_TASK01=COMPLETE_SCOPED_CAUSAL_PROOF

AXIA_G07_TASK01_FIRST_SOURCE_GAP_MS=172.590315

AXIA_G07_TASK01_NATIVE_PUBLISH_SOURCE_PAIR_MATCH=PROVEN

AXIA_G07_TASK01_NATIVE_TF_SLEEP_REQUEST_MS=120.000000

AXIA_G07_TASK01_NATIVE_PUBLISH_SOURCE_CLOCK_MAX_ERROR_NS=3295

AXIA_G07_TASK01_SCHEDULER_RUNQUEUE_WAIT=UNAVAILABLE

AXIA_G07_TASK01_PUBLIC_L0_REGRESSION=PASS_51

AXIA_G07_TASK02=NOT_RUN_READY_FOR_ONE_MINIMAL_FIX

AXIA_G07_TASK03_TRACER_OFF_L2=NOT_RUN

AXIA_G07_TASK04_OWNER_WSL2_L3=NOT_RUN

CM120_TRACER_OFF_RELEASE=HOLD

AXIA_G07_PUBLIC_L2_ACCEPTED=false

AXIA_G07_OWNER_WSL2_L3_ACCEPTED=false

AXIA_MVP_DEMO_ACCEPTED=HOLD

CERTIFIED_ESTOP=false

MAIN_MERGED=false
