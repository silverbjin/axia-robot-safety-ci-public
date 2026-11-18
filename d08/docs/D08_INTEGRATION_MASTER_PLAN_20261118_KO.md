# AXIA D08 — D04/D05 센서 · D06 CM · D07 공식 Nav2 통합 마스터 계획 v1

- 기준일: 2026-11-18 KST
- 범위: **교육용 NO_GOAL** 우선; **MOVING E2E 별도 G07 HOLD**
- 기준 저장소 main (실제 GitHub 조회): Instructor `f46874470a814be8f6976b6adbcaa1e43a1fe681`, Student `6a3047b5aa219687f5fc918e467cea5115d3d482`, CI `62e366b51c64da25ad0216328fe1e019b78e0bef`.
- 이 문서는 계획/정적 소스 조사만 기록한다. **현재 새 L0/L1/L2/L3 결과 없음**.

## 1. 완료선 및 아키텍처

교육 MVP는 공식 TurtleBot3 Waffle + Gazebo Harmonic **world/default 1개**, `axia_p2_g07_obstacle` **물리 Collision/Contact와 사람형 Visual 1개**, 실제 카메라 RGB+32FC1 Depth, YOLO `DetectionArray`, 실제 Waffle LaserScan, 공식 Nav2 Costmap/`ComputePathToPose` 및 공식 CM 실제 /scan 구독을 **같은 실행 SHA / ROS_DOMAIN_ID / GZ_PARTITION / clock 및 TF**에서 관측한다. **NavigateToPose, FollowPath 및 최종 /cmd_vel 발행 금지.** 학생 TODO와 private 강사 정답을 유지한다.

현재 공개 `d08/harness/d08_live_world.py`에 같은 물리 모델에 연결된 인간 Visual이 이미 있고, `d08/scripts/d08_public_gazebo_l2.py`의 한-world RGBD·실제 /scan·set_pose·Contact probe가 존재한다. **새 World/Planner/Controller/YOLO/driver 개발 금지.** D07-H01 물리 obstacle 및 Nav2 planner loop는 별도 Student PR #36에서 선별한다. D08 GUI SceneBroadcaster/mesh는 별도 Student PR #41에서 검증된 최소 수정만 선별한다. 세 PR을 통째 병합하지 않는다.

교실 설명: YOLO/Depth는 **관찰 전용**이고 CM과 Nav2 Costmap의 obstacle source는 실제 /scan. Depth UNKNOWN은 CLEAR가 아니다. 정적 NO_GOAL CM 상태 관측 ≠ 움직이는 로봇의 실제 감속 출력. SW Stop ≠ 인증 E-Stop.

## 2. 재사용/검증 비교표

| 구성요소 | 기존 기준 및 증거 | 기존 수준 | 통합 방식 | 아직 미연결 경계 | 수정? / 공개? |
|---|---|---|---|---|---|
| D08 물리 Proxy·등록 RGBD·실제 /scan | CI main `62e366b5`, `d08_live_world.py`, `d08_public_gazebo_l2.py` | 기존 Gazebo L2 시험 코드; 현재 HEAD 실행 별도 확인 | import + one-world overlay | 동일 장면 공식 Nav2 + CM 데이터 전달 | 최소 / 예 |
| D08 read-only YOLO·ROI | CI main `d08_live_readonly_probe.py`, `d08_ui9_yolo_replay_probe.py`; Student PR #41 `f77a3e84` | L0/L1/L2 참조, **실제 동시 거리 2단계 미입증** | read-only, private D05 reference는 Instructor 내부 | registered 근거·YOLO bbox ROI VALID/UNKNOWN 연결 | 최소 / 공개 계약만 |
| D05 미터 거리 | Instructor main `axia_d05_depth_demo/{ros_observer,range_core,triad_sync}.py` | 과거 D05 별도 | 강사 내부 import; 공개는 기존 D08 read-only 공개 probe만 활용 | same-run 2 VALID + 1 UNKNOWN | 최소 / 정답 비공개 |
| D06 공식 CM | CI main `d08_real_nav2_cm_l1.py` / `d06_cm_live_gate.py`, 참조 Run #42656227824 | 실제 ROS L1, **CI CM synthetic scan 격리 시험** | 공식 binary + read-only observer | 실제 World /scan 구독과 first gap | 예 / 공개 계측 |
| D07 공식 Planner | CI main `d07_nav2_planner_l1.py`, 참조 Run #42661513782 | 실제 ROS L1 | 공식 Action read-only Path | 동일 World set_pose → Costmap 갱신 → 3-phase Path | 예 / 예 |
| D07 physical classroom loop | Student PR #36 `8b851ab6`, 참조 Gazebo L2 #44051183220 | 이전 PR SHA L2, 현재 main diverged | 필요한 loop 파일/기존 smoke만 선별 | D08 RGBD/YOLO/CM과 월드 결합 | 예 / 예 |
| D08 GUI restore | Student PR #41 `f77a3e84`, 참조 Xvfb #44120800666 | 이전 PR SHA L2; Owner WSLg 미검증 | scene mesh/GUI change 선별 | 화면 렌더, D07 H01와 충돌 없음 | 예 / 예 |
| G07 moving strict | CI Run #44120024711 (`092124d2`) **failure** (RED job 실패); 더 이전 일부 PASS를 현 SHA에 전이 금지 | moving 전체 게이트 미충족 | **별도 의존** | CM source+observer <=120ms, Guard age <=150ms, odom/Goal/ACK | D08 변경 금지 / 진단만 |

