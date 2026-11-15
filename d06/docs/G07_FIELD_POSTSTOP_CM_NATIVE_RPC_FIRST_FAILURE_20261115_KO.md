# AXIA G07 — Cycle 09 최초 안전 위반 및 배포 보류 보고 (2026-11-15)

## 인수 판정

**`AXIA_MVP_DEMO_ACCEPTED=HOLD` · 새 Owner WSL2 주행용 배포 금지.**

마지막 사용자 지시는 기존 read-only HOLD 진단기가 아닌 **실제 Gazebo L2를 통과한 실행기만 Owner WSL2에 출고**하는 것이다. 해당 조건이 충족되지 않아 이번 Cycle에 주행용 원샷을 게시하거나 Owner Goal을 요청하지 않았다. 오래된 Owner 실패 예약 디렉터리는 보존한다.

## 변경 후보와 실제 검증

- Private Instructor 후보: `fix/g07-field-cm-delivery-cpu-headroom-20261115` commit `fed69ff67bc9dc76909faf9ef1e7456ca995a848` (sealed, 미병합).
- Public L0 workflow `.github/workflows/axia-g07-field-sealed-authorized-l0.yml`, commit `fa01abc5d4bf5f719cd808a0a01ce559e7b8e0a9`. 실제 Run [43715043705](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43715043705): SUCCESS. `TEST_FIELD_RC=0 TEST_PRIOR_CPU_RC=0 BASH_CI_RC=0 BASH_OWNER_RC=0 COMPILE_RC=0 TEST_POSTSTOP_CANCEL_RC=0`. **5+5+4=14개 L0 테스트 PASS**, ROS/Goal 미실행.
- Public real Gazebo GUI/RViz L2 workflow `.github/workflows/axia-g07-unified-gui-one-goal-l2.yml`, commit `3333e17c9fb7505733f1e3d50a8f1f5cfa87eec2`. 실제 Run [43715110448](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43715110448): **FAILURE**. Jazzy/Nav2/Harmonic 실제 SIM Goal; Xvfb GUI/RViz. WSLg와 동일하다고 주장하지 않음.

### 무엇을 수정했고 무엇을 수정하지 않았는가

- `tools/p2_g07_cm_stop_zero_delivery.py`: 시뮬레이션 G07에만 공식 Collision Monitor 반복 ZERO 발행 창을 기존 5s에서 30s로 후보 변경. **Guard 독립 TTL 150ms는 그대로**.
- `scripts/p4_g07_shared_runtime.sh`: `axia_g07_shared_zero_window_readback()` 단일 실측 유틸 추가.
- `scripts/p2_no_goal_smoke_ci.sh`, `scripts/p2_owner_l3_wsl2.sh`: 동일 실측 함수를 **Goal 이전**에 호출하고 이전 5s/누락 파라미터는 차단.
- `tools/p4_g07_exact_goal_cancel.py` 및 `tools/p2_g07_ci_moving_goal.py`: Supervisor가 Goal ownership을 비워도 원래의 **정확한 32자리 UUID**로 Nav2 Action StatusArray 조회, 합성 ACK 없음.
- `tests/unit/test_g07_field_poststop_zero_cancel_uuid_20261115.py`: 공개 CI/Owner 공통 호출, 30s 수락/5s 거부, 정확한 UUID, 안전 TTL 불변 회귀.
- 공식 Nav2/CM/TB3 소스·Guard 정책·Scan/Odom/Clock TTL·안전 STOP 동작 변경 없음. 새 30s 설정은 **L2 실패로 미승인 후보**이며 배포에 포함되지 않음.

## 최초 실패 — 최종 오류가 아닌 원본 타이밍

