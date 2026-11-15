# AXIA G07 Cycle 11 — CM TF timeout 20ms 가설 RED→GREEN 후 실제 L2 기각

- 2026-11-15 / 교육용 첫 실패 중심 리포트
- 최종 판정: **sealed L0 26/26 PASS, 실제 Jazzy·Harmonic G07 L2 FAIL, WSL2 L3 NOT_RUN, `AXIA_MVP_DEMO_ACCEPTED=HOLD`**.
- RED private SHA `88b894ac1cb8dc3a136d85080d3c39bae07132b8`, sealed L0 Run [43719279853](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43719279853) FAILED, 예상 TF20ms 계약 미충족 3건 / 기존 TF50ms 계약 4건 PASS.
- GREEN private SHA `71753b2903c6de1da956501097899819ad82dff7`, sealed L0 Run [43719428808](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43719428808) SUCCESS, 기존+신규 5+5+4+4+4+4=26개 unit PASS.
- 실제 Gazebo L2 Run [43719502735](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43719502735), workflow SHA `2171452eee6bd1dee05789ac38582e6d3ba25ff4`, **FAIL**. 새 SHA에서 CM `transform_tolerance=0.02` 실제 pre-Goal `ros2 param get` 통과.

## 증거: 최종 예외가 아닌 최초 안전 상태 전이

실제 Clear(2.032m)·Slowdown(0.7445m) 이후 G07 Native STOP Gazebo set_pose 물리 RPC `109.766ms`. STOP 직전 Slowdown 관측 CM 수신 age `47.897961ms`. 후속 첫 CM RMW 발행공백 `161.609079ms`에 Supervisor upstream 3회, 최대 upstream `49.770531ms`. **첫 Guard 내부 CM age `155.829854ms >150ms`**, 최초 전이 `UPSTREAM_STALE_AFTER_MOTION`, Guard 안전 ZERO. **Goal 취소/Contact 0/정상 종료 인수 증거 도달 전 차단**. 이 실패를 `cm 20ms` 설정의 성공으로 평가하지 않는다.

RPC 구간 /proc passive sampler 6회 모두 CM 16개 스레드 runnable 0, sleeping 6회. 누적 wait class `futex=71, other=19, sleep=6`. 이 제한된 스냅샷으로 TF callback/대기와 RPC의 인과를 증명할 수 없지만 추가 CPU 코어/우선순위 무작위 조절은 근거가 부족하다.

## 변경·판정

- `tools/p4_g07_cm_tf_bound.py`: G07 한정 `.05 -> .02`; 실제 CM invalid TF는 STOP fail-closed.
- `scripts/p4_g07_shared_runtime.sh`: CI·Owner 공통 실측 20ms 사전 검사.
- `ros2_ws/src/axia_safety_bringup/launch/axia_p2_launch_policy.py`: 동일한 한정 CM 파라미터 로그.
- `tests/unit/test_g07_cycle11_cm_tf_headroom_20261115.py`, 기존 `tests/unit/test_p4_g07_cm_tf_bounded.py`: RED→GREEN.
- Safety Supervisor/Guard 150ms TTL, sensor 300ms, native STOP 2 CPU, S02 Contact/정확 Cancel/Shutdown oracle는 완화하지 않음.
- 결론: TF 20ms만으로는 초과를 억제하지 못하므로 **Cycle12에서 TF를 이전 .05로 되돌리고** 다른 한 경계를 검증한다. 실제 WSL2 Goal 출고 금지.

## Cycle 12 제어 가설

새 원본은 STOP 이전 CM age 약 47.9ms와 Native RPC 약 109.8ms를 합치면 157.7ms가 되어 최초 150ms 위반을 설명할 수 있다. 기존 Observer의 **실제 `/cmd_vel_pre_guard` 메시지 수신시각**을 사용해 STOP 이동 RPC를 최대 ~5~10ms 신선 상태에 정렬하면 같은 RPC 동안 안전 TTL 소진 여유를 늘릴 수 있다. 이것은 메시지 재발행/가짜 CM/안전 정책 완화가 아닌, **실제 물리 장애물 이동 명령 시점만 조정하는 MVP Fault Injector 한정 가설**이다.

반드시 RED: stale/no CM/Guard latch/Goal non-executing에서 STOP RPC 금지. GREEN: bounded read-only wait+기존 /scan·odom·Goal 검증 유지. 같은 private SHA로 sealed L0→실제 GUI Gazebo L2, CM 최대 120ms 출고 여유/150ms 하드/7채널/S02/Cancel/Shutdown/WSLg 미검증 명시. 성공 원본이 없으면 READY 주장 금지.

`main` 병합·학생 배포·기존 실패 Owner lock 삭제 없음. 하드웨어 인증 E-Stop과 구분.
