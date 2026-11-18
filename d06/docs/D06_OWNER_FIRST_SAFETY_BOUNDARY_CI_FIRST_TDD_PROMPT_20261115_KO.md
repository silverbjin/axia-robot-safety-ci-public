# AXIA D06 G07 — Owner WSL2 신규 실패의 공개 CI 우선 TDD 실행 지침
작성일: 2026-11-15 · SIMULATION ONLY · main 미병합

## 역할과 적용 범위
ROS 2 Jazzy / Gazebo Harmonic / 공식 Nav2 Collision Monitor / TurtleBot3 Waffle 전문가로서, **D06 Owner의 최초 안전 상태 전이와 최초 전달 주기 위반**부터 분석한다. 이미 성공한 공개 CI L2 3/3(#43609296371, private exact c44414f8e3bad37a349565f211d554540cccb062)은 원본 증거로 보존하되 WSLg 동시 GUI 인수로 승격하지 않는다.

## 반드시 읽을 입력
- 비공개 사용자 업로드: p2-l3-owner-G85prCn1.tar.gz (로컬/비공개에서만 열기).
- G07/live/ci_moving_goal_result.json, G07/live/actual_ros_events.jsonl, G07/live.log, summary.json, rosbag2, launch.log, SHA256SUMS.
- 공개 회귀(비식별): d06/tests/fixtures/g07_owner_20261115_first_boundary_sanitized.json.
- 공개 실행 게이트: d06/acceptance/d06_g07_final_owner_ci_gate.json.
- 공개 코드/테스트: d06/live/d06_g07_field_triage.py 및 d06/tests/test_d06_owner_20261115_first_boundary.py.
- D06 Instructor 솔루션/Hidden Tests와 원본 Goal UUID/경로/rosbag 원본을 공개 저장소에 게시하지 말 것.

## 첫 실패의 고정된 사실(서로 다른 관측창을 하나로 합치지 말 것)
- Goal 이후 첫 **Guard 상태 토픽을 관찰한 Observer** 간격 162.774195ms (>150ms); 이것만으로 Guard 프로세스 내부 callback 결함이 입증된 것은 아니다.
- 이후 Observer /scan 간격 333.397997ms (>300ms); 이것만으로 Scan 전송 지연이 최종 Guard 래치를 직접 유발한 것이라고 판단하지 않는다.
- CM RMW 발행 source 간격 152.878980ms (>150ms); 해당 창 안에서 Supervisor 발행 3건, 커버리지 최대 간격 60.066921ms. 내부 CM callback vs OS 스케줄링의 원인은 미확정.
- 별도의 RMW 최초 측정 창은 source 153.792195ms / receive 149.857276ms / Observer 165.159385ms로 서로 다르다.
- Guard 내부 최초 latch: UPSTREAM_STALE_AFTER_MOTION, CM age 166.509123ms (>150ms), Supervisor age 56.089811ms.
- 실제 STOP zone/odom 정지 1초/Navigation·Localization ACK/CM 정상 종료/원본 custody 연결은 **인수 미증명**. 최종 ZERO twist는 물리 정지 인수 증거가 아니다.
- 이 실패 이후 기존 ADMITTED_FINAL_OWNER_ONLY 1회 인수 허가는 소진되었다. 자동/현장 재시도 금지. L2 3/3 과거 PASS 기록은 삭제하지 않는다.

## 실행 순서 — 반드시 RED → GREEN → REFACTOR → REVIEW → COMMIT
1. **보존·분리**: tar/SHA256/sqlite quick_check 및 초기 goal 상태/최초 래치/최초 time breach 확인. timestamp는 relative goal-scoped 형태로 정리하고 원본을 외부 업로드하지 않는다.
2. **RED**: 정확한 중첩 키 \`pre_latch_delivery_diagnostics.first_timing_violation\`에서 최초 위반이 유실되는 테스트와, 새로운 Owner L3 실패 후 과거 CI PASS를 이용해 계속 ADMITTED로 남는 오류를 공개 L0에 추가. 기대 실패를 실제 Actions 로그로 입증.
3. **GREEN-L0**: 진단기가 nested/top-level 모두 지원하고 Guard 상태 Observer/Scan/RMW source 위반을 각각 기록하게 수정. 최초 래치 및 TTL 판정은 실패 폐쇄. 인수 JSON을 HOLD_OWNER_L3_FIRST_SAFETY_BOUNDARY로 전환, owner 실행기는 **TTY/ROS/Goal 이전** 거부해야 한다.
4. **REFACTOR**: 중복 수정/사설 소스 확장을 하지 않는다. 공식 Collision Monitor, Safety Supervisor, Guard 안전 TTL 150ms 및 Scan 300ms를 변경하거나 STOP을 무력화하지 않는다. 새로운 /cmd_vel 또는 Goal publisher를 만들지 않는다.
5. **REVIEW**: 테스트에 Goal UUID·로컬 절대경로·비공개 코드·원본 bag·Hidden Tests가 없는지 검토. 전체 return code/실제 Actions 로그 및 README/instructor/student 경로에서 구버전 실행 안내가 남았는지 점검.
6. **COMMIT**: CI RED와 GREEN의 URL, source SHA, 변경 파일, 실제 출력, 실행 환경, 미검증 항목을 기록한다. main은 Owner 승인 전까지 병합하지 않는다.

## 다음 필수 검증 — L0 해결과 런타임 지연의 완전 해결을 혼동하지 않는다
- **L0/실제 ROS L1**: 비식별 재현 픽스처(Guard 관측 162.774ms, Scan 관측 333.398ms, CM RMW source 152.879ms, Guard age 166.509ms)에서 FAIL-CLOSED, 신선한 입력에서는 false positive 없음, 초기 프레임/접합 아티팩트 무시하지 않음.
- **실제 공개 Gazebo L2 신규 부하 조건**: 기존 성공한 headless L2를 그대로 반복하지 말 것. 최소한 실제 RViz2/교육용 MarkerArray와 하나의 Goal이 **동일 프로세스 경쟁 환경**에서 동작하도록 조건을 추가한다. 불가능하면 \`NOT_VERIFIED_GUI_LOAD_PARITY\`로 HOLD. Xvfb ≠ WSLg이므로 GUI 대체 성공은 사용자 실제 WSLg PASS가 아님.
- Goal-scoped 실제 /scan source/callback vs Supervisor native scan counter, RMW CM source/receive/sequence, Guard 내부 receive age 및 첫 latch, 최종 /cmd_vel, 실제 /odom STOP dwell≥1s를 같은 주행에서 검증한다.
- Navigation·Localization의 **native lifecycle ACK**, clean Collision Monitor exit, 실제 14-topic bag 무결성을 같은 SHA에서 결합. 기능 하나만 GREEN인 상태를 전체 시연 PASS로 승격하지 않는다.
- 새 지연 재현 시 근거 있는 최소 부하/우선순위 또는 발행 경로 수정만 검토하고 **동일 조건 L2 RED→GREEN**을 보인 후 인수 허가 재개.
- 다른 안전 계층(Scan / Supervisor / CM / Guard / odom)의 시간 경계 미검증이면 \`OVERALL_DEMO_STABILITY_NOT_VERIFIED\`로 표시한다.
- Guard latch 후 ZERO Twist는 SW stop이며 certified physical E-Stop이 아님.

## 완료 판정과 중단 기준
- 신규 공개 실제 L2에서 **동시 렌더링 부하, Scan≤300ms, CM/Supervisor/Guard≤150ms, CLEAR→SLOWDOWN→STOP, odom≥1s, lifecycle ACK/CM exit0, 원본 무결성**이 모두 확인되기 전에는 owner 재입장 금지.
- 한 번의 실제 Owner WSLg 검수에서 GUI 두 창 갱신 및 원본 주행/정지가 함께 입증되기 전에는 D06_GAZEBO_RVIZ_L3_ACCEPTED 금지.
- 각 작업은 경로·명령·실제 출력·검증 수준·미검증·브랜치/커밋을 제출. 안전 부정 증거를 누락하거나 FAIL을 PASS로 변환하지 않는다.

## 부록: 공개 실제 GUI 동시부하 L2 최초 전달지연 — 2026-11-15

- 새 실제 Gazebo+RViz2+Xvfb+MarkerArray 관찰기 같은 컨테이너에서 실행, 1회 Goal 실제 수행: public Actions #43664497257, source c017907570922e1d19e6c4901b38f6bd395b51cc, **전체 L2 FAIL**.
- 해당 실행에선 RViz 실제 창 생성 성공. /odom Observer 첫 간격 365.941227ms (>300ms); /scan Observer 428.090958ms (>300ms)이지만 Supervisor native scan gap delta=0. Observer gap을 native sensor safety failure라 단정 금지.
- CM 전체 RMW source 최대 139.491ms (<150ms). 다른 최초 RMW 창에서 CM source 69.596117ms인데 receive 393.579510ms, Observer callback 397.164783ms. 분류: RMW_RECEIVE_DELAY_CANDIDATE. native Guard latch 미관찰. DDS/스케줄링/Observer 내부 원인 특정 불가.
- 원래 Owner WSL2 G85의 CM RMW source 152.878980ms 및 Guard internal cm age 166.509123ms (>150ms), UPSTREAM_STALE_AFTER_MOTION 와 같은 원인이라고 입증되지 않음. 실제 CI 시연은 odom STOP 1초 일부 관측과 무관하게 전체 Goal timing oracle 및 lifecycle shutdown FAIL.
- 신규 sanitized fixture: d06/tests/fixtures/g07_ci_20261115_concurrent_gui_first_boundary_sanitized.json; test: d06/tests/test_d06_ci_concurrent_gui_first_boundary.py. RED #43664968558: 83 passed, 1 failed(실제 GUI L2 실패를 gate가 누락). GREEN #43665049485: L0 84 passed, 실제 ROS L1 및 RViz Xvfb L1 PASS. **신규 GUI 동시부하 실제 L2 자체는 RED 유지**.
- 안전 게이트는 기존 headless 3/3 기록을 지우지 않으나, 재인수 허가에 whole_concurrent_gui_l2_pass=true를 추가 요구. 현재 false. status=HOLD_OWNER_L3_FIRST_SAFETY_BOUNDARY, allow_one_final_wsl2_owner=false, allowed_final_owner_attempts=0.
- 절차 다음 단계: native Guard 콜백, CM source/RMW receive, Observer 시각을 동일 Goal 창에서 대조하고 최소 GUI 렌더링 부하 개입 후보를 계측→실제 동시부하 L2 GREEN으로 확인. 성공하지 않으면 Owner WSL2 재시도 및 PASS 주장 금지.
- 실제 GUI 부하용 공식 공개 실행 위치는 release/p2-g06-cm-ttl-20261110 의 .github/workflows/d06-g07-concurrent-rviz-actual-goal-l2.yml. Feature 브랜치의 시험 workflow 복제본은 제거.
