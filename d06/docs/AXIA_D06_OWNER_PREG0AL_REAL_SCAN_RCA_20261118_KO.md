# AXIA D06/G07 — 실제 WSLg PRE-GOAL LaserScan 초기 차단 증거·CI 보고서

작성: 2026-11-18 (KST) · 검증 형태: 사용자 원본/비식별 CI 수치/실제 Jazzy Gazebo+RViz L2 · **출고 HOLD**

## 1. 제출 원본과 최초 실패

- 사용자 첨부 `d06-moving-vUavDSKf.tar.gz` SHA256: `02b2054c12bcf446733dc8b194c24bb9cc4f5562fa565ab6ca93dd4f0997b932`. 동봉 .sha256의 절대 경로 대상 해시와 일치함.
- 압축 내부 `SHA256SUMS` **52/52 PASS**, `native/SHA256SUMS` **44/44 PASS**. 사용자 원본 raw BAG·호스트 민감 정보는 GitHub에 업로드하지 않음.
- 실제 `native/startup_verdict.json`의 Clock, Localization, AMCL/TF, Navigation, CM, P2 Graph, Nav2 Action 준비 모두 PASS. `/clock` 11,299개, `/odom` 941개, `/scan` 338개, `/safety/scan` 337개가 SQLite에 실재함. 14개 요청 토픽 중 `/cmd_vel_smoothed` 및 Nav2 Action Status 등 실제 메시지 0개인 토픽은 PASS로 승격하지 않음.
- **첫 Demo 차단**: `AXIA_G07_OWNER_PREGOAL_PHYSICAL_L2_BLOCKED RuntimeError:OWNER_PREGOAL_NOT_CLEAR_BEFORE_FIXTURE`. 이후 `AXIA_G07_CI_MOVING_GOAL_REAL_GAZEBO_PREG0AL_BLOCKED` 및 `P2_L2_SMOKE_RC=2`는 후속 오류. **Gazebo native set_pose/단일 Nav2 Goal은 전송되지 않음**.
- 실제 첫 보호 상태 전이: Supervisor `BOOT_SAFE`; Guard `NO_FRESH_PAIR`에서 `FORWARDING_MONITORED_CM`(일부 구간)로 변동하나 latch=false. 공식 Collision Monitor Launch 로그에는 `Robot to stop due to AXIA_StopFront polygon`이 실제 기록됨. Guard latch 없음은 PRE-GOAL 안전 CLEAR의 증거가 아님.
- ROS Scan callback 최대 간격 `0.819175s` (`HEALTH_BAD_DIAGNOSTIC`), 기존 Scan TTL `0.300s`를 초과함. 이 타이밍 위반과 즉시 Clear 조건 불만족을 동시에 조사해야 하며, 300ms TTL 완화 금지.
- WSLg OpenGL renderer 실제 `D3D12 (Intel(R) Iris(R) Xe Graphics)` Mesa 26.2.6. GTX/RTX 가속기가 아닌 통합 Intel로 열린 점을 기록하되, **센서 원인 판정 NOT_PROVEN**.

## 2. 원본 SQLite CDR 재계측 — 실제 `sector_min()` 각도와 동일

사용자 BAG의 LaserScan을 CDR로 직접 해석하였으며, 원본 G07의 전방 `abs(angle)<=.18`, 측면 `abs(angle-atan2(.75,.19))<=.12` 최소 거리를 사용했다. 각도 wraparound 포함.

| 항목 | 안전 Scan 실측 | 기존 Goal 이전 계약 |
|---|---:|---|
| Scan 샘플 | 337 | 3개 이상 실제 수신 |
| beams/scan | 360 | 실제 유효 beam |
| 전방(min / median / max) m | 0.503870 / **0.526377** / 0.548657 | **front >0.75** |
| 측면(min / median / max) m | 0.600543 / **0.629360** / 0.647628 | **side >1.20** |
| 전·측면 모두 CLEAR인 샘플 | **0 / 337** | 1차 CLEAR 필수 |
| 모든 유효 beam이 0.40~0.85m 범위에 있는 비율 | **100% (337 / 337 scans)** | 물리/렌더 원인 미판정 |
| 실제 odom velocity | 0 부근(정지) | Goal 전 정지 |
| Scan callback 최대 gap | **819.175ms** | **300ms 이내** |

이 값은 실제 원본으로부터 도출됨. 정면·측면 Clearance를 낮추거나 빔의 근거리 값을 무조건 버리는 것은 금지.

**우선 가설:** 모든 각도에서 동일한 근거리 벽처럼 측정된 값은 정상적인 국소 전방 장애물 장면과 다르다. Robot self-detection/월드 내부 장애물/WSLg OGRE2 GPU LiDAR + Intel D3D12 backend 차이를 **하나씩 검증**한다. Linux-native public CI의 같은 소스와 같은 world 물리 시연이 정면 1.4m·측면 2.5m를 보고한 것은 실제 플랫폼 차이가 있다는 증거이나 원인 규명 자체는 아니다.

