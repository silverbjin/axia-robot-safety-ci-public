# AXIA D06 — 두 번째 Owner 실패: 공개 CI-first TDD 검증·잔여 HOLD

> **최종 판단 (2026-11-15): D06 Owner WSLg L3 = HOLD / NOT_ACCEPTED.** 실물 WSL2 추가 Goal 재시도 금지. `main` 병합 없음. ROS2 Jazzy, Gazebo Harmonic, TurtleBot3 Waffle, 공식 Nav2 CM, Guard 150ms/Scan 300ms 무변경. 이전 원본 14-topic private bag은 공개 저장소에 게시하지 않음.

## 1. 실제 Owner 원본 첫 실패

- 실제 G07 Owner 아카이브(비공개 WSL2): 최초 native Guard `UPSTREAM_STALE_AFTER_MOTION`, internal CM age 169.168036ms>150ms(최초 임계 통과 19.168036ms 전).
- 연속 CM RMW publication sequence +1, source gap 184.414666ms>150, receive gap 184.358695ms, 독립 Observer callback gap 223.656034ms. 4 Supervisor publications/최대 source coverage gap89.04962ms, 14-topic bag의 실제 non-zero `/cmd_vel_smoothed` 3건 존재. **CM post-input 실행 또는 발행 스케줄링 후보**, 구체적 원인 미확정.
- 첫 진단의 `first_timing_violation=null`은 두 번째 CM packet이 Guard latch 이후에 도착한 우측 검열(right censor); 정상 증거 아님. raw SQLite quick_check=ok지만 실제 STOP/odom, Lifecycle ACK, CM clean exit 인수 불가. 별도 RViz mesh URI 오류와 CM late -11 exit; 최초 Guard latch 원인으로 단정 금지.

## 2. TDD 공개 CI 근거

