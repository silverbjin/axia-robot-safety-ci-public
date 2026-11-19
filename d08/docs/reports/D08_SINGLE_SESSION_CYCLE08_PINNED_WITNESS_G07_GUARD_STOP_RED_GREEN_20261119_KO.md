# AXIA D08 Cycle 08 — 동일 원본 Native Contact 재사용·G07 200ms Moving 안전 첫 경계

2026-11-19 KST · Public Draft PR #189 / Student Draft PR #63 · **L0 + source L1 GREEN, REAL Moving L2 HOLD, Owner L3 NOT RUN.**

## 1. 실제 CI 첫 실패와 최소 환경 수정
- Cycle07 수정 Student `d94a0f7090c976d4b0c9e57bb449581e96243bf1`, Public `e7ec03da6d1684c693b8366ee6b99f17d169db9f`.
- [공개 #44510477082](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44510477082): D08 240/240 PASS, Student 4+4+2/2 PASS, 공식 Jazzy/G07 World/SDF source PASS. Native Witness 빌드 작업 **APT exit100**:
```text
E: Failed to fetch http://security.ubuntu.com/ubuntu/dists/noble-security/main/binary-amd64/Packages.gz
File has unexpected size (1474828 != 1474838). Mirror sync in progress?
```
- 이는 **ROS/Gazebo 실제 실행 이전**의 미러 인덱스 오류. 현장 재시도나 G07 안전 로직 수정으로 해결할 대상이 아니다.
- 성공한 [이전 Public G07 job #44504838398](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44504838398)의 Native S02 Witness artifact #14518399790을 정확히 재사용. 기존 Student `0890f971...`과 최신 `d94a0f7...`의 `block_B/day07/h01_runtime/tools/native_s02_public` Git Tree SHA **`569d7cfd8590d38f17eb470f997f0170681e5fdf` 동일**. Raw binary `libaxia_g07_s02_ecm_witness.so` SHA256 **`1e2dd3ad4a7d445b981ca3df9677ea7c88a680a1e6b10d04084873cd578f7ba8`**, ZIP CRC PASS. ABI 검수 `ldd` 및 런타임 transport13.6 체크 유지.
- 수정 경로: `.github/workflows/d08-main-no-goal-real-gazebo-l2.yml`: 사용하지 않는 APT 빌드를 자격 증명 actions:read의 pinned `actions/download-artifact@v4`로 대체; 동일 run에 SHA가 검증된 artifact 재업로드. 원본 C++ 코드·Safety/Goal/P1 시스템 미수정.
- 주의: 기존 artifact 보존 7일. 단기 MVP CI 재사용이며 영구 바이너리 배포에 의존해서는 안 된다.

## 2. 실제 원본 GREEN/L2 RED
- 정확한 Public 소스 SHA **`9b2eca1876ec3ec797d0c36b8f82899a8312f31d`**, [공개 Run #44511494053](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44511494053).
- D08 L0 **240 passed**, Student 연결 4 / D08 TF 4 / CLEAR timeout 2 각각 PASS, 실제 공식 Jazzy/G07 Xacro Source L1 PASS, Native Witness pin SHA 재사용 job PASS, Gazebo/RViz 실제 GUI 둘 다 존재.
- 기존 G07 `transform_tolerance=0.2`, `base_shift_correction=false`, `source_timeout=1.0`, `stop_pub_timeout=5.0` **실제 Collision Monitor native GetParameters 읽기 PASS**.
- CLEAR 실제 `front_m=2.050755`, Supervisor/CM/Final `vx=0.036409m/s` PASS.
- SLOW 실제 `front_m=0.731325`, Supervisor `vx=0.027489`, CM/Final `vx=0.008247m/s` PASS.
- **STOP 중 최초 Guard hard150ms 위반**:
```text
AXIA_G07_PUBLIC_CI_FIRST_GUARD_LATCH_INTERNAL
  reason=UPSTREAM_STALE_AFTER_MOTION
  first_guard_tick_monotonic=198.793267466
  guard_cm_last_receive_monotonic=198.624180206
  guard_cm_age_ms=169.087 (>150 by 19.087ms)
  supervisor_age_ms=16.839 (NORMAL, GOAL_AUTHORIZED)
AXIA_G07_PUBLIC_CI_FIRST_CM_GUARD_RECEIPT_SKEW
  observer_cm_age_ms=166.184
  guard_minus_observer_age_ms=2.903
AXIA_G07_PUBLIC_CI_MOVING_GOAL_BLOCKED
  RuntimeError:GUARD_LATCH_DURING_STOP:UPSTREAM_STALE_AFTER_MOTION
AXIA_G07_TASK04_NATIVE_ONE_MOVING_RUNNER_RC=2
```
- 독립 Observer와 Guard CM 수신 age가 거의 동시에 150ms 초과 → **Guard 전용 지연보다 CM source 발행 또는 공통 DDS/호스트 dispatch 지연이 더 유력한 '후보'**. Publisher rcl timestamp/CM callback trace가 없으므로 `cause=UNDETERMINED`; 실제 인증 또는 CM source root cause 증명 아님.
- Numeric evidence artifact #14523712358 `d08-g07-same-world-moving-numeric-44511494053` ZIP SHA256 `9023984906110526cfc113d33cfd6b650d8726283a5cc85a1dc7894505bdac65`, 5-file allowlist, CRC PASS. `first_guard_ttl_boundary.json`: `moving_l2_accepted=false`, `cm_guard_150ms_safety_contract_pass=false`, no raw rosbag/models/private answers.
- 이전 standalone G07 성공·D08 NO_GOAL 성공을 동일 Moving E2E PASS로 합산하지 않는다.

## 3. 교육용 원인 분리 — 확정과 미확정
- **확정:** 20ms 후보 실행에서 CLEAR 속도 기준 미달; G07 200ms 복귀로 CLEAR/SLOW 도달; 그러나 STOP 최초 CM 전달 지연 169.087ms 및 정상 Guard 차단.
- **미확정:** CM publish 자체가 비었는지, official TF lookup/CM callback이 오래 수행됐는지, ROS RMW 공통 수신 경로가 밀렸는지, WSLg GPU/CPU 스케줄링 때문인지. 현재 L2의 STOP RPC와 동일 시간이 겹친다는 것만으로 인과 증명 금지.
- 이전 G07 공개 교육용 Cycle26 보고서와 Cycle28 보고서: CM source 최초 >120ms/150ms 공백, `/proc`에서 실제 runnable wait만으로 전체 지연 설명 불가; 기존 `d06/live/g07_cycle29_first_cm_callback_trace.py`, `g07_cycle30_bounded_cm_trace.py`, `g07_cycle31_cm_topic_callback_identity.py`를 재사용할 근거. 새 safety algorithm/CM/Guard node 작성 금지.

## 4. 다음 작업과 원샷 인수 차단
1. 기존 공개 Cycle29~31 LTTng/reusable trace에 실제 G07 STOP 첫 `CM→Guard` 위반 경계만 연결. `rclcpp_callback_start/end`, CM publish, Guard take vs independent Observer를 **같은 단일 주행의 mono timeline**으로 비교. 동일 위반 현장 재시도 반복 금지.
2. 최초 원인 확인 시에만 **최소** ROS callback/scheduling 설정 수정. 현행 CM source 120ms/Guard 150ms TTL과 Scan 300ms 불변. 수정 후 다른 안전 계층 timing 동시 검증.
3. D04 C++ YOLO + D05 실제 Depth ROI 2VALID/UNKNOWN + D07 Nav2 공식 3상 Path는 G07 Goal 전 read-only stage 코드까지 연결됐으나 **새 통합 실 Gazebo 같은 세션 L2 미실행**, `AXIA_D08_G07_READONLY_STAGE` 기본 OFF. L2가 먼저 PASS해야 Owner WSL2 L3 스크립트를 출고한다.
4. PR #189/#63 Draft 유지, 공개 main·Student main·Instructor main 미병합. 강사 정답 비공개. SW Stop은 인증 E-Stop 아님.

검증: **Public L0 GREEN, pinned official Source L1 GREEN, actual same-world G07 Moving L2 FAIL 169.087ms, whole D04~D07 single-session L2 HOLD, Owner WSL2 L3 NOT RUN.**
