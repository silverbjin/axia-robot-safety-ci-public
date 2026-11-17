# AXIA G07 CM120 — 아키텍처 리뷰 정합 단일 원인→단일 수정 게이트 (기능 Cycle08 아님)

## 승인된 범위
2026-11-17 사용자 지시: 새 기능 개발 Cycle08 금지. 단 2단계.
1. 실제 `/cmd_vel_supervised` 공식 CM 콜백(Cycle05 callback pointer) 내부의 TF 조회 시간과 여타 처리/스케줄링을 **직접 구분**.
2. 실제 원인 하나가 증명된 경우에만 해당 설정/경로 **한 곳**을 최소 수정하고 원래 단일 Moving Goal 통합 공개 L2에서 CM120/Guard150/Scan·Odom·Clock300/Contact0/CLEAR-SLOW-STOP/odom 정지 dwell/CancelGoal/Navigation+Localization shutdown ACK/CM clean exit을 같은 런에서 검증. 이후 Owner WSL2 한 번으로 최종 검수.

## 고정 기준·실측
- Cycle05 immutable public `202b66eb49001e59a06adecb70dde67a457f0780`; exact original private runtime `966886c4627deb2bb3b37111fe336eeee6b9ebb4`, [#43995793080](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43995793080) actual Jazzy+Gazebo Harmonic/official Nav2 ONE GOAL: CM RMW source first gap=120.172578ms, Observer 120.523837ms, exact CM input callback duration=81.972669ms, overlap=81.972669ms. Release 120ms FAIL, tracing active, TF wait/scheduling causality UNPROVEN.
- Previous untraced original C37 #43898345608 source128.644215ms, Cycle01 #43981875149 source133.658796ms; OWNER first Guard internal age158.007666ms>150ms on different run, `UPSTREAM_STALE_AFTER_MOTION` safe latch. Mixing source/run clocks forbidden.
- Official Jazzy `nav2_collision_monitor/src/collision_monitor_node.cpp` source: `CollisionMonitor::cmdVelInCallbackStamped→process→source->getData`; `src/scan.cpp::getData→Source::getTransform`; `src/source.cpp::getTransform` uses advanced time-interpolated `nav2_util::getTransform` if base_shift_correction true. Existing Cycle05 `d06/live/g07_cycle05_cm_callback_window.py` traces only `ros2:callback_start/end` with exact C31 ROS subscription handle, **no TF interior time**.
- Cycle07 original official installed Nav2 YAML and live `source_timeout=1.0`, `transform_tolerance=0.02`, `base_shift_correction=true` proven in separate NO_GOAL #43999183495; shutdown `BLOCKED_LIFECYCLE_NAVIGATION_SERVICE_TIMEOUT` remained FAIL. Cycle06/parallel Cycle07 experimental base_shift false and source_timeout 0.3/0.5 had **NO actual Moving Goal evidence**, not candidates for release.

## 1단계 — 기능을 만들지 않고 원인 판별
A. **기존 증거 정적 재검토**: callback_start/end, original RMW, /tf + /clock, TF warning, scheduler sample coverage를 정확한 Run/clock별로 배치. Existing trace does not contain `getTransform` entry/exit; LTTng ROS standard callback events are not TF tracepoints. 따라서 이전 데이터만으로 TF time 단언 금지.
B. **기존 런타임 비침습 trace 가능성 사전검사** (이번 최소 작업): exact SHA256 pinned `ghcr.io/silverbjin/axia-g07-runtime`에서 official CM 설치 ELF dynamic/full symbol의 `Source::getTransform`, `nav2_util::getTransform`, `tf2_ros::Buffer::lookupTransform`에 대한 symbol presence와 kernel userspace uprobe/probe 권한/기존 TF LTTng tracepoint 유무를 **NO ROS/NO Goal**로 확인. 고비용 bpf/perf 설치, privileged CI/container, 공식 Nav2 소스 patch 금지.
C. 명확히 대응되는 TF **함수 entry+exit**, 그 함수와 Cycle05 콜백 pointer·PID·VTID+host mono 시간축 연결까지 가능한 경우에만 기존 C05 LTTng 추적에 필터 하나를 추가한 **단일 진단 Goal** 설계 가능. 이 조건이 하나라도 불충족이면 `CAUSE_UNPROVEN`. 단순 TF WARN, odom 100Hz, 단일 callback81.973ms, symbol 존재만으로 원인 판정 금지.
D. 실제 원인을 구분하는 판정: `TF_WAIT_PROVEN`은 첫 초과 구간과 동일 콜백에서 TF entry/end가 연결되고 유의미한 TF 실행시간이 콜백 지연을 설명할 때. `CM_OTHER_PROCESSING_PROVEN`은 TF 구간이 짧고 다른 위치/대기 entry-end가 실증되었을 때. `SCHEDULER_WAIT_PROVEN`은 같은 vtid/sched_switch on/off CPU evidence가 있을 때. 그 외 `CAUSE_UNPROVEN`. 관찰 부하 trace-ON은 release timing PASS 근거 아님.

## 2단계 — 조건부, 하나의 해결책과 원래 공개 통합 L2
`CAUSE_PROVEN` 이전에는 **변경 금지**. 이후에도 1변수만 변경: TF 원인이면 공식 Nav2 원본 설정/TF 발행 경계 한 곳(센서 motion-compensating transform 정확도 재검 필수); CPU/Executor 원인이면 해당 ownership 한 곳. Safety Guard/Supervisor/CM TTL120/150/300, STOP0.40/SLOW0.75, nav2 source, source_timeout1.0, E-Stop 명칭 변경 금지.
순서: regression RED → 한 곳 GREEN → original official Waffle/Nav2/Gazebo **tracer OFF Moving Goal 단 1회** → 같은 세션에서 whole-system TTL/Contact0/CancelGoal/ordered shutdown → 사용자 Owner WSL2 단일 L3 → 승인 뒤에만 main merge.
원본 재사용: exact Cycle37 / original P4 runner와 report evidence. 새로운 GUI/CPU plan, 새 fake safety, 추가 기능/범용 계측기/임의 반복·과잉 테스트 만들지 않음.
만약 기존 CI에서 TF 직접 계측 불가능하면 원인 미확정과 소스/계측 한계, 최초 경계까지 정확히 기록하고 **진단을 종료**. 해결책 없는 CI 실행·Owner Goal을 추가하지 않는다.

## 검증/공개 보존 경계
- 이번 preflight는 CPU/Gazebo 실제 실행을 요구하지 않는 capability-only L0. Workflow `.github/workflows/axia-g07-cm120-tf-direct-capability-l0.yml` 단발성; 결과에서 **플랫폼 기능**과 **실제 원인 증명**을 혼동하지 않는다.
- 실패의 원인은 NO_GOAL/config vs true CM first-gap 분리. Public Draft PR만 생성, main merge 금지. Instructor 정답/비공개 소스 수정 불필요. Owner WSL2 미실행.
- 모든 실제 명령과 stdout, 정확한 SHA, 미검증 및 경과교육 레슨은 같은 보고서에 남긴다. 인증 E-Stop 아님.

현재 `CM120_CAUSE=UNPROVEN`, `CM120_RELEASE=HOLD`, `AXIA_MVP_DEMO_ACCEPTED=HOLD`, `OWNER_L3=NOT_RUN`.
