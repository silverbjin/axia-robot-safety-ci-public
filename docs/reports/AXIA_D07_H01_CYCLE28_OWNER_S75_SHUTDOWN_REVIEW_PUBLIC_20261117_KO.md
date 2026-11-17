# AXIA D07-H01 Cycle28 — Owner S75 실제 원인 및 통합 회귀 REVIEW (공개)

**2026-11-17 KST.** ROS 2 Jazzy / Gazebo Harmonic / TurtleBot3 Waffle / official Nav2 `ComputePathToPose` 무주행 강의 시연. 강사 정답/원본 개인 아카이브는 공개하지 않음.

## 1. 원본 실패의 실제 경계

원본 `d07-h01-owner-S75hTDrR.tar.gz` SHA256 `0933241021e53eb498d4c47a741f44f613f8095708cca0722251d27dc3a2c818` sidecar 일치. 바깥 82/82 및 실제 L2 62/62 해시 PASS.

**시연 성공:** 공식 Planner path Before/Intrusion/Restored 각 52 poses, 0.3659m 경로 변화, 장애물 신규 lethal 92, Costmap 전체 복원 해시 일치, `goal_sent=false`. 로봇 실제 이동 아님.

**최초 종료 분류 결함:** D07 Owner cleanup이 3단계 시연을 마친 뒤 GUI 프로세스 그룹에 SIGINT 전송. RViz PID8066은 exit code **0**이지만 watcher는 무조건 `CHILD_TERMINATED_BEFORE_PHASE_COMPLETE` rc3으로 기록. 당시 Gazebo GUI SIGSEGV 139는 재발하지 않았음.

**종료 감사 결함:** 기존 D07 cleanup은 P4 managed 26초가 아닌 기본 약 **10초**만 기다려 WSL2에서 Fault Injector 종료 증거 확보 전 강제 종료. Official Navigation/Localization SHUTDOWN ACK true, Supervisor·Guard·Collision Monitor 종료 code0. rc3이면 strict child audit JSON 호출이 생략되므로 실제 첫 누락 자식 증거가 숨겨짐.

## 2. 최소 수정과 TDD

- private runtime 검증 SHA **`3a893c1875d2647979a608afaaa335a88158469f`**. 동일 SHA의 진짜 official Planner/No-Goal geometry verdict + 3개의 RViz DDS 실제 Path phase 완료 후에만 watcher가 정상 SIGINT/exit0을 허용. 이전 조기 종료·SIGSEGV139은 계속 FAIL.
- D07 no-goal에서 P4 기존 bounded 26초 process-exit grace만 사용. Scan/CM 안전 TTL 변경 없음. 종료 실패 시에도 자식 프로세스 감사 JSON·실제 누락 이름을 보존하되 강제 종료를 PASS로 승격하지 않음.
- 공개 Owner 원샷은 정상 watcher exit0을 최초 GUI 오류로 기록하지 않으며, 종료 실패 시 missing child와 strict audit status를 `owner_first_teardown_boundary.txt` 및 Owner L3 verdict에 보고.

| 공개 GitHub Actions | 결과 |
|---|---|
| [L0 RED #44001990719](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44001990719) | 6개 중 4개 예상 FAIL |
| [L0 GREEN #44002353440](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44002353440) | **6/6 PASS** |
| [실제 ROS2/Gazebo/Xvfb L2 #44002483668](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44002483668) | **PASS**: 3 공식 Path, watcher 완료 상태 exit0, Navigation/Localization ACK, Supervisor/Guard/FaultInjector/CM exit0, strict teardown |
| [Owner 판정 RED #44002804360](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44002804360) | watcher exit0를 GUI 실패처럼 분류하는 결함 검출 |
| [Owner 판정 GREEN #44003054280](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44003054280) | **5/5 PASS** + `--self-check` + exact Git blobs |

실제 L2: `AXIA_D07_C28_GUI_REAL_OWNER_RUN_RC=0`, `AXIA_D07_C28_REAL_GAZEBO_NAV2_PATH_L2_PASS_NO_GOAL`, `AXIA_D07_C28_REAL_SUPERVISOR_CHILD_EXIT0_AND_P4_ORDERED_ACK_L2_PASS`, `AXIA_D07_C28_REAL_TEARDOWN_VERDICT_CHILD_PROOF_PASS`.

## 3. REVIEW와 미검증

Cycle27 GPU fix는 RED→GREEN을 수행했지만 **정상 시연 후 GUI SIGINT→느린 자식 종료→엄격 감사** end-to-end를 보호하지 못했다. 이전 GREEN은 한정 조건만 통과했고 WSL2 Owner 전체 인수를 뜻하지 않는다.

이번 Git diff는 private 도구 3개와 public 원샷/계약/워크플로 3개만 변경. 공식 Nav2, Fault Injector·Supervisor 기능, CM/Guard 안전 TTL, ROS Goal 및 학생 TODO/강사 정답은 그대로. 실제 Owner WSL2에서 26초 내 Fault Injector exit0와 혼합 WSLg 렌더 화면 성공은 **NOT_RUN**. 새로운 경계는 공개 CI로 재현한 뒤 Owner 검수 1회. 전체 `AXIA_MVP_DEMO_ACCEPTED=HOLD`, 인증 HW E-Stop과 혼동 금지.

**Draft PR로만 보존**하며 사용자 승인 없는 main 병합 금지.
