# AXIA G07 Cycle04 — 교육용 실제 CM 구독/콜백 식별 및 첫 실패 검증 기록

## 학습 목적
실제 공식 Nav2 Collision Monitor가 /cmd_vel_supervised 입력을 어떤 C++ callback으로 처리하는가? 기존 Cycle30 [Run #43812555906](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43812555906)의 trace 2,611,716개는 callback symbol 이름만으로는 정확한 입력 callback을 식별하지 못했다. 이번 Cycle은 토픽 이름의 **rcl_subscription_init → rclcpp_subscription_init → rclcpp_subscription_callback_added** 이벤트 3종만 활용한다. 아직 callback_start/end, TF getTransform 지연은 측정하지 않는다.

## 기준 및 작업 경계
- 이전 Moving Goal CM source128.644ms(#43898345608), 133.659ms(#43981875149) >120ms release HOLD. Owner Guard 최초 internal CM age158.008ms>150ms hard failure 별도 보존.
- Cycle03 정지 모드에서 clock/odom/TF 공통 wall gap333.601ms 발견. 주행 중 CM 원인 미확정.
- 본 Cycle에서 official Nav2/CM/Guard/Supervisor, Safety TTL, ROS Goal 및 /cmd_vel 송신 변경 **0건**.
- 계획 `d06/docs/AXIA_G07_CM120_CYCLE04_OFFICIAL_CM_CALLBACK_IDENTITY_PLAN_20261117_KO.md`, 계획 SHA `26e1f056a34faf40388392a321343cd0a0bd1c04`.

## RED→GREEN/코드/리뷰
- Public RED 신규 계약 `d06/tests/test_g07_cycle04_cm_metadata_audit.py` commit `8a5e2a4984e66eef29394422fc9fa41254529b9c` (초기 3건). 오인 토픽 구독 회귀 1건 추가 commit `25cf38a4764938afa577cf1166c2da41b86b0066`.
- 프로덕션 안전 코드 변경 없이 CI-only `d06/live/g07_cycle04_cm_metadata_audit.py` commit `55b1e87c01c0b4d11dac0f478edb3bc2782045e4`, 다른 토픽 구독자로 CM 소유권 혼동 방지 fix commit `ebe711ee06643bb654df8947da482f4bc0ff0514`. 기존 Cycle31 verifier 원본 blob `5478a034d119c9dd47aecf48604b0626075a81cc` 그대로 복사 재사용 commit `8ac8513c16a3ea1c4de2767e5ff981d7d8718964`.
- Public CI workflow `.github/workflows/axia-g07-cycle04-cm-meta-nogoal-l1.yml` exact pinned private `0682caeb413c9830107b1a0d297d36597896bed7`, public `ebe711ee06643bb654df8947da482f4bc0ff0514`, baseline `42817767a85be1022a3e11391e8e588bd3b8e814`.
- 범위: Official Harmonic+Nav2/Waffle staged NO_GOAL, 14-topic/CM/lifecycle 공통 실행기. LTTng metadata event 3개만 켜서 Cycle30 260만 callback event 재수집 방지. 정확히 하나의 공식 CM process name+topic subscriber+callback handle만 확보. ptr/PID/원본 rosbag은 공개하지 않음.

## 첫 실제 공개 CI: Run #43993776141
- 실제 상태 `completed/failure`. RED: 기존 공개 source에서 신규 모듈 미존재 예상 import error, GREEN: 수정 candidate 4/4 PASS.
- 실제 Jazzy+Gazebo/Nav2 노드가 구성되는 동안 LTTng metadata-only 수집: 아래 **실제 결과를 보존**.
```text
AXIA_G07_C04_RED_MISSING_REAL_CM_METADATA_AUDIT_CONFIRMED
Ran 4 tests in 0.001s
OK
AXIA_G07_C04_GREEN_4_OF_4_NO_ROS_NO_GOAL
AXIA_G07_C04_ONLY_3_SUBSCRIPTION_TRACEPOINTS_NO_CALLBACK_START_END
AXIA_G07_C04_REAL_CONFIGURED_CM_TOPIC_IDENTITY
  status=CM_INPUT_CALLBACK_HANDLE_IDENTIFIED_NO_GOAL
  owned_cm_process_count=1
  linked_cmd_vel_callback_handles=1
  metadata_only=true
  cm_callback_duration_proven=false
  ready_for_moving_goal=false
  goal_sent=false
```
- 이 결과는 **실제 공식 CM의 토픽→콜백 핸들 식별에 성공한 것**. 이전 Cycle30의 미해결 관찰에 필요한 사전조건 충족.
- 단 L1 전체 CI **최초 실제 실패 경계**는 `g07_ordered_shutdown.json` 미생성에 따른 `FileNotFoundError`. Start verdict의 `SMOKE_READY` 경로까지 도달했으나 실제 종료 ACK가 있었는지 증거가 부족함. 따라서 '전체 실시간 안전 CI PASS'로 승격 금지.
- 첫 로그의 `owned_cm_subscription_init_count=124`, `callback_added_event_count=100`은 *전체 LTTng 수집 이벤트 누계*이며 **CM 단독 이벤트 수가 아님**. 실제 소유 CM 단일성은 별도 PID/소유자 검증과 `linked_cmd_vel_callback_handles=1`로 입증. 향후 명칭 수정 후보이나 이번 인수 추가 게이트로 확대하지 않음.

## 실제 원인 분석 및 재검 확인
- 최초 합성 에러가 아닌 **종료 ACK 증거 파일 부재**가 실패. 원본 no-goal stdout을 첫 실행이 외부에 출력하지 않았으므로 원인(ROS lifecycle timeout/Observer side effect/기타 pre-shutdown) 미확정.
- 두 번째 같은 CI 수정은 safety/runtime 변경이 아니라, `runner_rc`, `startup_status`, `goal_sent`, `shutdown_ack_present`와 원본의 첫 장애 marker **요약만 출력**. 공개 워크플로 수정 commit `bda045da857bdd4ef5d896b7a9ef95b77fc292ba`; release run SHA `c6d18648ca6ce0748163d9dd0b9238274f21346d`, [Run #43994237080](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43994237080). **검증 결과는 본 보고서 후속 추가**.
- 구분: 메타데이터 수집에서 callback identity=PROVEN; callback execution duration=UNPROVEN; official getTransform wait=UNPROVEN; 실제 Moving Goal 120ms=FAIL historical; Owner L3=NOT_RUN.

## 교육 질문
1. 한 CI job의 중간 출력이 PASS여도 전체 CI를 PASS로 보고하면 왜 안 되는가?
2. 타입명/함수명 심볼보다 ROS subscription object handle 연결이 왜 더 믿을 만한가?
3. 3개 메타데이터 tracepoint를 사용하면 Cycle30의 260만 callback event와 달리 어떤 간섭을 줄일 수 있는가?
4. CM 입력 callback handle을 알아도 120ms 문제를 해결했다고 말할 수 없는 이유는 무엇인가?

## 실행·파일·검증 범위
- Code paths: `d06/live/g07_cycle31_cm_topic_callback_identity.py` (기존 원본 재사용), `d06/live/g07_cycle04_cm_metadata_audit.py`, `d06/tests/test_g07_cycle04_cm_metadata_audit.py`, `.github/workflows/axia-g07-cycle04-cm-meta-nogoal-l1.yml`.
- L0: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s d06/tests -p 'test_g07_cycle04_cm_metadata_audit.py' -v` (공개 CI GREEN4). 실제 L1 GitHub Run은 위 두 Run.
- 미검증: first CM source gap 당 cmd_vel callback start/end, TF lookup time, 120ms release margin, Guard internal 150ms, Owner WSL2.
- main 미병합, SW 정지는 인증 E-Stop이 아님. `AXIA_MVP_DEMO_ACCEPTED=HOLD`.

## Cycle04 최종 검증/종료 기록 — Run #43994237080
- 이전 실패로 추적 대상은 C04 startup 이후 `g07_ordered_shutdown.json` 부재였다. 기능/runtime/safety 코드 변경 없이 공개 CI workflow에서 첫 실패 marker와 startup status, rc, shutdown presence만 출력하도록 커밋 `bda045da857bdd4ef5d896b7a9ef95b77fc292ba`.
- 실제 [Run #43994237080](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43994237080) release SHA `c6d18648ca6ce0748163d9dd0b9238274f21346d`는 **completed SUCCESS**. Public L0 RED missing module 재현, GREEN 4/4 PASS. 같은 official CM+Waffle/Gazebo/Nav2 NO_GOAL runtime, metadata-only LTTng, lifecycle shutdown ALL PASS:
```text
AXIA_G07_C04_RED_MISSING_REAL_CM_METADATA_AUDIT_CONFIRMED
Ran 4 tests in 0.001s
OK
AXIA_G07_C04_GREEN_4_OF_4_NO_ROS_NO_GOAL
AXIA_G07_C04_ONLY_3_SUBSCRIPTION_TRACEPOINTS_NO_CALLBACK_START_END
AXIA_G07_C04_REAL_CONFIGURED_CM_TOPIC_IDENTITY {"status": "CM_INPUT_CALLBACK_HANDLE_IDENTIFIED_NO_GOAL", "owned_cm_process_count": 1, "linked_cmd_vel_callback_handles": 1, "cm_callback_duration_proven": false, "goal_sent": false, "ready_for_moving_goal": false}
AXIA_G07_C04_FIRST_NO_GOAL_LIFECYCLE_BOUNDARY {"goal_sent": false, "runner_rc": 0, "shutdown_ack_present": true, "startup_status": "SMOKE_READY"}
AXIA_G07_C04_REAL_OFFICIAL_CM_CALLBACK_HANDLE_IDENTITY_L1_PASS_NO_GOAL
AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false
```
- **첫 L1 실패와 두 번째 L1 성공의 차이는 코드 기능 수정이 아니라 실패 진단 가시성**이다. 이전 missing shutdown 파일 원인이 사라졌다고 증명된 것이 아니다. 같은 조건 2회 중 1회 종료 검증 실패를 이력으로 보존하고 확률적 안정성을 주장하지 않는다.
- 메타데이터 전체 수집 count (195 rcl_subscription_init / 133 callback_added)는 **전체 trace의 수**이지 해당 CM 단독 수가 아님. 공개 결과에서 원본 PID/핸들은 숨기고, **한 프로세스 소유권과 콜백 핸들 1개**만 확정.
- Cycle04 제한된 완료 정의: `OFFICIAL_CM_CALLBACK_TOPIC_IDENTITY=PROVEN_NO_GOAL`. Moving first-gap callback duration/TF wait/Guard150ms는 그대로 미검증.
- 학습 주제: CI GREEN의 인과와 재현성 한계. 두 번째 성공만 선택해 첫 실패를 삭제하지 않는다.
- **다음 Cycle05**: 이 exact `topic→callback` 매핑과 기존 Cycle30 bounded CM PID trace를 재사용해서 **Moving Goal 최초 CM source gap 하나의 callback start/end**를 시간축 맞춰 분리할 수 있는지 판단. 기존 표본/immutable trace를 우선하고 원본이 없을 경우에만 단일 짧은 공개 CI 시뮬레이션 진단 Goal을 허용. Tracing을 켠 실행은 별도 진단이며 120ms 운영 Release 통과 근거로 사용하지 않는다.

## 최종 출고/정리
- 공개 release의 Cycle04 한시 NO_GOAL workflow는 검증 성공 후 삭제 commit `96ae067290a4dad985c29c00c3ec315a2ea2b15c`. 이는 기존 release G07 Moving Goal HOLD workflow를 변경하지 않음.
- Cycle04 원본과 교육용 보고서, 수정 이력은 Draft PR #143 및 GitHub Run #43993776141(첫 L1 FAIL), #43994237080(둘째 L1 PASS)로 보존. 
- **완료 범위: 공식 CM callback handle identity YES, 실제 callback 실행시간 및 TF wait root cause NO**. 새로운 Moving Goal 시연 인수 승인 아님.
