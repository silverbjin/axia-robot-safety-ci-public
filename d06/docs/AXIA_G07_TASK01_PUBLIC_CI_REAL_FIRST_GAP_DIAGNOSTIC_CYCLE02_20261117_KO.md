# AXIA G07 Task01 Cycle 02 — 공개 CI 원시 증거 보존 전환과 실제 최초 CM 지연 인과 검토

**2026-11-17 KST | 최종 결론: 공개 CI 증거 저장 GREEN; 실제 진단 Moving Goal L2 FAIL; TF 10ms polling 관찰 강함, 동일 RMW source gap의 확정 인과 및 Scheduler 영향은 UNPROVEN; CM120 tracer-OFF RELEASE=HOLD.**

## 1. 정책 결정과 범위

사용자는 공개 CI에서 인수 전 진단·개발을 실행하도록 정책을 변경했고, 비공개 GitHub Actions/증거 브랜치 쓰기를 불필요하게 만들 것을 요청했다.

**정확한 기존 문제:** 새 Secret `AXIA_G07_EVIDENCE_WRITE_TOKEN`은 비공개 Actions를 호출하는 비밀값이 아니었다. 공개 CI에서 private Instructor 저장소에 원시 증거를 `git push`하기 위해 요청한 **쓰기 권한**이다. 기존 [실패 #44043431253](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44043431253)의 `AUTH_OR_CONTENT_WRITE_DENIED` 때문에 Goal 전 보관 게이트가 차단됐다.

**새 정책:** 공개 `axia-robot-safety-ci-public` Actions에서 실제 Nav2/Gazebo 테스트를 수행하고, 비공개 원본 raw는 sealed runner 안에서만 사용한다. `Contents:Write` private 토큰/증거 브랜치 push는 폐기. 외부로 나가는 것은 비공개 소스를 제거한 **정형 수치 타이밍 JSON + SHA256**뿐이다. 기존 비공개 Instructor checkout을 위한 **읽기 전용 `AXIA_CLOUD_CI`**는 계속 사용하되 private Actions를 실행하지는 않는다.

공식 ROS 2 Jazzy/Nav2/TB3 Waffle/Safety 코드·CM120/Guard150/ScanOdomClock300 및 STOP/SLOW 지오메트리, TF Advanced 설정, lifecycle/Goal 소유권 모두 변경하지 않음. 이 진단에서 Goal 1회만 새로 발행했고 사용자 WSL2 Owner L3는 미실행.

## 2. RED→GREEN→REFACTOR→REVIEW→COMMIT

### RED: 민감정보 누출 및 원본 증거 누락 반례

- `d06/tests/test_g07_task01_public_evidence_allowlist.py`: 강사 소스·Pose·기밀 경로·Callback 주소가 허용목록 JSON으로 유출되면 FAIL, source SYSTEM과 Observer MONOTONIC 혼합 금지, 원본 부재/타입 오류/용량 초과/가짜 SHA fail closed.
- `d06/tests/test_g07_task01_public_evidence_adapter.py`: private raw 부재·corrupt·invalid run identity에서 고정 `HOLD` JSON 또는 단호한 실패 판정. exception/raw 내용 무출력.
- [실제 public RED #44048040474](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44048040474): `export_public_cm120_first_gap` 구현 전 module import 실패; ROS/Gazebo 실패 아님.

### GREEN: 수치형만 변환·보관

- `d06/diagnostic/export_public_cm120_first_gap.py`: 정확한 최초 RMW source>120ms pair, source·received SYSTEM과 observer MONOTONIC **각 시계의 anchor 상대 ns**, official CM 콜백 동일 PID/TID에 소속된 TF call/sleep duration만 허용. 프로세스 주소·frame·Pose·센서 raw 원본/강사 코드는 저장하지 않음. `source_publication_to_monotonic_alignment_proven=false`, root cause/release/owner pass=false를 고정.
- `d06/scripts/g07_task01_extract_public_gap.py`: raw ROS event JSONL, bounded exact LTTng C++ CM callback, `TF_ADV/TF_SLEEP` 원본을 CI runtime 메모리/임시공간에서만 읽고 허용목록 스키마로 변환. 원본 없거나 해석 실패시 고정 `HOLD` 기록, 비공개 예외 내용 출력 금지.
- [최종 public L0 #44048860819](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44048860819), source SHA `5e6db932728085398fd1b6d9441847286d70c2be`: `Ran 5 tests ... OK`, `Ran 3 tests ... OK`, Python compile PASS, **실제 actions/upload-artifact ZIP 업로드 PASS**.
- L0 synthetic GitHub artifact ID `14312528121`, ZIP SHA256 `140e4d76f5a060957d59acd5f5abbe58f8c62b57a1668615c3db9e763f789303`.

### REFACTOR/REVIEW

- 공개 작업 브랜치 `fix/g07-cm120-task01-public-evidence-20261117`에서 종전 private canary script/test/workflow 3개 제거; 이전 기록은 [Draft PR #159](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/159)에 보존.
- 공개 release branch에서 `.github/workflows/axia-g07-task01-private-custody-release-preflight-20261117.yml` 삭제: commit `2256e190f4a1c57ad3df15b29b68d16de6c24f1c`. 더 이상 신규 write Secret을 요구하지 않음.
- 기존 공식 S2 one-Goal workflow를 재사용한 공개 단일진단 runner `.github/workflows/axia-g07-task01-public-evidence-one-goal-l2-20261117.yml`, workflow SHA `1b017541d5908f267711108f667bc248f4dfe939`. 실제 private Instructor code SHA `966886c4627deb2bb3b37111fe336eeee6b9ebb4` READ-only, public diagnostic SHA `5e6db932728085398fd1b6d9441847286d70c2be`. 
- **증거 생성 → allowlisted 2파일 artifact 업로드 → private checkout/LTTng/TF raw 삭제**라는 순서를 같은 public workflow에서 `if:always()` 적용. 실제 원본 14-topic bag은 공개 업로드하지 않았으므로 해당 원본의 장기 보존/인수는 별도다.

## 3. **실제 Gazebo 단일 진단 Moving Goal의 최초 실패 증거**

[Run #44049067368](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44049067368) / job `133921996670`, **completed/failure**. 실제 공식 TB3 Waffle/Harmonic/Nav2 Goal 한 번 발행. 처음에는 CLEAR/SLOW/STOP 각각 로그로 관측, 그러나 전체 Goal/안전/integration acceptance는 FAIL이다.

| 동일 run 첫 RMW source >120ms 원본 쌍에서 확인한 수치 | 실제 값 |
|---|---:|
| 최초 연속 CM RMW publisher source 간격 | **129.299071 ms** |
| 같은 메시지 쌍의 Observer callback 간격 | **128.391951 ms** |
| Official CM 입력 콜백 wall | **91.944586 ms** |
| Advanced TF 함수 wall 총합 (matched 2회) | **91.752789 ms** |
| TF thread CPU | **0.388890 ms** |
| 실제 TF `nanosleep` overlap (observer pair) | **9회 / 91.416406 ms** |
| 9개 실제 sleep의 요청시간 합계 | **90.000000 ms** (`req_ns=10000000` 각각, `rc=0`) |
| 9개 sleep 실제 벽시계 초과량 | **1.416406 ms** |
| TF sleep / 첫 RMW source 간격의 수치상 비율 | **약 70.70%** (시계/경계 인과 단정 금지) |

원본 공식 CM 프로세스는 `--ros-args ... -p use_sim_time:=True`로 실행됨을 실제 로그에서 확인했다. 공식 Jazzy `tf2_ros::Buffer::canTransform`은 `clock_->now()`로 timeout을 판단하며 `sleep_for(10ms)` 실제 스레드 대기를 반복한다. **같은 첫 observer pair의 TF 함수 총 91.753ms 중 91.416ms가 실제 libc sleep이라는 관측은 PROVEN_OBSERVER_PAIR**. Kernel Scheduler runqueue가 원인이라고 단정하지 말 것; 같은 함수 내 9회 sleep의 요청 총 90ms와 실제 91.416ms의 차이1.416ms는 벽시계 대기 초과분이며, 이것만으로 thread runqueue와 Clock stalled를 분리할 수 없다.

### 동일 실행 공개 artifact 수치 정합

[GitHub artifact ID 14313016879](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44049067368/artifacts/14313016879)에서 실제 ZIP 다운로드 후 검사:

- ZIP SHA256: `3563b21f0b7a81760edd026bb28a14aee677593703e3f14cda4bbc285ebe6f92`
- 파일 목록 **정확히** `first_gap_sanitized.json`, `SHA256SUMS.txt` 2개, JSON 2,592 bytes.
- 내부 JSON SHA256: `d242ea84b3b8cb3d133960998b62393bd34ad12ca1edef96e271695ac74977f9` = artifact `SHA256SUMS.txt` 값.
- 허용목록 밖 top-level key 없음, private/Instructor/pose/frame/topic/pointer 문자열 검사 음성.
- JSON `schema= axia.g07.cm120.public_first_gap_v1`, `status=FIRST_RMW_SOURCE_GAP_SELECTED_CAUSE_UNPROVEN`, `tf_sleep.count=14` (**첫 Observer pair와 전후200ms 범위의 전체 표본**, 이 중 9개만 첫 pair 안에 존재), `tf_sleep.coverage_proven=true` (선택한 10 TF calls와 sleep count 대응).
- source interval과 Observer를 **same-host clock calibration이 검증됐다는 가정 아래에만** 상대 배치하면 첫 source 시작/끝은 Observer 첫 시점 기준 `[-3.420484ms, +125.878587ms]`이며, 그 범위에 sleep 9개/91.416406ms가 모두 들어간다.
- 시작/종료 anchor의 `wall_minus_mono` offset 차이는 1ns로 계측. Source→RMW received SYSTEM 간격 첫/둘째 0.234035ms /0.100773ms. Source→Observer 보정 추정 약3.420484ms/2.513364ms. **이 수치들은 동일 host/sender RMW timestamp 신원·정확도까지 인증하지 않으므로 `source_publication_to_monotonic_alignment_proven=false` 유지**.

공개 artifact는 GitHub 기본 보존기간이 지나면 만료되므로, 수치만 있는 동일 JSON과 SHA256SUMS를 공개 개발 브랜치에 별도로 보존:
- `d06/evidence/g07_cm120_task01/run_44049067368_first_gap_sanitized.json`
- `d06/evidence/g07_cm120_task01/run_44049067368_SHA256SUMS.txt`
- [실제 public 회귀 #44050420229](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44050420229), tested SHA `733af05e767a91265fcdde92f668bf09d3accf49`, **completed/success**:
```text
AXIA_G07_TASK01_ACTUAL_FIRST_CM_GAP_129_299MS_TF_SLEEP_91_416MS_PUBLIC_SHA256_PASS
AXIA_G07_TASK01_SOURCE_TO_MONO_CAUSE_AND_SCHEDULER_UNPROVEN_RELEASE_HOLD
```

## 4. **실제 통합 시연 FAIL을 별개로 유지할 것**

같은 #44049067368 원래 CI의 첫 목표 안전 oracle은:
```text
AXIA_G07_PUBLIC_CI_MOVING_GOAL_BLOCKED
RuntimeError: ACTUAL_MOVING_GOAL_CI_ORACLE_SAFETY_DELIVERY_TTL_BOUNDARY_max_source_interval_sec
```
보호하고자 했던 최초 source 120ms gap은 **129.299ms**로 확인됐고, 동일 시연의 *전체* 최대 interarrival:
- `source=0.344100801s` (344.101ms)
- `cm=0.335076580s` (335.077ms)
- `supervisor=0.335095441s` (335.095ms)
- `guard=0.372483318s` (372.483ms)
- `clock=0.333514680s` (333.515ms)
- `odom=0.346211602s` (346.212ms)
- `scan=0.365052570s` (365.053ms)

여러 노드에서 300ms safety delivery 경계까지 초과하므로 **TF 함수 한 건만 줄였다고 시연 전체가 안정적이라 주장하면 안 된다**. 이 자료만으로 최초 Guard 내부 age 150ms의 단독 실패 시점/책임을 확정할 수 없다. 로그 후반에는 공식 `collision_monitor` process `exit code -11`(SIGSEGV)가 관측됐으나 **원인 미확정**이며, 최초 안전 전달 위반과 후속 비정상 종료를 혼동하지 않는다. 진단 LD_PRELOAD 또는 기존 종료 처리 중 어느 계층의 결함인지는 별도 회귀/증거 필요. 전체 L2 FAIL / 전체 원본 rosbag custody·Nav2 native ACK 이 실행에서 인수 불가.

**금지:** 편의상 source_timeout을1.0→0.3, Guard TTL150→늘리기, Scan/Odom/Clock300→완화, `base_shift_correction=false`, CPU affinity 변경을 일괄 적용하지 않는다. 공식 source TF 기능 / 로봇 장애물 안전 여유 검증 전에 성능만으로 채택 금지.

## 5. 다음 Task01→04 게이트 판단

| Task | 현재 증거 수준 | 판정 |
|---|---|---|
| Task01 evidence custody/공개 CI policy | PUBLIC RED→GREEN8 + 실제 sanitize/upload + ZIP/JSON SHA256 + 불변 public CI 회귀 PASS | **증거보존 문제 해결** |
| Task01 최초 TF sleep vs Scheduler | 동일 첫 Observer pair 9회/91.416ms sleep, 90ms intentionally requested **실측**, official Jazzy sim_time=True. 하지만 publisher 송신 시각 정합/최초 `/clock` 구간/Kernel scheduler runqueue 미계측 | **부분 인과 확인, ROOT_CAUSE_UNPROVEN** |
| Task02 proven cause 최소 수정 | Task01 남은 인과/다른 300ms 안전층 교차검증 전 착수 금지 | BLOCKED |
| Task03 tracer-OFF release | diagnostic tracer ON failing L2는 120ms 최종 릴리스가 아님 | NOT_RUN |
| Task04 Owner WSL2 L3 | 실제 user WSL2 GUI/Goal 실행하지 않음 | NOT_RUN |

**추가 실제 Goal의 필요성 판단:** 최초 source gap은 이번 1회에서 이미 재현되어 비공개 쓰기 증거 블로커를 해결했다. 동일 조건을 다시 실행하는 것으로는 새 정보가 생기지 않는다. 다음 관측은 **같은 처음 gap 시각에서 `/clock` 실측 진행, TF availability와 Kernel runnable 대기의 구분 및 공통 300ms 전송 경계의 최초 상태 전이**라는 단일 원인 가설을 먼저 기존 코드·기존 기록에서 재검토하는 것이다. 새로운 계측이 필요하면 기존 도구의 최소 수정 + 공개 CI L0 RED→GREEN을 선행한다. 안전 인수가 없으면 성능 수정·릴리스 승격 금지.

## 6. 파일 경로·명령·브랜치·검증 수준

공개 개발 브랜치: `fix/g07-cm120-task01-public-evidence-20261117`, prior Draft PR #159에서 분기; 신규 PR은 별도로 생성/검토하며 main 병합은 하지 않음.

- `d06/diagnostic/export_public_cm120_first_gap.py` — numeric allowlist
- `d06/scripts/g07_task01_extract_public_gap.py` — sealed raw→allowlist adapter
- `d06/tests/test_g07_task01_public_evidence_allowlist.py` — RED/GREEN 5
- `d06/tests/test_g07_task01_public_evidence_adapter.py` — fail-closed 3
- `.github/workflows/axia-g07-task01-public-evidence-canary-l0-20261117.yml` — pure public artifact upload L0
- `.github/workflows/axia-g07-task01-real-public-artifact-custody-l0-20261117.yml` — actual immutable JSON/SHA reverify
- 공개 release 브랜치 `.github/workflows/axia-g07-task01-public-evidence-one-goal-l2-20261117.yml` — 실제 한 Goal, diagnostic tracer ON; public sanitize/upload/cleanup before private data deletion
- 본 보고서와 `d06/evidence/g07_cm120_task01/*`.

실제 검증 실행 명령(공개 CI 수행):
```bash
python3 -m unittest discover -s d06/tests -p 'test_g07_task01_public_evidence_allowlist.py' -v
python3 -m unittest discover -s d06/tests -p 'test_g07_task01_public_evidence_adapter.py' -v
python3 -m py_compile d06/diagnostic/export_public_cm120_first_gap.py d06/scripts/g07_task01_extract_public_gap.py
cd d06/evidence/g07_cm120_task01
sha256sum -c run_44049067368_SHA256SUMS.txt
```
새 공개 CI + Gazebo 진단은 실제 GitHub Actions에서 실행됐으나 사용자 로컬 WSL2에서 실행한 것은 아니다. 강사 정답 소스/원본 raw는 공개 repo에 commit/Artifact로 게시하지 않았다.

```text
AXIA_G07_PUBLIC_CI_POLICY_NO_PRIVATE_WRITE_SECRET=ADOPTED
AXIA_G07_PUBLIC_L0_ALLOWLIST_AND_ADAPTER=PASS_8
AXIA_G07_PUBLIC_REAL_FIRST_GAP_EVIDENCE_SHA256=PASS
AXIA_G07_TASK01_SAME_OBSERVER_PAIR_TF_NANOSLEEP=PROVEN_9_CALLS_91_416406MS
AXIA_G07_TASK01_ORIGINAL_SOURCE_CLOCK_ALIGNMENT=UNPROVEN
AXIA_G07_TASK01_SCHEDULER_AND_CLOCK_FIRST_GAP_CAUSALITY=UNPROVEN
AXIA_G07_TASK01_REAL_DIAGNOSTIC_MOVING_GOAL_L2=FAIL
AXIA_G07_TASK02=BLOCKED
AXIA_G07_TASK03_TRACER_OFF_RELEASE=NOT_RUN
AXIA_G07_TASK04_OWNER_WSL2=NOT_RUN
CM120_TRACER_OFF_RELEASE=HOLD
AXIA_MVP_DEMO_ACCEPTED=HOLD
CERTIFIED_ESTOP=false
MAIN_MERGED=false
```
