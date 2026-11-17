# AXIA G07 CM120 Cycle03 — NO_GOAL 동시 공백 식별 계획
작성일 2026-11-17 | 증거기반 독립 연구 사이클 | 원래 Safety TTL 유지

## 교육 목표와 가설
Cycle02 실제 [Run #43991016109](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43991016109): 8초 정지 상태에서 clock max333.464ms, odom339.852ms, odom->base TF339.766ms, scan102.943ms, RTF 0.999124. 각 토픽의 **최대값이 같은 시간창에서 발생했는지 미확인**이라는 증거 공백이 있다.

H1: clock/odom/TF max gap의 각 wall-monotonic 시간 구간에 공통 겹침이 존재한다.
H0: 각 최대 간격은 독립 시점이다.
- H1이면 공통 스케줄링/시뮬레이션 transport/한 관찰자 executor 대기의 후보를 키우지만, **CM TF lookup 원인이나 120ms Moving L2 고장의 입증은 아니다**.
- H0이면 TF 특이 지연을 별도로 조사한다.
- 기존 데이터는 max만 보존하고 원본 시각 배열은 CI cleanup 뒤 복구 불가. 동일 NO_GOAL 임시 Waffle10Hz/odom100Hz/official Nav2 조건에서 한 번의 제한된 재계측만 시행한다.

## RED→GREEN→REFACTOR→REVIEW→COMMIT
1. RED: Cycle02 불변 source `0682caeb413c9830107b1a0d297d36597896bed7`에는 `wall gap alignment` 필드가 없는 테스트 실패를 증명; 긴 gap 겹침/안겹침/부정확한 clock domain 3종.
2. GREEN: 기존 `tools/p4_g07_cm120_tf_clock_readonly.py`의 순수 `evaluate()`에만 wall-gap [start,end] 공통 교집합 길이 및 `aligned` 후보 필드를 추가. raw monotonic timestamps/UUID는 공개 출력하지 않는다. callback/tf 원인 미입증 flag 유지. 기존 4건 테스트와 신규 3건 통과.
3. Public L0: 이전 RED/현재 GREEN을 exact private SHA pin으로 확인. No ROS, Goal, cmd_vel.
4. Public L2: 기존 Cycle02 sealed real Jazzy/Harmonic Gazebo/Nav2 **NO_GOAL** workflow만 재사용해 단일 실측; 새 P4/CM 노드·LTTng·외부 publisher 불필요. Previous successful C02 evidence는 보존.
5. REVIEW: H1/H0 및 실제 max-gap 최초 시작·끝 교집합만 공개 **집계값**으로 보고; 이 값은 공통 병목 후보이지 인과가 아니며 150/300ms 안전 TTL의 판정 근거로 삼지 않는다.
6. STOP: 동시 gap 확인되더라도 Moving Goal CI는 실행하지 않는다. CM callback identity 사전검증(이전 Cycle31 원본) 필요하면 그 다음 한 단계만. 120ms/150ms 임계값 및 official Nav2 수정 금지. 성공한 기존 고비용 Gazebo L2 반복 금지.

## 범위와 제출
공개 `fix/g07-cm120-cycle03-common-gap-20261117`, 비공개 동일 브랜치. GitHub Draft PR; 원본 전용 CI 실행 워크플로는 완료 후 release에서 회수. 매 Cycle 보고서는 경과·실패→수정·원본 테스트 출력·정확한 SHA 및 CI Run·원인 미확정·후속 게이트를 교육용으로 기록하고 커밋. Owner WSL2와 main 병합 없음.

상태: `AXIA_MVP_DEMO_ACCEPTED=HOLD`, `CM_120MS_RELEASE=HOLD`, `OWNER_WSL2_GOAL=BLOCKED`, `CERTIFIED_ESTOP=false`.
