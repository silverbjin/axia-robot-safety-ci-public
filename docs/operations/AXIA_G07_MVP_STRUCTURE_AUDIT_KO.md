# AXIA G07 — MVP 패키지·스크립트·환경·Launch 구조 감사

작성: 2026-11-21 KST. 감사 기준: Student a04f9a7da8d54bbd9f944d05388792cb706adf28 / Public 8daaa1a734edfb54126b7e2d5ecadfb3ca4b89f1. 설계 기준: Instructor docs/baselines/AXIA_Robot_Safety_MVP_Baseline_Scenario_Acceptance_v1_KO.md. 성공한 jrCIgoGl 교육용 증거는 보존한다.

## 1. 실제 Student G07 파일 구조

~~~text
block_B/day07/h01_runtime/
  ros2_ws/src/
    axia_safety_bringup/
      package.xml setup.py setup.cfg resource/ axia_safety_bringup/
      launch/axia_tb3_p2.launch.py
      launch/axia_bringup_p2.launch.py
      launch/axia_navigation_p2.launch.py
      launch/axia_p2_include.py
      launch/axia_p2_launch_policy.py
    axia_safety_supervisor/
      package.xml setup.py setup.cfg resource/ axia_safety_supervisor/
      axia_safety_supervisor/p2_supervisor_node.py
      axia_safety_supervisor/p2_base_guard_node.py
      axia_safety_supervisor/p2_shutdown_context.py
    axia_fault_injector/
      package.xml setup.py setup.cfg resource/ axia_fault_injector/
    axia_scenario_verifier/
      package.xml setup.py setup.cfg resource/ axia_scenario_verifier/
  scripts/
    p2_no_goal_smoke_ci.sh
    p2_g07_shared_staged_startup.sh
    d07_h01_gui_no_goal_once.sh
  configs/
  tools/
~~~

4개 패키지 모두 ROS 2 Jazzy ament_python 필수 파일(package.xml, setup.py, setup.cfg, resource/패키지명, __init__.py) 존재. 설치형 Bringup에서 launch/config/tools를 data_files에 설치함. Student G07 scripts/에는 Shell 3개, 이 중 주 실행기는 약 1293줄. G07 tools/에는 진단·테스트까지 114개 Python 소스가 존재하나 전부 동시에 실행되는 것은 아니다. Git 원본 build/install/log/.cache 추적파일은 없음. 패키지 대이동·신규 노드는 불필요.

| 패키지 | 역할 | 상태 및 결정 |
| --- | --- | --- |
| axia_safety_bringup | 공식 Nav2/Waffle Launch 재사용·최소 Include 교체 | 패키지 구조 PASS, 독립 설치 후 모든 CLI 미검증, 유지 |
| axia_safety_supervisor | 보호 FSM/명령 게이트·P2 Guard | 정확한 after-SIGINT graph RCLError만 수정 |
| axia_fault_injector | Scan fault relay | 유지 |
| axia_scenario_verifier | P1 유닛/fake ROS 증거 | G07 Moving 직접 필수 경로 아님, 유지 |

공식 참고: https://docs.ros.org/en/jazzy/How-To-Guides/Developing-a-ROS-2-Package.html 및 https://docs.ros.org/en/jazzy/Tutorials/Intermediate/Launch/Launch-system.html

## 2. 실제 실행 데이터 흐름과 프로세스 책임

~~~text
Public CI 또는 강사 Owner (서로 다른 Goal 권한)
  -> Student scripts/p2_no_goal_smoke_ci.sh
      -> ROS Jazzy setup + colcon install overlay
      -> session-local official Waffle world/10Hz LiDAR SDF 사본
      -> ROS 2 Launch axia_tb3_p2
           -> official Nav2 tb3_simulation
              -> axia_bringup_p2 -> official bringup
                 -> axia_navigation_p2 -> official navigation
                    -> fault injector / P2 supervisor / P2 base guard
      -> 14-topic rosbag + staged startup
      -> real Gazebo physical Goal preflight / CLEAR SLOW STOP / Cancel
      -> ordered Nav+Localization shutdown
      -> 소유한 프로세스그룹만 신호 전송 및 증거 기록
~~~

속도 제어: official Nav2 Smoother /cmd_vel_smoothed -> Supervisor /cmd_vel_supervised -> official Collision Monitor /cmd_vel_pre_guard -> Base Guard /cmd_vel -> Gazebo. 최종 publisher 단일성, 타입 Twist, stale/TTL은 실제 Graph에서 확인해야 한다. SW Stop은 인증된 E-Stop 아님.

## 3. 환경변수 표준 소유권

