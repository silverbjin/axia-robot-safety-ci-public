# AXIA DAY02 — 성공/실패 G07 전체 소스 학생 배포 및 실제 Jazzy colcon 빌드 보고서

**2026-11-26 KST**  
**결론:** `DUAL_FULL_SOURCE_PUBLIC_RELEASE_L0_PASS`, `ROS_JAZZY_COLCON_L1_ACCEPTED_4OF4_PASS`, `ROS_JAZZY_COLCON_L1_FAILED_4OF4_PASS`, `NATIVE_MOVING_L2_NOT_RERUN`, `OWNER_WSL2_L3_NOT_RERUN`, `MAIN_NOT_MERGED`.

## 1. 두 전체 소스 공개 배포

Student Repo: [silverbjin/axia-robot-safety-student](https://github.com/silverbjin/axia-robot-safety-student/tree/release/day02-dual-mvp-full-source-build-20261126/special_lecture/day02_mvp_sources)

**빌드 및 CI 검증된 Student HEAD:** `96be43164fab3f15025edd59279bcfd50b6232cd`, Student [PR #120](https://github.com/silverbjin/axia-robot-safety-student/pull/120) Draft.

| 분류 | 실제 학생 저장소 경로 | 검증된 원본 소스 | 전체 runtime Git Tree | 파일 |
|---|---|---|---|---:|
| 완료된 G07 | `special_lecture/day02_mvp_sources/accepted/runtime/` | `f7edb2d126502eeeed58ae014adadc7a2096d41b` | `1ad1d424358345420b8bfc67a6a7ca44d634a974` | 186 |
| 실패한 G07 | `special_lecture/day02_mvp_sources/failed/runtime/` | `a04f9a7da8d54bbd9f944d05388792cb706adf28` | `0d44f39c8f5927d21411c33e7a793ca1a3f6f368` | 187 |

**직접 파일:** submodule·symlink가 아닌 Git tree object를 해당 디렉터리로 포함하므로 한 번의 Git clone으로 양쪽 실제 원본을 얻습니다. `block_B/C/D`의 현재 `main` 소스는 전혀 변경하지 않습니다. 성공/실패 원본의 ROS 2 `ros2_ws/src` 자체 SHA는 `767c3d10187280303f5226a90ede205eb0059033`로 동일합니다.

**정확한 파일 수준 차이 3개:**
- `tools/p2_g07_ordered_shutdown.py` (내용 차이)
- `tools/p2_g07_scan_wall_pregoal.py` (내용 차이)
- `tools/test_g07_localization_warm_shutdown_20261121.py` (실패본에만 존재)

두 전체 소스를 비교할 때 ROS 패키지 소스가 동일하다는 사실 및 원래 Public CI 환경·명령의 차이를 포함해 분석해야 합니다. 위 3개 파일 차이를 FastDDS 원인으로 단정하지 않습니다.

## 2. ROS 2 패키지와 빌드 실습

양쪽 스냅샷 각각 4개 **ament_python** 패키지:
`axia_fault_injector`, `axia_safety_bringup`, `axia_safety_supervisor`, `axia_scenario_verifier`.

학생용 명령:

```bash
git clone --single-branch --branch release/day02-dual-mvp-full-source-build-20261126 \
  https://github.com/silverbjin/axia-robot-safety-student.git "$HOME/axia-day02-full-sources"
cd "$HOME/axia-day02-full-sources"
git checkout --detach 96be43164fab3f15025edd59279bcfd50b6232cd
bash special_lecture/day02_mvp_sources/scripts/build_dual_mvp.sh --verify
bash special_lecture/day02_mvp_sources/scripts/build_dual_mvp.sh --doctor
bash special_lecture/day02_mvp_sources/scripts/build_dual_mvp.sh --both \
  --out "$HOME/axia-day02-colcon-builds"
```

빌드 도구는 원본을 변경하지 않고 `accepted/runtime`과 `failed/runtime`을 각 출력 작업공간에 복사합니다. 그 복사본에서 `python3 -m compileall`과 실제 `colcon build`를 실행하고, 4개 ROS 패키지의 `ros2 pkg prefix`가 등록됐는지 검사합니다. 실제 출력은 버전별 `logs/colcon_build.log`와 `BUILD_RESULT.json`으로 남습니다.

## 3. 실제 검증: 공개 GitHub Actions

**최종:** [Public Run #45801859735](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/45801859735), workflow commit `fb6b910afb0571999cf91c3ade595f770af004ed`, Student build source HEAD `96be43164fab3f15025edd59279bcfd50b6232cd`.

**L0 job `dual-source-l0-identity-and-red-green`: SUCCESS**
- 사전 RED 테스트 commit `17c0619be1601981a8d24a39d9f4f23cbc936f1d`: 필수 Manifest와 두 소스가 없어서 테스트 실패, 로그에서 의도된 RED 확인.
- GREEN: **Ran 7 tests / OK**; 전체 두 runtime Git trees, 4개 package.xml/setup.py, 정확한 historical moving verdict, 학생 소스 내 비공개 payload 차단.
- 임시 CI 작업 복사본에서 실패 소스 파일을 임의 변경 → `WORKTREE_MODIFIED:failed`로 실패. 원상 복구 → 검증 PASS.
- `AXIA_DAY02_DUAL_SOURCE_PREIMPLEMENTATION_RED_CONFIRMED`, `AXIA_DAY02_DUAL_SOURCE_L0_GREEN_EXACT_TREES_FOUR_PACKAGES`, `AXIA_DAY02_DUAL_SOURCE_TAMPER_REGRESSION_PASS`.

**L1 job `dual-source-l1-real-jazzy-colcon`: SUCCESS**
- 실제 `ros:jazzy-ros-base-noble` 컨테이너(24.04 + ROS Jazzy)에서 colcon toolchain 설치.
- `--doctor`: `AXIA_DAY02_JAZZY_COLCON_PREFLIGHT_PASS`.
- 성공본: `python3 -m compileall` PASS, 실제 `colcon build` **Summary: 4 packages finished [1.78s]**, 4 ROS 패키지 설치·prefix 확인 PASS.
- 실패본: `python3 -m compileall` PASS, 실제 `colcon build` **Summary: 4 packages finished [1.72s]**, 4 ROS 패키지 설치·prefix 확인 PASS.
- `AXIA_DAY02_REAL_DUAL_ROS_BUILD_L1_PASS_NO_GAZEBO_NO_GOAL`.
- 업로드된 빌드 로그/JSON 아티팩트: **ID `15106984518`**, `axia-day02-full-source-jazzy-colcon-build-logs`, Public Run 페이지에서 다운로드 가능.

**검증 수준 경계:** 이는 실제 Jazzy에서 **ROS 2 Python 네 패키지의 build/install/L1 확인**입니다. Gazebo/Goal/Moving, Nav2 lifecycle 현장 실행은 **NOT_RUN**입니다. C++ 컴파일을 수행했다고 보고하지 않습니다.

## 4. RED→GREEN·디버깅 이력 (첫 실패별 원인과 조치)

1. `1317ff7…` 첫 워크플로: GitHub Actions YAML 단계 이름의 이스케이프되지 않은 콜론으로 워크플로 자체 시작 불가 → `ce8639f…` 수정.
2. Public Run #45800966428: 신규 Manifest 테스트의 잘못된 필드 접근으로 L0 1건 실패 (`KeyError: certified_estop`) → Student `f6be416…`에서 정확한 중첩 구조로 수정, 이후 L0 7/7 PASS.
3. Public Run #45801069167: Jazzy 컨테이너 APT에서 `python3-ament-package` 이름을 찾지 못해 중단 → Public `5dd0dd6…`에서 이미 구성된 Jazzy에 맞는 패키지만 설치하도록 수정.
4. Public Run #45801406348: ROS 환경 `source` 전에 `ros2` 명령을 검사해 `AXIA_DAY02_BUILD_HOLD=MISSING_ros2` → Student `96be431…`에서 `source /opt/ros/jazzy/setup.bash` 이후 검증하도록 조정.
5. Public Run **#45801859735 최종 GREEN**: L0 7/7, 실제 Jazzy colcon 4+4 패키지 PASS, 로그 업로드.

기존 G07 Safety Supervisor/Guard/Nav2/Collision Monitor/TTL은 변경하지 않았습니다. 학생 소스 추가와 빌드기·교육 테스트만 변경했습니다.

## 5. 과거 실제 로봇 인수와 혼동 금지

| 분류 | 기존 증거 | 이번 신규 검증 |
|---|---|---|
| 완료본 Native Moving Gazebo | [#44965035965](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44965035965) **2/2 PASS** | **NO NEW L2** |
| 실패본 Native Moving Gazebo | [#44914827138](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44914827138) **0/2 FAIL** | **NO NEW L2** |
| 완료본 Owner WSL2 | 2026-11-22 원본 RAW 숫자·Lifecycle **PASS_SCOPED** | **NO NEW L3** |
| 실패본 Owner WSL2 | NOT_RUN | NOT_RUN |
| 신규 학생 릴리스 | 원본 SHA 동일성 L0 PASS | 실제 Jazzy Python ROS packages L1 **4+4 PASS** |

기존 Owner 자동 `HOLD_RAW_REVIEW_AND_VISUAL_PENDING`은 별도 사후 `PASS_SCOPED`와 함께 보존. FastDDS/RMW root cause `UNDETERMINED`. 소프트웨어 STOP은 인증된 E-Stop이 아닙니다. 학생 빌드가 성공하더라도 실패본의 0/2 인수 결과를 성공으로 바꾸지 않습니다.

## 6. 배포·브랜치 정리

- Student `release/day02-dual-mvp-full-source-build-20261126`, 소스/실습/7 L0 계약/빌드기, [Draft PR #120](https://github.com/silverbjin/axia-robot-safety-student/pull/120).
- Public `ci/day02-dual-full-source-colcon-20261126`, 실제 컨테이너 L1 및 아티팩트, [Draft PR #237](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/237).
- **main 브랜치 병합은 이번 요청에서 별도 승인 없으므로 미실행**. 본 배포 브랜치는 이미 학생들이 clone할 수 있고 CI 검증된 Student HEAD는 `96be43164fab3f15025edd59279bcfd50b6232cd`입니다.
- 실제 강사 WSL2에서의 신규 \`colcon build\` 현장 실행은 **NOT_RUN**. Ubuntu 24.04 Jazzy CI 컨테이너의 검증 결과에 한정합니다.
