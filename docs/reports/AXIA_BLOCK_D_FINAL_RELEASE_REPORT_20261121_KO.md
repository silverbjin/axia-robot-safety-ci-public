# AXIA BLOCK_D — D13~D15 통합 검증·최종 배포 보고서 (2026-11-21, KO)

**최종 한정 판정:** `AXIA_BLOCK_D_RELEASE_VERIFICATION=OFFLINE_L0_PASS`  
**실행 범위:** 강사·학생 실습 코드·교재·합성 데이터·증거 분석 및 기존 G07 기능/수치 기록의 SHA·계약 검증만. `ROS_GAZEBO_WSL2_NOT_RUN` — 이번 통합 인수에서 새로운 ROS 2 Jazzy/Gazebo Harmonic/Nav2 Goal 또는 강사 WSL2를 실행하지 않았다. 기존 G07 실물 Gazebo L2/강사 Owner L3 증거는 **이전 인수**로만 보존한다.  
**PPTX/슬라이드:** 별도 제작, 본 산출물에서 제외.  
**권한:** 사용자가 D15 main 병합 및 BLOCK_D 최종 검증·배포를 승인했다. 강사 비공개 정답은 Student 저장소로 병합하지 않는다.

## 1. 출시 대상·원본 커밋

| 저장소 | 검증된 실제 main SHA (최종 통합 자료 병합 후) | 역할 |
|---|---|---|
| Student `silverbjin/axia-robot-safety-student` | `2c1e7786d21e5f9385290e4bcedb9c4367c006fb` | D13/D14 TODO, D15 증거 Replay, 통합 학습 검증/가이드 |
| Instructor `silverbjin/axia-robot-safety-instructor` | `33d7647e927dc0f3b948d25dd0561377fb455a08` | 비공개 G09/G10 강사 정답, 수업 가이드·평가·봉인 검증 |
| Public CI (최종 보고서 작성 직전 main) `silverbjin/axia-robot-safety-ci-public` | `2a28d475e8be31af3327c5fe72560157f3f85804` | 기존 G07 Baseline·공개 CI. 본 보고서/통합 workflow는 별도 PR로 main 병합 예정 |

D15 선행 병합: Public #222 `2a28d475e8be31af3327c5fe72560157f3f85804`, Instructor #233 `714dc6816802eca79bc0387bf15bbab1067f3615`, Student #95 `aeb049b24dce36b0ac00bb47f349a2ffe0f58739`. D14 선행 main 병합도 유지한다. 최종 BLOCK_D 통합 가이드 변경은 Student #97, Instructor #235로 main 병합했다.

**기존 실물 기능 기준선:** `AXIA-G07-T04-DEMO-BASELINE-20261120-jrCIgoGl`; 기존 실제 Student runtime `5c7983598fa3bcd7148433a06f37a4e78b091273`, 기존 Public reviewer `362da68e31dd163a8d321601e191069c0d0a438b`.

### 보호된 원본 해시

- 기존 Student G07 Guard Git blob `cfcc7d53d0e7d2fbd0450f80332f6ddc3e4c2f9f`, Supervisor `920f36c966c7b72a858e73e120bc36598948f5d2`, Moving Goal runner `8bf6c00209f106a5c68f2fc5c57542654932bce4`, Demo 문서 `4d255be8eca57ca9447474e62063d43892f9bfb8`.
- Public G07 Owner script `26570de6762db8ade5c92b9d821fad0ebe368374`, 공개 파생 evidence `ae7d594b5452d96cc8802bc53bc8ad578fe99fb7`, 기존 원본 검수 보고서 `58dd49845e57fe4a47ea2c1d8407e41cb734c654`.
- Student 기존 `block_D/release/RELEASE_MANIFEST.json` 원본 Git blob `0b05d08d5bb5bbecaf94c0f41360a0168754708f` 보존. Stage1 메타데이터 검증 기록을 새 릴리스 인수로 소급 수정하지 않음.
- 비공개 P3 G09 원본 `p3_oracles.py` Git blob `85dd0fa35b2e7982b0c86020fdd4f4952e6a039f`; G09 Risk Policy `818a89077e95682c15906fba603b6eb8fe599d2c`; G10 compound `8ce0123e299e95fe5f49f2703ce55fa2250e220a`; G10 fixture `620f769f812e32f2c3d1fa193629668090fa756f`.
- SHA-1 표기는 *Git blob 식별자*이며 원본 Owner TAR/ZIP SHA256과 혼동하지 않는다.

