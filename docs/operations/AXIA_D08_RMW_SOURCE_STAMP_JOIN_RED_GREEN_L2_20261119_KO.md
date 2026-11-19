# AXIA D08 — Scan 첫 위반 RMW 발행→수신 메시지 연결: RED→GREEN→실제 L2

**2026-11-19 KST / 공개 CI / 증거 기반 교육용 보고서**

## 1. 왜 재작업이 아니었는가

- 먼저 기존 Draft PR #179~#184를 비교했다. 독립 Native Gazebo Scan, 분리 ROS 프로세스, 원래 Python Observer, bounded spin_once, Jazzy LTTng canary가 이미 존재하므로 재구현하지 않았다.
- 최초 실제 공개 CI #44312306299의 `cycle_0000`: ROS Scan host receive **505.365ms > 500ms**, 헤더 시뮬레이션 간격 **102ms**. 기존 FAIL-CLOSED가 정상이었으며 수정으로 무력화해서는 안 된다.
- #44455971240 소스 `76b569bfbef66b79c131ab66656886707b9059c7`: L0/실제 Gazebo+공식 Nav2 NO_GOAL 8-cycle PASS. 같은 실행 LTTng 원본 아티팩트 #14498745702에서 /scan의 RMW publisher와 receiver를 실제 토픽에 연결할 수 있었다. **구독 주기와 메시지 단위 지연은 다르다.**

## 2. 단일 RED → GREEN

- 신규 `d08/tests/test_d08_rmw_source_stamp_message_join.py`: `rmw_publish.timestamp`와 `rmw_take.source_timestamp`가 같은 **유일한 timestamp**인 경우만 발행/수신을 연결한다. 중복·0·미일치·음수 간격은 원인 미확정. 순수 입력 fixture는 실제 Gazebo 실증이 아니다.
- RED 소스 SHA `1f5a8bba25ad1ea4590b67946bc3ed192e94f886`; 공개 CI [#44458019842](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44458019842): `3 failed, 206 passed`, `KeyError 'rmw_scan_source_stamp_join'`; 신규 L2 SKIPPED.
- GREEN 코드 `d08/scripts/d08_rcl_trace_summary.py`만 최소 확장: /scan RMW timestamp 후보 최대 12,000개 bounded, 유일 매칭/중복/미매칭/overflow 명시. regex 초안 이스케이프 수정 이력을 유지.
- 검증 SOURCE SHA `b33e6c43656ec4e2030884795a71b186896e14f6`; 공개 CI [#44458214774](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44458214774): `209 passed in 1.01s`, 실제 Gazebo/공식 Nav2 NO_GOAL **8/8 cycle PASS**. Contact/YOLO 별도 job은 의도적으로 SKIPPED (전체 4-job PASS 아님).

## 3. 새 실제 물리 증거와 해석 제한

- 실제 RMW trace ZIP 아티팩트 `14498967235` (CRC PASS): `matched_unique_pairs=6464`, `duplicate_publisher_source_timestamps=0`, `unmatched_subscription_timestamp_groups=0`, `bounded_capture_complete=true`.
- **최장 동일 RMW source timestamp 발행→수신: 543.278ms**. PID `10734`; Trace time-of-day `16183.204081→16183.747359s`; 소스 timestamp `1795062583204080097`. 별도 anchor로 계산한 monotonic 시간 약 `267.135351→267.678629s`, 기존 `cycle_0006` Native Scan 수집 구간과 시간상 겹침.
- 같은 실제 실행의 모든 8개 cycle Scan callback 최대 간격은 500ms 이하였다. 이는 **콜백 수신 간격 PASS가 개별 메시지 publish→take 신선도까지 증명하지 않음**을 보여준다.
- 이 PID의 정확한 ROS 구독 노드/Guard/CM 소유권은 이 아티팩트에 없다. `rmw_take`까지의 총 지연을 DDS 자체 장애로 단정하거나 과거 WSL2 최초 518.394ms와 같은 원인으로 합치면 안 된다.
- CTF 원본 약 105MB는 보관량 제한으로 공개 artifact에서 제외하고, 크기 제한된 JSON summary·해시 목록만 업로드. 원본 사용자 압축/비공개 자료 공개 금지.

## 4. 안전·인수

- 원본 `d08/harness/d08_amcl_initial_pose.py` blob `f44ffe3aa67bbbde03a28319d0db3587742b6f52` 보존.
- Scan/Clock/Odom 500ms 경계, G07 CM 120ms, Guard 150ms 및 NO_GOAL/NO_CMD_VEL/인증 E-Stop 구분 **변경 없음**.
- 공식 Nav2/Collision Monitor/YOLO/World/학생 TODO·강사 정답 코드 변경 없음.
- 본 GREEN은 **RMW 메시지 연결 진단 + NO_GOAL 공식 Gazebo L2** 범위만 검증한다. 원인 확정, CM 내부 RX 및 Guard TTL, Owner WSL2/WSLg L3 **HOLD**.
- 다음 계측은 공식 `rcl_node_init`과 `rcl_subscription_init.node_handle`로 최초 543ms 수신자의 실제 ROS node 이름을 연결하는 범위로 제한한다. 다른 실패는 별도 최초 경계로 분리한다.
- 코드 브랜치: `diag/d08-live-rcl-publish-take-20261119` / Draft PR #187. **main 병합 NO**.

```text
D08_L0_RMW_SOURCE_STAMP_JOIN=PASS
D08_GAZEBO_NO_GOAL_8_CYCLES=PASS_SCOPED
D08_RMW_MESSAGE_MATCHED=6464
D08_RMW_MAX_SOURCE_TO_TAKE_SEC=0.543278
D08_HISTORICAL_505365MS_ROOT_CAUSE=UNDETERMINED
D08_OWNER_WSL2_L3=NOT_RUN
D08_G07_MOVING_E2E=HOLD
CERTIFIED_ESTOP=false
MAIN_MERGED=false
```
