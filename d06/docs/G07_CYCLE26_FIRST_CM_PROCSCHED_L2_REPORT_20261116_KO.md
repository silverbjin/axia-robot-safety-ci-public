# AXIA G07 Cycle 26 — 첫 CM 발행 공백 구간의 스케줄러 집계 (교육용 디버깅 보고서)

**날짜:** 2026-11-16. **판정:** 공개 sealed L0 PASS, 실제 Gazebo/공식 Nav2 L2 실행 **FAIL(출고 120ms 미달)**, WSL2 Owner L3 미실행, `AXIA_MVP_DEMO_ACCEPTED=HOLD`.

## 기준선과 원본 사건

- 기존 Owner WSL2 동일 원본 최초 Guard `UPSTREAM_STALE_AFTER_MOTION`, CM age `174.184617ms` >150ms hard, RMW source gap `186.714207ms`, 4 Supervisor 원본 발행. 구형 실행 잠금·raw·인수 증거는 보존.
- 기존 실제 CI 최신 실패: Cycle22 #43792753212 CM RMW source 142.776ms, Cycle23 #43794087620 source 142.906ms, Cycle25 #43795773109 source 142.086ms, 각각 120ms 출고 목표 실패. Stop/Cancel/shutdown 단일 Goal 실제 증거를 전면 재시험하지 않음.
- CPU 역할만 바꾸는 반복 추측 실험 중단. 공식 Nav2/CM와 Guard 150ms TTL, 120ms 출고 목표, software stop과 certified E-Stop 구분을 유지.

## TDD 및 소스/경로

- Instructor 작업 브랜치: `fix/g07-cycle26-first-cm-gap-proc-sched-20261116`, 검증 대상 private SHA `57b553b1b9a8cdfa68de0d5a58a20881bac99478` (이 시점의 HEAD, 이 문서는 public에만 기록).
- RED 테스트 `tests/unit/test_g07_cycle26_first_cm_gap_scheduler_probe_20261116.py` (8개): FIRST >120ms CM RMW 발행 구간과 같은 mono 관측 interval에서 proc schedstat runqueue/CPU exec 구간 확보; CM sequence/clock 불연속, 원본 부재 fail-closed.
- GREEN 최소 변경 `tools/p4_g07_proc_sched.py`: 원래 STOP RPC 기간에만 하던 owned CM /proc sampler를 최대 640회, 최소 간격 50ms로 한 번의 Goal 중 bounded read-only 측정 가능하게 확장. 새 ROS node/Goal/publisher 없음, /proc write·affinity·안전 정책 변경 없음.
- Owner/CI 동일 경로 `tools/p2_g07_ci_moving_goal.py`: Goal 전 sampler start, Observer flush 후 stop, RMW source의 최초 >120ms 공백 및 Observer monotonic 구간에 해당하는 CM 스케줄러 run_ns/wait_ns 차만 기록. 결과 `first_cm_source_gap_schedstat`, 출력 `AXIA_G07_FIRST_CM_SOURCE_GAP_SCHEDULER_WINDOW`. 인과 확정 금지/Owner Goal 승인 금지.
- 공개 sealed L0 [Run #43799310243](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43799310243): `TEST_CYCLE26_FIRST_GAP_RC=0`, `TEST_FIELD_RC=0`, 신규 8개 + 기존 tests PASS; NO_ROS_NO_GOAL. Workflow SHA `98f67441d3bc28e267813d26638108ba43685adb`.
- 실제 CI GUI/Xvfb Gazebo Harmonic, 공식 Jazzy Nav2, TB3 Waffle 한 Goal [Run #43799429562](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43799429562), workflow SHA `437157ae6f0be55db5fdf77a1293d018e9fc8ac3`: CLEAR, SLOWDOWN, STOP PASS; Goal cancel, ordered Navigation/Localization ACK + CM clean exit, `P2_L2_SMOKE_RC=0`; 그러나 120ms release margin validator FAIL.

## 실제 Cycle26 최초 경계 로그

```text
AXIA_G07_FIRST_CM_SOURCE_GAP_SCHEDULER_WINDOW
 first_cm_source_gap_ms=140.667774
 first_cm_observer_callback_gap_ms=142.649125
 upstream_publications_inside_source_gap=3
 scheduler_sample_coverage_ms=102.315237
 scheduler_samples_in_first_gap=3
 scheduler_thread_count_min=16
 scheduler_thread_count_max=16
 scheduler_run_delta_ms=1.505523
 scheduler_wait_delta_ms=3.248706
 status=FIRST_CM_120MS_GAP_SCHEDULER_VS_EXECUTION_UNDETERMINED
 host_clock_step_excluded=false
 cm_callback_processing_proven=false
 owner_goal_authorized=false
 AXIA_G07_CI_FIRST_120MS_CM_SUPERVISOR_RMW_WINDOW: CM_SOURCE_GAP_EXCEEDS_120MS
 AXIA_G07_CI_MEASURED_MESSAGE_PERIODS: cm=0.142649125 sec
 AssertionError: FIELD_CI_L2_PASS_LOW_MARGIN_OWNER_NOT_READY
```

**해석:** 102.315ms 범위에서 CM 전체 16 threads의 CPU runtime +1.506ms, runqueue wait +3.249ms. CPU busy/CPU runnable starvation을 주요 원인이라고 주장할 근거가 약하다. 나머지는 잠듦/대기/스케줄링되지 않음 중 복수 후보로 남아 있다. /proc 집계는 CM **입력 콜백 시작/종료** 시간과 분리된 관측이므로 입력 DDS 전달, RCLCPP Executor 대기, TF 조회 중 무엇인지는 미확정. 3개 스냅샷 및 host clock-step 미배제는 원인판정에 제한된다.

## 다음 한 사이클

1. 공식 Jazzy `tracetools` LTTng `ros2:callback_start/end` 가능성 확인 (이미 #43795191124에서 ROS2 tracetools 및 lttng user-session+callback trace enable는 PASS, `babeltrace` reader는 미설치).
2. 공개 CI 한정 L1에서 기존 공식 rclcpp demo의 callbacks 추적/기록·파싱 회귀, Goal 없이 성공 증명. 새로운 ROS 안전 노드/공식 Nav2 패치 금지.
3. 이후 같은 안전/GUI 실행기에서 실제 CM 입력 콜백의 실행 duration와 queue gap을 bounded trace로 분해하고, 첫 원인을 확인한 뒤에만 RED→GREEN 최소 수정 진행.
4. 실제 Gazebo L2 **CM release <=120ms**, hard Guard<150ms, Scan/Odom/Clock, S02 contact0, exact Goal Cancel, ordered shutdown까지 녹색일 경우에만 **새 pinned WSL2 Owner 1회 인수용 원샷**을 출고. UI Xvfb != WSLg.
5. 명시적 사용자 승인 없이 `main` 병합 없음. 기존 실패 레코드/잠금 삭제 없음. 원본 private/student 패키지 분리.

**검증 수준:** L0(GREEN) / L2(actual moving run FAIL release margin) / L3 Owner NOT_RUN. `AXIA_MVP_DEMO_ACCEPTED=HOLD`.
