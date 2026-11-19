# D08 Cycle 05 — G07 기존 주행 실행기에 D04·D05·D07 읽기 전용 단계 연결 (RED→GREEN)

2026-11-19 KST · **L0/공식 Source L1만 GREEN, 실제 YOLO+Moving L2/HW는 HOLD.**

## 처음 관찰한 실패
- Public CI [#44489284294](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44489284294) 신규 Student source 계약 **RED** `test_readonly_d04_d05_d07_phase_must_precede_any_moving_goal` → `AssertionError: AXIA_D08_G07_READONLY_STAGE not found`. 기존 D08 L0와 공식 World/SDF Source L1은 성공, 별개 Moving L2는 intentionally aborted.
- Student 초기 RED SHA `eabdd9d9646e6a8112de9d0afa35f070047dea6b`; G07 original G07 Runner는 Goal 이전에 D08 read-only phase와 image bridge를 호출하지 않았다.

## 최소 수정 (안전·기존 런타임 보존)
- Student Draft [PR #63](https://github.com/silverbjin/axia-robot-safety-student/pull/63), branch `feat/d08-g07-single-session-hook-20261119`, code SHA `bae5b4d02b7dcd09c54b523b015a24b3428012ac`.
- `block_B/day07/h01_runtime/scripts/p2_no_goal_smoke_ci.sh`는 원래 한 번의 Gazebo/Official Nav2 `ros2 launch`를 유지한다. **기존 소유 G07 Moving Goal/TTY 승인 전에만** `AXIA_D08_G07_READONLY_STAGE=1` opt-in에서 image bridge와 read-only Python을 시작한다. default OFF, 옵트인 실패 시 Goal 발행 전 종료. G07 native pregoal fixture는 원래 순서대로 그 다음에 실행하므로 D08 물리 사람 이동 후 위치를 재정비한다.
- `D08_IMAGE_BRIDGE_PID`로 image bridge 수명/종료 범위를 지정. 별도 Gazebo server, Planner, NavigateToPose 발행, /cmd_vel publisher, synthetic Scan 없음.
- Public `d08/scripts/d08_g07_readonly_pregoal.py`: **이미 구현·검증된** `d08_live_person_range_session.run_session`의 실제 2 VALID+1 UNKNOWN YOLO/RGB-D ROI와 `d08_same_world_replan.run`의 공식 Nav2 `ComputePathToPose` 3상 경로 관찰을 동일 프로세스의 ROS_DOMAIN_ID/GZ_PARTITION으로 순차 재사용. 두 실제 verdict가 모두 PASS일 때에만 read-only phase PASS; Goal 권한 없음.
- Public `d08/tests/test_d08_g07_readonly_pregoal.py`: 누락/비정상 YOLO ROI, 잘못된 공식 path, 감지 단계의 Goal/속도 발행 주장, 부정확한 source SHA는 L0에서 거절.
- Student SHA check는 pregoal fixture 이후 선언되는 `EXPECTED_CI_SHA`가 아닌 이미 고정한 `D08_STUDENT_SHA` 사용 (unbound variable 회귀 예방).

## 실제 GREEN 및 검증 수준
- Public workflow SHA `4c2b0fb19510dadde23578e0f9c263f4ef3653fa`, [#44489990479](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44489990479): `l0-human-proxy-red-green` SUCCESS, independent Student pinned `g07-student-single-session-hook-l0` **4/4 SUCCESS**, `g07-official-source-sdf-adapter-l1` SUCCESS.
- 성공한 실행 출력: `test_readonly_d04_d05_d07_phase_must_precede_any_moving_goal ... ok`, `Ran 4 tests ... OK`, `D08_G07_STUDENT_SINGLE_SESSION_HOOK_L0_PASS_NOT_GAZEBO`.
- 독립 기존 D08 NO_GOAL Gazebo L2/#44485688670은 완료된 별개 성공 증거로 보존, **신규 single-session Moving L2 PASS에 합산하지 않는다**.
- **실제 C++ YOLO engine launch와 registered RGB-D/D05 2 VALID/UNKNOWN을 기존 G07 Owner CI 컨테이너에 연결한 L2는 미실행**; 현재 새 read-only stage는 default OFF이며, 기존 G07 Moving L2는 Guard CM age 186.991ms > 150ms로 HOLD.
- G07 CI strict Source CM 120ms, Guard 150ms, Scan 300ms, existing TTY Goal admission 불변. SW Stop ≠ 인증된 E-Stop.

## 다음 병목, 불필요한 개발 확장 금지
1. 기존 G07 STOP 시 최초 CM/Guard 동시 수신 중단 경계 먼저 계측: Guard 186.991ms, independent observer 181.809ms, 편차 5.183ms. Guard만의 RMW 지연인지 CM 자체 publish/shared host 지연인지 현재 미확정. 기존 Gazebo+Task04 event logs 범위로 분석, fail-close 유지. 동일 현장 재시도 금지.
2. G07 Moving Gazebo L2 완전 GREEN 시, 동일 세션에서 별도 C++ `yolo_ros` 기존 build/runtime과 D08 등록 RGB-D bridge read-only 연결, Goal 이전 D04→D05→D07 source timeline 검증. 이전 NO_GOAL 테스트 반복 금지.
3. 기존 시연의 정지와 경로 재계획은 동일 World의 별도 관측 계약; YOLO가 CM을 직접 정지시킨다는 표현 금지.
4. 공개 CI 실제 Gazebo/YOLO/CM/Guard 전계층 L2 확보 전 **Owner WSL2 원샷 배포 불가**. 사용자 WSL2 L3 NOT_RUN; Student/main/Public/main 병합 금지.

## 기존 코드·인증 경계
Public source `feat/d08-d04-d07-single-session-20261119`, Student source `feat/d08-g07-single-session-hook-20261119`, 공개 Draft PR #189, Student Draft PR #63. 강사용 정답이 아닌 read-only 연동 Source만 공개. 검증: **L0 PASS / 공식 Source L1 PASS / 통합 Moving L2 HOLD / WSL2 L3 NOT RUN**.
