# AXIA DAY 02 — 듀얼 G07 MVP Master-first 워크북 v4 / 학생 배포·CI·디자인 기획 검수 보고서

**날짜:** 2026-11-26 KST  
**판정:** `STUDENT_DUAL_MVP_SOURCE_RELEASE_PUBLISHED`; `PUBLIC_CI_L0_RED_GREEN_PASS`; `DUAL_WORKTREE_ONE_SHOT_PASS`; `HISTORIC_NATIVE_L2_SUCCESS_AND_FAILURE_REUSED`; `NEW_ROS_GAZEBO_L2_NOT_RUN`; `MAIN_NOT_MERGED`.

## 1. 두 개의 독립 버전 — 정확한 SHA 고정

| | 성공본 (기본 180분) | 실패본 (선택 심화 90분) |
|---|---|---|
| **Student 원본 실제 런타임 SHA** | `f7edb2d126502eeeed58ae014adadc7a2096d41b` | `a04f9a7da8d54bbd9f944d05388792cb706adf28` |
| Student 릴리스 브랜치 | [release/day02-g07-accepted-20261126](https://github.com/silverbjin/axia-robot-safety-student/tree/release/day02-g07-accepted-20261126) | [release/day02-g07-failed-l2-20261126](https://github.com/silverbjin/axia-robot-safety-student/tree/release/day02-g07-failed-l2-20261126) |
| **교육용 릴리스 HEAD** | `045afa5658045ce150effc242443f6fb8fa5c53f` | `d9ba3f78ae701697a5986a2bc856e4d856a73dd9` |
| Public 원본 Native workflow SHA | `64ba0161e66126b4743b4b12a859f4a5349ae58a` | `8e03ac0a912ca9b81bdddda70212e52e6d804389` |
| 기존 실제 Moving L2 | [Run #44965035965](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44965035965), **2/2 PASS** | [Run #44914827138](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44914827138), **0/2 FAIL** |
| Owner WSL2 L3 | 2026-11-22 사용자 원본 [numeric/lifecycle `PASS_SCOPED`](https://github.com/silverbjin/axia-robot-safety-ci-public/blob/c2c4f66c532be2a41855239860b9a9f5d60c4586/docs/operations/AXIA_G07_OWNER_WSL2_L3_POSTRUN_RAW_EVIDENCE_REVIEW_20261122_KO.md) | **NOT_RUN** |
| 학생 배포 PR | [Student #116](https://github.com/silverbjin/axia-robot-safety-student/pull/116), Draft | [Student #117](https://github.com/silverbjin/axia-robot-safety-student/pull/117), Draft |

**중요:** 교육 문서가 추가되어 릴리스 HEAD가 원본 SHA와 다르지만, **각각의 `block_B/day07/h01_runtime` 전체 Git 트리는 원본 런타임 SHA의 동일 경로와 정확히 일치**합니다. 따라서 안전 제어 기능·TTL·Nav2/CM/Guard/Goal 런타임을 새로 수정하지 않았습니다.

## 2. 개정된 교육 기획

- [Master-first Visual Workbook v4 기획서](https://github.com/silverbjin/axia-robot-safety-student/blob/release/day02-g07-accepted-20261126/special_lecture/day02/workbook/DUAL_MVP_WORKBOOK_PLAN_v4_KO.md)
- [완성형 Master Prompt](https://github.com/silverbjin/axia-robot-safety-student/blob/release/day02-g07-accepted-20261126/special_lecture/day02/workbook/MASTER_PROMPT_DAY02_DUAL_MVP_KO.txt)
- [실패한 MVP 심화 90분 가이드·6개 Unit](https://github.com/silverbjin/axia-robot-safety-student/blob/release/day02-g07-failed-l2-20261126/special_lecture/day02/workbook/ADVANCED_FAILURE_ANALYSIS_KO.md)
- [듀얼 릴리스 Manifest](https://github.com/silverbjin/axia-robot-safety-student/blob/release/day02-g07-accepted-20261126/special_lecture/day02/DUAL_RELEASE_INDEX.json)
- [실패 원본 관측 수치의 익명 요약 fixture](https://github.com/silverbjin/axia-robot-safety-student/blob/release/day02-g07-failed-l2-20261126/special_lecture/day02/evidence/OBSERVED_L2_0OF2_SANITIZED.json)

**본편:** U00~U13의 완성본 아키텍처, 입력/출력 Topic, Message, Node, Goal UUID, 종료 ACK, CM120/Guard150/Scan300, 실제 odom ZERO 증거 및 AI 응답 검증. **심화:** A01~A06에서 원본 실패 0/2의 최초 상태 전이·시점·RMW/Observer/Callback 경계를 구분하고, 가설/반증 테스트·격리 RED→GREEN→REVIEW를 수행합니다. **각 Unit A면:** AI의 잘못된 응답 분석. **B면:** 복사 프롬프트·설계 이유·블록/설정 해설·예상/실제 결과·AI 응답 QA.

**수업 시간:** 본편 정확히 180분(휴식 10분 포함), 심화 추가 90분(정규 3시간 밖). 최종 워크북 40페이지 PDF의 신규 디자인·전체 렌더링은 **NOT_DONE**이며 본 문서는 그 제작 명세와 학생용 소스 출고입니다.

## 3. 학생용 원샷 실행 (WSL2에서 아직 직접 실행한 것은 아님)

```bash
cd ~
git clone --single-branch --branch release/day02-g07-accepted-20261126 \
  https://github.com/silverbjin/axia-robot-safety-student.git axia-day02-success
cd ~/axia-day02-success
git checkout --detach 045afa5658045ce150effc242443f6fb8fa5c53f

python3 special_lecture/day02/scripts/verify_release.py
bash special_lecture/day02/scripts/prepare_dual_mvp.sh "$HOME/axia-day02-failed"
python3 "$HOME/axia-day02-failed/special_lecture/day02/scripts/verify_failed_case.py"
```

원샷은 실패 REF가 정확 `d9ba3f78…`와 일치하지 않으면 중단하며, 성공·실패 원본 트리를 모두 검사하고 두 버전의 작업 디렉터리를 분리합니다. **Goal/Gazebo 자동 실행·파일 덮어쓰기 없음**. 실패본 수정은 개인 브랜치를 새로 만든 후에만 합니다.

## 4. 공개 CI: RED → GREEN 실제 실행

- **Public 최종 workflow SHA:** `2319bb16883a93d76952ef473d0a226cb7bb2efa`.
- **최종 [Run #45776242912](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/45776242912): SUCCESS**.
- 구현 전 실제 RED contracts: Student 성공용 테스트-only `ce9f944baf6b6dffd926843ca9947736ab4ae581`, 실패용 테스트-only `c6b439a006f831c98d7e7793dbc9da25c132ed2b`에서 **필수 Manifest 누락 등 의도된 실패 발생**. Public 로그: `AXIA_DAY02_BOTH_PREIMPLEMENTATION_RED_CONTRACTS_CONFIRMED`.
- 구현 후 GREEN: 성공본 **9 tests OK**, 실패본 **6 tests OK**, total **15/15 PASS**.
- 성공·실패 각각 **전체 G07 런타임 Git subtree 동일성**과 **8개 Git blob SHA** 검사 PASS.
- 실패 0/2 원본 수치와 판정 `UNDETERMINED` fail-closed 검증, 비공개 교육용 정답/모델/rosbag 유입 방지 검사 포함.
- **실제 원샷 Worktree 생성**을 Public Runner에서 수행: `AXIA_DAY02_DUAL_WORKTREE_L0_READY NO_ROS_NO_GAZEBO_NO_GOAL`, `AXIA_DAY02_SINGLE_COMMAND_DUAL_WORKTREE_GREEN`.
- Public CI는 **L0 소스·기록·배포 계약** 검사만 수행. 새 실제 ROS·Gazebo·Goal 또는 현장 WSL2 L3는 **NOT_RUN**. 이전 Native L2와 Owner L3 증거는 **정확한 소스에 한정해 재사용**.

## 5. 실패본 과제의 본질과 잘못된 결론 금지

2026-11-21 **Cycle1 pre-Goal** 최초 `/scan` 수신 간격 439.011892ms, `/clock` 335.393855ms, `/odom` 374.025229ms; Goal은 발행하지 않았습니다. **Cycle2 post-Goal** 첫 FSM `BOOT_SAFE→NORMAL` 뒤 최초 blocking `/odom` 362.100229ms, 이후 CM `/cmd_vel_pre_guard` 379.730024ms 초과했습니다. 독립 RMW와 기존 Subscriber의 수신 차이를 보고도 DDS/Executor 단일 원인을 증명한 것으로 판단해서는 안 됩니다.

소프트웨어 종료의 `RCLError` 수정과 RMW 지연 근본 원인 입증은 별개입니다. 실패·성공 스냅샷의 **Student와 Public CI 구성 모두 달라 단일 변수 A/B가 아닙니다.** 학생이 수정한 새 SHA에서 Native 2/2를 확보하지 못하면 **HOLD**가 올바른 기술 판정입니다.

## 6. 저장소와 보안·승인

- **Student** 성공 릴리스 PR #116과 실패 릴리스 PR #117은 기존 검증 기준선 브랜치를 대상으로 한 Draft; `main` 미병합.
- **Public** 듀얼 배포 CI는 [PR #234](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/234) Draft; `main` 미병합.
- 과거 0/2 실험 PR Student #105/#107, Public #229/#230은 SUPERSEDED 미병합 종료 상태를 유지, 최초 타이밍 증거 보존.
- 강사 정답/hidden tests/Owner raw TAR/ZIP/rosbag/개인 경로·토큰은 학생 브랜치에 포함하지 않습니다.
- SW STOP은 인증된 E-Stop이 아닙니다; `certified_estop=false`, FastDDS 최초 지연 근본원인 `UNDETERMINED`, 장기 하드웨어 안정성 미검증, 성공 원본 자동 verdict `HOLD_RAW_REVIEW_AND_VISUAL_PENDING` 보존.
- `main` 통합은 반드시 별도 검증·리뷰·사용자 명시 승인 이후에만 수행합니다.

**최종 판정:** 두 개의 실제 G07 소스 SHA가 학생용 공개 브랜치로 배포되고, 공개 L0 TDD/무결성/원샷 설치가 통과했습니다. 교육용 워크북 **기획 v4**는 완료, 실물 40페이지 신판 제작·렌더링 QA는 추후 별도 작업입니다.
