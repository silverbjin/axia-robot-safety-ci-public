# AXIA G07 Cycle35 — Owner WSL2 L3 실패 및 Gazebo WSLg GUI 회귀 분석 (증거 기반)

- 작성일: 2026-11-16 KST
- 분석 유형: **진단 전용**; 신규 안전코드, Goal runner, TTL, ROS 설정 변경 없음
- 기준: `AXIA_Robot_Safety_MVP_Baseline_Scenario_Acceptance_v1_KO.md` 및 승인된 `AXIA_MVP_DEMO_ACCEPTED` 축소 프로파일
- Instructor SHA: `420fd276ec1018f7fcc3f14873693cad02f080b4`
- 공개 L2 `43824411236` PASS는 Xvfb/컨테이너 한 Goal 한정. L0 `43828818188` PASS는 **NO_ROS_NO_GOAL** 부트스트랩 회귀 한정.
- Owner WSL2 L3 상태: `BLOCKED`, `AXIA_MVP_DEMO_ACCEPTED=HOLD`, **본 보고서는 Owner 실제 Gazebo 또는 WSLg 재실행을 수행하지 않음**.
- 소스: Owner 제공 지원 번들(원본 비공개), 공개 GitHub 정확한 SHA의 소스, 공식 Gazebo Harmonic 및 Nav2 Jazzy 문서. 원본 bag, event ledger, archive, 개인 경로는 공개 저장소에 추가하지 않음.

## 1. 원본 무결성과 한계

Owner 제공 지원 번들의 SHA256 `3951bfb6e2dc05e5932f5b08bd3f5be5daba9d5cd0a065992139cd221789ffd7`. 별도로 전달된 `SHA256SUMS`·매니페스트가 일치하고 내부 59/59 항목의 SHA256도 모두 일치. 비공개 원본 아카이브 복사 SHA256 `53c1543f18d6792ebf6988d41a64140a272d2b3c3f6fac1ff09ad6060830e9f2` 검증.

`RAW_CAPTURE_INCOMPLETE`는 원본이 위조되었다는 뜻이 아니라 **S02 결과·목표 Cancel ACK·정상 종료의 완성된 인수 증거가 없다**는 의미. 이 결함을 실제 최초 운행 중단 원인으로 오진 금지.

## 2. 원본 이벤트의 실제 시간 순서

첨부 원본 `actual_ros_events.jsonl`에는 5,186개 이벤트가 있다. Monotonic 상대시간을 기준으로 한 확인된 사건:

| Goal 발행 후 | 상태 | 증거 / 해석 |
|---:|---|---|
| 0.000초 | Goal 발행 | UUID 기록, 처음 EXECUTING(2) |
| 1.167초 | **Scan Observer** 최초 300ms 초과 | 308.184ms; Goal 중 최대 369.482ms, 총 4건 300ms 초과 |
| 4.960초 | **RMW system-clock** 불연속 후보 | CM source 2,234.885ms 대 같은 Observer monotonic 55.515ms; Supervisor source 2,223.023ms 대 31.608ms. CM publication sequence는 정상 +1 |
| 5.346초 | **Supervisor/command Observer** 첫 150ms 초과 | Supervisor 150.282ms, supervised 150.234ms. 단, 실제 native Guard와 동일한 timestamp가 아니므로 직접 latch 초과 단정 금지 |
| 12.295초 | **최초 확증된 Navigation 중단** | `bt_navigator`: `Timed out while waiting for action server to acknowledge goal request for follow_path`; 이후 `NavigateToPose` ABORTED(6) |
| 12.972초 | **CM Observer** 150ms 초과 | 187.532ms, RMW source 59.048ms, receive 51.876ms, seq +1. **이미 Goal ABORTED 후**이므로 이를 최초 Goal 중단 원인으로 단정 금지 |

**별도 시계 교차 점검:** Nav2 원본 wall-clock 로그의 Goal 시작→ABORT 경과는 14.450초, 원본 Observer monotonic Goal 발행→ABORT 경과는 12.295초로 약 **2.155초** 차이가 있다. RMW의 공동 source time-step 추정 약 2.185초와 같은 방향·크기다. 각 시작·종료 이벤트의 캡처 시차가 있으므로 동기화된 하드웨어 시계 점프의 **확증**은 아니지만, 2.235초 실제 CM 중단이라는 해석보다 host clock step 가설을 지지한다. BT가 실제 사용하는 ROS clock을 직접 측정하지 않았으므로 이 시계 차이가 `FollowPath` timeout의 직접 원인인지 역시 미검증이다.\n\nGoal 중에는 CM/Guard Observer 최대 각각 약 135ms여서 동일 경계의 150ms 초과를 원본 Observer만으로 확인하지 못했다. `first_guard_latch=null`, `first_safety_transition=null`. 실제 Safety Supervisor 및 Guard의 native source→receive→callback 경계에 대해서는 공식 인수 불가. Goal 중 Scan Observer 간격 위반의 원인이 Gazebo 센서, ROS bridge, DDS, 기록 콜백 중 어디인지 확정되지 않음.

