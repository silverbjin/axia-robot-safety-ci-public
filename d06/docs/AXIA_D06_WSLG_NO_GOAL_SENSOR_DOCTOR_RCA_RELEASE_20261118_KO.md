# AXIA D06/G07 — WSLg LiDAR 360° 근거리 첫 실패와 안전한 NO_GOAL 진단 실행기

문서: 2026-11-18 KST | RED → GREEN → REFACTOR → REVIEW → COMMIT | MVP 범위 유지

## 1. 처음 실패한 현장 원본

- `d06-moving-vUavDSKf.tar.gz`, SHA256 `02b2054c12bcf446733dc8b194c24bb9cc4f5562fa565ab6ca93dd4f0997b932` 및 동봉 .sha256 일치.
- TAR 내부 SHA256SUMS 상위 52/52, native 44/44 PASS. 원본 원시 BAG/WSL2 호스트정보는 공개 저장소에 복제하지 않음.
- 337개 유효 `/safety/scan` 각 360빔 전부 0.4~0.85m 집중(100%), front median **0.526377m** (원래 strict >0.75m 불합격), side median **0.629360m** (원래 strict >1.20m 불합격); 0/337 CLEAR. 실제 `/clock` 11,299, `/odom` 941. 단일 Goal 0.
- Supervisor Scan callback max gap **0.819175s**는 원래 Scan TTL **0.300s** 위반, 초기 Collision Monitor `AXIA_StopFront` STOP 관찰, Guard latch false. 첫 Demo 실패 `OWNER_PREGOAL_NOT_CLEAR_BEFORE_FIXTURE`은 **올바른 안전 차단**. SW Stop != 인증된 E-Stop.
- WSLg 원본 `D3D12 (Intel Iris Xe)`; 원인 후보: OGRE2/GPU LiDAR+Mesa d3d12 드라이버, 세계/world geometry, 로봇 self-detection, DDS·스케줄러. 실제 근거가 없으므로 GPU 원인으로 확정 금지.

## 2. 최초 RED→GREEN 및 기존 성공 증거

