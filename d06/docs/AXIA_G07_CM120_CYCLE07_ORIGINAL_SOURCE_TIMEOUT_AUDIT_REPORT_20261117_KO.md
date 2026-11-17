# AXIA G07 Cycle07 — 공식 CM source_timeout 런타임 출처 확인 교육용 경과보고서

## 문제·증거 우선 분석
이전 Cycle06 실제 L2 [Run #43997318717](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43997318717)는 `G07_C06_SOURCE_TIMEOUT_UNVERIFIED`로 공식 CM 구성 자체가 차단되고 후속 `CLOCK_MISSING`, `FIELD_NO_REAL_GOAL`만 나타났다. **Goal 미전송**이므로 CM120 지연 실험 실패가 아니다.

근본 계약 차이는 세 가지:
1. 공식 Nav2 Jazzy 소스 YAML `nav2_bringup/params/nav2_params.yaml`에는 `collision_monitor.source_timeout=1.0`, `base_shift_correction=True`, `transform_tolerance=0.2` 명시.
2. 공식 Nav2 C++ `collision_monitor_node.cpp`는 키를 생략할 경우 `source_timeout=2.0`의 코드 기본값 선언.
3. Instructor `tools/p2_zone_overlay.py`는 source_timeout 존재·양수 검증 후 **원본 값을 변경하지 않음**. Cycle06 후보 `tools/p4_g07_cm_sim_simple_tf.py`에서 근거 없이 만든 허용범위 **0.15~0.50s**는 공식 기본 YAML 1.0과 모순.

즉 실제 1.0 source_timeout을 0.3으로 바꿔 강제로 통과하는 것은 '공식 파라미터 1개만 변경' 실험을 파기하므로 **금지**했다. C++ 선언 기본 2.0과 설치 YAML 1.0을 혼동하지 않고, 실행 중인 실제 CM 값을 따로 확인하는 Cycle을 계획했다.

## 계획 및 RED→GREEN 코드·테스트
- 계획 커밋 `4a4af796855114994b9355379097bd217951da14`, public branch `fix/g07-cm120-cycle07-runtime-timeout-audit-20261117`, private 동일 branch.
- private RED test `tests/unit/test_g07_cycle07_cm_source_timeout_runtime.py` commit `bb0cd36b5f8a5146a2cfc702ff1e7b61aa365974`. C06 기준 source `67664552d9283d24db25fadb329733f83dc27878`에는 `p4_g07_cm_param_contract` 없음(예상 RED).
- private GREEN read-only parser `tools/p4_g07_cm_param_contract.py` commit `69218fc0d66dafb3752f0e011ed900914fc2cfb1`; CI-only opt-in NO_GOAL run insertion in `scripts/p2_no_goal_smoke_ci.sh` commit `493aeae195d0c62331da0ca150b6ae518638156f`. Original CM/Guard/Nav2 source·TTLs·Zone polygons·Goal authority 0 변경.
- 공개 워크플로 `.github/workflows/axia-g07-cycle07-runtime-cm-params-nogoal-l2.yml` 개발 커밋 `377d11d07daf0d6493d41e65ed6f4efeb8165a2e`, pinned private candidate `493aeae195d0c62331da0ca150b6ae518638156f`, original C06 baseline `67664552d9283d24db25fadb329733f83dc27878`.
- Release one-off public CI commit `5998246de354c8f5e991f7df03e8fffcc9fe7814`, [Run #43999183495](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43999183495) 실제 RED/GREEN / Jazzy+Gazebo NO_GOAL readback 결과를 확인 후 아래에 추가한다.

## 실행 방법과 인수 범위
Unit test: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/unit -p 'test_g07_cycle07_cm_source_timeout_runtime.py' -v`.

공개 CI에만 opt-in `AXIA_G07_C07_CM_PARAM_READBACK_NO_GOAL=1`, `AXIA_G07_CI_SIM_GOAL_ALLOWED=0`, `AXIA_G07_SHUTDOWN_L2_ONLY=1`, `AXIA_P4_G07_SHARED_PREFLIGHT_ONLY=1`, `GITHUB_ACTIONS=true`. 공식 `nav2_bringup/params/nav2_params.yaml` SHA256과 실제 `ros2 param get /collision_monitor` 세 파라미터를 읽음. 기존 Gazebo Harmonic/Nav2 Waffle, 안전 relay, 14-topic record, ordered shutdown 그대로. Raw ROS bag/개인 경로·Instructor private code 공개 금지.

## 수업 토론
- 왜 함수 기본값 2초를 공식 `nav2_params.yaml`의 1초로 보고하면 안 되는가?
- 왜 `source_timeout`가 공식 YAML에 있어도 런타임 readback을 확인해야 하는가?
- Guard Scan TTL300ms와 CM source_timeout1000ms는 동일한 안전 계층인가?
- 근거 없는 stricter bound가 CI를 실패시킨 경우, 더 짧은 값을 강제로 배포하는 것이 진정한 문제 해결인가?
- 왜 재현 실패의 최초 `source_timeout` 오류를 따라가야 하며 후속 `CLOCK_MISSING`을 일차 원인으로 보지 않는가?

## 대기 중인 실제 검증 결과
```text
AXIA_G07_C07_PUBLIC_L0=PENDING
AXIA_G07_C07_NO_GOAL_L2=PENDING
CM_120MS_RELEASE=HOLD
OWNER_WSL2_MOVING_L3=NOT_RUN
AXIA_MVP_DEMO_ACCEPTED=HOLD
CERTIFIED_ESTOP=false
MAIN_MERGED=false
```
