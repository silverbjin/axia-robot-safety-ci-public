# AXIA G07 Task 03 — 실제 공개 Gazebo L2 최종 인수 및 교육용 원인 분석

**판정일: 2026-11-18 KST.** Task03는 **COMPLETE_PUBLIC_FORMAL_L2_SCOPED**, 전체 제품은 **HOLD**입니다.

## 1. 확정 실행·원본 증거

최종 실제 공개 GitHub Actions [Run #44223320904](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44223320904), Job **134530314861**, 최종 상태 **completed/success**, 실제 원본 실행기 rc=0입니다. 작업은 ROS 2 Jazzy, Gazebo Harmonic, 공식 Nav2, TurtleBot3 Waffle의 저속 단일 Moving Goal로 진행했습니다. TF preload/LTTng tracer는 OFF이며 비공개 CI 및 강사 비공개 저장소를 사용하지 않았습니다.

- **정확 CI 소스 SHA:** 6bc8b0711ab056e63e100f3eede2c5f06cdf3856
- **정확 공개 학생 소스 SHA:** 01752add2e30c90c4d3286ef3a450f97746ecb55
- **실제 공개 Artifact:** ID 14391079934, axia-task03-formal-public-numeric-44223320904, 3457 bytes
- **ZIP SHA256:** 68652c89259c463ce471b5a8747b5abd6b4ee540ef726d202117e8ac221d167a
- **내부 정식 JSON SHA256:** d14ece50308c7dabf028ed1d30113b547c9b8b396e6be03933f70c8989b090d1
- **내부 Contact 양성 JSON SHA256:** 0cc9f1c7d579f604ba57cc906d56dbacce592aaf1458492cba3fdbd386150a4e
- **정확 파생 Evidence:** [run_44223320904_formal_public_l2.json](../evidence/g07_task03/run_44223320904_formal_public_l2.json). 원본 ZIP과 양쪽 JSON을 다운로드해 직접 SHA256 및 JSON 파싱을 확인했습니다.

공개 ROS 환경 패리티는 **25개 패키지·공식 파일 5개 PASS**입니다. 실제 WSL2/WSLg/GPU 패리티는 **미확인**입니다.

## 2. 교육용 디버깅 사례: 첫 위반 → 단일 가설 → RED → GREEN → 실제 재인수

각 항목은 **서로 다른 Run의 성공·실패를 합쳐 PASS 판정을 만들지 않았습니다**. 이전 정식 성공 [#44215546368](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44215546368)은 [기존 보고서](./AXIA_G07_TASK03_FINAL_PUBLIC_FORMAL_GAZEBO_L2_20261118_KO.md)에 역사적 증거로 보존합니다.

### Cycle A. 보조 양성 Contact JSON 직렬화 오류

실행 #44215546368의 정식 Contact0·Guard150·CM120·Bag14·Goal 및 shutdown 판정 JSON은 유효했지만, 별도 양성 보조 JSON의 마지막에 실제 개행이 아닌 리터럴 역슬래시-n 두 글자가 붙어 일반 JSON 파서가 실패했습니다. 원본 ZIP/SHA는 불변으로 유지하고 정상 LF로 바꾼 **별도 보존본**과 provenance를 생성했습니다. 향후 workflow 직렬화도 수정하고 [GREEN #44217623571](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44217623571)에서 JSON 파서·정확 SHA·불변 증거 회귀 **3/3 PASS**를 확인했습니다. **이 수정으로 실제 물리 주행을 다시 성공했다고 주장하지 않습니다.**

### Cycle B. NO_GOAL Contact 양성 월드의 Lifecycle 서비스 소실

실제 #44217387168과 #44218557392에서 폐기할 NO_GOAL 월드의 Contact 양성은 관찰됐지만 Navigation 서비스 소실/종료 ACK 시간 초과가 다음 Goal 실행을 차단했습니다. 양성 접촉은 **센서 원본 검증**이지 Nav2 Goal shutdown 인수가 아님을 구별했습니다. [RED #44218021537](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44218021537) → [GREEN #44218323983](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44218323983)로 NO_GOAL 증거 경계를 격리하고, 전용 공개 sim-only NO_GOAL 양성 월드에만 SIGINT graceful 정리를 적용하는 [RED #44219147757](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44219147757) → [GREEN #44219837011](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44219837011) **6/6**을 확보했습니다.

**안전 경계:** 반드시 Contact 양성, Goal 미전송, graceful teardown, 강제 SIGKILL 없음, 잔존 프로세스 0, 새 ROS_DOMAIN_ID 및 GZ_PARTITION입니다. 실제 Moving Goal의 Navigation/Localization ACK는 절대 면제하지 않습니다.

### Cycle C. 새로운 NO_GOAL 종료 경로와 증거 파일 계약 불일치

실제 [RED #44220702329](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44220702329)에서 양성 Contact·직접 SIGINT·rc=0이었으나 판독기에 필요한 g07_ordered_shutdown.json이 없어 FileNotFoundError로 FAIL이 났습니다. **Moving Goal 시작 전** 실패입니다. 기존 NO_GOAL 실행 스크립트에 실제 SIGINT 및 P2_L2_GRACEFUL_TEARDOWN 이후에만 JSON을 생성하도록 최소 수정했습니다. 전용 JSON에는 DISPOSABLE_NO_GOAL_DIRECT_SIGINT_CONFIRMED, navigation_ack=false, localization_ack=false, goal_sent=false, native_nav2_l2_pass=false를 명시해 종료 ACK를 조작하지 않습니다. [GREEN #44221365382](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44221365382) **7/7**. 이때 실제 Gazebo [#44221460587](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44221460587)은 NO_GOAL 양성 5409 Contact, 21314 physics frame, 누수 0을 확인하고 Moving Goal로 진행했습니다.

### Cycle D. STOP/Goal CANCELED 이후 Localization Lifecycle 응답 13초 한계

실제 #44221460587의 첫 Goal 주행 자체는 CLEAR→SLOW→STOP, **0.2111m 이동, 1.013초 odom 정지**, 정확 UUID 3798c76844e445ad9d48b146d896995d CANCELED, CM/Guard/Scan/Odom/Clock 주기 PASS였습니다. 그러나 **Navigation ACK=true / Localization ACK=false**, 상태 BLOCKED_LIFECYCLE_LOCALIZATION_SERVICE_TIMEOUT으로 종료 인수는 FAIL이었습니다. 정상 Goal 성능을 먼저 인정하되 전체 PASS로 승격하지 않았습니다.

코드 진단: 학생 tools/p2_g07_ordered_shutdown.py의 전체 종료 deadline은 **60초**, Navigation response cap **40초**, Localization response cap **13초**였습니다. Nav2 종료 시 lifecycle 비활성화·정리·종료 응답 지연의 경계이므로 **post-STOP Localization response cap만 최대 30초로 조정**하고 전체 60초 deadline, Navigation 40초, 실제 두 ACK 강제 및 CM clean process exit를 유지했습니다. CM120·Guard150·Scan/Odom/Clock300·STOP/SLOW polygon·Nav2 소스·cmd_vel·source_timeout에는 **변경 없음**.

- RED: [#44222527136](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44222527136), 신규 shutdown_stage_budget 함수 없음으로 ImportError; **ROS Goal 시작 전 종료**.
- GREEN: [#44223053492](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44223053492), NO_GOAL 7 + post-STOP Lifecycle 3 = **10/10 PASS**, ACK 없으면 여전히 FAIL.
- 실제 재인수: [#44223320904](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44223320904), 전체 **L0 29/29 PASS + 실제 Gazebo L2 completed/success**. 동일 단일 Goal에서 두 Lifecycle ACK, CM child clean exit, Contact0 및 SQLite14를 함께 확보했습니다.

## 3. 최종 공개 Gazebo 동일 실행 실측 (원본 한 Run)

| 계약 | 실측 | 결과 |
|---|---:|---|
| Native NO_GOAL Contact 양성 | 5664건 / 26342 physics frame, 별도 월드 종료·누수 0 | PASS (센서 검증만) |
| 독립 Moving Goal S02 Contact | **0건 / 32955 physics frame** | PASS (대상 S02 충돌 센서) |
| CLEAR LiDAR / 최종 속도 | 2.042136m / 0.037533m/s | PASS |
| SLOW LiDAR / CM 감속 속도 | 0.738948m / 0.011590m/s | PASS |
| STOP LiDAR / CM & final | 0.390879m / **0.0m/s** | PASS |
| 실제 displacement / odom ZERO dwell | **0.2111m / 1.013초** | PASS |
| CM RMW source max gap | **56.642455ms** / 120ms, 연속 publisher 483쌍 | PASS |
| CM Observer max gap | **71.462708ms** / 120ms | PASS |
| Guard 내부 CM 수신 age | **53.971531ms** / 150ms, 첫 실제 이동 후 479샘플 | PASS |
| Guard / Supervisor 주기 | 76.481 / 75.730ms | PASS |
| Scan / Odom / Clock 주기 | 199.253 / 153.974 / 105.375ms, 각각 300ms | PASS |
| 실제 Nav2 Goal UUID | 99e27f7a45b04e9890b17f81dc453f20, native ActionStatus **5=CANCELED** | PASS |
| Nav2 및 CM shutdown | Navigation ACK, Localization ACK, CM process clean exit | PASS |
| 공식 원본 판정 | **first_failure=NONE**, rc=0 | PASS |

Guard 초기 NO_FRESH_PAIR의 오래된 CM age는 *최초 비영속도 전달 이전* ZERO 상태입니다. 실제 Guard 내부 read-only guard_ever_moved 전이를 원본 same-tick status로 관찰한 뒤, 이동 이후 모든 샘플에서 CM age **150ms를 위반하면 반드시 FAIL**하도록 판정합니다. 더 이상 최초 안전 전이를 단순 Goal timestamp로 대체하지 않습니다.

### 실제 rosbag SQLite14 원본 custody

원본 rosbag DB를 공개 CI 컨테이너에서 SQLite mode=ro로 열어 quick_check=ok, 14토픽 모두 실제 메시지 count>0, 메타데이터 및 원본 DB SHA256을 계산했습니다.

| 토픽 | count | 토픽 | count |
|---|---:|---|---:|
| /clock | 32844 | /tf | 4891 |
| /tf_static | 1 | /map | 1 |
| /scan | 986 | /safety/scan | 986 |
| /odom | 2737 | /cmd_vel_smoothed | 505 |
| /cmd_vel_supervised | 2026 | /cmd_vel_pre_guard | 641 |
| /cmd_vel | 2026 | /axia/safety/state | 2026 |
| /axia/p2/base_guard | 2027 | /navigate_to_pose/_action/status | 3 |

SQLite SHA256 **807721884f63da47355e8f543077cc1323b7f2712f02679e051217aa4d79c9cb**, metadata SHA256 **40798362ed48ea932cf4da83cccfbedf9d398add0973cb959654d37717dc9ce4**. 원시 rosbag 자체는 외부 공개 artifact에 포함하지 않아 **오프라인 독립 재생은 미검증**입니다. 공개 자료는 SHA와 수치형 JSON만 보존합니다.

## 4. 실행 명령과 코드 경로

기준: 공개 학생 저장소의 block_B/day07/h01_runtime 루트, 공개 CI workflow .github/workflows/axia-g07-task03-formal-public-l0-l2-20261118.yml.

~~~bash
# 실제 공개 CI에서 실행된 L0 테스트
python3 -m unittest discover -s tools -p test_g07_task03_formal_evidence.py -v
python3 -m unittest discover -s tools -p test_g07_task03_calibration_cleanup.py -v
python3 -m unittest discover -s tools -p test_g07_task03_localization_shutdown_budget.py -v
python3 -m unittest discover -s tools -p test_g07_task02_simple_tf.py -v
PYTHONPATH="$GITHUB_WORKSPACE/ci" python3 -m unittest discover -s "$GITHUB_WORKSPACE/ci/d06/tests" -p test_g07_task02_public_strict_gate.py -v
PYTHONPATH="$GITHUB_WORKSPACE/ci" python3 -m unittest discover -s "$GITHUB_WORKSPACE/ci/d06/tests" -p test_g07_task03_numeric_artifact_contract.py -v
bash -n scripts/p2_no_goal_smoke_ci.sh
cmake -S tools/native_s02_public -B "$GITHUB_WORKSPACE/task03-native-build" -DCMAKE_BUILD_TYPE=Release
cmake --build "$GITHUB_WORKSPACE/task03-native-build" --parallel 2

# 실제 공개 runner에서 분리 실행: NO_GOAL positive 이후 새로운 ROS_DOMAIN_ID/GZ_PARTITION에서 Goal 1회
env -u LD_PRELOAD -u AXIA_G07_TASK01_TF_AVAIL_PROBE timeout --signal=TERM --kill-after=10s 900s bash scripts/p2_no_goal_smoke_ci.sh

# 실제 같은 Goal의 읽기 전용 native/SQLite/Guard/CM 판정
python3 tools/p2_g07_task03_review.py --positive-root ... --motion-root ... --positive-witness ... --motion-witness ... --output public_evidence/task03_formal_verdict.json
~~~

핵심 변경 파일: 학생 tools/p2_g07_ordered_shutdown.py 및 tools/test_g07_task03_localization_shutdown_budget.py, scripts/p2_no_goal_smoke_ci.sh, tools/test_g07_task03_calibration_cleanup.py, tools/native_s02_public/{s02_witness.cc,CMakeLists.txt}, tools/p2_g07_task03_{contract,review,calibration_cleanup,ecm_positive}.py, Guard node의 sim-only read-only status, CI 본 workflow 및 공개 원장. **기존 공식 Nav2/TB3 경로를 재사용**했습니다.

## 5. REVIEW, 보존 및 인수 경계

이번 최종 결정은 L0 GREEN 뒤에만 원본 Jazzy/Harmonic Moving Goal을 실행했고, 실제 최초 위반이 있었던 NO_GOAL 종료·Localization 종료에만 최소 변경을 적용했습니다. 이미 성공한 Contact0·CM120·Guard150·SQLite14를 매번 새로운 기능으로 개발하지 않았습니다. 기존 TTL·STOP zone·공식 Nav2를 변경하거나 다른 계층의 타이밍 검증을 생략하지 않았습니다.

- **Task03:** COMPLETE_PUBLIC_FORMAL_L2_SCOPED, 최종 Run #44223320904의 **단일 시뮬레이션 시연 범위 내 인수 PASS**.
- **Task04:** 실제 강사 WSL2/WSLg Gazebo GUI·RViz2 라이브 시연 L3 **NOT_RUN**. 공개 runner의 Azure 커널/헤드리스 환경이 Owner WSL2와 동일하다고 주장하지 않음.
- **하드웨어 안전:** 미검증. Task02의 공식 Nav2 Simple TF base_shift_correction=false는 공개 저속 시뮬레이션에서만 허용하는 성능/시간보정 정확도 절충. 다른 속도·센서지연·사람 및 전체 충돌 기하 안정성 인증 아님. SW STOP은 certified E-Stop이 아님.
- **Git:** 공개 Student 및 공개 CI 개발 브랜치만, Draft PR에 보관하며 **main 병합 없음**. 비공개 Instructor/CI 사용 없음.

~~~text
AXIA_G07_TASK03=COMPLETE_PUBLIC_FORMAL_L2_SCOPED
AXIA_G07_TASK03_PUBLIC_CI_RUN=44223320904
AXIA_G07_TASK03_PUBLIC_L0=PASS_29_OF_29
AXIA_G07_TASK03_ACTUAL_PUBLIC_GAZEBO=PASS_SCOPED
AXIA_G07_TASK03_FIRST_FAILURE=NONE
AXIA_G07_TASK03_S02_CONTACT_ZERO=true
AXIA_G07_TASK03_CM_SOURCE_MAX_MS=56.642455
AXIA_G07_TASK03_CM_OBSERVER_MAX_MS=71.462708
AXIA_G07_TASK03_GUARD_CM_AGE_MAX_MS=53.971531
AXIA_G07_TASK03_SQLITE14_ACTUAL_COUNTS_SHA256=PASS
AXIA_G07_TASK03_EXACT_NAV2_GOAL_TERMINAL=CANCELED
AXIA_G07_TASK03_NAVIGATION_LOCALIZATION_ACK=true
AXIA_G07_TASK03_CM_CHILD_CLEAN_EXIT=true
CM120_TRACER_OFF_RELEASE=PASS_PUBLIC_L2_SCOPED
AXIA_G07_TASK04_OWNER_WSL2_L3=NOT_RUN
AXIA_MVP_DEMO_ACCEPTED=HOLD
CERTIFIED_ESTOP=false
MAIN_MERGED=false
~~~
