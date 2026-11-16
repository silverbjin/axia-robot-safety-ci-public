# AXIA Block C 공개 CI — 교육용 D09–D12 MVP 정식 출고 승인

**사용자 승인:** 2026-11-16 교육용 Block C 정식 출고 및 관련 변경 `main` 병합.

## 공개 CI 범위

- C01 고정 학생 fixture 및 checksum L0, C05 교육 전용 `DiagnosticArray` ROS 2 Jazzy DDS L1, C06 학생 TODO·출고 계약.
- 실제 Owner WSL2 승인 자료: 13/13 단계 PASS, 강사 32 Python tests PASS, 학생 5 계약 PASS, 학생 4 TODO expected RED, 실제 교육용 Jazzy DDS 3×8건, 제어 토픽 발행 없음.
- Owner 원본 증거 파일은 **공개 저장소에 업로드하지 않음**. 감사용 sanitized verdict의 범위와 공개 합성 감사기를 구분한다.
- 공개 Owner 증거 감사 CI [Run #43787896067](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43787896067): **9 passed**; 동일 원샷의 실패 전파·SHA 계약 테스트 [Run #43782287875](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43782287875): PASS.
- GitHub PR 순서: **#129(C01) → #130(C05/C06) → #131(Owner 재검증/증거 감사)**. 각각 병합 완료 및 `main` 포함을 확인하여 정리.
- GitHub Actions와 Owner는 동일 `block_c/scripts/axia_block_c_owner_final_once.sh` 코드를 공유한다. Public CI 모드 `--ci-parity`의 통과를 실제 WSL2 L1 검증으로 허위 확대하지 않는다.

## 승인 경계

`BLOCK_C_EDUCATION_MVP_RELEASE_APPROVED=true`는 교육용 합성 데이터 분석·학생 TODO·비제어형 ROS 진단만 대상으로 한다. 기존 `verdict.json`과 Manifest의 `release_approved=false`는 **사용자 승인 이전 불변 증거**이므로 그대로 보존한다. 실제 Gazebo 주행, 생산 Guard TTL, 인증 E-Stop은 미검증. Instructor 비공개 답안/Hidden Test/Owner TAR는 공개 CI에 게시하지 않는다.
