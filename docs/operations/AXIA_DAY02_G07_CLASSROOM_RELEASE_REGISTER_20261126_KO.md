# AXIA G07 — 성공 SHA 기반 DAY02 학생용 릴리스·미병합 PR 정리 등록부

**작성일:** 2026-11-26 KST  
**상태:** `STUDENT_RELEASE_L0_PUBLIC_CI_PASS`, `EXISTING_G07_L2_2OF2_PASS_REUSED`, `EXISTING_OWNER_L3_PASS_SCOPED_REUSED`, `MAIN_NOT_MERGED`.

## 1. 최종 인수 기준선 — 이전 0/2 실패가 아닌 2026-11-22 성공본

| 대상 | 고정된 식별자 | 증거 |
|---|---|---|
| 학생 G07 정상 실행 코드 | `f7edb2d126502eeeed58ae014adadc7a2096d41b` | [Student 성공 PR #108](https://github.com/silverbjin/axia-robot-safety-student/pull/108) |
| 공개 엄격 Native Moving L2 | Public `64ba0161e66126b4743b4b12a859f4a5349ae58a` | [2/2 PASS #44965035965](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44965035965) |
| 실제 강사 WSL2 Owner L3 | `u88ZXW8W`, 사후 원본 검수 보고서 SHA `c2c4f66c532be2a41855239860b9a9f5d60c4586` | [RAW 증거 보고서](https://github.com/silverbjin/axia-robot-safety-ci-public/blob/c2c4f66c532be2a41855239860b9a9f5d60c4586/docs/operations/AXIA_G07_OWNER_WSL2_L3_POSTRUN_RAW_EVIDENCE_REVIEW_20261122_KO.md) |

Owner 실제 결과는 Moving Goal·CLEAR→SLOW→STOP·동일 UUID CANCELED(5)·odom ZERO 1.026194649s·안전 수신 주기·14토픽 rosbag·21 프로세스 정상 종료를 확인한 **교육용 기능/수치/Lifecycle PASS_SCOPED**입니다. 원본 자동 기계 verdict의 `HOLD_RAW_REVIEW_AND_VISUAL_PENDING`는 덮어쓰지 않았습니다. 독립 GUI 화면 콘텐츠 검수 `NOT_PROVIDED`, FastDDS 지연 근본 원인 `UNDETERMINED`, `CERTIFIED_ESTOP=false`입니다.

## 2. 교육 배포 코드와 검증 — 정확한 커밋

- **학생 공개 배포 브랜치:** [`release/day02-g07-accepted-20261126`](https://github.com/silverbjin/axia-robot-safety-student/tree/release/day02-g07-accepted-20261126)
- **학생 배포 최종 커밋:** `0a8c43d0334474608ed3825abe79c7efad37ec17`.
- **릴리스 전용 경로:** `special_lecture/day02/`; Manifest, 학생 README, 읽기 전용 Python 검증기, 5개 공개 계약 테스트, 배포 정책, 학생 Evidence 기록지.
- **검증 대상:** `block_B/day07/h01_runtime` 트리 전체가 기존 성공 SHA의 트리와 동일. 8개 핵심 운영 파일 Git blob SHA도 추가 확인. 공식 Nav2/CM/Guard/Goal/TTL 코드 변경 없음. 실행기는 ROS/Gazebo/Goal **전혀 실행하지 않음**.
- **RED 준비:** Student `ce9f944baf6b6dffd926843ca9947736ab4ae581` (Manifest/검증기보다 계약 테스트 선행, 실제 공개 RED CI 증거와 구별).
- **GREEN 배포 코드:** Student `a628df141d148fe7cfbc1a8cd7cba120bdb91568`, Manifest 상태 반영 최종 `0a8c43d...`.
- **공개 CI 최초:** [#45774381274](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/45774381274) `SUCCESS`.
- **공개 CI 최종 정확한 학생 SHA:** [#45774509890](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/45774509890) `SUCCESS`; Workflow commit `ec8eb6251a4080a535d472eae534163f2654e766`. 단계별 `Pin runtime tree`, `8-blob L0`, `5-unit regression/tamper`, `scoped L2/L3 provenance` 모두 성공.
- **학생 배포 PR:** [Student #116](https://github.com/silverbjin/axia-robot-safety-student/pull/116) Draft, 성공 SHA 기준 브랜치 대상, 미병합.
- **공개 CI PR:** [Public #234](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/234) Draft, 과거 검증 기준선 대상, 미병합.

**검증 경계:** 위 신규 #45774509890은 파일·문서·소스 무결성의 **L0 공개 CI**이고, **이번 릴리스에서 Gazebo L2 또는 강사 WSL2 L3를 다시 수행한 것은 아닙니다.** 기존 f7ed… + 64ba… + L3 원본을 변경하지 않았기에 기존 증거를 그대로 재사용합니다.

## 3. 이전 실패 PR의 최종 처리 — 증거 보존, 코드 미병합

| 저장소 | PR | 원래 근거 | 처리 |
|---|---|---|---|
| Student | [#105](https://github.com/silverbjin/axia-robot-safety-student/pull/105) | Native #44914827138 0/2 | `SUPERSEDED`, 미병합 종료 |
| Public | [#229](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/229) | Native #44914827138 0/2 | `SUPERSEDED`, 미병합 종료 |
| Student | [#107](https://github.com/silverbjin/axia-robot-safety-student/pull/107) | Native #44916662519 0/2 | `SUPERSEDED`, 미병합 종료 |
| Public | [#230](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/230) | Native #44916662519 0/2 | `SUPERSEDED`, 미병합 종료 |

모든 PR에 후속 성공 #108/#231과 L3 보고서를 연결하고 **최초 타이밍 위반 및 실패 증거를 유지**했습니다. Git 브랜치를 강제 삭제·rebase·force-push하지 않았습니다. 다른 G07 실험 Draft PR은 이번 범위에 포함되지 않습니다.

**성공 원본 PR:** [Student #108](https://github.com/silverbjin/axia-robot-safety-student/pull/108), [Public #231](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/231)은 2026-11-22 L3 사후 검수로 제목·설명을 갱신했으며, 둘 다 Draft·미병합 유지합니다.

## 4. 학생에게 배포하는 실행 명령 (WSL2 Ubuntu 24.04, Goal 없음)

```bash
cd ~
git clone --single-branch --branch release/day02-g07-accepted-20261126 \
  https://github.com/silverbjin/axia-robot-safety-student.git axia-day02-mvp
cd ~/axia-day02-mvp
git checkout --detach 0a8c43d0334474608ed3825abe79c7efad37ec17
python3 special_lecture/day02/scripts/verify_release.py \
  --out /tmp/axia-day02/release_result.json
python3 -m unittest discover -s special_lecture/day02/tests -p 'test_*.py' -v
```

**예상:** `L0_RELEASE_CONTRACT_PASS`, `checked_runtime_blobs=8`, public unit 5/5 PASS. 학생 현장 재실행 전에는 이를 학생 로컬 실행 PASS라고 보고하지 않습니다. 수업에서는 `README_KO.md`, `workbook/RELEASE_AND_BRANCH_POLICY_KO.md`, `evidence_templates/STUDENT_EVIDENCE_TEMPLATE_KO.md`를 사용합니다.

## 5. 운영 정책과 다음 게이트

- 학생 공개 저장소에는 **이미 공개된 완성 MVP** 및 읽기 전용 실습 자료만 배포. 강사 비공개 정답/hidden tests, Owner 로컬 원본 TAR·ZIP·rosbag 및 개인 경로·비밀값을 공개하지 않습니다.
- 안전 SW STOP을 인증 E-Stop으로 소개하지 않습니다. Safety 수신 120/150/300ms 등 기준 임의 완화 금지, 자동 Goal 발행 금지.
- 학생 릴리스 브랜치 `0a8c43d...`와 CI workflow `ec8eb...`는 정확한 커밋으로 재현합니다. 수업 실행기는 Goal·Gazebo를 시작하지 않습니다.
- **main 미병합:** Student `main=93fd3e4838470f3ac836cc626e05ddb6d18e40e7`, Public `main=37feba99c39776cccc9dca1698937c9a970d1fe9`는 본 작업에서 변경하지 않았습니다.
- 나중에 `main` 통합을 원하면 현재 main의 Block C/D 변경과 충돌 여부 점검, 운영 파일 차이 분류, 정확한 변경 SHA 공개 CI 회귀, 사용자 명시 승인 이후에만 병합합니다.

**결론:** 최종 실패로 기록된 2026-11-21 0/2 후보가 아니라 **2026-11-22 실제 성공 SHA 기준의 학생용 완성 MVP 릴리스 관리 및 공개 L0 검증이 완료**되었습니다. 수업 배포용 브랜치 이용 가능; 전체 로봇 안전 인증·장기 신뢰성 보증·main 병합은 주장하지 않습니다.
