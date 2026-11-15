# AXIA G07 — CI→Owner WSL2 현장 재현성·출고 게이트 운영 표준

- 문서 버전: `v1.0`, 작성: 2026-11-15 KST
- 우선순위: **P0 — 기존 CI PASS 이후 Owner WSL2 실패가 반복되는 문제 해결**
- 대상: ROS 2 Jazzy / Gazebo Harmonic / 공식 TurtleBot3 Waffle·Nav2 / AXIA Safety Supervisor·Fault Injector·Scenario Verifier
- 기준 원본: `AXIA_Robot_Safety_MVP_Baseline_Scenario_Acceptance_v1_KO.md`, `AXIA_MVP_DEMO_ACCEPTANCE_PROFILE_V1_KO.md`, G07 통합 Cycle 01~07, Owner 첨부 비공개 지원 묶음 2건
- 원칙: `RED→GREEN→REFACTOR→REVIEW→COMMIT`; **이미 통과한 정확 SHA·범위의 L2 증거 보존**, `main` 병합은 사용자 승인 필요
- 공개 저장소에는 이 **비식별 분석·운영 지침만** 둔다. Owner 원본 tar/rosbag/UUID·사용자 로컬 경로·비공개 강사 정답은 공개하지 않는다.

## 0. 최종 결론과 현재 판정

**이번 화면의 직접 차단은 `AXIA_G07_FINAL_OWNER_REPEAT_BLOCKED_CI_FIRST_REVIEW_REQUIRED_NO_GOAL`이며, 주행 이전 `mkdir` 기반 기존 시도 예약 중복 탐지에 따른 의도적 fail-closed이다.** 그래서 현 시도 자체는 ROS/Goal을 새로 실행하지 않았다. 뒤따른 `D06_RVIZ_NOT_CONFIRMED`, `D06_G07_POSTRUN_TRIAGE_RUN_AMBIGUOUS count=0`은 새 실행 자료가 없어서 발생한 후속 상태이고 최초 장애가 아니다.

**그러나 첨부된 읽기 전용 G11 검토 증거에는 같은 Instructor SHA로 진행된 앞선 Owner 실행의 실제 안전 실패가 존재한다.** Guard 내부 CM 입력 age `0.158007666s`, 기존 TTL `0.150s`, 초과 `0.008007666s`; 최초 래치 `UPSTREAM_STALE_AFTER_MOTION`, ZERO 출력. 시점: monotonic 기준 CM 마지막 수신 `220.322693622`, TTL 경계 `220.472693622`, 래치 tick `220.480701288`. 이 자료는 단순 반복 실행 잠금 해제의 근거가 아니라 **새 CI RED 재현을 요구하는 현장 안전 결함**이다. 해당 검토는 Goal UUID/Cancel/Shutdown 결합과 실제 owner 원본 전체가 미완전하여 최종 인수 `HOLD`였다.

동일 사건의 CM·Supervisor RMW source timestamp 약 `1.5s` 간격은 시스템 시계 영역 불연속 후보와 연관되어 있으므로, 이를 CM publisher가 1.5초 정지한 것으로 단정하지 않는다. 별도 직전 연속 publish-sequence 구간 `source≈173.204ms / receive≈173.735ms / observer≈165.438ms`가 보이지만 최초 Guard TTL 인과는 추가 원본·동기화 검증이 필요하다.

**현재 판정**: `FIELD_TTL_BREACH_CONFIRMED / OWNER_ATTEMPT_LOCK_VALID / CI_RELEASE_GATE_INADEQUATE / NEW_OWNER_GOAL_DENIED / AXIA_MVP_DEMO_ACCEPTED=HOLD`. 인증된 하드웨어 E-Stop이 아니며, SW Stop은 시뮬레이션 안전 제어이다.

## 1. 정확히 무엇을 놓쳤는가 — 증거와 원인 계층 분리

