# AXIA D08 / G07 — 최초 안전 타이밍 경계 감사 및 신규 RMW 최소 계측 (2026-11-21)

**현재 판정: ROOT_UNDETERMINED / PUBLIC_L0_GREEN / OWNER_L3_HOLD**  
기준 계획 Public 66a260f428f2191ef21a52b194140bbe8f120674. 신규 Public Draft PR #215 / diag/g07-first-scan-rmw-exact-native-20261121.  
본 문서는 진행 중인 실제 native 진단을 성공으로 보고하지 않습니다. 인증 E-Stop과 SW STOP은 서로 다릅니다.

## 1. 브랜치·선행 이력 중복 감사

Public/Student/Instructor의 G07·D08 개발 브랜치 및 관련 PR을 점검하였습니다. 기존 증거 보존: Public #161 (CM Advanced TF polling의 제한된 원인), D08 #180 (Gazebo native read-only Scan receiver), Public #207 (첫 Scan 317.943ms), Public #210/#211/#212/#213/#214, Student #73/#79/#80/#83/#84/#86/#88. 비공개 강사 증거를 공개 저장소로 이동하지 않았습니다.

- #211 / Student #83: 첫 Observer lock/JSON/write/flush stall root 미증명.
- #212 / Student #84: Clock 12s retention과 postGoal graph 개선 후 실제 L2 0/2 실패.
- #213 / Student #86: 공식 EventsExecutor CI A/B 실제 L2 #44861540326 0/2 실패. 채택 금지.
- #214 / Student #88: 첫 HEALTH ledger, 정확한 Scan Header에 대한 RMW MessageInfo source/received/sequence 추출 코드 존재. 기존 native는 추가 코드 이전 Student SHA로 실행했습니다.

## 2. 실제 첫 안전 전이와 타이밍 위반

### Native #44861540326

Cycle 1의 최초 안전 진입 위반은 Goal 이전 12초 preflight에서 Clock host gap 331.671633ms(한계 300ms)입니다. 같은 창의 Scan Observer 385.643415ms, 정확한 두 Scan Header sim 간격 99ms, 독립 rosbag의 같은 Header pair /scan 83.539915ms입니다. 독립 recorder Clock max476.612466ms와 Odom max369.490976ms는 세션 전체 최대값이지 첫 Scan과 동일 창 증거는 아닙니다. Goal 미발행, 실제 CLEAR→SLOW→STOP 전이 및 Cancel/Shutdown 미검증입니다.

Cycle 2는 preGoal Scan PASS 이후 EventsExecutor spin worker의 SystemError: null argument to internal routine가 먼저 발생했으며, 이후 CI_MOVING_GOAL_TIMEOUT_HEALTH, 최종 AXIA_G07_CI_MOVING_GOAL_ACTUAL_NAV2_BLOCKED 순서였습니다. 최종 Nav2 blocked만으로 Nav2 근본 원인 또는 물리 STOP 판정을 해서는 안 됩니다. Goal 미발행, 최초 Supervisor 안전 상태 전이는 이 증거에서 미확정입니다.

### Native #44863792399

Goal 이전 Clock first gap 337.093495ms, Scan Observer gap424.373456ms vs Header sim gap99ms, 독립 rosbag exact Scan pair101.297422ms. Odom session max343.795109ms, Clock session max335.607688ms. 12s 평균 RTF 1.026597과 최초 Scan gap 주변 local RTF0.227495는 서로 다른 통계입니다. 이 Run은 후속 Student RMW pair 계측 이전 SHA였으므로 RMW root는 미분류입니다.

## 3. 신규 구현 경계 / RED → GREEN

**Student 기존 PR #88 HEAD:** 8bc6826eed88726c166118dfb2b8d7425bafc574. 이번에 학생 소스의 신규 수정은 하지 않았습니다.

**신규 Public 파일**
- d06/diagnostic/g07_first_scan_pair_attribution.py : 같은 Scan Header exact bag pair와 원 Observer RMW interval/sequence를 별도 판정. 시계 절대값 혼합 금지, Clock/Odom 전역 최대를 첫 Scan window로 승격 금지. 항상 root_cause_proven=false / release=HOLD.
- tests/test_g07_first_scan_rmw_evidence_export.py : #448615 실제 숫자와 #448637 숫자(명시적 synthetic RMW 조건), 누락 seq/시계 위반/헤더 불일치 회귀 4건.
- .github/workflows/axia-g07-first-scan-rmw-pair-l0.yml : 최초 수치 회귀.
- .github/workflows/axia-g07-original-multi-first-scan-rmw-native-l2.yml : 기존 #214 native의 한 번짜리 진단 분기. 원래 MultiThreadedExecutor 2-worker, Student PR #88 exact SHA, first_scan_rmw_pair 숫자만 allowlist, 기존 12s preGoal/Goal/Guard/CM/Nav2 fail-closed 규칙 유지.

