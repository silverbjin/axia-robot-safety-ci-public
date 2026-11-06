# AXIA 공개 CI — 브랜치·검증 인계

- 저장소: `silverbjin/axia-robot-safety-ci-public`, **Public**.
- 개발 브랜치: `feat/public-ci-bootstrap`, Draft PR #1.
- 강사용 Private 저장소 `silverbjin/axia-robot-safety-instructor`는 변경하거나 복제하지 않았다.
- 학생용 별도 Public 저장소 `silverbjin/axia-robot-safety-student`는 독립적으로 관리한다.

## 증거 및 실행 순서

1. Canary: GitHub-hosted Ubuntu Runner가 실재하고 실제 echo 출력이 있는지 확인한다.
2. Python Unit: `pytest -q -ra tests` 와 JUnit, Scan gap·SHA256 계약을 확인한다.
3. 실제 Jazzy DDS: `scripts/dds_echo_smoke.py`의 합성 메시지 pub/sub 결과를 Job 로그로 확인한다.
4. 공식 Gazebo: PR 이벤트에서 3회 **no-goal/read-only**. `workflow_dispatch` 10회는 Workflow가 default branch에 등록된 후 가능. 사용자 승인 전 `main`에 병합 금지.
5. 각 결과를 Head SHA·Job ID·JUnit/원본 stdout·evidence SHA256와 함께 보고한다.

## 제한

공개 S01-S05는 교육·환경 검증 샘플이며 실제 강사 Supervisor를 테스트하지 않는다. 성공하더라도 `P1 PRE-LOCAL BLOCKED`를 자동 해제할 수 없다. 인증된 E-Stop 성능 주장 금지.
