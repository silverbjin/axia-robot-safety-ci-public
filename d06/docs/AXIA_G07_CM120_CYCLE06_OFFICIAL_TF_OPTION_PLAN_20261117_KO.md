# AXIA G07 Cycle06 — 공식 Nav2 base_shift_correction 단일 SIM 후보 계획

## 근거·성격
- Cycle05 실제 diagnostic Goal CI #43995793080: CM RMW source 첫 120.172578ms 간격, 동일 observer 창에 공식 /cmd_vel_supervised C++ callback 81.972669ms 확인. Callback 안에서 TF lookup / Scan transformation / Executor 중 무엇이 원인인지는 UNPROVEN; tracer-on 성능은 릴리스 근거가 아니다.
- Nav2 공식 Jazzy src/source.cpp는 base_shift_correction=true 시 odom fixed frame advanced TF lookup, false 시 source->base simple transform. 공식 Nav2 Issue #3402, 병합 PR #3412 참고. 이미 G07은 transform_tolerance=0.02s, odom 임시 100Hz.
- 이번은 공식 파라미터 *한 개*를 G07 CI 시뮬레이션 후보로만 false 설정해 실측 비교하는 제한된 개발. 정식/Owner/학생/Instructor baseline P1, Safety hard TTL, CM release 120ms, zone geometry, scan freshness, official Nav2 코드 변경 금지.
- 시간 보정 생략으로 주행 중 LaserScan points 위치오차가 발생할 수 있다. 본 후보는 실제 WSL2 또는 인증된 E-Stop에 적용하지 않는다. STOP 영역 x<=0.40m, SLOWDOWN 영역 x<=0.75m는 그대로 유지하고, 기존 실제 Contact0/STOP/scan age/odom zero dwell 동시 통과가 필수다. 정지 안전 인증을 얻은 것은 아니며 false 실험만으로 출고 승인 금지.

## RED→GREEN→REFACTOR→REVIEW→COMMIT
1. RED: 기존 private baseline SHA 966886c4627deb2bb3b37111fe336eeee6b9ebb4는 G07 CI SIM 한정 base_shift 변경 함수·런타임 readback 계약이 없어 신규 unittest RED. 불명확한 zone, TF fast-fail 미적용, Owner/NO_GOAL/비CI 환경에서 반드시 ValueError.
2. GREEN: private tools/p4_g07_cm_sim_simple_tf.py 하나만 작성. 적용 조건 GITHUB_ACTIONS=true, ROS_DISTRO=jazzy, AXIA_P0_SIM_ONLY=1, AXIA_G07_CI_SIM_GOAL_ALLOWED=1, AXIA_G07_C06_SIMPLE_TF_SIM=1, GZ_PARTITION=axia_p2_*, transform_tolerance=.02, original base_shift_correction absent-or-true, original Stop/Slow polygon exact. CM 한 필드 base_shift_correction=false. 다른 파라미터 절대 변경 금지.
3. 기존 nav2 param writer (ros2_ws/src/axia_safety_bringup/launch/axia_p2_launch_policy.py)에 opt-in 호출 한 곳만 연결; 원래 안전/Goal 코드 재사용. Public CI RED→GREEN L0와 config diff 범위/negative scope 모두 검증.
4. 실제 한 개 Gazebo Harmonic Waffle/Nav2 CI simulation Goal(C37 exact real runner)에서 NO_GOAL 실제 /collision_monitor base_shift_correction=false readback을 Goal 전에 검사한 뒤에만 Goal. 원본 Contact0/CLEAR→SLOWDOWN→STOP/odom 1초 dwell/Goal Cancel/ordered Shutdown/14-topic, Guard150/Scan300/CM RMW source+Observer <=120ms 유지. **후보 시뮬레이션 성공도 Owner WSL2 출고 PASS 아님**.
5. 이동 보정 생략의 모션 오차는 실제 speed·angular rate·LaserScan header age에 의존한다. 기존 ROS callback interarrival max를 scan age로 등치하지 않는다. 내부 TF 원인 미확정 상태에서 정식 안전성 주장/배포 금지. 해당 증거가 미흡하면 실험의 120ms PASS 여부와 관계없이 safety acceptance HOLD.
6. PASS 후보 시 original true/shadow false 소스 SHA, 실행 시간, first gap과 전체 통합 7채널 TTL 비교 및 미검증 항목을 교육용 보고서에 기록. FAIL 후보면 원본의 root cause를 증명하지 못한 것으로 표시하고 candidate 퇴역, 동일 구성 반복 금지.
7. 실패/성공 여부와 무관하게 cycle마다 실제 Run ID·원본 stderr·first fault·branch/commit·L0/L2/Owner 미검증을 보고서 커밋. 일회성 release workflow 회수, 모든 main 병합 사용자 승인 전 금지.

## 공통 상태
AXIA_MVP_DEMO_ACCEPTED=HOLD
CM_120MS_RELEASE=HOLD
OWNER_WSL2_MOVING_L3=NOT_RUN
CERTIFIED_ESTOP=false