| 단계 | Actions | 실제 결과 및 검증 수준 |
|---|---|---|
| RED native Guard/CM post-latch join | [#43669825169](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43669825169) | FAIL; 최초 native 래치·RMW pair 우측 검열 회귀 기존 구현 미지원 |
| GREEN first source/receive/native-Guard diagnostics | [#43670328256](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43670328256) | L0 98 passed + 실제 ROS L1/RViz Xvfb L1 PASS; 물리 Gazebo NOT_RUN |
| RED graphical cleanup and right-censor | [#43670647682](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43670647682) | 99 passed, 2 failed; educational RViz mesh URI and monitor shutdown |
| GREEN display cleanup and original failure retention | [#43670906596](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43670906596) | L0/L1 PASS; RViz RobotModel OFF (Gazebo Waffle kept), scan/TF/odom/rings visible |
| RED owned official CM isolation, CI/Owner parity | [#43671039903](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43671039903) | FAIL 4 new tests |
| GREEN owned CM isolate pre-Goal | [#43671229065](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43671229065) | 5 Observer + 4 CM static tests PASS; actual ROS/Gazebo NOT_RUN |
| RED/Green CM original per-thread affinity restoration pre-Nav2 shutdown | [#43673038730](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43673038730), [#43673260197](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43673260197) | static source RED then GREEN; actual native shutdown not yet GREEN |
| Public source final (latest) | [#43673610455](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43673610455) | L0/actual ROS L1/actual RViz Xvfb L1 PASS, NOT Gazebo L2 |

## 3. 실제 동시 RViz Xvfb + Gazebo G07 L2 실패 원인 구분

| Actions | 최초 실패 경계 | 직접 수치/사실 |
|---|---|---|
| [#43671373817](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43671373817) | POST_GOAL_CLEANUP native Navigation `SERVICE_TIMEOUT` 40s | Guard latch 없음, CM source129.671ms, scan199.744ms, odom1.009s. Test-only CPU burner on protected CM core; native shutdown FAIL |
| [#43672164632](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43672164632) | GOAL_TIMING_OR_ORACLE_BLOCKED | CM source162.678ms>150 with 3 upstream pubs, Guard latch unobserved; source-policy failure, not accepted |
| [#43672596853](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43672596853) | POST_GOAL_CLEANUP native Navigation `SERVICE_TIMEOUT` 40s | Test-only renderer-core bounded duty and stress-stopped-after-Goal; CM source142.176ms, native Guard no latch, scan212.505ms, odom1.007s; ACK FAIL |
| [#43673304437](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43673304437) | PRE_GOAL_PHYSICAL | `PREG0AL_PHYSICAL_L2` first failure. No Goal; CM affinity restore not tested |
| [#43673636317](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43673636317) | GOAL_TIMING_OR_ORACLE_BLOCKED | Actual physical pregoal PASS first. CM **source max130.446ms**, native Guard source/receive gate no gap, **independent Observer RMW received gap343.560ms**, callback346.988ms, odom observer348.432ms>300, scan observer399.700ms>300; full L2 FAIL. The independent Observer delay is NOT proven native Guard CM delivery delay. Nav2 shutdown path and restore remain unverified in this run |

**경고:** 위 실제 L2 중 최신 인수 후보의 **전체 PASS는 없음**. 과거 [#43667573251](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43667573251) full L2 PASS는 다른 Instructor 소스/부하 조건의 역사적 증거이며, 두 번째 WSL2 첫 Guard latch와 신규 L2 FAIL을 덮지 못한다.

## 4. 현행 소스와 분리된 저장소

- 공개 CI Draft PR #108: `feature/d06-gazebo-rviz-owner-20261114`; 최신 source-only HEAD는 PR에서 확인. 코드 `d06/live/d06_guard_cm_first_latch_join.py`, `d06/live/d06_ci_goal_phase_stress_gate.py`, `d06/live/d06_ci_stress_cpu_topology.py`, `d06/live/d06_ci_physical_pregoal_barrier.py`, 비식별 fixture/tests.
- 비공개 강사 후보 브랜치 `fix/d06-g07-official-cm-core-affinity-20261115` HEAD `6e402e30f5036285f067b5dffed085eff41af599`: owned official CM threads preGoal CPU affinity/after-Goal original mask restoration, separate Verifier/GUI/rosbag CPU. **L0 GREEN only; native full Gazebo L2 NOT_ACCEPTED**.
- 실제 L2 테스트 정의 공개 Release 브랜치 `release/p2-g06-cm-ttl-20261110` workflow `.github/workflows/d06-g07-concurrent-rviz-actual-goal-l2.yml` HEAD `0e946099d0bc5ba99f21f2ce4c3de06adfc566b5`.
- 사용자 교육용 STUDENT TODO 변경·공개 Instructor 소스 업로드·`main` 병합 모두 수행하지 않음. SW Stop != certified HW E-Stop.

## 5. 다음 최소 디버깅 경계 (Owner 재시도 금지)

1. **RMW receive gap attribution:** 실제 Guard 내부 CM 수신 주기는 건강하고 CM RMW source 간격도 130ms 이내인데, 읽기 전용 Observer receive가 343.560ms 벌어진 첫 Goal 창을 같은 ROS_DOMAIN_ID에서 별도 진단한다. DDS subscriber QoS/executor scheduling을 구분하는 최소 계측(원본 시계별 source/received/callback)만 추가한다. Native Guard의 정상 값으로 Observer failure를 숨기거나 Observer lag로 Guard 위반을 발명하지 않는다.
2. **Native ordered shutdown independently:** 처음 안전·Goal oracle이 성립한 CI 조건에서 CM original CPU mask restore 후 **Navigation/Localization ACK와 CM clean exit**를 같은 세션에서 검증한다. `SERVICE_TIMEOUT` 40s와 global60s는 유지한다. 전체 Goal 반복 대신 필요한 구간만 독립 L2로 좁히고, 성공 근거는 재사용한다.
3. **Owner 출고 gate 유지:** `d06/acceptance/d06_g07_final_owner_ci_gate.json`은 `HOLD_OWNER_L3_FIRST_CM_SOURCE_TTL_GAP`, `allow_one_final_wsl2_owner=false`, `allowed_final_owner_attempts=0`. 새 동일 소스 real Gazebo+RViz+Safety TTL+STOP+Shutdown+14-topic custody GREEN 전에 한 번의 WSL2 Goal도 허가하지 않는다.

## 6. 검증·출고 방침

`RED → GREEN → REFACTOR → REVIEW → COMMIT`. 공개 CI의 L0/L1 PASS는 해당 범위까지만. 원격 공개 CI L2 FAIL이면 Owner L3 NOT_READY. 실제 사용자의 WSLg에서 실행하지 않았으므로 PASS라고 보고하지 않는다. 공식 CM/Guard/Scan 안전 TTL 완화 없음. 첫 타이밍 위반이 무효화되었다는 주장을 피하고, native Guard safety path와 independent diagnostic observer를 분리한다.

관련 전체 프롬프트: `d06/docs/D06_FIRST_CM_GUARD_WSL2_CI_FIRST_TDD_PROMPT_20261115_KO.md`.
