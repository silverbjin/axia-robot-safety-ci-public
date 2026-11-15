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
