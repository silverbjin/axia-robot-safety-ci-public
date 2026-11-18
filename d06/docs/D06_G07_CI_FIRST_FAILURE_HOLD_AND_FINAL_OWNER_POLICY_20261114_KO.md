# AXIA D06 G07 — 공개 CI 중심 최초 실패 분석 및 WSL2 최종 인수 조건

**기준:** ROS 2 Jazzy / Gazebo Harmonic / 공식 Nav2 Collision Monitor / TurtleBot3 Waffle. 전용 D06 화면은 기존 비공개 Instructor G07 Goal Owner를 재사용하며 새 안전 노드를 개발하지 않는다.

## 1. 첫 안전 상태 전이 (Owner WSL2 원본, 2026-11-14)

| 원본 | 최초 기록된 위반 | 이후 안전 전이 | 판정 |
|---|---|---|---|
| IB7mAJRW | /cmd_vel_pre_guard callback 172.739ms > 150ms | Guard CM age 181.552ms, UPSTREAM_STALE_AFTER_MOTION | BLOCKED |
| Nfb3pALe | /scan callback 364.642ms > 300ms | 수초 뒤 Guard CM age 153.018ms > 150ms, UPSTREAM_STALE_AFTER_MOTION | BLOCKED |

Nfb3pALe에서 먼저 발견된 Scan 위반이 나중의 Guard 래치를 **유발했다는 증거는 없음**. RMW CM-vs-Supervisor 윈도우는 NO_CM_SOURCE_GAP_OBSERVED, classification=UNVERIFIED. Supervisor NORMAL, Goal 승인된 상태에서 Guard fail-closed 정지 명령 출력. 정상 STOP 구역 진입 및 /odom 정지 1초를 대체하지 않는다.

## 2. 공개 GitHub Actions — 비공개 소스 유출 금지

- Public CI repo: silverbjin/axia-robot-safety-ci-public
- D06 feature / Draft PR #108: feature/d06-gazebo-rviz-owner-20261114
- Actual real Gazebo L2 workflow, only authorized public release branch: release/p2-g06-cm-ttl-20261110 / .github/workflows/d06-g07-real-moving-timing-l2.yml
- Instructor pinned private source SHA: afe4e9ae3f6542ef7b2bd3097ce5c15ae5a5ddcc, runtime immutable image digest ghcr.io/silverbjin/axia-g07-runtime@sha256:861ae1df0560f991698d8967193380b1619589ba7770b5e2ca91ea4ef31f0c8e
- CI-only single simulation Goal authorization is isolated from owner real TTY YES-P2-G07-GOAL. No private Actions or public raw rosbag, private solution, UUID, original Owner paths.
- Fail-first diagnostics separate PRE-GOAL STARTUP, PRE-GOAL PHYSICAL, GOAL SAFETY LATCH/TIMING, POST-GOAL CLEANUP. No rc3 masking of earlier fault.
- Guard CM 150ms and Scan 300ms TTL UNCHANGED, hardware E-Stop not certified.

## 3. 실제 측정 — L0/L1 PASS != 실제 L2 전체 PASS

Public CI feature HEAD 8552e4fa061f60b3be9caf23d668b7b306bbf44d:
- Actions #43587253029: 32 pytest PASS; real Jazzy ROS L1 and real Xvfb RViz2 L1 PASS; NO actual Gazebo moving Goal.

Actual public CI L2:
1. #43585912040: real G07 moving Goal CLEAR/SLOW/STOP, Scan max 198.075ms, CM max 135.023ms, odom STOP dwell 1.00166s; no Guard latch. But post-Goal runner rc3, overall FAIL; underlying first teardown reason not identified by initial sealed log setup.
2. #43586564811: no Goal evidence and runner rc3; early phase failure cannot be called post-Goal cleanup. HOLD.
3. #43587404886: Actual real Gazebo G07 Goal, CM RMW **source publication** gap 172.152953ms (consecutive publication sequence gap 1), observed callback 170.878ms, three Supervisor publications within gap, Supervisor max coverage gap 50.078ms, Scan max 194.329ms, odom dwell 1.00604s. Original quantitative CI oracle FAIL due CM 150ms; Guard internal latch absent in this example. RMW classification CM_POST_INPUT_EXECUTION_OR_SCHEDULING_GAP_CANDIDATE, **callback processing vs OS scheduling cause NOT PROVEN**. Full L2 FAIL.
- All three are separate CI real-Gazebo runs and must NOT be conflated with successful Owner WSLg simultaneous GUI+RViz2.

## 4. Official Jazzy code semantics: do NOT introduce fake frequency tuning

Source: https://api.nav2.org/nav2-jazzy/html/collision__monitor__node_8cpp_source.html
Nav2 CollisionMonitor::cmdVelInCallbackStamped -> process(...) -> publishVelocity(...). It consumes input Twist, collects collision points and checks zones; no independent fixed monitor frequency parameter to tune in its published parameter contract.
https://docs.nav2.org/jazzy/configuration_and_development/configuration_guide/core_servers/collision_monitor/configuring_collision_monitor_node/

CollisionDetector (a **different** node) has frequency: 10.0:
https://docs.nav2.org/jazzy/configuration_and_development/configuration_guide/core_servers/collision_monitor/configuring_collision_detector_node/

Do NOT change actual collision_monitor.frequency, Guard 150ms threshold, scan 300ms TTL, source_timeout, base_shift_correction or certified E-Stop handling without a separate measured safety regression. Real 172ms CM source interval is not evidence for one specific internal callback bottleneck.

## 5. Admission policy for classroom and final Owner WSL2

**NOW: CI_G07_FULL_DEMO_HOLD; OWNER_WSL2_FINAL_NOT_ADMITTED**.

One successful real moving Goal with a failing teardown is scoped evidence only. Multiple genuine CI L2 failures prevent final release even when an intermittent run succeeds. Before final Owner test:
1. Identify the first RMW source-vs-received CM callback gap and why the input continued while output source gap exceeded 150ms; do not infer causality without instrumentation.
2. RED->GREEN for targeted cause with same real L2 full stack; single Goal CI with continuous Scan <=300ms, Supervisor/CM/Guard <=150ms, physical /odom zero dwell >=1s and COMPLETE native Nav2 lifecycle ACK + CM clean exit + original 14-topic bag check.
3. Review source lock / safety policies / no private leak; publish approved exact source SHA from public CI.
4. ONLY THEN one classroom WSL2 final Owner acceptance: WSLg Gazebo GUI+RViz2 simultaneous, one TTY-authorized Goal, first safety timing, odom STOP and clean teardown. CI Linux container is not WSLg timing parity.
5. Any new WSL2 failure becomes sanitized public CI regression before retest; no repeated field-only attempts.
6. If live G07 stays HOLD by class, use existing **official isolated Collision Monitor L1** teaching demo, and use public historical G07 L2 evidence with explicit date and **NOT today's new WSL2 pass**. This fallback meets D06 *policy/TDD understanding* but does not represent live moving G07 acceptance.

**No change to main; no instructor answer in Student repo; no certified hardware E-Stop claims.**
