# AXIA Robot Safety MVP — 개발시간·TDD·디버깅 효율 감사 및 G07 잔여 인수 실행안

- 기준일: **2026-11-15 KST**
- 범위: `AXIA_G07_UNIFIED_MVP_CONTINUATION_HANDOFF_20261115_KO.md`, P0~P4 현존 GitHub 기준 기록, G07 통합 Cycle 01~07의 **선택된 실제 Actions 26건**
- 검증: GitHub 커밋 메타데이터·원격 브랜치 HEAD·실제 Actions job verdict/원본 로그 시간/성공 문구 읽기 전용 재조회.
- 최종 판정: **`CI_GUI_L2_PASS_SCOPED` / `OWNER_WSL2_L3_NOT_RUN` / `AXIA_MVP_DEMO_ACCEPTED=HOLD`**.
- **중요:** 이번 감사는 실제 WSL2/Gazebo를 새로 실행하거나 코드를 수정하지 않았으며, 기존 Run 성공을 현재 L3 성공으로 승격하지 않는다.

## 1. 결론

**ROS 2 안전 MVP에 TDD는 유효하다. 다만 모든 환경 문제를 TDD 단위테스트와 다수의 형식 게이트로 해결하려는 개발 방식은 비효율적이다.** 안전 FSM/TTL/Fail-closed/Goal 권한의 정합성은 작은 회귀 테스트로 보호하고, DDS 수신·GUI·CPU·Gazebo 물리는 실제 동일 시나리오 L2로만 확인해야 한다. 비효율의 주원인은 *TDD 그 자체*보다 **CI↔WSL2 시연 부하 불일치 → 실제 L2에서만 오류 발견 → 다단계 재현·새 승인 실행기·반복 문서/브랜치**였다.

이미 성공한 L2를 재실행하지 않는다. 최종 후보 private `bc270e28620c1909fcb34669e6036504b5cae951`의 G07 GUI L2 `#43693480829` 성공과 Owner v2 admission `#43694023013/#43694275463/#43694440201`을 그대로 보존하고 **Owner WSL2 최종 수동 1회 인수**만 남긴다.

## 2. 경과시간과 실제 작업시간: 서로 다른 지표

| 지표 | 실제 확인 결과 | 주의 |
|---|---:|---|
| 확인된 프로젝트 초기 P0 커밋 | 2026-11-01 09:17:16 KST, `2d6cdce1a266cef88ed7f710d409f6e66662e127` | 저장소의 확인 가능한 시작점; 기획·별도 로컬작업은 포함하지 않음 |
| 초기 P1 관련 커밋 | 2026-11-01 17:50:58 KST, `302a8fe3483a2ff9060eaa4fce83d99950695ee2` | P1 기록상의 기준점 |
| 최종 v2 bootstrap CI 로그 | 2026-11-15 17:25:43 KST, Run `43694440201` | 실 ROS/Goal 아님 |
| P0 기록→v2 인수 준비 경과 | **14일 8시간 8분 27초** | 달력상 경과; 인간 작업시간이 아님 |
| P1 기록→v2 인수 준비 경과 | **13일 23시간 34분 45초** | 위와 동일 |
| G07 Cycle 중 선택 검증 로그 첫~끝 | **2026-11-15 15:31:25~17:25:43 KST**, 약 **1시간 54분 18초** | *선별* 26건의 외곽 간격; 미선별 Actions/코딩/대기 포함 가능 |
| 인간 실제 코딩·분석·리뷰·WSL2 조작시간 | **UNKNOWN** | 시간기록 부재. GitHub 실행시간을 사람 시간으로 쓰지 않음 |
| 전체 프로젝트의 모든 Actions 누적 실행시간 | **UNKNOWN** | 저장소 전체 Actions run 목록/원본에 대한 전수 집계가 없으므로 수치 생성 금지 |

## 3. 직접 조회한 G07 26건의 CI 실행시간

GitHub Actions의 **job 로그 첫 타임스탬프와 마지막 타임스탬프**를 이용했다. 각 실행시간은 초 단위 반올림이고, **대기열·개발·재시도 준비·사람의 수동 작업을 포함하지 않는다.**

| 유형 | 건수 | 로그 상 실행시간 합계 | 결과 |
|---|---:|---:|---|
| L0 / sealed 또는 공개 무주행 회귀 | **21** | **99초 = 1분 39초** | 기대한 RED 9 / GREEN 12 |
| 실제 Gazebo/Nav2/GUI L2 | **5** | **965초 = 16분 5초** | 실패 3 / 성공 2 |
| **확인된 선별 총계** | **26** | **1,064초 = 17분 44초** | 실패 12 중 9건은 의도적 RED |