## 2. 하루별 인수 결과 (Student 기본 TODO ≠ 학습 완료 코드)

| 실습 | 학생에게 공개된 출고 패키지 | 비공개 강사 참조 검증 | 교육 출력 |
|---|---|---|---|
| D13 G09 Reachability | `10` tests, 기본 TODO `intended_red=2` | **8/8 PASS**, 원본 참조를 학생에 임시 적용한 이전 공개 봉인 CI **10/10** | 16시점·8 합성 사례의 P/N/U; 학생 스스로 구현 |
| D14 위험정책 | `20` tests, 기본 TODO `intended_red=11` | **18/18 PASS**, 원본 참조를 학생에 임시 적용한 이전 공개 봉인 CI **20/20** | P/U 제한 요청, N으로 자동해제 금지, seq·출처·0.5초 TTL |
| D15 G07 증거 분석 | **18/18 PASS** (읽기 전용 완성 실행기) | **7/7 PASS** 강사 문서 계약 | CLEAR→SLOW→STOP, Goal 취소, odom 정지 유지, 타이밍·P/N/U 구분 |
| 기존 G07 Baseline | Public 기존 불변 계약 **4/4 PASS** | 실제 과거 Owner·Gazebo 별도 증거 보존 | 교육용 기능·수치 21/21, 원본 파일 141/141 |

D13·D14 기본 TODO가 RED라는 것은 **출고 실패가 아니라 학습자의 구현 공간**이다. 새 원샷 `BLOCK_D_RELEASE_STUDENT_CONTRACT_PASS`는 *올바른 미완성 Starter 배포*의 PASS다. 비공개 원본 정답 적용의 10/10·20/20 테스트와 학생 개인이 직접 완성한 결과는 구분한다.

## 3. 실제 공개 CI 실행 증거와 실패 수정

