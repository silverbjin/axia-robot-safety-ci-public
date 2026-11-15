# AXIA G07 통합 개발 — 사이클 01 중간 보고서 (교육용)

- 작성: 2026-11-15 KST
- 상태: **L0 GREEN / 실제 GUI L2 1회 PASS / WSLg Owner L3 HOLD**
- P4 Instructor 고정 소스: `db1eec05e01e1db0d0d2e0c05610806ef4e499f9` (Tree `005cc352d63067beb9d34397e51b51f7974ce7ef`)
- 공개 통합 브랜치: `integration/g07-unified-ci-20261115`
- 공개 L2 전용 Release: `release/p2-g06-cm-ttl-20261110`

## A. 관찰한 문제와 안전 경계

실제 Gazebo Harmonic+RViz2 Xvfb 동시 실행 [#43683837146](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43683837146)의 **최초 Guard 래치**는 `UPSTREAM_STALE_AFTER_MOTION`이었다.

- Guard 내부 CM age **154.238454ms > 150ms** (초과 4.238454ms)
- 실제 CM RMW source gap **170.642126ms > 150ms**
- 당시 Supervisor age **7.311674ms**, Supervisor FSM NORMAL
- CM source 구간에는 Supervisor publication 3회 (최대 49.920437ms)
- CM source gap과 native STOP RPC 관측 구간이 겹쳤으나 RPC 원인이라는 인과관계 **미입증**
- 원본 STOP/odom/ECM/native shutdown **통합 성공 미검증**, Owner WSL2 L3 **NOT_RUN**

**교육 포인트:** 마지막 종료 오류가 아닌 *첫 안전 상태 전이*로 사건을 정의한다. CM 발행, RMW 수신, Guard callback 및 시간 영역을 구분하며, 미측정 원인은 추정하지 않는다.

## B. 원인 가설

추정: llvmpipe 기반 GUI 렌더링 및 read-only Marker 관측이 CPU 자원을 공유해 CM/Guard 데이터 전달 지연에 기여했을 가능성.

**한계:** 이것은 원인 확정이 아니다. P4 기준선에는 독립적인 CM 전용 코어 고정이 없으므로 표시 CPU만 제한한다고 CM scheduling이 독립적으로 보장되는 것도 아니다.

## C. RED → GREEN → REFACTOR → REVIEW → COMMIT

1. **RED** [#43685561461](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43685561461): `d06.live.d06_gui_cpu_plan` 누락으로 정해진 테스트 실패.
2. **GREEN** [#43685622178](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43685622178): 기존 D06 CPU 선택기 재사용 및 sidecar의 RViz/Gazebo GUI=첫 허용 코어, read-only 관측기=뒤에서 두 번째 코어. Guard/Nav2/CM/Bag의 정책 및 스케줄러는 변경 없음.
3. **RED** [#43685680734](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43685680734): GUI CPU 준비 상태를 Goal 이전에 확인하지 않는 계약 오류 재현.
4. **GREEN** [#43685749812](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43685749812): 4개 이상 허용 CPU와 서로 다른 표시/관측 CPU를 요구하는 사전검사. 부적합 환경은 Goal 이전에 fail-closed.
5. **REVIEW:** 안전제어·Goal·Nav2·TTL·기존 검증된 Instructor 파일 수정 없음. GUI 출력만 변경, D06 원본 helper blob `b0e3a44d55d0cb4b1eeaf009f32e0ac50c25e9e0`와 내용 동일.
6. **COMMIT:** RED `66a1293d` → GREEN `e1a8d125`; preflight RED `0201b986` → GREEN `d5401e15`, L0 workflow 계약 최종 `a54caa3d`.

### 변경 파일

- `d06/live/d06_gui_cpu_plan.py` — 기존 D06 helper 이식
- `d06/scripts/g07_unified_ci_readonly_display.sh` — CI 전용 GUI/Observer taskset 및 역할 로그
- `d06/tests/test_g07_unified_gui_sidecar_contract.py` — RED/GREEN 검사
- `.github/workflows/axia-g07-unified-gui-one-goal-l2.yml` — 원본 P4 소스 기반, Goal 이전 CPU preflight
- `.github/workflows/axia-g07-unified-first-boundary-l0.yml` — 변경에 따른 자동 회귀

## D. 검증 수준 및 인수 게이트

- L0: **PASS**, ROS/Gazebo 실제 실행은 이 L0로 증명하지 않음
- 새로운 GUI+Gazebo L2: [#43685818018](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43685818018) **SUCCESS** (workflow SHA `2bb0a46dd1eccdce364ccc9faeb4d5650bfb99f2`, Instructor SHA `db1eec05e01e1db0d0d2e0c05610806ef4e499f9`, original Docker digest pinned). 
  - 첫 Guard latch **없음**, P4 original oracle `CI_GAZEBO_MOVING_GOAL_CANDIDATE`; native shutdown 이후 CM exit=0.
  - 실측 최대 간격: clock 100.127ms, CM observer 130.047ms, Guard observer 57.722ms, Odom 130.199ms, Scan 204.809ms, supervised/source 70.502ms, Supervisor 70.568ms, **CM RMW source max 131.836ms**. 모든 측정 한계 미만.
  - CLEAR 2.0357m → SLOWDOWN 0.7498m → STOP 0.3991m, odom stationary dwell **1.024892초**, Goal CancelGoal ACK 후 Navigation/Localization native ACK, 종료 감사 CM exit code=0.
  - Native S02 접촉 +건수=0, 관측 33994 iterations, 정확히 해당 Goal 원본 14-topic SQLite/원본 확인 성공 (개인 Goal UUID는 보고서에 기록하지 않음).
  - Xvfb에서 실제 RViz/Gazebo 두 창이 Goal 이전 나타났고 Goal 도중 실제 Scan을 관측; `owner_wslg_verified=false`.
  - GUI CPU 사전검사: renderer CPU 0, observer CPU 2. **CM 전용 CPU와 독립성 입증 아님**.
  - `NO_CM_SOURCE_GAP_OBSERVED`은 이 실행 동안의 관찰에 한정. 정상 출력이 곧 영구적 root cause 수정 증거가 아님.
- 동일 기준 P4 headless 과거 실증: [#43674784552](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43674784552) **해당 범위 PASS, 재실행 생략**
- Owner WSL2 Gazebo+RViz: **NOT_RUN**. CI 시뮬레이션으로 WSLg 동시 화면/스케줄링 동등성을 증명할 수 없음.
- `AXIA_MVP_DEMO_ACCEPTED`: **HOLD**. 안전 TTL 변경이나 인증 E-Stop 대체 없음.
- main 병합: **하지 않음**. 강사용 정답/학생용 코드 외부 유출 없음.

## E. 다음 사이클 규칙

실제 L2가 실패하면 모든 실패를 평면적으로 재시도하지 않고, 같은 원본 run의 **최초 안전 전이 → 최초 시간 위반 → CM source/receive → Guard native callback → Supervisor/Scan/Odom → shutdown** 순으로 원인을 좁힌 뒤 비식별 fixture를 L0 RED로 먼저 추가한다.

CI L2에서 동시 GUI, 안전 TTL, 원본 14-topic/ECM, odom STOP, native shutdown을 같은 소스·실행에서 모두 검증한 경우에만 Owner WSL2 최종 1회 인수 준비 후보로 올린다. 그 전에는 현장 Goal을 요청하지 않는다.

## F. 교육용 회고 — 원인과 해결의 구분

- **문제:** 실제 동시 GUI 로드 중 154.238ms Guard TTL latch와 후속 CM 170.642ms RMW source 간격 초과.
- **검증된 수정:** UI/관측기 CPU 사용 범위를 개별 제한하고 Goal 전 자원 요건을 검사한다. 실제 GUI L2 신규 동일 P4 소스 1회 전체 테스트가 GREEN.
- **입증하지 못한 부분:** 과거 문제의 단일 인과적 root cause, 모든 CPU 스케줄러 환경에서의 타이밍 보장, Owner WSLg GUI 동등성 및 장시간 반복 안정성.
- **설계 교훈:** 원인을 확정하지 못했더라도 *제어·안전 정책 불변 + UI 부담 축소 + fail-closed 계약 + 실제 end-to-end 증거*로 MVP의 제한된 CI 준비 범위에 도달할 수 있다.
- **인수 결정:** CI scoped GUI L2 `PASS`, Owner WSL2 L3 `NOT_RUN`, `AXIA_MVP_DEMO_ACCEPTED`는 계속 `HOLD`. 다음 사이클은 Owner 최종 1회 승인·절차·환경 parity admission.