**해석:** 선택된 실행에서 L0 자체는 약 9.3%의 job 시간, L2는 약 90.7%를 차지한다. 앞뒤 달력 간격과 총 17분 44초의 차이는 코딩·검토·CI 대기·미선별 실행 등이 혼재하므로 *전부 낭비*라고 계산할 수 없다. 26건을 전체 프로젝트 Actions 총량이라고 주장해서도 안 된다.

### 3.1 핵심 L2 실패→성공 사슬

| Run | 로그 시간 | 결과 | **최초 실패 경계 또는 입증 내용** |
|---|---:|---|---|
| [43685818018](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43685818018) | 204초 | PASS_SCOPED | 이전 GUI 구성에서 1회 성공. **이후 Owner와 실행기 parity 문제를 닫은 증거는 아님** |
| [43690412617](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43690412617) | 181초 | FAIL | Nav2 shutdown 첫 서비스 발견 실패 |
| [43690918618](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43690918618) | 190초 | FAIL | 첫 PRE_STOP Odom **355.882ms**. CM RMW source **70.892ms**, receive **377.049ms**, Observer **383.109ms** → receive/CPU 경합 후보 |
| [43692909902](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43692909902) | 187초 | 안전 BLOCKED | Goal 전 `G07_PREARMED_CPU_ISOLATION_NOT_AVAILABLE_NO_GOAL`: Goal Observer 가용 CPU를 1개만 남겨 원래 native STOP 2-CPU 불변조건 위반 |
| [43693480829](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43693480829) | 203초 | **PASS_SCOPED** | 동일 G07 Goal + 외부 Gazebo GUI/RViz Xvfb, prearmed STOP, 7채널, S02 native contact0, exact Cancel·shutdown |

### 3.2 감사대상 모든 Run (재현 가능한 원장)

| Run | 수준 | 판정 | job 로그 초 | 대상 |
|---|---|---|---:|---|
| [43685818018](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43685818018) | L2 | PASS | 204 | prior unified GUI L2 scoped success |
| [43689306583](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43689306583) | L0 | EXPECTED_RED | 3 | first mismatch and clock-step fixture |
| [43689362501](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43689362501) | L0 | PASS | 6 | mismatch/clock-step classifier green |
| [43689577854](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43689577854) | L0 | EXPECTED_RED | 2 | private sealed runtime parity red |
| [43689643931](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43689643931) | L0 | PASS | 6 | private sealed runtime parity green |
| [43690073396](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43690073396) | L0 | PASS | 8 | pre-Goal GUI barrier |
| [43690121848](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43690121848) | L0 | PASS | 2 | shared GUI clients contract |
| [43690335847](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43690335847) | L0 | PASS | 8 | private evidence bundle synthetic |
| [43690412617](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43690412617) | L2 | FAIL | 181 | Nav2 shutdown first-service discovery |
| [43690918618](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43690918618) | L2 | FAIL | 190 | first Odom PRE_STOP 355.882ms/receive delay |
| [43691430319](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43691430319) | L0 | EXPECTED_RED | 2 | first receive-gap fixture red |
| [43691482482](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43691482482) | L0 | PASS | 5 | first receive-gap fixture green |
| [43692517210](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43692517210) | L0 | EXPECTED_RED | 2 | multichannel delivery fixture red |
| [43692568543](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43692568543) | L0 | PASS | 6 | multichannel receive attribution green |
| [43692715147](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43692715147) | L0 | EXPECTED_RED | 2 | private Goal Observer CPU parity red |
| [43692856500](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43692856500) | L0 | PASS | 2 | private Goal Observer CPU parity green |
| [43692909902](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43692909902) | L2 | FAIL | 187 | pre-Goal STOP minimum 2 CPU admission blocked |
| [43693340153](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43693340153) | L0 | EXPECTED_RED | 2 | 2-CPU prearmed invariant regression red |
| [43693435159](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43693435159) | L0 | PASS | 2 | 2-CPU prearmed invariant regression green |
| [43693480829](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43693480829) | L2 | PASS | 203 | real Jazzy/Harmonic/Nav2/Gazebo GUI+RViz L2 |
| [43693901706](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43693901706) | L0 | EXPECTED_RED | 6 | Owner v2 source/tree release red |
| [43694023013](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43694023013) | L0 | PASS | 8 | Owner v2 source/tree release green |
| [43694177547](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43694177547) | L0 | EXPECTED_RED | 8 | Owner v2 admission gate red |
| [43694275463](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43694275463) | L0 | PASS | 7 | Owner v2 admission gate green |
| [43694386318](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43694386318) | L0 | EXPECTED_RED | 3 | final pinned WSL2 bootstrap red |
| [43694440201](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43694440201) | L0 | PASS | 9 | final pinned WSL2 bootstrap green |