| 변수 | 현재 실제 사용처 | 리스크/결정 |
| --- | --- | --- |
| ROS_DOMAIN_ID | G07 쉘 기본 56, D07 별도 GUI 기본 57, Public Native 88 | 프로필별 격리 의도, 그대로 유지 |
| ROS_AUTOMATIC_DISCOVERY_RANGE | G07/D07 LOCALHOST 강제 | 외부 DDS 노출 방지, 유지 |
| GZ_PARTITION | 세션 격리 및 CI cycle 구분 | 유지 |
| FASTDDS_BUILTIN_TRANSPORTS | Native CI UDPv4 | 실험 환경 전체 동일 적용, 근본원인 확정 아님 |
| AXIA_G07_CI_SIM_GOAL_ALLOWED | CI만 1, Owner는 0 및 TTY 별도 | 권한 차용 금지 |
| AXIA_G07_DEPTH_SENSOR_ENABLED | G07 기본 0 | 기존 Depth OFF, 유지 |
| AXIA_G07_OBSERVER_IO_PROBE | 원 Native 진단=1, 실험 #228 lean=0 | 비활성 후보 Native 0/2 FAIL, 이번 변경에 미포함 |
| QT_QPA_PLATFORM, LIBGL_ALWAYS_SOFTWARE, GALLIUM_DRIVER | Gazebo 서버 offscreen/GUI 자식 조건부 | 기존 GUI 자식 격리 유지 |
| PYTHONPATH, AMENT_PREFIX_PATH | 설치 overlay 및 CI 검사 | 설치된 실제 Launch 경로 별도 검증 필수 |

주 실행 Shell에서 grep되는 AXIA 문자열에는 로그 마커가 다수 포함되어 있으므로 단순 고유 토큰 수를 실제 환경변수 개수로 보고하지 않는다. 동일 환경변수의 프로필별 상이한 기본값도 반드시 충돌은 아니다.

## 4. Launch 분석

- axia_tb3_p2.launch.py: 공식 tb3_simulation_launch.py를 재사용. DeclareLaunchArgument 3개, 원래 include signature 검증, OpaqueFunction으로 P2 임시 YAML을 생성. D07 NO_GOAL 한정 OnProcessExit world-Xacro→Gazebo 순서 보정이 존재하며 G07 Moving에 임의 확대하지 않는다.
- axia_bringup_p2.launch.py: 공식 bringup Include만 정확히 1회 교체.
- axia_navigation_p2.launch.py: official Nav2에 Injector/Supervisor/Guard를 1회씩 연결. remap/params/use_sim_time은 기존 계약 유지.
- axia_p2_include.py: upstream Include 개수/인자 변경을 탐지하면 예외, fail-closed.
- axia_p2_launch_policy.py: official YAML 비파괴 복제 후 cmd_vel_pre_guard를 지정. tempfile delete=False로 남는 tmp YAML은 관찰사항이나 실제 저장량 미측정, 무리한 cleanup 이벤트 추가 금지.

## 5. 확정 결함 vs 잠재 결함

- 확정, 수정: #44912769355 Cycle2 SIGINT 이후 Supervisor graph-info 호출이 무효 ROS Context에 접근, 원래 WaitSet/Publish classifier에 미포함. 이번에는 live context false만 정확한 RCLError로 처리한다.
- 확정, 미해결: #44914827138 첫 Scan/Clock/Odom·CM/Guard RMW 타이밍 위반. 원인 DDS/Executor/Gazebo bridge 미확정, 보호 TTL 완화 금지.
- 잠재 부하, 수정하지 않음: Supervisor 50ms timer의 정상 health 경로에서 5개 graph endpoint를 조회할 수 있음(이론상 최대 약 100 graph query/s). 실제 CPU·수신 지연의 원인 증거는 없으며 Graph health는 안전 계약이라 단순 저주기화 금지.
- 잠재 패키징: Scenario Verifier runner가 __file__의 parents[4]로 교육용 소스 ROOT를 계산함. 설치된 prefix에서는 루트가 달라질 수 있음. G07 Moving 필수 경로 밖이므로 별도 L1 설치 시험 전까지 미검증.
- 스크립트 1293줄·Tool 114개라는 파일 수만으로 런타임 부하 입증 불가. 실제 PID·스레드·RTF 전후 데이터 없는 통합/삭제는 금지.

## 6. 범위 종료 판정

기존 패키지 이름, Launch 체인, 기본 환경변수, 시뮬레이션 센서 주기/안전 TTL을 보존. 정적 구조 AUDIT COMPLETE, L0 부분 수정 PASS, G07 Moving L2 FAIL 0/2. 신규 Owner WSL2 NOT RELEASED, main NOT MERGED.
