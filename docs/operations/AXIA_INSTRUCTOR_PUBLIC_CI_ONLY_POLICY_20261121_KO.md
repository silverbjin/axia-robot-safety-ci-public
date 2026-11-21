# AXIA Instructor CI 전용 Public 검증 운영 정책

**적용일:** 2026-11-21 · **CI 실행 저장소:** `silverbjin/axia-robot-safety-ci-public`

## 결정

Instructor 저장소의 GitHub Actions 실행을 중단하고 **모든 강사 검증을 Public CI에서 수행**한다. 비공개 Instructor에 접근하기 위한 보호 환경은 `axia-instructor-sealed`이고, 기존 승인된 보호 브랜치 `release/p2-g06-cm-ttl-20261110`에 한해서만 강사 job을 실행한다. 이는 공개 CI 로그나 Artifacts에 비공개 정답을 공개해도 된다는 뜻이 아니다.

## 공개와 비공개 작업 분리

| 게이트 | 실행 조건 | 검증 대상 | 공개 출력 |
|---|---|---|---|
| Public L0 | Public CI PR / 신뢰된 push | Student D13 16시점·8사례, 10 tests 중 의도된 RED 2개, 새 문서 3 tests | 상태·테스트 수·SHA·합성 범위 |
| Protected Instructor L0 | 승인된 보호 브랜치 push & `axia-instructor-sealed` 환경 | Instructor 고정 SHA, G09 정답 blob, 8 참조 tests, 3 문서 tests, 기존 워크플로 제거 | `PASS/HOLD` + 테스트 수, 민감한 traceback 없음 |
| ROS/Gazebo L2·WSL2 L3 | 별도 기존 G07 인수 | 이번 정책 변경과 무관 | 신규 수행하지 않으면 NOT_RUN |

강사 비공개 job에서 `AXIA_CLOUD_CI`는 보호 환경에 저장된 최소권한 토큰이다. PR 또는 일반 public branch에서는 이 비밀 토큰에 접근하지 않는다. `persist-credentials: false`, `permissions: contents: read`, 임시 폴더 삭제를 강제한다.

## D13 정합성 고정

- Student main 검증 기준: `f1e69d72201bcb81478a9aac615cdb9d169821f7` (D13 가이드 PR #98 통과 후 병합).
- Instructor 이전 main에서 신규 정책 브랜치를 만들었으며, 보호된 최신 정답·가이드 검증 pin은 해당 Instructor 정책 후보의 **정확한 SHA**를 기록해야 한다.
- G09 원본 Git blob SHA-1: `85dd0fa35b2e7982b0c86020fdd4f4952e6a039f` (Student에 공개 금지).
- D13 Student: 공개 테스트 10개 중 초기 TODO P/N 2개 RED; Private Instructor: 참조 테스트 8개 GREEN, 신규 문서 계약 3개 GREEN.
- 이미 완료된 G07 Owner/L2 증거의 인수 상태를 새 정책으로 승격하지 않음.

## 검증과 병합 규칙

RED→GREEN→REFACTOR→REVIEW→COMMIT. Public CI에서 일반 job만 성공했고 protected job이 `skipped`이면 강사 통합 검증은 **HOLD_PUBLIC_ONLY**다. 보호 경로의 실제 `success` run ID + 정확한 Instructor SHA가 확인되어야 `INSTRUCTOR_PRIVATE_L0_PASS`로 승격한다.

강사 private job stdout/stderr는 **임시 파일에만** 보존하고 공개 workflow 로그·Artifacts에 정답 traceback/코드를 출력하지 않는다. 종료 시 항상 cleanup하며 Student checkout에 강사 정답을 복사하지 않는다.

**main 병합은 별도 사용자 승인 후 진행.** D11·D12의 기존 Instructor workflow는 제거 후보이나, 해당 교육단위의 Public CI 회귀 검증이 아직 없으면 해당 범위는 미검증으로 남긴다.

## 구현 경로

- `.github/workflows/block-d-d13-instructor-public-sealed-l0.yml`
- `tests/test_instructor_public_ci_policy_l0.py`
- Instructor `docs/CI_POLICY_PUBLIC_ONLY_KO.md`

**안전 한계:** 소프트웨어 STOP은 인증 하드웨어 E-Stop이 아니며, 정적/L0 CI 성공은 Gazebo/WSL2 실제 운행 인수 또는 안전 타이밍 인증을 뜻하지 않는다.
