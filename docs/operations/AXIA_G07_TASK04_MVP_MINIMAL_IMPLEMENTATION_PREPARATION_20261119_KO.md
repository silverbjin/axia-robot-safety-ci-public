# AXIA G07 Task04 — MVP 최소 구현 준비 보고서 (2026-11-19)

## 목적 및 결정

**현재 요청은 구현 전 준비/근본 원인 후보 분리입니다. 이 문서 커밋 자체는 코드 수정·실제 CI 재실행·WSL2 최종 인수를 의미하지 않습니다.**

- 실제 ROS2 Jazzy/Gazebo Harmonic/TB3 Waffle/공식 Nav2/CM/Supervisor 코드 재개발 금지
- 교육 시연 대상: 기존 한 Goal로 CLEAR → 실제 SLOW → 실제 STOP → 해당 UUID CancelGoal
- 유일한 구현 후보: **(A) 장애물 SLOW 위치 변경 시점** 및 **(B) STOP 후 정확 Goal 취소와 진단 순서**
- 현재 CM SLOW 0.75m/STOP 0.40m/ratio 0.30, Scan TTL 300ms, Guard 150ms, Nav2 Goal/Planner/센서 주기 불변
- 형식적 안정성/Localization Lifecycle 종료 고도화는 별도 HOLD; 안전 감시 게이트를 삭제·완화하거나 실제 인증 E-Stop으로 부르지 않음

## 1. 원본 WSL2 증거 무결성 및 최초 위반

Owner 원본은 로컬 제출 `owner-moving-KwcTfR01.tar.gz` 및 `owner-moving-KwcTfR01.diagnostics.zip`; SHA256 원본 sidecar 일치:

