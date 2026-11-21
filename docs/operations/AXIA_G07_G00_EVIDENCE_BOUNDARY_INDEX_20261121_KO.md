# AXIA G07 G00 — 최초 안전·타이밍 위반 실증 인덱스 (2026-11-21)

**상태:** G00_EVIDENCE_INDEXED / A_HOLD / B_HOLD / T_HOLD / G30_STRICT_2_OF_2_NOT_PASS / G50_WSL2_NOT_RUN. 정지 기능은 SW STOP이며 인증된 하드웨어 E-Stop이 아닙니다.

## 기준 및 수정 금지

- 공식 baseline: `AXIA_Robot_Safety_MVP_Baseline_Scenario_Acceptance_v1_KO.md`
- User-approved educational G07 baseline: `block_d/release/RELEASE_MANIFEST.json` on main; 별도의 엄격 안전 인수는 아님.
- 통합 개발계획: Public Draft #219 HEAD `5e724bb9acd0fc391165f9e199820837e8703e72`.
- 재사용 Public Draft #215 HEAD `5193b92ef2c4dc00a2d5e92a3f0d6744c4927a26`; Student Draft #89 HEAD `6895f90815fe62a4358abe6b306854af5b8cb6a5`.
- 원래 `MultiThreadedExecutor(num_threads=2)`; Scan/SafetyScan/Odom/Clock 300ms, CM 120ms, Guard 150ms; 정확한 UUID Cancel, Navigation/Localization ACK, 14-topic custody.
- Public #211/#212/#213/#214/#215, Student #83/#84/#86/#88/#89의 실제 코드 재구현 금지. EventsExecutor / SingleThreadedExecutor / 20ms bounded spin_once 0/2 기각, 원인 증명 없는 I/O rewrite 금지.

## 원본 사건 우선순위 (CI 로그 재조회, 별도 ROS/Gazebo 신규 실행 아님)

