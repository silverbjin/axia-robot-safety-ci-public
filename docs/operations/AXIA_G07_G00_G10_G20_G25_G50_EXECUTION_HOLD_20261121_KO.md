# AXIA G07 — G00→G50 현재 실행 증거 및 인수 HOLD 판정 (2026-11-21)

## 범위·기준

- 기준: `AXIA_Robot_Safety_MVP_Baseline_Scenario_Acceptance_v1_KO.md`, Public final plan Draft #219 (5e724bb9acd0fc391165f9e199820837e8703e72).
- 작업 분리: Public Draft #221 `fix/g07-g50-first-boundary-ci-20261121`, Student Draft #94 `fix/g07-g50-first-boundary-student-20261121`. 강사 private 강의 정답/개인 rosbag은 공개하지 않는다.
- 현재: G00 증거 인덱스 완료; G10 계측 L0/L1 GREEN 하지만 **root 미확정**; G20 물리 fixture entry 보강 L0 GREEN, **실제 native SLOW/STOP 미검증**; G25 최초 종료 process 분류 L0 GREEN, **26초 잔존 PID 실증 원인 미확정**. G30 독립 Moving 2/2 PASS 없음, G40 새 Owner one-shot 미출고, G50 WSL2 실제 NOT_RUN. RELEASE=HOLD.
- 기존 교육용 G07 Baseline `block_d/release/RELEASE_MANIFEST.json`는 유지. 본 실험은 새 공식 안전승인/인증 E-Stop 아님.

## G00 — 원본 증거 감사 완료

`docs/operations/AXIA_G07_G00_EVIDENCE_BOUNDARY_INDEX_20261121_KO.md`, Public `68608f2205a0a6fc00fabfb458996ae23b46149c`. 실제 native:
- #44870974857 Cycle2: 최초 Goal 前 Scan callback **600.502826ms >300**, 동일 Header sim **102ms**, RMW Source **107.857389ms**, 원 RMW Received **599.696375ms**, 독립 rosbag 동일 Header 수신 **107.737729ms**, seq+1; Clock callback 9회와 Odom callback 1회가 그 공백 내부에 존재. 전체 프로세스 정지·DDS/Executor root 입증 금지.
- #44870371777 Cycle1: 최초 Odom 364.600854ms; CM Source50.018636ms/Received382.004174ms/Observer388.878454ms; lock/write/flush 1ms 미만. BOOT_SAFE→NORMAL은 안전 악화 상태 전이가 아님.
- #44871515361 Cycle2: SLOW cylinder ACK 이후 실제 전방 0.6776m, supervised 음수, yaw0.1147→1.5198 rad, 97 샘플 중 SLOW 구간 최대 전진속도0.0001208934m/s, 엄격 양의 전진 SLOW 미통과.
- #44865087050: Goal CLEAR/SLOW/STOP→UUID Cancel→Nav/Loc ACK 후 26초 관리 launch PID 생존. 실제 잔존 PID role은 기존 numeric artifact에서 미수집.

## G10 — 실제 ROS Jazzy 계측 보강, 안전 원인 미해결

- Public `d06/diagnostic/g07_g10_multichannel_causal_stage.py` / `tests/test_g07_g10_first_multichannel_causal_stage.py` / `.github/workflows/axia-g07-g10-first-boundary-l0.yml`.
- **실제 RED** #44876314311 (누락 분류기) → **GREEN** [#44876350616](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44876350616) `Ran 4 tests / OK`; Public `7619221ebdbe44ad2dd5f7be5c0001ba77ded2fe`. 전 stream 중복/시계 절대값 혼합/누락 seq·Header는 HOLD.
- 기존 Public D08 #201 (`d08/harness/d08_rcl_take_dispatch_probe.py`)를 **재구현하지 않고** Student `tools/p2_g07_scan_take_first_pair.py`, `p2_g07_scan_wall_pregoal.py` CI-only opt-in에 연결. 실제 Jazzy 프로세스 2개, 300Hz Clock/10Hz Scan, NO_GOAL L1. 첫 RED #44877378675 환경 PYTHONPATH overwrite → GREEN [#44877500899](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44877500899): `scan=35 clock=1049 take=35 callback=35 exact_header_join=35 callback_gap_max_ms=101.452`. Public `c8fdb10015e293f3be83291c90ecb2eb77e65803`.
- G10 root remains **UNDETERMINED**: no same-fault 600ms actual probe at wait-set/native rcl_take; native Gazebo/RMW bridge test never claimed PASS. Original MultiThreadedExecutor 2-worker stays; rejected 20ms bounded wait / EventsExecutor / SingleExecutor experiments not adopted in release.

