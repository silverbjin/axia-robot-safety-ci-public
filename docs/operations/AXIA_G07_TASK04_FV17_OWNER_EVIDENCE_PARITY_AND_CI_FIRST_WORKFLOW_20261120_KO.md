# AXIA G07 Task04 — FV17z53O Owner 수치 검증 실패 원인과 CI-First 작업 흐름 개선안

**2026-11-20 / 시연 범위:** ROS 2 Jazzy, Gazebo Harmonic, 공식 Nav2·TurtleBot3 Waffle, 기존 Safety Supervisor·CM·Guard. `main`의 교육용 MVP Baseline은 그대로 유지한다. 새 수동 WSL2 실행에 앞서 공개 CI에서 재현 가능한 부분을 먼저 검증한다.

## 1. 업로드 원본 검증

- `owner-moving-FV17z53O.tar.gz`: SHA256 `250c566d4182e8004d7510afecfb838bc4df5a3f4b181b5fa569a7284ec2c2fd`; 첨부 sidecar 일치
- `owner-moving-FV17z53O.diagnostics.zip`: SHA256 `bf619c3969a76c38c21999d272e2dc8a2e9e0a9abb37bdaadd6dbd813df81f0a`; 첨부 sidecar 일치
- TAR 외부 manifest **80개 이상 경로**와 내부 native manifest, ZIP manifest 22개 검증: **mismatch 0**. rosbag2 SQLite `PRAGMA quick_check=ok`, 14개 토픽. 원본 raw bag·개인 경로는 공개 GitHub에 업로드하지 않음.
- 실제 Student source SHA `43a26a2f870c0fd99d66d06887cdf4e706b637b7`, 당시 Public Owner `9e1ad0e86bb0822b2050b46bc7055732666a9307`, 공개 L2 기준 `#44557868822`.

## 2. 시연 실제 물리 증거는 PASS, Owner numerical은 HOLD

- Native `ci_moving_goal_result.json`: `goal_sent=true`, Goal status EXECUTING, 동일 UUID `1b5ef842f49645ab9ca422fd4ae64666` 정확 취소(5), CLEAR 이동 **0.120475m**, 전체 odom 이동 **0.133818m**, SLOW 전방 **0.672139m**, 최종 velocity **0.015307m/s**, STOP 전방 **0.380903m**와 **0m/s**, 정지 유지 **1.015769초**.
- 실측 host monotonic 간격: Clock max103.815ms, CM callback max80.995ms, Guard status max74.893ms, Odom max141.475ms, Scan max213.166ms, Supervisor max87.068ms. `first_timing_violation=null`, `guard_latched=false`.
- Nav2 Navigation shutdown ACK **3.0743초**, Localization ACK **0.33369초**, CM child exit0, Gazebo·RViz X11 2/2. Certified E-Stop `false`; software stop만 확인.
- Owner `task04_owner_numeric_review.json`: **19/21 checks true**, `cm_source_and_observer_120ms=false`, `guard_internal_150ms=false`. 실제 원본 `first_failure=NATIVE_NUMERICAL_REVIEW_BLOCKED`는 최종 래퍼 메시지이며, strict review 첫 false는 `cm_source_and_observer_120ms`.

## 3. 원인이 된 원본 코드의 증거 계약 불일치

**첫 번째:** Guard `p2_base_guard_node.py`는 `GITHUB_ACTIONS=true` AND `AXIA_G07_TASK03_FORMAL_CI=1`일 때에만 `cm_age_sec`, `supervisor_age_sec`, `guard_ever_moved`를 기록했다. Owner 원샷은 의도적으로 CI 권한과 Formal CI 환경변수를 사용하지 않는다. 실제 Goal 구간 Guard status **163개 중 내부 타이밍 필드 0개**이므로 Guard verifier는 영구적으로 `GUARD_INTERNAL_CM_AGE_UNVERIFIED_HOLD` 상태였다.

**두 번째:** 기존 Task02 `d06/diagnostic/g07_task02_strict_gate.py`는 `CI_GAZEBO_MOVING_GOAL_CANDIDATE`만 허용했고, 실제 Owner의 `NUMERICAL_CANDIDATE`를 맨 앞에서 `TASK02_ACTUAL_GOAL_OR_GUARD_UNVERIFIED_HOLD`로 반환했다. 그래서 이미 존재한 실제 RMW CM 메시지 164개와 연속 publish sequence를 분석하지 못했다.

**세 번째:** 미리 거부된 strict gate의 입력을 더 분석하자, Owner ROS event host monotonic은 정상 증가하나 다음 두 채널의 `rmw_source_ns`와 `rmw_received_ns`가 같은 구간에 약 **6.68초 역행**했다.

