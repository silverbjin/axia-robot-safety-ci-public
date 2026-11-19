# AXIA D06/G07 — Localization Lifecycle 최초 30초 무응답 분리 및 NO_GOAL 실제 L2 재검증

- 작성일: **2026-11-19**
- 기준: ROS 2 Jazzy / Gazebo Harmonic / 공식 Nav2 / TurtleBot3 Waffle / **NO_GOAL** 실행
- 공개 CI: `silverbjin/axia-robot-safety-ci-public`, Draft PR #177, `fix/d06-wslg-lidar-vs-rtf-ci-20261118`
- 학생: `silverbjin/axia-robot-safety-student`, Draft PR #62, `fix/g07-nogoal-ordered-cm-shutdown-20261119`
- 검증 원칙: **원본 보존 → 최초 오류 → RED → GREEN → REFACTOR → REVIEW → COMMIT**. Main 병합 없음, Moving Goal 아직 미허가.

## 1. 이전에 성공했던 것과 이번 첫 실패

이전 공개 CI NO_GOAL real L2 성공은 #44461092763, #44461627846. 사용자 NVIDIA WSL2 `fr1FN4YJ`에서는 Sensor 20.003초/Raw255.948ms/Safety256.287ms 및 Nav2 ACK가 정상이나 **native gz.transport13 read-only receiver SIGABRT134**, 별도 Gazebo server SIGSEGV -11로 최종 HOLD. 이후 독립 Gazebo Transport 수신기를 종료 전에 `/scan`·`/clock` 명시 unsubscribe하도록 하는 최소 수정과 Gazebo8 공식 ServerControl stop 경로를 도입했습니다.

