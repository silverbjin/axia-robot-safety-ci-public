# AXIA D06/G07 Cycle 07 — Navigation Manager SHUTDOWN 응답 경계 단일 계측 중간 보고

기준일 2026-11-20 (KST) | 공개 Draft PR #177 / 학생 Draft PR #62 | 배포 HOLD

## 1. 이전 L2에서 실제 관측된 최초 위반

공개 Jazzy/Harmonic/TB3 Waffle/공식 Nav2 NO_GOAL 같은 세션 [Run #44540963499](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44540963499), 원본 artifact #14539141620. 해당 소스 `d58bf03044f733c00e281ed14617892e4eae33d3`.

- Student Raw199/Safety201, 20.024초, 각 max119.060/119.308ms, Safety 201/201 거리 CLEAR.
- Nav2 READY 후 독립 native/ROS Scan 20초에서 300ms 위반 없음.
- **첫 종료 위반**: Navigation /manage_nodes SHUTDOWN 단일 request 전송, **40.000932초 서비스 ACK TIMEOUT**, Nav/Loc 모두 ACK 아님.
- 그 뒤 Collision Monitor child exit -11, Guard child exit1, Gazebo server exit0. 각 child 종료 실패는 독립 기록. Parent `GRACEFUL_TEARDOWN` 자체는 정상 종료 증명이 아님.
- 기존 C05 Localization /manage_nodes 30.000328초 무응답 뒤 **같은 callback group**의 /is_active는 0.027376초에 응답. `/get_parameters`도 응답했으나 서비스/요청 전달 경계를 입증하지 못함.
- 이전 C06 센서 GREEN이 전체 L2 또는 강사 NVIDIA WSLg 인수를 뜻하지 않음.

## 2. 기존 구현과 공식 근거

공식 Nav2 Jazzy lifecycle manager는 `/manage_nodes`와 `/is_active` 서비스를 같은 MutuallyExclusive callback group과 별도 SingleThreadedExecutor로 생성한다.
- 소스: https://api.nav2.org/nav2-jazzy/html/lifecycle__manager_8cpp_source.html
- 공식 서비스: https://api.nav2.org/srvs/jazzy/managelifecyclenodes.html
- 설계: https://api.nav2.org/nav2-jazzy/html/md_nav2_lifecycle_manager_README.html

이번 코드 수정은 Navigation Manager에 있는 **기존 단일 SHUTDOWN 요청을 재전송하지 않고**, 서비스가 timeout 난 경우 동일 callback group `/lifecycle_manager_navigation/is_active`를 한 번만 read-only Trigger로 조회한다. 그 사후 응답은 SHUTDOWN ACK가 아니며, 시뮬레이터 모션 허용 근거도 아님.
또한 호출자의 실제 `rclpy.utilities.get_rmw_implementation_identifier()`를 결과에 기록하여 DDS 가설 검증 시 실제 환경값과 연계한다. 미식별은 UNDETERMINED.

## 3. RED → GREEN → REFACTOR → REVIEW → COMMIT

1. **RED**: 공개 테스트 `d06/tests/test_d06_c07_navigation_manager_service_liveness.py`에 C06 Navigation 40초 timeout 재현 및 요청 1회/동일 callback group read-only 계약 추가.
   [Run #44542353540](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44542353540): `AttributeError: module ... has no attribute probe_navigation_manage_callback_group` (의도한 RED).
2. **GREEN Student**: `silverbjin/axia-robot-safety-student`, `block_B/day07/h01_runtime/tools/p2_g07_ordered_shutdown.py`, SHA `b9132d51150be31973476ac34ef97d466f17187f`. 기존 Localization callback group probe를 공통 내부 helper로 리팩터하고 Navigation 대상 wrapper와 RMW 식별 필드만 추가. Goal/velocity/fault/Scan300/CM120/Guard150 변경 없음.
3. 공개 Owner 실행기의 학생 소스 SHA가 바뀌었으므로 외부 Owner 스크립트, public L0·L2 checkout, immutable blob 회귀를 1개 원자적 커밋 `81e4d467ad1ef53950f230fc51745cecc2032a0a`로 동기화. Owner blob `3906a5e9c1a7b63a3ab639d5ffeb7f837a7405fe`.
4. **GREEN L0** [Run #44561289766](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44561289766) **128/128 PASS** (ROS-free); code SHA `81e4d467ad1ef53950f230fc51745cecc2032a0a`.
5. **실제 Gazebo L2**: [Run #44561289931](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44561289931) same code SHA에서 검사 중. 완료 후 첫 Scan 위반과 최초 Lifecycle 실패 증거를 별도 추가.

## 4. Scope와 검증 한계

- 공식 Nav2 소스 수정 없음; 관리 서비스 재전송·timeout 완화 없음.
- 이전에 성공한 Cycle06 Scan 관측은 원본 보존; 별개 lifecycle 장애와 혼동하지 않음.
- 이 사이클은 아직 **원인 수정이 아닌 원인 분리 계측**. /is_active 응답으로 ManageLifecycleNodes SHUTDOWN 성공을 주장하지 않음.
- Linux Xvfb 실제 L2 != Windows WSL2 WSLg NVIDIA. Gazebo server WSLg -11 core stack NOT_CAPTURED.
- Moving Goal, Collision Monitor120/Guard150 안전 데이터 전달 주기, 인증 E-Stop 미검증.

`D06_GAZEBO_LIVE_RELEASE=HOLD`, `AXIA_MVP_DEMO_ACCEPTED=HOLD`, `CERTIFIED_ESTOP=false`; `main` 미병합.