- TAR SHA256: `5e2a4d3e88f40171baf02d17a8d30e6bd793472059e02d92c1905c0f48600ec2`
- ZIP SHA256: `3dd85920541b27fb083888bb5c71ea70e4d8994db975f512d576ec0e504ea7e7`
- 내부 rosbag2 SQLite `pragma quick_check`: `ok`, 실제 14토픽 존재
- Owner 실행 소스: Student `2ca257c80fa12f35d801ca525cb16bebbaaa0c8f`; public reviewer `d60beed5e18d8104b254f17476d47f1d1917a7eb`
- public CI 실증 [#44468919246](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44468919246)에서 단계·정확 Goal UUID 취소 확인, 그러나 Localization 종료 FAIL; Owner 원본은 다음과 같음

| 관측 원본 | 실제 값 |
|---|---|
| Goal published (host monotonic) | 2568.451311 sec |
| 마지막 CLEAR LiDAR sample | 2569.493774 sec / front 1.936m |
| 최초 SLOW LiDAR sample | 2569.895793 sec / front 0.615m |
| Observer /safety/scan? 실제 Observer scan event gap | 0.402019 sec |
| SQLite /scan 수신 공백 | 0.401729 sec |
| SQLite /safety/scan 수신 공백 | 0.396857 sec |
| 같은 구간 SQLite /odom 최대 공백 | 0.163619 sec |
| 같은 구간 SQLite /clock 최대 공백 | 0.098609 sec |
| 실제 최종 Odometry 이동량 | 0.085359m |
| 실제 STOP 0 명령 유지 / Odom dwell | CM/Guard final zero, 1.027999 sec |
| first failure | ACTUAL_MOVING_GOAL_CI_ORACLE_SENSOR_DELIVERY_TTL_BOUNDARY_max_scan_interval_sec |
| 첫 guard latch | 없음 |
| 정확 UUID CancelGoal 증거 | 시나리오 함수에서 호출되기 전에 `assess()` 실패. 후속 Nav2 로그의 일반 취소 기록과 구분 |

실제 시간상 장애물의 전방 라이다 거리 점프(1.936→0.615m)와 Scan 402ms 공백이 **동일한 첫 SLOW 전환 구간**에 나타남. 두 스캔 채널에 동시에 나타났으나 Odom/Clock은 계속 도착하므로 전체 ROS 그래프 정체로 단정 불가.

중요: SLOW `move_ci_verified` 호출 시작·ACK의 **host-monotonic timestamp가 현장 로그에 없으므로** Gazebo 서비스가 공백을 일으켰다고 단정하지 않음. ROS bag은 시작 준비 중에도 큰 Scan 공백이 있었으므로 인과를 과대평가하지 않음.

## 2. 다른 개발 브랜치 중복 해결 여부

2026-11-19 원격에서 확인:

- Student `fix/g07-task03-public-proof-20261118` HEAD `2ca257c80fa12f35d801ca525cb16bebbaaa0c8f`: 현장 기준 구현
- Student `fix/g07-task04-owner-timing-evidence-20261119` HEAD `efff0fb8bf941de74572336d1988dfb0005e11f7`: 기존 타이밍 증거 브랜치; 최신 CLEAR/SLOW/STOP 전환 변경 없음
- Student `fix/g07-nogoal-ordered-cm-shutdown-20261119` HEAD `64de9dc02e9073dc1c2898b14c973e38c664ba6e`: NO_GOAL 종료 스크립트만, 본 첫 Scan 공백 및 CancelGoal 순서 해결 아님
- Public CI `fix/g07-task04-owner-wsl2-public-pregate-20261118` HEAD(준비 전) `eb87b62add796c0b473f827026308abb3fa0da34`
- 이미 성공한 Goal/Nav2/CM 코드를 재구현하지 않음; main 병합 보류

## 3. 확정 변경 후보 (최소)

### A. SLOW 장애물 전환과 CLEAR 가시성

파일: Student `block_B/day07/h01_runtime/tools/p2_g07_ci_moving_goal.py`

- 기존 실제 CLEAR 판정(Scan >0.75m, CM/final >0.03m/s, 실행 중인 하나의 Goal)을 유지.
- `start_pose` 대비 `/odom` 실이동을 **bounded CLEAR 시연 기준 0.12~0.15m의 후보값**으로 관찰한 뒤 SLOW `set_pose` 실행; 무한 sleep 금지, 약 8초 내 실제 Goal EXECUTING/Guard 및 기존 demo corridor 유효성 유지.
- 현행 `obstacle_world_pose(...,.62,.07,...)`, `move_ci_verified`, `plan_stop_fixture` 재사용. SLOW/STOP 물리 위치, 맵, Goal, Polygon 자체는 변경 금지.
- `slow_native_request_started_monotonic`/`slow_native_ack_at_monotonic`만 기존 결과 JSON에 기록하고 첫 Scan 공백과 시간 겹침을 확인. 새 ROS 노드/rosbag 주제/진단 프로세스 추가 없음.
- 요청 전후 Guard 정상·실제 fresh Scan/Odom 확인. 이상 시 HOLD. 안전 TTL 300ms 유지.
- 숫자 0.12~0.15m는 **수정 전 후보 범위이며, 실제 실행 성공 수치는 아님.** CI 단 한 번 실행하여 현장 관찰성 중심으로 고정.

### B. STOP 후 Goal CancelGoal을 타이밍 최종 판정보다 먼저

파일: 같은 `p2_g07_ci_moving_goal.py`에서 재사용 `_task03_exact_goal_terminal`의 **호출 순서**만 변경:

1. 실제 STOP 스캔/CM ZERO/최종 cmd ZERO와 1초 이상 Odom ZERO 확인.
2. 같은 UUID가 EXECUTING인지 확인한 뒤 기존 정확 UUID `CancelGoal` 1회 호출하고 ActionStatus=5(취소 완료) 원본 저장.
3. 그 다음 기존 `first_delivery_breach`/초기 안전 위반 기록 및 `assess()` 검사. 402ms 재발 시 타이밍 **HOLD**, 취소 성공을 지우거나 전체 시연 안전 PASS로 위장하지 않음.
4. 중간 예외 시 Owner가 발행한 동일 UUID가 확인되고 상태가 EXECUTING일 때만 bounded best-effort exact UUID 취소를 시도, 재시도 폭주·새 Goal·직접 cmd_vel·강제 재무장 금지. 취소 ACK가 없으면 HOLD와 첫 실패 원인을 유지.
5. 이미 TERMINAL/Guard latched/UUID 불명 때는 '취소 완료'를 만들어내지 않음. 최초 오류와 cleanup 결과를 별도 필드로 남김.

예외 계층은 새 안전 시스템이 아니라 기존 서비스 호출을 안전한 지점에서 재사용하는 수준으로 제한.

## 4. RED → GREEN → REFACTOR → REVIEW → COMMIT 제안

- RED: 작은 ROS-free 계약 테스트 **1개 파일, 2개 케이스만**: (1) 현장 0.402019s Scan gap이 있어도 STOP 후 UUID 취소 기록은 `assess()` 이전에 이루어져야 함; (2) CLEAR 이동 기준 이전에는 SLOW 이동 금지, 기준/타임아웃 이후 Guard/Goal 정상 여부에 따라 진행/중단.
- GREEN: 오직 기존 Student 단일 시나리오 실행기 수정; Safety Supervisor/Collision Monitor/Nav2 자체 미수정.
- REFACTOR/REVIEW: 코드 변경 2개 이하(시나리오와 회귀 테스트) 및 오류 처리 분리; 중복 서비스·추가 계측 금지.
- 한 번의 공개 실제 Gazebo/RViz L2에서 동일 ROS 소스/Goal/Scan/CM/Guard/odom 증거 확인. 통합 CI 실패 시 첫 오류를 분류하고 **같은 현장 재실행을 반복하지 않음**. 후속 Localization 종료 오류는 시연 성공과 정식 인수의 별도 상태.
- CI 성공 범위가 시연 조건을 만족할 때 **그때만** CI SHA와 Student SHA를 고정한 Owner WSL2 원샷 스크립트를 같은 공개 CI 브랜치에 커밋하고 Bootstrap L0 확인.
- 강사 WSL2에서 Goal 수동 승인 `YES-P2-G07-GOAL`으로 **실제 한 세션** 실행; Gazebo/RViz 화면에서 로봇 이동·감속·STOP과 정확 UUID 취소를 확인. SHA256과 소형 ZIP만 제출. 이 전까지 Owner L3=HOLD.
- Main 병합은 사용자 승인 전 금지. 공인 E-Stop 아님. 목표 외 반복 CPU/RMW/RTF 장기 안정성 실험은 진행하지 않음.

## 5. 실제 준비 단계 검증과 미검증

현재 수행: 업로드 SHA256 비교, rosbag SQLite quick_check, 14토픽과 실제 원본 callback interval 분석, GitHub 브랜치/시나리오 코드 read-only 확인. **이번 준비에서 ROS2/Gazebo 재실행·새 단위 테스트·코드 수정은 수행하지 않음.**

검증 수준: 원본 L3 실패 원인 분류와 코드 변경 지점 확정까지만 (L0 분석). `AXIA_MVP_DEMO_ACCEPTED=HOLD`, `CERTIFIED_ESTOP=false`.

미검증: 장애물 변경 CLI가 Scan 402ms 공백을 직접 일으켰는지, 0.12~0.15m CLEAR 지연이 시연성 및 300ms TTL 둘 다 만족하는지, 비정상 exact UUID 취소의 현장 도달 여부, 새 단일 통합 CI와 Owner WSL2 최종 결과.