| Run/실제 job | 최초 실패·안전 상태 | 독립 계측 및 후행 증상 | 판정 |
|---|---|---|---|
| [#44870371777](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44870371777), Cycle 1 | 첫 Odom callback 364.600854ms > 300; 그 전의 Supervisor BOOT_SAFE→NORMAL은 악화 전이가 아님 | 같은 7채널 CM callback 388.878454ms, CM seq+1 Source 50.018636ms / 원 RMW Received 382.004174ms; Observer IO flush 0.165788ms, lock 0.836827ms; 실제 Goal/CM SLOW까지 가능, 후행 TTL oracle FAIL | A_HOLD, 1/2 FAIL, Source 원인 아님 후보 |
| [#44870974857](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44870974857), Cycle 1 | 첫 Odom callback 364.150617ms >300 | CM callback361.513010ms, Source50.456883ms vs 원 RMW Received354.987322ms. 20ms wait 후보 여전히 실패 | A_HOLD, 0/2 FAIL |
| 같은 Run Cycle 2 | Goal 전에 첫 Scan callback 600.502826ms >300, 동일 Header simulation 102ms | 원 Scan Source107.857389ms / RMW Received599.696375ms / seq+1, 독립 ROS bag 같은 헤더 pair 수신107.737729ms; Clock/Odom session max는 첫 Scan pair 동시성 증거 **아님**; Goal 미발행 | A_HOLD, wait/take/Subscriber 경계 미분류 |
| [#44871515361](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44871515361), Cycle 2 | Goal CLEAR 이후 물리 SLOW fixture ACK, 최초 SLOW 양(+) 전진 속도 증명 부족 | front0.6776m, supervised vx <=0.0001208934m/s, 97 samples, odom yaw0.1147→1.5198rad. 후행 Cancel은 성공 SLOW 아님 | B_HOLD, 1/2 FAIL |
| [#44865087050](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44865087050) | 실 Goal CLEAR/SLOW/STOP·UUID Cancel·Nav/Loc ACK 후 26초 관리 launch exit 미확인 | `G07_CI_LAUNCH_LIVE_AFTER_MANAGED_EXIT_BUDGET`; `teardown_processes.txt` raw PID/role은 이 공개 숫자 기록에 없음 | T_HOLD. root 미확정 |
| [#44865216748](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44865216748) | 최초 `CI_MOVING_GOAL_TIMEOUT_SLOW` | Supervisor exit1은 후행 별도 종료 문제, 최초 SLOW 위반으로 소급 금지 | B_HOLD/T 별도 |

**최초 safety state 해석:** 관측된 `BOOT_SAFE→NORMAL`은 악화 상태 전이가 아니다. 동일한 최초 오류 구간의 명시적 `NORMAL→STOP` 또는 Guard latch가 원본에서 확인되지 않았을 경우 `FIRST_UNSAFE_SUPERVISOR_TRANSITION_NOT_OBSERVED`, `GUARD_LATCH_NOT_PROVEN`을 기록한다. 처음 시간 위반이 root라는 주장도 하지 않는다.

**RMW 정확 쌍:** ROS Header stamp 매칭은 Source 생성/sim 주기를 비교하기 위한 것. RMW source/received는 **각자 간격**, callback은 **동일 host monotonic 축의 간격**으로 비교한다. RMW absolute epoch와 host monotonic 절대값을 빼지 않으며, 독립 rosbag 헤더 일치를 DDS GID/sequence 동일성으로 단정하지 않는다.

## 해결 이력과 단계 게이트

- `MessageInfo` callback signature 문제: Student #89, 실제 Jazzy separate ROS L1 #44865731221 Source/Received/Seq 35/35/35 GREEN. 다른 300ms root로 승격 금지.
- D08 실제 same-world YOLO/D05 NO_GOAL 500ms: Public #208 별도 성공. G07 Moving 300ms는 미검증.
- Nav/Loc ACK, AMCL map-TF fallback, SIGINT WaitSet 예외: Student #69 / Public #196/#197/Instructor #197/#202 재사용. 남은 launch 26초는 별도 원인.
- S1/S3/Events/20ms A/B 반복 금지. 기존 D08 rcl take/Gazebo native/독립 ROS probe: Public #180/#201/#206을 G10에서 필요한 부분만 재사용.
- **G10 Gate A:** 최초 Source→RMW→wait→take→callback 어느 경계인지 동일 이벤트 재현으로 분리하고 원인에 따른 최소 RED→GREEN 후 연결된 120/150/300ms 안전 전달 검증; 미확정이면 HOLD.
- **G20 Gate B:** Goal heading/odom yaw/fixture pose/Scan+vx 정렬 증명, 양의 전진 SLOW+실제 감속 및 STOP 확인; 미증명 시 HOLD.
- **G25 Gate T:** `teardown_processes.txt` 잔존 PID·role·termination 원인 증명, 기존 ordered shutdown 최소 재사용, CM/Guard/Supervisor exit0; 미증명 시 HOLD.
- **G30:** 단일 Source Public/Student SHA로 실제 Jazzy/Harmonic Gazebo Moving Goal 독립 cold-run 2/2 및 일곱 채널 safety gate 전부 PASS해야 함.
- **G40:** G30 이전 신규 Owner script 배포 금지, 공개 CI PIN/syntax/self-check/negative test로 WSL2 원샷 검사.
- **G50:** 실제 강사 WSL2 GUI·Goal 수동 승인 1회, 14topic raw bag/해시, Nav2 shutdown/CM+Guard 종료/첫 안전 타이밍 확인. 실행 안 했으면 L3 NOT_RUN.

## 파일 경로 및 기존 실행 명령

- Public: `d06/diagnostic/g07_first_actual_delivery_gap.py`, `d06/diagnostic/g07_first_scan_pair_attribution.py`, `d06/diagnostic/g07_first_postgoal_boundary.py`, `.github/workflows/axia-g07-original-multi-first-scan-rmw-native-l2.yml`.
- Student: `block_B/day07/h01_runtime/tools/p2_g07_ci_moving_goal.py`, `tools/p2_g07_scan_wall_pregoal.py`, `tools/p2_g07_observer_io_probe.py`, `scripts/p2_no_goal_smoke_ci.sh`.
- 기존 CI 실행: `python3 -m pytest -q -ra tests`; `python3 -m unittest discover -s tests -p 'test_g07_first_scan_rmw_evidence_export.py' -v`.
- 새 코드 변경 전후 첫 위반 증명 필요. **이번 G00는 문서·소스 감사이며 신규 L0/L1/L2/L3 시험을 실행한 적 없다.**

## 검증 범위/미검증

G00 로그·소스 감사 COMPLETE. 원본 artifact tar/rosbag bytes와 WSL2 NVIDIA/WSLg 직접 실행은 이번 단계에서 열지 않았다. 처음 600ms RMW read/take의 최초 OS/rcl 원인, 회전 중 SLOW fixture 정합, 26초 종료 잔존 PID는 모두 미확정. 프로그램 소스 및 TTL 변경 없음. 사용자 승인 없는 main 병합 금지.
