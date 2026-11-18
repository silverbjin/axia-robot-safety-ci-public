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
