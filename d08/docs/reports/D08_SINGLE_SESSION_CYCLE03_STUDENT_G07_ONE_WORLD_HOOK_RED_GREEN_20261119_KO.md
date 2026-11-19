# D08 통합 Cycle 03 — 기존 G07 Owner의 ONE Gazebo World/Robot 연결 RED→GREEN

일자: 2026-11-19 KST. 공개 소스 독립 Student 저장소와 Public CI 분리를 유지. 실제 ROS/Gazebo 새로운 통합 주행은 **미실행**이며 이 사이클에서 PASS 선언하지 않는다.

## 오류 재현 RED
- Student 기준 실증 G07 Task04 코드는 `efff0fb8bf941de74572336d1988dfb0005e11f7`이고, G07 Owner 원샷 실행기는 그 코드를 그대로 재사용한다.
- D08 camera+person adapter는 공식 World에 적용할 수 있지만 원래 Student `scripts/p2_no_goal_smoke_ci.sh`에는 adapter를 호출하고 기존 `world:=`, `robot_sdf:=` 값을 교체하는 경로가 없어 **실제 단일 Gazebo 시연으로 연결되지 않았다**.
- RED: Student 테스트 `tools/test_d08_g07_single_session_hook.py` commit `df1b9ea853a980825d35d544414c04d7d53a8ac5`; 공개 CI [#44481613749](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44481613749) 결과 3 tests: **2 FAIL, 1 ERROR**. 누락된 옵션과 world/robot 계약에 대해 실패. 기존 CI L0/공식 소스는 독립 PASS.

## GREEN 최소 수정
- Student branch `feat/d08-g07-single-session-hook-20261119`, 공개 [Student PR #63](https://github.com/silverbjin/axia-robot-safety-student/pull/63), 코드 SHA **`8f5e262151f570e02d23646487504dafaa169b63`**.
- `block_B/day07/h01_runtime/scripts/p2_no_goal_smoke_ci.sh`의 **기존 단 한 번의** `setsid ros2 launch "$LAUNCH" "${LAUNCH_ARGS[@]}"` 전에만 다음을 수행:
  1. `AXIA_D08_G07_SINGLE_SESSION=1` 명시 opt-in, 원래 G07 승인된 CI/WSL2-Owner 이동 권한만 허용.
  2. Original `AXIA_P0_SIM_ONLY=1`, G07 physical/Owner startup parity 필요. CI 자동 Owner TTY 허위 승인 금지.
  3. 현재 실제 Student `git rev-parse HEAD`와 기대 SHA, D08 공개 adapter의 실제 Git SHA, 사람 DAE **SHA256 `49af0df3a319d1cb8ca2cebf02dbd00f625e5d5bec820bc5e109925b18b65c6e`** 모두 확인. 틀리면 Goal/런타임 시작 전에 차단.
  4. 기존 G07 Contact+Scene/10Hz Waffle overlay 소스를 D08의 **이미 검증된 Source Adapter**에 넘긴 뒤, 원래 `LAUNCH_ARGS`에서 **world / robot_sdf 각각 정확히 하나**만 교체. 두 번째 Gazebo 서버/새 Planner/자체 Twist/Goal 발행 없음.
- `AXIA_D08_G07_SINGLE_SESSION` 기본 0은 기존 Task04 경로를 바꾸지 않음; 기존 TTL/정지 원칙/TTY 요구 불변.

## 공개 CI 실제 GREEN
- Public workflow source `3895d58178c06a0a73613b81e0044b50f8089448`; [#44481908551](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44481908551).
- `g07-student-single-session-hook-l0`: **3 tests OK** + `bash -n` + `D08_G07_STUDENT_SINGLE_SESSION_HOOK_L0_PASS_NOT_GAZEBO`.
- `l0-human-proxy-red-green`: 기존 D08 총 **226 passed**.
- `g07-official-source-sdf-adapter-l1`: 실제 공식 Jazzy/G07 xacro SHA 고정 SOURCE job **SUCCESS**.
- 전체 Workflow SUCCESS. 아직 Gazebo/Goal/YOLO 동시 런타임 아님; 기존 개별 L2 성공은 변경된 통합 소스 L2 성공으로 승격하지 않음.

## REVIEW / 남은 최초 간극
- 기존 G07 Owner은 여전히 직접 TTY 승인을 필요로 하며 YOLO/D05를 안전제어의 원인으로 주장할 근거 없음.
- Student runtime에 D08 RGBD Gazebo→ROS image bridge 생명주기가 아직 없음; 현 단계는 SDF + launch arg 연결만.
- 다음 RED 우선: 동일 G07 소유의 한 World에서 브리지 실제 RGB/Depth 수신·원본 C++ YOLO 2 VALID/UNKNOWN·공식 3상 Path 관측 후, 원래 G07 안전 Goal을 전송. Scan **300ms**/CM·Guard 원래 TTL 불변. G07 Owner 이전 field 317.863ms >300ms를 안전 PASS로 은폐 금지.
- WSL2 Owner L3 NOT RUN, Student/Public main 미병합, instructor 정답 비공개, 실제 인증 E-Stop 해당 없음.

재현:
```bash
# 공개 CI 자체 수행: 정확한 Student SHA 다운로드 후
bash -n student/block_B/day07/h01_runtime/scripts/p2_no_goal_smoke_ci.sh
cd student/block_B/day07/h01_runtime
python3 -m unittest discover -s tools -p test_d08_g07_single_session_hook.py -v
# 실제 출력: Ran 3 tests ... OK
```
