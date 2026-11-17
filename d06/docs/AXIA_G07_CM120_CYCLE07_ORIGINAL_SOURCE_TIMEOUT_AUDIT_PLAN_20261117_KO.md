# AXIA G07 Cycle07 — 원래 Collision Monitor source_timeout 출처·실행값 증명 (NO_GOAL)

## 배경과 학습 목표
- Cycle06 공개 L2 #43997318717에서 최초 실패 `G07_C06_SOURCE_TIMEOUT_UNVERIFIED`, 이어 CLOCK_MISSING, FIELD_NO_REAL_GOAL; 실제 Goal은 없었다. 원래 official Nav2 YAML 기본 소스 / installed config와 새 테스트의 `0.15~0.50s` 범위 불일치가 의심됨.
- 공식 upstream Jazzy `nav2_bringup/params/nav2_params.yaml`에는 `collision_monitor.source_timeout: 1.0`, `base_shift_correction: True`, `transform_tolerance: 0.2`. 코드 `collision_monitor_node.cpp` 선언 기본값은 소스 파일이 키를 누락할 때 `2.0`. 서로 다른 계약.
- 강사 private `tools/p2_zone_overlay.py`는 source_timeout >0 존재를 검증하고 원래 값을 보존하며, 기존 `tools/p4_g07_cm_tf_bound.py`는 transform_tolerance=0.20→0.02만 변경. 이 사실을 검증 없이 `source_timeout` 누락이라고 보고한 Cycle06 교육용 보고서는 사후 정정 완료.

## 이번 Cycle의 최소 범위
기존 proven public NO_GOAL real Gazebo/Nav2 runner C02 #43991016109를 재사용하고, **실제 실행 중인 `/collision_monitor`**의 런타임 파라미터 3개 (`source_timeout,base_shift_correction,transform_tolerance`)를 읽어 설치된 official `nav2_bringup/params/nav2_params.yaml`와 대조한다. G07 simulation-only false 후보는 **비활성화**하고 어떠한 Goal·cmd_vel·ROS publisher도 생성하지 않는다.

1. RED: 이전 C06 private exact SHA `67664552d9283d24db25fadb329733f83dc27878`에 아직 없는 읽기 전용 `tools/p4_g07_cm_param_contract.py`에 대한 3개 정적 계약 실패를 실제 CI에서 확인. original yaml 1.0, runtime 1.0, base_shift true, TF0.02가 정합하면 PASS; runtime mismatched/invalid/missing이면 fail closed. `Goal=false` 고정.
2. GREEN: 기존 `scripts/p2_no_goal_smoke_ci.sh`의 NO_GOAL pre-shutdown 경계에 **opt-in 한 블록만** 추가해, `ros2 param dump /collision_monitor`의 실제 파라미터와 설치된 official source YAML의 SHA를 원본 안전 체계 손대지 않고 읽음. 원래 `base_shift` true, TF bound .02, source_timeout installed yaml value와 같아야 PASS. 원본 `0.4m/0.75m` stop/slow polygons 변형 0건.
3. 공개 L0: 원본 RED3 → GREEN3 + bash syntax. 공개 L2: 동일 #43991016109 프로파일 Gazebo Harmonic, Nav2, Waffle, 14 topic, lifecycle ACK, **Goal 0**. 1회만 실행. 첫 실패 경계 관측과 실제 세 파라미터 정합만 보고.
4. 원본 출력은 `source_timeout` 수치, installed yaml SHA256, `base_shift`, `tf_tolerance` 세 필드만 공개. raw ROS trace/UUID/개인 식별자/비공개 Instructor 소스는 공개 workflow cleanup.
5. REVIEW: 원본 `source_timeout`가 1.0으로 실제 확인되면 Cycle08에서 **기존 정확한 원본을 그대로 보존**하도록 Cycle06 실험 안전 범위 검사를 수정. `0.15~0.50s` 상한을 인수 기준으로 바꾸거나 `source_timeout`을 실제로 줄이지 않음. 실제 WSL2/인증된 E-Stop/단일 Goal은 이번 Cycle에서 미실행.

## 중단 규칙
- 실제 runtime source_timeout이 installed original과 다르면 첫 mismatch 기록하고 수정하지 않는다. NO_GOAL CI가 실패하면 공개 RED 회귀로 편입, 현장 Goal 반복 금지.
- Motion compensation 변경은 실제 moving Scan header age·속도/각속도·STOP 충돌/Stop dwell 검증 없이는 출고 승인 불가. 기존 Guard150ms/Scan300ms/CM120ms 그대로 HOLD.

## 결과물
Public plan/교육 보고서: `d06/docs/AXIA_G07_CM120_CYCLE07_*.md`, public branch `fix/g07-cm120-cycle07-runtime-timeout-audit-20261117`; private 강사 코드·테스트: 동일 branch. Public Draft PR, original CI immutable Run. `main` 미병합.

```text
AXIA_G07_C07_NO_GOAL_L2=PENDING
CM_120MS_RELEASE=HOLD
AXIA_MVP_DEMO_ACCEPTED=HOLD
CERTIFIED_ESTOP=false
```
