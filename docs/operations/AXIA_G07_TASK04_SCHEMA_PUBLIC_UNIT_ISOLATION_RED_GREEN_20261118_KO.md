# AXIA G07 Task04 — public-unit / native Path schema 계약 분리 RED→GREEN 교육용 보고서

- 날짜: 2026-11-18 KST
- 개발 범위: **Task04 공개 Python 계약 격리 한 건**. 새로운 ROS 노드, Nav2 포크, Goal 발행 경로, TTL 완화 없음
- 저장소: `silverbjin/axia-robot-safety-ci-public`
- 브랜치: `fix/g07-task04-owner-wsl2-public-pregate-20261118`, Draft PR #169
- 기준 Student 코드 SHA: `01752add2e30c90c4d3286ef3a450f97746ecb55`
- 수정 커밋: `ef855371ee4cfe2d6a30c092bb3b338dd631e5c3`
- 최종 공개 unit 원본: [Actions #44240074839](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44240074839), Job `134585515680`, **228 passed in 1.56s**
- 정확한 실주행 판정: **Task04 Owner WSL2/WSLg Moving Goal L3 NOT_RUN**, `AXIA_MVP_DEMO_ACCEPTED=HOLD`

## 1. 실패 재현 및 최초 경계

실제 공개 `python -m pytest -q -ra tests --junitxml=results/junit-public.xml` 실행
[Run #44238649926](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44238649926),
Job `134580817326`의 출력은 **227 passed / 1 failed**이다. 실패 단언:

```text
tests/test_g07_task04_native_path_stage_schema.py:17
self.assertTrue(STUDENT.is_file())
E AssertionError: False is not true
1 failed, 227 passed
```

테스트는 `ROOT.parent/student/block_B/day07/h01_runtime/tools/d07_h01_path_visual.py`가 존재할 것이라고 가정했다. 일반 공개 Python job은 **CI repo 하나만 체크아웃**한다. 따라서 이 실패는 ROS Path schema 위반의 증거가 아니라 **검증 대상 fixture 부재/테스트 실행환경 전제 불일치**이다. 기존 native-Xvfb workflow는 반대로 `ci/`와 정확한 공개 Student SHA를 각각 체크아웃하며, 실제 Path 모듈 테스트를 수행하도록 구성돼 있다.

동일 테스트를 학생 파일 없이 격리 재현하면 수정 전 `1 failed, 1 passed`이며 `STUDENT.is_file()`이 처음으로 실패한다. 다른 계약이나 안전 전이가 먼저 실패한 것이 아니다.

## 2. 단일 가설과 최소 수정 (GREEN)

가설: 범용 unit에서는 **공개 Student의 정확한 checkout 계약을 정적으로 검증**하고, 실제 native job에서는 **체크아웃한 원본 Python 모듈을 동적으로 검사**하면 두 job 모두 거짓 PASS 없이 분리할 수 있다.

오직 `tests/test_g07_task04_native_path_stage_schema.py`를 수정했다.

1. Native workflow 텍스트의 정확한 `ref: 01752add...`, `path: student`, `git -C student rev-parse HEAD` 동등성 검사, `test_g07_task04_native_path_stage_schema.py` 실행 명령을 **모든 레이아웃에서 필수 정적 검증**한다.
2. Student 소스 파일이 없는 **일반 public-unit** 환경에서는 이 정적 계약 검사 결과로 종료한다. 이는 실제 Path 함수 동적 실행을 주장하지 않는다.
3. 실제 native workflow의 checkout 위치인 `GITHUB_WORKSPACE/ci`에서 Student 소스가 없다면 `NATIVE_PINNED_STUDENT_PATH_MISSING`으로 **즉시 FAIL**한다. 실제 native checkout에서는 원래의 `validate_official_path` 호출과 `stage`, `PHASES` 검사를 그대로 수행한다.
4. native workflow의 실제 소스 SHA 검사, 모듈 존재 확인 경계와 Path DDS subscribe 판정, `goal_sent=false`는 그대로 유지한다. workflow나 Student 실행 코드를 수정하지 않는다.

## 3. 실행 명령과 **실제** 출력

### 로컬 ROS-free 좁은 회귀

```bash
python3 -m pytest -q tests/test_g07_task04_native_path_stage_schema.py
python3 -m py_compile tests/test_g07_task04_native_path_stage_schema.py
```

```text
# Before, Student 파일 없는 일반 레이아웃
1 failed, 1 passed in 0.08s
# After, Student 파일 없는 일반 레이아웃
2 passed in 0.03s
# After, 실제 native 레이아웃(ci/)에서 Student 파일 의도적 제거
1 failed, 1 passed in 0.06s
AssertionError: 'ci' == 'ci' : NATIVE_PINNED_STUDENT_PATH_MISSING
```

세 실행 모두 **별도 ROS-free 격리 재현**이며, 실제 Gazebo 실행이라고 주장하지 않는다.

### 실제 공개 GitHub Actions GREEN

```bash
python -m pytest -q -ra tests --junitxml=results/junit-public.xml
```

- 실제 Actions [#44240074839](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44240074839): `public-unit` **success**, 원본 출력 `228 passed in 1.56s`
- 같은 수정 커밋의 공개 runner canary [#44240074838](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44240074838): **success**
- RED #44238649926의 다른 227개 성공을 새 GREEN으로 복사하지 않았다. **228개는 수정 커밋의 실제 단일 Actions 재실행 결과**이다.

### 실제 Gazebo L2의 별도 경계 — 이미 성공한 결과 재사용

[Native Xvfb Run #44237948105](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44237948105)는 GUI 원본 `rc=0`, RViz/Gazebo X11 양쪽 창 감지, 그후 CI verifier의 `KeyError: 'phase'`로 **FAILED**.

정확 소스 필드 `stage` 수정 후 [Run #44238643061](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44238643061), Job `134580794869`, source `5bb0cd72086f2f1a057f382649b773fff106f1f9`에서 **12/12 native용 L0 + 실제 ROS Jazzy/Gazebo Harmonic/TB3/공식 Nav2/RViz2 Xvfb L2**가 성공했다.

```text
AXIA_G07_TASK04_NATIVE_RUNNER_RC=0 RVIZ_X11=1 GAZEBO_X11=1
AXIA_G07_TASK04_PUBLIC_REAL_GAZEBO_RVIZ_XVFB_PATH_SUBSCRIBER_L2_PASS
AXIA_G07_TASK04_OWNER_WSL2_WSLG_GPU_L3_NOT_RUN
```

실제 official Path의 before/intrusion/restored 3단계 `stage`와 각 `rviz_subscription_count>=1`을 원본 하나의 native 실행에서 검증했다. **이번 수정 커밋에서는 native ROS 런타임과 workflow를 변경하지 않았고**, 이미 확보한 동일 pinned Student의 native L2 성공을 다시 실행한 것으로 주장하지 않는다. 이 결과는 headless Xvfb 소프트웨어 GUI 검증이며 **Owner WSLg GPU 또는 Moving Goal 검증이 아니다**.

## 4. REFACTOR → REVIEW → COMMIT

- REFACTOR: 변경 범위가 한 테스트 파일의 실행 레이아웃 분기에 그치므로 추가 구조 리팩터링은 하지 않음.
- REVIEW: 예상치 못한 전역 skip 없음. 정확 공개 Student SHA와 native 검증 명령을 확인. native `ci/` 레이아웃에서 필요한 파일 누락은 여전히 fail-closed. `phase` 문자열 재도입을 막는 두 번째 테스트는 계속 실행. 일반 Python runner의 ROS 설치/clone 불필요. 문서/테스트 외 범위 확대 없음.
- COMMIT: [`ef855371ee4cfe2d6a30c092bb3b338dd631e5c3`](https://github.com/silverbjin/axia-robot-safety-ci-public/commit/ef855371ee4cfe2d6a30c092bb3b338dd631e5c3), 공개 PR #169 브랜치. **main 병합/Student 코드 변경 없음**.
- 변경 파일 경로: `tests/test_g07_task04_native_path_stage_schema.py`, 본 교육용 보고서.

## 5. 현장 최초 오류 재발 방지 및 Owner 단일 실행

이전 WSL2 현장 원본 ZIP SHA256 `60794337c9dd346c08be41571fec7b84a931154b27d9a06566eaea835d587415` (내부 SHA 11/11 PASS). Bash `$_`가 `GZ_PARTITION`에 직전 `ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST` 인자를 섞는 최초 오류는 공개 RED #44237062643 → GREEN #44237386904에서 재현·차단됐다. GUI watcher의 첫 자식 종료, Transport topic, Path subscriber 증거를 tar.gz 안으로 보존하는 Owner 래퍼가 공개 브랜치에 존재한다. 이전 잘못된 실행기 SHA `4db31c90...`는 **사용 금지**.

강사 WSL2에서 사용할 **NO_GOAL GUI 사전게이트** 단일 명령은 `docs/operations/AXIA_G07_TASK04_OWNER_WSL2_PUBLIC_GUI_PREGATE_20261118_KO.md`를 따른다. 검증된 실행기 SHA `5bb0cd72086f2f1a057f382649b773fff106f1f9`를 고정하여 `scripts/axia_g07_task04_public_owner_wsl2_pregate_once.sh`를 `--run`으로 실행한다. 현장 증거는 `$HOME/axia_g07_task04_wsl2/*.tar.gz{,.sha256}`로 생성된다. 이 실행기는 **Moving Goal을 발행하지 않는다**.

## 6. 검증 수준과 보류 조건

| 항목 | 판정 |
|---|---|
| 범용 공개 Python 228계약 | **PASS**, 실제 Actions #44240074839 |
| native 체크아웃 누락 fail-closed | **PASS**, ROS-free 의도적 음성 테스트 |
| 실제 NO_GOAL Gazebo+RViz Xvfb L2 | **PASS (기존 원본)**, Actions #44238643061 |
| 최초 WSL2 partition 오염 회귀 | **PASS (기존 원본)**, #44237386904 |
| 강사 WSL2/WSLg/GPU 실제 화면 재인수 | **NOT_RUN** |
| 강사 WSL2 Moving Goal/CM120·Guard150·Contact0·Bag14·ACK 동일 실행 | **NOT_RUN** |
| 실제 하드웨어 E-Stop 인증 | **NOT_CLAIMED** |
| Public/Student main 병합 | **NOT_MERGED** |

Task03의 실제 Moving Goal L2 [#44223320904](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44223320904)은 별도 증거로 유지한다. Task04 NO_GOAL GUI의 완료와 Task03 Moving Goal을 서로 조합해 Task04 Owner L3 PASS를 만들지 않는다.

```text
AXIA_G07_TASK04_PUBLIC_UNIT=PASS_228_OF_228
AXIA_G07_TASK04_PUBLIC_NATIVE_XVFB_L2=PASS_PRIOR_RUN_44238643061
AXIA_G07_TASK04_OWNER_WSL2_WSLG_L3=NOT_RUN
AXIA_G07_TASK04_OWNER_MOVING_L3=NOT_RUN
AXIA_MVP_DEMO_ACCEPTED=HOLD
CERTIFIED_ESTOP=false
MAIN_MERGED=false
```