정확한 Student PR 비교: #36 `main...8b851ab6`: diverged, ahead 12 / behind 15, 총 6개 변경 파일. #41 `main...f77a3e84`: ahead 20 / behind 0, 총 11개 변경 파일. Instructor PR #210은 `main...eb6e87f9` diverged, 현재 main과 변경 중복 검토 필요. **모든 기존 Run은 참고 증거일 뿐 새로운 D08 통합 런의 합격 증거가 아니다.**

## 3. 단일 런타임 데이터 계약 / 최초 확인 목록

- Gazebo World: `default`; physical proxy: `axia_p2_g07_obstacle`; robot Waffle; same ROS_DOMAIN_ID/GZ_PARTITION 및 sha pinned.
- 카메라: `/axia/d08/rgbd/image` (`sensor_msgs/msg/Image`), `/axia/d08/rgbd/depth_image` (`sensor_msgs/msg/Image`, `32FC1`), `/yolo/cam0/detections` (설치 `yolo_ros` `DetectionArray`, **정확한 ROS package/type은 런타임 확인**). `camera_info`·registration·optical TF는 매 실행에서 증거화. frame_id/크기 일치 **만으로 registration 주장 금지**.
- 공통: `/scan` (`sensor_msgs/msg/LaserScan`, 실제 Waffle), `/clock` (`rosgraph_msgs/msg/Clock`), `/tf` (`tf2_msgs/msg/TFMessage`), `/odom` (`nav_msgs/msg/Odometry`); QoS `ros2 topic info -v` 실측. LaserScan은 sensor-data QoS 구독.
- Planner: `/compute_path_to_pose` (`nav2_msgs/action/ComputePathToPose`)에서 원본 `nav_msgs/msg/Path` 추출, original request/result UUID·header(frame/map, stamp)·costmap source와 연관; RViz Path 발행은 **read-only copy**만 허용.
- CM: 설치 공식 `nav2_collision_monitor`의 실제 `/scan` 또는 기준선의 `/safety/scan` remap 입력; `/cmd_vel_smoothed → Supervisor → /cmd_vel_supervised → CM → /cmd_vel` 실제 토픽 그래프/단일 publisher 확인. NO_GOAL에서 실제 Twist/Goal 발행 금지. isolated CM 합성 Twist 테스트는 **로봇 주행과 별도**.
- 타이밍: ROS header skew <=50ms; host monotonic 입력 age <=0.5s; `/clock` 진행/TF freshness; scan/control/CM source→observer 전달 주기 및 **첫 gap** 수집. 서로 다른 시계 기준은 변환 근거 없이 합성하지 않는다.
- 수치: 0.65m SLOW, 0.30m STOP은 **Gazebo set_pose 목표가 아닌 실제 LaserScan 값 기준**; 2개 실제 VALID, UNKNOWN 1개, before/obstacle/restore 실제 Path 원본.
- GPU/GUI: CI Xvfb의 launch/scene 교환 증거 ≠ WSLg 3D 픽셀 인수.

## 4. 단일 개발 계열 및 작업 의존

**공개 CI 통합 브랜치:** `feat/d08-unified-sensor-cm-path-20261118` (위 CI main 시작). 이 브랜치에 실제 source/검증기/공개 Task 보고서. Student는 별도 `feat/d08-integrated-no-goal-live-20261118`에서 **공개 CI green 이후** 검증된 실행기 연동과 교육 TODO 보존. Instructor는 `docs/d08-unified-teacher-guide-20261118`에서 비공개 참조/가이드만. 상호 SHA pinned; 서로의 private 파일 복제 안 함. **main 병합 자동 금지.**

| 순서 | 최소 변경 파일/산출 | 최소 RED | GREEN 실제 증거 |
|---|---|---|---|
| 00 | `d08/harness` 기존 world/probe + 공개 L0 world/graph 계약, report | 2 worlds, 다른 domain, blank scene, fake scan, cmd_vel 중복 | 한 SHA·World·Robot·Proxy, 정확한 센서/scan/clock/TF/odom 및 Nav2/CM 토픽 Provenance, 기존 L2 영향 보존 |
| 01 | `d08/harness/d08_live_readonly_probe.py` 재사용/최소 개선, `d08/tests` 1~3개 + report | 실제 valid 0 / skew>50ms / stale / no person | 실제 동시 RGB/Depth/YOLO bbox ROI 2 VALID 다른 거리 + 1 UNKNOWN, age/stamp/registration 근거, otherwise HOLD |
| 02 | 기존 `d08_public_gazebo_l2.py` + D07 official Planner loop 선별, D06 official CM read-only 연결, Public workflow + report | synthetic scan masquerade / wrong world / stale TF/costmap / path provenance 누락 | **동일** Gazebo 실제 RGBD/YOLO/range/scan/Costmap/Path(before,near,restore)/official CM source + first gaps, no Goal |
| 03(조건) | `docs/reports/D08_TASK03_G07_DEPENDENCY_HOLD_REPORT_KO.md` | G07 strict moving not green | G07 별도 SHA tracer-OFF goal + source/observer<=120ms, Guard<=150ms, terminal/ACK/exit0 전부 GREEN 전에는 **HOLD만** |
| 04 | Public runner + Student/Instructor 가이드/원샷 + SHA256/verdict/trace/report | 잘못된 SHA, private 유출, --self-check 실제 runtime 주장, unsafe cleanup | 동일 pinned CI/Owner runner, --self-check/doctor/run, 수업 계층별 rqt_graph, exact L2 SUCCESS, WSLg 별도 |

## 5. 검증/증거/종료

