# AXIA G07 Cycle 15 — TF20ms + Fresh CM STOP 조합의 실제 L2 및 첫 종료 실패

**날짜:** 2026-11-15. **최종:** SEALED L0 39/39 GREEN; 실제 Jazzy/Harmonic GUI L2 Goal·STOP·Cancel 부분 PASS; **Nav2 localization shutdown ACK TIMEOUT**, CM 120ms 운용 여유 미달. Owner WSL2 NOT_RUN; `AXIA_MVP_DEMO_ACCEPTED=HOLD`.

- Instructor exact SHA `dbe57a76092c44718c8f00a3cfb0a0eab32d6640` (`fix/g07-field-cm-delivery-cpu-headroom-20261115`)
- Public exact L2 workflow SHA `1c3a0f6f5502d5e48996feca80e72ea970e75feb` (`release/p2-g06-cm-ttl-20261110`)
- [RED 43725940140](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43725940140) → [GREEN 43726079347](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43726079347) → [실제 L2 43726160832](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43726160832).

## 1. 실험 가설

Cycle11 TF20ms 단독은 STOP RPC 이전 CM age 약 48ms 때문에 150ms Guard 위반으로 실패. Cycle13/14에서 **실제 CM 메시지 수신 후 0~8ms 이내 STOP RPC 발행**이 개선됐고, 첫 120ms CM source gap 안에 Supervisor RMW 발행 3개가 존재함을 증명했으므로 좁힌 TF20ms + Fresh CM STOP 조합을 시험했다. Guard TTL 150ms 및 120ms 별도 운용 게이트는 변경하지 않았다.

## 2. RED→GREEN, 코드 경계

- RED: `tests/unit/test_g07_cycle15_combined_tf_fast_fail_and_stop_alignment_20261115.py` 3 tests; [43725940140] `TEST_TF_AND_CM_FRESH_RC=1` (2개 예상 계약 실패).
- GREEN: G07 sim 한정 `tools/p4_g07_cm_tf_bound.py` TF lookup bound 50→20ms; `scripts/p4_g07_shared_runtime.sh`를 통한 CI/Owner 같은 실제 ROS param 20ms readback; `ros2_ws/src/axia_safety_bringup/launch/axia_p2_launch_policy.py` exact log, 기존 TF 단위 회귀 2개 최신 계약화.
- [43726079347] sealed `TEST_TF_AND_CM_FRESH_RC=0`, 포함 39개 unit PASS; shell 문법/compile PASS. 공식 Nav2/CM 원본 소스 및 안전 STOP 정책 불변.
- 기존 ROS2/Gazebo 안전 계층 전체 PASS가 아닌 **테스트 코드 L0**라는 점 유지.

## 3. 실제 L2 최초 실패와 시연 관찰

Run `43726160832`: 실제 Gazebo Clear front `2.04627m`, Slow `0.740005m`, STOP `0.382827m`; Native STOP RPC `0.103117s`; `CM fresh age=0.000631387s`; odom zero dwell `1.004099s`; 정상 스캔·CM STOP 및 **exact Nav2 Goal UUID `2358474b40f24019ac658955ee7732ed` CANCELED ACK**. 실행 중 최초 Guard latch는 확인되지 않음.

7채널 최대 Observer 수신 간격(ms): source `66.996`, Supervisor `67.006`, CM `121.193`, Guard `49.672`, Scan `207.767`, Odom `140.684`, Clock `105.457`. 실제 CM RMW source 기준 첫 >=120ms gap은 이번 run에서 `NO_CM_SOURCE_GAP_OBSERVED`, 반면 Observer callback max `121.193ms`. **CM 내부 발행 지연 원인 확정 불가**, observer / DDS 전달 jitter 1.193ms 초과 후보. 150ms hard는 PASS지만 120ms 출고 목표 미달.

**최초 추가 실패(시연 종료):**
```text
AXIA_G07_CANCEL_ACK_REQUIRED_BEFORE_ORDERED_SHUTDOWN exact_goal_uuid_verified=true canceled_status=5
G07_MOVING_GOAL_ORDERED_SHUTDOWN_BLOCKED
G07_NAV2_ORDERED_SHUTDOWN {"status":"BLOCKED_LIFECYCLE_LOCALIZATION_SERVICE_TIMEOUT",
 "navigation_ack":true,"localization_ack":false,
 "navigation_elapsed_sec":1.75945,"localization_elapsed_sec":25.000376,
 "navigation_request_sent":true,"cm_clean_process_exit_verified":false}
P2_L2_SMOKE_RC=3
```
후속 Exit1 및 진단 미확정은 이 첫 공식 Nav2 shutdown ACK 실패의 결과. **Shutdown clean·CM exit0·S02 original 0 contacts의 이 SHA 최종 적격 증거는 없음.** 과거 PASS로 승격 불가.

## 4. Cycle16 권장 원인 분리

공식 navigation manager Shutdown은 ACK, localization manager는 request_sent=True 후 25s 응답 없음. 기존 `tools/p2_g07_ordered_shutdown.py`는 navigation 실패 진단만 갖고 localization의 **첫 manager/node lifecycle 상태**를 수집하지 않음. 기존 실제 L2에서 localization STARTUP timeout이 발생한 이력도 있음. **새 재시도/더 긴 시간제한/강제 SIGKILL 이전에** 실제 요청 후 첫 timeout의 native receipt와 map_server/amcl lifecycle 및 service 상태를 bounded read-only로 수집하는 공통 diagnostics 개선을 RED→GREEN하여, 실제 L2에 재현되면 원인을 좁힌다.

같은 CI/Owner runner에서 localization ACK를 임의 생성하거나 Timeout을 성공으로 간주하지 않는다. Guard 150ms·CM 120ms release goal·센서300ms·Supervisor500ms 유지. 모든 다른 안전 계층의 첫 타이밍 경계 확인이 필요. `main` 미병합, student TODO/Instructor 정답 분리, Owner lock·raw 보존. 인증 E-Stop 아님.

**출고: WSL2 OWNER ONE-SHOT NOT_RELEASED / AXIA_MVP_DEMO_ACCEPTED=HOLD.**
