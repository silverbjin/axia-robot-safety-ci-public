# AXIA G07 개발 사이클 06 — 원본 Prearmed STOP 2-CPU 제약과 GUI·Goal Observer 공통 배치

- 일자: 2026-11-15
- 상태: **강사용 sealed L0 GREEN / 실제 Gazebo L2 진행 / Owner WSL2 NOT_RUN / MVP HOLD**.
- 기존 P4 실제 PASS `db1eec05e01e1db0d0d2e0c05610806ef4e499f9` 및 원본 Safety TTL 변경 없음.
- 공통 실행기 후보: Instructor `fix/g07-ci-owner-runtime-parity-20261115`, SHA `bc270e28620c1909fcb34669e6036504b5cae951`.

## A. 실제 CI가 처음 차단한 경계
선행 첫 수신 간격 사례 [#43690918618](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43690918618): CM source gap 정상, receive/observer gap 약 377~383ms. 원본 Goal Observer를 GUI/rosbag에서 CPU 역할 분리하는 테스트와 코드를 만들었다.

그러나 실제 [#43692909902](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43692909902)에서는 Goal 이전 `RuntimeError:G07_PREARMED_CPU_ISOLATION_NOT_AVAILABLE_NO_GOAL`이 발생해 안전하게 차단되었다. 원래 `tools/p4_g07_prearmed_stop.py`는 `os.sched_getaffinity(0)`의 CPU가 최소 2개여야 독립 native STOP 프로세스를 준비한다. 4코어 GitHub hosted CI에서는 GUI 0, read-only monitor 2, rosbag 3을 예약하여 Goal Observer에 1만 남겼던 것이 원인이었다. **Goal은 전송하지 않았으며 STOP을 우회하거나 CPU 요건을 낮춰 통과시키지 않았다.**

## B. RED → GREEN → REFACTOR → REVIEW → COMMIT
1. RED `cd070a63ca857ed05084ae21201077bb7d2166a8` — 실제 실패를 재현한 `tests/unit/test_p4_g07_goal_observer_cpu_parity_20261115.py`의 4-CPU -> minimum 2-CPU 원장 테스트.
2. 공개 sealed CI [#43693340153](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43693340153) **FAIL (expected RED)**. Real ROS/Gazebo/Goal 없음.
3. GREEN `bc270e28620c1909fcb34669e6036504b5cae951` — `tools/p2_g07_goal_observer_cpu_plan.py`에서 허용 CPU N>=4이고 Goal Observer 선택 2개 미만이면 penultimate GUI 관측 CPU를 낮은 우선순위 read-only Marker 모니터와 **공유**해 native STOP용 CPU 최소 2개를 보존. GUI renderer 첫 코어, rosbag 마지막 코어와는 계속 분리. N>=5인 경우 penultimate monitor와 분리 유지.
4. 공개 sealed CI [#43693435159](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43693435159) **SUCCESS (GREEN)**.
5. CI/Owner 스크립트 모두 동일 `tools/p2_g07_goal_observer_cpu_plan.py`를 사용하고 같은 `tools/p2_g07_ci_moving_goal.py` 안에서 실제 프로세스 affinity를 Goal 이전 검증. Guard/CM/Nav2 프로세스 affinity는 변경하지 않는다.
6. 실제 Gazebo+Xvfb/RViz 동시 1-Goal L2: [#43693480829](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43693480829) **실행 중(작성 시점)**. 이 결과가 나올 때까지 새로운 Owner 배포 및 MVP 인수 승격 금지.

## C. 핵심 실행기 파일
- Instructor `tools/p2_g07_goal_observer_cpu_plan.py`: 사용 가능한 CPU 산출 (4-core: `1,2`; 8-core: `1,2,3,4,5`).
- Instructor `scripts/p2_no_goal_smoke_ci.sh`, `scripts/p2_owner_l3_wsl2.sh`: 환경별 인증 차이만 유지한 동일 Goal observer role.
- Instructor `tools/p2_g07_ci_moving_goal.py`: `ensure_expected_role(os.environ)`로 실제 affinity readback before ROS init.
- Instructor `tools/p4_g07_prearmed_stop.py`: **수정 없음**, `len(allowed)<2` 안전 차단 보존.
- Public GUI `d06/scripts/g07_shared_gui_clients.sh`: CI Xvfb/Owner WSLg 공통 외부 `gz sim -g`/RViz/Marker observer.

## D. 검증 범위, 미검증, 교육 교훈
- L0: 정적 검증/실제 모듈 실행(Green)만 확인됨; 이것은 Gazebo L2 통과 증거가 아니다.
- L2: 별도 실 Gazebo+실 Nav2 Goal/Stop/Cancel/Native shutdown/CM exit/7-channel TTL 검증 필수.
- Owner WSL2, WSLg 영상, 원본 rosbag/CM/Guard 안전 인수: **NOT_RUN**.
- 교육 포인트: CPU 최적화를 신규 안전 기능으로 오해하지 않는다. 기존 Prearmed STOP의 CPU **2개 필수 요건**도 안전 경계이므로, 프로그램 전체를 태스크셋 1개 CPU로 묶는 성능 최적화는 운영 계약 위반이다. 다음 실제 L2가 실패하면 최초 위반부터 새 RED를 만든다.
