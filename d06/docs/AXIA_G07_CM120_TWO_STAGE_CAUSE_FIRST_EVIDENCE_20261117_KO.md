# AXIA G07 CM120 — 두 단계 원인 우선 리뷰·실행 증거 (기능 Cycle08 아님)

## Step 1: 최초 아키텍처 리뷰로 회귀, CI·Owner 원본 구분
- C05 exact private baseline `966886c4627deb2bb3b37111fe336eeee6b9ebb4`, public tracer snapshot `202b66eb49001e59a06adecb70dde67a457f0780`, real [Public Run #43995793080](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43995793080).
- **같은 첫 CM source gap:** RMW SYSTEM source 차이 120.172578ms; CM Observer callback gap120.523837ms; exact official C++ `/cmd_vel_supervised` subscription→handle verified, callback wall elapsed81.972669ms and overlap first gap81.972669ms, metadata callback count2, upstream Supervisor 2 publishes, original release margin120ms FAIL.
- C05 trace scope LTTng only `ros2:rcl_subscription_init` → `ros2:rclcpp_subscription_init` → `ros2:rclcpp_subscription_callback_added` and CM-procname filtered `ros2:callback_start/end`. Missing **per-function** `nav2_collision_monitor::Source::getTransform` entry/exit, `nav2_util::getTransform` or tf2 lookup time, kernel schedule/wait exact first vtid. C05 report itself `tf_lookup_causality_proven=false`, `scheduler_causality_proven=false`.
- Official Jazzy source paths: `nav2_collision_monitor/src/collision_monitor_node.cpp::cmdVelInCallbackStamped → process() → Source::getData()`; `nav2_collision_monitor/src/scan.cpp::getData() → Source::getTransform()`; `nav2_collision_monitor/src/source.cpp::getTransform()` selects advanced time-interpolated transform with `base_shift_correction=true`. Control path known **statically** ≠ that function's runtime duration.
- Official Nav2 docs note advanced base-shift costs compute/TF time but also spatial safety precision. C07 NO_GOAL #43999183495 source_timeout1.0, base_shift true, tolerance.02 provenance only; entire L2 shutdown failed lifecycle service timeout. C06/parallel C07 `base_shift=false` / `source_timeout=.3` was **not actually tested on Moving Goal**; cannot claim fix.

## Minimal new evidence: NOT a product change
- Read-only pinned `ghcr.io/silverbjin/axia-g07-runtime@sha256:861ae1df...` inspection workflow `.github/workflows/axia-g07-cm120-tf-direct-capability-l0.yml` (public dev source from immutable C05 commit) checks installed official CM ELF symbol visibility and Linux perf/tracefs uprobe capability **without ROS, simulator, Goal, or new publisher**.
- Need **both** exact TF function entry/exit and the same caller CM callback vpid/vtid, plus host clock anchor and first RMW source gap to prove cause. An exported symbol alone is not sufficient. Kernel uprobe device unavailable ≠ no technical tracing possible anywhere; classify as **current CI noninvasive capability constraint**.
- Do not enable privileged CI, fork official Nav2, change `base_shift_correction`, source_timeout, CPU affinity, 120/150/300ms TTL or stop polygons simply to obtain traces. If direct function boundary cannot be obtained with existing tools, Step 1 verdict `CAUSE_UNPROVEN`, Step 2 **NOT_STARTED**, no additional Moving Goal.

## RED→GREEN→REFACTOR→REVIEW→COMMIT fit for non-functional review
No production code changed in this review: RED/ GREEN implementation contract **not applicable yet**. Existing C05 tests and actual Run preserved. Read-only capability smoke test is infrastructure evidence, **not** a new product regression, release-green, or motion capability. If a single-root-cause product fix becomes justified, it must then follow RED→GREEN→REFACTOR→REVIEW→COMMIT exactly and integrate a single original tracer-OFF Moving Goal.

## Immutable output and safety
Plan: `d06/docs/AXIA_G07_CM120_TWO_STAGE_CAUSE_FIRST_PLAN_20261117_KO.md`, report this file, one preflight workflow, single public branch `review/g07-cm120-2stage-cause-gate-20261117`. No private source or any WSL2 script changed.
Moving public CI/Owner L3: **NOT_RUN_THIS_REVIEW**. `CM_120MS_RELEASE=HOLD`, `AXIA_MVP_DEMO_ACCEPTED=HOLD`, `CERTIFIED_ESTOP=false`. No `main` merge.

## 실제 CI 결과
## 실제 공개 CI 사전검사 — 비침습 TF 계측 가능성

- 원본 소스: Cycle05 public SHA `202b66eb49001e59a06adecb70dde67a457f0780`, private `966886c4627deb2bb3b37111fe336eeee6b9ebb4`. 새로운 제품 기능 또는 Safe/CM/Guard 변경 없음.
- 정확한 사용 이미지: `ghcr.io/silverbjin/axia-g07-runtime@sha256:861ae1df0560f991698d8967193380b1619589ba7770b5e2ca91ea4ef31f0c8e`.
- 실제 [public Run #44002730420](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44002730420), release SHA `496d540f28f867e940467264801d8f2b15e03144`, completed SUCCESS — 오직 바이너리/추적 기능 검사용 L0이며 **ROS/Gazebo/Goal 미실행**.

```text
AXIA_G07_CM120_DIRECT_TF_CAPABILITY_PREFLIGHT
cm_library_candidates=1
dynamic_symbols=Source::getTransform:true, Scan::getData:true, CollisionMonitor::process:true, nav2_util::getTransform:true
kernel_perf_event_paranoid=4
tracefs_uprobe_events_present=false
tracefs_uprobe_events_writable=false
tf_function_entry_exit_recorded_in_cycle05=false
tf_duration_proven=false
goal_sent=false
cm120_root_cause=CAUSE_UNPROVEN
AXIA_G07_CM120_KERNEL_UPROBE_ACCESS_NOT_AUTHORIZED_IN_CI_HOLD
AXIA_G07_CM120_CAUSE_UNPROVEN_NO_GOAL_NO_POLICY_MUTATION
AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false
```

### 검증 수준과 원본 실패의 구분
- 바이너리에서 공식 CM 및 TF 동적 심볼을 확인했다. 하지만 함수 **실행시간**을 측정할 entry/exit tracepoints가 Cycle05에 없으며, 현재 CI 컨테이너에서는 기존 tracefs uprobe endpoint와 쓰기 권한이 확인되지 않는다. `perf_event_paranoid=4`는 원본 sysctl readback. 이를 근거로 **기존 CI 방식으로 직접 TF 시간창을 당장 확보할 수 없다고 판정**한다.
- 다만 최초 사전검사 스크립트에는 `/proc/self/status` CapEff 정규식에 불필요한 역슬래시가 있었다. 따라서 첫 Run 출력의 `cap_perfmon=false`, `cap_sys_admin=false`, `cap_bpf=false`는 잘못된 파싱일 수 있으므로 **검증 근거에서 제외한다**. 커널 설정/tracefs 항목은 독립적으로 검사했으므로 유효하다. 외부/별도 특권 시스템까지 uprobe 불가능하다는 주장으로 확장 금지.
- 이 검사 후 정규식 수정 시 JavaScript `String.replace`의 replacement 패턴 문법으로 워크플로 본문이 잘려 두 workflow-parse 오류 [#44002963615](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44002963615), [#44002989928](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44002989928)가 발생했다. 이것은 **ROS/CM 실패가 아닌 YAML 생성 실수**이다. 원본 기준 전체 YAML 복구 및 CapEff 파서 self-test를 dev branch commit `a1485a8153999fda7d0053de3862b8a64f48d787`에 반영했으며 **해당 수정본의 CI 동적 실행은 하지 않았다**. 잘못된 workflow를 release에서 제거한 cleanup SHA `1ee66b67b7015eb6df97ea93c40fc7c6433d00f1`.
- 신규 일반 tracer, privileged CI, Nav2 source fork 및 현장 WSL2 계측으로 범위를 늘리지 않는 사용자 제약에 따라 Step 1은 `CAUSE_UNPROVEN`으로 닫는다. 이 평가는 공식 코드의 TF 실행 경로가 없다는 뜻이 아니다.

### 두 단계 결과와 중단 판정
- **Step 1: CAUSE_UNPROVEN**. 정확한 C05 콜백 elapsed 81.972669ms와 첫 RMW source 120.172578ms는 이미 확보됐지만, TF 함수 내부 entry/exit와 동일 스레드의 scheduler wait을 실제 측정하지 못했으므로 TF·기타 처리·Executor 원인 분리 불충분.
- **Step 2: NOT_STARTED_CAUSE_UNPROVEN**. 하나의 검증된 원인이 없으므로 `base_shift_correction=false`, `source_timeout=0.3`, CPU affinity, 타이밍 120/150/300ms 완화, STOP/SLOW 거리 수정 모두 금지. Tracer-OFF 원래 public Moving Goal 통합 L2와 Owner WSL2 L3 모두 미실행.
- 필요한 경우 추후 사용자 **별도 범위 승인** 후에만 비침습 추적 권한을 부여한 CI 또는 공식 Nav2 진단 빌드의 안전 영향 검토를 제안할 수 있다. 범위 확대 자동 진행 금지.

### 경로·명령·Git 및 검증
- 재사용: `d06/live/g07_cycle05_cm_callback_window.py`, `d06/live/g07_cycle31_cm_topic_callback_identity.py` (변경 없음). 직접 읽은 공식 소스: `nav2_collision_monitor/src/{source.cpp,scan.cpp,collision_monitor_node.cpp}` (변경 없음).
- 작성: `d06/docs/AXIA_G07_CM120_TWO_STAGE_CAUSE_FIRST_PLAN_20261117_KO.md` (계획 SHA `f48bf90c97b2dac177352b67ef8fe4c7ab231b90`), 본 교육 보고서, `.github/workflows/axia-g07-cm120-tf-direct-capability-l0.yml`.
- 실제 검증 명령: 설치 Jazzy CM ELF `nm -C -D` 및 `nm -C`, `/proc/sys/kernel/perf_event_paranoid` readback, `/sys/kernel/tracing/uprobe_events` 존재/쓰기 여부. 전체 명령은 같은 브랜치의 workflow `run:` 절. 신규 프로덕션 코드 변경이 없어서 제품용 RED→GREEN 테스트는 적용하지 않음.
- 정적 수정/보고서와 원본 Run 증거는 리뷰 브랜치에 보존. private Instructor·Student·main 병합/수정 **없음**.

```text
AXIA_G07_CM120_STEP1=CAUSE_UNPROVEN
AXIA_G07_CM120_STEP2=NOT_STARTED_CAUSE_UNPROVEN
CM_120MS_RELEASE=HOLD
AXIA_MVP_DEMO_ACCEPTED=HOLD
OWNER_WSL2_MOVING_L3=NOT_RUN
CERTIFIED_ESTOP=false
MAIN_MERGED=false
```

### 교육용 토론
1. ROS 콜백 wall elapsed 81.973ms를 TF 함수 실행시간으로 단정하면 왜 안 되는가?
2. 바이너리에서 TF 함수 심볼이 검색되어도 해당 호출 구간을 추적할 권한/tracepoint가 필요하다는 것은 무엇을 의미하는가?
3. 잘못된 CapEff 정규식이 만든 false 출력과 독립 tracefs/perf readback을 어떻게 구분하는가?
4. capability-only L0 workflow SUCCESS가 실제 Safety CM120 RELEASE PASS를 의미하지 않는 이유는?

