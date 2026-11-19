# AXIA D06/G07 Cycle 06 — Student Scan 실행 큐 분리 / 공개 CI 중간 보고
작성: 2026-11-19 | 공개 PR #177 / 학생 PR #62 Draft | WSL2 배포 HOLD

## 1. 최초 안전 타이밍 위반과 정확한 인과 경계
기준: 실제 Linux Xvfb/Gazebo Harmonic/Nav2 동일 세션 CI #44538452186. artifact #14536669582.
source stamp 36.600→36.702초(동일 메시지):
- Gazebo native /scan: host monotonic 499.057340→499.171147 = 113.807ms.
- 독립 ROS /safety/scan: 499.059103→499.176314 = 117.211ms.
- Student Safety callback: 499.061499→499.503779 = 442.280ms (Scan TTL300 FAIL).
- 동일 stamp 두 번째 Student callback은 독립 ROS peer보다 327.465ms 늦음.
- Student Raw 첫 위반 442.855ms, global /clock RTF 약0.996211. 거리 Safety CLEAR200/200은 안전 TTL PASS가 아님.
- Nav2 Navigation SHUTDOWN ACK1.473939s, Localization SHUTDOWN 30.000328s timeout.
  Localization /get_parameters(23.428ms), 같은 manager 그룹 /is_active(27.376ms) 응답은 SHUTDOWN ACK가 아님.
- CM 및 Gazebo child exit0은 Localization ACK 실패를 무효화하지 않음.

가설: 공유 Python MultiThreadedExecutor의 task queue에 300Hz Clock/Odom과
20Hz Raw/Safety Scan callback이 경쟁하여 Student 입력 진입이 지연.
원인 분류는 AFTER_INDEPENDENT_ROS_RECEIPT; bridge send timestamp 미측정,
GPU/OS 스케줄러 단일 인과는 여전히 UNDETERMINED.

## 2. 기존 코드 재사용과 최소 수정
- 학생 저장소 silverbjin/axia-robot-safety-student, branch
  fix/g07-nogoal-ordered-cm-shutdown-20261119
- Student commit 4f51d255660359f345028410f758793674aaac1c,
  tools/g07_wslg_no_goal_sensor_probe.py blob
  069b0aba9a7da9ba523049ede668d2aa3acfdcb3.
- 기존 노드/토픽/검증 알고리즘 유지; 공유 MultiThreadedExecutor 대신
  Scan node와 Clock/Odom node에 독립 SingleThreadedExecutor 두 개 배치.
  Scan은 메인 스레드, Clock/Odom은 읽기 전용 배경 스레드.
  Event → bounded join(3초) → Executor shutdown → subscription cleanup.
  종료 실패·보조 스레드 예외는 FAIL-closed 처리.
- 공식 Nav2, CM, Safety Supervisor, Guard, Goal, Fault, velocity,
  Waffle/Gazebo sensor 10Hz, Scan TTL300ms, CM120ms, Guard150ms 변경 없음.
- 공개 WSL2 Owner 스크립트는 새로운 Student exact SHA/blob을 고정,
  외부 Owner wrapper도 SHA/blob 연쇄 검증 갱신.

## 3. TDD RED → GREEN → REFACTOR → REVIEW → COMMIT
- RED 재현 #44540133908:
  새 d06/tests/test_d06_c06_two_executor_scan_receipt.py에 정확한
  327.465ms Student callback 지연 fixture 및 독립 Scan 실행 큐 요구.
  이전 소스에는 SingleThreadedExecutor 부재로 실패.
- 구현/정리: 위 Student commit, 기존 d06/tests/test_d06_student_scan_clock_executor_isolation.py
  계약을 새 실행기 구조에 맞게 최소 수정.
- 중간 false RED #44540827016은 scan_executor 이름이
  옛 executor.add_node와 부분 문자열로 일치하는 테스트 자체 오류.
  정확한 토큰 경계를 사용하도록 수정.
- GREEN #44540976700: 125/125 public L0 PASS.
  Tested public code SHA d58bf03044f733c00e281ed14617892e4eae33d3.
  Runner canary #44540976717 PASS.