| 종류 | 실제 원본/코드 | 증명된 내용 | 잘못된 해석 금지 |
|---|---|---|---|
| 이번 **최초 제어흐름 차단** | Public v2 `d06/scripts/g07_unified_final_owner_wsl2_v2_once.sh`의 `ATTEMPT_ROOT`·`ATTEMPT_NAME`·`mkdir` | 동일 `(private SHA, L2 run)` 예약 폴더 존재 시 `exit 3` 전 새 Goal 없음 | `RViz`가 실패해서 Guard 오류가 났다고 역산 금지 |
| 앞선 **최초 안전 상태 전이** | 첨부 지원 tar의 `g11_custody/reviews/g07-20261115T100107Z-1653.json` | `UPSTREAM_STALE_AFTER_MOTION`, Guard CM 입력 `158.008ms`, 150ms 초과, ZERO 출력 | 최종 `RAW_CAPTURE_INCOMPLETE`를 최초 원인으로 취급 금지 |
| 앞선 **RMW 해석 제한** | 첨부 지원 tar의 `g11_custody/reviews/g07-rmw-20261115T100108Z-1653.json` | `CROSS_TOPIC_HOST_CLOCK_STEP_CANDIDATE`; 발행 중단 미증명 | wall/system clock과 host monotonic 직접 차감 금지 |
| 실제 CI 통합 1-Goal L2 | [#43693480829](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43693480829), Instructor `bc270e28…`, workflow `29dfd7a1…` | CI Xvfb/RViz 실제 Gazebo L2 범위 한정 PASS, CM observer max `141.483ms`, CM source max `139.004ms`, Contact 0, Cancel/Shutdown | Owner WSL2·WSLg·지속 상태 성공으로 승격 금지 |
| 기존 v2 출고 검사 | Public [#43694275463](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43694275463) 및 [#43694440201](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43694440201) | NO ROS/NO Goal 시나리오에서 새 HOME 기준 문법·SHA·TTY·기존 gate 확인 | **이미 예약된 Owner HOME**에서 실행 가능한지 증명하지 못함 |
| 지원 묶음의 진단 한계 | 첨부 `support_evidence.tar.gz` 25개 엔트리; GUI ZIP은 디렉터리와 빈 `SHA256SUMS`만 있음 | 과거 G11 보존 감사/리뷰 자료 일부 확보. 이번 새 실행의 완전한 raw/GUI 없음 | `BUNDLE_CAPTURE_COMPLETE`를 `EVIDENCE_COMPLETE`로 표현 금지 |

Owner 이전 G11 manifest는 private 원본 보관 위치와 14-topic 원본 존재를 *보고*하지만, 첨부된 지원 묶음에 그 원본 전체가 직접 실려 있는 것은 아니다. 필요시 **기존 원본을 읽기 전용으로** 확인해야 하며 새 Goal부터 실행하지 않는다.

## 2. 반복 실패의 CI 구조적 원인

1. **영속 상태 모델이 빠짐**: GitHub-hosted VM은 job마다 새 환경이므로 `~/.axia_g07_final_owner_attempts` 같은 WSL2의 이전 이력과 충돌하지 않는다. 현재 CI는 처음 실행 및 NO TTY만 점검하고, **이전 실제 실패 후 동일 SHA 재호출**을 충분히 검증하지 않았다.
2. **입장 용어와 검증 순서 오류**: gate가 `ADMITTED_ONE_FINAL_WSLG_OWNER_ONLY`를 출력한 뒤에야 `mkdir` 잠금이 검사되어 실제 Goal 진입 불가를 늦게 알린다. **CI 메타데이터 합격**과 **현재 현장 실행 가능**을 별개 상태로 만들어야 한다.
3. **타이밍 여유 부족**: CI CM callback 최대 `141.483ms`는 하드 안전 TTL `150ms` 대비 약 `8.517ms` 여유밖에 없다. 이는 기술적 PASS이지만 WSL2의 다른 커널·DDS·WSLg·CPU 경쟁하에서 충분한 안정성을 보장할 수 없다. 이번 Owner `158.008ms` 위반으로 위험이 현실화되었다.
4. **런타임 바이트 일치≠실행 조건 동등**: 공유 `p2_g07_ci_moving_goal.run()`, 공통 shell, image digest 일치는 유효하지만 GitHub 4-CPU·Xvfb와 Owner WSL2·WSLg는 스케줄링·GPU·디스플레이·메모리·기동 서비스·가용 CPU 마스크가 다르다.
5. **증거 수집의 빈 성공 신호**: Owner가 PRE-GOAL에서 차단되면 새 원본 디렉터리가 없을 수 있는데, `support_evidence.tar.gz` 생성 성공만 보고하면 진단이 완료된 것으로 오인한다. collector 실행 성공·원본 존재·안전 판정 완료를 분리해야 한다.
6. **다른 안전 계층 영향 누락**: 과거 CPU 분리 변경이 기존 Prearmed STOP의 최소 2-CPU 제약을 깨뜨려 `#43692909902`에서 NO GOAL 차단되었다. CM 수신 계층을 개선한 뒤 Goal/STOP/Scan/Odom의 첫 타이밍 경계도 함께 확인해야 한다.

**지침의 목표는 불가능한 `현장 100% 성공 보증`이 아니다.** 새 현장 오류의 종류를 CI에서 재현·차단하여 **재시도 횟수와 원인 발견 지연을 줄이는 것**이다. 물리 Owner WSLg를 실행하지 않은 결과를 `OWNER VERIFIED`로 표시하지 않는다.

## 3. CI 출고 계약: 별도의 다섯 조건을 모두 만족해야 `READY_FOR_OWNER_ONE_ATTEMPT`

### G0 — 원본/소스/안전불변 조건 (매 후보, L0)
- 공개 runner·강사 sealed checkout의 commit SHA, Git tree, 필수 blob, runtime digest, 공식 Nav2/TB3/CM 버전, 파라미터·QoS·RMW, start/goal/obstacle, 14-topic schema를 기록한다.
- CI와 Owner는 **정확히 동일한** `tools/p2_g07_ci_moving_goal.run()`, `scripts/p4_g07_shared_runtime.sh`, `p2_l3_live_session.Observer`, shutdown/cancel verifier를 호출한다. Goal 허가 및 Xvfb/WSLg만 분리한다.
- 기존 120ms reconciliation·CM/Guard 150ms TTL·Scan/Odom/Clock 300ms·Supervisor timeout 500ms·Prearmed STOP 최소 2 CPU·ZERO fail-closed·Goal 수동 TTY를 완화하거나 우회하지 않는다. 공식 코드는 fork하지 않는다.
- 셸 문법·Python import·exact pin·no-TTY·no ROS/Goal·missing evidence fail-closed, private/public 분리 확인.

### G1 — **영속 HOME 및 재진입 상태 계약** (이번 문제의 최우선 신규 L0)
- `temp HOME`에 실제 WSL2와 동일한 구조를 **비식별 fixture**로 만드되 아래 시나리오를 모두 테스트한다.
  - `EMPTY`: 아직 시도가 없는 상태에서 읽기 전용 preflight는 통과, **아무 잠금도 만들지 않음**.
  - `EXISTING_FAILED_ATTEMPT`: 기존 예약 폴더와 실패 증거가 있는 상태에서 **동일 SHA/CI run**은 새 Goal 없이 차단. 그러나 실행 전 `CURRENT_OWNER_STATE=BLOCKED_EXISTING_FAILED_ATTEMPT`를 출력하고 **`ADMITTED`를 출력하지 않음**.
  - `PRE_GOAL_ABORT`: pin/ROS/GUI/TTY 사전검사 실패 시 자동으로 `ATTEMPT_RESERVED`를 만들지 않음. 시도 흔적이 있다면 `GOAL_NOT_SENT`가 원본에서 입증되는 것만 별도 안전 복구 규칙으로 관리하며 강제 삭제 금지.
  - `NEW_REMEDIATED_SHA`: 이전 실패는 보존하되 **새로운 변경 SHA + 최초 오류 RED/GREEN + 실제 변경영향 L2 PASS + 명시된 새 Owner 승인 토큰**일 때만 별도의 신버전 단일 시도 허가.
  - `DOUBLE_INVOKE/RACE`: 동시에 두 시작을 요청해도 Goal 권한은 하나에만 부여, 나머지는 `NO_GOAL`.
- 승인 순서: read-only local state/CI receipt 검사 → 호스트·GUI·CPU preflight → **원자적 예약 및 TTY 확인** → Goal 시작. 메시지도 `CI_SCOPED_PASS`와 `OWNER_ATTEMPT_ELIGIBLE`을 구분하여 출력한다.
- `--self-check`와 `--admission-check`는 절대 예약 생성·ROS/Goal·기존 lock 삭제를 하지 않는다. `--field-preflight` 같은 읽기 전용 진단 옵션을 별도 지원한다.

### G2 — **노드 간 실제 전달 타이밍 및 성능 여유** (L1/변경 영향 L2)
- 동일 Goal UUID·`steady/monotonic` 기준 최초 위반을 추적한다: CM publisher source → RMW publication/received → 외부 Observer → **Guard 내부 실제 callback** → Supervisor cmd → 최종 `/cmd_vel` → `/odom` 및 `/scan`·`/clock`.
- ROS/RMW system-clock epoch timestamp와 monotonic timestamp는 분류기에서 **시계 영역을 명시**한 후에만 비교한다. 같은 `source≈1.5s`가 여러 토픽에 나타나도 publisher 정지나 TTL PASS/FAIL을 임의 판정하지 않는다.
- **기존 안전 hard limit는 그대로**: CM/Guard/Supervisor 주기 `150ms`, Scan/Odom/Clock `300ms`, Guard reconciliation `120ms`. 임계값 이상 또는 근거 누락이면 기술 인수 FAIL/HOLD.
- **배포 여유 경보(새 운영 권고, 안전 TTL 변경 아님)**: 우선 CM·Guard 전달 구간은 목표 `≤120ms` (150ms의 80%), Scan/Odom/Clock은 `≤240ms` (300ms의 80%)로 보고, 초과하면서 하드 TTL 미만이면 `CI_L2_PASS_LOW_MARGIN / OWNER_RELEASE_HOLD`로 분리한다. 80%는 **첫 후보 운영값**이며 실측 jitter/WSL2 수집자료에 따라 검토하지만 법정·안전 기준을 바꾸지 않는다. 현재 CM `141.483ms`는 이 조건에서 **LOW_MARGIN**이므로 이전의 범위 한정 CI PASS를 무효화하지 않되 새 Owner 배포 재승인으로 사용하지 않는다.
- Goal-window 1회 실물 L2에서 GUI/RViz+Marker, native STOP, 7채널 first gap, 14-topic SQLite, native Contact 0, zero dwell ≥1s, exact CancelGoal ACK, Navigation/Localization shutdown ACK, CM exit0를 같은 UUID로 연계한다.
- 새로운 성능 수정이 특정 계층의 callback을 개선하면, 최소한 그 계층과 **인접 안전 계층(예: Prearmed STOP CPU, Scan/Odom, Guard native callback)** 을 검증한다. 과거 S01~S05 등 영향 없는 테스트는 기존 SHA/범위 증거를 재사용한다.

### G3 — 환경/시각화 동등성·자원 제약 계약 (CI/Owner manifest)
- 런타임 해시가 같아도 다음 fingerprint를 **CI와 Owner 양쪽에서 자동 수집하고 비교**한다: WSL2 여부·커널/WSL 버전·Windows build, CPU quota/affinity(실제 effective mask), RAM/스왑, ROS/GZ/Nav2 package 버전, RMW implementation, locale/time sync, `ROS_DOMAIN_ID`, `GZ_PARTITION`, DDS config, graphics/WSLg/Xvfb·DISPLAY/Wayland, Mesa/GL driver, GPU software/hardware renderer, process count 및 `nice`/`taskset`/max CPU load.
- CI가 직접 복제하지 못하는 `WSLg`, 호스트 커널, GPU renderer는 `ENV_PARITY_UNVERIFIED`에 기록한다. 실제 사용자의 `~/.wslconfig`를 변경하거나 시스템 패키지를 자동 업그레이드하는 방식으로 시험을 억지 통과시키지 않는다.
- CPU 역할: 4코어 CI에서는 Goal Observer에 Prearmed STOP용 **2개 이상 실제 CPU**, renderer/bag/monitor를 가능한 한 분리. CPU가 부족하면 안전하게 `NO_GOAL`.
- 필요할 때만 **신뢰된 비공개 격리 WSL2 테스트 머신**을 보조 CI로 사용한다(보안 격리/단독 소유/코드 출처 제한). 퍼블릭 PR이 Owner WSL2 머신의 self-hosted runner에서 임의 실행되도록 연결하지 않는다. GitHub-hosted Windows의 nested virtualization은 안정적 WSL2 동등성 근거로 취급하지 않는다.

### G4 — 관측 가능성·증거 완전성·출고 순서 계약
- 오류를 `FIRST_FAILURE_PHASE`, `FIRST_SAFETY_TRANSITION`, `FIRST_TIMING_BOUNDARY`, `ROOT_CAUSE_PROVEN`, `UNKNOWN`으로 구분. 후행 `RVIZ_NOT_CONFIRMED`나 shutdown 예외는 항상 첫 경계와 연결한다.
- Owner bundle 생성 성공과 실제 증거 충족을 분리한다: `COLLECTOR_RAN`, `OWNER_ORIGINAL_PRESENT`, `GUI_LOG_PRESENT`, `RAW_GOAL_WINDOW_JOINED`, `BUNDLE_COMPLETE`, `OWNER_ACCEPTED` (모두 독립 boolean). `owner_root=None`이고 GUI 로그도 0바이트이면 `INCOMPLETE_PREGOAL_NO_NEW_OWNER`; 이전 G11 자료만 존재하는 경우 이를 **현재 실행의 완전한 증거**로 보이지 않는다.
- 신규 안전 실패가 발견되면 **기존 Owner raw 읽기 전용 보존 → 비식별 최초 실패 fixture → 실패 재현 RED → 최소 GREEN → REFACTOR/REVIEW/COMMIT → 실제 관련 Gazebo L2 PASS → 출고 CI gate 전체 PASS → 새 exact SHA로 Owner 1회**. 기존 같은 SHA 현장 재시도/잠금 삭제 금지.
- CI는 `PASS_SCOPED` 및 `LOW_MARGIN`을 동시에 표시 가능하지만, **`READY_FOR_OWNER_ONE_ATTEMPT`는 G0~G4 전체를 만족할 때만** 출력한다. Owner 결과 검토·사용자 최종 승인 전 `AXIA_MVP_DEMO_ACCEPTED=HOLD` 유지.

## 4. 최소 회귀 시험 집합 — 이것만 우선 추가할 것

| 우선 | 신규/보강 테스트(제안 파일명) | 첫 RED 기대 | GREEN 합격 조건 | ROS/Gazebo |
|---|---|---|---|---|
| P0 | `d06/tests/test_g07_owner_persistent_attempt_state.py` | 기존 failed attempt가 있는 HOME에서 `ADMITTED` 후 `REPEAT_BLOCKED`; 순서 오류 | `BLOCKED_EXISTING_FAILED_ATTEMPT`를 초기에 표시, TTY/Goal/ROS 없음, 원본 보존 | L0, NO ROS |
| P0 | `d06/tests/test_g07_owner_preflight_does_not_consume_attempt.py` | GUI/ROS/TTY 사전 실패에서도 lock가 예약될 수 있음 | preflight 순수·멱등, no-goal 확정과 reservation audit | L0, NO ROS |
| P0 | `d06/tests/test_g07_owner_bundle_empty_scope_truth.py` | 빈 GUI/새 Owner 없음에도 `CAPTURE_COMPLETE`만 출력 | `COLLECTOR_RAN=true`, `BUNDLE_COMPLETE=false`, 이유 분명 | L0, NO ROS |
| P0 | `d06/tests/test_g07_field_cm_158ms_first_ttl.py` | 158.008ms Owner Guard 내부 위반을 일반 `RMW CLOCK STEP`로 오분류 | `GUARD_INTERNAL_CM_TTL_BREACH`, hard HOLD, `clock_domain_unverified` 별도 | L0 fixture |
| P1 | `d06/tests/test_g07_l2_margin_release_gate.py` | 기존 `141.483<150`이라 Owner READY라고 표시 | `CI_L2_PASS_LOW_MARGIN`, `OWNER_RELEASE_HOLD`; 150ms hard TTL 불변 | L0 gate |
| P1 | 기존 `.github/workflows` **공통 Goal 실제 L2 1건** | GUI/CPU 부하하 최초 주기·다른 안전 계층 경계 이상 | 동일 SHA/Goal 소스·실제 7채널/Guard 내부 150/300ms + 충분한 여유 및 원본 | 실제 L2 |

RED가 의도된 테스트인 경우 **RED run은 실패로 기록**한다. GREEN 이전에 권한 있는 새로운 Owner Goal 스크립트를 배포하지 않는다. `RETEST=SKIP_EXISTING_PASS`는 이 표의 변경 영향이 없는 항목에만 사용한다.

### 필수 CI synthetic fixture (비식별)

```json
{
  "schema": "axia.g07.field_first_failure_sanitized.v1",
  "first_transition": "UPSTREAM_STALE_AFTER_MOTION",
  "phase": "GOAL_WINDOW",
  "cm_guard_age_sec": 0.158007666,
  "cm_ttl_sec": 0.15,
  "cm_ttl_exceeded_sec": 0.008007666,
  "guard_last_emitted_is_zero": true,
  "cm_rmw_epoch_jump_candidate": true,
  "cm_publisher_stopped_proven": false,
  "must_hold": true,
  "owner_full_raw_available_in_public_ci": false
}
```

이는 Owner 원본 JSON/Goal UUID/개인 경로를 재발행한 것이 아닌 **재현 가능한 안전 판정의 비식별 수치**이다. 테스트가 `safety_pass=true`를 만드는 것을 금지한다.

## 5. 배포/실행기 개선 요구사항 (에이전트 체크리스트)

**배포 전**: `--field-preflight` (무상태 변경·NO ROS/NO Goal)으로 `existing_attempt`, 소스 pin, WSL2/WSLg 설치, 실제 CPU/메모리/프로세스, rosbag 보관 경로, runtime bundle completeness를 먼저 검사한다. 일치하지 않으면 **스크립트를 Goal 단계에 진입시키지 않고** 정확한 첫 BLOCKED 사유·필요한 기존 원본 디렉터리만 출력한다.

**기존 시도 차단 처리**: 이번 문제처럼 앞선 Goal에서 Guard TTL 위반이 있으면 이전 예약 디렉터리를 절대 임의 삭제하지 않는다. 새 release 후보 SHA와 실제 CI 재검증이 선행된 뒤 별도 시도 ID를 생성한다. `exit 3` 자체는 **안전하게 작동한 결과**이며, 문제는 *불일치한 사전 승인 표시*와 *이 안전 문제를 해소하지 않은 채 동일 SHA 재배포한 것*이다.

**성공 메시지 계약**:

```text
CI_L2_PASS_SCOPED                  # 기존 exact source에서 기술적 PASS
CI_L2_PASS_LOW_MARGIN             # 안전 제한은 만족하나 배포 여유 부족
OWNER_FIELD_PREFLIGHT_BLOCKED     # 영속 상태/환경 이슈, NO_ROS_NO_GOAL
OWNER_ONE_ATTEMPT_ELIGIBLE        # 새로운 승인된 SHA에서 모든 입장 조건 충족
OWNER_GOAL_CONSENT_REQUIRED       # 물리 TTY에서 YES-P2-G07-GOAL 필요
OWNER_L3_PASS_SCOPED              # 실제 WSL2 원본 1-Goal 평가까지 성공
AXIA_MVP_DEMO_ACCEPTED=HOLD       # 현재 상태; Owner 명시 승인 이전 유지
```

불필요한 사용자 왕복을 줄이기 위해 **하나의 스크립트가 preflight→(허가된 경우만)TTY→Owner Goal→증거 원자 보존→최초 실패 분석**까지 한 번에 수행하게 한다. 단 이미 실패한 같은 SHA를 다시 재시도하지 않는다.

## 6. 에이전트에 그대로 전달할 강제 프롬프트

> 당신은 AXIA ROS 2 Jazzy/Gazebo Harmonic/Nav2 기반 G07의 CI→WSL2 재현성 책임자다. 기존 Cycle 07 PASS를 폐기하지 말고 exact SHA/검증 범위로 보존하라. 사용자가 올린 첨부 증거에서 이번 즉시 오류는 **기존 시도 예약 중복으로 인한 PRE-GOAL NO_GOAL 차단**이고, 이전 Owner raw 리뷰에는 **Guard 내부 CM age 158.008ms > 150ms, 최초 `UPSTREAM_STALE_AFTER_MOTION` 래치**가 있음을 인정하라. 이것을 `D06_RVIZ_NOT_CONFIRMED`나 `RMW 1.5s clock step`으로 잘못 대체하지 마라.
>
> 최우선 개발 작업은 (1) 영속 Owner HOME을 모사한 CI 비식별 재진입 L0 RED, (2) 첫 158ms Guard TTL 실패의 L0 RED, (3) 현재 141.483ms CI CM 최대값의 release margin 부족 검출 RED이다. 위험한 lock 삭제, 무단 Goal, TTL·120ms 유예 완화, 공식 Nav2/CM 재구현을 하지 마라. 최소 수정으로 GREEN을 얻고 코드 리뷰·커밋한 뒤 CI·Owner가 **같은 공통 실행기 코드·최종 안전 판정기**를 사용하는지 검증하라. 추가적으로 Guard 내부 직접 callback/CM source/receive·Scan/Odom 및 Prearmed STOP 2-CPU의 인접 타이밍 경계를 실제 Gazebo+Gazebo GUI+RViz에서 **변경 영향 단일 Goal L2**로 검사하라. 불필요한 15회 반복 주행이나 무관한 S01~S05 전수 검사는 생략하고 적격 원본 증거를 재사용하라.
>
> `CI_L2_PASS_SCOPED`, `LOW_MARGIN`, `OWNER_ATTEMPT_ELIGIBLE`, `OWNER_L3_VERIFIED`를 서로 다른 상태로 다루어라. GitHub-hosted Xvfb가 사용자 WSLg와 동일하다고 주장하지 마라. Owner에서는 Goal 전에 읽기 전용 preflight를 자동 수행하고 기존 failed attempt가 있으면 즉시 NO_GOAL 차단한다. 후속 수정과 충분한 CI 증거를 새로운 source SHA에 고정한 다음에만 새 Owner 단일 TTY 시도를 배포하라. 모든 실행의 파일 경로·명령·원본 출력·Git branch/SHA·CI Run·검증 범위·미검증 목록을 보고하라. public에는 비식별 fixture·테스트·지침만 올리고 private Instructor 정답과 raw는 보존하라. `main` 병합은 사용자 승인을 받아라.
>
> **종료 조건**: CI에 최초 현장 실패를 재현하는 RED가 남고, GREEN 코드는 안전 TTL을 유지하며, 변경 영향 실제 Gazebo L2가 PASS + release margin 게이트 충족, 배포된 새 WSL2 실행기는 existing attempt를 Goal 전에 정확히 차단하거나 새로운 승인된 후보를 1회 허가해야 한다. 이 조건 전에는 `AXIA_MVP_DEMO_ACCEPTED=HOLD` 및 Owner Goal 신규 시도 금지.

## 7. 재실행 비용을 억제하는 운영 결정

- 이번 사이클은 **정적 실패/실제 안전 위반 두 경계에 한정**한다. 기존 P4 L2 #43674784552, 통합 GUI L2 #43693480829는 원본 범위에서 재사용한다.
- 한 개의 의도된 RED + 수정 GREEN + 영향된 L2 **최소 1회**로 출고 가능성을 판정한다. 초과 시 새 실험을 자동 늘리지 않고 원인 자료만 비교한다.
- 사용자 WSL2에서 새 오류가 발생하면 한 번 보관된 기존 원본을 재검토하고 CI 재현을 먼저 추가한다. 현장 같은 SHA 재시도 요청은 금지한다.
- 필요 시 UI 상에서는 **CI 준비 완료**와 **실제 Owner 현장 인수 완료**를 다른 지표로 표시한다.

## 8. 검증 완료/미검증 및 출처

- 본 문서 작성 중 한 실제 작업: **업로드된 2개 아카이브 내용과 정확 GitHub 실행기/게이트/CI 원본을 읽기 전용 대조함**. 새 ROS, Gazebo, Goal, GitHub Actions 실행 없음. 원본 SHA·의도된 선행 실패 결과를 임의 승격하지 않음.
- 현재 확정: v2 repeat-lock, 앞선 Guard 158ms TTL 위반, Owner bundle 신규 raw 누락, 기존 통합 GUI L2 `PASS_SCOPED`, CI gate의 영속 state 테스트 누락.
- 현재 미확정: 158ms 원인의 CPU/kernel/DDS 정량 인과, Windows WSLg 실영상 정상성, 동일 SHA에서 안전 타이밍 장기간 안정성, Owner 기존 원본 full ROS bag의 추가 packet timing, 신규 CI 회귀 GREEN과 새 Candidate 실제 L2.
- 공개 소스 참고: `silverbjin/axia-robot-safety-ci-public`의 고정 커밋 `8b9e44f4...` 및 `6a5ffa4486...`, 실제 L2 `#43693480829`; 비공개 Instructor 정확 후보 `bc270e28...`.
- 플랫폼 근거: [GitHub-hosted job별 새 VM](https://docs.github.com/en/actions/how-tos/manage-runners/github-hosted-runners/use-github-hosted-runners), [WSLg Linux GUI](https://learn.microsoft.com/en-us/windows/wsl/tutorials/gui-apps), [Self-hosted runner 보안주의](https://docs.github.com/en/actions/reference/security/secure-use).

**기준 판정: `CI_PARITY_POLICY_DOCUMENTED / SOURCE_REVIEWED / OWNER_PREGOAL_BLOCKED / PRIOR_FIELD_TTL_BREACH_CONFIRMED / NEW_CI_TESTS_NOT_RUN / AXIA_MVP_DEMO_ACCEPTED=HOLD`.**