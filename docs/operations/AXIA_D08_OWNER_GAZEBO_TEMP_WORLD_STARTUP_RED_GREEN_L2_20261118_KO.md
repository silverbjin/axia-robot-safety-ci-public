# AXIA D08 — Owner Gazebo 임시 World SDF 시작 실패: RED→GREEN→실제 L2 출고 보고서

**작성:** 2026-11-18 KST. **저장소:** silverbjin/axia-robot-safety-ci-public, PR #166, feat/d08-unified-sensor-cm-path-20261118. **출고 검증 소스 SHA:** 342c6355b27af5b8b11a79b7e345820be18a581f. **범위:** D08 Jazzy/Harmonic NO_GOAL 교육 시연, official Nav2/Waffle 재사용. 로봇 이동 명령과 인증 E-Stop은 범위 밖.

## 1. Owner 원본 최초 오류와 원인 분석

- 제출 증거: run_20261118T122924Z_KA2KHd.diagnostics.zip, 원본 SHA256 b3269045dfd3becf463c426fc456305addba7defe4b828f82f34652f049c967a, 외부 해시 및 내부 15/15 PASS. 원본 소스 SHA 81487f00ff9c20f2bc4e503548d43803297acc85.
- 정확한 최초 치명 오류: Gazebo 서버 gz sim -r -s /tmp/nav2_rlmwzhmj.sdf 가 "Unable to find or download file" 출력 후 exit **255**. 해당 서버 종료 로그가 xacro-1의 clean completion 로그보다 먼저 출력됨.
- 하류 결과: 실제 RGB=0, Depth=0, Contact topic 미발견, Costmap odom TF 부재. 마지막 G07_NATIVE_CONTACT_SENSOR_TOPIC_NOT_PUBLISHED는 **원인 아닌 후속 증상**임.
- 생성된 D08 actual_world.sdf XML과 SceneBroadcaster 1개, NVIDIA D3D12 렌더러 준비는 별도로 관찰되었다. 따라서 이번 최초 실패를 SceneBroadcaster 누락이나 GPU 선택 실패로 분류하면 안 됨.
- 실제 Owner 실패 순간 /tmp/nav2_*.sdf의 stat/inode/크기는 원본에 없음. 따라서 Xacro/Gazebo 동시 실행의 경쟁은 공식 코드와 로그가 강하게 뒷받침하는 가설이며, 정확한 OS scheduling race 자체의 직접 측정은 **미검증**.
- 공식 Jazzy tb3_simulation_launch.py는 임시 SDF에 Xacro ExecuteProcess 출력과 gz sim 서버를 별도 액션으로 추가한다. use_simulator:=False를 지원하며, 이 옵션에서도 공식 Waffle Spawn·Nav2 bringup·RViz 동작은 유지한다.
- 참고: https://api.nav2.org/nav2-jazzy/html/tb3__simulation__launch_8py_source.html , https://github.com/ros-navigation/navigation2/issues/5350

## 2. RED — 테스트부터 도입

