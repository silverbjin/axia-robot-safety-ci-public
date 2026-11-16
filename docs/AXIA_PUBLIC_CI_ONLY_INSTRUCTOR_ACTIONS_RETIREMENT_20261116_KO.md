# AXIA — Instructor GitHub Actions 사용 중지 / Public CI 단일 검증 운영 지침

**시행:** 2026-11-16. 사용자 명시 지시: **“Instructor의 GitHub Actions은 사용하지 않는다. 그 내용을 Public CI에서 활용한다.”**

## 목표와 금지사항

1. **Instructor private 저장소에서 GitHub Actions를 실행하거나 필수 출고 게이트로 요구하지 않는다.** Instructor `main`의 기존 `.github/workflows/` 18개를 사용 중지하고 Git 이력에만 보존한다. 다른 오래된 Instructor 브랜치에 워크플로 파일이 남을 수 있으므로, 완전한 저장소 수준 중지는 관리자가 GitHub Settings → Actions → General에서 Actions를 Disable해야 한다. 관리 설정 변경이 확인되지 않았으면 **‘main에서 워크플로 0개’와 ‘저장소 전체 Actions 비활성’은 구분**한다.
2. **Public CI** `silverbjin/axia-robot-safety-ci-public`에서 공개·독립 검증을 수행한다. Instructor Actions의 **의도/검증 항목**을 재사용하되, 강사 정답·Hidden Test·개인 WSL2 RAW·비공개 저장소 checkout·비공개 시크릿을 Public CI에 옮기지 않는다.
3. 공개 CI가 실제 실행하는 범위는 기존 공개 `public-contracts.yml`(합성 Python), `public-jazzy-dds.yml`(실제 Jazzy 합성 DDS), `public-gazebo-readonly.yml`(공식 Nav2/TB3 Waffle Gazebo 읽기 전용), `public-canary.yml`(Runner) 및 Block C C01/C05/C06·증거 감사 계약이다. **Public CI의 대응 계약이 비공개 P0/P1 소스·G00~G10 Goal·Supervisor Guard TTL·Gazebo Owner 현장 증명을 대체했다고 주장하지 않는다.**
4. 과거 Instructor Actions 18개 → 공개 CI 대응 워크플로 및 정확한 미검증 경계는 [이관 인벤토리](../public_ci/instructor_workflow_migration_20261116.json)에 기록한다. `equivalence=not_equivalent`는 이름·개념만 재사용하며 기능/인수 완료를 뜻하지 않는다.
5. 앞으로 현장 오류 발견 시 **공개 재현 가능한 부분부터** 공개 CI에서 RED→GREEN→REFACTOR→REVIEW→COMMIT. 공개적으로 재현 불가한 강사 소스 특성은 개인 Owner WSL2 또는 로컬 검증으로 표시하고 출고 PASS로 승격하지 않는다. Inspector의 Actions를 재활성화하거나 private CI를 우회적으로 호스팅하지 않는다.
6. Owner WSL2는 최종 통합 검수에만 사용한다. 특히 **최초 안전 상태 전이·최초 timing violation·노드간 topic 전달 주기와 TTL**을 관찰하며 SW Stop을 인증 E-Stop으로 부르지 않는다. Public DDS 통과를 생산 안전 TTL 통과로 확대하지 않는다.
7. 개발 보고서마다 파일 경로·실제 실행 명령·CI Run·HEAD·증거 SHA/범위·미검증 항목·브랜치/커밋을 남긴다. **main 변경은 사용자 승인 필요**, 기존 교육용 Block C 출고 승인은 이 문서와 별도로 보존한다.

## 이번 즉시 조치

- Instructor `main`의 `18`개 workflow 파일은 Git commit으로 제거해 더 이상 `main`에서 PR/Push/Dispatch 기반 새 설정으로 사용하지 않는다. *단, Instructor 오래된 브랜치에서 workflow가 남아 있을 수 있으므로 repo-level Actions disabled는 관리 설정 변경을 따로 확인해야 함*.
- Public CI의 기존 4개 공개 검증 프로그램과 Block C 공개 게이트를 재사용하고, 공개 회귀 테스트 4건으로 **18개 목록 완전성, 허위 동등성 승격 방지, 비공개 소스 부재, 공개 workflow 존재**를 검사한다.
- Instructor private Actions를 통해 브랜치를 삭제하려던 이전 시도는 **중단**한다. 이미 병합된 `plan/block-c-d09-d12-freeze-20261115` 한 브랜치는 Owner의 승인된 GitHub CLI/GUI로 직접 삭제한다. Public CI가 PRIVATE_BRANCH_DELETE_TOKEN을 가져서는 안 된다.

## 검증 수준

| 검증 항목 | 증명 가능한 범위 |
|---|---|
| Public Python L0 | 공개/합성 계약 |
| Public ROS Jazzy DDS L1 | 공개 메시지 송수신 |
| Public Gazebo L2 | 공식 스택·읽기 전용 cold start(실제 수행 시 Run별) |
| Owner WSL2 | 실제 현장·private source 인수(원본 증거가 제출될 때만) |
| Instructor GitHub Actions | **운영에서 제외**. 실패한 기존 private runner 결과는 더 이상 Release gate 아님 |
| Safety Guard TTL, certified E-Stop | **이 정책으로 새 검증 성립하지 않음** |

## GitHub 설정 완료 기준

**(A) 파일 기준:** `Instructor main`의 `.github/workflows` 하위 workflow 개수 = 0 (connector로 원격 확인).

**(B) 저장소 기능 기준:** `GET /repos/silverbjin/axia-robot-safety-instructor/actions/permissions`에서 `enabled=false` 확인. 현재 GitHub 연결 도구는 Actions 설정 변경 권한을 제공하지 않을 수 있다. **(A)는 (B)를 증명하지 않는다.**

**(C) 잔여 브랜치:** 해당 브랜치의 PR #184 merged, merge SHA 부모 및 브랜치 HEAD 동일 검증 후 Owner에서 직접 삭제. 실패하면 삭제되지 않은 상태로 보고.

## 실습용 작업 프롬프트

> Instructor GitHub Actions는 사용하거나 재활성화하지 않는다. 먼저 Public CI에서 재사용 가능한 공개 계약·실제 Jazzy DDS·공식 Nav2/Gazebo read-only 테스트를 검토한다. 강사 답안 및 비공개 증거는 절대 공개 CI에 체크아웃하지 않는다. 본 과제에서 재현 가능한 실패 경계를 Public CI에 RED로 추가하고, CI와 Owner가 동일하게 사용하는 소스/검증 함수만 최소 수정한 후 GREEN을 확인한다. 안전 TTL·현장 주행·E-Stop 검증을 과장하지 않는다. RED→GREEN→REFACTOR→REVIEW→COMMIT 단계마다 파일·명령·실제 출력·검증 한계·Git SHA를 남기며, 검증된 코드만 배포하고 Owner 최종 검수 및 main 병합은 승인 범위 내에서만 수행한다.
