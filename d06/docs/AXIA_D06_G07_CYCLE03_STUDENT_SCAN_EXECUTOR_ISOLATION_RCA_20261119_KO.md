# AXIA D06/G07 Cycle 03 — 최초 Student Scan 콜백 경계 분리·L0 GREEN·실제 Gazebo 검증 (2026-11-19)

## 최초 실패 경계와 원본 증거

- 공개 실제 Gazebo L2 [#44531611496](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44531611496) 원본 artifact #14533782394, SHA `ff8d61d6534992c7f29db5184bf0e92591d0b5e1`.
- 정확히 동일한 Scan source stamp **43.800→43.902초**의 독립 Gazebo Transport native 수신 gap **89.121ms** (host monotonic 342.925123→343.014244), 독립 ROS Raw **89.806ms** (342.925639→343.015445), Student Raw 동일 콜백 **427.533ms** (342.928454→343.355987).
- Student 콜백의 두 번째 메시지 시각은 독립 ROS raw 구독보다 **340.542ms 뒤**. Gazebo 센서 publisher 자체의 427ms 지연이 아님. 독립 ROS witness의 정상 gap과 Student 단일 Executor의 지연을 구분해야 함.
- 구 기존 `g07_wslg_no_goal_sensor_probe.py`는 Scan Raw/Safety, Odom, 수백 Hz /clock을 한 `rclpy.spin_once` node/executor에서 처리. 단일 Executor 내 콜백 경쟁은 합리적인 **개선 후보**일 뿐 OS/DDS/GPU 근본 원인을 증명하지 않음.

## RED → GREEN → REFACTOR → REVIEW → COMMIT

1. **RED 테스트**: `d06/tests/test_d06_student_scan_clock_executor_isolation.py`는 정확한 same-pair 계측, 별도 Scan/Clock-Odom callback 실행 경계, `MultiThreadedExecutor(num_threads=2)` 요구. Scan300/Guard150/CM120 무변경 및 Publisher/Goal 금지. 공개 L0 워크플로 연결 (SHA `59aa41173c58c5c4c56a9567432e3b67dfaefc5c`); 코드에 분리 Executor 부재로 의도한 테스트 FAIL.
2. **GREEN Student 코드**: `silverbjin/axia-robot-safety-student`, PR #62, SHA `b67d22af3687c2662117a590f909eab9216399a8`, 파일 `block_B/day07/h01_runtime/tools/g07_wslg_no_goal_sensor_probe.py`, Git blob `8bd44fb8a55d2cdb8c03bdc510985a8561a7118d`. Raw+Safety Scan에 별도 node, Clock+Odom에 별도 node, 2-thread Executor로 기본 callback group을 분리; 종료 시 Executor join→subscription 정리→node 삭제→`rclpy.try_shutdown`. 관측·출력·Scan300 승인 조건은 동일. 신규 Goal/Publisher 없음.
3. **Owner release pin 동기화**: `d06/scripts/axia_d06_g07_wslg_sensor_no_goal_once.sh` SHA `58cdaa535343720e0c4dd21438c7abee9725eb29`, blob `70bcce196f99d5ef7af4051574b890aac5c10365`. 외부 원샷과 공개 L0/L2 학생 commit SHA 고정. 코드 검수 시 D08 RGB-D sensor update_rate 변경을 D06으로 이식하지 않음.
4. **GREEN L0** [#44533992763](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44533992763): 118/118 통과, 소스 SHA `7c38ac2e756e60e64b9262ed13c5fb9ad437523d`. 실제 ROS/Gazebo가 아닌 read-only 계약 검증임.

## 첫 공개 실제 L2 — 인프라 실패로 효과 미검증

- 실제 ROS/Jazzy Gazebo/Harmonic/Nav2 동일 세션 L2 [#44534113749](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44534113749), 소스 SHA `566350e86f9d0b55de3fa86f3fe4e2c463ba5b15`.
- 최초 실패는 `apt-get update`가 Ubuntu `http://security.ubuntu.com/ubuntu noble-security/InRelease`를 다운로드할 수 없어 **rc100**, 이후 실제 ROS/Gazebo startup는 **NOT_RUN**. 이것을 Scan 성능 개선 실패로 오판하지 않음.
- 관련 독립 CI 환경 수정 후보는 Cycle04 `test_d06_l2_apt_https_bootstrap.py`와 signed HTTPS sources만 사용. APT 서명 검증 우회·WSL2 Owner 전역 패키지 설정 변경 금지.
- 패키지 준비를 통과한 실 Gazebo L2에서 실측 Scan TTL·Nav2 Lifecycle·CM/Guard/Supervisor/Gazebo 실제 exit0를 검사하기 전 Cycle03은 **L2_NOT_VERIFIED**.

## 관련 독립 Student 공개 CI 정적 계약 오류

- Student 기본 `block_B/tests/test_d07_h01_rqt_continuous.py`의 과거 `on_exit=[gazebo_server]` 문자열 기대는 현재 성공한 **SDF 선검증 후 Gazebo 실행** launch `_on_world_xacro_exit` 구현과 달랐음. 이는 기존 테스트 정적 계약의 stale expectation이며 새로운 Executor 문제로 단정하지 않음.
- Student PR #62에서 테스트만 실제 Xacro returncode/SDF 내용 확인 계약으로 고침: SHA `ebcf65cde1d96c817eafd5e7bd587e3a47059854`. 공식 Nav2 launch 로직, world Xacro, Gazebo 실행 경로 **미변경**. Student 해당 실제 CI 결과는 별도로 확인하며 L0/ROS-free 통과를 L2로 주장하지 않음.

## 상태 / 안전

공개 PR #177과 학생 PR #62 둘 다 Draft, main 미병합. NVIDIA WSLg D3D12와 Gazebo SIGSEGV core backtrace 없음. LiDAR 내부 pub timing 미측정; Scan300 성능 해결 미확정. `D06_GAZEBO_LIVE_RELEASE=HOLD`, `AXIA_MVP_DEMO_ACCEPTED=HOLD`, `CERTIFIED_ESTOP=false`. Final WSL2 L3 NOT_RUN, Moving Goal and downstream CM120/Guard150 NOT_VERIFIED.

재실행할 실제 L2가 source stamp와 host monotonic을 동시 보존하여, first post-READY native/raw/safety TTL과 Student qualified 20초 및 종료를 모두 만족해야 다음 gate로 진행.