## 3. 주행 실패 직접 원인과 미증명 하위 원인

동일 Owner의 공식 Nav2 `launch.log`는 Goal 시작 후 반복적인 Controller 주기 지연 경고, 다수 `Passing new path to controller`, 이어 `FollowPath` 승인 ACK 타임아웃 → `NavigateToPose` ABORTED를 표시한다. 이어 `Failed to make progress`가 기록되었으나 **그 문구는 상위 Goal ABORT보다 나중에 출력**되므로 최초 원인이 아니다. 외부 진단 도구의 `GOAL_TERMINATED_DURING_SLOW:6` 역시 후행 판정.

가설(우선순위): (1) Goal 중 Controller/BT action goal response 처리 지연과 주기 교란, (2) GUI/센서/odom 증가로 인한 CPU·Gazebo·WSLg 렌더 부하, (3) DDS/action 응답 또는 ROS time 설정 문제. **최초 `FollowPath` goal request 송신/ACK 수신/BT timeout 임계값 및 controller thread scheduling 자료가 없어** 아래 가설의 단일 인과를 증명할 수 없음. Nav2의 timer를 무조건 늘려 PASS로 포장해서는 안 된다.

해당 source는 원래 공식 Waffle의 LiDAR `5→10Hz`, Odometry `30→100Hz`를 *임시 SDF에서만* 변경한 사실이 Owner manifest로 확인된다. 정상 데이터의 최대 전송주기보다는 end-to-end 최악 전달 주기와 Controller/BT 부하가 우선 분석 대상이다.

## 4. GUI 회귀의 유력한 도입 시점: Cycle03 (2026-11-15)

| 이전 verified 기능 소스 | 신규 통합 소스 |
|---|---|
| Instructor `db1eec05...` `scripts/p4_g07_shared_runtime.sh`: `owner-gui → headless=False` | Instructor `319f327c32f786ad331526110fd39af5a97235d1`: Sidecar 연결 시 `owner-gui → headless=True` |
| 직접 Gazebo 통합 UI | Public commit `30599879c12c7f3a1a12c14b8b39b656362fc5ed`: Gazebo server `-s` + 분리된 `gz sim -g` GUI/RViz/Marker |
| WSLg 소프트웨어 GL 옵션 기본 `0` | 공유 GUI 스크립트가 **CI와 WSLg 모두** `LIBGL_ALWAYS_SOFTWARE=1`, `GALLIUM_DRIVER=llvmpipe` 강제 |
| 정상 UI를 가정한 소스가 아님; 기존 Owner 시연 근거 유지 | 두 GUI를 **동일한 CPU0**, `nice 19`에 묶어 실행 |

첨부 `gz_gui.log`의 유일한 경고:

```text
MESA-EGL: warning: Not allowed to force software rendering when API explicitly selects a hardware device.
```

Owner WSLg에서 강제 llvmpipe와 EGL hardware-device 선택 사이의 충돌을 직접 보여 주는 정황 증거이며, **렌더링 실패 또는 심각한 부하에 관여했을 가능성이 높다**. 다만 경고 자체만으로 3D world 미수신의 유일한 원인이라고 확정할 수 없다. 동일 세션의 `GZ_PARTITION`은 측정·기록돼 있으나 서버/GUI 양쪽의 실제 `gz service -l` 및 world state 수신 검증은 없다.

**Owner CPU 역할 실제 배치:** CM 16개 thread affinity는 CPU `1,6`, Goal Observer는 `2,3,4,5`, read-only Marker Observer는 `2`, Gazebo GUI+RViz2는 `0`, Bag recorder는 `7`. CM과 Goal Observer는 직접 겹치지 않으나 **Marker observer CPU 2는 Goal Observer와 겹친다**. Nav2 Controller 및 Gazebo server의 모든 thread가 이 배치와 분리됐다는 증거는 없다. CPU affinity는 부하의 실측치 또는 병목 인과관계가 아니다.\n\nSidecar의 `display_attestation.json`: `real_gazebo_gui_window=null`, `real_rviz_window=null`, `wslg_verified=false`. **프로세스 존재는 3D scene attachment 성공이 아니다.** Gazebo Harmonic 문서도 GUI-only `gz sim -g`에서 서버가 없으면 빈 화면이라고 명시한다. 사진의 `Entity 0`은 연결되지 않은 GUI, 서버 종료 후 GUI, 렌더 path 문제와 부합하지만 어느 하나를 확정하지 않는다.

중요한 시각상의 함정: 제출된 사진명 시각 `08:21:19`는 지원 번들 `08:20:35 UTC` 이후 약 44초이므로, **이미 Owner 시뮬레이션/Sidecar 종료 후 남아 있는 빈 Gazebo window** 가능성이 있다. Nav2 주행 중에도 빈 화면이었는지는 동일 시각 스크린샷/서버 alive 증거가 없다.

## 5. CI GREEN이 왜 L3를 담보하지 못했는가

