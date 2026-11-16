# AXIA G07 — CM 120ms 원인 제한 및 단일 최종 인수 계획
작성: 2026-11-17 | 상태: 계획 확정·실행 진행 | 범위: 기존 G07 단일 시뮬레이션 Goal

## 1. 작업 성격·위험
- 분류: **안전 제어 데이터 전달의 비결정적 타이밍 결함**. 신규 기능 개발이나 CM/Guard/Navigation 전면 개선이 아니다.
- 기준: `AXIA_Robot_Safety_MVP_Baseline_Scenario_Acceptance_v1_KO.md`, 기존 G07 원본 시나리오, 공개 CI/WSL2 동등 실행 및 원래 14-topic custody. *원문 baseline 파일 내용은 본 작업에서 직접 대조되지 않았으므로 정확한 acceptance 세부는 기존 실제 CI oracle를 우선하고 baseline 일치 여부는 미검증으로 기록한다.*
- 공개 단일 개발 브랜치: `fix/g07-cm120-final-owner-gate-20261117` from release `68742938e68e6f9e1151bd07563d44f004c6a89c`. Instructor 강사 정답/학생, main 병합/안전 TTL 변경 금지. C38 GUI 실측 PASS/C39 scope freeze 증거 보존.
- 원본 [#43898345608](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43898345608): 실제 1 Goal 약 0.1975m, STOP 1.013s, native Nav2 종료 ACK/CM exit0/14-topic 통과; CM RMW source gap **128.644215ms** 및 외부 Observer callback gap **128.318661ms** 때문에 *별도 120ms 릴리스 여유* FAIL. 다른 실제 측정: Supervisor 81.858ms, Guard 65.968ms, Scan 217.059ms, Odom 96.791ms, Clock 82.440ms.
- **최초 확정 위반은 120ms margin**이고 150ms CM/Guard hard TTL breach는 이 실행에서 증명되지 않음. 이전 Owner Guard 내부 CM age 158.008ms 최초 `UPSTREAM_STALE_AFTER_MOTION`는 별도 실제 현장 safety FAIL이다. 두 사건을 혼동하지 않는다.
- 원인 미확정: CM 입력 처리/TF wait/ROS executor·OS scheduling/native STOP RPC 간 경합. 기존 `CM_POST_INPUT_EXECUTION_OR_SCHEDULING_GAP_CANDIDATE`는 판정이 아니라 가설. CM publishes on command input callback; output frequency knob 임의 변경은 근거 없음.
- 시스템시계 RMW source/received와 host monotonic observer 시간은 직접 빼거나 한 clock처럼 비교하지 않는다. 기존 source/seq와 monotonic window를 별도로 기록.

## 2. 단일 개발 전략과 Stop Rule

### Gate A — 기존 원본으로 첫 경계 원인 후보 좁히기 (읽기 전용, Goal 없음)
1. 기존 성공·실패 SHA와 CI Run #43898345608의 first 120ms RMW source/Observer, Supervisor, native STOP RPC / Guard 첫 전이, scheduler sample coverage를 같은 Goal 창으로 대조한다.
2. 기존 `tools/p2_g07_ci_moving_goal_oracle.py`와 `d06/live/` 진단기를 먼저 재사용. **신규 LTTng/proc sampler·new daemon·helper를 만들지 않는다.**
3. 간격 시작·끝이 native RPC 관측 구간과 실제로 겹치는지, upstream 발행 2건이 살아있는지 확인. 데이터 부족 시 `ROOT_CAUSE=UNPROVEN` 유지하고 잘못된 CPU 인과 추측 금지.
4. 내부 콜백 입력/출력 시각이 확보되지 않으면 기존 일회성 L2에 포함된 기록만 사용; 원본에 없는 GPU·CPU·WSLg 근거를 만들지 않는다.

### Gate B — 최소 RED→GREEN (진단 증거가 뒷받침하는 *단 하나*만)
- RED: 기존 실제 원본 수치 (0.128644215/0.128318661/0.081858/0.217059)와 이전 Owner 0.158007666을 사용해 `120ms release HOLD`/hard TTL 기준 보존/clock 영역 불일치 FAIL CLOSED를 재현한다.
- GREEN: 가장 작은 기존 **비안전성 배치·관찰자 로드 변화** 또는 검증된 입력 데이터 간격 원인만 수정. TF/CM/Guard/Supervisor 원본 안전 TTL(150/300ms), Nav2 lifecycle, Scenario Verifier의 판단 함수/Goal 권한은 바꾸지 않는다. 원인 미확정이면 **구현 없이 HOLD**가 정답이다.
- 과거 Cycle20–38의 CPU/nice/Trace 실험을 먼저 확인; 이미 실패한 조합 반복하지 않는다. CI L0 GREEN 이후 공개 Draft PR 코드 리뷰/정적 계약 검사.

### Gate C — 변경 영향 공개 CI 실제 Gazebo/Nav2 통합 L2 **1회**
- 기존 공개 `.github/workflows/axia-g07-unified-gui-one-goal-l2.yml`과 immutable runtime digest `ghcr.io/silverbjin/axia-g07-runtime@sha256:861ae1df...`/공식 Waffle 및 Nav2 코드를 재사용. 별도 전체 재설치, 다른 G00–G10 추가 검증 금지.
- 동일 pinned private source/GUI, 동일 one-Goal UUID 창의 7채널 wall/monotonic callback, 실제 source RMW seq, Scan/Odom/Clock/Guard/CM/Supervisor, native STOP/odom dwell/Contact0/Goal Cancel/종료 ACK 및 14-topic 원본을 확인.
- release gate: CM source 및 CM Observer **max <=0.120s** (운영 margin), CM/Guard hard <=0.150s, Scan/Odom/Clock <=0.300s, 원본 shutdown・safety・collision 증거 필요. missing/clock-unmatched -> HOLD.
- **실제 L2 fail이면 해당 최초 위반만 public CI regression에 RED 재현 후 한 번의 변경 후보로만 복귀**. 성공한 과거 항목은 근거 재사용. 실패 상태에서 Owner Goal 차단.
- public CI SUCCESS는 정확한 source SHA와 위 범위의 실측 시점으로만 인수 준비 후보다. 해당 workflow가 `success`만 해도 120ms/다른 safety gate가 누락되면 `READY`로 승격 금지.

### Gate D — CI GREEN 뒤 Owner WSL2 **수동 단일 인수**
- 별도 Owner one-shot은 public GitHub immutable SHA에서 내려받아 실행, 동일 검증된 private SHA를 gh auth로 접근. NO GOAL preflight/CPU affinity/WSLg real window/GZ scene 먼저 확인.
- 과거 실패 attempt lock/원본 ZIP은 삭제하지 않는다. 기존 같은 SHA 현장 재시도 금지; 새 SHA/CI 증거와 수동 TTY `YES-P2-G07-GOAL`이 요구된다.
- 1회 실제 WSLg Gazebo+RViz2 단일 Goal, CLEAR→SLOWDOWN→STOP, CM/Guard first-latch & periods, Scan/Odom/Clock, 물리/odom 정지, CancelGoal ACK, ordered Nav2 shutdown and CM exit0, 원본 SHA256/14-topic 확인.
- 결과는 사용자 원본 로그 후 `ACCEPTED` 혹은 `HOLD`만. SW Stop != certified physical E-Stop. 새 Owner 오류는 CI 재현부터; 같은 현장 재시도 금지.

## 3. 실행 순서/제출 산출물
1. **계획 문서 커밋** (이 파일)
2. 기존 근거·최초 실패의 **독립 진단 보고서**, Root cause proven/unproven, 변경 여부 결정
3. 근거 있는 최소 RED→GREEN 공개 L0 + 코드 커밋 (원인이 미확정이면 HOLD 보고서)
4. 공개 단일 실제 Gazebo L2, 정확한 Run ID 및 원본 결과 검토. 전체 L2 누락 시 절대 PASS 아님.
5. GREEN이면 Owner WSL2 단일 실행 블록 SHA pin + 기대 출력/실패 bundle; 실제 실행은 Owner 권한/WSLg에서 수행. main 병합은 사용자 승인 전 금지.
6. 매 사이클: `file path / command / actual test output / verified-level / unverified / branch-commit`을 문서+커밋으로 기록.

## 4. 범위 금지
새 안전 노드, Nav2/CM fork, 새로운 서비스/접근제어·상태머신, 15회 반복인수, 불필요한 센서/TF 기하학 연구, 임계값 완화, 거짓 ROS/WSLg PASS, 강사 정답 공개, 자동 main 병합 금지.

```text
AXIA_G07_CM120_ROOT_CAUSE=UNPROVEN
CM_120MS_RELEASE=HOLD
PUBLIC_ONE_GOAL_L2_NEW=NOT_RUN
OWNER_WSL2_L3=NOT_RUN
AXIA_MVP_DEMO_ACCEPTED=HOLD
CERTIFIED_ESTOP=false
```