**실제 공개 GitHub Actions**
- RED #44864467752 / Public SHA a76329f14fa9adf5aa87354d3d298949238d3575: ModuleNotFoundError, 예상한 신규 분류기 부재.
- RED #44864544851 / Public SHA 166ef1fa5209614be93bd53d23a1ec7a98a240ce: 3개 수치 테스트 성공, 신규 native workflow 부재로 예상한 실패.
- GREEN #44864568449 / Public SHA 48727efed93a564e8acccae1cecb8783d1a6072e: Ran 4 tests / OK.
- 전체 Public 계약 #44864572718 / 같은 SHA: 313 passed, 3 skipped.
- 실제 native 단일 계측 #44864568561 / 같은 SHA: 결과 조회 전이므로 잠정 HOLD. 이 진단이 PASS해도 FULL L2 2/2나 Owner L3 PASS가 아닙니다.

테스트 명령 (GitHub Actions 실제 수행):
    python3 -m unittest discover -s tests -p 'test_g07_first_scan_rmw_evidence_export.py' -v
    python3 -m pytest -q -ra tests

## 4. 코드 Review와 통과/미검증 경계

Review 기준 diff: Public 4afc6f0... → 48727efe..., 신규 진단 Python·테스트·복제된 CI workflow만 변경되었습니다. 공식 Nav2/Collision Monitor/TurtleBot3/Guard/Supervisor 소스, 모든 publisher, 안전 임계값, Goal authority 및 Owner WSL2 스크립트는 수정하지 않았습니다. 새 workflow는 두 GUI가 필요한 실제 시뮬레이션 진단이지만 인수용 2/2가 아닌 단일 Run입니다.

필수 불변 한계: Scan/SafetyScan/Odom/Clock 300ms, CM 120ms, Guard 내부 age 및 전파 150ms; 정지 후 odom zero 1초, 정확한 Goal UUID Cancel ACK, Nav/Loc clean ACK, CM/Guard exit0, raw rosbag 14 topic custody.

미검증: 이번 native 첫 위반의 유효한 RMW publication sequence, Gazebo native publish → bridge → RMW exact pair, 실제 Moving Goal 독립 cold-run 2/2, NVIDIA WSL2/WSLg 현장 L3, 실제 첫 CLEAR→SLOW→STOP/정상 종료. 어느 하나라도 미확인이면 전체 시연 안정성 RELEASE=HOLD입니다.

**다음 판정**: Native #44864568561의 최초 PREGOAL / first_scan_rmw_pair / exact rosbag pair / 첫 HEALTH 전이를 우선 검토. RMW seq 미지원이면 exact pair를 강제 생성하지 말고 HOLD. 최종 근본 원인이 확인된 최소 수정만 새로운 RED→GREEN→REFACTOR→REVIEW→COMMIT으로 수행. 새로운 source SHA로 실제 L2 2/2 성공 전 WSL2 실행기 출고 및 main 병합 금지.

## 5. 후속 실증 결과 확정 — 이전 Pending 항목을 실제 verdict로 대체

앞선 3장에 기록된 `#44864568561`은 더 이상 Pending이 아닙니다. 실제 Jazzy/Harmonic/TB3/Nav2·RViz·Gazebo Xvfb **단일 run 성공(1/1)**입니다. Strict preGoal PASS, 실제 Moving CLEAR→SLOW→STOP·UUID Cancel·odom dwell·Guard/CM 종료까지 PASS; Guard CM age 최대 13.365751ms. 실패 간격은 이 run에서 재현되지 않았고 최초 Scan/RMW pair는 없으므로 **root cause 증명 아님**. FULL 2/2 NOT_RUN.

### Native #44865087050 — 실패는 종료 경계 (FIRST 26s launch PID)

