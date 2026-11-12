# D04 RViz2 로봇 상태 관찰 가이드 — ROS 2 Jazzy / Gazebo Harmonic

**목표:** 레이저 스캔, Waffle 로봇 모델, TF, 오도메트리, 카메라, YOLO bbox를 **하나의 RViz2 화면**에서 살펴보고, 최초 오류가 어디서 발생했는지 논리적으로 진단한다. RViz는 **관찰 전용**이며 Nav2 Goal, /cmd_vel, Fault Injector를 실행하지 않는다. SW STOP은 인증된 하드웨어 E-Stop이 아니다.

## 1. 열기: 자동 표시 + 클릭 바로가기

**WSL2 Ubuntu 24.04에서 한 번에 실행 (공개 CI 검증 고정 SHA):**

~~~bash
(
  set -Eeuo pipefail
  SHA='228b4f1555e8eb7c9c341607c1dcae417ddeede3'
  SCRIPT="$(mktemp)"
  trap 'rm -f -- "$SCRIPT"' EXIT
  curl -fsSL --retry 3 \
    "https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public/$SHA/scripts/axia_d04_classroom_wsl2_once.sh" \
    -o "$SCRIPT"
  bash -n "$SCRIPT"
  bash "$SCRIPT" --run
)
~~~

**원샷의 원본 P1/Nav2/YOLO 실행 SHA는 기존 `c775820077917c4da56c6aa60001b224071664b3` 그대로**이며, RViz 설정·표시 감시만 추가했다. **비공개 강사 저장소에 대한 기존 접근 권한은 필요하다.** 학생의 단일 이미지 Python YOLO 실습만 실행했다면 로봇·TF·LaserScan 토픽이 없으므로 RViz에도 표시되지 않는다.

**강사용 D04 WSL2 원샷 실행기** `scripts/axia_d04_classroom_wsl2_once.sh`를 사용한다. 기존 D04 사람 검출·안전 그래프 검사를 마치고 `[D04][GUI_DEMO_HOLD] START`에 진입하면 **RViz가 자동으로 열린다**. 기존 P1·Nav2·YOLO 원본과 검증 조건은 바꾸지 않는다. D04 정상 종료 때 이번 실행에서 자동으로 띄운 RViz만 정리한다.

원샷은 아래 두 파일을 자동으로 설치한다.

- 설정 파일: `~/.local/share/axia-d04/rviz/axia_d04_robot_state.rviz`
- 클릭용 바로가기: `~/Desktop/AXIA-D04-RViz.desktop` (WSLg의 Ubuntu 파일 탐색기에서 더블클릭하거나 처음에는 **Allow Launching** 선택)
- 터미널 대체 명령: `~/.local/bin/axia-d04-rviz --open`
- 사전 검사: `~/.local/bin/axia-d04-rviz --doctor`

**WSL2 주의:** Ubuntu의 `~/Desktop`은 Windows 바탕화면이 아니다. WSLg에는 일반 데스크톱 셸이 없는 경우가 있으므로 **자동 RViz 창 표시가 기본 방법**이다. RViz가 없으면 `sudo apt-get install ros-jazzy-rviz2`를 별도 설치해야 하며, 그 경우 기존 Gazebo·YOLO 실행 성공을 RViz 실패와 혼동하지 않는다.

자동 실행은 `AXIA_D04_RVIZ_AUTO=1`(기본)이고, GPU/WSLg 자원이 부족하면 `AXIA_D04_RVIZ_AUTO=0`으로 실행한 후 바로가기로 수동 열 수 있다. D04의 GUI 유지 시간은 최대 120초이며 그 시간이 지난 후에 시연 프로세스가 종료되면 ROS 토픽은 사라진다.

RViz가 이미 설치되어 있고 Gazebo가 실행 중이라면 `File → Open Config`에서 저장된 `axia_d04_robot_state.rviz`를 선택할 수도 있다. 정확한 구성 파일은 [rviz/axia_d04_robot_state.rviz](../rviz/axia_d04_robot_state.rviz).

## 2. 저장된 RViz 화면 이해

| Display | 입력·설정 | 학습할 상태 |
|---|---|---|
| Global Options | **Fixed Frame = odom** | scan·TF·model을 동일 기준 좌표계로 표현할 수 있는가 |
| RobotModel | `/robot_description` (Topic, Transient Local QoS) | Waffle 본체·링크가 보이는가 |
| TF | ROS 기본 `/tf`·`/tf_static` | `odom`에서 `base_link`, `base_scan`, `camera_link`까지 연결되는가 |
| LaserScan | `/scan` (Best Effort QoS), 빨간 점 | 레이저 거리점이 수신되고 표시되는가 |
| Odometry | `/odom` | 로봇 추정 위치/방향; D04에서 로봇이 정지한 것은 정상 |
| RGB Camera | `/camera/image_raw` (Best Effort) | Gazebo RGB→ROS 이미지 브리지 확인 |
| YOLO Debug Image | `/yolo/cam0/debug_image` (Best Effort) | bbox와 레이블이 실제 이미지에 표시되는가 |