- 같은 실제 L2에서 `AXIA_G07_REAL_CM_STOP_ZERO_WINDOW_30S_GUARD_150MS_UNCHANGED_NO_GOAL` 실측 출력 확인. 따라서 **이번 최초 위반을 5s ZERO 종료로 설명할 수 없음**.
- Clear (LaserScan front 2.042m), SLOWDOWN (0.749m), native dynamic STOP intrusion ACK (native service 109.343ms)까지 실행.
- **첫 CM RMW source publication gap = 176.944537ms**, 같은 간격 내 Supervisor upstream 3회, 최대 upstream gap 49.972317ms.
- **첫 Guard internal CM age = 173.903862ms > 150ms**, `UPSTREAM_STALE_AFTER_MOTION`; Guard 출력 ZERO로 보호 정지. 이때 Supervisor age 47.000881ms 및 상태 NORMAL/Goal authorized.
- 원본 진단 `CM_RMW_GAP_DURING_NATIVE_STOP_RPC_CANDIDATE`: 위반이 native STOP RPC 구간과 시간상 겹침은 확인, **RPC가 CM 지연을 유발했다고 인과 확정하지 않음**.
- CM proc sched 변화: wait 9.681218ms / run 2.842719ms / thread_count 16. 전체 176.9ms가 CPU 선점 탓인지, executor/TF 내부 대기인지 **미확인**.
- 실패 메시지 `GUARD_LATCH_DURING_STOP:UPSTREAM_STALE_AFTER_MOTION`; 이후 S02 contact, 정확 Cancel ACK, Nav2 lifecycle shutdown의 **완결 인수 증거 미확보**.
- 독립 Observer에서는 `EARLY_LATCH_TIMING_DIAGNOSTIC_NO_BREACH_IN_OBSERVER`도 출력했지만, **Guard 자체 수신 TTL 위반의 부정 증거가 될 수 없음**.
- 현장 이전 사례와 동일한 종류의 **내부 Guard 150ms 초과**가 이제 실제 공개 CI L2에서도 재현됨. 미확인 Owner WSLg를 다시 호출해 이 문제를 해결해서는 안 됨.

## 다음 최소 작업 (CI 우선)

1. 이전과 이번 원본을 첫 Guard latch / 첫 CM source publication gap / 첫 native RPC 간격으로 정렬한 **원인 판별용 계측 하나**를 선택한다. 특히 CM callback 진입·종료 또는 TF 대기와 native RPC 구간의 인과를 확인한다. ROS/Gazebo 소스 변경이나 새 안전 계층 개발 없이 가능한 기존 계측을 우선 재사용한다.
2. 실제 원인에 대한 최소 RED 회귀 → GREEN 수정 → 재검토 → commit. Guard 150ms와 S02/Cancel/Shutdown 인수 게이트 완화 금지. 반복 시연 재시도만으로 PASS 처리 금지.
3. 수정한 **같은 Instructor SHA**로 sealed L0 GREEN → 실제 Gazebo GUI/Nav2 L2 단일 Goal. 모든 7채널 hard TTL과 별도 120ms CM 출고 여유, S02 native zero contact, exact Goal CANCEL 및 Nav2 ACK, CM exit0 원본 검증. 추가 2코어 Prearmed STOP 불변.
4. 위 증거가 적격일 때만 변경 SHA와 L2 Run으로 고정한 새 Owner WSL2 단일 시도 원샷을 배포. 기존 `bc270e...` 실패 잠금 삭제·우회 금지.
5. `main` 병합은 사용자 승인 후. 비공개 Instructor 솔루션/Owner 원본은 공개 저장소에 게시하지 않음.

## 검증·미검증·Git

- 정적/비공개 L0: **PASS** Run `43715043705`.
- 실제 Gazebo/Harmonic L2: **FAIL** Run `43715110448` (first Guard internal CM TTL).
- 실제 WSL2/WSLg Owner L3: **NOT_RUN**. 인증된 E-Stop 아님.
- 신규 Owner 주행용 배포/학생 패키지/main merge: **NOT_DONE**.
- 현장에 남아 있는 마지막 HOLD 상태를 **PASS로 승격하지 않는다**.
