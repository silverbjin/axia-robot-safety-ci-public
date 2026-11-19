# AXIA D08 Cycle 07 — 공식 CM TF 20ms 후보 실제 CLEAR 실패, 최초 수치 증거 누락 수정

2026-11-19 KST · 공개 Draft PR #189 · **완료 판정: 20ms 후보 REJECT / 전체 통합 Moving L2 HOLD.**

## 1. 재사용 기준과 가설
- G07 Task04 Student pin `0890f9717439c839a6fcb7c3d2a931ba10cbf528`, G07 official Collision Monitor의 기존 simple-TF `base_shift_correction=false` 사용.
- D08 카메라/사람 Mesh를 실제 G07 10Hz LiDAR World에 결합했을 때 STOP에서 발생한 최초 Guard internal CM age: 169.429ms(#44483897411), 186.991ms(#44485688526), 184.290ms(#44491362187). 정상 Guard TTL **150ms**, 출고 목표 CM **120ms**, Scan **300ms**를 유지.
- 가설: official CM `transform_tolerance=0.2s`를 simulation-only 0.02s로 줄이면 CM 입력 처리 지연을 축소할 가능성이 있음. G07 native 파라미터 실측, 로봇 실제 Moving L2로만 판정.

## 2. RED (정확한 실제 CI 증거)
- [#44504838398](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44504838398), public source `0f03e27a747ad2d65946a17c9d738da5ecf43051`, Student source `0890f9717439c839a6fcb7c3d2a931ba10cbf528`:
```text
AXIA_G07_CM_NATIVE_ACTIVE_PARAMETER_READBACK {..."transform_tolerance": 0.02, "base_shift_correction": false,... "status":"ACTIVE_CM_NATIVE_PARAMETER_READBACK_PASS"}
D08_G07_REAL_CM_TF_WAIT_READBACK_PASS 0.02S SHIFT_FALSE SOURCE_TIMEOUT_1.0 GUARD_150MS_UNCHANGED
AXIA_G07_OWNER_PREGOAL_PHYSICAL_L2_PASS_NO_GOAL front_m=2.034 side_m=0.671
AXIA_G07_PUBLIC_CI_MOVING_GOAL_BLOCKED RuntimeError:CI_MOVING_GOAL_TIMEOUT_CLEAR
AXIA_G07_TASK04_NATIVE_ONE_MOVING_RUNNER_RC=2 RVIZ_X11=1 GAZEBO_X11=1
```
- 실패 직전 원본 CM 측정 약 0.010~0.012m/s; CLEAR 승인에는 CM 및 final **>0.03m/s**가 필요. `CI_MOVING_GOAL_TIMEOUT_CLEAR`은 주행 성능 실패이고, Guard 첫 latch JSON은 **INCOMPLETE**였으므로 150ms TTL 위반으로 잘못 분류하지 않는다. 20ms 파라미터가 속도 미달의 단독 원인이라는 인과는 **미증명**.
- 추가 진단 결손: 기존 G07 `tools/p2_g07_ci_moving_goal.py`가 타임아웃 수치를 `SLOW`/`STOP`에서만 기록해, 최초 CLEAR에서 Supervisor/CM/Guard/Scan 동시 스냅샷 증거가 없는 것을 발견.

## 3. RED→GREEN 최소 변경
- Student `block_B/day07/h01_runtime/tools/test_d08_g07_clear_timeout_first_evidence.py`: 기존 bounded 수집 로직에 CLEAR를 포함해야 한다는 신규 단위 테스트. [RED #44510230443](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44510230443) `test_clear_in_existing_bounded_timeout_sampling ... FAIL`, `AssertionError: ... CLEAR ... not found`.
- Student `tools/p2_g07_ci_moving_goal.py` 단 한 줄 변경: `if label in ("CLEAR","SLOW","STOP") and now-last_sample>=.35:`. 기존 0.35s sampling, FIRST 3 + LAST 8 스냅샷, 원래 CLEAR 속도와 GOAL/Guard 조건 불변; 새로운 ROS 노드·Goal·센서 없음. GREEN Student SHA `d94a0f7090c976d4b0c9e57bb449581e96243bf1`.
- Public `.github/workflows/d08-main-no-goal-real-gazebo-l2.yml`: Student 정확한 SHA 핀, 신규 테스트 `2/2` 실행, `clear_timeout_trace.json`만 compact artifact allowlist에 추가.
- 20ms 후보는 **새 주행 CI에서 꺼두고**, 기존 `AXIA_G07_TASK02_SIMPLE_TF_CANDIDATE=1` + `transform_tolerance=0.2s`로 복귀. 20ms 코드가 존재하더라도 CI-only opt-in default OFF이며 Owner L3 release 불허.

## 4. 검증 결과와 범위
- 공개 [#44510477082](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44510477082): D08 **240 passed**, Student 기존 4+4 + 신규 **2/2 OK**, 공식 Jazzy/G07 Xacro L1 PASS. Native Contact 빌드 중 Ubuntu APT mirror `File has unexpected size`, exit100; 실질 Moving L2는 이 Run에서 **NOT RUN**.
- 후속 실제 baseline comparator는 Cycle08 [#44511494053](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44511494053)에서 수행. 기존 0.2s로 CLEAR/SLOW PASS, STOP 최초 Guard TTL 초과 (세부 숫자 Cycle08).
- **20ms RED 가설 폐기.** 단위 GREEN이나 파라미터 읽기 성공만으로 실제 주행 안전 인수/CM 120ms를 주장하지 않는다.

## 5. 리뷰·안전·브랜치
- ROS2 Jazzy, Gazebo Harmonic, 단일 물리 Waffle/World, 공식 Nav2, Safety Supervisor+CM+Guard 재사용; Guard TTL 150ms, source_timeout 1.0, stop_pub_timeout 5.0, Scan 300ms 불변.
- PUBLIC Student Draft PR #63, PUBLIC CI Draft PR #189, main 미병합. D04 C++ YOLO + D05 live ROI는 아직 실제 G07 Moving 동일 세션에서 검증하지 않았다. Owner WSL2 L3 NOT RUN. SW stop은 인증된 E-Stop 아님.
- 검증 등급: **L0 GREEN / 공식 Source L1 GREEN / TF20ms 실제 Moving L2 FAIL / 단일 D04~D07 E2E HOLD**.
