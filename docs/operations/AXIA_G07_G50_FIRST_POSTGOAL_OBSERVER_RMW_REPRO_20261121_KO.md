# AXIA G07 — G50 최근 실제 Gazebo 최초 수신 위반 및 작업 인계

- **기록:** 2026-11-21, 출고 상태 **HOLD**, Owner WSL2 L3 **NOT_RUN**, main **NOT_MERGED**.
- 기준: `AXIA_Robot_Safety_MVP_Baseline_Scenario_Acceptance_v1_KO.md`.
- Public Draft PR [#215](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/215), Student Draft PR [#89](https://github.com/silverbjin/axia-robot-safety-student/pull/89).
- 실제 ROS 2 Jazzy / Gazebo Harmonic / official Nav2, Waffle, Collision Monitor, 자체 Safety Supervisor/Base Guard/Verifier. 인증된 E-Stop이 아닌 교육용 **SW STOP**.

## 1. 변경 전·후 검증 범위

| 스냅샷 | 검증 | 의미 |
|---|---|---|
| Student `5667575aac777c374735b1c351445bcc8f83140e`; Public `09ea6cbc8b9079532ef13c0962d193966e99a03b` | Native [#44902396373](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44902396373) GUI-present **2/2 PASS** | 당시 실제 Goal/Cancel, CLEAR/SLOW/STOP, odom≥1s, Nav/Loc 종료, Depth OFF/Scan 확인 범위만 보존 |
| 별도 headless 실증 [#44903962133](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44903962133) | **0/2 FAIL** | Cycle1 Scan observer discovery absent, Cycle2 Clock333.634ms/Odom357.160ms, Goal 차단 유지 |
| Student `fb1a2010616bc86126858de9322c7d3b44678372` | 실제 Native [#44905877093](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44905877093) **1/2 PASS** | Cycle1 최초 preGoal Clock334.279ms 위반, Cycle2 PASS |
| Student `e1241a2f3cc4fe85412b68ce026c337312d56a02`; Public workflow exact head `6ed4156a5a4e7f720e7767326ce0c172433bc520` | 새 Native [#44907226265](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44907226265): Cycle1 **FAIL**, Cycle2 **PASS** | RED→GREEN Clock/Odom exact-pair 계측 반영. 이번에는 preGoal PASS, **postGoal** 처음 위반. 전체 2/2 인수 불가 |
| Public 최신 HEAD `b686a49492dd241f3d67790ee299286ed87c18b9` | [Python #44907251974](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44907251974) SUCCESS; Runner Canary #44907251955 SUCCESS | 정적·계약 테스트만, 이 최신 HEAD 자체의 새 Native 2/2 검증과 Owner WSL2 실증을 뜻하지 않음 |

## 2. 이번 RED → GREEN → 재실행

- **RED:** [#44906891421](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44906891421) 전체 Python **2 failed / 336 passed / 3 skipped**, 예전 helper가 최초 Clock/Odom 헤더 쌍을 독립 rosbag과 매치하지 못함.
- **Student 구현:** `block_B/day07/h01_runtime/tools/p2_g07_scan_wall_pregoal.py`, commit `e1241a2f3cc4fe85412b68ce026c337312d56a02`. Clock/Odom 최초 300ms 위반의 previous/current simulation stamp 및 정확한 header delta 추가. 원래 300ms 차단은 유지. ROS 노드/토픽 추가 없음.
- **Public 구현:** `d06/diagnostic/g07_scan_rosbag_first_boundary.py` commit `138b6a6081f311fe44659e0ef4891c5417b340f8`; `d06/diagnostic/g07_first_scan_pair_attribution.py` commit `748a6b64df4ecd7863575b1b62ad4b4301657cf6`. 오프라인 rosbag에서 **동일한 첫 Clock/Odom sim-time 두 헤더**만 매치하며 duplicate/missing은 HOLD. 시스템 epoch/monotonic 절대값 혼합 금지. Timestamp가 맞아도 DDS root proven=false, release=HOLD.
- **Public 테스트:** `tests/test_g07_scan_rosbag_first_boundary.py`, `tests/test_g07_first_scan_rmw_evidence_export.py`. 추가 RED [#44907083507](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44907083507) 1 FAIL, 이후 GREEN [#44907143109](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44907143109) 관련 L0 PASS.
- **Native 재실행:** [#44907226265](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44907226265) exact Student `e1241a2f...` 실제 2-cycle, **1/2 PASS**, UI 2/2 observed but GUI itself diagnostic-only. 이 실행에서 최초 preGoal 위반이 재현되지 않았으므로 새로운 Clock/Odom 정확 쌍 비교 분기는 **L0 PASS / Native positive-branch NOT_EXERCISED**. Goal 이후 다른 수신 결함이 발생.
- 사용자 WSL2 직접 실행, `colcon build` 및 `ros2 launch` 실측은 이 Chat 세션에서 수행하지 않음(실행 환경에 Jazzy/WSL2 없음). 대신 위 Native가 실제 컨테이너 Jazzy/Gazebo를 수행한 원본 CI 출처임을 정확히 구분.

## 3. 최초 실제 위반 — Cycle1, Goal 실행 중 STOP 이전

[Native Cycle1 job #136855289444](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44907226265/job/136855289444) 원본 ROS event 및 RMW pair:
- 최초 관측 FSM 전이 `BOOT_SAFE → NORMAL`, host monotonic **837.924096507**, 최초 아래 위반보다 이전. 최초 Guard latch 관측 없음; 따라서 마지막 예외로 최초 전이를 대체하면 안 됨.
- **첫 Odom 위반** host **839.368603139 → 839.734406805**, 간격 **365.803666ms >300ms**. 같은 경계의 Clock **334.970987ms >300**, PreGuard CM Observer callback **364.794637ms >120**, Guard Observer **355.514836ms >150**, Supervisor Observer **358.081536ms >150**, Scan Observer **354.54699ms**(300ms 초과는 **진단**), supervised Observer **358.076771ms**.
- **같은 CM 실제 발행 메시지 쌍:** RMW publisher source interval **55.973048ms**, 독립 ROS 수신 프로세스 RMW received **55.938737ms**, 기존 Observer RMW received **360.35697ms**; RMW publication sequence gap **1**, 일치. 분류 `ORIGINAL_PROCESS_RECEIPT_GAP_CANDIDATE`. CM source publishing stall 증거는 없음; 원래 Observer 소속 Fast DDS/RMW 수신·take/Executor 경계가 의심되나 **최종 root UNDETERMINED**.
- 실제 Observer `first_executor_silence_snapshot`: **179.136383ms**, `executor_spin` stack `_wait_for_ready_callbacks → wait_for_ready_callbacks → _spin_once_impl → spin`, worker 둘 모두 `_worker` 대기. JSON max0.633ms / writer max0.325ms / flush max0.497ms / lock-wait max0.025ms. Callback 파일 I/O가 365ms를 만들었다는 증거 없음.
- **주의:** `heartbeat_max_gap_ms=364.989207`는 **전체 세션 최대값**이며 첫 위반 동일 시간의 지연임을 증명하지 않음. 이전 공개 원본 ZIP `axia_g07_headless_depthoff_44901777431_cycle1.zip`에서는 첫 위반 시 별도 heartbeat 17회, 최대21.357ms로 동작 지속. **process-wide descheduling 확정 금지**.
- 실물 CLEAR 실측 `front_m=2.045054`, Slow `front_m=0.672129, supervised_vx=0.011617, cm_vx=0.003485`, Stop `front_m=0.399944, cm_vx=0, final_vx=0`; 동일 Goal UUID `f0a634b2db1b45ef86768b49fd4096f5` 실제 Cancel, odom zero dwell **1.033788s**. 이 동작들만 개별 관측이며 **formal safety delivery TTL FAIL** 이므로 전체 불합격.
- 최종 exception `ACTUAL_MOVING_GOAL_CI_ORACLE_SAFETY_DELIVERY_TTL_BOUNDARY_max_source_interval_sec`는 최초 오류가 아님. 최초는 **odom 365.804ms**, 그리고 여러 Observer 채널 동시 지연임.

**Cycle2** [job #136855289602](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44907226265/job/136855289602): native runner rc0, `TASK04_REAL_GAZEBO_MOVING_L2_SCOPED_PASS`, Guard/Supervisor child exit0, Depth OFF와 실제 LiDAR/safety Scan evidence PASS. 성공한 원본은 보존, 실패 Cycle을 성공으로 대체 금지.

## 4. 증거 custody

- Run [#44907226265](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44907226265) Cycle1 artifact **14708641486**, GitHub artifact digest **sha256:8d03aa308034fba31b11cde740eb99cbbab1524d5d16d8e1046742866610b327**, 22,445 bytes.
- Cycle2 artifact **14708670690**, digest **sha256:5fb6d763eea7b7acdb09f5c0c4bebc91f9596d8b039a0e486af6c8fa1d750bf8**, 19,446 bytes.
- Numeric artifacts contain `public_evidence/first_delivery_actual_pairs.json`, `public_evidence/independent_cm_pair_verdict.json`, `public_evidence/observer_io_first_boundary.json`, `public_evidence/first_scan_pregoal_boundary.json`, `public_evidence/first_scan_rosbag_exact_pair.json`, `public_evidence/first_scan_rmw_bag_attribution.json`, `native/g07_depth_absence.json`, `native/g07_phase_timings.tsv`. 원본 ROS 14-topic bag은 별도 raw custody, Public ZIP에 포함하지 않음.
- 사용자 PC 원본 파일 경로와 SHA256은 **현장 미실행으로 없음**. GitHub artifact digest는 **개인 WSL2 ZIP checksum이 아님**.

## 5. 다음 최소 개발 범위 및 인수 경계

1. 기존 Goal 중 첫 Observer RMW >300ms / 독립 CM 정상 수신의 동일 시각을 기준으로 Observer spin/waitset, **heartbeat 첫 위반 window**, main thread의 실제 operation을 분리한다. 전체 세션 heartbeat max나 마지막 예외로 원인 단정하지 않는다.
2. 최소 원인이 확인되면 Verifier/실제 수신 경계만 RED→GREEN, ROS runtime 및 승인된 공식 Nav2/CM·안전 제어 수정 금지. Failed bounded20ms/EventsExecutor/Guard wake 등을 무근거 재도입하지 않는다.
3. 실제 Native **동일 SHA 독립 2/2 PASS**와 Clock/Odom300, CM120, Guard150, live Scan freshness 및 실제 Goal/Cancel/odom/14-topic bag/Nav/Loc 종료 증거를 분리 확인해야 새 Owner release를 검토한다.
4. 기존 Owner 스크립트는 이전 실제 GUI-present 2/2 소스 `5667575aac777c374735b1c351445bcc8f83140e`를 **계속 PIN**. 신규 `e1241a2f...`를 Owner로 승격 금지. 강사 WSL2의 실제 TTY 단일 Goal 승인·ROS/Gazebo L3는 아직 수행되지 않았다.
5. WSLg GUI 생성/유지는 정식 인수 게이트 아님. Localization STARTUP ACK timeout은 원본 그대로 기록 + 읽기전용 map_server, amcl ACTIVE와 실제 pose/TF 준비 시에만 전진, 자동 재전송 없음. Nav/Loc SHUTDOWN ACK는 여전히 필수.
6. **USER MAIN MERGE APPROVAL REQUIRED**, 공개 CI 성공만으로 강사 L3 완료 아님.
