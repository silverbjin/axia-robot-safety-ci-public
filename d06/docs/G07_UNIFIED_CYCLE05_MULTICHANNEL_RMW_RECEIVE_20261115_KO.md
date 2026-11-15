# AXIA G07 개발 사이클 05 — 다중 채널 RMW 수신 지연과 공통 Goal 관측기 CPU 분리

- 날짜: 2026-11-15
- 상태: **공개 회귀 GREEN + 비공개 sealed L0 GREEN / 실 Gazebo L2 재검 진행 중**.
- 증거: CI 실 Gazebo L2 [#43690918618](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43690918618) **FAIL**.
- 진단 범위: **첫 실제 전달주기 위반**. Guard·CM/스캔 150/300ms TTL 불변.

## 1. 관측·원인 후보
첫 위반 Odom `367.364025880`→`367.719907854` = **355.881974ms**, PRE_STOP. CM 콜백 383.109139ms; Guard 364.427292ms; scan 373.624092ms; Supervisor 352.722632ms. 반면 동일 CM RMW source sequence +1의 source gap **70.891726ms**, receive gap **377.049077ms**, observer callback gap **383.109139ms**. Source 최대 131.984ms. CM 발행 중단 증거가 아닌 **DDS 수신/Goal Observer CPU 스케줄링 지연 후보**이다.

## 2. 공개 CI TDD
- `d06/tests/fixtures/g07_ci_43690918618_multichannel_rmw_receive_gap_sanitized.json`: 실측 비식별 수치만 제공하며 원본 Goal UUID, private rosbag 미포함.
- RED `cdacc356835ab16b51c2a4a75432dc029520260f`, [#43692517210](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43692517210) 기대된 FAIL.
- GREEN `b0935e54da59b4af910dc62184b04daef67dd8cf`, [#43692568543](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43692568543) SUCCESS. `d06/live/g07_multi_channel_receive_gap.py`는 `HOLD_MULTICHANNEL_DELIVERY_BEFORE_STOP`, `RMW_RECEIVE_OR_OBSERVER_SCHEDULING_CANDIDATE`로 구분한다. 미관측 CM scheduler root를 확정하지 않는다.

## 3. 비공개 CI/Owner 공통 실행기 TDD
- RED `64a338a6f1e04683f7e6920d22ef434f14ea44d6`, sealed [#43692715147](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43692715147) FAIL.
- GREEN `5a70ab6afb1290e5d6a1b9ce892716272cc3bbab`, sealed [#43692856500](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43692856500) SUCCESS. 코드 `tools/p2_g07_goal_observer_cpu_plan.py`; 동일 `scripts/p2_no_goal_smoke_ci.sh`와 `scripts/p2_owner_l3_wsl2.sh`에 Goal 관측기 `taskset` 마스크 주입; 공통 `tools/p2_g07_ci_moving_goal.py`에서 ROS/Gazebo Goal 이전 runtime CPU mask readback 검사.
- 선택 로직: 허용 CPU N>=4일 때 display=첫 번째, MarkerArray monitor=끝에서 두 번째, 14-topic bag=마지막, **Goal observer는 나머지 중간 코어**만 사용. CI 4-core이면 CPU1, Owner 8-core이면 CPU1~5 (실제 허용 목록에서 산출). 노드 안전정책 CPU, Guard/CM/Official Nav2, 120/150/300ms 제한은 변경하지 않음.
- 정적 검증은 스케줄러 원인 확정이 아니며 실제 L2 안전 주기 개선 여부가 필요.

## 4. 검증 게이트 및 다음 단계
- 실제 L2 후보: [#43692909902](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43692909902) — **실행 결과 대기(문서 작성 시점)**. 비공개 SHA `5a70ab6...`, public GUI source `70f9d4ec...`; 위반 또는 shutdown 실패하면 기존 후보를 Owner에 배포하지 않음.
- Owner WSL2 신규 Goal **NOT_RUN**, 기존 성공 P4 `db1eec05...` 불변, main 병합 없음.
- 사용자 증거 수집: `d06/live/g07_owner_evidence_bundle.py`가 나중에 Owner exit에서 원본·GUI·G11 자료를 로컬 단일 압축 디렉터리와 SHA256SUMS로 보존하도록 공개 CI L0 테스트됨; 실제 WSL2 보존은 미검증.
- 교육 교훈: **RMW source 간격과 RMW receive/콜백 간격의 인과를 분리하고 첫 위반을 재현해야 한다**. 짧은 CM source gap을 포함한 실패를 임의로 PASS 처리하지 않는다.