| 게이트 | 실제 GitHub Actions Run | 결과·의미 |
|---|---|---|
| 통합 학생 초기 RED | [#44879737092](https://github.com/silverbjin/axia-robot-safety-student/actions/runs/44879737092) | `ModuleNotFoundError: No module named 'block_D.tools'`, 통합 원샷 미구현으로 실패 |
| 통합 학생 GREEN | [#44879801487](https://github.com/silverbjin/axia-robot-safety-student/actions/runs/44879801487) | 5개 통합 테스트 OK, D13 10개(의도된 RED 2), D14 20개(의도된 RED 11), D15 18/18 |
| 최종 Student main | [#44880178625](https://github.com/silverbjin/axia-robot-safety-student/actions/runs/44880178625) | **SUCCESS**, main 통합 원샷과 G07 해시 |
| G07 + Student 공개 CI 후보 | [#44880032050](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44880032050) | 기존 G07 4/4 및 Student 통합 L0 |
| 보호된 강사·학생 합동 후보 | [#44880045629](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44880045629) | **SUCCESS, 두 Job**: 강사 통합 4/4·강사 D13 8/8, D14 18/18, D15 7/7, Student D13~D15·기존 G07 |
| **병합된 실제 Student/Instructor main 정확 SHA** | [#44880212578](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44880212578) | **SUCCESS, 보호된 두 Job**. 실출고 두 main pin으로 재검증 |
| 기존 D13 강사 정답 임시 적용 | [#44875120216](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44875120216) | 강사 8/8, 학생 정답 대체 **10/10** |
| 기존 D14 강사 정답 임시 적용 | [#44875926644](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44875926644) | 강사 18/18, 학생 정답 대체 **20/20**, 16개 합성 정책 PASS |
| 기존 D15 L0 실증 | [#44878410578](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44878410578) | G07 4/4, Student D15 18/18, Instructor 문서 7/7 |

`#44880212578`은 `axia-instructor-sealed` 보호 환경의 기존 승인된 릴리스 레인 `release/p2-g06-cm-ttl-20261110`에서 실행했다. 일반 feature/PR `main`에서는 비공개 job을 실행하지 않고 skip으로 기록하며, **skipped를 PASS로 해석하지 않는다**. 보호된 job이 실제 완료된 실행 ID를 위 표에 명시한다.

한때 D15 기존 보호 릴리스 브랜치에 `jrCIgoGl` 공개 fixture가 없어 CI [#44878345250](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44878345250)가 실패했다. 실물 안전 코드를 변경하지 않고 검증된 Public source `29a8c86f1fbfed51172353fd6c2df66af6867c0a`를 정확히 체크아웃하여 GREEN [#44878410578](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44878410578)을 확보했다. 동일 오류를 현장 재시도로 처리하지 않았다.

## 4. 인수 산출물·경로

### 공개 Student main

- **통합 상세 실행 가이드:** `block_D/BLOCK_D_STUDENT_FINAL_GUIDE_KO.md`
- **WSL2/Ubuntu 오프라인 단일 실행기:** `block_D/tools/verify_student_release.py`
- **통합 자동검증:** `block_D/tests/test_block_d_release.py`, `.github/workflows/block-d-final-student-l0.yml`
- **D13:** `block_D/day13/STUDENT_LAB_GUIDE_KO.md`, `reachability_student.py`, `run_lab.py`, `STUDENT_WORKSHEET_KO.md`
- **D14:** `block_D/day14/STUDENT_LAB_GUIDE_KO.md`, `risk_policy_student.py`, `run_lab.py`, `STUDENT_WORKSHEET_KO.md`
- **D15:** `block_D/day15/STUDENT_LAB_GUIDE_KO.md`, `run_lab.py`, `STUDENT_EVIDENCE_WORKSHEET_KO.md`, `FINAL_EVALUATION_RUBRIC_KO.md`

### 비공개 Instructor main

- **10시간 통합 상세 강사용 가이드:** `training/block_D/BLOCK_D_INSTRUCTOR_FINAL_GUIDE_KO.md`
- **비공개 단일 정답 계약 검증기:** `training/block_D/tools/verify_instructor_release.py`
- **비공개 통합 tests:** `training/block_D/tests/test_block_d_instructor_final.py`
- **D13:** `training/block_D/day13/solution/p3_oracles.py` 및 `INSTRUCTOR_GUIDE_KO.md`
- **D14:** `training/block_D/day14/solution/p3_g09_risk_policy.py`, `solution/p3_g10_compound.py`, `INSTRUCTOR_GUIDE_KO.md`, `ERROR_RESPONSE_GUIDE_KO.md`
- **D15:** `training/block_D/day15/INSTRUCTOR_DEMO_GUIDE_KO.md`, `DEMO_FAILOVER_KO.md`, **`INSTRUCTOR_ANSWER_KEY_KO.md` 비공개**

### 공개 CI main

- `.github/workflows/block-d-final-integrated-l0.yml`: 실제 합쳐진 Student/Instructor SHA와 기존 G07 공개 검수 pin; 비공개는 보호 레인에서만 테스트
- `tests/test_block_d_final_report_l0.py`: 본 최종 보고서·검증 수준·SHA·HOLD 수용 계약
- `docs/reports/AXIA_BLOCK_D_FINAL_RELEASE_REPORT_20261121_KO.md`: 이 보고서

## 5. Student 통합 클론/실행 명령 (한 터미널)

```bash
cd ~
git clone --depth 1 --branch main \
  https://github.com/silverbjin/axia-robot-safety-student.git \
  axia-block-d-student
cd ~/axia-block-d-student
git rev-parse HEAD
python3 block_D/tools/verify_student_release.py \
  --out /tmp/axia-block-d-final
```

정상 로그:

```text
BLOCK_D_D13_STARTER_L0_PASS tests=10 intended_red=2 cli_rc=2
BLOCK_D_D14_STARTER_L0_PASS tests=20 intended_red=11 cli_rc=2
BLOCK_D_D15_STARTER_L0_PASS tests=18 intended_red=0 cli_rc=0
BLOCK_D_RELEASE_STUDENT_CONTRACT_PASS=1 ROS_GAZEBO_OWNER_GOAL_NOT_RUN=1
```

실습 후 학생이 TODO를 직접 완성한 경우 통합 *Starter* 배포 검사는 더는 적용되지 않는다. D13은 해당 요일별 unittest **10/10**, D14는 요일별 unittest **20/20**으로 개인 구현 성취를 검사한다.

## 6. 인증과 시연을 혼동하지 않는 최종 범위

**기존 jrCIgoGl Owner:** 한 회 실물 Gazebo/Nav2 교육용 Moving Goal·숫자 21/21 ACCEPTED (이전 검수). 실제 Goal `EXECUTING`→동일 UUID `CANCELED(5)`; 전방 LiDAR CLEAR 2.024826m → SLOW 0.662775m → STOP 0.384303m; 최종 `/cmd_vel` STOP=0; odom ZERO 유지 1.029446초. 기존 실물 Gazebo 2-cycle 공개 CI [#44653465671](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44653465671)와 WSL2 원본 검수 결과를 새로 재실행하지 않았음.

**기존 한 세션 최대 타이밍:** Scan 253.822/300ms, CM source 68.093/120ms, CM Observer 70.981/120ms, Guard 내부 CM 수신 age 47.653/150ms, Guard 상태 72.352/150ms. 단일 실행에서 지표가 통과했다는 사실과 **모든 실행에서 전체 안전층 타이밍 안정성이 보장**된다는 주장은 다르다. 별도 간헐 오류 Guard 최초 래치 **188.578ms > 150ms** [Issue #157](https://github.com/silverbjin/axia-robot-safety-ci-public/issues/157) OPEN. 이번 릴리스에서 근본 원인이 해결되었다고 선언하지 않는다.

**원본 상태 불변:** `raw_machine_status=HOLD_RAW_REVIEW_AND_VISUAL_PENDING`, `owner_moving_l3_accepted=false`, `visual_content_verified=false`, `FORMAL_SAFETY_TIMING_ACCEPTANCE=NOT_CLAIMED`, `CERTIFIED_ESTOP=false`. `VISUAL_CONTENT_NOT_VERIFIED` = 실제 Gazebo/RViz 창 존재와 화면 속 내용 검증을 구별. 실제 새 ROS/Gazebo, 강사 WSL2 및 HTML 브라우저 화면 검증은 모두 `ROS_GAZEBO_WSL2_NOT_RUN`, `HTML_BROWSER_NOT_RUN`으로 표기한다.

**P/N/U와 G10:** D13 G09 예측 P/N/U, D14 제한 요청과 G10 15개 사건은 **합성 데이터**다. 별도 S04 실제 Gazebo L2 [#43455456960](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43455456960)은 G09 합성을 실제 Supervisor/CM/Guard에 연결했던 *다른 실행*이며 `jrCIgoGl` Owner의 실제 사람 검출을 증명하지 않는다.

**변조 테스트의 의미:** D15 Scan 301ms, Guard age 151ms, Goal Cancel 위조, dwell 0.5s, 인증 status 위조는 **학생용 합성 수치 반례 5/5 탐지**. 실제 현장의 최초 위반 시각은 공개 aggregate fixture에 포함되지 않아 `first_violation_timestamp=null`; 추측하여 만들지 않는다.

**인수 선언:** `AXIA_BLOCK_D_RELEASE_VERIFICATION=OFFLINE_L0_PASS` = 학생 Starter 배포·강사 비공개 정답·기존 실물 기준선 불변성의 **CI 준비 완료**. 새 Gazebo/Owner L3 검증, 정식 G10/G11 인증, 반복 안전 성능, 화면 콘텐츠·하드웨어 인증 E-Stop을 포함하지 않는다.

## 7. 배포 순서 및 Git 관리

RED → GREEN → REFACTOR(실행 명령을 main으로 정리) → REVIEW(PR 코멘트/변경 범위) → COMMIT(Public CI·Student·Instructor main 각각 SHA 보존). 사용자 승인으로 D15 관련 PR 세 건 및 이번 BLOCK_D 통합 가이드·CI 변경을 main에 병합한다. **기존 G07 runtime 파일·Baseline manifest 원본 변경 금지**를 지켰다.

마지막 검증은 각각의 실제 main SHA에서 다시 수행하여, 공개 CI의 통과 여부 및 최종 main 커밋을 PR과 배포 보고에 추가 기록한다. Main merge 전의 봉인 CI 성공만으로 배포 완료를 주장하지 않는다.
