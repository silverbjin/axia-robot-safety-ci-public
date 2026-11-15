# AXIA G07 — CI First/Owner 실행기 동일성 및 최초 안전 전이 회귀 지침 (2026-11-15)

## 목적/범위
Owner WSL2는 **최종 1회 현장 검수**이며 디버깅 반복 실행기가 아니다. 현장 오류는 원본 아카이브 보관 → 첫 안전 상태 전이 및 첫 타이밍 위반 분리 → 비식별 CI 회귀 RED → 최소 수정 GREEN → 실제 Gazebo+RViz GUI CI L2 → 산출물 리뷰·커밋 → 새로운 Owner 최종 1회 입장 승인 순서로 처리한다. 이미 통과한 P4 소스는 별도 SHA로 불변 보존한다. main 병합은 사용자 승인 전 금지.

## 본 사례 고정 증거 (원본은 비공개)
- Owner source `db1eec05e01e1db0d0d2e0c05610806ef4e499f9`; Owner 원본 `p2-l3-owner-aU7DEqQs.tar.gz`; CI Xvfb 이전 PASS `43685818018`.
- 최초 Guard latch: `CM_EXCEEDS_SUPERVISOR`; CM age 69.384740ms/ Supervisor age 43.692944ms; TTL 위반 **아님**. ZERO-only reconciliation 시작 3903.631154036, 첫 latch tick 3903.756578606: 125.424570ms 경과, 120ms 내부 불일치 조정 경계 초과.
- 실제 CM: linear 0.074427179992 / angular 0.183299303055; 최신 Supervisor: linear 0.057661004364 / angular 0.098228774965. 오래된 CM을 **출력하지 않았고**, ZERO-only 후 보호 latch.
- RMW source CM=1.470056234s/Supervisor=1.466053786s vs monotonic CM observer=0.053606801s: 공통 HOST CLOCK STEP 후보. **RMW 시스템 시계 스텝은 CM 발행 정지, 네트워크 지연, Guard TTL 위반의 증거로 승격 금지.**
- ROS 2 rclpy `Destroyable`/wait-set 오류는 latch 이후 shutdown의 2차 현상. 최초 latch로부터 원인 분석.
- 화면 경로 차이: CI `ci-headless=True`+별도 `gz sim -g`+RViz Xvfb, Owner `owner-gui=False(headless)` 내장 Gazebo GUI+별도 RViz WSLg. GUI 프로세스 수·CPU affinity·nice 값이 다르므로 *동일 사용자 공간 패키지*가 **런타임 부하 동등성**을 의미하지 않음.

## 강제 실행 프롬프트 (각 사이클)
> ROS 2 Jazzy/Gazebo Harmonic/Nav2/TB3 Waffle G07 시나리오를 담당하라. 이전 P4 PASS SHA는 불변으로 보존하고 공개 CI와 Instructor 후보를 별도 브랜치에서 다룬다. 원본 Owner failure의 최초 Guard latch와 최초 monotonic 시간 경계를 식별하되 ROS/RMW source timestamp 도메인을 혼합하지 마라. Guard가 불일치 또는 stale CM에 대해 ZERO를 출력하고 120ms/150ms/300ms 안전경계를 지키는지를 먼저 RED 회귀로 입증하라. 성공을 위해 Guard 유예/TTL을 연장하거나 latch를 무시하지 마라. **CI와 Owner는 같은 P4 private `p2_g07_ci_moving_goal.run()`/공통 launch/Bag/Goal oracle/Shutdown 실행기 소스를 재사용**하고 승인·DISPLAY·WSLg/Xvfb 차이만 분기한다. 공식 Nav2 코드를 수정하지 않는다. 실제 CI GUI에서 Owner와 같은 `gz sim -g`/RViz/관측기 스케줄링·프로세스 역할을 검증하고, 차이와 한계를 명시한다. 누락 증거는 결과 HOLD로 판정하고 Owner 종료 직후 private 원본 rosbag·GUI 로그·시계 도메인 자료·기동/종료 로그·환경 SHA를 하나의 디렉터리에 원자적으로 모아 아카이브+SHA256SUMS를 만든다. GitHub public에는 비식별 fixture·결과·회귀 테스트만 올리고 학생용에는 강사 정답을 내보내지 마라. RED → GREEN → REFACTOR → REVIEW → COMMIT마다 원인·수정·실제 테스트 출력·Run/SHA·검증 범위·미검증·교육용 교훈을 문서화한다. 실 Gazebo L2 PASS와 해당 검증 범위를 확인한 경우에만 새 Owner 1회 실행기 배포 후보로 올려라. Owner WSL2에서 재시도는 사용자 확인을 반복 요구하지 말고 단일 원샷을 제공한다.

