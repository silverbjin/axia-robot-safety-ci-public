# AXIA D08 Owner WSLg Scan/CM/GPU 실패 원인 → RED/GREEN → 실제 Gazebo L2 인수 보고서 (2026-11-18)

기준: silverbjin/axia-robot-safety-ci-public PR #166, branch feat/d08-unified-sensor-cm-path-20261118. NO_GOAL 교육 시연만 해당하며 Goal/로봇 cmd_vel과 인증 E-Stop은 범위 밖이다.

## 1. 현장 증거와 기존 검증의 공백

강사 원본 run_20261118T095036Z_df6e7i.zip: 내부 SHA256SUMS 12/12 PASS. 실행 구버전 SHA a4dbb714f74d31ac410b1504f2b5087df3a4ec64. 실제 Gazebo Waffle/RGBD/AMCL 초기 pose 및 TF가 관찰되었으나 Path 전 D08_NO_GOAL_RX_NOT_STABLE:SCAN_INSUFFICIENT_REAL_CALLBACKS로 차단. GL renderer D3D12 Intel Iris Xe. GPU 자체가 오류의 확정 원인이라는 증거는 없음. 종료 RViz -6, Gazebo -11은 최초 실패 후 별도 정리 오류.

이전 #44269396804는 Gazebo/공식 Nav2 Path PASS였으나 Owner 첫 Callback 지연과 동일한 조건은 재현하지 못했다.

## 2. 실제 Gazebo RED에서 원인을 확정

