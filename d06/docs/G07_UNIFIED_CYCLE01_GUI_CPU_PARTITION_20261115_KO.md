# AXIA G07 통합 개발 — 사이클 01 중간 보고서 (교육용)

- 작성: 2026-11-15 KST
- 상태: **L0 GREEN / 실제 GUI L2 검증 중 / 최종 인수 HOLD**
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
- 새로운 GUI+Gazebo L2: [#43685818018](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43685818018) **실행 중(작성 시점)**. 실제 출력 판독 뒤 이 문서를 갱신한다.
- 동일 기준 P4 headless 과거 실증: [#43674784552](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43674784552) **해당 범위 PASS, 재실행 생략**
- Owner WSL2 Gazebo+RViz: **NOT_RUN**. CI 시뮬레이션으로 WSLg 동시 화면/스케줄링 동등성을 증명할 수 없음.
- `AXIA_MVP_DEMO_ACCEPTED`: **HOLD**. 안전 TTL 변경이나 인증 E-Stop 대체 없음.
- main 병합: **하지 않음**. 강사용 정답/학생용 코드 외부 유출 없음.

## E. 다음 사이클 규칙

실제 L2가 실패하면 모든 실패를 평면적으로 재시도하지 않고, 같은 원본 run의 **최초 안전 전이 → 최초 시간 위반 → CM source/receive → Guard native callback → Supervisor/Scan/Odom → shutdown** 순으로 원인을 좁힌 뒤 비식별 fixture를 L0 RED로 먼저 추가한다.

CI L2에서 동시 GUI, 안전 TTL, 원본 14-topic/ECM, odom STOP, native shutdown을 같은 소스·실행에서 모두 검증한 경우에만 Owner WSL2 최종 1회 인수 준비 후보로 올린다. 그 전에는 현장 Goal을 요청하지 않는다.
