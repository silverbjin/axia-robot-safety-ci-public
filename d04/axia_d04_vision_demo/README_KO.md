# AXIA D04 Vision Demo — ROS 2 Jazzy 패키지

> **교육용 시뮬레이션 전용. 실제 로봇의 인증된 안전 제어나 E-Stop이 아닙니다.**

## 목표
기존 AXIA P1 Nav2 Waffle 주행·제어 그래프를 변경하지 않고, ROBOTIS Waffle Pi **공식 RGB 카메라 센서만 선택적으로** 삽입합니다. 같은 Gazebo World에 공식 Gazebo 사람 Actor(시각 객체) 한 개를 추가하고 공식 `ros_gz_image` + `mgonzs13/yolo_ros` C++ ONNX를 실행합니다. YOLO는 이미지 검출만 하며 **명령 토픽을 발행하지 않습니다.**

## 구성

- `launch/d04_p1_yolo.launch.py`: 기존 P1 Launch를 인자로 포함, ROS 이미지 브리지와 upstream YOLO launch 포함
- `axia_d04_vision_demo/overlay.py`: 공식 Nav2 Waffle SDF에 Pi RGB 센서 하나만 추가; 임시 world에 visual-only 사람 Actor 추가
- `axia_d04_vision_demo/config.py`: 검증된 YOLO CPU ONNX 모델 해시 검증, Detection+Debug 플러그인 YAML 생성
- 사전 학습 가중치 `yolo26n.onnx`는 AGPL-3.0. 저장소와 학생 배포물에 포함하지 말고 이용 목적·조건을 따로 확인하십시오.
- 사람 DAE 역시 런타임 입력으로만 사용하며, 공개 학생 저장소에 복제하지 않습니다.

## 의존성

Ubuntu 24.04, ROS 2 Jazzy, Gazebo Harmonic, `nav2_bringup`, `nav2_minimal_tb3_sim`, `turtlebot3_gazebo`, `ros_gz_image`, C++ `yolo_ros` 고정 upstream commit `94d2dd500cb26027ee9c019f4d3a02029ac615cc` 및 `yolo_bringup`.

P1 강사 전용 `ros2_ws/src/axia_safety_bringup/launch/axia_tb3_p1.launch.py`는 외부에서 실제 파일 경로로 지정합니다. 본 패키지에는 강사 정답·P1 코드를 복사하지 않습니다.

## 빌드
```bash
source /opt/ros/jazzy/setup.bash
cd <AXIA_INSTRUCTOR_REPO>
colcon build --base-paths ros2_ws/src --packages-select axia_d04_vision_demo axia_safety_supervisor axia_fault_injector axia_scenario_verifier
source install/setup.bash
ros2 pkg prefix axia_d04_vision_demo
```

## 실행
```bash
ros2 launch axia_d04_vision_demo d04_p1_yolo.launch.py \
  p1_launch:=<AXIA_INSTRUCTOR_REPO>/ros2_ws/src/axia_safety_bringup/launch/axia_tb3_p1.launch.py \
  onnx_model:=<LICENSED_CACHE>/yolo26n.onnx \
  actor_dae:=<LICENSED_CACHE>/walk.dae \
  headless:=false show_image:=true
```

실행 중 ROS 2에서 `/camera/image_raw`, `/yolo/cam0/detections`, `/yolo/cam0/debug_image`를 확인합니다. 사람 검출 성공은 **실제 person DetectionArray + bbox/confidence + debug 이미지**로 검증해야 하며 토픽 이름만으로 PASS가 아닙니다.

**P1 보호 그래프**: `/cmd_vel_smoothed` velocity_smoother → `/cmd_vel_supervised` axia_safety_supervisor → `/cmd_vel` collision_monitor. 구성은 변경하지 않습니다. P1 G00~G04, 주행 중 정지, HW E-Stop 인수와 다른 데모입니다.

## 검증
```bash
python3 -m pytest -q ros2_ws/src/axia_d04_vision_demo/test/test_d04_package_contract.py
ros2 launch axia_d04_vision_demo d04_p1_yolo.launch.py --show-args
```

WSL2의 검증된 P1+YOLO 이전 원클릭 실행기는 별도 공개 CI 소스 `scripts/axia_d04_p1_yolo_wsl2_once.sh`입니다. 새 패키지 Launcher의 실제 P1 동시 실행은 별도 인수로 진행해야 하며 예전 실행 결과를 이 패키지의 실제 PASS로 주장하지 않습니다.
