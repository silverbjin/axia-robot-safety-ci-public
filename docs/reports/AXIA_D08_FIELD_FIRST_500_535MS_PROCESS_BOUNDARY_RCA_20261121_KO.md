# AXIA D08 — WSL2 500.535ms Scan 최초 경계 포렌식 및 원인 분리 보고

- 날짜: 2026-11-21 KST
- PR #205 / branch diag/d08-owner-first-500ms-process-boundary-20261121
- 기준 PR #204 head 31e2d0662c39e4e35781d9d62f0d98699d383845 (실제 D05 통합 L2 공개 #44736215113 PASS 보존)
- 현장 원본: 2026-11-20 WSL2 run_20261120T143716Z_Fj7oCf.diagnostics.zip + SHA256
- 현장 소스 SHA c3373bbd66c67cc5d59e99a18127ddc6c58a0d3f
- 비공개 ZIP 및 로그 원본은 공개 저장소에 업로드하지 않음
- 판정: **WSL2 L3 HOLD, Scan 500ms FAIL-CLOSED 유지, 물리적 근본 원인 UNDETERMINED**

## 1. 원본 무결성 및 성공 범위

- ZIP 38개 항목, 79 KiB, ZIP CRC 검사 PASS, 외부 SHA256 = 7604a80c8f9185b5d1a15ccbd73d0454bbdc89d8f1e8c33d1d14b66b64355085, 내부 SHA256SUMS 37/37 PASS.
- 실제 WSL2 공식 Nav2 before/intrusion/restored = PASS.
- 동일 월드 D05 farther VALID: 0.704023m, stop VALID: 0.534591m, 차이 0.16943m, unknown UNKNOWN: NO_PERSON_CLASS_IN_ACTUAL_YOLO.
- D05 farther Scan 최대 wall gap 0.412461s (20 samples, RTF 0.7055), stop 최대 0.226002s (20 samples, RTF 0.8162), 모두 0.5s 한계 이내.
- 이 이전 성공이 Owner cycle_0000의 실패를 상쇄하지 않음.

## 2. 최초 Fail-Closed 이벤트

- Owner cycle_0000 최초 활성 Scan RX gap **0.500535s** > 0.500000s.
- 같은 sensor_msgs/LaserScan header source stamp: 39102000000ns → 39201000000ns (SIM header delta 0.099s).
- 원본 Observer callback wall monotonic: 272.757400s → 273.257935s (gap 500.535ms).
- Native Gazebo transport 수신 동일 source pair: gap 165.625ms.
- 별도 OS 프로세스 ROS witness 수신 동일 source pair: gap 164.282ms.
- 같은 Python 프로세스 독립 rclpy Executor node의 gap: 약 496.165ms.
- 원본 rclpy Subscription.handle.take_message 완료 간격 500.334ms, 마지막 take→callback dispatch 0.048ms.
- 원본 Scan callback 처리 최대 9.41ms, 해당 구간 spin_once 최대 51.722ms, 프로세스 heartbeat 최대 38.94ms. 500ms 동안 전체 Python 중단이라는 주장은 부적절.
- Native→원본 ROS 동일 source 수신 시차: 이전 4.572ms, 이후 339.482ms. 이 지표는 RMW/DDS 내부 원인 증명은 아님.
- CM service /collision_monitor/get_state 준비 대기 272.342032~273.620514 (약 1.278482s) 및 cm_native_service_probe 272.286077~273.862419가 첫 gap 전체와 중첩. **중첩은 정황 증거일 뿐 원인이 입증된 것은 아님**.
- RMW trace 발행 이벤트 최대 근접 gap 170.281ms, 하지만 DDS source_timestamp가 LaserScan.header.stamp와 동일함은 별도 증명되지 않음.
- 기존 JSON RMW field "independent_ros"는 실은 원본과 SAME Python 프로세스의 다른 노드/executor를 뜻한다. 별도 OS 프로세스 관측 결과라고 해석하면 오진.

## 3. 최초 안전 상태 전이 / 종료 별도 HOLD