별도 기계 판독 가능한 검증 로그 요약: `AXIA_G07_CI_26_RUN_EVIDENCE_LEDGER_20261115.json`. **과거 원본 Run의 전체 raw artifact 재다운로드나 Owner 원본 현장 로그 재채집은 이번 감사에서 수행하지 않았다.**

## 4. 근본 원인과 개발 방식의 과잉 요소

| 기여 요인 | 1차 증거 | 지연 구조 | 수정 방향 |
|---|---|---|---|
| **Owner와 CI의 실행 환경/GUI 차이** | Owner 최초 `CM_EXCEEDS_SUPERVISOR` 및 Cycle03·L2 실패 계열 | WSLg·렌더러·CPU 배치가 다른 상태에서 헤드리스 PASS를 현장 준비로 오해. 현장에서 발견 → CI 재현 루프 | 하나의 Goal·launch·GUI sidecar·CPU 역할 선택기 사용. 차이는 manifest에 기록 |
| **시계 영역/오류 귀속 혼동** | Owner CM age 69.385ms vs 150ms, mismatch 125.425ms vs 120ms, RMW source clock step 약 1.47s | 최종 `Destroyable` exception 또는 RMW 시스템시계 점프를 최초 안전 원인으로 오판할 위험 | 최초 Guard 상태 전이·monotonic 첫 간격·source/receive/Guard 내부 이벤트를 따로 증거화 |
| **다중 채널 수신/observer I/O 경합** | #43690918618: source 70.892ms vs receive 377.049ms | 단일 unit PASS로 발견 불가. 실제 동시 GUI/rosbag 동작에서만 드러남 | real L2로 CPU/프로세스 역할을 검증, Safety TTL 불변 |
| **수정의 부작용을 다른 안전 계층에 미검증** | #43692909902 Prearmed STOP minimum 2 CPUs | 하나의 주기 지연 개선이 Native STOP 진입을 Goal 전 차단 | L0에 2-CPU invariant + 실제 Goal 전 readback을 최소 영향 테스트로 포함 |
| **인수 게이트·보고·브랜치 과잉** | 21회 선택 L0, 별도 v2 release/gate/bootstrap의 RED→GREEN | 코드 수정보다 source pin/TTY/admission 관리 반복에 설계·검토 비용. 다만 RED 자체는 짧음 | 안정된 고정 pin과 1개 통합 release를 유지; 새 문제 없으면 재발행 금지 |
| **범위 혼재** | P4 형식 G11 15회 요구와 축소 demo 프로파일 병존 | 정식 형식 인수를 MVP에 동일 적용하면 인력·원본·실행 비용 폭증 | `AXIA_MVP_DEMO_ACCEPTED` 축소 데모만 목표; 정식 v1은 별도 마일스톤으로 분리 |

**강조:** 120ms mismatch는 Guard의 의도된 fail-closed 상태다. “시연 실패”를 없애기 위해 grace/TTL을 늘리거나 latch를 무시하면 기능 안전성이 약화된다. 여기서 해야 할 일은 upstream 정합성·스케줄링을 안정화하고 그 경계를 검증하는 것이다.

## 5. TDD 방법론 평가

**유지:** 안전 Supervisor FSM 우선순위, CM 150ms TTL, Supervisor 500ms timeout, Scan/Odom/Clock 300ms 관측 기준, Guard mismatch 120ms ZERO-only, E-Stop과 SW Stop 분리, TTY Goal 허가·Cancel·shutdown·증거 누락 HOLD에 대한 **단일 실패 재현 테스트**.

**축소:** 작은 문서/리팩터링마다 ROS/Gazebo 전체재검, 정식 v1 3×/15× 반복, 모든 실패에 과도한 새 유닛 테스트/문서/별도 브랜치, 기존 검증된 공식 TB3/Nav2 구현의 재시험. 기존 PASS SHA와 증거/검증 범위를 원장에 연결한다.

