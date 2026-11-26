# AXIA DAY02 — G07 MVP 시나리오 운영 가이드·읽기 전용 시연기·공개 CI QA (2026-11-26)

**최종 판정:** `SCENARIO_GUIDE_RELEASED_ON_STUDENT_FEATURE_BRANCH`; `SCENARIO_REPLAY_L0_PUBLIC_CI_PASS`; `G07_RUNTIME_SOURCE_UNCHANGED`; `NEW_L2_L3_NOT_RUN`; `MAIN_NOT_MERGED`.

## 1. 사용자 요구와 기존 기능 재사용 판단

원본 G07 MVP는 Gazebo Harmonic/TurtleBot3 Waffle/공식 Nav2·Collision Monitor + Safety Supervisor/Fault Injector/Base Guard/Verifier를 이미 갖췄습니다. **추가 Moving 제어기·새 Goal publisher·안전 TTL 변경은 불필요**합니다. 기존 러너를 재사용하고 학생 수업에는 읽기 전용 역사적 수치 카드만 추가했습니다.

사용 가능한 학습 단위:
- **S01** Gazebo→Bridge→`/scan`→`/safety/scan` 준비/역할 구분
- **S02** CLEAR, 실제 WSL2 전방 2.048107m, CM 0.062925m/s, Base Guard final 0.037684m/s
- **S03** SLOW, 전방 0.674758m, CM 0.004810m/s, 최종 0.003422m/s
- **S04** STOP, 전방 0.396788m, CM/final 0.0m/s; `/odom` 추가 검증
- **S05** exact Goal UUID CANCEL `CANCELED(5)`, odom ZERO dwell 1.026194649s; 누적 실제 이동 0.129946523m
- **S06** Nav/Localization ACK true, CM exit0, 21개 launch 프로세스 정상 종료
- **A01** 실패본 2026-11-21 Native L2 0/2, Cycle1 pre-Goal Scan 439.011892ms/Clock335.393855ms/Odom374.025229ms, Cycle2 post-Goal 첫 Odom362.100229ms/CM preGuard379.730024ms — **근본 원인 UNDETERMINED**

## 2. SHA와 검증 범위