**관찰 시작점:** RViz Displays 오른쪽의 `Status: Ok / Warn / Error`. 모든 항목이 공백이면 `Global Options → Fixed Frame=odom`과 `/tf`를 확인한다. TF 축이 너무 많으면 `TF → Frames → All Enabled`를 끄고 관심 프레임만 켠다. 이미지는 각 Image Display의 패널을 펼쳐 확인한다.

**토픽 존재와 메시지 수신은 다르다.** 카메라 토픽 목록에 나타났더라도 실제 이미지 프레임이 오는지 확인해야 한다. TF가 없으면 `/scan` 메시지가 실제로 있어도 RViz에 레이저 점이 보이지 않을 수 있다. `/robot_description` 미발행이면 TF가 정상이어도 3D 모델은 표시되지 않는다.

## 3. 실습: 최초 실패 경계부터 역추적

1. **레이저 점이 없다:** `/scan`의 Hz → LaserScan QoS Best Effort → `header.frame_id` → `odom`까지 TF 연결 여부 순서로 확인한다. 바로 LiDAR 고장이라고 결론 내리지 않는다.
2. **로봇 모델이 없다:** `/robot_description` 토픽과 `robot_state_publisher`, TF의 `base_link` 연결 확인. 모델 경로와 TF를 구분한다.
3. **카메라 영상이 없다:** `/camera/image_raw` 실제 Hz, `ros_gz_image` 브리지 확인. YOLO부터 수정하지 않는다.
4. **RGB는 있는데 bbox가 없다:** `/yolo/cam0/debug_image`와 `/yolo/cam0/detections` 구독/주기 및 YOLO 추론기 상태 확인. 사용자 정의 `yolo_msgs` overlay가 필요한 CLI 문제와 추론 오류를 구분한다.
5. **카메라엔 사람이 있는데 레이저에 사람이 없다:** D04의 Gazebo 인간 Actor는 **visual-only**이며 충돌·LiDAR 반사를 갖춘 실제 장애물이 아니다. 사람 검출이 물리 정지 성공을 입증하지 않는다.
6. **시연 종료 후 Unknown topic:** D04는 검증 후 Nav2를 관리형 종료하며 `ROS_DOMAIN_ID=40`, `ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST`를 사용한다. 종료한 노드의 토픽은 보이지 않는 것이 정상이다.

**현장 진단 명령:** (같은 WSL2 배포판에서 D04 실행 중)

~~~bash
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=40
export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
ros2 topic list -t | grep -E '^/(scan|odom|tf|tf_static|robot_description|camera/image_raw|yolo/cam0)'
ros2 topic info -v /scan
ros2 topic info -v /camera/image_raw
timeout 8s ros2 topic hz /scan || true
timeout 8s ros2 topic hz /camera/image_raw || true
~~~

YOLO Detection 자체의 주기는 별도의 `yolo_msgs` 설치 overlay가 필요하다. 공개 진단기 `scripts/axia_d04_ros_cli_diagnose.sh --doctor` 또는 `--live`를 사용한다. 카메라 약 4Hz를 **YOLO 검출률**이라고 잘못 설명하지 않는다.

## 4. 훈련생 5분 관찰 미션

강사 질문: “Waffle 로봇은 보이는데 LaserScan 점이 없으면 센서 고장인가요?”  
훈련생 답: “아닙니다. `/scan` 실제 메시지, Best Effort, LaserScan frame_id, TF→odom 순서로 진단해야 합니다.”

강사 질문: “카메라에는 사람이 보이는데 LiDAR에는 없다면?”  
훈련생 답: “D04의 사람 Actor는 시각용이며, 물리 충돌 또는 센서 반사가 보장되지 않습니다.”

**결과물:** (1) RViz 화면 캡처, (2) `/scan`과 카메라 실제 수신주기, (3) TF·RobotModel의 첫 경고 원인, (4) 증거 `EVIDENCE/round-1/live/verdict.json` 경로, (5) 미검증 항목. **NO_GOAL** 정책 유지.

## 5. 검증 범위와 주의

공개 CI는 RViz YAML 구성·LaserScan QoS·클릭용 설치기·GUI 유지 구간 자동 표시 및 소유한 RViz만 종료하는 동작을 검증한다. **공개 CI의 headless/static PASS를 사용자 WSL2 화면 렌더링 PASS로 승격하지 않는다.** 실제 Gazebo·RViz·TF·LaserScan·RGB/YOLO GUI는 사용자 WSL2에서 확인해야 한다. RViz 시연만으로 Nav2·Safety Supervisor·Collision Monitor TTL 또는 인증된 E-Stop은 **미검증**이다.

참고: [Nav2 Jazzy RViz 기본 구성](https://github.com/ros-navigation/navigation2/blob/jazzy/nav2_bringup/rviz/nav2_default_view.rviz), [ROS 2 RViz](https://github.com/ros2/rviz).
