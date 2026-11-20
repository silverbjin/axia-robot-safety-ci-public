# AXIA D08 — Owner WSL2 첫 Scan/Odom 수신 공백·AMCL TF 실패: 원본 기반 RED→GREEN 원인 분석

- 날짜: 2026-11-18 KST
- 개발 기준: 공개 CI `silverbjin/axia-robot-safety-ci-public` / PR #166 / `feat/d08-unified-sensor-cm-path-20261118`
- 현장 원본 소스 SHA: `a83629edd71ce51567e184451f2a76bafcf1318b`.
- 사용자가 제공한 비공개 증거 bundle SHA256: `78163b10cafad23338610cefcbe8e1c9516c829c2fff86ee0166e825b5477721`.
- 원본 압축의 `live_evidence/SHA256SUMS`: **12/12 실제 일치**. 원본 압축/rosbag/개인 경로/로그 본문은 공개 저장소로 업로드하지 않는다.
- 범위: **D08 NO_GOAL 공식 Nav2 읽기 전용 ComputePathToPose 실행 전 초기 위치 확인**. 실제 이동 Goal, cmd_vel, 인증된 E-Stop은 해당 실행 범위 아님.

## 1. 관찰된 최초 위반과 최종 오류의 차이

원본 `verdict.json`/Launch 로그 및 ROS 후속 관측을 시간순으로 비교하였다.

| 항목 | 원본 확인 | 해석 |
|---|---|---|
| D08 boot / 소스 고정 | ROS·WSLg doctor 통과, 지정 SHA 일치 | ROS/Gazebo 성공 증거 아님 |
| Gazebo + Waffle + Nav2 | 모두 실제 프로세스 시작, 실제 RGBD 640×480 RGB·Depth 0ms skew, 접촉 토픽 확인 | 센서/월드 실재 |
| Nav2 TF 초기화 | AMCL 실제 `map` 초기 Pose stamp 1.8초, 첫 source age 0.114초 | AMCL이 완전히 없었던 것은 아님 |
| **최초 실제 수신 위반** | Scan callback gap **0.819491초**, Odom callback gap **0.752105초** | 현재 0.5초 상한 초과, 원인 미분류 |
| 후속 최신 수신 | Scan callback age 0.004799초, Odom 0.000381초, 실제 TF `map→base_link` stamp 2.808초 | 해당 관찰시 다시 수신 |
| Nav2 계획 | 이전 첫 위반 때문에 `D08_FIRST_LIVE_SCAN_ODOM_GAP` 유지, ComputePathToPose 미실행 | 안전하게 차단했으나 이력/현재 가용성 혼용 |
| 종료 시 오류 | RViz rclcpp invalid context, Gazebo 종료 신호, 임시 world SDF not found | 최초 실패 뒤 종료·정리 단계 2차 메시지. 최초 원인 아님 |

실제 Nav2 로그에는 초기 `map` 프레임 부재, `base_footprint→odom` 시각 외삽, 가장 최근 2.800초 map TF보다 이른 Scan stamp의 `map→base_link` 시간 외삽 등이 확인되었다. **실제 TF는 후속으로 준비됐으므로 TF를 가짜/static으로 치환하지 않는다.**

두 수신 공백은 거의 같은 시각(Owner host monotonic 28432.08)에 기록되었다. 따라서 공통 시뮬레이션/스케줄링/Executor 정체 가능성은 있으나, 이 archive에는 동기화된 발행자 측 RMW 간격이나 /clock 단위 gap 원본이 없어 어느 계층이 근본 원인인지 입증되지 않았다. Intel Iris Xe D3D12 renderer 확인만으로 렌더러가 원인이라 단정하지 않는다. 런타임 전체 RTF도 archive에서 계산할 수 없다.

## 2. 기준선 및 단일 가설

기존 `d08/harness/d08_amcl_initial_pose.py`의 `assess_static_amcl_witness()`는 한 번이라도 500ms 초과 첫 수신을 기록하면 **이후 최근 Scan/Odom이 정상이고 실제 TF가 조회되더라도 무조건 실패**시킨다.

이는 이동 중 안전 TTL을 보수적으로 검사하는 데는 타당하지만, **NO_GOAL + Control 미발행**인 Localization 초기화 직후의 read-only Path 준비 판정에서는 이전 최초 공백과 현재 연속 수신이 서로 다른 증거다. 변경 가설: 과거 위반 이력을 삭제하거나 0.5초 한도를 늘리지 않고, 이전 최초 위반을 원시 기록으로 유지하면서 **새로운 실제 Scan/Odom/Clock callback 1초 이상 연속 정상 구간을 입증**하면 읽기 전용 Path 이전 단계만 해제할 수 있다. 재차 0.5초 이상 수신 공백이 나면 새로운 연속 구간부터 다시 입증해야 한다.