## 3. TDD 공개 CI 및 재발 방지 수정

1. **RED:** 실제 기존 `tools/p2_g07_owner_pregoal_l2.py`가 최초 실패 직전 근거리 빔 분포를 검증 가능한 JSON으로 출력하지 않았음을 새 5개 테스트로 검출. 공개 [#44280935165](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44280935165)에서 해당 함수 import 실패로 RED.
2. **GREEN L0:** Student `tools/p2_g07_owner_pregoal_l2.py`에 read-only `near_ring_fraction()`, `diagnose_pregoal_baseline()` 추가. 실제 `/safety/scan` 콜백에서 360도 근거리 빔과 기존 front/side를 분리 수집하고, **원래 `admit_preloaded_fixture()` 전** `owner_pregoal_baseline.json`을 기록. 실패면 기존 `OWNER_PREGOAL_NOT_CLEAR_BEFORE_FIXTURE`를 그대로 발생시키고 NO_GOAL/HOLD. 0.75/1.20·300/150/120ms 및 Goal/Guard/CM를 바꾸지 않음.
3. **실제 Native L2 최초 회귀:** Student 초기 소스가 기존 4개 `scans` 튜플에 근거리 진단 2개를 합쳐, 후속 `t,stamp,front,side=scans[-1]`에서 `ValueError:too many values to unpack (expected 4)` 발생. 공개 [#44282051585](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44282051585)에서 실제 물리 실행 중 검출 (본래 WSLg 첫 오류 아님). 최소 수정: **기존 4개 Scan tuple 보존** + `scan_ring_metrics` 별도 deque. 테스트 1개를 회귀 추가. 최종 Student SHA `8934f30ed7c497f31f3eeccacab49f5585156fbd`.
4. **L0 GREEN:** 공개 [#44282796951](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44282796951), Student 원본 함수 테스트 6개 PASS. 추가 공개 [#44281901520](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44281901520) 5개 기존 + 사용자 실제 수치 replay 3개 PASS. 변경된 최종 소스에 대해 CI 본문 동일 증거 재확인.
5. **수정된 Student 실제 Native L2 GREEN:** [#44282820380](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44282820380), GitHub Actions HEAD `3e55d613533f14abbb282b2834ba947ef1d90b82`, Student SHA `8934f30ed7c497f31f3eeccacab49f5585156fbd`. 실제 Waffle/Gazebo+RViz X11 2창, G07 Task04 native Goal runner rc=0, 엄격한 21-gate verdict `TASK04_REAL_GAZEBO_MOVING_GUI_L2_SCOPED_PASS`, `first_failure=NONE`. 같은 세션의 새 PRE-GOAL 원본 파일: **front 1.405655m / side 2.519770m**, `BASELINE_CLEAR_NO_GOAL`. 기존 CM source+observer <=120ms, Guard 내부 age<=150ms, Scan<=300ms, Contact0, STOP odom>=1s, 동일 UUID Cancel, SQLite14 messages, Nav2 Navigation+Localization ACK/CM clean exit0을 동일 checker로 검증.
6. **미검증:** 실제 WSLg Intel GPU에서의 원형 센서 거리 정상화, NVIDIA D3D12 선택 시 렌더·센서 성능, 각 환경의 Scan callback <=300ms, 실제 Owner Goal L3. Linux Xvfb의 새로운 PRE-GOAL 정상 거리로 WSLg 문제를 해결했다고 표시하는 행위를 금지.

## 4. 출고 게이트 / 향후 최소 현장 검증

- 공식 Mesa `MESA_D3D12_DEFAULT_ADAPTER_NAME`를 통한 NVIDIA adapter 선택은 **개선 후보**일 뿐입니다. 그 설정만으로 LiDAR 수정 PASS로 인정하지 않습니다. 설정 변경 시 진짜 `glxinfo -B` renderer 변경을 확인하고 동일 월드·ROS LaserScan 360도·거리·수신 주기 및 Guard/CM 120/150ms를 **NO_GOAL**로 선행 측정하십시오.
- WSLg 같은 하드웨어에서 front >0.75m, side >1.20m 그리고 Scan max gap <=300ms가 원형 센서로 실증되기 전, **새 Moving Owner 실행기 출고 `D06_GAZEBO_LIVE_RELEASE=HOLD`**. 기존 마지막 D06 소스를 재실행하는 방식의 현장 반복 검수는 금지.
- 최종 인수 전 `AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false`; SW 정지는 인증된 HW E-Stop 아님. 불필요한 Nav2/Guard 포크, Scenario 변경, main 병합 금지.
- 프롬프트: `d06/docs/AXIA_D06_OWNER_PREGOAL_LIVE_CI_TEST_AND_RELEASE_PROMPT_20261118_KO.md` (실제 임무 지침).
