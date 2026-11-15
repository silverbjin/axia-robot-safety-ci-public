# AXIA G07 — Cycle 05 공동 수신 경로 지연과 STOP 이전 최초 300ms 위반 (교육용 중간 보고서)

일자: 2026-11-15 KST. **상태: 공개 L0 GREEN / 실제 Xvfb GUI L2 FAIL / Owner WSL2 NOT_RETRIED / 인수 HOLD**

## 사건 및 최초 안전 경계

원본 실제 CI Xvfb+공식 Gazebo Harmonic/Nav2 실행 [#43690918618](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43690918618), 비공개 P4 후보 `36ce8e6909193413181fad965d6f63b06c187fb2`, 공개 source `70f9d4ece5c405cff0fb2d17843391856f3d8c08`.

주행 동작에는 CLEAR/SLOW/STOP 후보와 정지 관측이 있었고 **Guard latch는 없었다**. 그러나 이 사실은 전체 안전 데이터 전달 PASS가 아니다.

- **최초 시간 위반**: 실제 Observer의 `odom` 간격 355.881974ms (허용 300ms) at host-monotonic 367.719907854, **PRE_STOP**, STOP/Shutdown 후속 오류 아님.
- 콜백 최댓값: `clock` 339.159ms, `cm` 383.109ms, `guard` 364.427ms, `odom` 355.882ms, `scan` 373.624ms, `source` 352.279ms, `supervisor` 352.723ms. 해당 Goal의 관측 경로 7채널에서 모두 한계 초과.
- **RMW 발행/수신 구분**: CM source 최댓값 131.984ms 및 특정 연속 pair source 간격 70.891726ms(기존 150ms 이내), 동일 pair RMW receive 간격 377.049077ms, Observer callback 383.109139ms, sequence gap=1.
- 따라서 **CM 발행 중단으로 단정 금지**. RMW receive 또는 공통 Observer 실행 지연 후보이며 원인(스케줄러/DDS/GIL)은 미입증.
- 실제 P4 오라클 출력: `ACTUAL_MOVING_GOAL_CI_ORACLE_SAFETY_DELIVERY_TTL_BOUNDARY_max_source_interval_sec`, **whole L2 FAIL**, 실제 Nav2 정식 cleanup 미완성. 제한값은 완화하지 않는다.

## RED → GREEN → REFACTOR → REVIEW → COMMIT

1. **RED** 공개 CI [#43691430319](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43691430319): 신규 사후 진단 모듈 부재, 비식별 원본 회귀 실패.
2. **GREEN** 공개 CI [#43691482482](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43691482482): 해당 신규 테스트 5/5, 기존 회귀 27/27 등 총 **32/32 L0 PASS** (`5+7+8+4+3+5`). 실제 CI stdout 6개 unittest group가 모두 `Ran X tests ... OK` 출력.
3. **수정 범위**: `d06/tests/fixtures/g07_ci_20261115_multitopic_receive_gap_sanitized.json` (Goal UUID/원본 경로 제외), `d06/tests/test_g07_ci_multitopic_first_receive_gap_20261115.py`, `d06/live/d06_ci_multitopic_receive_gap_triage.py`. 증거 분리/후보 분류뿐이며 **runtime safety, Guard, official CM, native Stop, TTL 무변경**.
4. **REVIEW**: first PRE_STOP odom과 CM RMW source/receive pair를 각각 독립 근거로 유지, 서로 같은 정확한 시각에 발생했다고 단정하지 않음. Guard의 input callback가 377ms 지연됐다고 주장하지 않음. 모든 결과 `safety_pass=false`, `owner_l3_accepted=false`. 150ms/300ms 한계 우회 금지.
5. **COMMITS**: RED `1dfcd53a3f9b3aa650fc442abe121b62caaea64d`, GREEN `10eda72ac621751022176d6badd88307cd26c7a4`.

## 아직 검증할 문제와 교육용 교훈

관측기 RMW receive 지연이 왜 발생했는지 실측으로 확정하는 최소 계측(Observer 콜백·공통 스케줄링/CPU 경계)이 필요하다. 추정만으로 CPU affinity를 계속 바꾸거나 리트라이하지 않는다. 유효한 RED 재현 → 후보 GREEN → 같은 Exact Runner/GUI를 쓰는 전체 Gazebo L2 PASS 후에만 새 Owner 1회 재입장을 검토한다. WSL2 기존 실패 아카이브는 유지한다.

**교육 핵심:** 하나의 토픽의 정상 발행은 안전 시스템 전체 전달 주기 보증이 아니다. 원본 RMW 발행/수신과 실제 콜백, 첫 시간 위반, 이후 shutdown 오류를 독립된 시계/단계로 분석한다.
