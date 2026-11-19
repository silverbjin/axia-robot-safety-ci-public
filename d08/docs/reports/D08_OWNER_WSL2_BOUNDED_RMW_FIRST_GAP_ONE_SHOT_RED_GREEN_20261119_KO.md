# AXIA D08 — Owner WSL2 RMW 단일 실행 연결·최초 Scan 타이밍 위반 분리 보고서

**2026-11-19 KST / 공개 CI 실증 / 교육용 RED→GREEN→REFACTOR→REVIEW→COMMIT**

## 기준·재사용

- 공개 코드 Draft [PR #188](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/188), `fix/d08-owner-rmw-one-shot-20261119`, 정확한 코드 SHA `28c554b1a112499af9f8e1159a77e1f70185ab8b`. 코드는 Draft 상태, main 미병합.
- 재현 출발점: #44312306299의 `cycle_0000` ROS Scan 최초 수신 공백 **505.365ms > 500ms**; 과거 Owner 518.394ms. 기존 fail-closed 판정 유지.
- 재사용한 실제 검증: PR #179~#187의 Native Gazebo Scan, 분리 ROS subscriber, Executor 50ms bounded wait, Jazzy LTTng rcl/rmw timestamp trace. 이전 정확한 기준선 `6cfc076894fb5747931ecebf1bc3eb0838bc5bac`, CI #44460443303 L0 215/215 및 공식 Gazebo NO_GOAL 8-cycle SUCCESS. 원본 성공 증거 불변.
- 금지: Nav2/TB3/World/CM/Supervisor 변경, 새 Goal 또는 `cmd_vel` 발행, 500ms Scan/CM120ms/Guard150ms 기준 완화, 인증 E-Stop 주장.

## 최소 구현

| 경로 | 수정 목적 |
|---|---|
| `d08/scripts/d08_owner_no_goal_bootstrap.sh` | 기존 WSLg/YOLO/Gazebo Owner 원샷에서 정확한 개발 브랜치 SHA fetch·확인, 공식 Gazebo Native Scan 및 독립 ROS Scan observer 구동, RMW trace 시작·자동 종료·Ctrl+C 처리, 실패 시 소형 개인 증거 ZIP |
| `d08/scripts/d08_ros_trace_live_ci.sh` | `AXIA_D08_TRACE_OUT`, 고유 세션, `flock` 기반 idempotent stop, 기존 공식 RMW trace에 제한된 source별 timing JSONL 추가 |
| `d08/scripts/d08_rcl_trace_summary.py` | 기존 source timestamp publish→take 검증·Node identity 보존, 최대 12,000개 RMW event row 로컬 임시 보관; 거짓 source/TTL 판정 금지 |
| `d08/scripts/d08_owner_rmw_first_gap.py` | 최초 실제 공식 3상 Path/Owner 반복 Scan >500ms를 같은 host monotonic의 publisher/독립 ROS/기존 Observer RMW 창과 비교; AMCL initial recovery 최초 raw record 별도 보존 |
| `d08/scripts/d08_compact_evidence.py` | 기존 비공개 ZIP에 RMW summary·첫 진단 verdict·trace 크기/상태만 추가. 원본 CTF, 임시 JSONL, 자산, 바이너리 미포함 |
| `d08/tests/test_d08_owner_rmw_one_shot.py` 및 `.github/workflows/d08-main-no-goal-real-gazebo-l2.yml` | 최초 실패 RED unit, exact Owner 스크립트 계약, 실제 Gazebo same-run RMW trace→Owner 분류기 오프라인 검증 |

## RED→GREEN 회차별 실제 CI

1. 최초 Owner 미연결 RED [#44463991605](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44463991605): `3 failed, 216 passed`. 브랜치별 trace 검증 위치·부동소수점 브래킷·압축 경로 정적 계약 수정.
2. 재현 RED [#44464115536](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44464115536): `1 failed, 218 passed`. RMW가 100ms마다 전송 중인데 최초 Observer 550ms 창의 양끝만 비교해 publisher가 600ms 멈췄다고 오분류한 실제 테스트 실패. **양끝 차이가 아니라 연속 RMW 발행 이벤트의 최대 간격**으로 수정.
3. 부분 GREEN [#44464661039](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44464661039): L0 `219 passed`, 실제 Gazebo/공식 Nav2 NO_GOAL 8/8, RMW trace와 분류기 same-run 오프라인 PASS. RMW 매칭 5,953건, 최대 514.404ms (read-only 독립 RX 노드). 첫 AMCL 650ms 인위적 복구가 별도 첫 경로 위반을 가리는 문제를 발견.
4. 초기 recovery vs 첫 Path 구간 RED [#44465432317](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44465432317): `2 failed, 219 passed`. 시계열 최초 AMCL pre-Goal recovery 기록을 버리지 않으면서 **첫 공식 Path 또는 Owner `cycle_0000` 위반**이 있을 때 해당 이벤트를 RMW 분석 대상으로 우선 선택하도록 수정.
5. 최종 GREEN 정확한 SHA `28c554b1a112499af9f8e1159a77e1f70185ab8b`, [실제 공개 CI #44465533031](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44465533031): **L0 `221 passed in 1.10s` + 원샷 `--self-check` PASS**, Gazebo ONE World·공식 Nav2·첫 3상/동일 World **8/8 NO_GOAL L2 PASS**, `D08_OWNER_RMW_PUBLIC_L2_OFFLINE_CONTRACT_PASS_NOT_WSL2`.
6. REFACTOR/REVIEW: 임의 Sleep, RMW/CM/Guard/센서 변경 및 안전 기준 완화 없음. 초기 복구 gap은 그대로 기록; RMW가 없거나 독립 Observer 정보가 부족하면 `cause=UNDETERMINED`. 같은 실행을 현장 재시도하는 대신 공개 CI로 회귀 편입.

## 실제 GREEN 아티팩트와 해석

- 공식 Gazebo/8-cycle L2 artifact `14501189387`: ZIP SHA256 `024d4a4c7a61bf87d8d5440e618c6ed091fd81357ecda8ffe0d6d0bbac9c4538`, 113 entries, CRC PASS, 8개 `cycle_XXXX/verdict.json` 전부 `D08_REAL_THREE_OFFICIAL_NAV2_PATH_PHASES_L2_PASS_NO_GOAL`.
- RMW+Owner offline artifact `14502071934`: ZIP SHA256 `80a582a6c588bfd5eb147dd982b05556883f895005196cb51f14bf231bfd3ed2`, 8 entries, CRC PASS. 같은 RMW source timestamp **6,234건**, 최대 686.360ms, 수신 노드 **`axia_d08_independent_rx_no_goal`**. 이 큰 값은 독립 관측자의 발행→take 지연이며 Collision Monitor 내부 수신 TTL 또는 안전 위반을 직접 증명하지 않음.
- CI가 인위적으로 만든 초기 AMCL 회복 gap **658.265ms**는 `chronological_first_raw_boundary`와 `initial_pregoal_recovery`에 유지. 이후 공식 Path/Owner 8-cycle에는 Scan >500ms 위반 없음. Offline 최초 recovery만 보면 `candidate=EVIDENCE_INCOMPLETE`, `cause=UNDETERMINED`이며 **의도한 fail-closed**. 성공한 Path로 원본 초기 위반을 소급 PASS하지 않음.
- 실제 WSL2/WSLg 화면, GPU 렌더러·사용자 관찰, 현장 518.394ms의 완전한 근본 원인, CM 내부 receiver와 Guard TTL·STOP/SLOW는 **NOT_RUN / NOT_VERIFIED**.

## WSL2 강사 Owner 한 번 실행

아래 블록 하나로 정확한 공개 CI GREEN 코드를 내려받아 실행한다. 운영체제 WSL2 Ubuntu 24.04 / ROS Jazzy / Gazebo Harmonic / WSLg 및 NVIDIA D3D12 선택 조건을 기존 원샷이 검증한다. Native Python 바인딩과 공식 tracing 패키지는 필요 시 apt로 설치한다. 현장 실행 중 Gazebo/RViz에서 관찰하다가 **Ctrl+C**로 종료하면 종료 trap이 RMW trace·최초 위반 verdict 및 개인 증거 ZIP/해시를 자동 생성한다.

```bash
(
  set -Eeuo pipefail
  SHA='28c554b1a112499af9f8e1159a77e1f70185ab8b'
  SCRIPT="$(mktemp --suffix=.sh)"
  trap 'rm -f -- "$SCRIPT"' EXIT
  curl -fLsS --retry 3 --connect-timeout 15 --max-time 90 \
    "https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public/$SHA/d08/scripts/d08_owner_no_goal_bootstrap.sh" \
    -o "$SCRIPT"
  bash -n "$SCRIPT"
  bash "$SCRIPT" --self-check
  export AXIA_D08_PUBLIC_SHA="$SHA"
  export AXIA_D08_TRACE_CAPTURE_MAX_S=120
  bash "$SCRIPT" --run
)
```

예상 증거 패턴: `D08_OWNER_NATIVE_GZ_ROS_RX_PROBES_AVAILABLE`, `D08_OWNER_RMW_TRACE_STARTED_BEFORE_YOLO_AND_GAZEBO`, `D08_OWNER_FIRST_BOUNDARY_RMW_CANDIDATE=<CANDIDATE>`, `D08_OWNER_FIRST_BOUNDARY_RMW_CAUSE_UNDETERMINED`, `D08_OWNER_FIRST_BOUNDARY_RMW_VERDICT=...`, `D08_OWNER_COMPACT_EVIDENCE=...`, `D08_OWNER_COMPACT_EVIDENCE_SHA256=...`. 마지막 두 파일만 공유하면 된다. CTF 원본은 로컬 보관하고 공개 저장소에 업로드하지 않는다.

`EVIDENCE_INCOMPLETE`는 오류 분석에 필요한 최초 RMW 시각 창이 충분히 수집되지 않은 뜻이다. 과거 실제 Owner 500ms 초과 경계가 재발하면 동일 현장 재시도를 반복하지 말고 그 ZIP을 받아 **최초 위반의 재현 가능한 부분을 CI 회귀 RED부터 편입**한다. 인수 자동 승인, G07 Moving Goal 및 인증 E-Stop 주장은 하지 않는다.

## 현재 판정

```text
D08_OWNER_RMW_ONE_SHOT_SOURCE_SHA=28c554b1a112499af9f8e1159a77e1f70185ab8b
D08_OWNER_RMW_L0=PASS_221
D08_OWNER_RMW_PUBLIC_ACTUAL_GAZEBO_L2=PASS_8_OF_8_NO_GOAL
D08_OWNER_RMW_PUBLIC_OFFLINE_WIRING=PASS_NOT_WSL2
D08_OWNER_WSL2_L3=NOT_RUN
D08_HISTORICAL_FIRST_GAP_ROOT_CAUSE=UNDETERMINED
D08_CM_INTERNAL_RX_GUARD_TTL=NOT_VERIFIED
D08_MOVING_GOAL_E2E=HOLD
CERTIFIED_ESTOP=false
MAIN_MERGED=false
```