그 다음 [real Gazebo L2 #44491751936](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44491751936)의 **첫 실패**는 더 이상 Scan300이나 native 프로세스 SIGABRT가 아니었습니다. 해당 원본 아티팩트 `axia-d06-g07-nogoal-cm-ordered-l2-44491751936`의 시퀀스:

| 관찰 계층 | 실제 원본 |
|---|---|
| 시작 | Gazebo/실제 공식 AMCL·Map·Nav2·CM 모두 READY |
| Raw/Safety 20초 | 20.003초; 192/193개, Raw 최대135.530ms, Safety 최대132.749ms, CLEAR193/193 |
| Nav2 Navigation shutdown | `navigation_service_request_sent=true`, `status=ACK`, 2.633초 |
| **Nav2 Localization shutdown** | `localization_service_request_sent=true`, `SERVICE_TIMEOUT`, **30.000493초** |
| 원본 Launch | Localization Manager가 종료 전이에 들어갔다는 로그 없음. SIGINT 후 preshutdown 로그는 존재 |
| 결과 | `BLOCKED_LIFECYCLE_LOCALIZATION_SERVICE_TIMEOUT`, 전체 smoke rc3 |
| 비관련 종료 | CM exit0, Gazebo server exit0, Guard/Supervisor exit0; 이 성공으로 Localization ACK 누락을 보상할 수 없음 |

이전에는 단일 rclpy 노드였으나 최근 버전에서는 Navigation/Localization 각각 새 rclpy 노드의 *독립된 단발* `ManageLifecycleNodes::SHUTDOWN` 요청을 사용합니다. 그래도 간헐적으로 응답이 사라졌습니다. 이것이 ROS discovery·service callback·응답 RMW 중 어느 단계인지는 **아직 증거 부족**이며 특정 시스템 원인으로 단정하지 않았습니다.

공식 Nav2 Jazzy `nav2_lifecycle_manager`에서 ManageLifecycleNodes 서비스 callback은 SHUTDOWN 명령에 대해 서버 측 `shutdown()` 전이 완료 후 응답합니다. 따라서 `request_sent=true`만으로 해당 callback이 실행되었거나 정상 종료했다고 주장할 수 없습니다.

공식 참고: [Nav2 lifecycle manager Jazzy 소스](https://api.nav2.org/nav2-jazzy/html/lifecycle__manager_8cpp_source.html), [Nav2 Lifecycle Manager 구조](https://api.nav2.org/nav2-jazzy/html/md_nav2_lifecycle_manager_README.html).

## 2. RED → GREEN: 안전 승인 없이 첫 응답 경계 관찰

### RED

- [Run #44493060902](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44493060902) — `d06/tests/test_d06_g07_nogoal_ordered_cm_shutdown.py::test_localization_30s_no_ack_probes_readonly_service_without_retry`에서 **읽기 전용 서비스 진단 미구현**을 재현. 이 실패는 실 ROS/Gazebo가 아닌 정적 L0 계약입니다.
- 신규 회귀에서는 timeout 후 **두 번째 SHUTDOWN 재전송 금지**, 전체 60초 종료 기한 초과 금지, 각 관리 노드 ACK를 독립 기록하도록 유지합니다.
- 첫 GREEN 후보는 만료된 타이머에서도 `rcl_interfaces` 모듈 import를 시도하는 오류가 L0로 잡혀 수정했습니다. [Run #44502620706](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44502620706) RED.

### GREEN

- 학생용 파일: `block_B/day07/h01_runtime/tools/p2_g07_ordered_shutdown.py`.
- `probe_localization_parameter_service(rclpy, timeout_sec=remaining)`: Localization SHUTDOWN 요청 **정확히 1회**가 30초 내 ACK 없으면, 기존 Node context에서 새 임시 Read-Only 노드를 사용해 `/lifecycle_manager_localization/get_parameters` 서비스에 `GetParameters(node_names)`를 **최대 1회** 요청. 서비스 발견 0.5초·응답 최대 2초·사용 가능한 전체 기한 최대 3초 범위 내 분류. 기한이 0이면 ROS import·서비스 요청 자체를 생략.
- `PARAMETER_SERVICE_RESPONSIVE` / `PARAMETER_RESPONSE_TIMEOUT` / `PARAMETER_SERVICE_MISSING` / `PARAMETER_PROBE_ERROR` / `NOT_RUN_DEADLINE_EXPIRED`를 원본 최초 원인 후보로 보고. 읽기 전용 GetParameters가 응답해도 **Lifecycle Shutdown ACK가 아니라는 점은 유지**.
- 이전과 동일하게 `if ack["status"] != "ACK"`이면 `BLOCKED_LIFECYCLE_LOCALIZATION_SERVICE_TIMEOUT`을 반환하여 **NO_GOAL 인수 HOLD**. CM120ms / Guard150ms / Scan300ms 안전 TTL 또는 Gazebo World·Goal 제어 변경 없음.
- 강사 외부 실행기는 `native_nav2_ordered_shutdown.json`의 최초 `localization_parameter_probe`, `localization_service_request_sent`, `localization_response_elapsed_sec`를 작은 forensic TAR/summary에 보존하도록 추가했습니다.
- 최종 학생용 코드 SHA: **`df911a88f88f70a7e622170b55678ee821423d8f`**.

### 실제 검증 출력

- **공개 L0** [#44502886416](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44502886416): **102/102 PASS** — ROS-free 단위·소스·가짜 ROS 인터페이스 테스트.
- **공개 실제 Gazebo L2** [#44503070174](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44503070174), 원본 artifact `axia-d06-g07-nogoal-cm-ordered-l2-44503070174`: **PASS**.
  - 센서 원본 `NO_GOAL_SENSOR_WINDOW_CLEAR_CANDIDATE`; dual-topic 20.007초, Raw 196개 최대126.182ms, Safety 196개 최대125.575ms, CLEAR196/196, 전방/측면 1.414006m/2.519869m
  - `AXIA_D06_G07_NATIVE_SHUTDOWN_SMOKE_RC=0 RVIZ=1 GAZEBO=1`
  - `NAV2_LIFECYCLE_SHUTDOWN_ACK`, Navigation 1.504530초, Localization **0.249842초**, 둘 다 실제 ACK
  - 독립 native Gazebo/ROS receiver exit0, unsubscribe-before-teardown, 공식 Gazebo ServerControl(stop:true) ACK
  - Collision Monitor, Gazebo server, Supervisor, Base Guard 각각 실제 `process has finished cleanly`
  - `AXIA_D06_G07_NO_GOAL_STRICT_INTEGRATED_L2_PASS_SENSOR300_NAV2_ACK_CM0_GZ0` 실제 출력
  - Localization timeout이 이 성공 세션에서 재발하지 않아 **`localization_parameter_probe=NOT_TRIGGERED`**. 이 GREEN 실행만으로 간헐적 30초 시간 초과의 원인이 제거됐다고 결론 내리면 안 됨.
- **공개 L0 추가 forensic** [#44504282378](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44504282378): **103/103 PASS**, 최초 timeout 진단 필드가 압축 요약에 반드시 포함된다는 테스트 추가.

## 3. 강사 WSL2 단일 실행 (현장 미수행)

외부 실행기: `d06/scripts/axia_d06_g07_wslg_gpu_rtf_compare_once.sh`, 코드 commit **`c7c22ab0a4f6a8aeb3c92b11d3bbca434b8c6941`**, Git blob **`3384b4febae248440951b0f862714083df7f324b`**.

본 실행은 NVIDIA WSLg 원래 월드를 **한 번만** 사용하고 `--nvidia-causal`로 NO_GOAL 증거를 압축합니다. 실제 GPU/Wslg의 Gazebo 최종 종료코드와 L2 소프트웨어 렌더러 결과를 혼동하지 않습니다.

```bash
(
  set -Eeuo pipefail
  SHA="c7c22ab0a4f6a8aeb3c92b11d3bbca434b8c6941"
  BLOB="3384b4febae248440951b0f862714083df7f324b"
  SCRIPT="$(mktemp --suffix=.sh)"
  trap 'rm -f "$SCRIPT"' EXIT
  curl -fLsS --retry 3 --max-time 90 \
    "https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public/$SHA/d06/scripts/axia_d06_g07_wslg_gpu_rtf_compare_once.sh" -o "$SCRIPT"
  test "$(git hash-object "$SCRIPT")" = "$BLOB"
  bash -n "$SCRIPT"
  bash "$SCRIPT" --self-check
  bash "$SCRIPT" --nvidia-causal
)
```

WSL2 실행이 실패하면 현장 재시도 대신 출력된 `D06_FORENSIC_ARCHIVE`와 `D06_FORENSIC_SHA256`를 확인하여 **최초 안전 전이와 최초 Lifecycle 시간 초과**를 구분하고 공개 CI 회귀를 먼저 만듭니다.

## 4. 명확한 인수 제한

1. `CI L0 PASS`: Python 계약/가짜 ROS 클라이언트 검증, 실제 시뮬레이터 아님.
2. `CI L2 PASS`: 동일 실제 ROS2 Jazzy·Gazebo Harmonic·공식 Nav2 NO_GOAL 세션 20초 관찰 + 정상 종료 한 번.
3. `WSL2 NVIDIA NO_GOAL L3`: 아직 현장 실행 **NOT_RUN**, 가속 렌더러 경계 불확실.
4. `Moving G07 L3`: 실제 Goal/Controller/CM120ms/Guard150ms/Scan300ms 전달 주기, 최소 안전 상태 전이, 감속·정지·Goal Cancel·정상 종료 **NOT_RUN**. 기존 승인된 실행기만 재사용. 새 Planner·Supervisor·Fault Injector 개발 금지.

따라서 **`AXIA_MVP_DEMO_ACCEPTED=HOLD`**, `D06_GAZEBO_LIVE_RELEASE=HOLD`, `CERTIFIED_ESTOP=false`. Main 병합은 사용자 승인 후에만 진행합니다.