**대체:** GUI/DDS/스케줄링/물리 충돌은 mock 기반의 얕은 RED로만 합격 처리하지 않는다. “처음 실패한 원인”이 코드로 결정론적 재현 가능하면 L0 RED→GREEN, 그렇지 않으면 **실제 단일 Gazebo L2 실패 증거를 테스트 오라클의 RED 기준**으로 삼고 한 번의 변경 영향 L2를 수행한다.

## 6. 승인된 MVP용 경량 개발·디버깅 표준 (즉시 적용)

1. **불변 증거 인덱스**: `branch + source SHA + tree SHA + runtime digest + workflow SHA + Goal UUID + scope + verdict + artifact custody` 조인. 기존 통과는 `RETEST=SKIP_EXISTING_PASS`.
2. **최초 실패 1개**: Guard 상태 전이·첫 monotonic gap·source→receive→native Guard callback→`/cmd_vel`·첫 shutdown ACK 실패를 시간순 정렬. 종료 exception은 후행으로 분류.
3. **한 가설/한 수정**: 첫 오류의 인과를 밝히는 최소 비식별 fixture/회귀 RED 1개. 소스 수정 GREEN 후 REFACTOR·짧은 REVIEW·COMMIT. 두 안전 계층의 경계가 얽힌 경우에만 해당 2개 경계를 함께 재검.
4. **차등 검증**: 문서·비동작 파일은 lint/syntax만. 기능·타이밍·CPU·QoS·ROS wiring 변경은 L0→필수 L1→**실제 Gazebo+GUI L2 단일 Goal**. 전체 S01~S05 재실행 금지.
5. **배포/현장 횟수 제한**: 실제 L2 PASS 및 Owner 수동 입장 계약을 가진 정확한 SHA만 v2 원샷 배포. Owner WSL2는 통합 **최종 1회**; 현장 최초 실패면 raw bundle → CI 회귀 → 새 후보, 현장 반복 금지.
6. **종료 조건**: L2는 7채널 TTL+Native Contact+Stop/Dwell+exact Cancel ACK+Managed Shutdown+CM exit0+14-topic custody의 *같은 Goal*이 모두 확인된 범위만 PASS. Owner L3는 추가로 실제 WSLg/WSL2/raw 확인과 사용자 최종 승인이 필요.

## 7. G07 마지막 후보의 원격 상태 및 다음 수행

| 자산 | 확인된 브랜치/고정 SHA | 상태 |
|---|---|---|
| Private Instructor G07 공통 실행기 | `fix/g07-ci-owner-runtime-parity-20261115` = `bc270e28620c1909fcb34669e6036504b5cae951` / tree `59c35abb651cdce18d3131b28497a500ca692cc2` | 원격 확인, 실제 L2에 사용 |
| P4 이전 기준선 | `integration/g07-mvp-consolidated-20261115` = `db1eec05e01e1db0d0d2e0c05610806ef4e499f9` | 기존 L2 증거 보존 |
| Public G07 통합 작업 | `integration/g07-unified-ci-20261115` = `a359ca8e1d18aa8811f11be570e4cb1a29e3df70` | docs/cycle07 HEAD 확인 |
| Public Owner v2 pin | `8b9e44f4b622210831dd68055dad3efe8a293c92` / tree `9e33400972463d42627c37a35f02f5a3dcb87be8` | sealed 검증 |
| Public Bootstrap | `e0ecb7abe7a0ddc8beb38f706f5094024e1083c5` | #43694440201 실제 no-Goal job 로그 **PASS** |
| Real GUI L2 | #43693480829 / workflow `29dfd7a1a36e45d130d803e1b8a46cad191de50f` | **PASS_SCOPED**, **not Owner L3** |

원본 성공 로그에서 확인한 구체 출력:

```text
AXIA_P4_G07_REAL_RMW_CM_SOURCE_MAX_GAP_SEC=0.139004
AXIA_P4_G07_NATIVE_RMW_SOURCE_RECEIPT_SEQ_L2_PASS_CI_ONLY
AXIA_G07_UNIFIED_GUI_STRESS_XVFB_REAL_L2_CANDIDATE_NOT_WSLG
AXIA_P4_G07_OWNER_WSL2_NOT_RUN_SCHEDULER_UNVERIFIED_FORMAL_HOLD
AXIA_G07_FINAL_BOOTSTRAP_STATIC_PASS public_sha=8b9e44f4b622210831dd68055dad3efe8a293c92 private_sha=bc270e28620c1909fcb34669e6036504b5cae951 ci_l2=43693480829 NO_ROS_NO_GOAL
AXIA_G07_FINAL_OWNER_GATE {"certified_estop": false, "full_demo_accepted": false, "manual_attempt_allowed": true, "owner_l3_accepted": false, "status": "ADMITTED_ONE_FINAL_WSLG_OWNER_ONLY"}
AXIA_G07_FINAL_OWNER_V2_BOOTSTRAP_CI_NO_ROS_NO_GOAL_PASS_OWNER_L3_NOT_RUN
```