| 채널 | 이전 순번 → 다음 순번 | source 시각 이전 → 다음 (ns) |
|---|---|---|
| `/cmd_vel_pre_guard` | 132 → 133 | `1795134992890347373` → `1795134986208843701` |
| `/cmd_vel_supervised` | 1403 → 1404 | `1795134992888535010` → `1795134986207769576` |

같은 전이에서 Observer callback gap 약 54ms, 두 채널의 RMW source/receive 시각이 동반 역행. **CM Publisher가 6.68초간 멈췄다는 증거가 아니다.** 가장 가능성 있는 계층은 공통 벽시계/RMW 시간 기반이지만 어느 WSL2 clock sync 프로세스가 조정했는지는 PID/커널/journal 증거가 없어 미확정이다. 기존 `/clock` 복수 발행자 문제와 혼동 금지: 이번 실제 sim `/clock`은 Goal 시나리오를 완료했다.

공식 배경: Ubuntu on WSL time sync documentation `https://ubuntu.com/wsl/docs/stable/explanation/time-sync/`, WSL issue `https://github.com/microsoft/WSL/issues/11790`. 문서와 이슈는 **가능한 메커니즘**, 현장 NTP 원인 확정이 아님.

**부수 경고:** RViz GLSL, AMCL 초기 일시적 TF future extrapolation, `bt_navigator`의 FollowPath halt result 경고는 원본에 존재하지만 이번 Goal 정확 취소 및 물리 STOP 증거를 뒤집는 최초 실패가 아니다. Shutdown 이후 Supervisor의 HEALTH_BAD는 CM 비활성화 순서와 분리하여 읽는다.

## 4. 안전 임계치 불변의 최소 수정

- Student PR: 실제 Owner simulation 프로파일 `AXIA_G07_TASK04_OWNER_MOVING_L3=1`, `AXIA_G07_OWNER_STARTUP_PARITY=1`, `AXIA_G07_CI_SIM_GOAL_ALLOWED=0`, `AXIA_P0_SIM_ONLY=1`일 때도 **기존 Guard 타이머 스냅샷을 읽기 전용으로 출력**. Guard FSM, 150ms TTL, ROS 토픽, Nav2 Goal 권한, Output ZERO 모두 불변. 일반 P2/비-시연 실행에서 새 진단 필드 없음.
- Public strict CM verifier: 원래 CI 성공 상태와 **실제 Owner의 provenance가 검증된 NUMERICAL_CANDIDATE**를 동일한 물리·Goal·RMW 검증 계약으로 검사. 잘못된 Owner 출처는 거부.
- RMW source/received timebase 역행은 `TASK02_RMW_TIMEBASE_DISCONTINUITY_HOLD` + 두 토픽·최초 timestamp gap 진단으로 남긴다. 메시지 전달 TTL PASS로 승격하지 않으며, 종전 generic `TASK02_CM_RMW_SEQUENCE_OR_SOURCE_UNVERIFIED_HOLD`와 구분.
- User가 승인한 **교육용 MVP 시연**과 **정식 안전 타이밍 검수**를 분리: 실제 Goal/정지/취소/Guard 내부 <=150ms 및 나머지 20 gate가 true일 때에만 RMW timebase formal HOLD를 유지하며 교육용 수치 후보로 보고할 수 있다. 어떤 필드가 누락되거나 실제 CM callback 기간이 기준을 넘으면 절대 적용하지 않는다. 현장 육안 리뷰 전 `axia_mvp_demo_accepted=true`가 되지 않음.

## 5. CI-First 변경 관리 표준 (이후 모든 Owner 오류에 적용)

| 단계 | 위치·수행 | 반드시 제출하는 증거 | 완료 조건 |
|---|---|---|---|
| 0 원본 보전 | WSL2에서 얻은 TAR/ZIP은 비공개 보관, 분석은 CI용 작은 회귀 수치만 채택 | SHA256, 최초 타이밍/상태 경계, 오류보다 앞선 event chronology | 실패 분류 명확 |
| 1 계약 RED | 공개 Student L0 + Public CI L0 | **Owner/CI 환경 프로파일 매트릭스**, 빠진 필드/상태, 오염/빈 데이터 실패 재현 | 예상 FAIL |
| 2 최소 GREEN | 기존 Supervisor/CM/Nav2 코드 변경 금지, Guard 읽기 전용 필드와 검증기만 수정 | 300/120/150ms 불변, 누락/invalid 증거 fail-closed, 시각 역행 별도 HOLD | 실제 테스트 GREEN |
| 3 실제 통합 L2 | 공개 1회 실물 Gazebo Waffle + Nav2 Moving Goal | Goal UUID, CLEAR/SLOW/STOP, 정지 dwell, 14-topic bag, 양 GUI, source+observer RMW 연속성, Guard 내부 틱, 두 safety child exit0 | **실제** Run 결과가 Success; 원본 실패 구간만 재현 |
| 4 출고 PIN | Public Owner script fixed Student + Public Review SHA + L2 Run | 이 세 값 상호 일치, `bash -n`, `--self-check`, artifact allowlist, 권한 오인 차단 | Public CI success **이후** 브랜치 출고 |
| 5 최종 인수 | Owner WSL2 1회, 수동 Goal 승인 | `task04_owner_numeric_review.json`, `domain_selection.json`, 2 GUI, 최초 Guard latch/타이밍, SHA, 원본 차일드 exit | L3 scope 증거 판정, 누락은 CI 회귀로 환원 |

