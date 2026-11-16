# AXIA Instructor Actions 운영 종료 — 최종 관리 원샷 (2026-11-16)

## 목표와 현황

사용자 지침: **Instructor GitHub Actions는 사용하지 않고 Public CI에 공개 가능한 검증 계약만 유지한다.**

- Instructor `main` commit `86c1e2a8197ebc93e6e528d385c1a322b6e836a8`에서 **18개 Actions workflow 파일 제거 완료**, 원격 트리상 0개 확인. 이전 Git 히스토리는 보존.
- 공개 CI PR [#133](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/133) 병합. [Run #43792457174](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43792457174) **164 passed, 1 skipped**. 공개 대응 범위표: `public_ci/instructor_workflow_migration_20261116.json`.
- Instructor 저장소 **전체 GitHub Actions 기능 설정(enabled=false)**은 연결 도구에서 수정/확인 불가. 
- 이전 merged PR #184의 브랜치 `plan/block-c-d09-d12-freeze-20261115` 1개는 삭제 대기. **Private Actions cleanup 워크플로 재시도 금지.**

## Owner에게 남은 단일 관리 작업

공개 CI에서 테스트된 [Owner 관리 원샷](../scripts/axia_instructor_admin_closeout_once.sh)은 인증된 `gh` CLI로 다음 순서를 수행한다.

1. 대상이 정확히 `silverbjin/axia-robot-safety-instructor` 비공개 저장소인지 확인.
2. PR #184가 병합됐고, 병합 커밋 `d1f10b220143b4138c260768a59c35b6166abfe1`의 두 번째 부모 SHA와 삭제 대상 브랜치 HEAD가 **정확히 같은지** 검사.
3. GitHub API로 Actions를 비활성화하고, 다시 읽어 `enabled=false`인지 검증.
4. **위 조건이 모두 PASS일 때만** `plan/block-c-d09-d12-freeze-20261115` 하나의 ref를 DELETE한다. main 및 다른 계열 브랜치는 건드리지 않는다.

Owner WSL2에서 이미 `gh` 인증이 되어 있다면 다음 명령을 한 번 실행한다. **`gh auth status` 및 해당 저장소 admin 권한 필요**.

```bash
(
  set -Eeuo pipefail
  SHA="ba1b9ac257244c41235f1c9e46700a3b8998a11b"
  SCRIPT="$(mktemp)"
  trap 'rm -f -- "$SCRIPT"' EXIT

  curl -fL --retry 3 -sS \
    "https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public/${SHA}/scripts/axia_instructor_admin_closeout_once.sh" \
    -o "$SCRIPT"

  bash -n "$SCRIPT"
  bash "$SCRIPT" --self-check
  bash "$SCRIPT" --run
)
```

이 SHA는 GitHub에 저장된 수정 완료 원샷의 **고정 소스 커밋**이며 공개 CI [Run #43793348577](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43793348577)에서 168 passed, 1 skipped로 검증됐다. PR #134 병합 후에도 이 Git 객체는 main 역사에 보존된다.

### 기대 성공 출력(아직 실제 관리 실행 증거 아님)

```text
AXIA_INSTRUCTOR_ADMIN_SELF_CHECK_PASS_NO_MUTATION
AXIA_INSTRUCTOR_ACTIONS_DISABLED_VERIFIED enabled=false
AXIA_INSTRUCTOR_MERGED_BRANCH_DELETED=plan/block-c-d09-d12-freeze-20261115
AXIA_INSTRUCTOR_ADMIN_COMPLETE enabled=false deleted=1
```

검증되지 않은 계정 권한, Actions 설정 조회 실패, PR/브랜치 이동이 감지되면 `AXIA_INSTRUCTOR_ADMIN_HOLD_...`로 실패하고 변경하지 않는다. Actions를 먼저 비활성화했지만 브랜치 삭제가 실패한 경우 재수행 전 원격 상태를 확인한다.

## 공개 CI와 검증 범위

관리 원샷의 Bash 파싱·`--self-check`·고정 대상·불일치 브랜치 SHA 차단은 **실제 Public CI 테스트** `tests/test_instructor_admin_closeout.py`에서 검증한다. 가짜 `gh` 실행기로 위험한 변경을 모사하며 **실제 비공개 저장소 변경/API PUT·DELETE는 공개 CI에서 수행하지 않는다**.

본 조치는 ROS/Gazebo/Owner WSL2 교육용 L0/L1을 재실행하지 않고 GitHub 운영 경계만 변경한다. 인증 E-Stop과 SW stop은 별개이며, 실제 Guard TTL/Goal/Gazebo 주행을 새로 검증한 것이 아니다.

## 완료 판정

- Instructor `main`의 워크플로 파일 0개: **완료**
- Instructor `actions/permissions.enabled=false`: **Owner API 원본 확인 전 미완료**
- Instructor 잔여 Block C merged 브랜치 실제 삭제: **Owner API 원본 확인 전 미완료**
- Instructor Actions를 검증 게이트로 사용하지 않는 정책과 공개 CI 회귀: **완료**