| 항목 | 정확 기준선 | 결과 |
|---|---|---|
| Student 성공 런타임 원본 | `f7edb2d126502eeeed58ae014adadc7a2096d41b` | 기존 코드·주행 계약 보존 |
| 원본 성공 Public | `64ba0161e66126b4743b4b12a859f4a5349ae58a` / [#44965035965](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44965035965) | 실제 Moving Gazebo **2/2 PASS** · 재실행 안 함 |
| Owner 원본 사후 RAW | [2026-11-22 보고서 c2c4f66](https://github.com/silverbjin/axia-robot-safety-ci-public/blob/c2c4f66c532be2a41855239860b9a9f5d60c4586/docs/operations/AXIA_G07_OWNER_WSL2_L3_POSTRUN_RAW_EVIDENCE_REVIEW_20261122_KO.md) | 실제 WSL2 1회 수치·Lifecycle `PASS_SCOPED` (원본 자동 HOLD 유지) |
| Student 실패본 원본 | `a04f9a7da8d54bbd9f944d05388792cb706adf28` | `0/2 FAIL` |
| 실패 Native Public | `8e03ac0a912ca9b81bdddda70212e52e6d804389` / [#44914827138](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44914827138) | 실패 두 사이클, Owner L3 NOT_RUN |
| 신규 학생 시나리오 변경 HEAD | `f43df3132c8c1dac29f7c980274cd85bcdda02fc` | **실제 G07 런타임 Git subtree SHA 동일성** 확인 |
| 신규 공개 시나리오 CI Workflow HEAD | `62f0ca9f99e94ec555453cb5f45b11a65f8f4d59` | [**Run #45780391900 SUCCESS**](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/45780391900) |

**L0만 신규 실행:** 실제 Native L2 2/2와 Owner L3는 과거 인수 증거를 정확한 SHA로 재사용하였으며, G07를 오늘 다시 실행하지 않았습니다. 독립 GUI 화면 콘텐츠 확인 `NOT_PROVIDED`, FastDDS 최초 지연 근본 원인 `UNDETERMINED`, 인증 E-Stop `false`.

## 3. 변경된 파일 (학생 feature 브랜치)

- `special_lecture/day02/scenarios/SCENARIO_OPERATION_GUIDE_KO.md`: 시나리오별 실행·질문·데이터/코드 연결·강사 NO_GOAL/Owner 라이브 옵션·슬라이드 43장 대응
- `special_lecture/day02/scenarios/PROVEN_G07_SCENARIO_SNAPSHOT_20261122.json`: 공개 원본 보고서 수치만 선정한 교육용 스냅샷. **원본 rosbag 아님**
- `special_lecture/day02/scripts/g07_scenario_replay.py`: `--case success|failed|compare`, `--json-out`(기존 파일 덮어쓰기 거부), ROS·Gazebo·Goal·네트워크 호출 없음
- `special_lecture/day02/tests/test_g07_scenario_demo.py`: 7개의 검증 계약; 오염된 수치/출처는 fail-closed
- `special_lecture/day02/evidence_templates/SCENARIO_STUDENT_OBSERVATION_KO.md`: 학생 관측·AI 답변 QA·개인 SHA
- `special_lecture/day02/README_KO.md`: 이번 시나리오 자료로 연결

**운영 런타임 전체 `block_B/day07/h01_runtime` Git tree를 원본 `f7edb2...`와 비교하여 완전 일치 PASS.** Nav2/CM/Guard/Supervisor/Fault Injector의 동작 코드 변경 없음.

## 4. RED → GREEN → REVIEW → COMMIT 공개 CI 실제 결과

- **RED 계약 선행 커밋** `b8ae7418e2bae7cdff297004aef469f3cf8d2bac`: 구현 전 테스트가 `RED: historic scenario snapshot missing`으로 실패하는 사실을 [Run #45780391900](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/45780391900)에서 재현. `AXIA_DAY02_G07_SCENARIO_PREIMPLEMENTATION_RED_CONFIRMED`.
- **GREEN 구현** `1c50b69fd6ae5db82e039dd76eed254c89476889`, 가이드 추가 `292099e2da6c3c8a6b0d97a05a164219b0a7b078`.
- **첫 CI 회귀 실패** [#45780103207](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/45780103207): 신규 테스트 2개가 JSON schema의 중첩 필드명과 불일치(`certified_estop`, `first_blocking_odom_ms`). **ROS/Gazebo 실패가 아님.** 원본 수치/안전 코드 미변경, 테스트 이름 정렬 커밋 `71ba9871697926268fd8039bf5d729d1a1e6683a`.
- **GREEN 중간** [#45780214452](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/45780214452) PASS 16 tests.
- **학생 최종** `f43df3132c8c1dac29f7c980274cd85bcdda02fc`: 실제 43장 강의 목차(05~12/27~30/38~43)와 시나리오 연결.
- **공개 최종 CI** [#45780391900](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/45780391900) **SUCCESS**, Workflow commit `62f0ca9f99e94ec555453cb5f45b11a65f8f4d59`:
  - `AXIA_DAY02_G07_SCENARIO_SUCCESS_RUNTIME_TREE_UNCHANGED_PASS`
  - `AXIA_DAY02_G07_SCENARIO_PREIMPLEMENTATION_RED_CONFIRMED`
  - **`Ran 16 tests ... OK`**
  - `AXIA_DAY02_G07_SCENARIO_REPLAY_EVIDENCE_QA_PASS`
  - `AXIA_DAY02_SCENARIO_PUBLIC_DISTRIBUTION_SCOPE_QA_PASS`

## 5. 학생 실행 명령 (공개 CI에서 실행된 범위)

```bash
# 학생용 성공본 + DAY02 시나리오 교육 도구를 분리된 feature 브랜치에서 사용
git clone --single-branch --branch feat/day02-g07-scenario-demo-20261126 \
  https://github.com/silverbjin/axia-robot-safety-student.git "$HOME/axia-day02-scenarios"
cd "$HOME/axia-day02-scenarios"
git checkout --detach f43df3132c8c1dac29f7c980274cd85bcdda02fc
python3 special_lecture/day02/scripts/verify_release.py
python3 special_lecture/day02/scripts/g07_scenario_replay.py --case success
python3 special_lecture/day02/scripts/g07_scenario_replay.py --case failed
python3 special_lecture/day02/scripts/g07_scenario_replay.py --case compare
python3 -m unittest discover -s special_lecture/day02/tests -p 'test_*.py' -v
```

**예상/CI 실제:** read-only L0, 16 tests OK. 이 명령들이 학생 개인 WSL2에서 실행됐다는 주장은 하지 않습니다. 새 파일을 출력하려면 `--json-out "$HOME/axia-day02-evidence/scenario_compare.json"`을 추가하며 이미 존재하는 파일은 덮어쓰지 않습니다.

## 6. 필요 시 기존 라이브 데모 재사용

강사용 **NO_GOAL**: `block_B/day07/h01_runtime/scripts/d07_h01_gui_no_goal_once.sh --self-check|--doctor|--run`. 기존 D07 별도 실증/시연용이며 새 SHA WSL2 GUI QA는 **NOT_RUN**.

강사용 **Moving G07**: Public `c2c4f66...`의 `scripts/axia_g07_stabilization_wsl2_final_once.sh --self-check|--ci-check|--run`; `--run`은 실제 ROS/Gazebo/Goal 발행, 새 현장 시연/로컬 동의가 필요하며 이번 공개 L0 CI에서는 미실행. 기존 Owner 1회 인수 결과를 반복 측정한다고 자동 주장하지 않음. 실패 새로 발견 시 **최초 타이밍 위반 재현을 CI RED→GREEN으로 먼저 편입**.

## 7. 출고/미검증/브랜치

- **Student** `feat/day02-g07-scenario-demo-20261126` 독립 feature branch, Draft PR 작성, `main` 병합 없음
- **Public CI** `ci/day02-g07-scenario-replay-20261126` 별도 branch, 공개 L0 PASS, `main` 병합 없음
- **새 L1 ROS 2 런타임:** NOT_RUN
- **새 L2 Native Gazebo Moving:** NOT_RUN
- **새 L3 강사 WSL2 실제 시연:** NOT_RUN
- **학생 실습 L0:** CI runner 성공, 개별 학생 로컬 아직 NOT_RUN
- **장기 그래픽 재현/성능·공식 안전 인증:** NOT_CLAIMED

**결론:** 기존 안전 MVP에 새로운 주행 기능을 추가하지 않고, 관측 근거를 바탕으로 S01~S06과 F01/F02를 강의·실습에서 활용하는 상세 가이드와 오프라인 데모가 신규 공개 CI에서 재현 가능하게 검증되었습니다.
