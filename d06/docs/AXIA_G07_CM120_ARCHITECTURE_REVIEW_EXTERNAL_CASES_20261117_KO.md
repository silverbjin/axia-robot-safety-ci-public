# AXIA G07 — CM 120ms 아키텍처 리뷰 및 외부 사례 조사

작성 2026-11-17 KST. 범위: 읽기 전용 소스·기존 L2 로그와 공식 Nav2 이슈 연구. 이번 리뷰 신규 ROS, Gazebo, WSL2 실행/코드 수정 없음.
기준 공개 release ef039b7866ab1a83b02dcf0496398a4629f47b02. 비공개 Instructor 강사 정답/원본 ROS·Goal UUID는 공개하지 않음.
기준 문서 AXIA_Robot_Safety_MVP_Baseline_Scenario_Acceptance_v1_KO.md 원문은 이번 조회에서 열람되지 않았음. 기존 실제 오라클로 확인 가능한 범위만 판단함.

## 1. 실제 측정과 실패 경계
- C37 실제 public L2 #43898345608: CM RMW source 128.644215ms, 외부 Observer 128.318661ms; 120ms release margin FAIL. Supervisor 81.858ms, Guard 65.968ms, Scan 217.059ms, Odom 96.791ms, Clock 82.440ms.
- Cycle01 실제 public L2 #43981875149: CM source 133.658796ms, Observer 131.488230ms; Supervisor 89.637ms, Guard 88.471ms, Scan 173.912ms, Odom 82.431ms, Clock 82.443ms. CLEAR/SLOW/STOP, 약 0.20m 주행, 1.01s odom 정지, S02 native Contact0, 14 topics, shutdown/CM exit0는 해당 범위 PASS이지만 release FAIL.
- Guard 내부 CM 150ms hard TTL은 120ms 운영 여유와 분리. 과거 Owner G11 최초 UPSTREAM_STALE_AFTER_MOTION, Guard CM age 158.007666ms >150ms 현장 hard FAIL은 별도 보존. OWNER MOVING GOAL=BLOCKED.
- 두 L2의 첫 CM gap 동안 Supervisor RMW 발행 2건, CM publication sequence delta1. publisher 출력 공백은 실재하나 input callback start와 TF 처리 종료 시각은 미확정. RMW system timestamp와 host monotonic callback timestamp 직접 차감 금지.
- Cycle01 기존 read-only /proc sampler를 기본 비활성화했으나 CM 격차가 더 커져 채택 실패. 대규모 trace/CPU 분리 반복 금지.

## 2. 실제 공식 Nav2 Jazzy 구현과 AXIA 오버레이
- 공식 Jazzy source: nav2_collision_monitor/src/collision_monitor_node.cpp. Twist input callback 안에서 process, sensor getData, velocity publish 순서. cmd_vel 입력 subscriber queue depth=1. CM 출력은 독립적인 frequency timer 아님. 가짜 Twist heartbeat나 임의 추가 발행기는 안전 금지.
- 공식 Jazzy source: nav2_collision_monitor/src/source.cpp. base_shift_correction=true면 sensor stamp->current time advanced TF lookup에 fixed odom frame 포함. false이면 simple source->base TF lookup. scan.cpp에서도 getTransform 수행 후 point 변환.
- 기존 private tools/p2_g07_demo_lidar_overlay.py: 공식 Waffle SDF 임시 복사에서 LiDAR 5->10Hz, odom 30->100Hz. C37/01 실제 로그: AXIA_G07_DEMO_LIDAR_ODOM_5TO10_30TO100_HZ_TEMP_SDF_PASS.
- private tools/p4_g07_cm_tf_bound.py + shared runtime: transform_tolerance 원본 0.20s에서 0.02s로 축소, 실제 /collision_monitor param readback PASS. base_shift_correction/source_timeout 값 변경 안 함. 실제 base_shift_correction 런타임 직접 readback은 이번 증거에 없음.
- **100Hz SDF 설정은 /tf 실제 전달 deadline의 증거가 아님.** 관측된 /odom 최대 callback 지연 82~97ms도 TF odom->base_link age와 동일하지 않음. 각 타임스탬프 원본 비교가 필요.