**금지:** WSL2 같은 오류 반복 재시도, 코드 없이 오직 CI unit만 PASS로 출고, `GITHUB_ACTIONS=true`를 Owner에서 가짜로 설정하기, 실측 없는 timing PASS/인증 E-Stop 승인, 자동 `main` 병합.

## 6. 검증 결과 표시 규칙

- `DEMO_PHYSICAL_CANDIDATE`는 실제 CLEAR/SLOW/STOP/Goal 취소 근거가 있고 Guard 내부 증거도 만족할 때만.
- `FORMAL_RMW_TIMEBASE=HOLD`는 source/received clock provenance를 복구하지 못한 사실을 보존하는 것이지 물리 시연 실패로 선고하는 것이 아니다.
- `OWNER_L3_ACCEPTED=false`는 사용자 WSL2 최종 검증 전까지 유지.
- `CERTIFIED_ESTOP=false`, `FORMAL_SAFETY_TIMING_ACCEPTANCE=NOT_CLAIMED`.
- 일시적 종료 경고와 안전 감시 수신 주기는 분리해야 하며, 어떤 계층의 300/120/150ms 타이밍 검증도 생략·완화하지 않는다.

## 7. 진행 상태

- 공개 L0 증거 프로파일 및 timebase 회귀: RED→GREEN 확보.
- 신규 학생 브랜치에서 실제 Owner Guard 내부 증거 출력 enabled, CI 모드 원형 유지.
- 공개 실제 Gazebo L2 [Run #44652361407](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44652361407) **SCOPED PASS**. Student SHA `5c7983598fa3bcd7148433a06f37a4e78b091273`, public workflow SHA `9825c4e2d675f7a6dbf6cfcf58e84d446fd53706`. 실제 Gazebo Harmonic + Nav2 + RViz2 Waffle Moving Goal runner rc0, Gazebo/RViz 양 창1+1, Guard/Supervisor 실제 child exit0, 실제 Guard 내부 CM 수신 나이 **129 samples / max 11.071574ms** (<150ms), 원본 CM RMW 발행·Observer 120ms strict 검증 `TASK02_PUBLIC_L2_NUMERICAL_CANDIDATE`, 동일 실제 ROS 이벤트의 CI/Owner *오프라인 판정 투영* 일치. 가짜 Owner L3 권한을 생성하지 않았음.
- 실패 증거도 그대로 보존: [Run #44650103452](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44650103452)는 실제 Goal 및 취소 이후 Nav `SERVICE_MISSING:/lifecycle_manager_navigation/get_parameters`를 보고. 같은 공식 60초 총 종료예산에서 해당 읽기 전용 파라미터 서비스 탐색만 3초→최대 8초로 조정, 서비스/실제 ACK 없으면 여전히 BLOCKED. [Run #44652034063](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44652034063)는 STOP 중 **첫 Guard 래치 원인 `UPSTREAM_STALE_AFTER_MOTION`, 실제 Guard 내부 CM age 188.578ms/기준150ms, 독립 Observer age 173.465ms**. 정확 Goal 취소와 통합 인수까지 도달하지 않아 정상 시연 PASS 금지. 원인 추적 [OPEN Issue #157](https://github.com/silverbjin/axia-robot-safety-ci-public/issues/157)과 연결. 이후 성공으로 이 최초 전이 증거를 지우지 않음.
- 신규 공개 CI 원샷 출고는 `STUDENT_SHA=5c7983598fa3bcd7148433a06f37a4e78b091273`, `REVIEW_SHA=362da68e31dd163a8d321601e191069c0d0a438b`, `CI_L2_RUN=44652361407`로 고정하며, 원본 엄격 사후검증이 FIRST, 교육용 Scope classifier는 오직 진단된 RMW timebase HOLD + 그 외 20가지 실제 조건 참일 때만. `FIRST_FAILURE=FORMAL_RMW_TIMEBASE_HOLD_ONLY`와 원래 `cm_source_and_observer_120ms` 실패명 모두 증거에 보존.
- **새 Student/Owner WSL2 현장 L3 NOT_RUN**, 공식 safety timing 인수 NOT_CLAIMED. L2 1회 성공과 별도의 Guard 래치 실패가 있어 전 조건에서 반복 안전성 PASS를 주장하지 않음.
- Owner 원샷 새 Student SHA/Review SHA 고정 및 사용자 WSL2 L3: 검증 성공 전까지 출고 금지, 미실행. 기존 교육용 baseline은 ACCEPTED 유지.


## 8. 재현된 간헐 Guard 래치와 최종 공개 CI 출고 게이트

User WSL2 최초 `FV17z53O`와 별개의 **실제 공개 CI** [#44652034063](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44652034063)에서는 STOP 중 최초 Guard `UPSTREAM_STALE_AFTER_MOTION` 상태 전이가 발생하였다.

- Guard 실제 `cm_age_sec=0.188577986`초 **> 150ms** (실제 안전 타이밍 위반)
- 독립 Observer `CM age=0.173465091`초, 약 15.112895ms 더 최근 CM 수신 사실. Supervisor age `0.040541022`초, Supervisor는 정상 연속 수신
- `observer_newer_cm_samples=1`, 따라서 CM publisher 종료로 단정할 수 없음. 원인 후보는 CM 소스 일시 지연 / 독립 Observer와 Guard의 DDS-RMW 전달 차이 / 프로세스 스케줄링. Guard는 **정책대로 안전 ZERO + 영구 latch**를 적용했으며 Goal 취소 시연은 해당 실행에서 완료되지 않았음.
- 다른 실제 공개 CI [#44652361407](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44652361407)은 실제 Moving Goal·양 GUI·정상 종료·Guard 실제 129틱 / 최대 11.071574ms의 CM age로 **SCOPED PASS**. 이전 실패를 성공으로 덮어쓰면 안 됨.
- 이 간헐 안전 이슈는 기존 공개 [OPEN Issue #157](https://github.com/silverbjin/axia-robot-safety-ci-public/issues/157)과 연결하며, 인증된 하드웨어 E-Stop이라고 오인해서는 안 됨.

**추가 최종 공개 CI 게이트:** `.github/workflows/axia-g07-fv17-owner-evidence-parity-native-l2.yml`의 하나의 source SHA를 별도 Ubuntu 24.04 + Gazebo Harmonic 컨테이너 두 개에서 독립 실행(matrix cycle 1/2)한다. 두 사이클 모두 실제 Gazebo Waffle LiDAR/TF, AMCL/Nav2 Goal, Goal 정확취소, 14토픽 rosbag, 실제 Guard 내부 CM 150ms, CM 발행/Observer 120ms, Scan 300ms, 양 안전 노드 exit0, 공식 Nav2 lifecycle ACK를 **실제로** 검사한 경우만 해당 출고 게이트를 성공으로 판단한다. 한 사이클이라도 보호 래치 또는 서비스 ACK 오류 시 **출고 HOLD**, 재시도 반복 대신 해당 최초 안전 상태 전이/타이밍 위반을 공개 CI 이슈에 추가한다. 테스트 실행 후 증거 URL·각 job verdict·고정 SHA를 보고한다.

이는 MVP 검증을 과도하게 늘리는 것이 아니라, 실제로 관측된 간헐 Guard 188.578ms 안전 경계 한 가지를 **강사 WSL2 대신 공개 CI에서 차단하기 위한 최소 2회 독립 게이트**다. 공식 CM/Guard TTL과 기존 물리 시연 경로는 불변이다.

**최종 독립 2-cycle 실증:** [Run #44653465671](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44653465671) `SUCCESS` (동일 Student `5c7983598fa3bcd7148433a06f37a4e78b091273`, 공개 workflow SHA `85a530babfdd55e0b0afb7b4aae8273aa1e0fae5`). Cycle 1: 실제 native runner RC0, Gazebo/RViz 1+1, Guard/Supervisor exit0, Guard 내부 age **164 samples / max53.664037ms**. Cycle 2: 동일 RC0·GUI·exit0, Guard 내부 age **126 samples / max52.396081ms**. 두 사이클 모두 **동일 Goal 실증·CM source/Observer strict120ms·Guard150ms·Owner/CI 오프라인 검증 계약**을 통과했다. 기존 [#44652034063](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44652034063)의 첫 188.578ms Guard latch는 원인 미확정으로 Issue #157에 남긴다. 이 결과는 WSLg/WSL2 실제 L3 검증이나 보편적 신뢰성 보증이 아니다.
