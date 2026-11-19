# AXIA D06/G07 — Cycle 05 중간 보고: CI-only GUI priority 후보 / 정적 계약 복구

기준일: 2026-11-19 | 공개 PR #177 (Draft) | L3 배포 HOLD

## 1. 작업 재개 기준과 이미 존재하던 수정
- 이전 완료 보고: `d06/docs/AXIA_D06_G07_CYCLE04_CI_APT_HTTPS_GREEN_REAL_NATIVE_SCAN_FIRST_GAP_20261119_KO.md`
- 공개 실제 Gazebo L2 #44535830485는 source-stamp 34.302→34.401초에서 native Scan gap 300.409ms, ROS raw 300.898ms, safety 301.307ms, 국소 /clock 관측 RTF 약0.375로 **최초 TTL 위반**. 20초 Student qualified 구간과 Nav2/CM/Gazebo 종료의 다른 PASS와 분리하여 전체 L2 FAIL.
- 최신 브랜치 HEAD `fc323aa73d2032858c3e797917c0a4873686e766`에는 이미 Student CI-only Gazebo/RViz GUI `nice -n 15` 가설이 구현되어 있었음. Student commit `112f2ac6aaed3123e2d38ccec7b9f7429fd02af9` / `block_B/day07/h01_runtime/scripts/p2_no_goal_smoke_ci.sh` (blob `9b0cbc348a48784c29e042a55b549d08dd9c57a7`).
- 이 분기는 `GITHUB_ACTIONS=true`, `AXIA_G07_CI_SENSOR_TRUTH_NO_GOAL=1`, `AXIA_D06_L2_GUI_NICE_ONLY=15`, `SENSOR_NO_GOAL=1`일 때만 양쪽 GUI 자식 프로세스에 `nice15` 적용. Gazebo server, CM, Guard, Supervisor, Nav2, WSL2 Owner 기본 실행 환경은 변경하지 않음.

## 2. 최초 CI 정적 계약 오류 및 RED (재현)
- 공개 L0 #44537214358, #44537202424: `test_d06_ci_only_gui_nice.py`가 전체 Student smoke에 `taskset -c` 문자열이 없을 것을 요구함. 원본 smoke의 별도 Task03 구현에 이미 CPU affinity가 존재하므로 **신규 GUI 분기에 무관한 가짜 RED**.
- 같은 실행에서 `test_d06_gpu_rtf_runner_safety.py`는 과거 Student smoke blob `ca4af428...`을 기대했으나 실제 SHA 고정 소스 blob `9b0cbc...`. Git blob 검증 자체가 유효하므로 오래된 상수만 교체해야 함.
- 수정 후 #44538026154: 테스트가 `src.index('   sleep 3')`의 잘못된 공백으로 ERROR. #44538270703: 실제 GUI 블록과 테스트의 `else` 다음 들여쓰기가 달라 false FAIL. 두 오류 모두 실제 런타임 오류가 아니라 CI 테스트 자체의 계약 정밀도 문제.

## 3. 최소 수정 / REFACTOR / REVIEW
변경 파일:
- `d06/tests/test_d06_ci_only_gui_nice.py`: 실제 `# CI Xvfb-only single hypothesis` 블록부터 종료 `sleep 3` 앞까지 **GUI branch 영역만** 추출하여 음성 검사. 예상한 문자열의 공백을 실제 소스에 맞춤. 역사적 Task03 taskset은 그대로 유지.
- `d06/tests/test_d06_gpu_rtf_runner_safety.py`: 새 smoke blob `9b0cbc348a48784c29e042a55b549d08dd9c57a7` 고정.
관련 구현 커밋 `9a252041116fbe027a89f3829f87121967aecca7` → `a67a40f6be4cad02acd06ed0de398b1556f4b4cc` → `0c0444a0a8a02c2f8578d3fb0ef08e30f1d1a0ec` → `2ae1d2f283c9c4ea2843d7dbd8ec648883c54ecd`.
테스트 수정 외 실제 Gazebo/ROS/센서/QoS/TTL/Goal 경로 변경 없음.

## 4. 공개 GREEN
- L0 [#44538463431](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44538463431): 122/122 PASS.
- Runner canary [#44538463629](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44538463629): SUCCESS.
- Tested exact SHA `2ae1d2f283c9c4ea2843d7dbd8ec648883c54ecd`.
- **L0=소스·정적 회귀 검증**. 실 Gazebo native Clock/Scan 지연 개선의 근거가 아님.

## 5. 실제 L2 검증 및 판정
- 공개 실제 Jazzy+Harmonic+Waffle+공식 Nav2+Xvfb **같은 SHA** [#44538452186](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44538452186). 최종 verdict는 CI Run/원본 로그 완료 후 별도 증거로 업데이트.
- 최초 READY 이후 native/raw/safety 20초 Scan300 위반, 이후 Student qualified 20초, Nav/Loc ACK, CM/Guard/Supervisor/Gazebo exit0는 **독립적으로 모두 확인**해야 통합 PASS.
- 공식 Gazebo 문서는 렌더링 GUI와 Sensors server가 별개 장면/렌더링 경로를 사용하며 RTF 저하 가능성을 설명함. 이는 시뮬레이터 CPU/GPU 자원 경쟁 후보의 동기일 뿐, C05 성능 개선 증거는 아님. https://gazebosim.org/api/sim/8/server_config.html ; https://gazebosim.org/docs/harmonic/sensors/

## 6. 인수와 보안 정책
- `AXIA_MVP_DEMO_ACCEPTED=HOLD`
- `D06_GAZEBO_LIVE_RELEASE=HOLD`
- `CERTIFIED_ESTOP=false`
- `OWNER_WSLG_L3_NOT_RUN`
- WSLg GPU 특이 SIGSEGV 코어 스택 미확보, 최종 인수 미검증. 공개 PR #177/학생 PR #62 Draft 유지, main 미병합.
