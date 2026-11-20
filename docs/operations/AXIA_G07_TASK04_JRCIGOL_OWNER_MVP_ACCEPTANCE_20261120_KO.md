# AXIA G07 Task04 — jrCIgoGl 강사 WSL2 교육용 MVP Baseline 인수 보고서

**일자:** 2026-11-20  
**새 교육용 기준선 ID:** `AXIA-G07-T04-DEMO-BASELINE-20261120-jrCIgoGl`  
**판정 범위:** **교육용 실물 Gazebo/Nav2 Moving Goal 및 수치 인수 ACCEPTED**. 실제 카메라 화면의 콘텐츠 품질·정식 안전 타이밍 인증·하드웨어 인증 E-Stop 인수와는 별개.  
**기존 기준선:** `AXIA-G07-T04-DEMO-BASELINE-20261119-CZObXAdP` 원본 및 Scan 339.177ms 초과 사례 그대로 보존. 이전 실패를 새 성공으로 소급 변경하지 않음.

## 1. 원본 파일 SHA256·custody 검증

강사 WSL2 사용자 제공 자료를 독립 읽기 전용 검사:

| 원본 | SHA256 |
|---|---|
| `owner-moving-jrCIgoGl.tar.gz` | `2d454845183704d8f53b50dcdbaa48446d1103bfa9f750cc3ce662d9af7684db` |
| `owner-moving-jrCIgoGl.diagnostics.zip` | `92c31af277bc7a64742540a2b9e5c99f13ded4cac51ae1bd1b76f3c16a4dd331` |