- RED→GREEN→REFACTOR→REVIEW→COMMIT. 이미 성공한 독립 D06 CM L1, D07 Planner L1, D07 classroom L2, D08 GUI L2는 **정확한 SHA·계약 재사용**; 변경된 통합 PR HEAD는 공개 CI L0→필요 L1→**실제 Gazebo L2**가 별도 성공해야 한다.
- L0: bash -n/py_compile/pytest 새 실패 1~3개. L1: 실제 ROS Jazzy CM/Planner 주기/QoS. L2: 실제 Gazebo 한 World + timestamps/TF/nav2 /scan Path CM. Owner L3: 마지막에만 WSL2 WSLg 화면.
- 명령 및 실제 출력은 Task마다 보고서에 인용. `verdict.json`, `trace.jsonl`, graph, native logs, source SHA, `SHA256SUMS`, first-failure, 미검증 항목 보존. rosbag 10~30s 선택. CI artifact retention 명시. Ctrl+C는 소유한 프로세스 그룹만 중지하고 외부 폴더 삭제/강제 reset/pkill 금지.
- ROS setup은 `set +u; source /opt/ros/jazzy/setup.bash; set -u`. Owner 실행기는 GitHub 정확한 검증 SHA `curl -fL` 다운로드 + `bash -n` + `--self-check|--doctor|--run`.
- 출력 판정: **Task00+01+02+04 exact SHA 실제 검증 후에만** `D08_LIVE_NO_GOAL_ACCEPTED=YES`; Task03은 G07 strict 이전 `D08_MOVING_E2E_ACCEPTED=HOLD`; Owner GUI L3 이전 `D08_OWNER_WSLG_VISUAL=NOT_RUN`.
- 사용자 확인이 필요한 유일한 후속 사항: 최종 Owner WSL2 1회 + 세 저장소 main 병합 승인 일괄. 나머지 GitHub 조사/PR/CI/보고서 승인 요청 없음.

## 6. 현재 알려진 명확한 블로커

1. 현재 공개 D08 L2는 실제 registered RGBD + 물리 /scan 계층을 갖지만, CM isolated L1이 **synthetic /axia_ci/scan**을 사용한다. 이것을 한 월드 실제 /scan의 CM 관측 PASS로 승격하면 안 된다.
2. 현재 공개 D08 image/YOLO replay와 강사 개인 D05 실제 거리 계측을 같은 사람·같은 실시간 시점으로 연결한 2 VALID + UNKNOWN 원본 실행 증거를 아직 확보하지 못했다.
3. Student PR #36/#41은 브랜치 상태가 다르며 두 실행기의 월드/렌더/Planner가 합쳐진 동일 실행을 검증하지 않았다.
4. G07 이동 strict 최신 Green 확인 전 Task03은 별도 HOLD.

계획 수정이 필요하면 기능 수정 전에 별도 계획 수정 커밋을 남긴다.

## 7. 2026-11-18 v1.1: upstream ONNX Runtime 404로 인한 최소 CI 공급 경로 변경

- 최초 실패 증거: Public CI Run #44202916170 (HEAD a538c15a956f4bf4ff651c306a0bdafba113ce48). Real Gazebo same physical proxy + native /scan L2 job succeeded, **downstream C++ YOLO job failed**: `curl: (22) The requested URL returned error: 404` when downloading Microsoft's official ONNX Runtime 1.20.0 GitHub tarball.
- **새로운 확장 아님**: YOLO 엔진 `mgonzs13/yolo_ros` 고정 SHA `94d2dd500cb26027ee9c019f4d3a02029ac615cc`와 ONNX Runtime **1.20.0 그대로** 유지. Engine fork/새 YOLO 모델/임의 버전업 금지.
- 수정 가설: Microsoft official NuGet `Microsoft.ML.OnnxRuntime` **1.20.0** (공식 flat-container `https://api.nuget.org/v3-flatcontainer/microsoft.ml.onnxruntime/1.20.0/microsoft.ml.onnxruntime.1.20.0.nupkg`)의 linux-x64 runtime .so와 해당 버전 C++ headers를, 원본 vendor의 `-DONNXRUNTIME_ROOT` 지원으로 전달. NuGet asset은 HTTP/ZIP 검사, package metadata ID/version, include/lib ABI & ELF 점검 및 파일 SHA256 로그를 통과한 경우에만 사용. 단순 HTTP 200이나 파일 존재만으로 build/ROS PASS 금지.
- RED: GitHub tarball 404 및 6MB 미만 HTML/비 ZIP, 잘못된 NuGet package/version/arch, lib·header 누락; upstream 에러를 Gazebo 센서 FAIL로 잘못 판정하는 오류.
- GREEN: 공식 NuGet 1.20.0 정확한 pkg 바이너리 재사용으로 pinned C++ `yolo_ros` build, 실제 `yolo_msgs/DetectionArray` 생성까지 PUBLIC CI. 기존 실제 Gazebo RGB 재생 L1과 같은 실행의 실시간 YOLO는 여전히 별도 계약.
- 실패 시 `D08_ORIGINAL_ONNX_ASSET_UNAVAILABLE` 또는 `D08_NUGET_ASSET_VALIDATION_BLOCKED`를 증거에 남기고 Task04 HOLD. 외부 무결성/ABI가 충족되지 않으면 새로운 모델 구현으로 확대하지 않는다.

## 8. v1.1: Task02 단일 세계 공식 Nav2 최소 launch 후보

