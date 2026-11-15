# AXIA G07 Cycle 10 — 최초 CM 발행 공백: Native RPC 스레드 계측과 출고 여유 분석

- 작성: 2026-11-15 / 공개 CI 비식별 교육용
- 최종 판정: **L0 GREEN, 실제 Gazebo L2 기본 시연 PASS_SCOPED, 120ms 출고 여유 FAIL, Owner WSL2 NOT_RUN, `AXIA_MVP_DEMO_ACCEPTED=HOLD`**
- Instructor 후보: `56d5f62a3e2ac03d19bfc6868def9e5180f9ab21` (sealed)
- 공개 CI L0: [Run 43718588097](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43718588097), 실제 L2: [Run 43718661078](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43718661078)
- 공개 실제 L2 워크플로: `c3209e8f009fc47c5541ad49932520cc6c82a277` (`release/p2-g06-cm-ttl-20261110`), `main` 미병합.

## 1. RED: 최초 실패의 경계

기존 Run `43715110448`의 최초 오류는 `UPSTREAM_STALE_AFTER_MOTION`, 첫 CM RMW 원본 발행 간격 `176.944537ms`, Guard 내부 CM age `173.903862ms > 150ms`였다. 이 간격은 Gazebo native set_pose STOP RPC(109.343ms) 구간과 중첩됐으며, 같은 간격에 Supervisor가 3회 발행했다. 이 사실만으로 RPC가 CM 지연을 *유발*했다고 결론 내리지 않는다. 이전 5초 ZERO timeout 가설도, 실제 30초 파라미터 readback 이후 같은 TTL 위반이 발생했으므로 단독 원인으로 기각한다.

**RED 계약**: 기존 ROS·Nav2·Guard 정책을 바꾸지 않고 정확하게 소유권을 확인한 CM `/proc/<pid>/task/*/status,wchan`을 native STOP RPC 동안만 최대 24회, 최소 8ms 간격으로 샘플링할 수 있어야 한다. 결과는 공개 가능한 합산 숫자만 남겨야 하며, 실패한 Goal을 PASS로 승격해서는 안 된다.

## 2. GREEN 변경

비공개 Instructor 변경:
- `tools/p4_g07_proc_sched.py`: `sample_thread_states()`, `BoundedCMRPCSampler` 추가. runnable/sleeping/기본 wait 분류 합계, no ROS/no Goal. 알 수 없으면 `CM_PROC_STATE_UNAVAILABLE`, 인과관계 `causality_proven=false`.
- `tools/p2_g07_ci_moving_goal.py`: 실제 CI 및 Owner가 공유하는 STOP RPC 호출 직전 계측 시작 → 응답/예외 모두 중지 후 합산 증거 출력.
- `tests/unit/test_g07_first_cm_rpc_thread_state_20261115.py`: 비정상 PID, 비식별 합산, 샘플 상한, shared runner 배치, 150ms Guard TTL 유지 확인.

실제 sealed L0 Run `43718588097`: `TEST_FIELD_RC=0; TEST_PRIOR_CPU_RC=0; TEST_POSTSTOP_CANCEL_RC=0; TEST_RPC_PROC_RC=0; BASH_CI_RC=0; BASH_OWNER_RC=0; COMPILE_RC=0`. 테스트 5+5+4+4=18개 PASS. ROS/Gazebo/Goal은 이 단계에 없음.

## 3. 실제 Gazebo L2 결과 — 성공 범위와 출고 경계를 혼동하지 않음

실제 실행: Run `43718661078`, Jazzy·Harmonic·공식 Nav2·TurtleBot3 Waffle, 실제 Gazebo GUI/RViz Xvfb, 하나의 Supervisor Goal과 Native STOP RPC.

- `AXIA_G07_CM_NATIVE_RPC_THREAD_STATE`: `samples=6, valid_samples=6, thread_count_max=16, runnable_samples=0, all_sleeping_samples=6, wait_classes={futex:74,other:18,sleep:4}`, `causality_proven=false`.
- Native STOP RPC `0.116134s`; 물리 LaserScan CLEAR `2.0356m`, SLOWDOWN `0.7492m`, STOP `0.3999m`.
- 7채널 외부 Observer 최대 수신 간격(초): `source=.073896241, cm=.132797429, guard=.069387719, supervisor=.073776410, scan=.189036130, odom=.136262689, clock=.106794262`.
- Guard 최초 latch 없음, 1.017633s 정지 odom dwell, **정확한 Nav2 Goal UUID `CANCELED` ACK**, Nav2 정상 종료, CM exit0, rosbag 14 토픽, S02 동일 Goal Native Contact 0 후보.
- 실제 L2의 원래 Goal 단계 `P2_L2_SMOKE_RC=0` / `AXIA_G07_CI_REAL_HARMONIC_NAV2_MOVING_GOAL_CLEAR_SLOW_STOP_L2_PASS_OWNER_L3_NOT_RUN`.
- 그러나 **CM 최대 132.797429ms > 운영 출고 목표 120ms**, 공개 CI의 독립 출고 여유 단계 `AssertionError: FIELD_CI_L2_PASS_LOW_MARGIN_OWNER_NOT_READY`. 따라서 **전체 workflow 실패**. Guard hard TTL 150ms는 통과했으나 WSL2에서 충분히 여유 있다고 판정하지 않는다.

## 4. 원인 판정 및 다음 한 경계

6회 모든 CM 스레드가 /proc 샘플 시점 수면 상태였으며 runnable 표본 0. 이번 RPC 창에서 **지속적인 CPU 실행량/스케줄러 과부하 가설은 지지되지 않음**. 다만 /proc wchan은 callback의 C++ call stack 또는 TF 내부 대기 상태를 입증하지 못한다. 정상 타이밍 수치 `CM 132.797ms`와 upstream Supervisor `73.776ms` 사이 차이가 약 59ms이며, 기존 G07 CM TF timeout 설정 `transform_tolerance=.05`가 하나의 제한된 대기 후보. 공식 Nav2 Jazzy Collision Monitor는 입력 Twist callback에서 센서 source `getData()`와 TF를 평가한 뒤 출력한다. 참조: https://api.nav2.org/nav2-jazzy/html/collision__monitor__node_8cpp_source.html

**Cycle 11 제안**: Safety Supervisor/Guard TTL 및 Nav2 원본을 변경하지 않는 G07 simulation 전용 CM TF 대기 최대치 `.05s -> .02s`의 좁은 가설 테스트. 대기가 실제 원인이라고 단정하지 않는다. 가설을 RED unit contract, CI·Owner 동일 runtime param readback, exact Instructor SHA sealed L0 후 **하나의 실제 L2**로 판정한다. invalid TF는 공식 CM STOP fail-closed여야 하고 CLEAR/SLOW/STOP 실제 시연이 유지되어야 한다. 실패 시 같은 시뮬레이션 재시도 대신 첫 이벤트 증거로 가설을 기각/수정한다.

## 5. 보안·출고 결론

비공개 솔루션·원본 rosbag 공개 없음, 학생 TODO 배포 없음. Xvfb GUI는 Owner WSLg 재현성 인증이 아님. 인증된 하드웨어 E-Stop 아님. `main` 병합 없음. Owner 실패한 `bc270e...` 잠금 보존. **Owner WSL2 주행 원샷 NOT_RELEASED**, `AXIA_MVP_DEMO_ACCEPTED=HOLD`. 새로운 실제 Gazebo L2와 승인된 운영 출고 여유가 충족되지 않는 한 WSL2 Goal 지시 금지.
