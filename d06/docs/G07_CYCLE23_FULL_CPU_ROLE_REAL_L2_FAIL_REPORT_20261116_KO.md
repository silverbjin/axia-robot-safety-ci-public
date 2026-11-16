# AXIA G07 Cycle 23 — GUI/Marker/CM/Goal 전체 CPU 역할 분리, 실제 L2 실패

**작성:** 2026-11-16. **판정: L0 GREEN / 실제 Gazebo L2 120ms 출고 게이트 FAIL / WSL2 Owner NOT_RELEASED / AXIA_MVP_DEMO_ACCEPTED=HOLD.**

## 원본 근거

실제 Owner WSL2 first Guard 내부 CM age 174.184617ms > 150ms; CM RMW source 186.714207ms, Supervisor publications 4. Native STOP RPC는 처음 지연과 겹치지 않음. 정확한 CM subscriber/TF executor 원인은 미계측.

Cycle22 CPU 8개 전용 CM {1,6} 후보가 Goal observer {2,3,4,5}와 겹치지 않게 했지만, 공개 D06 Marker observer는 이전 버전에서 CPU6을 사용해 CM6과 겹쳤음. CI 4core에서는 CM{1,2}, Goal{2,3}, Marker2가 동시에 겹침. 이는 실제 원인 후보일 뿐 인과 확정은 아님.

## RED→GREEN→REFACTOR→REVIEW→COMMIT

- Instructor pinned code SHA `124edc82c84ea5c248afb7ba6299b28dbf777092` (tree `67f81138f01a8e58ba93512470dbae4193740759`); 이전 sealed L0 Run [43792670891](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43792670891) PASS.
- Public D06 branch `fix/g07-cycle23-full-role-cpu-partition-20261116`, pinned D06 candidate `d6cc6ae8388c33b10787be2eb03be2cb0e084b16`.
- `d06/live/d06_gui_cpu_plan.py`: 4/5CPU Marker/readonly observer=4th allowed CPU, 6+CPU Marker=3rd allowed CPU. 4core CI {0,1,2,3}에서 Marker3, CM{1,2}와 분리. 8core WSL2에서 Marker2, CM{1,6}와 분리. GUI0, bag last, Goal 역할 유지. 이 모듈은 안전 TTL·Goal·발행 cmd_vel·CM 소스 수정 없음.
- `d06/tests/test_g07_cycle23_cm_marker_role_conflict.py` 4 tests; 기존 `d06/tests/test_g07_unified_gui_sidecar_contract.py` 7 tests를 새 역할 계약과 동기화.
- RED [43793614104](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43793614104): Marker가 CM CPU를 공유한다는 4/8 CPU 테스트 실패. GREEN [43794018046](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43794018046): **신규 4/4, legacy 7/7 PASS, Ubuntu 24.04, NO_ROS_NO_GOAL**.
- 첫 실제 L2 [43793748225](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43793748225)는 legacy sidecar 테스트의 오래된 기대값 4를 5로 갱신하지 않아 **Goal 실행 전 BLOCKED**. 따라서 실제 Goal 실패나 성공으로 오해 금지.
- 고정한 계약을 모두 포함한 실제 GUI Gazebo Harmonic/공식 Nav2 한 Goal L2 [43794087620](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43794087620), public workflow SHA `335f4d767b00025c76bfef6f65f9d210ece9e0d6`, 동일 Instructor SHA124ed 및 D06 SHA d6cc.
- 실제 CLEAR front=2.041817m, SLOWDOWN=0.748779m, STOP=0.398205m, exactly canceled Goal, Navigation/Localization ACK, clean CM exit, `P2_L2_SMOKE_RC=0`; **CM first 120ms source gap=142.906165ms**, Supervisor 3 publications/upstream max gap49.878001ms. Observer CM max **140.619870ms**, Guard66.553123ms, odom138.555498ms, scan206.189249ms, source79.533319ms, supervisor79.563536ms, clock101.778910ms.
- 독립 출고 판정 `AssertionError: FIELD_CI_L2_PASS_LOW_MARGIN_OWNER_NOT_READY`. CM source 및 callback 약 143ms/141ms는 150ms hard 이내지만 **120ms release 미달**. Run conclusion failure.
- CPU-only 변경에서 최초 CM source gap 약143ms가 두 번 재현됐으므로, Marker/Goal 역할 분리만으로 120ms 출고 여유가 해결됐다는 가설은 지지되지 않음. 임의로 Goal 재시도, TTL 완화, TF/base_shift 위험 정책 변경 불가.

## 다음 좁힌 원인 분석

공식 Jazzy Nav2 CollisionMonitor는 입력 velocity callback에서 `process`를 거쳐 output을 publish한다. Supervisor source 발행 3/4회가 CM output gap 안에서 존재했지만 실제 CM **subscriber callback 진입, TF/sensor processing, publish**의 개별 단계를 기록하지 않았음. 따라서 CI runner의 ros2_tracing 콜백 시작·종료 tracepoint 지원 여부를 공개 CI에서 무주행 체크해 이 경계를 재현할 수 있는지 결정한다. 해당 기능 미지원이면 UNKNOWN 유지.

이전 사용자 WSL2 Ubuntu 24.04는 Jazzy/Harmonic 공식 조합. CPU affinity는 4cpu CI/8cpu field 실험 조건을 반드시 구분해야 하며 4core CI 실물 L2도 release 실패여서 Owner 원샷 배포 불가.

**최종: AXIA_MVP_DEMO_ACCEPTED=HOLD / Owner WSL2 moving Goal NOT_AUTHORIZED. 학생 TODO 독립, 강사 private, public sanitized evidence만 사용. main 병합 사용자 승인 전 금지. Certified E-Stop 아님.**