- Official Jazzy `nav2_bringup/tb3_simulation_launch.py`는 실제 `world:=...`, `robot_sdf:=...`, `headless:=True`, `use_rviz:=False`, `use_composition:=False` 인자를 지원한다. **새 두 번째 Gazebo 없이**, 기존 D08 `build_overlay` 결과를 같은 공식 launcher에 주입하는 opt-in 실행 경로만 검토한다.
- 기존 D08 단독 Gazebo L2는 변경하지 않고 보존; opt-in 통합 분기는 검증된 D07-H01 물리 proxy/공식 planner 경로와 provenance를 일치시킨다.
- 우선 실제 공식 Nav2 launch의 named Waffle spawn, /scan·/clock·TF·/odom, lifecycle, `ComputePathToPose` read-only 경계 **최초 실패 1개**만 L0→ROS L1→Gazebo L2로 평가. 준비되지 않은 경로에서는 GOAL/속도 발행 및 통합 PASS를 금지한다.
- D06 실제 CM /scan input은 격리 output/read-only로만 구독 관찰하며, 기존 isolated synthetic CM L1 결과를 승격하지 않는다.
- G07 Moving strict 및 Owner WSLg 진입 게이트 변경 없음.

## 9. v1.2 — 실제 Nav2 공식 AMCL 초기위치 실패 경계 / CI 격리 (2026-11-18 KST)

- 최신 실제 RED: Public PR #166 HEAD `94b5cc892041116192f50c63b279c3ddf234062c`, [Run #44208629430](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44208629430). 기존 Gazebo Human/RGB-D/Scan + isolated CM 실제 L2 구간 PASS, 별도 **같은 D08 world**의 공식 Nav2 `/compute_path_to_pose` Action은 `STATUS_ABORTED(6)`. 원본 native launch에서 최초 원인 `AMCL cannot publish a pose ... Please set the initial pose`, `map frame does not exist`, `Unable to get start pose`. 종료 후 planner SIGABRT/exit -6는 최초 원인이 아닌 후속 teardown 결과로 구분한다.
- **최소 수정 한계:** D07-H01의 공식 AMCL P0 실습 계약 재사용: `/map` OccupancyGrid 실제 셀 검사, 유효 /clock, 기존 실제 Waffle spawn map 좌표 `(-2.0,-0.5,0)`, `/set_initial_pose` 공식 `nav2_msgs/srv/SetInitialPose` 단 한 번, `/amcl_pose`와 `map→base_link` 실제 TF 확인 뒤 읽기 전용 `ComputePathToPose` 요청. `/initialpose`는 localization 초기화일 뿐 NavigateToPose/FollowPath/속도명령이 아니다. 서비스 ACK만으로 AMCL/TF 성공이라고 주장하지 않는다. map free-cell 및 TF를 검증할 수 없으면 즉시 HOLD; 임의 TF/fake pose 주입·타임아웃 완화 금지.
- **CI 개선:** 이미 성공한 Gazebo 독립 센서/physical Proxy + YOLO replay L1 작업은 보존하고, 새로운 AMCL/Nav2 first-Path 후보는 **별도 L2 job**으로 분리하여 해당 실패가 기존 독립 센서/YOLO regression을 SKIP시키지 않게 한다. 서로 다른 두 job의 센서/Yolo/Path 데이터를 단일 인과적 E2E로 붙여 PASS라고 보고할 수 없다. 완전 결합은 추후 하나의 Nav2+CM+YOLO sensor runtime에서 별도 확인.
- RED: Action STATUS_ABORTED(6), AMCL 미초기화, map 좌표 위험 셀, map→base_link 미검증, GitHub YAML heredoc 재발; GREEN: 공식 map/AMCL/TF 수신 원본 + 해당 RUN의 valid official Path 원본. 실제 이동 Goal 금지.
- 현재 C++ pinned upstream `yolo_ros` 자체는 Run #44206496600에서 빌드 성공했으나, `DetectionArray` 0개라 ROS 런타임 출처 로그 진단 중. 이 오류는 공식 Nav2 AMCL 오류와 별개다.

## 10. v1.3 — D08 실제 한 World 공식 Path L2 성공, 다음 3상 장애물 계획 재사용