- 검증 수준은 L0이며, Gazebo 실증이나 WSLg GPU 검증으로 승격하지 않음.
  최초 실증 대상: 공개 L2 #44540963499.
- 공식 rclpy Executor API: https://docs.ros.org/en/jazzy/p/rclpy/api/execution_and_callbacks.html

## 4. Gate / 미검증
다음 실제 L2에서 READY 이후 native/raw/safety 20초 Scan300,
학생 qualified 20초 Scan300, 공식 Nav2 Nav/Loc ACK,
CM/Guard/Supervisor/Gazebo native exit0, witness unsubscribe를 모두 검증.
NVIDIA WSLg SIGSEGV 첫 core backtrace는 NOT_CAPTURED.
L3 final NO_GOAL/MOVING GOAL 미검증.

D06_GAZEBO_LIVE_RELEASE=HOLD
AXIA_MVP_DEMO_ACCEPTED=HOLD
CERTIFIED_ESTOP=false
MAIN_MERGED=false

## 6. C06 실 Gazebo L2 완료 — 센서 GREEN/전체 L2 FAIL (원본 추가)

동일 코드 SHA d58bf03044f733c00e281ed14617892e4eae33d3, [실제 Run #44540963499](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44540963499), artifact #14539141620.

- 실제 Jazzy/Harmonic/TB3 Waffle/공식 Nav2+Gazebo GUI+RViz 동시 세션, NO_GOAL.
- Student **20.024s** qualified Raw199/Safety201: max **119.060/119.308ms**, Safety 201/201 거리 CLEAR (front1.414395m, side2.520718m). 전체 /clock 수신 RTF **0.999071**.
- READY 후 20s 독립 Gazebo native/ROS Raw/Safety witness: first Scan300 breach **NO_ROS_TTL_VIOLATION_WITNESSED** (이 계측 범위에서만). Previous C05 동일 stamp Student delay 327.465ms 이번 Student 검사에서는 재발하지 않음.
- 하지만 실 종료: Navigation manager ManageLifecycleNodes SHUTDOWN request_sent=true, **40.000932s SERVICE_TIMEOUT**, Nav/Loc ACK 둘 다 없음. Runner rc3.
- 원본 native/launch.log의 Navigation Manager **Shutting down managed nodes** 메시지는 요청 이후 SIGINT 전 없음. 시그널 전달 후 preshutdown만 관찰되어 서비스 요청 처리 여부 불확실. Gazebo native server exit0.
- 안전상 인접 후속 실패: Collision Monitor exit **-11**, Base Guard exit **1**, Supervisor exit0. 부모 GRACEFUL 마커와 별개로 네이티브 종료 FAIL. 최초 종료 실패는 Navigation Manage SHUTDOWN timeout, 후속 CM/Guard 비정상 종료의 독립 원인/스택은 미확보.
- 결론: **Task A 센서 측 L2 단일 실행 PASS**(정확히 NO_GOAL 20s+READY witness), **동일 세션 전체 L2 FAIL**. 강사 WSL2 GPU SIGSEGV 해결 및 L3 인수 증거로 승격 불가.

공식 Nav2 API는 ManageLifecycleNodes SHUTDOWN에 대한 positive ACK를 요구한다. 관련 ROS 2 middleware issue [ros2/rmw_fastrtps #842](https://github.com/ros2/rmw_fastrtps/issues/842) 및 [ros2/ros2 #1668](https://github.com/ros2/ros2/issues/1668)는 서비스 응답 소실 가능성의 조사 후보이나, 이 실행의 RMW 종류/서버 실제 수신 증거가 없으므로 인과 확정 금지. 다음 가장 작은 계측: Navigation Manager 동일 callback group의 /is_active read-only probe와 실제 RMW identifier를 최초 timeout 뒤 수집. SHUTDOWN 재요청이나 TTL 완화 금지.

D06_GAZEBO_LIVE_RELEASE=HOLD
AXIA_MVP_DEMO_ACCEPTED=HOLD
CERTIFIED_ESTOP=false
