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
