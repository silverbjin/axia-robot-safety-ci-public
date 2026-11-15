# AXIA G07 — Cycle 03 원본 Guard 불일치·RMW 시계·실행기 동등성 (교육용 중간 보고서)

날짜: 2026-11-15 KST. **상태: L0 GREEN / 동일 실행기 실제 GUI L2 #43690412617 종료 ACK FAIL / Owner 재시도 금지**

## 문제를 어떻게 발견했는가

사용자 첨부 원본 `p2-l3-owner-aU7DEqQs.tar.gz`, `axia_d06_gazebo_rviz_owner_BJROyuNz.zip`, `axia_p4_g11_session_custody.zip`를 직접 읽어 최초 안전 전이와 ROS 데이터 시간을 분리했다. 다음 수치는 Owner 원본에서 나온 것이다. 원본 파일 내용/Goal UUID/절대 경로는 공개 저장소에 게시하지 않는다.

- 최초 래치 `CM_EXCEEDS_SUPERVISOR`. Guard CM age=69.384740ms, Supervisor age=43.692944ms. **150ms CM TTL 위반 아님**.
- CM=(0.07442718m/s,0.1832993rad/s), Supervisor 최신=(0.0576610m/s,0.0982288rad/s). 나중 Supervisor 명령보다 큰 옛 CM 출력.
- ZERO-only 조정 시작 t=3903.631154036; 내부 최초 래치 판정 t=3903.756578606; 경과 **125.424570ms**, 기존 120ms 유예 한계 초과. Guard는 그 동안 **ZERO**를 출력하고 난 뒤 래치했다. 보호 해제나 TTL 확대로 성공 처리하는 것은 부적절.
- CM RMW source gap=1.470056234s, Supervisor RMW source gap=1.466053786s, 외부 CM monotonic 관측간격=53.606801ms. **호스트 시스템 시계 변경 후보**이지 실제 CM 발행 1.47초 중단이 입증된 것이 아님.
- 최초 사건 직후 `rclpy Destroyable` 경고는 종료 중의 후속 현상; 최초 원인으로 바꾸지 않는다.

## RED → GREEN → REFACTOR → REVIEW → COMMIT

1. **RED** 공개 [#43689306583](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43689306583): Owner 최초 불일치 진단기가 없어 비식별 테스트 실패.
2. **GREEN** 공개 [#43689362501](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43689362501): `d06/live/d06_guard_first_mismatch_triage.py`에서 불일치 조정 만료/TTL 구분과 RMW 시스템 시계·monotonic 분리, 명시적 HOLD 판정. 비식별 fixture만 공개.
3. **RED** private GUI launch 계약 및 외부 GUI 준비 누락 테스트, 공개 sealed L0 [#43689577854](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43689577854), [#436899...](https://github.com/silverbjin/axia-robot-safety-ci-public/actions)와 동등성 테스트 (Run ID 원본 교차확인 필요).
4. **GREEN** private [#43690073396](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43690073396) Instructor SHA `e3706dfeec14f20699c99f8995a2ec68180a24aa`: `scripts/p4_g07_shared_runtime.sh`는 CI/Owner 모두 headless Gazebo server를 선택하되 Owner 새 공개 sidecar 플래그에만 적용. `scripts/p2_no_goal_smoke_ci.sh`, `scripts/p2_owner_l3_wsl2.sh` 양쪽에서 같은 GUI readiness 확인 후 같은 `tools/p2_g07_ci_moving_goal.run()` 실행.
5. **RED** 공개 GUI 실행기 이원화 테스트 [#43689743262](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43689743262) 예상 실패.
6. **GREEN** 공개 [#43690121848](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43690121848): `d06/scripts/g07_shared_gui_clients.sh` 하나가 Xvfb/WSLg에서 모두 `gz sim -g`, RViz2, read-only Marker 관측기를 동일 `taskset`·`nice`로 시작. CI는 xwininfo 창 검증, WSLg는 시각 확인 미완료로 기록.
7. **RED** 공개 원본·GUI·custody 자동 묶음 미구현 [#436902...](https://github.com/silverbjin/axia-robot-safety-ci-public/actions) (정확한 RED Run 교차확인 필요).
8. **GREEN** 공개 [#43690335847](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43690335847): `d06/live/g07_owner_evidence_bundle.py` + Owner wrapper EXIT trap. 실패·완료 모두 개인 Home 아래 하나의 지원 폴더에 archive+manifest+SHA256SUMS 보존. 자동 업로드·자동 재시도 없음.
9. **REVIEW:** 기존 P4 PASS Instructor `db1eec05...`/main/student/공식 Nav2 소스 불변, Guard 120ms/CM TTL 150ms/Scan TTL 300ms 불변. 실제 Owner 화면은 WSLg vs CI Xvfb라 플랫폼 동등성 **미확보**.
10. **COMMIT:** 공개 fixture RED `708bb874`, green `bac79c59`, GUI red `cb8385d5`, green `30599879`, bundle red `7ea3f320`, green `fe66eb9d`+`70f9d4ec`. Instructor GUI parity 소스 `e3706dfe`.

## 실제 L2 검증 및 후속 발견

새 Source/GUI parity 조합 L2 [#43690412617](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43690412617): 실제 Goal CLEAR/SLOW/STOP, odom dwell 1.01119s, exact Cancel ACK, Guard 래치 없음, seven-channel timing 범위 내. **그러나 종료 첫 서비스 발견 실패** `SERVICE_MISSING:/lifecycle_manager_navigation/get_parameters`; Navigation/Localization ACK 없음; 강제 정리 단계 CM exit -11 관측. **전체 L2 FAIL**. 후속 수정은 Cycle04. 미검증: Owner WSLg, CI와 WSL2 kernel 스케줄링 동등성, intermittent CM 명령 지연 원인.

## 교육 포인트

(1) 이름이 비슷한 두 시간 문제(Guard monotonic 조정 만료 vs DDS RMW system clock jump)를 절대 혼동하지 않는다. (2) 안전 Guard가 오래된 고속 CM을 0으로 억제하고 래치했다면 이를 무시하는 것이 아니라 데이터 전송/스케줄링을 개선한다. (3) ROS 종단 시뮬레이션 성공 판정에는 Cancel과 관리 노드 shutdown이 모두 포함된다.