- 원래 Student `1edd816039381719b4b3a4b0725dd18320ea6ae9`, original MultiThreadedExecutor 2 workers / EventsExecutor=0.
- 실제 `/scan` 등 preGoal 12초 PASS, `AXIA_G07_PUBLIC_CI_MOVING_GOAL_CLEAR_SLOW_STOP_ODOM_PASS` 및 정확 UUID Cancel, 정지 후 dwell 1.011385초, Nav/Loc lifecycle ACK.
- **첫 후행 실패**: `G07_CI_LAUNCH_LIVE_AFTER_MANAGED_EXIT_BUDGET`, 최종 `P2_L2_SMOKE_RC=3` (실제 CI [#44865087050](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44865087050)). Guard/CM source TTL 위반으로 분류하지 않음.
- 기존 `block_B/day07/h01_runtime/scripts/p2_no_goal_smoke_ci.sh::cleanup`에서 26초 내 launch process non-Z/non-X 종료를 요구. 기존 `teardown_processes.txt`에 남은 PID/role 최초 증거가 이번 공개 numeric artifact에서 누락되어 **잔존 실제 process root 미확정**. Shutdown grace만 확대하거나 실패를 PASS로 재분류 금지.
- 같은 run의 READ-ONLY RMW capability 수치: 238 Scan 메시지 수신, source/received/seq 필드 유효 0건. 이것은 로봇 수신 장애가 아니라 **진단용 callback의 선택적 두 번째 인자** 때문에 MessageInfo 미제공으로 확인됨.

### Native #44865216748 — 별개 SLOW 실패

- 같은 원본 기준에서 12초 preGoal PASS, 실제 Moving Goal CLEAR와 물리 SLOW fixture ACK까지 확인.
- **최초 후행 오류**: `CI_MOVING_GOAL_TIMEOUT_SLOW`, 96개 샘플, SLOW 구간 `max_supervised_in_slow_zone=-0.0019620272796601057`, `min_front_m=0.6688`. 양(+)의 전진 감속을 관측하지 못한 것. Nav2 후속 상태/Guardian 프로세스 exit1은 별도 종료 진단이며 첫 SLOW 실패의 입증된 원인이 아님.
- 실제 CI [#44865216748](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44865216748) **FAIL**. 기존 타이밍 TTL을 늘리거나 임의 장애물 위치·임계값을 변경하지 않음.

## 6. 확인된 최소 진단 버그 수정 — Jazzy MessageInfo 진짜 두 인자

- 공식 ROS2 Jazzy `rclpy/rclpy/subscription.py`의 Callback setter는 `inspect.signature(value).bind(object())`에 성공하면 **MessageOnly**로 선택합니다. 이전 `def cb(msg, info=None)`는 1개 인자로도 유효해 Info가 공급되지 않았습니다.
- Student Draft PR [#89](https://github.com/silverbjin/axia-robot-safety-student/pull/89) `block_B/day07/h01_runtime/tools/p2_g07_scan_wall_pregoal.py`의 해당 콜백을 **필수 인자** `def cb(msg, info)`로 수정. 기존 QoS, Scan/Odom/Clock 300ms, CM120, Guard150, Goal 승인, 워커 수 및 ROS publisher 변경 없음.
- RED `#44865561565` → GREEN [#44865588545](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44865588545) **9/9 unit tests**. Student 정확 SHA `a95156156c0c60da6c2185a53e8ec4956ba35928`.
- **실제 Jazzy 두 독립 ROS 프로세스** [#44865731221](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44865731221) GREEN: `source_valid=35 received_valid=35 sequence_valid=35`/35, `clock_samples=1047`, Scan callback max100.250ms, RMW source gap max100.125ms. 이는 **MessageInfo 진단 누락만 해결**함을 입증하며 Gazebo·Nav2·WSL2·이전 300ms 원인에 대한 전체 GREEN 아님.
- 공개 파일 `.github/workflows/axia-g07-original-spin-scan-rmw-real-l1.yml` (source Public `78bda45c6d2d08da793d9acbc4cdce4e1d26a2b2`)은 L1에서만 실제 2개 ROS process를 띄우며 Goal/Gazebo 없음.

## 7. 원래 실패의 후행 rc와 첫 원인을 분리하는 공개 RED→GREEN

- 신규 `d06/diagnostic/g07_first_postgoal_boundary.py`, `tests/test_g07_native_first_postgoal_failure_448650_448652.py`, `.github/workflows/axia-g07-native-first-postgoal-l0.yml`.
- 실제 두 native 실패 로그의 수치·순서를 고정, 후행 rc3/rc2로 원인을 설명하는 것을 금지하는 **fail-closed synthetic replay** 회귀 (Gazebo 재실행 아님).
- RED [#44865879368](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44865879368) `ModuleNotFoundError` → GREEN [#44865902530](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44865902530), `Ran 3 tests / OK`.
- Public 최종 후보 HEAD `55b938e2d7b4e2dfe3abc75706457b405fbeb63c`에 대한 전체 공개 Python 계약 [#44865906619](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44865906619) **318 passed, 3 skipped**. main에는 미병합.

## 8. 최종 기술 판정과 재개 경계

- **확인된 원인**: Jazzy `MessageInfo` 메타데이터 누락의 Python 콜백 서명; 실제 Jazzy L1 수집으로 GREEN. 기존 `/scan` 300ms 간헐 수신 지연의 원인은 **UNDETERMINED**.
- **분리된 신규 첫 실패**: `#44865087050`=26초 관리 launch process 종료 미확인; `#44865216748`=SLOW 구간 양(+) 전진 명령 관측 실패. 두 장애를 한 변경으로 고쳤다고 주장 금지.
- 다음 우선 작업: 기존 `teardown_processes.txt` 원본에서 실존 프로세스 role/pgid와 최초 종료 순서를 확보하여 **종료 문제만** 최소 CI 회귀; SLOW 실패는 동일 Goal/물리 fixture 첫 SLOW 경계의 raw trace·제어 상태로 검증. 둘 다 수정 근거가 없으면 변경 금지.
- 원래 Scan 수신 300ms 첫 위반이 다시 확인될 때만 새 `MessageInfo` RMW pair의 SOURCE/RECEIVED/SEQ와 독립 rosbag *같은 Scan Header pair*를 조인. Seq가 빠지면 fail-closed, 다른 절대 clock domain을 빼지 않음. Gazebo native/bridge 분리가 필요하면 기존 D08 #180 read-only receiver 재사용.
- 신규 소스의 실제 Moving 2/2 independent cold-run **미통과**; WSL2 L3 **NOT_RUN**; **Owner one-shot 미출고**, 사용자 승인 없는 main 병합 없음, 인증 E-Stop 아님.