- 제공된 SHA256 sidecar 두 개와 위 실제 계산값 일치. ZIP 중앙 디렉터리 무결성 검사 정상.
- TAR 내부 `SHA256SUMS` **80/80**, `native/SHA256SUMS` **61/61** 일치. 누락·불일치 **0**.
- 실제 `rosbag2_0.db3`: SQLite `PRAGMA quick_check=ok`, **14개 ROS 토픽 / 50,172개 메시지**.
- 공식 설치 Nav2/TB3/ros_gz 등 패키지 25개, 공식 파일 5개 패리티. 실제 Student 런타임 `5c7983598fa3bcd7148433a06f37a4e78b091273`, 공개 검증기 `362da68e31dd163a8d321601e191069c0d0a438b`, 공개 2-cycle 실제 Gazebo L2 [#44653465671](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44653465671).
- 사용자 원본 rosbag, 개인 환경 로그 및 압축파일은 **공개 GitHub에 게시하지 않음**. `tests/fixtures/g07_task04_jrcigogl_20261120_public_derived.json`은 공개 가능한 파생 숫자·해시만 포함.

## 2. 실제 Goal → CLEAR → SLOW → STOP → Cancel 및 정지 유지

- 실제 고유 Nav2 Goal `80e9482161224ddd8916931e7b42569e`: 한 번만 발행, `EXECUTING` 확인. 동일 UUID 취소 요청 ACK 및 ActionStatus **5 CANCELED**.
- CLEAR: 실제 odom **0.120132m** 이동 후 장애물 진입, 전방 LiDAR **2.024826m**. 총 실제 이동 **0.137285m**.
- SLOW: 실제 가동 Gazebo 장애물 이동 ACK, LiDAR **0.662775m**; Supervisor **0.045759m/s**, Guard 최종 **0.014534m/s**. 최종 명령 절댓값은 Supervisor 대비 약 **31.8%**.
- STOP: 전방 LiDAR **0.384303m**에서 CM와 최종 명령 **0m/s**, Odometry ZERO 유지 **1.029446초**.
- 실제 Nav2 Navigation·Localization shutdown **각각 ACK** (`3.067629초`/`0.356288초`). Collision Monitor 실제 child exit0, Gazebo/Guard/Supervisor/Nav2 노드 전반 clean process exit; Guard 비예상 Latch 없음.
- **실제 WSL2 GUI 창 탐지:** RViz2 1 + Gazebo 1. 단, 화면 스크린샷/녹화가 원본에 없으므로 지도와 이동 장면의 **시각적 내용·교실 가독성은 미검증**.
- `task04_owner_numeric_review.json`: 21개 strict 검증 전부 **true (21/21)**, `first_failure=NONE`, `cm120.status=TASK02_PUBLIC_L2_NUMERICAL_CANDIDATE`, `guard_internal_cm_age_max_ms=47.653131`.

## 3. 안전 TTL·데이터 전달: 실제 WSL2 한 세션 판정

| 경계 | 최대 관측 | 기존 기준 | 결과 |
|---|---:|---:|---|
| Scan Observer | **253.822ms** | 300ms | PASS |
| CM 실제 RMW 발행 | **68.093ms** | 120ms | PASS |
| CM 독립 Observer 수신 | **70.981ms** | 120ms | PASS |
| Guard 내부 마지막 CM 수신 나이 | **47.653ms** | 150ms | PASS |
| Guard 상태 메시지 간격 | **72.352ms** | 150ms | PASS |
| /odom 메시지 간격 | **140.214ms** | 300ms | PASS |
| /clock 메시지 간격 | **95.591ms** | 300ms | PASS |

- 원본 `actual_ros_events.jsonl` 3,980줄을 확인. `/clock` 시뮬레이션 시간 2,480개 표본: 역행 **0회**. `pre_guard` RMW source 184개 연속 샘플: 역행 **0회**; `supervised` 228개 샘플: 역행 **0회**. 이전 `FV17z53O`의 6.68초 교차 RMW 시간축 불연속 이번 실행에서는 재현되지 않음.
- `/axia/p2/base_guard`의 실제 내부 `cm_age_sec` 필드가 기록되며 `guard_latched=false`. 임의로 TTL을 키우거나 검증기를 무력화하지 않았음.
- **별도 미해결 이슈:** 실제 다른 공개 CI [#44652034063](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44652034063)의 `UPSTREAM_STALE_AFTER_MOTION` Guard 첫 래치 (내부 **188.578ms > 150ms**)는 [Issue #157](https://github.com/silverbjin/axia-robot-safety-ci-public/issues/157)에 OPEN. 이번 WSL2 1회 성공이 그 실행을 PASS로 바꾸거나 재현 불가능성을 증명하지 않음.

## 4. 원본 HOLD 및 경고와 교육용 ACCEPTED의 구분

원본 `task04_owner_verdict.json`은 **`status=HOLD_RAW_REVIEW_AND_VISUAL_PENDING`, `owner_moving_l3_accepted=false`, `axia_mvp_demo_accepted=false`, `visual_content_verified=false`** 입니다. 자동검증기는 로컬 수치 후보만 출력하고 원본 raw/GUI 콘텐츠의 최종 검토를 인간에게 남기도록 설계됐습니다.

이번 별도 원본 검수와 사용자 요청에 따른 **교육용 기능·수치 Baseline 인수 판정은 문서·출고 범위에만 한정**합니다. 원본 상태 JSON을 `true`로 소급 수정하거나, 화면 콘텐츠를 보지 않았는데 `visual_content_verified=true`라고 주장하지 않습니다.

실제 실행 로그의 미해결 비차단 이슈도 보존합니다.

1. `native/g07_ci_moving.log`: 종료 과정에서 `The following exception was never retrieved: cannot use Destroyable because destruction was requested` **2회**. ROS 노드 실제 종료와 Nav2 ACK·CM exit0은 검증됐지만 asyncio/rclpy 비동기 정리 경고의 세부 원인은 미검증. `native/g07_shutdown_audit.json`의 `rclpy_destroyable_warning_observed=false`는 **감시 범위 밖 로그에 있던 경고를 배제하지 못한 한계**이므로 '경고 없음'으로 해석 금지.
2. `native/task04_rviz.log`: `rviz/glsl120/indexed_8bit_image.vert` GLSL shader link **ERROR**와 Message Filter drop 경고. Gazebo/RViz 창 2개는 확인되지만, 실제 지도 렌더링 성공이나 화면 가독성은 **캡처 자료가 없어 주장하지 않음**.
3. 초기 AMCL Initial Pose TF future extrapolation **6ms**, 이후 AMCL pose 수신·TF·Goal·Lifecycle 활성 성공. Controller loop missed-rate 경고도 있으므로 실시간 운영 안정성을 전반 PASS로 과장하지 않음.

## 5. 빌드 캐시·실행성

- 새로운 Student SHA의 첫 실제 Owner 실행은 네이티브 플러그인 **MISS 45.555초**. 동일 캐시/ABI 재실행 시 HIT로 컴파일을 생략하는 경로는 공개 실제 Gazebo8 빌드 L1에서 [#44654295960](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44654295960) PASS (4.170초→0.002초).
- 원본 `startup_timing.tsv`: RViz2 첫 창 감지 **119.915초**, Gazebo 첫 창 감지 **123.978초**, Owner runner 시작 **55.314초**, runner 완료 **174.483초** (모두 Owner 최초 기준 경과).
- 시작 시간 단축은 기존 Owner 캐시를 그대로 보존한 결과이며 첫 새로운 SHA에서 반드시 2분 이하가 되는 것은 아님.

## 6. 승인·배포·교육용 선언

- **`AXIA_G07_TASK04_DEMO_BASELINE=ACCEPTED`** — `20261120-jrCIgoGl` 교육용 실제 Moving Goal 및 수치 증거 인수. 원본 `20261119-CZObXAdP` 도 그대로 보존.
- **`FORMAL_SAFETY_TIMING_ACCEPTANCE=NOT_CLAIMED`** — 한 회의 WSL2 성공과 공개 CI 2-cycle은 인증된 시간 신뢰성·반복 안전성의 보증이 아님.
- **`CERTIFIED_ESTOP=false`** — 시뮬레이션 소프트웨어 안전 정지이고 실제 인증된 하드웨어 E-Stop이 아님.
- **`GUI_CONTENT_VISUAL_VERIFICATION=NOT_EVIDENCED`** — RViz/Gazebo 창 확인과 지도·실제 이동 장면 화면 검증을 혼동하지 않음.

**RED → GREEN → REFACTOR → REVIEW → COMMIT:** 공개 L0에 SHA·21/21·최초 실패·TTL/Guard·원본 HOLD/시각 미검증 계약을 보존하는 `tests/test_g07_task04_jrcigogl_baseline_contract.py`를 추가하여 신규 보고서·파생 수치 fixture가 없는 단계에서 RED를 먼저 확인하고, 실제 증거와 Baseline 문서로 GREEN 검증. 새 플래너·Safety FSM·Guard TTL·ROS 2 Node를 개발하지 않음. PR 검증 후 사용자 명시 승인에 따라 관련 Student 및 Public CI `main`에만 병합한다.