## G20 — 실제 SLOW 거부 조건부터 수정 (스코프 보존)

- Student `block_B/day07/h01_runtime/tools/p2_g07_ci_slow_entry.py`, `p2_g07_ci_moving_goal.py`, `test_g07_ci_slow_forward_entry.py`. 기존 실제 set_pose 및 엄격 SLOW/STOP 검사/Goal/Fault/안전 TTL 수정 없음.
- 최초 실제 Native [#44876802910](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44876802910), Public `f6f438f87319d5193381ee53c87e70b29518f931`, Student `196310a2a92e4c0b01e643293d9725561b384dd3`: 12초 pregoal PASS, 실제 Goal EXECUTING, CLEAR vin0.03762598m/s + odom0.1201586m 완료. 새 fixture gate 0.05m/s를 충족 못 해 `CI_MOVING_GOAL_TIMEOUT_SLOW_ENTRY_FORWARD`, 물리 SLOW 배치 *전* FAIL. 성공 판정 금지.
- bounded first reason 추가 RED [#44877197366](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44877197366)→GREEN [#44877261269](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44877261269) 8/8.
- 추가 실제 Native [#44877303360](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44877303360), Public `30602b281df799343988bf34811b6dfc56c497ef` (Student `f6b77dd6ab0f3e8427825ffe7c5508afaec7d1ad`) **FAIL**. 첫 차단 `SUPERVISED_FORWARD_BELOW_ENTRY_GATE`, 실패 종료 시 vin0.018827m/s, 실제 CLEAR vin0.03763954m/s, 부모 최종 rc2. 기존 CLEAR >0.03보다 **추가 0.05 조건이 과도**.
- 정확한 실제 CLEAR 양의 진입 조건으로만 정렬: RED [#44877613136](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44877613136) → GREEN [#44877658981](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44877658981), `Ran 9 tests / OK`; Student `c07f0f278673519191f7e5c310056e74d9bc4287`; forward entry >0.03, 실제 0.018827은 여전히 FAIL, odom angular/positive guards 유지. 120/150/300ms Safety TTL 수정 없음.
- 동일 변경을 실제 scoped native 1-cycle [#44877702505](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44877702505) (실제 종료 판정 조회 전: L2 HOLD)에서 검증 중. **분리된 G20 L2는 아직 PASS 아님**.

## G25 — 종료 최초 위반 분리, 실제 root 미해결

- Public `d06/diagnostic/g07_g25_teardown_process_boundary.py`, `tests/test_g07_g25_teardown_process_boundary.py` 및 `.github/workflows/axia-g07-g25-teardown-first-process-l0.yml`.
- 실제 RED #44876429840 → GREEN [#44876461111](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44876461111), role만 남기는 진단, private PID/args는 공개 금지. 
- 실제 #44876802910에서 `SLOW_ENTRY_FORWARD`를 `SLOW`로 오분류한 회귀 RED [#44877125020](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44877125020) → GREEN [#44877147311](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44877147311). 후속 #44877303360 실제 `FIRST_SLOW_ENTRY_FORWARD_TIMEOUT_HOLD`, 올바른 첫 상태로 보고됨. 26초 원인 자체는 이전 SLOW 실패로 미도달.
- 26초 management grace 늘리기/exit1 무시/Parent marker를 child0으로 승격 금지. 기존 `tools/p2_g07_ordered_shutdown.py`, Student #69, Instructor #197/#202 성공 원본 재사용.

## Gate 판단·후속

- 모든 신규 개발은 RED→GREEN→REFACTOR→REVIEW→COMMIT, Public/Student Draft, main 미병합.
- A(G10)=HOLD, B(G20)=HOLD, T(G25)=HOLD. FULL G30 strict independent cold-run 2/2=NOT PASS. G40 SHA-pinned Owner executable=NOT RELEASED. **G50 actual instructor WSL2=NOT_RUN**.
- 다음 최초 경계: G20 .03 기준 실제 Gazette RMW/Goal physical SLOW와 odom yaw; 정상 SLOW라면 G25 26초 첫 child role; G10 원래 wait/take 600ms 재현 시 새 D08 hook으로 동일 Header join. 문제 없던 성공 이력의 중복 시험 금지.
- 신규 WSL2 명령 출고·main 병합 금지, SW stop ≠ certified hardware E-Stop.

## G20 보완 실증: 기존 Goal heading과 장애물 배치 시점의 불일치

- 최신 native #44877702505 (Public 6293eaa97334dd94a17775f7625f2f7d2518115b, Student c07f0f278673519191f7e5c310056e74d9bc4287): 12초 Scan PASS, 실 Nav2 Goal EXECUTING, CLEAR 실제 vin0.03617092m/s→45초가 아닌 기존 12초 진입 대기 동안 -0.024844m/s로 전이, **첫 장애: CI_MOVING_GOAL_TIMEOUT_SLOW_ENTRY_FORWARD**. 물리 Cylinder 아직 배치하지 않음; 인증 STOP 아님.
- 기준 source `tools/p2_g07_demo_corridor.py`: DEMO_START=(-2,-0.5), DEMO_GOAL=(-1.7,+0.7), 목표 방위 atan2(1.2,0.3)≈1.326rad(~76°). 원본 #44871515361 실제 odom yaw .1147rad→1.5198rad 동안 로봇이 회전한 뒤 forward speed가 양(+)이 되고 전방 장애물은 원래 각도에서 사라짐.
- 이 데이터는 **초기 heading 방향과 실제 목표 진행방향이 일치하지 않는 상태의 장애물 배치** 가설을 강하게 뒷받침하되, 그 자체로 실제 SLOW root/수정 성공을 입증하지 않는다.
- Student `p2_g07_ci_slow_entry.py`: 기존 `make_frame_anchor`의 실제 map/odom 원점을 이용하고 DEMO_GOAL 목표 방위와 live yaw 간 오차 ≤0.30rad일 때만 기존 Cylinder를 앞으로 이동. 새로운 TF publisher/Goal/cmd_vel 없으며 원본 `p2_l3_coordinate_frames.py`, Planner, CM 및 Guard 수정 없음. 실제 회전 약 35sec를 고려한 시연 **stage-readiness** bounded wait 45sec는 Scan300/CM120/Guard150 안전 TTL 변경이 아니다. 실행 전 max 45sec 동안 실제 Goal EXECUTING/Guard unlatched 및 양의 전진・yaw 안정성/센서 300ms fresh를 계속 요구하며 실패 시 Goal Cancel + HOLD.
- TDD 공개 RED [#44878069580](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44878069580) → GREEN [#44878130168](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44878130168), **11/11**. Student exact `8f995fe3d600c3f0c1df78700981178d39f5aa46`; Public CI workflow at `eaa717ddabccadbcfd692f9d760fc4b2ce67a72d`.
- 실제 **단일 scoped** Jazzy/Harmonic/Xvfb/Goal trial [#44878195833](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44878195833) source Public `9206b92ff5ceb1d3a7ce7df463a008e5fbe30c4b`, Student `8f995...` → **최종 결과 확인 전 HOLD**. 이것은 G30 독립 2/2를 대체하지 않음.