**L0 재현:** 2026-11-18 [Public Run #44308188790](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44308188790), **4 failed, 124 passed**. 테스트는 파일 생성 지연 중 이전 Gazebo 경로가 존재하지 않는 SDF를 접근하는 실패 조건을 deterministic하게 만들고, 공식 Nav2가 이전 방식대로 내부 시뮬레이터를 실행한다는 계약 위반을 확인하였다.

**실제 Gazebo 네이티브 재현:** [Public Run #44310101993](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44310101993)의 gazebo-official-nav2-oneworld job에서 ROS Jazzy + 실제 Gazebo Harmonic의 gz sim -r -s 를 생성되지 않은 임시 SDF에 실행. stderr "Unable to find or download file", **exit 255**를 확인하고 기대 RED 증거로 별도 artifact 기록. 출력 D08_REAL_GAZEBO_TEMPFILE_RED_REPRODUCED exit=255 NOT_SAFETY_PASS. 이는 동일한 **missing-file 실패 서명 재현**이고 실제 Nav2 스케줄링 race 발생을 재현했다고 과장하지 않는다.

RED 실패를 숨기기 위해 기존 Scan 500ms, Clock, Guard 또는 CM 안전 TTL을 완화하지 않았으며 가짜 ROS Scan/Odom/TF를 발행하지 않았다.

## 3. GREEN — 최소 수정과 프로세스 소유권

1. d08/harness/d08_world_startup.py 신규: 완성된 D08 actual_world.sdf 파일의 regular/nonempty/단일 default world/실제 person fixture XML을 검사, 파일 크기와 SHA256 고정. 서버 시작 후 진짜 /world/default/scene/info 서비스를 요청해 물리 장애물 모델을 확인. 준비가 되기 전에 Gazebo가 죽으면 D08_GAZEBO_SERVER_EXIT_BEFORE_WORLD_READY:exit_code=N을 첫 오류로 즉시 반환. 최초 진단 gazebo_startup.json 기록.
2. d08/harness/d08_one_world_official_nav2_launch.py 수정: 공식 Nav2 tb3_simulation_launch.py에 use_simulator:=False 전달. **Nav2의 임시 Xacro 생성은 그대로 일어날 수 있으나** Gazebo 서버는 더 이상 이 임시 파일을 읽지 않는다. 공식 Waffle Spawn, robot_state_publisher, Nav2 lifecycle, CM, AMCL, Costmap, Planner, RViz 재사용.
3. d08/scripts/d08_public_gazebo_l2.py 수정: 생성 actual_world.sdf 검증 → D08 소유 단일 gz sim -r -s 서버 시작 → 진짜 native scene/world 서비스 READY 확인 → 공식 Nav2 연결 순서를 확정. Owner 모드의 Gazebo GUI는 이미 실행된 서버에 gz sim -g 클라이언트로 연결. CI에서는 동일한 서버에 하나의 Xvfb GUI 클라이언트를 붙이고 8회 경로 계산. 서버와 Nav2/GUI 중 하나라도 종료되면 fail-closed.
4. d08/tests/test_d08_owner_temp_world_startup_order.py 신규: 실제 Owner 처음 실패 경계, Xacro 지연된 파일 접근, 공식 Nav2 독립 서버 차단, 올바르지 않은 SDF, 조기 Gazebo 사망, 경량 증거 보존을 검사.
5. .github/workflows/d08-main-no-goal-real-gazebo-l2.yml 수정: 실제 Gazebo missing-SDF RED 증거를 생성한 뒤 같은 소스의 L2에서 서버 선기동 및 Scene 서비스, 공식 AMCL/TF/Nav2, 8회 경로, 기존 센서 안전 간격을 확인한다.
6. d08/scripts/d08_compact_evidence.py 수정: 실패 시 gazebo_startup.json, bounded gazebo_server_error_context.txt를 Owner ZIP에 포함. ONNX Runtime NuGet/모델/소스 checkout/빌드와 다른 대용량 파일 제외. SHA256SUMS와 원본 실패 경계는 보존하고 원본 실행 폴더는 자동 삭제하지 않는다.

**프로세스 소유:** D08 생성 World를 여는 Gazebo 서버 정확히 하나; 공식 Nav2는 use_simulator False; 공식 Waffle Spawn은 기존 Nav2 경로; Owner GUI는 GUI-only client; 토픽/제어/플래너 fork 및 임의 Safety 패치는 없다.

## 4. 실제 공개 CI GREEN 및 검증된 결과

[Public Actions Run #44310101993](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44310101993) / exact code SHA **342c6355b27af5b8b11a79b7e345820be18a581f** / completed **SUCCESS** / 전체 4 jobs **SUCCESS**:

- l0-human-proxy-red-green: **129 passed in 0.85s**.
- gazebo-official-nav2-oneworld: 실제 RED missing SDF exit255 재현 후, 변경된 동일 runner 실제 Gazebo server Native World **READY in 2.32s**, 실제 Waffle/person Scene와 GUI client, AMCL map→base_link TF, 공식 Path 3단계 및 **8회 반복 PASS**.
- gazebo-contact-positive-once: 기존 실제 Gazebo RGBD/LiDAR/physical contact 경로 **SUCCESS**.
- real-gazebo-rgb-pinned-upstream-yolo-ros: 실제 같은 유형의 Gazebo Waffle/RGBD와 공식 Nav2, 고정 upstream C++ yolo_ros/D05 통합 **SUCCESS**. 거리 VALID far 0.704022m, VALID stop 0.534589m, UNKNOWN NO_PERSON_CLASS_IN_ACTUAL_YOLO.

**실제 L2 World evidence:** server가 사용한 actual_world.sdf 3,669 bytes, SHA256 17cfc974cc278b40692680ec12b7ffb270b9339746a22068d2779ea3fad25b7c. native_world_service_verified=true, nav2_launched_at_probe=false, temp_nav2_sdf_used_by_server=false. **8회** 성공, 매 회 Scan 최대 wall receive gap [0.428470, 0.216859, 0.386382, 0.470548, 0.245246, 0.340054, 0.232011, 0.240969]초; 최대 0.470548초로 500ms 한도 유지, 최소 여유 약 29.452ms. Sensor/Guard Safety TTL 설정 자체는 변경하지 않았음.

해당 L2 세션에서 Gazebo 서버, 공식 Nav2 Launch, Gazebo GUI client, RGBD Bridge process_exit가 **모두 0**, shutdown_escalated 없음. 움직이는 Goal=false, cmd_vel_published=false, certified_estop=false.

**실제 원본 artifact:** https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44310101993/artifacts/14429986729 . ZIP SHA256 9f38252fe94d11b6577615507d5a750e19524aa6c292bc307fc0fad0a956867e, 내부 L2 SHA256SUMS **17/17 PASS**. 처음 RED gz stderr 및 verdict와 GREEN startup JSON, 실제 Path, 8개 cycle verdict를 보존한다. 4 jobs의 success를 L3 GUI 인수 성공으로 승격하지 않는다.

## 5. 출고 조건·현장 원샷·남은 미검증

WSL2 Ubuntu 24.04 강사 환경에서 아래 **한 명령 블록**만 실행한다. 강사/학생 저장소 정답·TODO 공개 범위는 이 변경에서 수정하지 않았다.

    (
      set -Eeuo pipefail
      SHA='342c6355b27af5b8b11a79b7e345820be18a581f'
      SCRIPT="$(mktemp --suffix=.sh)"
      trap 'rm -f -- "$SCRIPT"' EXIT
      curl -fLsS --retry 3 --max-time 90 "https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public/$SHA/d08/scripts/d08_owner_no_goal_bootstrap.sh" -o "$SCRIPT"
      bash -n "$SCRIPT"
      export AXIA_D08_PUBLIC_SHA="$SHA"
      bash "$SCRIPT" --self-check
      bash "$SCRIPT" --run
    )

Owner 기대 메시지(아직 미실측): D08_OWNER_WSLG_NVIDIA_D3D12_VERIFIED, D08_GAZEBO_WORLD_READY_BEFORE_NAV2_L2_PASS, D08_REAL_GAZEBO_SCENE_BROADCASTER_L2_PASS, D08_OWNER_GUI_REPLAN_LOOP_READY, Ctrl+C 후 D08_OWNER_COMPACT_EVIDENCE=...diagnostics.zip.

**남은 미검증:** 실제 Owner WSLg GPU 화면 pixel, Gazebo/RViz 시각 표시, 긴 반복 시 수신 공백과 실제 RTF, Ctrl+C 종료 안정성은 **L3 HOLD**. 별개 Moving Goal 안전 타이밍/실제 CM STOP/SLOW/인증 E-Stop은 NO_GOAL CI 검증 범위 밖. 문제 재발 시 새 경량 ZIP의 첫 gazebo_startup.json, gazebo_server_error_context와 Scan source-vs-host gap을 CI 회귀에 먼저 편입한다. 동일 오류 현장 재시도를 반복하지 않는다.

    D08_PUBLIC_L0=PASS
    D08_ACTUAL_GAZEBO_TEMP_SDF_RED=REPRODUCED_EXIT_255
    D08_PUBLIC_GAZEBO_NAV2_8_CYCLE_L2=PASS_SCOPED
    D08_PUBLIC_SAME_WORLD_YOLO_D05_L2=PASS_SCOPED
    D08_OWNER_WSLG_L3=HOLD
    D08_RELEASE=READY_FOR_OWNER_ONLY
    AXIA_MVP_DEMO_ACCEPTED=HOLD
    CERTIFIED_ESTOP=false
    MAIN_MERGED=false