- 공식 Collision Monitor는 Lifecycle active (id=3), topic scan 설정만 확인. 안전 상태 전이/실제 정지 작동, CM 내부 120ms 및 Guard 150ms는 미검증.
- NO_GOAL, robot cmd_vel/Goal 발행 없음. 인증 E-Stop 성공이 아님.
- 원본 D08_OWNER_GUI_REAL_PATH_CYCLE_FIRST_BOUNDARY에서 ValueError:D08_FIRST_REAL_SCAN_RECEIVE_GAP_OVER_500MS:{index:10,gap_sec:0.500535} 발생.
- 종료 요약: Nav2 런처 rc1, Gazebo 서버 -11, RViz2 -6; SIGINT/종료 이후의 RViz abort 및 /tmp/nav2_*.sdf 부재는 최초 Scan 위반보다 먼저였다는 증거 없음. 첫 실패 원인으로 혼동 금지.

## 4. 최소 공개 CI RED→GREEN

- 신규 코드: d08/tests/test_d08_wsl2_first_500ms_process_boundary.py, 제한된 숫자 계약 3개.
- RED 공개 #44762069941: 2/3 PASS, 신규 RMW process origin 필드 미존재로 1 ERROR; 원본 500.535ms Fail-Closed 및 CM 서비스 overlap=correlation 기존 검증 PASS.
- GREEN 공개 #44762207636: 3/3 PASS, 실제 ROS/Gazebo는 실행되지 않은 L0 진단 계약.
- 최소 보정: d08/scripts/d08_owner_rmw_first_gap.py에서 independent_ros_origin=SAME_PYTHON_PROCESS_DIFFERENT_RCLPY_NODE_EXECUTOR, independent_ros_separate_process=false, isolated_os_process_not_represented_here=true 명시. **기존 후보 계산, first 500ms gate, 실제 코드 동작은 변경 없음**.
- Main 병합 없음. 동일 오류의 현장 재실행을 권고하지 않음.

## 5. 검증 가능한 후속 단일 가설 및 수락 기준

우선 가설: 원본 Python 프로세스에서 CM 상태 서비스 준비 대기가 진행되는 동안 동일 프로세스 rclpy Executor의 Scan callback wake 또는 take 경로에 수백 ms 지연이 생겼을 가능성.

이 가설의 검증은 기존 공개 SAME Gazebo 월드와 Nav2로 수행하는 read-only A/B여야 함:
(A) 기존 동일 Python CM GetState/GetParameters 조회와 Scan 관측의 중첩,
(B) CM 조회를 별도 프로세스 또는 별도 독립 컨텍스트로 격리하되 CM 실제 active/topic 확인은 그대로 수행.
두 모드 모두 동일한 가상 월드, QoS, Scan 500ms 임계값, CM/Guard Safety TTL, 원본 LaserScan callback, 8-cycle 이전 성공 증거를 보존함.
최초 timing gap source pair를 Native Gazebo→별도 ROS OS→원본 같은 Python Executor→원본 콜백으로 분류하고, CPU heartbeat·spin/wait 및 실제 RMW tracing을 대조할 것. A/B 동일 조건에서 재현된 첫 gap이 별도 CM 조회로 소실되고 다른 안전 경계 위반이 없는지 평가해야 하며 단발 A/B 성공을 장기 안정성으로 보고하지 말 것.
공식 rclpy Executor는 wait set으로 구독/서비스 client를 대기하므로 관계는 기술적으로 검증할 가치가 있지만, 본 관측만으로 rclpy 자체 결함 또는 CM fault를 확정할 수 없음.
실제 공개 CI 레벨의 회귀 RED→GREEN 및 새로운 최초 위반 분류가 완료되기 전에는 SHA 고정 WSL2 재인수 스크립트를 재출고하지 않음.

## 6. 검증 수준

- 실제 WSL2 원본: 위 수치와 최초 FAIL 증거 확인. WSL2 최종 인수는 FAIL/HOLD.
- 새 공개 CI L0: 첫 시간 위반 처리 및 프로세스 정체성 메타데이터 회귀 PASS.
- 새 root-cause 수정, CM 조회 격리 실기 A/B Gazebo/Nav2 L2: **NOT_RUN**.
- 이전 PR #204 실제 Nav2+RGBD+YOLO+D05 단일 월드 통합 L2 PASS 보존, 이번 500.535ms 오류를 해결했다고 승격하지 않음.
- CM 내부 120ms, Guard 150ms, Moving E2E, 인증된 E-Stop 미검증.