- 과거 Student 최초 미계측 G07 수정: 공개 RED #44280935165 → 최소 near-ring 읽기 전용 원형 증거 코드 + native 4-field scan tuple 불변조건 회복.
- 과거 공개 `9/9 L0 PASS`: [#44282796951](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44282796951). 기존 공개 실제 Gazebo/RViz/Moving Goal 21-gate [#44282820380](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44282820380) PASS, Linux CI 초기 front1.405655m side2.519770m. 이 결과를 **현장 WSLg 안전 통과로 승격하지 않음**.
- 이번 작업의 새 별도 NO_GOAL Runner는 기존 `p2_no_goal_smoke_ci.sh`를 복제하지 않고, `AXIA_G07_OWNER_SENSOR_TRUTH_NO_GOAL=1`에만 명시적으로 분기. `GITHUB_ACTIONS=true`와 전용 CI-ONLY `AXIA_G07_CI_SENSOR_TRUTH_NO_GOAL=1`은 Linux CI에서 실제 NO_GOAL 진단 검증만 허용하며 **Moving Goal 권한은 0**. Owner는 진짜 WSL2 커널+DISPLAY를 요구, CI 권한과 혼합 불가.
- 기존 D07 H01 실험용 Gaussian noise-free Waffle overlay **재사용 금지**: 실제 Owner G07 공식 world+임시 물리 cylinder+정품 Waffle 10Hz SDF를 재사용. ROS 2 Nav2 Lifecycle staged startup, Xacro→Gazebo 유효 SDF 준비, 기존 Gazebo 서버에 별도 `gz sim -g` + RViz read-only client를 재사용.
- 신설 `tools/g07_wslg_no_goal_sensor_probe.py`: 실제 ROS `/safety/scan`, `/scan`, `/odom`, `/clock`을 **읽기 전용**으로 20초간 수집. 360도 0.4~0.85m 집중, front/side, 원본 Header 간격과 host monotonic callback 간격, 첫 300ms 위반, stationary odom 및 Clock 증가를 독립 기록. `Goal/Velocity/Fault/set_pose` 발행 0. 기록 `native/g07_wslg_sensor_truth.json`은 실제 ROS 원형 숫자; unsafe면 RC3/NO_GOAL/HOLD.
- `d06/scripts/axia_d06_g07_wslg_sensor_no_goal_once.sh`는 공개 Git 소스 정확 SHA와 세 핵심 파일의 Git blob을 검증한 뒤, WSL2 GPU `glxinfo -B` 렌더러와 실제 ROS/Gazebo·RViz NO_GOAL Run 원본 및 SHA256 TAR를 **비공개 강사 WSL2 경로**에 보존. 이전 쉘에 남은 `AXIA_P2_G07_OWNER_PARITY_CHECK=1`(CI-only WSL2 커널 오진), `AXIA_G07_TASK03_ECM_WITNESS=1`를 본 NO_GOAL 한정 0으로 정리. 수동 Goal 문자열 입력은 지원하지 않는다.

## 3. 이번 개발에서 발견한 소스 실행 순서 회귀

- 최초 NO_GOAL native probe [#44291784026](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44291784026): 실제 `/safety/scan` 201개, front1.413895m, side2.519858m, raw max 120.855ms, safety max 122.071ms, 정상 종료 PASS — **그러나 Gazebo/RViz GUI 창 수 검증 범위에 들어있지 않았음**. 이 성공을 전체 GUI PASS로 보고하지 않는다.
- 초도 GUI 추가 후 실측 [#44292894077](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44292894077): native sensor rc0, X11 Gazebo/RViz 0/0, **실패**. 단위 테스트 RED [#44293675089](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44293675089)는 NO_GOAL 센서 분기의 `exit`가 기존 GUI 클라이언트 연결 **이전에** 위치했음을 검출. 최종 최소 수정: 새 센서 분기를 기존 `gz sim -g`+RViz 연결/창 readiness 게이트 **이후**, Moving Goal dispatch **이전**으로 이동. GUI 준비 전에 센서를 성공으로 보고하지 않음.
- WSLg 환경에선 별도 GUI 창과 GPU 렌더러를 물리적으로 확인해야 하므로 `xwininfo` + `glxinfo`를 필요 실행 도구로 고정. 실제 D3D12 GPU 선택은 `MESA_D3D12_DEFAULT_ADAPTER_NAME`을 사용하되 이름 설정 자체는 PASS 아님.
- 단위 공개 CI는 실제 Subscriber/Observer의 순서와 안전 경계를 원본 함수로 검사. Fake CI/Owner 혼용 시 NO_GOAL 실패. 0.75/1.20m, Scan TTL300ms, CM120ms, Guard150ms 불변. 출력 성공도 `NO_GOAL_SENSOR_WINDOW_CLEAR_CANDIDATE`까지만.

## 4. 실제 CI 출고 게이트

1. Student Python 및 Bash/Launch/Git source exact pin·이전 첫 실패 회귀 **L0 GREEN**.
2. 같은 Student source의 진짜 Gazebo server + Gazebo GUI + RViz **NO_GOAL L2**: GUI X11 2창 확인 후 연속 20초 ROS `/safety/scan`·`/scan` 각 20개 이상, front>.75 side>1.20, raw/safety host receipt max<=.3초, Clock 증가, stationary odom, no Goal, 외부 프로세스 그룹 정상 종료. Linux Xvfb가 WSLg GPU와 다르다는 미검증 표시 필수.
3. 같은 source의 진짜 Task04 Gazebo+RViz+Moving Goal strict 21-gate L2: CM source/observer120ms, Guard native internal age150ms, Scan300ms, Contact0, real odom+STOP dwell1s, UUID Cancel, actual SQLite14 topics, Nav2 Navigation·Localization ACK, CM exit0.
4. **NO_GOAL WSL2 진단 출고**: 위 CI가 통과한 SHA만 읽기 전용 진단 용도로 공개. 실제 MOVING Goal 원샷 신규 배포/실물 인수는 금지. WSLg 동등 검증 결과가 나오기 전 `D06_GAZEBO_LIVE_RELEASE=HOLD`.
5. **Owner WSL2 실제 결과 미검증**: 사용자가 한 번만 NO_GOAL 진단을 실행하여 renderer, 정면/측면/near-ring, Scan callback gap 및 원본 TAR를 제출. 실제 WSLg에서 CLEAR+Scan<=300ms가 증명되고 CM/Guard 타이밍이 전체 세션에서 검증될 때만 Owner L3 Moving 인수 후보를 별도 검토한다.

## 5. 공식 참고

- https://github.com/microsoft/wslg/wiki/GPU-selection-in-WSLg
- https://docs.mesa3d.org/drivers/d3d12.html
- https://gazebosim.org/docs/harmonic/troubleshooting/
- https://gazebosim.org/docs/harmonic/sensors/
- https://github.com/iRobotEducation/create3_sim/issues/240

**선언:** main 병합 전 승인 필요, 강사 정답 비공개/학생 TODO 분리, 인증 E-Stop 아님, `AXIA_MVP_DEMO_ACCEPTED=HOLD`.


## 6. 최종 공개 CI 검증·출고 판정 (동일 Student SHA)

**고정 Student source:** `9862353e7116bc4a14a5bb365ae356642e83ef0e`; 기존 G07 CM·Guard·Goal·TTL 코드는 변경하지 않고 read-only NO_GOAL branch만 추가.

1. **RED FIRST GUI ORDER**: [#44293675089](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44293675089), NO_GOAL sensor probe의 `exit`가 GZ/RViz GUI 연결보다 앞서 있음을 실제 단위 인덱스 테스트로 재현; 이전 native [#44292894077](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44292894077)은 20초 Scan 자체는 0.12초 이하였지만 Gazebo/RViz X11 **0/0**으로 명확히 실패. 순서 문제를 GPU 느림으로 오판하지 않음.
2. **최소 GREEN**: 기존 `gz sim -g`+RViz client 연결/실제 `xwininfo` 창 준비 확인 **후** read-only sensor 20초 시작. 원래 G07 물리 world, Waffle 원래 10Hz GPU LiDAR (D07 Gaussian-noise-zero profile 사용 안 함), shared Nav2 staged startup, Xacro/Gazebo 원래 순서 그대로 재사용. 0.75/1.20, Scan TTL300, CM120, Guard150을 변경하지 않음.
3. **공개 L0 GREEN**: [#44294289112](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44294289112), public HEAD `f907dfe4b2da9fad091da4982bbc3dd237d9fd79`, 실제 **Student 6개 + D06 4개 = 10/10 PASS**. `--self-check`, WSL2 Owner가 아닌 Linux CI에서 `--run`의 RC3/no-Goal, Student SHA+Git blob, GUI-before-scan 순서, unsafe Scan 및 300ms gap·Clock·Odom/민감 데이터 보존을 검사.
4. **공개 진짜 NO_GOAL 물리 L2 GREEN**: [#44293986036](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44293986036), public HEAD `2420d3c26e111a18150ef394ebddfabcd2bf271c`, Student 정확 SHA `9862353...`. 실제 native Gazebo world 서버+Gazebo GUI X11=1 + RViz X11=1. `AXIA_G07_NATIVE_SENSOR_NO_GOAL_SMOKE_RC=0`; 실제 `/safety/scan` **197개 모두 CLEAR**, front median **1.414334m**, side **2.519027m**, 360도 near fraction median 0.297222, safety callback max **0.130253s**, raw max **0.128779s**, source stamp delta 0.102s. Odom stationary, /clock advancing, **Goal 전송 0**, `P2_L2_GRACEFUL_TEARDOWN` 및 `AXIA_G07_NATIVE_REAL_ROS_NO_GOAL_SCAN_CLEAR_TTL_SHUTDOWN_L2_PASS`. CI Xvfb/llvmpipe는 WSLg D3D12가 아님.
5. **실제 같은 Student SHA Moving Goal Safety L2 GREEN**: [#44294004552](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44294004552), public HEAD `7d36971b6c50a9f46a3499841233360140dd4a69`, Student `9862353...`, runner rc0, Gazebo+RViz 창 2개, 실제 `TASK04_REAL_GAZEBO_MOVING_GUI_L2_SCOPED_PASS` `first_failure=NONE`. 기존 엄격한 21-gate (CM source/observer120ms, Guard native age150ms, Scan300ms, Contact0, STOP dwell, 실제 UUID cancel, SQLite14 실제 메시지, Nav/Loc Lifecycle ACK/CM exit0) 유지.
6. **출고 가능한 산출물은 NO_GOAL 진단기 하나뿐**: `d06/scripts/axia_d06_g07_wslg_sensor_no_goal_once.sh`, 공개 GREEN L0 고정 ref `f907dfe4b2da9fad091da4982bbc3dd237d9fd79`, Git blob `df1c6158a07ed3139bacc451b9c452a562732929`. Owner WSL2에서 ROS2 Jazzy/Gazebo Harmonic, NVIDIA/Intel WSLg 실제 20s 센서 결과를 자동 수집하고 `~/axia_d06_g07_sensor_no_goal_evidence` 아래 원본 tar.gz + SHA256 보존. 안전 위반 시 RC3/HOLD, 정상 20s도 `NO_GOAL_SENSOR_WINDOW_CLEAR_CANDIDATE`까지만, 절대 Moving·최종 인수 PASS 아님.

**WSLg 검증 범위:** 실제 강사 MSI WSLg 센서 실측은 수정 후 `NOT_RUN`. 기존 현장 .526/.629m와 Intel renderer의 근거는 보존되지만, NVIDIA 어댑터 전환 시 원인 해결은 미증명. `D06_GAZEBO_LIVE_RELEASE=HOLD`, `AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false`. 사용자 현장 한 차례의 NO_GOAL 증거에서 actual renderer, Scan 데이터, 주기, Guard/CM 경계를 먼저 판정하고 승인 전 main 병합 금지.