[실제 RED #44290635539](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44290635539): Gazebo의 진짜 Scan/Odom/Clock을 수신하는 Python Executor만 의도적으로 650ms 멈춰 최초 위반을 재현. 가짜 ROS 메시지 발행 없음.

원본 [artifact #14421376337](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44290635539/artifacts/14421376337)의 amcl_receive_timing.json: 실제 Scan callback **186개** / age **68.924ms**, Odom 200개 / age 23.321ms, Clock 200개 / age 2.969ms. 최초 Scan receive gap 669.078ms, Odom 675.128ms. 실제 센서가 6개 미만인 것은 아니었음.

**최초 결함 A:** assess_pre_goal_receive_recovery()는 list/tuple만 허용하지만 실제 ROS receive_history는 collections.deque. 그래서 Scan 186개가 있어도 SCAN_INSUFFICIENT_REAL_CALLBACKS로 잘못 분류된다.

**연쇄 결함 B:** /clock 약 333Hz를 deque 최대 200개에 모두 기록하여 보존 구간은 597ms. 기존 1초 연속 복구 판정 조건을 구조적으로 충족할 수 없었다.

**별도 CM 준비 시점:** [Run #44271106709](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44271106709)의 실제 공식 Path 이후 CM 활성화 전 단 한 번 Lifecycle state를 읽어 D08_OFFICIAL_CM_NOT_ACTIVE로 차단했다. 활성화 로그와 native service state의 시간 차이가 확인되었으며 최종 종료 메시지는 최초 원인이 아니다.

## 3. 최소 수정과 안전 경계 보존

- d08/harness/d08_amcl_initial_pose.py: 실제 deque 수신 버퍼를 인정하고, /clock 진짜 콜백 시각을 최소 20ms 간격으로 관찰 저장해 1초 회복 기간을 확보. 첫 Scan/Odom/Clock gap 및 실수신 수, host receive timestamp, source ROS timestamp, age, clock-based observed RTF는 진단용 별도 보존. 실패 시에도 amcl_receive_timing.json 기록.
- d08/harness/d08_nav2_path_preflight.py: AMCL 실제 observer의 성공과 실패 모두 관찰 원본 아카이브 연결.
- d08/harness/d08_same_world_replan.py: 실제 /collision_monitor/get_state 응답이 **id=3 + label=active**가 될 때까지 최대 12초 bounded 재조회. 다른 state를 active로 승인하지 않고 기간 초과 시 BLOCKED. 실제 observation_sources/scan.topic 파라미터 검증 유지.
- d08/scripts/d08_owner_no_goal_bootstrap.sh: 공식 WSLg GPU selector MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA를 사용하고 실제 OpenGL D3D12 (NVIDIA...) Renderer인지 조기 검증. llvmpipe/Intel 잔류 시 무거운 다운로드와 Gazebo보다 먼저 HOLD. 단, NVIDIA 선택 자체는 RTF PASS 아님.
- .github/workflows/d08-main-no-goal-real-gazebo-l2.yml: PR #166 실제 Jazzy/Gazebo/Nav2 job 강제 실행; ROS Subscriber 650ms 정지 후 실제 메시지 1초 연속 회복, 최종 공식 Nav2 3 Path 및 기존 RGBD/YOLO/D05 연결 확인. Skip이면 인수 불가.
- d08/tests/test_d08_owner_ci_field_boundaries.py: sparse 입력, deque 실제 타입, 고속 Clock ring 경계, CM inactive/active, GPU 확인, 주입 L2 회귀를 추가.

불변 조건: 가짜 Scan/Odom/Clock/TF 발행 없음. Goal과 제어 미발행. 공식 Nav2/CM/AMCL 소스 수정 없음. 기존 Scan/Odom 500ms limit 및 1초 복구 검사 유지. Safety Supervisor·Guard TTL 수정 없음.

## 4. RED → GREEN → REFACTOR → REVIEW → COMMIT

- RED 로컬: 새 helper 미구현 ImportError; 실제 deque >=6건 전달 시에도 SCAN_INSUFFICIENT_REAL_CALLBACKS; 고빈도 Clock 관찰 함수 미구현. 두 오류를 별도 재현.
- RED 실제 Gazebo: #44290635539에서 실제 186 Scan callback에도 잘못된 INSUFFICIENT 판정이 발생해 원본 증거 확보.
- 개발 중 실패도 보존: YAML 중복 env 때문에 #44290493299가 워크플로 구문에서 실패. #285bd628f14344adda48e86eaaa16243e06ecfa6에서 env 한 곳으로 통합. 이것은 ROS/Gazebo 런타임 실패가 아님.
- GREEN 로컬 관련 회귀 **31 passed**; 확장 관련 회귀 **43 passed**.
- 실제 GREEN 실행 소스 SHA **e48b7124bd8e01bdc9f80631f65a69dbbc6742c1**.
- 검토: 외부 공식 Nav2/AMCL을 fork하지 않고 read-only 진단과 bound readiness만 추가. 첫 위반을 기록하고 미복구·CM 비활성은 여전히 Fail Closed.

## 5. 공개 CI 완료 증거

[GitHub Actions Run #44291671984](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44291671984), exact SHA e48b7124bd8e01bdc9f80631f65a69dbbc6742c1, completed **SUCCESS**, 4개 job 전부 SUCCESS:

1. l0-human-proxy-red-green: **112 passed in 0.47s**.
2. gazebo-official-nav2-oneworld: 실제 650ms 수신 지연 후 1초 연속 복구, AMCL/TF2, 공식 Path 14 points / 0.4m, GZ 장애물 전·침입·복원 3 Path **PASS**.
3. gazebo-contact-positive-once: 실제 Gazebo/RGBD/LiDAR 및 물리 시험 **PASS**.
4. real-gazebo-rgb-pinned-upstream-yolo-ros: 실제 같은 월드 YOLO/D05 거리 VALID far **0.704022m**, VALID stop **0.534589m**, UNKNOWN NO_PERSON_CLASS_IN_ACTUAL_YOLO, Nav2 3 Path **PASS**.

실제 Nav2 세션 원본 첫 위반 Scan **664.354ms**, Odom **665.801ms**, Clock **652.011ms**. 이후 회복: Scan 16 callback / span 1.135181s / max gap **122.475ms**; Odom 39 / 1.242982s / **37.392ms**; Clock 60 / 1.251592s / **22.937ms**. 최초 위반을 삭제하지 않고 모두 이력으로 보존했다.

[공식 Nav2 L2 artifact #14422231771](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44291671984/artifacts/14422231771) ZIP SHA256: 7c88ecb692ff2fa33df105dbaeda44fddd8f472ccb36ed3a7545354d7146ec46, 내부 SHA256SUMS **12/12 PASS**. 관측 Clock RTF **1.002348은 공개 CI** 실측이며 Owner WSLg 성능 보증 아님. YOLO same-world artifact #14422381932.

## 6. 강사 WSL2 한 번 실행 및 출고 한계

아래 고정 SHA로만 실행한다. CI 소스가 아니라 변경된 문서 HEAD나 main을 선택하지 않는다.

~~~bash
(
  set -Eeuo pipefail
  SHA='e48b7124bd8e01bdc9f80631f65a69dbbc6742c1'
  SCRIPT="$(mktemp --suffix=.sh)"
  trap 'rm -f -- "$SCRIPT"' EXIT
  curl -fLsS --retry 3 --max-time 90 "https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public/$SHA/d08/scripts/d08_owner_no_goal_bootstrap.sh" -o "$SCRIPT"
  bash -n "$SCRIPT"
  export AXIA_D08_PUBLIC_SHA="$SHA"
  bash "$SCRIPT" --self-check
  bash "$SCRIPT" --run
)
~~~

기대 로그(Owner 미실행): D08_OWNER_WSLG_NVIDIA_D3D12_VERIFIED, D08_OWNER_EXACT_SOURCE_SHA_VERIFIED, D08_AMCL_REAL_FIRST_POSE_PLUS_LIVE_TF_READY, D08_OFFICIAL_SAME_WORLD_THREE_PHASE_PATHS_L2_PASS_NO_GOAL, D08_OWNER_GUI_REPLAN_LOOP_READY. NVIDIA renderer를 실제 선택하지 못하면 D08_OWNER_WSLG_NVIDIA_D3D12_NOT_AVAILABLE에서 먼저 HOLD. 현장 수신 rate가 여전히 한도 위반이면 진단 amcl_receive_timing.json을 기반으로 새 CI 회귀를 먼저 편입한다.

**명시적 미검증:** Owner WSL2/WSLg 실제 NVIDIA/Gazebo/RViz GUI Pixel/RTF, Ctrl+C 정상 종료, Moving Goal 안전 CM120/Guard150/Scan300 TTL은 이번 NO_GOAL CI로 증명되지 않음. Publisher RMW gap도 직접 측정하지 못함. 기 인증된 E-Stop 아님. main 별도 승인 전 병합 금지.

최종: D08_PUBLIC_L0=PASS; D08_GAZEBO_NAV2_L2=PASS_SCOPED; D08_PUBLIC_SAME_WORLD_YOLO_D05_L2=PASS_SCOPED; D08_OWNER_WSLG_L3=HOLD; D08_RELEASE=READY_FOR_OWNER_ONLY; AXIA_MVP_DEMO_ACCEPTED=HOLD; CERTIFIED_ESTOP=false; MAIN_MERGED=false.
