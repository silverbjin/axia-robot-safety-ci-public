# AXIA D08 — 교육용 기능 동결 이후 종료 안정성·시작 속도·RTF 개선 백로그

**작성일:** 2026-11-18 KST. **문서 성격:** 후속 개선 계획. 아직 구현/CI GREEN/Owner 인수 결과가 아님. **D08 NO_GOAL 기능 완료 판정과 분리하여 관리한다.**

## P0 — Ctrl+C 정상 종료(현재 L3 HOLD의 직접 원인)

- 강사 원본 `run_20261118T141633Z_OgyMwe.diagnostics.zip`: `owner_completed_cycles=6`, 종료 시 `RCLError: rcl_shutdown already called on the given context`; `Destroyable because destruction was requested`; Nav2 exit 1, Gazebo server SIGSEGV(-11).
- 경계: `d08/harness/d08_same_world_replan.py`의 Executor 및 rclpy 종료와 현재 처리 중인 callback 경합. `rclpy.shutdown()`의 이중 호출을 허용하지 않는 동작, 실제 thread join 전에 Node 파괴하는 순서를 조사. **가설이지 모든 프로세스 종료의 단일 확정 원인으로 간주하지 않는다.**
- 최소 수정 후보: 정상 사용자 중단을 개별 상태로 기록, Executor/worker join 보장, context 활성 확인과 `rclpy.try_shutdown()` 등 안전한 중복 종료 처리. 외부 Gazebo SIGSEGV는 별도 원인 분석.
- 필수 RED→GREEN: 실제 ROS Executor를 동작시킨 상태의 Ctrl+C를 공개 CI에서 재현 → 단일 가설 수정 → 실제 Gazebo·RViz/GUI·Nav2·Bridge 동일 세션의 정상 종료 확인. 하류 예외를 무작정 무시하거나 종료 code를 조작하지 않는다.

## P1 — 최초 Scan 수신 간격 위반(운영 안정성)

- 실제 선행 Owner 0.546644s, 이후 공개 CI [#44312306299](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44312306299)에서 0.505365s **최초 host Scan 수신 위반**. 한도 0.5s 유지.
- Gazebo 발행자 stamp 간격, ros_gz_bridge/RMW 전달 주기, subscriber host 수신, Clock RTF를 최초 0.5s 위반 시각 기준으로 계측. 현재 `publisher_rmw_cadence_measured=false`이므로 원인 경계는 추가 관찰 전 미결.
- 성공 기준: 실제 L2/Owner 본 시연과 같은 노드 간 수신 주기·Scan/Odom/Clock 안전 TTL, 다른 안전 계층에 미치는 영향 검증. 8회 반복 관찰만으로 이동 Goal 안전/CM/Guard 정지 인수를 대체하지 않는다.

## P1 — 재실행 준비 시간 최적화

- 현재 Owner 스크립트는 매번 새로운 실행 폴더에서 공개 소스 + upstream yolo_ros Git clone, 약 103MB ONNX Runtime NuGet 재다운로드(이번 현장 약 30초), 모델 다운로드, C++ `colcon build --executor sequential`를 반복한다.
- **MVP 최소 변경:** 고정 소스 SHA와 upstream YOLO SHA, ONNX Runtime 1.20.0 NuGet SHA256, 모델 SHA256, ROS Jazzy 및 ABI/ELF 의존성을 검증하는 **로컬 warm cache**. 캐시 HIT는 동일 원본만 재사용; MISS/해시 불일치 시 기존 공식 빌드로 복귀.
- cold vs warm의 다운로드·컴파일·Gazebo world-ready·AMCL/TF·첫 Path 시각을 각각 기록. 실제 ROS/Gazebo 데이터 증거는 반복 실행마다 생략하지 않음.

## P2 — WSLg 실시간 성능(RTF) 및 자원 사용

- 사용자 육안 Gazebo 표시 약 RTF 0.70~0.80. 별도 AMCL 짧은 구간 clock 관찰 RTF 0.909198. 전체 RTF 평균이나 CPU/GPU 병목은 **확정되지 않음**.
- 실제 Gazebo world stats 30초 이상 median/min/p10 RTF, Scan/Odom/Clock 최대 host receive gap, Gazebo/YOLO/RViz CPU, 메모리 압박 및 NVIDIA D3D12 GPU 사용을 작은 JSON으로 기록.
- 동일 물리 World/센서/YOLO 조건에서 Gazebo/RViz 패널 최소화 A/B 관찰. 사용자가 원하는 실제 Gazebo와 RViz 동시 GUI 표시를 최종 시연 범위에서 제외하지 않는다.
- 물리 timestep·LiDAR 10Hz·RGB-D 설정·Scan 500ms/CM/Guard TTL은 성능 최적화를 위해 바꾸지 않는다. RTF 향상 자체를 안전 승인 기준으로 삼지 않는다.

## 실행 통제

**RED→GREEN→REFACTOR→REVIEW→COMMIT**, 공개 CI 실제 Gazebo L2 및 변경 영향 타이밍 범위 명시, Owner WSL2 L3 별도. 기존 PASS 증거를 반복 무효화하지 말고 새 실패 경계만 좁게 재현한다. 오류 수정 후 다른 안전 계층의 수신 간격과 TTL이 미검증이면 **전체 시연 안정성은 HOLD**로 표시. 강사 정답/학생 TODO 공개 경계를 유지하며 main 병합은 별도 승인 필요.

```text
D08_NO_GOAL_FUNCTIONAL_MVP=COMPLETE
D08_POST_MVP_SHUTDOWN_FIX=NOT_STARTED
D08_POST_MVP_SCAN_TIMING_FIX=NOT_STARTED
D08_OWNER_L3_FINAL_ACCEPTANCE=HOLD
MAIN_MERGED=false
```
