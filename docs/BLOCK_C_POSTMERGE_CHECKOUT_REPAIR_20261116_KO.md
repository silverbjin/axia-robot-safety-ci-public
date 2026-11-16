# AXIA Block C — 정식 출고 후 브랜치 삭제에 따른 Bootstrap 회귀 수정 (2026-11-16)

**상태:** 교육용 D09~D12 MVP 정식 출고 승인 유지. Student/Instructor/Public CI 각 `main` 병합 완료. 이번 변경은 배포 후 bootstrap의 영구 브랜치 참조 수정에 한정.

## 최초 발견과 원인

- 승인된 Block C 병합 PR: Student #30, Instructor #184, Public CI #129→#130→#131.
- 병합 후 자동 정리에서 Student `feat/block-c-c01-synthetic-20261115`, Public CI 3개 Block C 브랜치 삭제 성공. Instructor 브랜치는 별도 cleanup 워크플로가 Runner 배정 전에 실패하여 남음(보호·미병합 브랜치와 구별).
- **첫 후속 회귀 경계:** `block_c/scripts/axia_c01_owner_wsl2_once.sh`의 `git clone --branch "$STUDENT_BRANCH"`가 이미 삭제한 Student 개발 브랜치를 요청. 정확한 SHA에 대한 후속 `fetch/checkout`은 clone 이전 실패로 실행되지 못함.
- `block_c/scripts/axia_block_c_owner_final_once.sh`에서도 Student 및 Instructor 개발 브랜치 이름을 clone에 사용하여 동일한 잠재 실패가 존재.
- 본 현상은 합성 센서/ML/ROS 데이터 기능 실패가 아니라 **출고 후 소스 접근 경로의 수명 주기 오류**.

## TDD RED → GREEN

1. **RED**: 새 `block_c/tests/test_postmerge_branchless_checkout.py`에서 영구 `main` 기반 clone과 exact SHA detached checkout을 요구. [Run #43790120115](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43790120115) 실제 **2 failed**(C01/Owner의 옛 브랜치 참조). [Run #43790054914](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43790054914)는 C01 clone을 포함하는 공개 CI 초기 RED.
2. **GREEN**: 동일 원샷의 clone 브랜치만 `main`으로 변경. 실제 검증 commit의 `git fetch --depth 1 origin <SHA>` + `git checkout --detach <SHA>` + `rev-parse HEAD` 비교는 그대로 유지. [Run #43790277681](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43790277681) GREEN: **3 postmerge tests + 4 C01 bootstrap contract + 3 policy tests + 10 fixture tests**, 실제 공개 학생 Git clone/fetch 성공. 동일 HEAD의 [Owner runner contract #43790277671](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43790277671), [Owner parity #43790277680](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43790277680), [Canary #43790277718](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43790277718) success.
3. **REFACTOR/REVIEW**: `block-c-c01-l0.yml`, `block-c-owner-field-parity.yml`, `block-c-owner-wsl2-contract.yml`의 push 필터에 `main` 추가. 기존 검증된 Owner 코드, ROS 타이밍 임계값, 정답 데이터/Hidden Test는 변경하지 않음. GitHub PR #132는 기존 3개 CI release PR에 대한 **최소 bootstrap 유지보수**.
4. **COMMIT**: 개발 작업과 회귀 결과를 PR #132에 커밋, 공개 CI GREEN 후 사용자 승인에 포함된 `main`으로 merge. Postmerge cleanup 워크플로는 PR #132 병합을 확인하고 해당 분기만 삭제하도록 추가.

## 출고 승인과 미검증 경계

- 출고 범위는 `SYNTHETIC_COURSE_FIXTURE`의 Block C D09~D12 교육용 ROS Jazzy L0/L1. 원본 Owner WSL2는 13/13 PASS 및 `READY_FOR_OWNER_APPROVAL`, 사용자 명시 승인으로 출고 결정됨.
- **실제 이 수정본의 Owner WSL2 비공개 Instructor clone은 현장에서 새로 수행하지 않음**. 공개 CI는 같은 C01 실행기의 공개 Student Git clone/fetch를 실행하고, Instructor 부분은 정적 검사와 공개 합성 동일 함수 계약으로만 검증한다.
- 실제 Gazebo 주행, 생산 Safety Guard/CM TTL, 인증 E-Stop은 여전히 교육용 인수 범위 밖.
- 학생 TODO 미완성(expected RED) 유지, 비공개 강사 정답·원본 증거는 공개 CI에 올리지 않음.
- Block C 이외 D07/G07/P4 등 병렬 개발 브랜치는 이번 승인으로 임의 삭제하지 않는다.

## 다음 실행 원칙

향후 브랜치 정리 전에는 반드시 **배포 실행기와 CI의 clone/checkout 의존 브랜치**를 검색해 제거 후보가 영구 참조되지 않는지 검증할 것. 병합 완료 브랜치를 삭제하기 직전, 공개 CI에 "branch deleted"를 모사한 테스트와 실제 `main` clone + 고정 SHA fetch를 포함한다. 삭제 완료 여부를 최종 기록하고, Runner 배정 오류처럼 삭제가 불가능한 항목은 미완료로 보고한다.
