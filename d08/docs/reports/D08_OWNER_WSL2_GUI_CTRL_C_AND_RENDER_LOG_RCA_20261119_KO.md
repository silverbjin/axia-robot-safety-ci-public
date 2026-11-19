# D08 Owner WSL2 — 실제 GUI 시연 경고와 Ctrl+C 종료 실패 RCA

**2026-11-19 / 증거 분석 전용 / RED-GREEN 수정 전 HOLD**

## 원본과 검증
- 사용자가 전달한 `run_20261119T054830Z_JXa9lq.diagnostics.zip` SHA256 `5383b55c79498ec18118a9c4c06867089e5f69fa30da19446fc014604cc17c06`, 별도 .sha256 일치, 33개 ZIP 엔트리 CRC PASS.
- 실제 WSL2/WSLg 실행 소스 `28c554b1a112499af9f8e1159a77e1f70185ab8b`; 분석은 로컬 증거에 한정. 이번 보고서로 ROS/Gazebo 재실행, 코드 수정, CI GREEN, main 병합을 선언하지 않음.
- Gazebo World와 실제 Waffle/person Scene PASS, 공식 Planner Lifecycle ACTIVE 및 AMCL·map→base_link TF·3상 경로 PASS, YOLO RGBD 2 VALID + 1 UNKNOWN PASS, Owner 반복 `cycle_0000`~`cycle_0003` 4회 PASS. 완료된 `cycle_0000` Scan 최대 0.239781s, `cycle_0003` 0.254896s, 공식 첫 3상 0.240284s. `cycle_0001,0002`의 상세 로그는 ZIP 미포함이므로 수치 추정 금지. NO_GOAL, NO_CMD_VEL.
- GPU `D3D12 (NVIDIA RTX 2060 Max-Q)` 실제 확인. 별도 YOLO는 `provider=cpu` 채택.

## 시간순 최초 현장 이슈 (KST)
1. **14:52:37.503** RViz Map GLSL shader link error: `rviz/glsl120/indexed_8bit_image.vert/.frag`, `active samplers with a different type refer to the same texture image unit` (Nav2 로그 281~284). upstream ros2/rviz #463에 동일 오류가 최초 Map 수신 중 발생하는 사례 존재. 이후 실제 Path와 4회 Owner 시연 성공하므로 현 시점 주행 실패 원인으로 승격 금지. 현장 픽셀 렌더링 품질은 로그만으로 보증하지 않음.
2. Nav2 초기 `map`/`odom` TF unavailable, AMCL `set initial pose` 요구, RViz message filter queue full (241,256,267,288~320). **14:52:46.345** AMCL 첫 initial-pose TF future extrapolation 약 21ms, 이후 `Setting pose`, planner active/공식 경로로 회복. 지속적인 Localization 실패가 아님.
3. YOLO `Provider cpu contradicts device cuda:0; using cpu` 경고는 CPU 설정과 표시 불일치, 추론은 CPU로 수행되어 실제 VALID/UNKNOWN 판정에 치명적인 오류는 아니었음.
4. **14:54:40.710** Nav2 `user interrupted with ctrl-c (SIGINT)` (367). 직후 대부분 Nav2 노드 clean exit.
5. `cycle_0004` 미완성: `D08_NATIVE_GZ_SCAN_RX_EVIDENCE_INCOMPLETE`, Native+독립 ROS 샘플 0. Ctrl+C가 해당 수집 시작에 겹쳤을 개연성이 높지만 단일 compact ZIP의 cycle timestamp 부재로 **원인·정확한 선후 관계 미검증**. 이번에는 500ms 초과 Scan 첫 위반이 기록되지 않음.
6. 상위 `live_evidence/verdict.json`: `owner_completed_cycles=4`, `status=BLOCKED`, `blocker=RCLError: failed to shutdown: rcl_shutdown already called on the given context`. source `d08/harness/d08_same_world_replan.py`의 finally에서 `rclpy.shutdown()`을 **무조건 호출**하며 SIGINT가 Context를 먼저 종료하면 RCLError로 덮어써 `d08_public_gazebo_l2.py`의 `except KeyboardInterrupt`로 전달되지 않는 코드 경로와 부합. ros2/rclpy #1081, #1352와 동일한 문제 유형.
7. 종료 후 RViz `exit -6`, `terminate called without an active exception`, Gazebo server `exit -11`, Nav2 공식 launcher `/tmp/nav2_*.sdf` No such file. **실제 GUI graceful shutdown 미검증**. crash 원인 backtrace 없음. 공식 Nav2 Jazzy `tb3_simulation_launch.py`는 xacro 임시 SDF와 OnShutdown 삭제 기능을 가지고 있으므로 이미 준비된 사용자 World가 실행 실패했다는 뜻은 아님.