- 공개 CI [Run #44210297492](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44210297492), PR HEAD `ffff73105abb05290d618d6f912ac4fb7af8a404`, 실제 체크아웃 provenance SHA `098dba8081371adfa80d349454849c343d19b308`, World default, ROS_DOMAIN_ID=69, GZ_PARTITION=`axia_d08_ci_9968`: 실제 registered RGBD + 물리 사람형 Proxy + 원본 /scan, 공식 AMCL P0 service ACK, /map 자유 셀 16개, 실제 `map→base_link` TF, 공식 `ComputePathToPose` 14 Pose, 0.400m에서 단일 before Path **actual L2 PASS**. 사용자 Goal/명령 발행 없음. 다른 독립 CI job과 영상·값을 이어 붙이지 않는다.
- 최신 D07-H01 학생 공개 CI [Run #44051183220](https://github.com/silverbjin/axia-robot-safety-student/actions/runs/44051183220) **실제** 기하 기준(reference, 이번 D08 L2 아님): 같은 TB3 sandbox, Waffle spawn (-2.0,-0.5), 공식 map goal (-1.7,0.7), 물리 Proxy `axia_p2_g07_obstacle`를 far (-0.58,-0.5) → 같은 기존 공식 Path 내부 좌표 (-1.979118934,0.171291396) → far 복귀. 해당 RUN의 공식 before/intrusion/restored Path 52 Pose, 실제 global costmap lethal 0→92→0, D07 별도 L2. 전체 D07-H01 알고리즘 복사 금지, **검증된 세 좌표와 표준 Nav2 action/source schema만 최소 재사용**.
- 다음 Task02 최소 통합 목표: **한 새로운 D08 실제 Gazebo 실행 내부에서** 같은 물리 Proxy native set_pose 3상, 각 구간 실제 /scan header·host monotonic 첫 gap 및 공식 global costmap 원본 timestamp가 진행한 뒤, 공식 `ComputePathToPose` Path before/intrusion/restored를 읽는다. Goal map (-1.7,0.7)은 단위 후보, 실제 장애물이 경로 밖/invalid map이면 원본 evidence와 HOLD; 정적 순서대로 set_pose 한 것은 새 경로 증거가 아님.
- **카메라 시야 중요:** D07 경로 침입 위치는 로봇 전방에서 거의 측면(각 ~1.54rad)이고 D08 RGBD HFOV 2.20rad 범위 밖일 수 있다. 따라서 전방 Depth person VALID 단계와 측면 Path 동적 변화 단계는 **동일 World/동일 Proxy/동일 RUN의 순차 상태**로 명확히 설명한다. 영상 person이 계속 추적됐거나 직접 CM에 제어 신호를 줬다고 주장하지 않는다. 측면 YOLO UNKNOWN이면 CLEAR/이동허가는 아님.
- 공식 Nav2 launch에는 `collision_monitor`와 global `obstacle_layer.scan`이 포함됨이 native 로그에서 관찰됨. 그러나 실제 수신 QoS/주기·첫 gap·state를 아직 증명하지 않았으므로 별도 read-only ROS graph probe 필요. 기존 synthetic CM isolated L1을 실제 /scan CM PASS로 승격 금지.
- RED: 서로 다른 World/Proxy, 잘못된 D07 좌표를 SDF 입력값으로만 PASS 처리, 오래된 scan/costmap/TF, native Action result ABORTED, 단계별 경로 원본 분실. GREEN: 실제 ROS source stamps + callback monotonic gap + costmap epoch + before/near/restore 원본 Path + 동일 SHA/World + NO_GOAL.
- 이 확장은 교육용 세 경로 관찰에 한정하며 복잡한 범용 경로 탐색기/새 Planner/상용 안전 타이밍 개발은 하지 않는다.

## 11. v1.4 — 실제 YOLO ELF loader 실패 해소만 허용

- Public Run #44210297492, source HEAD ffff73105abb05290d618d6f912ac4fb7af8a404의 원본 C++ YOLO native log: `yolo_node: error while loading shared libraries: libonnxruntime.so.1: cannot open shared object file`, **실제 node exit 127**. 외부 NuGet 패키지 SHA·C++ pinned upstream build는 PASS, DetectionArray 발행 0은 loader 단계 실패의 후속 결과.
- 최소 가설: 공식 Microsoft NuGet 1.20.0 Linux x64 라이브러리에는 `libonnxruntime.so` 파일이 존재하지만, ELF NEEDED/SONAME인 `libonnxruntime.so.1` 경로가 upstream vendor install layout에 없었다. 바이너리를 변경하거나 다른 버전을 받지 않고 **같은 SHA 검증된 실제 바이너리 파일의 soname symlink만 설치**.
- RED: 원본 exit127 log / `ldd ... libonnxruntime.so.1 not found` / package missing symlink. GREEN: 오리지널 C++ YOLO executable loader exit127 소멸, 실제 ROS DetectionArray (person >=1)와 원본 Gazebo RGB replay L1 SUCCESS. ELF `readelf -d` SONAME을 검증하지 못하면 BLOCKED, 임의 symlink명 추가 불가.
- 검증 계층 추가 금지: 기존 L0 symlink contract, 기존 공용 C++ YOLO Build/Replay L1과 실제 same-world Nav2/Gazebo L2를 사용한다. 이 YOLO replay는 **라이브 RGBD+YOLO 동시** 증거가 아니라 다음 Task01 선행 준비일 뿐.

## 12. v1.5 — 2026-11-18 Task02 실제 3상 Path·실측 Scan/Costmap (CI 별도 범위)

- 최신 D08 PASS: public Run #44211587111 HEAD `05503ecc434152ac497e3ae4b1535516a5410fc4`에서 독립 job ① Gazebo 물리 인체/RGBD/LaserScan, ② 한 World 공식 Nav2 AMCL/TF + 첫 `ComputePathToPose`, ③ 고정 upstream C++ YOLO의 **실제 Gazebo RGB 재생** DetectionArray ROS L1가 각각 성공. 서로 다른 job의 원본을 실제 단일 E2E로 승격 금지.
- 후속 필수 1차 RED/목표: 현재 공식 Nav2 job은 `before` 한 Path만 관찰한다. 기존 D07-H01 공개 L2 [#44051183220]의 검증 좌표 goal map `(-1.7,0.7)`, 인체 Proxy far `(-0.58,-0.5)`, intrusion world `(-1.9791189342778877,0.17129139623634398)`를 **같은 D08 Gazebo 프로세스의 opt-in stage sequence**에 재사용한다. 좌표가 실제 D08 scan/costmap/path에 맞는지는 새 실행에서 독립 검증해야 하며 예전 D07 PASS를 자동 승격 금지.
- 기존 센서-only·공식 Nav2 first Path 성공 경로는 보존한다. `--official-nav2-replan-phases`를 별도로 명시했을 때만 실제 `/scan` 및 `/global_costmap/costmap`의 header stamp·host receive time·phase epochs를 모으고, native `/world/default/set_pose` ACK 이후 actual Costmap lethal increase/clear 및 공식 Action 원본 before/intrusion/restored path 3건을 JSONL에 기록한다. 종료 시 반드시 original far pose로 복원. *로봇 주행 Goal*이나 Twist publisher 없음.
- 성공은 동일 ROS_DOMAIN_ID/GZ_PARTITION·source SHA/World와 각 단계를 연결한 live ROS 원본 증거에서 before↔intrusion 경로 변동 `>=0.15m`, restored↔before `<=0.12m`, /scan Costmap stamp 진행·/odom 정지·TF freshness; 최초 gap/타이밍 위반과 공식 CM 실제 /scan subscription discovery를 별도 기록한다. 실제 scan→CM 수신 주기 미계측 시 CM end-to-end PASS 금지.
- 최소 L0: ① before/near/restore 공식 Path 원본을 요구하는 판정기, ② 실제 source stamps 및 monotonic first gap 누락·stale 방지, ③ NO_GOAL/중복 publisher 금지. L2는 기존 공식 Nav2 job 한 번만 재검증; 다른 성공 job은 SHA 변화 영향 범위만 확인한다.
- 3상 기본 geometry 불일치나 CPU 부하로 clock/Scan gap이 최초 발생하면 CI 원본 evidence 보존, 최초 실패 경계만 수정한다. 안전 TTL 연장/Planner 교체/새 프레임워크 금지.

## 13. v1.6 — 동일 World 3상 L2 최초 진입 실패: AMCL→TF 구독 준비 순서

- 실제 RED: Run [#44226367924](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44226367924), HEAD `339f92df043f0b5e22212812428555ec8ee682ba`. **L0 57 passed (0.28s)**, 독립 물리 Gazebo 센서 L2 및 공식 `yolo_ros` 고정 RGB replay L1는 성공. 그러나 추가 3상 코드를 실행하기 전 공식 Nav2의 첫 Path P0 경계가 `D08_AMCL_REAL_MAP_BASE_TF_NOT_READY:AMCL_POSE_STALE`로 HOLD. 원본 증거 `d08-official-nav2-oneworld-l2-evidence` artifact #14393167386, `official_nav2_before_path.json`, native `d08_official_nav2_one_world.log`.
- 원인 **가설, 미확정:** 현재 `d08_amcl_initial_pose.py`가 `/set_initial_pose` 서비스 완료 **이후** `tf2_ros.TransformListener`를 생성한다. 정지 로봇의 공식 AMCL은 TF를 초기화/필터 처리 시 발행하므로 수신 구독 준비 순서에 따라 최초 `map→odom` 변환을 놓칠 수 있다. 참고 공식 Jazzy AMCL 원본 `https://api.nav2.org/nav2-jazzy/html/amcl__node_8cpp_source.html`, 설정 `https://ros-navigation.github.io/mkdocs.nav2.org/jazzy/configuration_and_development/configuration_guide/others/configuring_amcl/`.
- TDD: 구조적 RED는 TransformListener 생성이 `SetInitialPose.call_async`보다 뒤라는 소스 순서 회귀. GREEN 최소 변경은 동일 ROS 노드의 TF listener를 `/map`/Scan 대기 이전부터 만들고 **그 후** 공식 SetInitialPose를 1회 발행. **AMCL 1s host age, /scan·/odom 0.5s age, CM 0.15s/120ms 안전 TTL, Planner 또는 TF 값을 변경하지 않는다.**
- 실제 CI에서 다른 운영 부하나 DDS discovery 영향도 가능하므로 원인 확정은 exact-SHA 새 Run의 최초 진입 로그와 단계별 stamp/TF 증거를 보고 결정한다. 같거나 새로운 최초 경계가 발생하면 증거를 보존하고 그 부분만 수정하며 무작정 재시도하거나 AMCL·안전 TTL을 늘리지 않는다.
- 3상 L2 및 Task01 실제 YOLO+Depth 2 VALID/UNKNOWN, native CM /scan 수신/상태는 기존 HOLD 유지. 성공한 한 World 첫 Path SHA의 별도 증거는 보존한다.

## 14. v1.7 — Task01 actual one-world live YOLO/Depth person range, 최종 관측 결선 계획

- 새 증거: PR #166 HEAD d37d1a36507cfe5c99cd41f4384cc9c7cac3c5ca, public CI https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44227457087 FULL SUCCESS. 한 world에서 실제 RGBD/LaserScan, AMCL, Costmap lethal 0→73→0, official Nav2 3 Path before→intrusion→restored 및 CM 실제 /scan 구독 graph를 입증. 별도 CI job의 원본 Gazebo RGB replay에서 pinned C++ yolo_ros Person DetectionArray도 입증했으나 동일 프로세스 동시성/실제 D05 거리 결선은 미검증.
- 목표는 새 YOLO/D05/Planner 재구현이 아니라 **동일 world와 동일 physical Proxy를 공유하는 경량 public read-only ROS adapter 결선**. 기존 d08/harness/d08_public_person_range.py의 0.05s stamp skew·0.5s steady age·동일 optical frame·32FC1 4x4 ROI median을 그대로 사용한다. 인지 엔진은 exact pinned upstream yolo_ros SHA 94d2dd500cb26027ee9c019f4d3a02029ac615cc, Microsoft NuGet ONNX 1.20.0 verified SHA. Student TODO/Instructor sealed answer 무변경.
- 기존 YOLO L1 job은 오리지널 Gazebo RGB replay의 SUCCESS를 보존하고, 그 job에서 이미 설치한 C++ upstream overlay·pinned model을 재사용해 **새 하나의 Gazebo Harmonic + official Nav2 + same physical person**을 실행한다. 여기에 YOLO를 use_sim_time true로 구동하고 실제 live Gazebo registered RGB/Depth→actual DetectionArray→D05 관측을 수행한다. 동시 구동 센서 World가 시작된 뒤부터만 triad를 인정; 별도 job 데이터와 합쳐 E2E PASS 금지.
- 최소 3개 실제 stage: physical Proxy slow (-1.43,-0.5,.24)에서 첫 VALID, stop (-1.63,-0.5,.24)에서 두 번째 실제 VALID 및 0.12m 이상 거리 차, 카메라 측면 외부 (-1.979118934,.171291,.24)에서 실제 RGBD·YOLO callback과 reasoned UNKNOWN(사람 class 없음). 원본 native set_pose ACK + actual new ROS LaserScan/camera frame과 monotonic 받은 시각을 함께 보존, 완료·실패 관계없이 far(-.58,-.5,.24)로 원상 복귀.
- RED: 이전 실제 Owner 유효 거리 0개 / real ROS triad stamp·frame·stale 경계 및 손실; L0 mock fixtures가 ROS success를 증명하지 못함. 먼저 public test source-only 실제 RED로 adapter 부재 재현, 다음 최소 GREEN. 이미 SUCCESS인 이전 Gazebo/YOLO 분리 시험의 근거 SHA/아티팩트를 보존하고 바뀐 동시 경계 L2만 추가 검증.
- live YOLO/Depth로 인해 기존 실제 Scan wall gap 500ms 상한, AMCL/TF 및 official CM /scan QoS/cadence에 최초 위반이 생기면 FAIL-CLOSED/HOLD; safety TTL 완화 금지. CM state 미발행 및 실제 감속 미실행은 표시하되, 테스트용 합성 cmd_vel을 실제 /cmd_vel로 배선하지 않는다.
- 새 결선에서 원본 ROS Graph·tf/clock·2 VALID+UNKNOWN과 공식 Path 3상이 동일 GZ_PARTITION / ROS_DOMAIN_ID / SHA로 확인돼야 Task01/Task02 교육형 완성 후보. 화면 픽셀/Owner WSLg와 G07 moving strict 인수는 여전히 별도 조건.
- 한 CI 실행기의 동일 public SHA 원샷을 Student/Instructor 가이드에 반영하고, owner L3 마지막 한 번 + main 병합은 최종 승인 전까지 하지 않는다.

## 15. v1.8 — 2026-11-18 실제 D05 깊이 ROI 물리 불일치 첫 경계 / 1회 최소 후보

- Public CI [#44229304083](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44229304083), source feature SHA d06c00a3846b1fcdcc8a5f3532b54a523de78283: L0 75 PASS, 독립 Gazebo sensor job PASS, original YOLO C++ replay L1 PASS. 새 **같은 World** 한 번의 Gazebo/Nav2+실시간 YOLO에서 Scan/Costmap 공식 3 Path PASS, RGBD/YOLO/Depth 실제 VALID 2건 및 사유가 있는 UNKNOWN 1건을 확보. 다만 실제 두 VALID ROI가 물리적으로 서로 다른 거리를 일관되게 반영하지 않아 `D08_TWO_ACTUAL_PERSON_DISTANCES_NOT_DISTINCT` HOLD.
- 원본 동일 World 로그/아티팩트 #14394487446:
  - slow native person(-1.43,-.50,.24): 실제 /scan 0.559762m, person confidence 0.254660, bbox XYXY (162,92,458,380), valid Depth pixels 11/16, ROI median 0.475343m, RGB/Depth/Detection stamp 모두 18.801s.
  - stop native person(-1.63,-.50,.24): 실제 /scan 0.362725m, person confidence 0.549731, bbox (116,25,499,105), valid pixels 10/16, ROI median **0.534589m** (더 가까워졌으나 증가), stamps 25.401s.
  - Side unknown: actual 4 registered RGBD + 4 YOLO DetectionArray, `NO_PERSON_CLASS_IN_ACTUAL_YOLO`, stamps 30.402s; 2 VALID/1 UNKNOWN **자료 전달 자체는 입증**.
  - Stop bbox 세로 80px(480px 이미지의 16.7%)로 Slow 288px 대비 상단 일부만 검출. 사람 전신 ROI와 물리 Proxy 연관성이 부족한 후보로 판단. 원인은 **아직 확정 아님**. 같은 frame ID+stamp는 정확한 사람 물리 거리의 증명이 아님.
- minimal RED/진단: 기존 두 실제 VALID가 감소 방향·유의미한 간격을 만족하지 못한 원본을 L0 계약에 편입: `slow_distance > stop_distance` and `slow-stop>=0.12m`, 절대 차만으로 거꾸로 측정한 결과를 PASS로 승격 금지. 각 VALID의 실제 16개 Depth ROI(float32)·RGB frame PPM·bbox 원본·stamp/host age·LiDAR를 SHA256 묶음으로 저장. 새로운 tracker/학습/인공 깊이 금지.
- 한 개 물리 후보만 조정: 첫 유효 거리 단계의 물리 Proxy를 x=-1.20,y=-0.5,z=.24 (기존 x=-1.43 대비 0.23m 먼 장면; LiDAR 후보 약 .79m)로 이동하여 확실한 거리 분리 여유 확보. **측정 전 위치 후보 ≠ 실제 측정 거리**, 실제 Scan으로 증명. 두 번째 Stop x=-1.63과 UNKNOWN 측면 위치/기존 World/YOLO 엔진·confidence threshold·Depth median 알고리즘은 그대로. 더 먼 위치에서 Person 검출 실패하면 새 원본 증거로 HOLD하고 모의 sample/threshold 완화 금지.
- 동시에 새 same-world combined job이 공식 Nav2/Costmap/Path 3상 모두 PASS했는데 별도의 **이미 검증된 독립** Nav2 첫 Path job이 `D08_OFFICIAL_NAV2_PLANNER_UNAVAILABLE`로 실패. 해당 job 원본에서 `/controller_server/change_state` service 응답 timeout 경고가 먼저 기록; 공식 Nav2 GitHub Issue #6556도 lifecycle response timeout vs actual state 확인을 제안함. 원인 확정 아님. **중복 독립 Nav2 L2를 일반 push에서 재실행하지 않고 opt-in workflow_dispatch 진단 전용**으로 두어, 새 combined same-world job 자체의 Nav2/Path 3상 실증이 유일한 release gate가 되게 한다. 기존 센서/YOLO replay L1은 model pin 확인 용도로 보존하며 성공 증거 합성 금지.
- CM 공식 Scan subscription graph는 확보했지만 CM 내부 첫 Rx gap/Guard age/CM state는 NOT_VERIFIED. Scan 0.5s 안전 관측 상한과 Guard/CM TTL은 늘리지 않는다. G07 moving strict/Owner GUI 추가 개발은 게이트 통과 이전까지 보류.

## 16. v1.9 — 2026-11-18 실제 AMCL Pose/TF의 정지 로봇 갱신 의미와 최소 초기화 게이트 수정

- 최신 새 후보 `8e0c3c2340319ac7b374c345ea42d2b525598453`, 공개 [Run #44231766775](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44231766775): L0 79 passed, Gazebo sensor L2 PASS, 단일 live YOLO/Depth 통합 L2는 본격 ROI 측정 전 **`D08_AMCL_REAL_MAP_BASE_TF_NOT_READY:AMCL_POSE_STALE`**로 종료 (evidence artifact #14395254641). 실제 Nav2/AMCL 서버는 ACTIVE. native log: initialPoseReceived sim 8.247s, map→base_link TF가 다음 scan 뒤 sim 9.301s에 등장, planner_server는 1.1s 뒤 활성화. ROS/CM 안전 TTL 또는 Depth 입력 오류라는 증거는 없음. 당시 source SHA는 PR feature HEAD와 별도로 실제 Actions checkout `5811c7688ac0a880cb79c631c0bbbd5c3e206eb3`, ROS_DOMAIN_ID=69, GZ_PARTITION=axia_d08_ci_12493.
- **공식 Jazzy AMCL 소스 확인** `ros-navigation/navigation2@jazzy:nav2_amcl/src/amcl_node.cpp` commit-blob `e9c29ccac44b927e0687ee2ca16ed5cc27b3ba64`, L693–748: AMCL은 filter resampling/first pose 때 `publishAmclPose`, 정지 이후에는 `latest_tf_valid_`이 있으면 **새 `/amcl_pose` 없이 이전 map→odom TF를 현재 LaserScan stamp+transform_tolerance로 재발행**. 정지 중 새 /amcl_pose가 계속 발행될 것을 요구하는 기존 1s *현재 상태* 게이트는 공식 동작과 충돌할 수 있음.
- **단일 근본원인 가설:** 이전 검사기는 `AMCL pose host age ≤1.0s`와 최신 map→base_link TF 수신을 동일 루프 반복마다 동시에 요구하여, 최초 신뢰 가능한 post-request AMCL pose가 1s 뒤 TF가 준비될 때 먼저 stale 됨. 이 검사는 물리 센서/CM 안전 TTL와 별개이며 정지 AMCL Pose의 **one-shot 증거**를 실시간 구독 주기로 오해함.
- RED L0 2종: `/set_initial_pose` 이후 **최초 실제 /amcl_pose (map frame, nonzero stamp, host age at callback≤1s)**를 one-shot latch로 기록해야 함; 그 다음에는 실제 현재 /scan 및 /odom 최신 host age≤0.5s와 TF2의 `map→base_link` 존재·frames·stamp를 요구. 1s 지나도 새 Pose가 없다는 이유만으로 false STALE 금지, 하지만 최초 AMCL sample 자체가 없으면 절대 PASS 금지.
- GREEN 최소: 동일 `d08/harness/d08_amcl_initial_pose.py` 하나만 수정. TF listener는 이전 성공 수정대로 SetInitialPose 전에 생성. 서비스 1회, synthetic Pose/TF 없음, 최초 AMCL callback 수신 시각/원본 stamp, 최초 TF 수신 host 시각/원본 stamp, 현재 Scan/Odom 각 receive age, source frames와 최대 수신 gap 진단 필드를 저장. 기존 `/scan`·`/odom` 0.5s 센서 TTL 및 CM/Guard 기준선 120/150ms는 유지, AMCL pose callback 도착 당시의 1.0s 신선도 유지; 실제 lidar/path 데이터의 안전성을 검증한 것으로는 승격하지 않음.
- 같은 오류가 계속되면 loop 장시간의 결과 문자열이 아닌 **최초** `AMCL_pose_received`, `TF_received`, `scan/odom freshness`에서 끊긴 지점을 CI 원본으로 관찰하고 한 가설만 수정. 재요청·TTL 연장·무작정 sleep/retry 금지.
- 통합 다음 관문: 같은 source/World에서 기존 Depth 첫 단계 거리/방향과 2 VALID/1 UNKNOWN 및 동일 run 3 official Path가 모두 통과해야 NO_GOAL 후보. Task03 G07 moving strict/Owner WSLg는 여전히 별도 HOLD/NOT_RUN.