## 3. 외부 해결 사례 직접 검증
### Nav2 issue #3402 / merged PR #3412
- https://github.com/ros-navigation/navigation2/issues/3402
- https://github.com/ros-navigation/navigation2/pull/3412
- TB3 Gazebo/odom 30Hz에서 advanced lookup의 현재 TF 대기로 cmd_vel 지연. 유지보수자 보고 평균 18,991us/최대 92,719us vs simple 평균 49us/최대 788us (2023년 사례 측정, AXIA 성능 수치 아님). 2023-02-17 공식 PR merged, base_shift_correction 설정으로 두 동작 지원.
- 느린 로봇은 simple lookup이 유리할 수 있으나 움직인 거리를 보정하지 않아 장애물 위치 오차 발생. 저속/scan age/zone 여유 근거 없이 false로 바꾸지 않는다. 보수적 상계의 출발점: positional error <= max_speed * scan_age; yaw error <= max_yaw_rate * scan_age. 실제 측정 전 적용 금지.
### Nav2 issue #4863
- https://github.com/ros-navigation/navigation2/issues/4863
- Jazzy sensor /clock stamp 비동기 때문에 CM source invalid 경고; Nav2 유지보수자는 use_sim_time, zero stamp, 시계동기 검사 권고. AXIA와 같은 실패로 단정하지 않으며 source/receive clock domains를 별도 확인.
### Nav2 issue #3744
- https://github.com/ros-navigation/navigation2/issues/3744
- velocity smoother와 CM의 토픽 배선 순서 문제; upstream 권장 controller -> smoother -> collision monitor -> base. AXIA Guard는 CM 뒤의 별도 안전 계층이며 pre-goal publisher exclusivity 증거가 있으므로 낮은 우선순위, 그래도 배선 회귀 검사 유지.
### ROS 2 tracing
- https://github.com/ros2/ros2_tracing
- ROS2 tracing callback_start/end, rclcpp_publish 이벤트로 executor ready/queue와 실제 실행 시간을 분리 가능. 단 AXIA 기존 Cycle30 trace 2,611,716건 및 CM input callback identity 미확정 사례가 있으므로 또 다른 전체 trace 수집은 금지. 기존 trace에서 one CM PID+handle identity 확인이 가능할 때만 bounded 진단 채택.

## 4. 가설 우선순위와 반증 증거
1. [P1] CM advanced TF lookup/scan-transform 대기: 공식 #3402 관련성 가장 높음. 다만 현재 20ms TF bound와 100Hz odom overlay 이후에도 133ms. 첫 gap 중 실제 input callback entry/exit와 odom->base TF wait를 재검토하지 않으면 인과 UNPROVEN.
2. [P1] CM 구독 depth1/Executor 스케줄링: upstream 발행 2회인데 CM RMW source 133ms gap. callback start 자체가 지연되었는지 TF 내부에서 오래 걸렸는지 분리 필요.
3. [P2] RMW/system-clock jump 또는 DDS transport: source/Observer 각 clock domain을 따로 검사; 두 독립 120ms 초과는 단순 관찰자만의 지연 가설을 약화시키지만 clock jump를 입증/배제하지 않음.
4. [P3] native STOP RPC/GUI competition: 과거 Owner gap은 RPC 종료 435ms 뒤; CI 일부 겹침은 인과가 아님. CPU nice/affinity 재튜닝보다 직접 callback 증거 우선.

## 5. 후속 계획으로 넘길 의사결정 게이트 (이번 리뷰는 구현하지 않음)
- G0 NO GOAL: 기존 원본 SHA/clock-domain/RMW sequence를 대조, 실제 base_shift_correction param·/tf odom->base transform stamp/scan stamp/odom 수신 간격 검증. 없으면 MISSING.
- G1 원인 분리: Supervisor publish->CM subscriber callback start->TF processing->CM RMW source publish->Observer callback->Guard internal receive 동일 Goal/시간창으로 연결. 정확한 내부 시각 없으면 ROOT_CAUSE=UNPROVEN.
- G2 TF 원인이 입증됐을 때만 공식 base_shift_correction false를 G07 sim-only 작은 A/B 후보로 검토. v*age 기반 위험·stop/slow polygon geometry, scan freshness와 150ms Guard 안전 정책 사전 검토. 아니면 timeout/priority/CPU 임의 변경 금지.
- G3 실제 1 Gazebo/Nav2 Goal L2에서 CM RMW source 및 Observer <=120ms, Guard/CM <=150ms, Scan/Odom/Clock <=300ms, real Stop/Contact0/Cancel/14-topic/shutdown 모두 같은 source/Goal PASS 시에만 Owner WSL2 단일 기회 검토.

## 6. 검증 수준 / 명령 / 상태
- Verification: READ-ONLY source review + 이전 public actual L2 raw log retrospective. 신규 CI GREEN/RMW/WSL2 미수행.
- 읽기 전용 확인 명령: gh run view 43898345608 --repo silverbjin/axia-robot-safety-ci-public ; gh run view 43981875149 --repo silverbjin/axia-robot-safety-ci-public
- 미검증: Baseline 원문, AXIA CM 실제 callback entry/exit, TF wait timestamp, base_shift_correction actual readback, WSLg Owner L3, 시연 안전 임계 설계 타당성.
- 현재 판정: CM_ROOT_CAUSE=UNPROVEN; CM_120MS_RELEASE=HOLD; AXIA_MVP_DEMO_ACCEPTED=HOLD; OWNER_WSL2_MOVING_GOAL=BLOCKED; CERTIFIED_ESTOP=false. main merge 없음.