## RMW 요약 누락
- tracetools enabled, 원본 CTF `100864344` bytes (~96MiB) 생성.
- 이번 ZIP에 `rmw_trace/summary.json`, `rmw_source_rows.jsonl`, `stop.success` 없음.
- `rmw_trace/owner_first_gap_verdict.json`: `trace_event_count=0`, `rmw_trace_capture_complete=false`, `candidate=NO_FIRST_GAP_IN_AVAILABLE_VERDICTS`, `cause=UNDETERMINED`, Owner L3 NOT_ACCEPTED. 이는 **정상 RMW 신선도 PASS 아님**.
- stop/watchdog/session 로그가 ZIP에 없어 parse 중단의 정확한 원인은 미확정. 기존 WSL2 run 디렉터리의 raw CTF 및 관련 로그 **보존 후 오프라인 점검**, 현장 재시도 반복 금지.
- 추가 코드 검토: `d08_owner_no_goal_bootstrap.sh`의 `AXIA_D08_TRACE_SESSION="axia_d08_owner_$"`는 실제 고정 문자열이며 PID 고유 세션이 아니다. 다중 실행 충돌 위험으로 다음 회귀에 포함. 이 1회 실패의 증명된 원인은 아님.

## RED→GREEN 최소 수정 계획 (아직 미실행)
- 1순위: 정상 Ctrl+C에서 Context 중복 종료가 일어나도 원래 KeyboardInterrupt/OWNER_STOP 판정을 덮어쓰지 않도록 `rclpy.try_shutdown()` 또는 Context 상태 검사와 단일 종료 소유권 적용. 이미 기록된 미완주 `cycle_0004`를 PASS로 바꾸지 말고 `OWNER_INTERRUPTED`로 구분.
- 재현 가능한 부분을 L0 RED 테스트로 먼저 고정 → 최소 GREEN → 기존 실증과 동일한 Gazebo+RViz GUI SIGINT L2 → REVIEW → COMMIT. 타이밍 500ms, CM120ms/Guard150ms 변경 금지.
- 2순위: RViz exit -6 / Gazebo -11 / Nav2 temp file teardown은 단일 실세션 종료 회귀 안에서 조사. 새로운 World·Planner·GUI 기능 개발 금지.
- 3순위: RMW 고유 trace-session 회귀와 종료 실패 시 소형 stop/watchdog/session 요약 ZIP 포함 회귀. 원본 CTF는 공개하지 않음.
- 마지막: 위 공개 CI GREEN 범위를 명시한 뒤 Owner WSL2 1회만 재인수. 실제 안전계층 인터노드 주기·TTL, 물리 STOP/SLOW, 인증 E-Stop은 여전히 HOLD.

## 외부 유사 사례
- https://github.com/ros2/rclpy/issues/1081
- https://github.com/ros2/rclpy/issues/1352
- https://github.com/ros2/rviz/issues/463
- https://api.nav2.org/nav2-jazzy/html/tb3__simulation__launch_8py_source.html
