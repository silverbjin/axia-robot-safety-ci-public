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

## 7. 현재 AXIA MVP 최신 버전 재검토 및 D06 선택 적용 (2026-11-15 오후)

### 실제 최신 저장소 기준과 소스 재사용 판단

- Public `main` `6a19f5a96aab55d0c97505963f468b93fb6d3494` (D06/D07 교육·공식 Nav2 READ-ONLY 범위만 main 통합). Instructor `main` `2fc87f7c134896849ed299c2d68b329c8b8125f5`, Student `main` `e707c1b03cd20889eb84250a24322161a6147196`. 세 main을 이번 D06 개발에 병합하지 않았다.
- 최신 Public `main`의 `d06/live/d06_readonly_monitor.py`, `d06/rviz/d06_safety_bubble.rviz`, `d06/live/d06_ros_l1_visual_probe.py`는 D06 개발 브랜치와 각각 Git blob이 **완전히 동일**. 코드 중복 이식 불필요; 기존 PASS 보존.
- P4의 `AXIA_MVP_DEMO_ACCEPTED` 축소 인수 프로파일: Instructor 후보 ref `ed096eac8427fe18496eccde348da315ec366632`의 `docs/acceptance/AXIA_MVP_DEMO_ACCEPTANCE_PROFILE_V1_KO.md`, `configs/axia_mvp_demo_acceptance_v1.json`. **현재 HOLD**. 강사 시연용 G11 15회 반복/G12 TODO 릴리스/G13 2PC와 별도지만, G07 최초 TTL 위반 해결, S02 native contact 0, G02~G04 서면 검수, 사용자 WSL2 통합 실제 실행·승인 필수. D06 공개 Owner Gate를 임의로 ACCEPTED로 승격하지 않음.
- 실제 최신 P4 G07 공통 소스에서 Observer 측 RMW `received/callback` 간격은 **Native Guard 내부 CM 수신 TTL과 별도**라는 진단 방법을 재사용하고, CI/Owner 동일 Goal 경로·출처 검증은 유지. CM/Guard/Scan TTL, Goal 수동 TTY, 공식 Nav2 안전 설정 변경 없음.

### 선별 시도한 최소 개선 및 실제 검증

- 변경 경로: 공개 D06 `d06/live/d06_gui_cpu_plan.py` (`--role monitor`), `d06/scripts/d06_rviz_sidecar.sh` (교육용 MarkerArray Subscriber를 RViz GUI CPU가 아닌 중간 CPU에 배치), 신규 `d06/tests/test_d06_latest_mvp_observer_cpu_partition.py`. Owner 배포 후보이지만 Owner L3 **차단 상태**.
- 공개 source-only `RED` [#43676010727](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43676010727): 역할 분리 CLI 부재 / 동일 GUI CPU 기존 sidecar로 **3개 신규 테스트 실패**.
- 공개 source-only `GREEN` [#43676083228](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43676083228): **L0 111 passed**, 실제 ROS L1 PASS, RViz Xvfb L1 PASS. 스크립트 bash -n, Owner fail-closed 검증 포함. 이는 실제 Gazebo/Nav2 Goal 성능 검증이 아니다.
- 공개 실제 Gazebo+RViz Xvfb 단일 Goal [#43676192483](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43676192483), workflow source `dcfb82f8853bec63b601cf1eaf366e2e5f9685c2`, Public D06 pinned SHA `d0b398e5aa1f23bf950bbba93ed815c7d6288138`: **FULL L2 FAIL**. 4역할 CPU 배치 출력은 `display=0 monitor=2`, CM source max `91.306ms` (150ms 이내), Native Guard latch 미관찰, 그러나 독립 Observer `odom` 첫 gap `368.392ms` 및 `scan` 첫 gap `388.215ms` (300ms 초과). CM 원본 first-gap으로 분류되지 않았으며, Goal STOP/odom dwell/native Nav2 shutdown·CM clean exit의 적격 원본 결합을 확보하지 못함.
- **판정:** GUI CPU/MarkerArray 모니터 격리는 안전 런타임의 무변경 후보이지만 새 L2 실증에서 이점 미확인. 따라서 **L0/L1 개선 후보만 GREEN**, 실제 L2 출시·Owner WSL2 적용은 HOLD. 특히 4-core 환경에서 `monitor`와 Scenario Verifier 중간 CPU가 공유될 수 있으므로, 새로운 실제 사용 조건에서 Native 안전 / Observer scheduling을 별도로 계측해야 한다. 이번 변경을 'WSL2 오류 해결 완료'라고 주장하지 않는다.
- P4 축소 프로파일의 기존 5개 시나리오 성공 증거는 역사적으로 재사용할 뿐, D06의 새 GUI 부하와 Owner WSLg 화면/CM TTL 인수 증거로 전용하지 않는다. G11 15회 반복 테스트를 새로 수행하지 않았다.

### 다음 최소 실행 경계 (추가 현장 재시도 금지)

1. Public CI에서 실제 native Guard 내부 CM 수신 및 `/cmd_vel_pre_guard` RMW source/receive 경계와 **Scenario Verifier/교육용 Observer의 독립 callback gap**을 분리: CPU 0=GUI, 1=CM, 중간=Verifier/교육용 Monitor, 최후=bag 역할이 4-core에서 경쟁한다는 가설을 확인한다. 파라미터·TTL 완화 금지.
2. 시연 인수에는 동일 CI 실제 Gazebo/Xvfb Goal에서 first Guard latch 없음, CM/Guard <=150ms, Scan <=300ms, CLEAR/SLOWDOWN/STOP, /odom dwell>=1s, official Nav2 native Lifecycle ACK, CM clean exit0, 14-topic raw custody가 함께 있어야 한다. 최신 L2는 이 조건을 충족하지 못했다.
3. 공개 Source+L1 Green과 역사적 L2 Green을 합쳐 **새 통합 L2 PASS**로 만들지 않는다. Owner `ADMITTED_FINAL_OWNER_ONLY` 재발급 금지, `main` 병합 금지, 학생 TODO/비공개 강사 정답 변경 없음. D06 수업은 공식 CM 격리 L1 대체 경로 유지.
