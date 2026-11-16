# AXIA G07 Cycle 28 — Prearmed Native STOP nice10, 실제 CM 최초 공백 검증

2026-11-16 | 공개 CI 우선 | **최종 결과: L0 GREEN, 실제 Jazzy/Harmonic L2 FAIL, Owner WSL2 미인수, `AXIA_MVP_DEMO_ACCEPTED=HOLD`.**

## 기존 입력 원본 및 바꾸지 않은 인수 조건

- 이전 L2 #43804314391: CLEAR/SLOWDOWN/STOP 실제 Gazebo, CM RMW 원본 source **163.532665ms** >150ms Guard hard, Observer 178.395ms. Native STOP RPC **155.148057ms**, 첫 CM 공백과 monotonic 구간 중첩 true. 해당 STOP RPC가 실제 원인이라는 것은 **미입증**.
- 원래 Owner WSL2 원본: 첫 Guard `UPSTREAM_STALE_AFTER_MOTION`, CM age **174.184617ms** >150ms, CM RMW source gap **186.714207ms**, Native STOP RPC 종료 **435.347732ms 후**에 첫 공백 발생. 따라서 CI STOP RPC 중첩과 현장 실패는 **동일 원인 미확정**.
- 기준: 공식 Collision Monitor 재사용, Guard TTL **150ms 고정**, CM source/observer 출고 목표 **120ms 미만**, Scan/Odom/Clock 300ms hard 및 240ms 출고 목표, S02 native contact 0, exact Nav2 Goal Cancel ACK, ordered localization/navigation shutdown, CM exit0; 소프트웨어 STOP은 인증된 E-Stop 아님.

## RED→GREEN→REFACTOR→REVIEW→COMMIT

- 비공개 Instructor 브랜치: `fix/g07-cycle28-prearmed-stop-lower-latency-20261116`. 소스 `tools/p4_g07_prearmed_stop.py`만 Native STOP 보조 프로세스 priority `nice +19 → nice +10` (직전부터 준비된 단일 helper, 마지막 CPU, 실제 Goal 중 새 CLI spawn 불가)로 변경. Goal 승인, Safety Supervisor, Guard, 공식 CM 파라미터는 그대로. 기존 Test `tests/unit/test_p4_g07_goal_observer_cpu_parity_20261115.py` 기대값과 신규 `tests/unit/test_g07_cycle28_prearmed_native_stop_priority_parity_20261116.py` 수정.
- 정확한 private 후보 SHA `c1d778c0f8ad68837487b65fc4f8557aef842887`.
- RED 공개 sealed [Run 43805186813](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43805186813): 신규 nice10 요구와 기존 nice19 구현 충돌로 예상 FAIL.
- GREEN 공개 sealed [Run 43807359414](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43807359414): **16/16 PASS** = 신규 priority 3, 기존 observer CPU 5, first CM /proc 8. Ubuntu24, **NO ROS/NO GOAL**.
- 실제 L2 [Run 43807492492](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43807492492) 워크플로 head `3f09ffc0753d8344dcf7ec2720441e645ed9e0ba`, Instructor pin `c1d778c0f8ad68837487b65fc4f8557aef842887`: **FAIL**. actual Gazebo Harmonic GUI Xvfb/RViz, 공식 Nav2·TB3 Waffle 한 Goal 수행.
- **원본 최초 문제:** CM RMW source gap **156.345327ms** >150ms, source sequence delta1, gap 중 Supervisor RMW 3회 (최대 source coverage 49.784693ms), CM observer interval **133.611298ms** >120ms. Native STOP RPC **109.705409ms**, 첫 CM RMW source gap과 monotonic observation window 중첩 true. 이는 동시성 관찰이며 **인과 미증명**.
- 7채널 관측자 간격: source **76.140ms**, CM **133.611ms**, Guard **76.405ms**, Supervisor **93.409ms**, Scan **183.201ms**, Odom **135.066ms**, Clock **99.104ms**. CM만 release 120ms 초과; source RMW 또한 hard150ms 초과. `AXIA_G07_CI_FIRST_120MS_CM_SUPERVISOR_RMW_WINDOW`→`CM_SOURCE_GAP_EXCEEDS_120MS`; `AXIA_G07_CYCLE27_FIRST_CM_120MS_SOURCE_RPC`→`CM_SOURCE_120MS_GAP_OVERLAPS_RPC_HOLD`.
- 런타임 관측은 CLEAR→SLOWDOWN→STOP, Nav2 Goal Cancel ACK 및 navigation/localization shutdown ACK, CM exit0, S02 native physics contact **0/32813**, 14-topic rosbag original custody가 성공. **그러나 CM TTL 위반 때문에 전체 L2 FAIL**.
- CM /proc 최초 120ms 공백 후보 구간 101.855ms sampling, CM thread aggregate run **1.216ms**, wait **3.111ms**, 3 samples, 16 threads, `FIRST_CM_120MS_GAP_SCHEDULER_VS_EXECUTION_UNDETERMINED`. CM 입력 callback·TF lookup 내부 경계는 아직 직접 계측하지 못함; CPU 경합이나 RPC 원인을 확정하지 않는다.

## REVIEW / 미검증 및 다음 단일 경계

- Nice10 후보는 Native STOP RPC 시간을 155.148→109.705ms로 줄였으나, 실제 CM source 최대 gap은 156.345ms로 여전히 hard TTL을 넘었음. 성공 보고·Owner 출고 **금지**.
- Cycle29에서는 기존 공식 Jazzy `ros2:rclcpp_callback_register`, `ros2:callback_start/end`의 LTTng capability L1을 재사용하여 CM 구독 callback의 실행 시간과 동일 목표의 **첫 CM output source gap**을 상대 monotonic 기준으로 결합한다. 해당 경계가 확인되기 전 임의 Guard TTL 완화/Goal 재시도/추가 Node 구현은 하지 않는다.
- 새 actual ROS/Gazebo L2 GREEN과 7채널 하드·출고 여유, S02 contact0, exact Cancel+Shutdown 모두 증명되어야만 새 Instructor SHA/CI Run을 고정한 WSL2 TTY 수동 Goal 원샷을 배포한다.
- Owner 기존 실패 archive·단일시도 lock 보존, 강사용 답안은 비공개, 학생 TODO 분리, 공개 CI에 Goal UUID/원본 bag/솔루션 올리지 않음. `main` 병합은 사용자 승인 전 하지 않음.

**최종: `AXIA_MVP_DEMO_ACCEPTED=HOLD` / `OWNER_GOAL_RELEASE=BLOCKED`; WSL2 시연 인수 원샷 미배포.**
