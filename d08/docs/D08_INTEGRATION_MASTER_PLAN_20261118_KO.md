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
