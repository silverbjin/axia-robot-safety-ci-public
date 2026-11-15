# AXIA G07 — 자동 개발·디버깅 사이클 원장

## 운영 규칙

- 단일 검증 기준선 P4 Instructor `db1eec05e01e1db0d0d2e0c05610806ef4e499f9` 유지. 새로운 Instructor 버전은 명시적인 CI 검증 후 갱신한다.
- 매 사이클 **관찰 → 최초 실패 경계 분석 → RED → GREEN → REFACTOR → REVIEW → COMMIT → 실제 CI 검증 → 중간 보고 → 다음 사이클**.
- 이미 성공한 범위는 원본 SHA·evidence로 재사용하고, 신규 실패는 먼저 CI 재현 테스트로 편입.
- 실제 Gazebo나 WSL2를 실행하지 않았으면 PASS로 표현하지 않음. 최종 Owner 목표는 승인된 1회 인수.
- `AXIA_MVP_DEMO_ACCEPTED` HOLD 상태에서 main 병합과 학생용 정답 공개 금지. SW Stop은 인증된 E-Stop이 아님.

## 사이클

1. [사이클 01 — GUI CPU 경합 완화 후보](./G07_UNIFIED_CYCLE01_GUI_CPU_PARTITION_20261115_KO.md): L0 및 실제 GUI L2 PASS, Owner WSLg L3 NOT_RUN. 교육용 보고서 완료.

각 기록에는 실제 출력·검증 수준·원본 Run·미검증 항목과 변경 파일/커밋을 포함한다.

2. [사이클 02 — CI 근거 고정 및 Owner 1회 실행 자동화](./G07_UNIFIED_CYCLE02_OWNER_FINAL_ADMISSION_20261115_KO.md): L0 20 PASS + Public Release Bootstrap L0 PASS; Owner WSLg 미실행.

[최종 WSL2 원샷 실행 가이드](./G07_FINAL_OWNER_WSL2_ONE_SHOT_GUIDE_20261115_KO.md)

3. [Cycle 03 — Owner 최초 Guard 불일치/RMW 시계 분리, CI·Owner GUI 실행 일치, 증거 묶음](./G07_UNIFIED_CYCLE03_OWNER_LATCH_RUNTIME_PARITY_20261115_KO.md): L0 PASS, 실제 GUI L2 #43690412617 종료 첫 서비스 발견 FAIL.
4. [Cycle 04 — Nav2 Shutdown 첫 서비스 발견](./G07_UNIFIED_CYCLE04_NAV2_SERVICE_DISCOVERY_20261115_KO.md): L0 PASS, 실제 GUI L2 #43690918618 FAIL (최초 PRE_STOP odom 355.882ms, 다중 관측 채널 수신 지연).

[CI First 실행 지침/새 창 프롬프트](./AXIA_G07_CI_FIRST_RUNTIME_PARITY_DEBUG_STANDARD_20261115_KO.md)

5. [Cycle 05 — 최초 PRE_STOP Odom 및 RMW 수신 지연](./G07_UNIFIED_CYCLE05_MULTITOPIC_RECEIVE_GAP_20261115_KO.md): 실제 L2 #43690918618 FAIL 분리, RED #43691430319 / GREEN #43691482482, Owner HOLD.

3. [사이클 03 — Owner Guard 불일치와 GUI 동일 실행기](./G07_UNIFIED_CYCLE03_OWNER_FIRST_MISMATCH_AND_EXECUTOR_PARITY_20261115_KO.md): 실제 원본 Guard 래치 구분, 첫 RMW clock-step 후보, 공개·강사 L0 GREEN, local custody 자동화 테스트. Owner HOLD.
4. [사이클 04 — Nav2 종료 서비스 및 첫 전달 주기](./G07_UNIFIED_CYCLE04_NATIVE_NAV2_SHUTDOWN_AND_TIMING_20261115_KO.md): 실 L2 #43690412617 shutdown FAIL → RED/GREEN → #43690918618에서 더 이른 다중채널 delivery FAIL. Owner HOLD.
5. [사이클 05 — RMW 수신·Observer CPU 분리](./G07_UNIFIED_CYCLE05_MULTICHANNEL_RMW_RECEIVE_20261115_KO.md): 공개·강사 sealed L0 GREEN, 실 L2 #43692909902 대기, Owner 미실행.
6. [CI-first 재현·실행기 동일성 표준 프롬프트](./AXIA_G07_CI_FIRST_RUNTIME_PARITY_DEBUG_STANDARD_20261115_KO.md): 현장 오류의 최초 safety transition/타이밍과 임의 인수 승격 금지.

6. [사이클 06 — Prearmed STOP 2-CPU 제약](./G07_UNIFIED_CYCLE06_PREARMED_STOP_CPU_INVARIANT_20261115_KO.md): 첫 L2 #43692909902 Goal 전 BLOCKED, sealed L0 RED #43693340153 → GREEN #43693435159, 새 L2 #43693480829 진행 중.