정확한 L2 한 Goal 실측: source 81.066ms, CM 141.483ms, Guard 64.882ms, Supervisor 81.140ms, Scan 190.864ms, Odom 139.586ms, Clock 105.497ms. 실물 Gazebo S02 physics 34,819 tick 중 대상 contact positive 0, Odom zero dwell 1.016659s, exact Cancel ACK/ordered Nav2 shutdown/CM exit0. 그러나 **다른 환경/모든 Goal에서 최초 120ms mismatch가 영구 해결됐다는 증거가 아니다.**

### 7.1 다음 단계: 코드 변경 없는 Owner 단일 인수 후보

현재 GitHub 고정 CI와 공개 v2 부트스트랩에서 **새 미해결 결함이 발견되지 않았으므로 소스 수정이나 새 CI L2 재주행을 하지 않는다**. 기존 실행기 그대로 WSL2 수동 한 번을 수행할 수 있는 상태다. 별도 CLI 입력 전에는 주행이 시작되지 않으며, 사용자가 TTY에서 `YES-P2-G07-GOAL`을 직접 입력한다.

```bash
(
  set -Eeuo pipefail
  SHA="e0ecb7abe7a0ddc8beb38f706f5094024e1083c5"
  SCRIPT="$(mktemp)"
  trap 'rm -f -- "$SCRIPT"' EXIT
  curl -fL --retry 3 -sS \
    "https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public/${SHA}/scripts/axia_g07_final_owner_v2_wsl2_bootstrap.sh" \
    -o "$SCRIPT"
  bash -n "$SCRIPT"
  bash "$SCRIPT"
)
```

Owner L3가 `HOLD/FAIL`이면 `~/.axia_g07_owner_support/g07-*/`의 `support_evidence.tar.gz`, `manifest.json`, `SHA256SUMS`를 비공개 수집하고 첫 상태 전이/첫 위반부터 다음 CI RED로 전환한다. 동일 오류를 Owner에서 반복 실행하지 않는다. 원본은 절대 공개 CI/학생 저장소에 업로드하지 않는다.

## 8. 남은 항목·운영 판정

| 항목 | 최종 상태 |
|---|---|
| 기존 P4, S01~S05, G02~G04 scoped 성공 증거 | 검증한 범위 내 재사용, 불필요한 재실행 없음 |
| 새로운 안전·GUI 실행기 소스 수정 | 이번 감사에서 **없음** |
| 이번 감사 새 CI/ROS/Gazebo/Owner 실주행 | **실행 안 함**. 기존 실제 결과 원본 확인만 수행 |
| Owner 최신 v2 단일 Goal/WSLg | **NOT_RUN** |
| 새로운 최초 120ms mismatch가 WSLg에서 사라짐 | **UNVERIFIED** |
| Certified hardware E-Stop | **해당 없음**. SW STOP 데모일 뿐 |
| `AXIA_MVP_DEMO_ACCEPTED` / main | **HOLD / 병합 미실행(사용자 승인 필요)** |

### 참조 문서

- `d06/docs/AXIA_G07_AUTONOMOUS_DEBUG_CYCLE_LEDGER_KO.md` — Cycle 01~07
- `d06/docs/G07_UNIFIED_CYCLE07_FINAL_OWNER_V2_CI_PARITY_20261115_KO.md` — 원본 Run·SHA
- `d06/docs/AXIA_G07_CI_FIRST_RUNTIME_PARITY_DEBUG_STANDARD_20261115_KO.md` — 첫 실패 및 CI-first
- `d06/docs/G07_FINAL_OWNER_WSL2_V2_ONE_SHOT_GUIDE_20261115_KO.md` — 고정 Owner 가이드
- `AXIA_G07_UNIFIED_MVP_CONTINUATION_HANDOFF_20261115_KO.md` — 대화 인계 기준

**결론:** 안전회귀 TDD는 유지하되, 시뮬레이터 L2와 현장 인수까지 모든 수정마다 재실행하는 **중복 형식 TDD**는 중단한다. 안정화된 최신 후보의 인수 준비는 기존 검증 범위 안에서 완료됐으며, **아직 남은 것은 실제 Owner WSL2의 동일 조건 한 번의 실주행과 근거 검토**다.