ROS2 Jazzy SensorData QoS는 BEST_EFFORT/작은 큐이므로 DDS graph 발견이나 SetInitialPose 서비스 ACK가 실제 callback 연속 수신 자체를 의미하지 않는다. 공식 근거:
- https://docs.ros.org/en/jazzy/Concepts/Intermediate/About-Quality-of-Service-Settings.html
- https://docs.ros.org/en/jazzy/Concepts/Intermediate/About-Executors.html
- https://api.nav2.org/nav2-jazzy/html/amcl__node_8cpp_source.html
- https://gazebosim.org/docs/harmonic/sensors/

## 3. RED → GREEN → REVIEW

**RED**
- 신규 regression file: `d08/tests/test_d08_owner_first_scan_odom_gap_regression.py`.
- RED Student 아닌 **공개 CI PR #166** 소스/테스트 commit: `94f04443c58bc70045bed301d6bcc6af966210d0`; 별도 최소 L0 워크플로 `2f9863a50580858c01891d9272dd8697a5562ab4`.
- 실제 공개 Run [#44268455861](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44268455861): 첫 callback recovery helper 없어서 `ImportError`. Run은 ROS/Gazebo 미실행이다.

**GREEN 및 작성 중 오류 기록**
- 제1 수정 `501bc6b2b316860aa660ee79089f9519c42db6be`는 recovery helper·500ms 불변 계약을 추가했지만 통합 후 구문 오류 `4cf1a8fbc8a55b87792bb3cbce1cedb9fcbed02c`에서 공개 CI [#44268795841](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44268795841) **실패**. 새 코드에서 괄호 누락과 기존 Scan/Odom age 검사 루프 삭제를 발견했다. 두 문제를 함께 바로잡은 `3b329e912182bfa1a3b67f290312a17e877d9b87`에서 [#44268920802](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44268920802) **19/19 L0 PASS**. 실패를 숨기거나 성공으로 오인하지 않는다.
- 실제 callback ledger를 `/scan`, `/odom`, `/clock`에 부착하고, 최근 수신 age<=0.5초·source sim-stamp/clock 동기성·1초 이상 연속 실수신·각 gap<0.5초를 모두 요구한다. 첫 위반 간격과 source stamp는 별도로 보존한다.
- 기존 `/set_initial_pose` 1회, 실제 `map→base_link` TF2 lookup, Nav2 원본, Goal 전 NO_GOAL 권한, 500ms Scan/Odom age 한도, G07 CM/Guard TTL은 **변경하지 않았다**.
- 실제 WSL2에서 0.8초 초과 공백이 계속 발생하면 여전히 BLOCKED여야 한다. 새 검사는 그 공백을 정상으로 조작하지 않는다.

**REFACTOR / REVIEW**
- 범용 장애물/계획/시각효과 신기능 없음; read-only Observer 내부 일시 history (최대 200 samples/토픽)만 추가.
- 장기 정체/Clock 멈춤/누락된 Odom/ROS timestamp 역행/0.5초 후속 gap은 모두 RED.
- 이전 0.8s/0.75s 최초 위반과 후속 복구 증명을 구별하며, `startup_gap_not_l3_safety_pass=true`로 구분. 실제 이동 L3 및 안전 주기 통합 PASS로 승격하지 않는다.

## 4. 기존 CI 녹색의 사각지대

[기존 #44263690201](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44263690201) 및 [#44248098353](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44248098353)는 전체 워크플로 성공이지만, `gazebo-official-nav2-oneworld` job은 `if: github.event_name == 'workflow_dispatch'` 때문에 **SKIPPED**. 따라서 공식 Nav2/AMCL 경로 타이밍의 동일 시나리오 L2로 인수하면 안 된다. 실제 공식 Nav2 L2가 성공한 소스 SHA에서만 현장 배포 후보로 판단한다.

## 5. 다음 필요한 검증

1. 공개 CI L0 19개 GREEN을 유지.
2. 기존 `gazebo-official-nav2-oneworld`를 이 개발 브랜치의 PR에서 실제 실행하고, 단일 Gazebo/공식 Nav2/AMCL/TF + 실제 Clock/Scan/Odom + 전/침입/복원 3개 Path를 한 번에 검증. 부분 성공 조합 금지.
3. 동일 출고 SHA의 Owner WSL2 D3D12 실제 GUI에서 사람 모델·픽셀·RGBD·Path를 시연하고 원본 증거로 인수. 이 CI는 WSLg GPU 성능 L3와 다름.
4. 실패 시 최초 실제 데이터 수신 공백의 앞/뒤 ROS source stamp·host receive gap·Clock gap을 먼저 비교하고, 수정 전의 안전 감시/TTL과 인접 데이터 전달 경계를 그대로 재검증. 임의 대기시간 증가나 500ms 한도 완화 금지.

현재 보고서 판정: **L0 GREEN, 신규 동일 소스 L2 결과 검증 전 HOLD, Owner L3 미검증, certified E-Stop 아님, main 미병합**.
