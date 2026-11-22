# AXIA Velog Domain AI Labs — 5편 L0 검증·배포 보고서 (2026-11-23 KST)

## 1. 개발계획 → 개발 → 검증 → 배포 결과
- 기준: Instructor `docs/baselines/AXIA_Robot_Safety_MVP_Baseline_Scenario_Acceptance_v1_KO.md`.
- 원본 AXIA G07/공식 Nav2/Collision Monitor를 수정하지 않는 **5개 독립 `ament_python` 교육용 패키지**.
- 강사: 비공개 reference 5개, 공개 계약 테스트 24개, 비공개 네거티브 테스트 5개, 강사 해설.
- 학생: 독립 레포의 5개 TODO, 공개 24개 RED tests, Mermaid/코드 해설/선택 ROS CLI/AI 프롬프트.
- CI: 공개 레포에 학생 스캐폴드/RED 검사와 `axia-instructor-sealed` 보호형 강사 GREEN 검사.
- 배포: **Instructor PR #248 main MERGED**; Student PR #112, Public PR #232 open feature branches only.

## 2. Git SHAs / PRs
| 영역 | 커밋 | PR / 최종 |
|---|---|---|
| Instructor reference GREEN | `e049cd85ea52ba4d55c0b79dbb96aa8476a6b10e` | [Instructor PR #248](https://github.com/silverbjin/axia-robot-safety-instructor/pull/248) MERGED |
| Instructor main merge | `da1487510f08b8f3a7d84d4e282e8aba31da1acd` | main |
| Student TODO RED | `89277c433a1b6485b8926712b54b6c0b133f11ec` | [Student PR #112](https://github.com/silverbjin/axia-robot-safety-student/pull/112) OPEN |
| Public CI feature | `14cf910a3d73f988a902ed6e723cf34ada4ce500` | [Public PR #232](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/232) OPEN |
| Sealed CI execution | `b878354976e1b8af5122362d37796f87f9e5fd34` | [Actions #45085852414](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/45085852414) SUCCESS |

## 3. 실제 CI 출력 및 검증의 의미
- `student-scaffold-expected-red`: **SUCCESS** (student 의도적 NotImplementedError 24개 확인)
  - `AXIA_VELOG_FIVE_STUDENT_TODO_PACKAGES_AND_DIAGRAMS_PASS`
  - `AXIA_VELOG_STUDENT_EXPECTED_RED_24_OF_24_PASS_L0`
- `instructor-private-green-sealed`: **SUCCESS** (정확한 Instructor SHA 고정)
  - `AXIA_VELOG_INSTRUCTOR_PRIVATE_29_OF_29_GREEN_L0`
  - `PRIVATE_SOURCE_SHA=e049cd85ea52ba4d55c0b79dbb96aa8476a6b10e`
- 강사 로그는 보호된 임시 파일에만 남기고 사용자에게 노출되지 않음.
- 사용자 로컬 WSL2, ROS2 Jazzy `colcon build`, Gazebo Harmonic Goal/physics **이번 배포에서 미실행**. 따라서 실 ROS/L2/L3 검증 PASS 주장은 하지 않음.

## 4. 재현 명령
학생:
```bash
git clone --branch feat/velog-domain-knowledge-labs-20261123 --single-branch https://github.com/silverbjin/axia-robot-safety-student.git
cd axia-robot-safety-student/velog_domain_labs
export PYTHONPATH="$(find "$PWD/ros2_ws/src" -mindepth 1 -maxdepth 1 -type d | paste -sd: -)"
python3 -m unittest discover -s tests -p test_contracts.py -v
# 최초 TODO에서는 의도적 RED; 각 실습을 구현하면서 GREEN으로 전환
```

강사 (비공개 접근권한 필요):
```bash
git clone https://github.com/silverbjin/axia-robot-safety-instructor.git
cd axia-robot-safety-instructor/training/velog_domain_labs
export PYTHONPATH="$(find "$PWD/ros2_ws/src" -mindepth 1 -maxdepth 1 -type d | paste -sd: -)"
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

ROS2 선택 검증(실행 결과는 미확인):
```bash
source /opt/ros/jazzy/setup.bash
cd ros2_ws
colcon build --symlink-install
source install/setup.bash
ros2 run axia_command_chain_lab axia_command_chain_lab_demo
```

## 5. 발견·조치한 배포 오류
1. 신규 feat/release 브랜치에서는 `axia-instructor-sealed` Job이 runner 할당 전 거절되어, 기존 승인된 `release/p2-g06-cm-ttl-20261110`에 신규 독립 워크플로를 배치함. 기존 안전제어 코드는 미변경.
2. 첫 protected run #45085786260: Instructor GREEN이었으나 student checker 미배치로 전체 FAILURE. checker를 동일 릴리스 브랜치에 추가 후 최종 #45085852414 2 job SUCCESS.
3. `ament_python` console_scripts 경로 누락을 Review 중 발견하여 5개 패키지 모두에 `setup.cfg` 보강. `ros2 run` 실제 L1 검증은 별도.

## 6. 출고·안전 경계
- Student에 private 정답/hidden test 없음. Public CI에는 테스트 계약만 게시함.
- 별도 시험용 `release/velog-domain-knowledge-labs-20261123` branch는 보호 환경 미허용으로 인수하지 않았으며 최종 게이트로 사용하지 않음.
- 기존 `release/p2-g06-cm-ttl-20261110`에는 Velog CI 워크플로와 공개 checker만 추가됨; G07/S01~S05 Safety acceptance 결과를 신규 평가한 것이 아님.
- SW 정지는 인증된 물리 E-Stop이 아님.
