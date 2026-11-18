# D06/G07 WSL2 PRE-GOAL LiDAR 최초 실패 → 공개 CI 증거 중심 검증·출고 실행 프롬프트

## 역할과 범위

당신은 ROS 2 Jazzy, Gazebo Harmonic, Nav2, TurtleBot3 Waffle, WSLg OGRE2 GPU LiDAR, DDS 안전 TTL과 공개 GitHub Actions 검증 전문가다. MVP 라이브 시연의 기존 G07 Task04 공식 Goal·CM·Guard·S02 Contact·RViz 경로만 재사용한다. **새 Goal publisher, CM/Guard 우회, LiDAR 데이터 보정/대체, 임의 목표거리·TTL 완화, Nav2 포크, 무의미한 반복 출고 금지.**

**출고 목표**는 이미 성공한 Linux Xvfb/Gazebo 시뮬레이션을 재현하는 것이 아니라, 실패한 강사 WSL2의 **실제 센서 CLEAR 조건과 센서 주기**가 공개 CI 검증 후 최종 현장에서 안전하게 확인되는 것이다.

## 첫 단계: 원본 보존과 시계열 복원

1. 원본 `d06-moving-vUavDSKf.tar.gz` SHA256 `02b2054c12bcf446733dc8b194c24bb9cc4f5562fa565ab6ca93dd4f0997b932`를 함께 업로드된 `.sha256`와 비교하고 TAR 상위 52/52 및 native 44/44 원본 체크섬을 증명한다. 원본 raw rosbag·로컬 환경정보는 공개 repo에 업로드하지 않는다.
2. 실제 SQLite CDR `/scan`과 `/safety/scan`을 읽고 원래 `sector_min()`의 정면 ±0.18rad·측면 `atan2(.75,.19)` ±0.12rad로 전·측면 최소 거리를 계산한다. **사용자 원본:** safety scan 337개, CLEAR 0개; 중앙값 front 0.526377m, side 0.629360m; 모든 유효 360 beam이 0.4~0.85m 범위인 비율 1.0; 원래 요구는 front>0.75m, side>1.20m. 원본 측정 이상 여부는 로직을 통해 검증하고 조건을 낮추지 않는다.
3. 실제 첫 safety 상태를 추적한다: `BOOT_SAFE`, Guard `NO_FRESH_PAIR`(초기), `FORWARDING_MONITORED_CM`(일부 구간), Guard latched=false; Collision Monitor의 `AXIA_StopFront` polygon stop은 로그에 존재한다. Scan callback gap 최대 0.819175초는 Scan TTL 0.300초를 초과한다. 이 위반과 최초 `OWNER_PREGOAL_NOT_CLEAR_BEFORE_FIXTURE`를 구분해 기록한다. 실주행 Goal은 **0회**.
4. 현장 WSLg OpenGL D3D12 (Intel Iris Xe); CI native Xvfb는 다른 렌더러이다. **360도 전방위 근거리값은 GPU LiDAR/OGRE2 렌더 이상 또는 로봇/월드 기하 문제의 진단 가설이지 원인 확정이 아니다.** 공식 Gazebo GPU LiDAR/WSLg 이슈를 조사하되 임의 필터로 제거하지 않는다.

## RED → GREEN → REVIEW 순서

A. **공개 L0 RED**: 기존 실제 `p2_g07_owner_pregoal_l2.py`에는 실패 직전 scan front/side/360방향 근접 비율을 산출·보존하는 기능이 없어 정확한 원인을 사용자가 알 수 없다. 증거 기반 함수의 부재를 CI에서 RED로 확보한다. 실제 G07 코드를 import해서 검사하고, 별도의 가짜 Goal/scan publisher는 작성하지 않는다.

B. **최소 GREEN**: 기존 `/safety/scan` subscriber 콜백에 수동·읽기 전용 360도 near fraction 기록과 `diagnose_pregoal_baseline()`을 추가. 실제 pregoal 점검에서 Gazebo `set_pose` 이전 `owner_pregoal_baseline.json` 원본 근거를 저장하고 `FRONT_AND_SIDE_NOT_CLEAR`·`ALL_AZIMUTHS_NEAR_UNEXPLAINED` 등을 원인으로 출력한다. 기존 front>.75, side>1.2, 두 개의 post-ACK LiDAR, stationary odom, native set_pose, TTY Goal owner authority를 **그대로 유지**하고 unsafe면 Goal 이전 HOLD.

C. **회귀 추가**: 비식별 실제 수치 fixture로 337/337 비-clear와 Scan 0.819s>TTL0.3s를 검증하고, WSLg 렌더링이 원인이라는 과도한 주장과 0/14-topic 가짜 성공을 금지. 기존 성공 경계와 음성 케이스 (missing/nonfinite, 경계값, 후속 goal absence)를 포함하되 MVP 범위 이외로 확장하지 않는다.

D. **동일 소스 실제 Native L2**: 수정된 Student SHA로 기존 Gazebo+RViz+Nav2 한 Goal 워크플로 전체를 공개 CI에서 1회 검증한다. 같은 세션에서 `/clock`, scan/odom, CM 실제 RMW source+observer<=120ms, Guard native CM age<=150ms, Scan<=300ms, Contact0, 동일 UUID Goal 취소 ACK, odom STOP 1초, SQLite14 actual messages, Nav+Loc lifecycle ACK, CM clean exit0을 엄격하게 확인한다. 이 CI 성공이 WSLg D3D12 센서 정확도를 **증명하지 못함을 기록**한다.

E. **실제 WSLg renderer 원인 구분**: 기존 강사 WSL2에서 적어도 **한 번의 NO_GOAL 진단**으로 동일 월드·Waffle LiDAR의 정면/측면/360방향 near fraction과 시각적 world↔LiDAR 일치를 확보한다. Intel D3D12와 RTX 2060의 NVIDIA D3D12 선택을 비교한다면 기존 `MESA_D3D12_DEFAULT_ADAPTER_NAME`의 전후 `glxinfo -B` 실제 출력을 확인하고, 단순 GPU 선택이 아니라 실제 두 개 이상의 fresh scan과 Scan TTL300ms를 검증해야 한다. 이 현장 실측 이전에는 원인 해결/PASS 또는 안전 주행 출고라 선언하지 않는다.

F. **출고 게이트**: 어떤 하드웨어 모드에서도 실제 전방>0.75m·측면>1.20m 및 scan 주기/TTL이 통과하지 못하면 `D06_GAZEBO_LIVE_RELEASE=HOLD`. 수동 Goal 인가 절대 우회하지 않음. 공개 CI L0/L2 GREEN뿐이면 새 현장 안전 주행 실행기 **배포 금지**; 필요한 경우 사용자가 한 번에 수행하는 ROS/Gazebo NO_GOAL 진단 명령만 제안한다.

## 최종 보고 필수

각 사이클 RED/최소 GREEN/REFACTOR/REVIEW/COMMIT, repo·branch·commit, file path, 실제 CI job URL 및 로그 출력을 기록하고 미검증 항목과 WSLg 실제 성능 차이를 분리한다. 이미 통과한 독립 테스트 반복 금지. 로컬 WSL2 첫 오류 발생 시 원본 TAR를 보존하고 CI 재현 가능 부분부터 수정. 강사 정답 private/학생 TODO separate; main 병합 전 사용자 승인. SW 정지 ≠ 인증된 E-Stop; 전체 `AXIA_MVP_DEMO_ACCEPTED=HOLD`는 최종 Owner L3 전까지 유지한다.
