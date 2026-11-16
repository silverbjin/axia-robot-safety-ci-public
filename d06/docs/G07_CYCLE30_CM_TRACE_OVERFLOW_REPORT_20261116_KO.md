# AXIA G07 Cycle 30 — 실제 CM 최초 공백 LTTng 50만 건 파서 오류의 공개 CI 회귀

작성일 2026-11-16. 기준: ROS 2 Jazzy, Gazebo Harmonic, 공식 Nav2 + TB3 Waffle; 시연 MVP. **현재 AXIA_MVP_DEMO_ACCEPTED=HOLD**.

## 실제 최초 실패

- 실제 GUI Harmonic·Nav2 단일 Goal [Run 43809629649](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43809629649)은 7채널 CM 120ms release margin **FAIL**. CM RMW source **140.890192ms** / Observer **137.395864ms**. 동일 공백에 Supervisor 원본 메시지 3개, upstream max gap 50.085249ms. Guard 최초 latch 없음, 정확한 취소/정상 종료 증거와 CI 120ms 출고 성공은 별개.
- LTTng raw callback trace step이 단일 CM 프로세스가 아닌 **모든 ROS 노드의 callback**을 500000건까지 리스트에 저장하고, 초과 시 `AXIA_G07_CYCLE29_TRACE_EVENT_COUNT_UNBOUNDED_HOLD` (exit3). 이 진단 파서의 최초 오류 때문에 **실제 공식 CM 입력 callback 시간**을 확보하지 못했다. CM callback·TF·스케줄러 원인을 입증하지 못한 상황에서 안전 코드 수정/WSL2 Goal 배포 금지.
- 이전 실제 CI [Run 43792753212](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43792753212) CM source142.776ms, [Run 43794087620](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43794087620) source142.906ms. CPU 코어 분리만으로 개선되지 않았음. WSL2 원본 186.714ms/Guard174.185ms >150ms는 보존.

## RED→GREEN 검증 및 코드

- 공개 dev 브랜치: `fix/g07-cycle30-bounded-cm-trace-20261116`, `main` 미병합.
- RED [Run 43812184277](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43812184277): 실제 50만 건 초과 재현 Fixture `d06/tests/test_g07_cycle30_bounded_cm_trace.py`; 필터 모듈 미구현.
- GREEN [Run 43812355586](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43812355586): Ubuntu 24.04 public CI **7 신규 + Cycle29 기존 8 = 15/15 PASS**, `AXIA_G07_CYCLE30_TRACE_CM_PID_BOUNDED_L0_PASS_NO_ROS_NO_GOAL`.
- 모듈 `d06/live/g07_cycle30_bounded_cm_trace.py`: LTTng `bt2` 이벤트 iterable을 **지연 평가/단일 스트림**으로 받음. exact owner CM vpid만 보존; 실제 첫 120ms CM output RMW source seq consecutive pair의 Observer MONOTONIC 시간 창 전후 300ms callback start/end와 CM registration event만 메모리에 보존. 다른 PID 50만 건이 있어도 실패하지 않음. 동일 CM 창 자체가 40000개 callback 또는 2048개 등록 이벤트를 초과한다면 **HOLD**, 임의 truncation 없이 fail-closed. `wall_ns-mono_ns` anchor drift >=50ms 또는 RMW seq/source gap provenance 불명확하면 HOLD.
- 공개 릴리스 실제 L2 workflow `.github/workflows/axia-g07-unified-gui-one-goal-l2.yml`의 Cycle29 trace step만 이 도구로 전환, pinned public code `5f0ca47ed9f60378be2bac323f4a9f1710174e08`. 다른 private Instructor source, safety threshold, STOP/Goal logic, native Gazebo runtime digest는 바꾸지 않음.
- 실제 CI Goal [Run 43812555906](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43812555906): 진행 중인 별도 L2 확인 대상. 이 L0 보고만으로 L2 PASS나 Owner WSLg ACCEPTED를 주장하지 않음.

## 검증 범위/미검증 항목 및 향후

**PASS:** synthetic >500k unrelated vpid 처리, 실제 1개 CM vpid/window 보존, registration identity 보존, callback limit fail-closed, monotonic/wall-anchor/time order fail-closed, 15/15 공개 Ubuntu24 noROS L0. 사용자 원본/Lock 보존, certified E-Stop 아님.

**아직 미검증:** Run 43812555906의 실제 trace extraction, first callback duration/TF 원인, CM<120ms release를 만족하는 G07 실제 Gazebo L2, WSLg Owner L3. 실제 L2 trace가 CM callback long인지 executor/scheduler delivery인지 확인한 후에만 단일 최소 안전 런타임 수정 후보를 RED→GREEN으로 검증. 이후 최초 Guard latch, 7채널 TTL(Guard CM hard150ms, CM release120ms, Scan/Odom/Clock), S02 contact0, Goal cancel exact ACK, ordered Nav2 shutdown, CM exit0. 통과 전 WSL2 moving Goal 원샷 배포 금지.

**판정: AXIA_MVP_DEMO_ACCEPTED=HOLD / OWNER_MOVING_GOAL_RELEASE=BLOCKED.**

## 실제 L2 실행 결과 (Cycle30 closure)

- 실제 Harmonic/Nav2/Xvfb 동일 private source SHA `c1d778c0f8ad68837487b65fc4f8557aef842887` [Run 43812555906](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43812555906) **전체 FAIL**, **trace 메모리 처리 자체는 PASS**.
- 실제 로그 `AXIA_G07_CYCLE30_TRACE_STREAM_BOUNDED {"global_ros_events_scanned":2611716,"other_pid_ros_events_ignored":2487077,"owned_cm_callback_events":849,"owned_cm_registration_events":817,...}`. **전체 2,611,716건을 500k 배열 제한에 걸리지 않고 한 번 처리**.
- CM 최초 RMW source gap `134.064157ms > 120ms`, observer callback `129.247994ms`, Supervisor source 발행 3건 (max coverage 50.290314ms). Native STOP RPC duration `114.246702ms`와 최초 공백의 **시간상 중첩 후보**. 인과 입증 아님.
- `AXIA_G07_CYCLE29_OFFICIAL_CM_CALLBACK_FIRST_GAP`: `registered_callback_count=30`, `registered_cmdvel_callback_count=0`, `cm_finished_callback_count_near_first_gap=115`, `cm_any_callback_max_duration_ms=113.649394`, `cm_cmdvel_callback_count_near_first_gap=0`, status `CM_CALLBACK_IDENTITY_UNVERIFIED_HOLD`. **콜백 이름으로 /cmd_vel_supervised 구독을 식별할 수 없었음**.
- 안전 결과: 실제 CLEAR/SLOW/STOP 및 Nav2 Shutdown ACK 확인; `AXIA_G07_FIELD_REAL_L2_SEVEN_CHANNELS cm=0.129247994`; **CM120ms 출고 margin FAIL**, Guard latch 없음. Owner WSL2 Goal 새로운 배포 금지.
- NEXT Cycle31: ROS2 Jazzy 공식 `rcl_subscription_init / rclcpp_subscription_init / rclcpp_subscription_callback_added` 토픽→핸들 연결 계측으로 직접 CM 입력 콜백을 식별. 안전 TTL/공식 Nav2 소스 수정·원본 재주행 없음.

**Cycle30 종료 판정:** `CI_TRACE_STREAMING=PASS`, `CI_REAL_L2_RELEASE_MARGIN=FAIL`, `OWNER_WSL2_ONE_SHOT=NOT_READY`, `AXIA_MVP_DEMO_ACCEPTED=HOLD`.
