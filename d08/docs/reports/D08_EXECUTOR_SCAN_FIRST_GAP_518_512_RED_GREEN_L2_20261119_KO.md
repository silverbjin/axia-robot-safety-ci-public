# AXIA D08 — 최초 Scan 518.394ms 원인 분리 및 Executor A/B 검증 보고서
**일자:** 2026-11-19 (KST)  
**성격:** 교육용 RED→GREEN→Gazebo L2 증거 보고 / 릴리스 HOLD  
**공개 저장소:** `silverbjin/axia-robot-safety-ci-public`  
**개발:** [Draft PR #181](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/181), `fix/d08-scan-independent-ros-process-20261119`  
**검증된 진단/실험 코드:** `ed056f9662e2b2621e464f47a5908357df38a905`  
**중요:** CI가 L2 PASS라는 이유로 WSL2 Owner 현장 L3 또는 실제 CM/Guard/E-Stop을 승인하지 않는다.

## 1. 재현된 현상과 최초 안전 경계

| 최초 관측 | 실제 원본 증거 | ROS Observer Scan 수신 공백 | 결과 |
|---|---|---:|---|
| Owner WSL2 | `run_20261118T143911Z_VG0B5q.diagnostics.zip` (SHA256 `d5eafa80295d89d4713da7532b651e9b8ff5f64c49285025586891bc49cdb2eb`, 26/26 내부 SHA PASS) | **518.394ms** | HOLD |
| 공개 Gazebo + 공식 Nav2 | [Run #44312306299](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44312306299) | **505.365ms** | L2 FAIL |
| 후속 공개 Gazebo | [Run #44362964527](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44362964527) | **515.572ms** | L2 FAIL |
| 원천 프로브 사전기동 이후 | [Run #44364535033](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44364535033) | **667.085ms** | L2 FAIL |
| heartbeat 설치 이후 | [Run #44429198861](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44429198861) | **512.136ms** | L2 FAIL |

첫 안전 타이밍 위반은 **실제 ROS LaserScan callback의 host-monotonic 수신 간격이 500ms를 넘은 시각**이다. 원본 LaserScan header의 시뮬레이션 stamp 간격(약 99ms)이나 그 이후의 메시지 몰림·정상 Path 결과로 최초 위반을 소급 PASS 처리하지 않는다. 기존 코드 `D08_FIRST_REAL_SCAN_RECEIVE_GAP_OVER_500MS`의 FAIL-CLOSED 동작은 올바르게 보존됐다.

기존 AMCL 서비스 탐색 콜백 정체 수정 SHA `62d7e94abe2828792be32231e5ab79cdc6620f5f`, 원래 [GREEN Run #44306208316](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44306208316) 및 AMCL blob `f44ffe3aa67bbbde03a28319d0db3587742b6f52`는 재개 후에도 변경되지 않았다.

## 2. 계층별 동시간 계측: 최초 위반은 어디에서 발생했는가?

실제 [Run #44364535033](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44364535033)의 최초 667.085ms 구간(같은 두 LaserScan stamp 46.701→46.800초)에 대한 비교는 다음과 같다.

| 같은 원본 메시지 | host 수신 간격 |
|---|---:|
| Gazebo native Transport의 독립 /scan 구독 | **163.704ms** |
| **별도 Python 프로세스**의 독립 ROS /scan 구독 | **163.089ms** |
| 원래 Observer의 ROS /scan | **667.085ms** |
| 원래 Python 프로세스의 또 다른 ROS Executor | **709.067ms** |

즉 **667ms 추가 지연은 Gazebo native LiDAR와 공통 ROS Bridge 이전이 아니라, Observer가 속한 Python 프로세스 측 수신/디스패치 경계**에서 나타났다. 당시 원래 Scan callback의 처리 시간은 약 0.302ms 이하여서 단순 sector 계산이 667ms 소요됐다는 가설은 지지되지 않는다. 최초 지연은 CM/ROS graph/`gz set_pose` 호출이 시작되기 전이므로, 그 호출이 *그 최초* 위반을 직접 유발했다고 해석하지 않는다.

또한 [Run #44360979382](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44360979382)의 근접 공백 397.203ms는 native 139.462ms, 별도 ROS 139.660ms, 원래 Observer 397.203ms, 같은 Python의 ROS Executor 397.139ms로 동일 경계 패턴을 확인했다.

## 3. RED→GREEN 회차별 검증

### 3.1 SingleThreadedExecutor 단독 A/B

- RED SHA `3a012a641788e5e5dba9de2bd162e96819e837d7`, [Run #44367381479](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44367381479): `1 failed, 165 passed`; 실패한 계약은 기존 `MultiThreadedExecutor(num_threads=2)`의 한 줄을 지목.
- 최소 GREEN SHA `06f28e31c7d300e43a87e13aac51108b20b4d2fa`, [Run #44427732318](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44427732318): `166 passed`, 공식 Gazebo/Nav2 8사이클 L2 PASS.
- **그러나** 동일 수신 메시지 native 134.642ms / 별도 ROS 135.729ms인데 같은 프로세스 Observer는 **452.655ms** 지연. **MultiThreadedExecutor가 단독 원인이라는 가설을 승인할 수 없다.**

근거: [ROS 2 공식 콜백 그룹 설명](https://docs.ros.org/en/jazzy/How-To-Guides/Using-callback-groups.html). 기본 MutuallyExclusive 그룹만 있는 경우 스레드를 늘려도 같은 그룹 콜백은 병렬화되지 않는다. 이것은 A/B 선택의 이유이지 원인 확정 근거가 아니다.

### 3.2 프로세스 20ms heartbeat와 원래 Scan gap

- RED [Run #44428869885](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44428869885): `ImportError: cannot import name 'analyze_process_heartbeat_gap'`.
- GREEN `2412ccf03c0fd48d4850e7d38e9a9c172f2d8a2b`, [Run #44429198861](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44429198861): L0 **170 PASS**, **실제 Gazebo L2 FAIL**. 첫 Scan 512.136ms 위반은 그대로 HOLD.
- 실제 source stamp pair at 65.301→65.400s: native 228.366ms, 독립 ROS 프로세스 228.088ms, 원래 Observer **512.136ms**, 같은 Python ROS Executor **523.325ms**.
- 그동안 **일반 Python heartbeat의 최대 간격은 23.468ms**, 같은 구간 process_cpu/host 약 0.104였다. 따라서 **프로세스 전체 중단/GIL 독점만으로 이 장애를 설명하는 가설은 약함**. ROS Executor/공유 rclpy/RMW 경계를 우선 조사해야 한다.
- 이 위반의 일부가 `gazebo_native_set_pose` 구간과 겹쳤으나 **시간적 중첩은 인과관계 증명이 아니다**.

**원본 L2 evidence ZIP #14486056382**, 복사본 SHA256 `1eaac632878c499dc23381c4cdcf199bf8b561334dc7ede1bf58c4030ab6afe5`, CRC PASS.

### 3.3 Executor 스택의 한정 계측

- RED [Run #44430382969](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44430382969): `classify_executor_stack_frames` 부재.
- GREEN SHA `9b091703436ee9fd97ce15c13556701f78265128`, [Run #44430726549](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44430726549): L0 **174 PASS**, Gazebo/Nav2 8사이클 **L2 PASS**. 실제 379.737ms 근접 구간에서 Observer 및 같은 프로세스 독립 ROS Executor 모두

```text
executors.py
 spin
 _spin_once_impl
 wait_for_ready_callbacks
 _wait_for_ready_callbacks
```

에서 포착됐다. 그러나 **이 구간에서 Python heartbeat도 294.397ms 멈췄다**(process_cpu/host 약 0.082). 즉 정상 heartbeat인 512.136ms 위반과 다른 양상도 실제 존재한다. 스택은 Python 프레임만 보여 주므로 `rmw`/DDS 내부 호출 원인을 확정할 수 없다.

원본 L2 ZIP #14486017997, SHA256 `43ec137ebbe93c228f5b4f08329629e7ff7b945742d9731dc19fe3e8b4db9131`, CRC PASS.

### 3.4 Executor 50ms bounded wait A/B (현재 진단 후보, 릴리스 미승인)

- 단일 가설: rclpy 대기 상태가 길게 지속되므로 D08의 **read-only Observer 두 Executor**만 `spin_once(timeout_sec=.05)`로 제한해 wait-set을 주기적으로 재평가하면 first Scan 지연이 줄 수 있다.
- RED [Run #44431701052](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44431701052): `2 failed, 174 passed` (bounded wait 계약 부재).
- GREEN SHA `ed056f9662e2b2621e464f47a5908357df38a905`, [Run #44431911431](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44431911431): L0 **176 PASS**; **실제 Gazebo·공식 Nav2 8사이클 × 3회 = 24사이클 PASS**.

| 동일 검증 SHA의 실제 L2 독립 Job | GitHub Job ID | 원본 evidence artifact | 최장 Observer receive gap | 판정 |
|---|---|---|---:|---|
| 1회 | `135251255422` | `14487093104` | **370.251ms** | PASS |
| 2회 | `135253576341` | `14487278843` | **268.536ms** | PASS |
| 3회 | `135255989158` | `14489080017` | **437.558ms** | PASS |

모두 **real Gazebo same-world Waffle / 공식 Nav2 경로 8/8**, 원래 Scan 500ms 첫 위반 없음, 아티팩트 ZIP CRC PASS. 각 evidence 사본의 SHA256은 순서대로 `2a101b111b38bf5abae039bbfe9e6cd8138ec4fb726cfb368fdeaf5bf543e831`, `372f2980df147ffe1bec48843ea3357db4c8c3da285c8856e89aa03aef57fe08`, `bb0f7bf61c0d36ec42044204d11e03748ba2705950ee7f71a3f89bec6f652939`.

**하지만 3회차 중에도 같은 message pair에서 원천 Gazebo 159.463ms, 별도 ROS 159.799ms, 원래 Observer 437.558ms, 같은 Python Executor 440.813ms**가 관측됐다. 따라서 관측 지연이 사라진 것이 아니고, bounded wait 한 가지가 근본 원인이라는 명제도 증명되지 않았다. 과거 첫 518.394ms WSL2 실패의 동일 함수/스케줄링 원인 확정은 더욱 불가능하다.

## 4. REVIEW: 범위, 릴리스 게이트, 다음 원인 분리

**검증 수준**

- **L0**: 관련 순수 계약/계측/첫-위반보존 포함 **176 PASS** (SHA `ed056f...`).
- **L1**: 이 사이클의 독립 ROS/CM 실제 L1 acceptance를 수행했다고 보고하지 않는다.
- **L2**: 동일 SHA의 실제 Gazebo + 공식 Nav2 No-Goal 경로 **3회×8사이클 PASS**. 별도 Goal/Twist, YOLO/Contact Job은 의도적으로 **SKIPPED**, 전체 CI 4-job PASS가 아님.
- **L3 Owner WSL2/WSLg**: **NOT_RUN**. GPU 픽셀 및 Gazebo GUI Owner 현장 인수도 미수행.
- **다른 안전 계층**: Collision Monitor 내부 데이터 수신 주기, Guard TTL 및 SW STOP/SLOW·실제 인증 E-Stop은 **NOT_VERIFIED**.

**최종 원인 판정**

1. 확인된 타이밍 경계: Gazebo 원천과 독립 ROS 프로세스는 정시로 수신한 동안 원래 Observer Python 프로세스의 두 ROS Executor가 동시에 지연된 **같은 source-stamp 메시지 쌍**이 존재한다.
2. 512.136ms 실제 위반에서는 Python heartbeat가 정상이므로 프로세스 전체 멈춤만으로 설명하기 어렵다. 379ms 근접 구간에서는 heartbeat도 멈췄으므로 **두 현상이 한 가지 원인이라고 단정해서는 안 된다**.
3. Executor 스택 `_wait_for_ready_callbacks`는 측정되었지만 `rclpy` wait-set / RMW 내부 / OS 스레드 runqueue 중 **어느 함수·상태가 근본 원인인지는 아직 확정되지 않았다**.
4. 50ms bounded wait는 **단일 진단 A/B 후보**다. 24사이클 PASS를 넘어 근본 원인/간헐적 재발 억제까지 인수할 증거는 없다. **MVP 범위를 넘는 주행 알고리즘/Planner/Safety Supervisor/TTL 수정은 금지**한다.

가능한 다음 단일 가설은 Executor Python 스레드가 실제 OS 스케줄러에서 지연됐는지 여부이며, 필요하다면 Linux `/proc/self/task/<native_tid>/schedstat`의 read-only runqueue delay를 *첫 위반 시점에만* 조회해 ROS wait-set 대기와 구별하는 회귀로 한정해야 한다. 현재는 그런 실측이 없으므로 OS 스케줄링 문제를 **확정하지 않는다**. 같은 현장 오류의 재시도만 반복하지 않는다.

### 릴리스 Verdict

```text
D08_AMCL_PREVIOUS_GREEN_EVIDENCE=PRESERVED
D08_FIRST_SCAN_FAIL_CLOSED_500MS=PRESERVED
D08_EXECUTOR_BOUNDED_WAIT_L0=PASS_176
D08_EXECUTOR_BOUNDED_WAIT_REAL_GAZEBO_L2=PASS_3X8
D08_ROOT_CAUSE_CONFIRMED=NO
D08_FIRST_SCAN_GAP_FIELD_FIXED=NOT_VERIFIED
D08_CM_INTERNAL_RX_TTL=NOT_VERIFIED
D08_GUARD_TTL=NOT_VERIFIED
D08_OWNER_WSL2_L3=NOT_RUN
D08_LIVE_NO_GOAL_ACCEPTED=HOLD_OWNER_L3
D08_G07_MOVING_E2E=HOLD
D08_MAIN_MERGED=NO
```

**브랜치/커밋:** 진단 후보 `fix/d08-scan-independent-ros-process-20261119` HEAD `ed056f9662e2b2621e464f47a5908357df38a905`, Draft PR #181. 교육용 문서는 `docs/d08-executor-512ms-rca-20261119`에 별도 커밋하여 실제 L2 검증 SHA를 이동시키지 않으며, **main 병합은 사용자 승인을 받기 전 수행하지 않는다**.