1. Public L0 #43828818188은 실행기 shell/unit 10건과 고정 소스 fetch만 검사: Gazebo/RViz/Goal 실행을 하지 않았다.
2. Public L2 #43824411236은 Xvfb Docker에서 실제 Gazebo Goal PASS이나 **WSLg hardware EGL** 및 사용자 GPU·커널 스케줄러는 시험하지 않았다. 공용 GUI 검사도 X11 window 존재로 판정하며 Gazebo Scene3D의 실제 서버/world/entity attachment 또는 실제 화면 픽셀을 점검하지 않았다.
3. CI의 CM observer 118.762ms는 120ms release 목표 대비 **1.238ms**, CM RMW source 119.499ms는 **0.501ms** 여유에 불과하다. 150ms Guard TTL을 완화해서 해결하면 안 된다. 25개 패키지/5개 파일 일치는 WSL2 CPU scheduler·GPU·DDS의 동등성을 입증하지 않는다.
4. Owner 원본의 `g07_world_manifest`에서는 `s02_read_only_witness_optin=false`, `collision_ground_truth_available=false`이므로 동일 Goal Owner native Contact 0까지 인수되었다고 주장할 수 없다.
5. `first_timing_violation=null`은 검증 성공이 아니라 Guard-latch 및 post-Goal 정상 기록이 불충분했다는 의미. Scan Observer 주기, Nav2 action 실패, RMW clock-step 후보를 별개로 보고한다.

## 6. 최소 검증 순서 — 새 Goal은 **아직 금지**

A. 공개 CI L0에 이번 비식별 숫자 기준을 편입: (a) Goal 중 Scan 308.184ms·Supervisor 150.282ms 검출, (b) RMW 2.23초 **vs** monotonic 55ms·seq+1은 CM 실제 중단으로 오분류 금지, (c) CM 187.532ms 후행 공백을 ABORT 최초 원인으로 오분류 금지, (d) Nav2 `FollowPath` ACK timeout을 실제 첫 navigation failure로 기록.

B. GUI no-Goal 회귀: 공식 Waffle/World 서버를 실제로 띄우되 Goal 없음. `headless=False` 종전 소스 GUI와 `headless=True+gz sim -g` 신규 소스 GUI를 **같은 WSLg에서** 비교. GUI의 `LIBGL_ALWAYS_SOFTWARE/GALLIUM_DRIVER`를 WSLg hardware mode와 대조. 확인해야 할 것은 window PID가 아니라 `GZ_PARTITION` 일치, `gz service -l`에서 실제 world, 해당 world의 model/robot entity, 렌더 화면/카메라 이동. 소스·환경은 manifest로 보존하고 ROS Guard/TTL/Goal은 수정하지 않는다.

C. 분리 실험으로 실제 Nav2 Action ACK 지연 원인 규명: 같은 exact world/model/SDF에서 **GUI disabled no-Goal**로 CPU/rosgraph 정상 여부를 확인하고, Goal 시험이 다시 필요해지는 변경이면 먼저 공개 CI의 실제 L2 새 source에서 `follow_path` request→response와 BT timeout, controller cycle, Scan publisher→Supervisor→CM→Guard TTL의 동일 monotonic 시간축을 수집한다. 성공한 기존 L2 반복 금지.

D. 확인된 root-cause 한 개만 최소 수정해 RED→GREEN→REFACTOR→REVIEW→COMMIT. WSLg 고유 GL 설정 변경은 CI Xvfb 녹색만으로 Owner 화면 성공을 주장하지 않는다. 이후 Owner에 **새 source/tree/Run**만 1회 허가. 과거 Owner 실패 lock/원본 보존; 동일 Goal 반복 금지.

**현재 결론:** 직접 주행 실패 `FollowPath ACK timeout → NavigateToPose ABORTED`는 확증, 최초 관찰 안전주기는 Scan 308ms 및 Supervisor 150ms 초과, CM 2.23초는 host-clock-step 후보이고 CM 187ms는 ABORT 이후다. GUI 회귀는 Cycle03의 headless 분리+강제 software GL/CPU0 변경이 최유력 코드 경계지만 WSLg no-Goal A/B 검증 전 단일 원인으로 확정하지 않음. `AXIA_MVP_DEMO_ACCEPTED=HOLD`; **인증된 E-Stop 아님.**

## 7. 검증·배포 회계

- 자료 분석: **PASS** — 제공 원본 해시 59/59 검증, 실제 ROS 로그 정적 분석, 정확한 GitHub SHA 비교, 공식 문서 확인.
- 공개 CI 회귀 추가: **NOT_RUN** (진단 계획만 작성).
- ROS 2 Jazzy 실제 런타임 신규 실행: **NOT_RUN**.
- Gazebo Harmonic 현장 GUI/Gazebo 검증: **NOT_RUN**.
- Owner WSL2 L3 재시도: **금지/미수행**.
- main 병합: **미수행**.
- Student repo 변경: **없음**.