## CI에서 추가해야 할 검사
1. 비식별 원본 입력 재현: 정상 /cmd_vel source와 최신 CM 명령의 시간순 도착을 복원하여 120ms ZERO-only 지속 뒤 정상 보호 latch 재현. 동일 사건을 150ms CM TTL 위반으로 오분류하면 FAIL. 테스트가 보호 latch를 무시하여 PASS를 만들면 FAIL.
2. RMW domain step: CM과 Supervisor source clock에 동시에 약 1.4초 공통 변위, monotonic callback은 54ms인 fixture로 `HOST_SYSTEM_CLOCK_STEP_CANDIDATE`, `cm_publisher_stopped_proven=false`, `safety_pass=false` 확인. RTC/RMW 시계와 monotonic 직접 뺄셈 금지.
3. 실제 실행기 동일성: 두 실행 모두 동일 Instructor SHA, `tools/p2_g07_ci_moving_goal.py` shared `run()`, `scripts/p4_g07_shared_runtime.sh` launch/14-topic recorder/staged startup, 동일 official Nav2/Gazebo 설정·TTL을 사용. Goal 권한과 GUI 렌더링 transport 외 차이를 JSON manifest로 명시.
4. GUI 부하: Owner와 CI의 Gazebo GUI·RViz·read-only monitor 모두 동일한 CPU/nice 역할 제약; CI Xvfb != WSLg, 인증 PASS로 주장 금지.
5. 실제 L2: Goal 1회, 최초 Guard 상태/타이밍, seven-channel callback max, CM RMW source·receive sequence 및 clock domain, S02 contact, CLEAR/SLOW/STOP, Odom dwell ≥1초, exact CancelGoal ACK, Nav2 navigation/localization ACK와 CM exit0 및 원본 14-topic 모두 **동일 Goal** 원본으로 검증.
6. 불완전 Owner raw: 사고 직후 증거 bundle이 사적으로 생성되는지 CI에서 임시경로·합성 로그만으로 검증. 원본 안전 증거 누락시 내용별 경고와 HOLD. 이 스크립트는 Goal, ROS publisher, safety override를 추가하지 않음.

## 게이트
L0 pytest/unittest PASS는 ROS/Gazebo 검증이 아니다. L2 CI PASS는 Xvfb 범위만 입증한다. WSL2 kernel/WSLg 실제 인수는 사용자 원본 증거 확인 전 `AXIA_MVP_DEMO_ACCEPTED=HOLD`. 실제 인증 E-Stop 주장 금지. 시연 범위 외 과도한 신규 개발·다중 PC·15회 반복 강요 금지.

## 신규 Cycle05 필수 검증 (2026-11-15)

CI run [#43690918618](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43690918618)은 동일 실행기/GUI 구성에서 **첫 PRE_STOP odom 355.882ms, CM RMW source 70.892ms vs receive 377.049ms, observer 383.109ms**를 확인했다. 기존 P4 headless CI 성공은 이 실패를 해소하지 않는다. 특정 source pair의 receive gap과 최초 odom gap이 절대적으로 동일 시간구간이라는 증거는 없으므로 각각 독립적으로 분석한다. 새 원인 가설은 반드시 단일 관측 지표/스케줄러 증거를 근거로 삼고, Guard native callback와 외부 Observer 간극을 혼동하지 말라. Safety TTL·reconciliation grace·STOP 판단을 늘리거나 무시하여 통과시키지 말라. CI의 원본 7채널 callback 최대 주기는 계속 실제 L2 인수 조건이다. 공개 비식별 회귀 `d06/tests/test_g07_ci_multitopic_first_receive_gap_20261115.py`와 원본 [#43690918618](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43690918618)을 이후 모든 후보의 RED baseline으로 재사용한다. 시연 전체 통과와 동일 검증 범위 없이는 Owner WSL2 추가 Goal을 승인하지 않는다.
