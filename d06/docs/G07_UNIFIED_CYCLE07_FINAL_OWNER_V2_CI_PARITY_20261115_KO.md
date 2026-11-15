# AXIA G07 개발 사이클 07 — 실 Gazebo 성공 SHA 고정과 Owner WSL2 v2 원샷 인수 준비 (교육용)

- 작성일: 2026-11-15
- 상태: **CI L2 PASS_SCOPED / v2 공개 CI 인수 게이트 GREEN / Owner WSL2 L3 NOT_RUN / MVP HOLD**.
- 사용자 WSL2 원본 최초 실패: `CM_EXCEEDS_SUPERVISOR` (CM age 69.385ms, Guard 120ms 불일치 조정 한계 초과). 같은 현장 결과의 RMW clock-step 1.47s는 별도 진단 후보로 보존.
- 최신 Instructor 후보 SHA: `bc270e28620c1909fcb34669e6036504b5cae951`; Tree `59c35abb651cdce18d3131b28497a500ca692cc2`.
- 기존 P4 성공 Instructor SHA `db1eec05e01e1db0d0d2e0c05610806ef4e499f9` 불변. 공식 TB3/Nav2 source, TTL, Guard grace 수정 없음.

## 1. 검증 범위를 제한한 실제 L2 결과
공개 Actions [#43693480829](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43693480829), workflow SHA `29dfd7a1a36e45d130d803e1b8a46cad191de50f`, 원본 Docker digest `sha256:861ae1df0560f991698d8967193380b1619589ba7770b5e2ca91ea4ef31f0c8e`.

- 동일 Private `tools/p2_g07_ci_moving_goal.run()`, 공통 `scripts/p4_g07_shared_runtime.sh`/14-topic bag, CPU 배치 `taskset=1,2` (CI 4core), Goal 전 GUI 가동 및 prearmed STOP 성공.
- 외부 Gazebo GUI `gz sim -g`, RViz, read-only MarkerArray 관측기 소스 blob `5962cefbe5cb771c09873ae0ae139948b37ae81b`. 최종 v2 공개 통합 브랜치에서도 blob 동일함을 재조회.
- 7 채널 관측 최대: source **81.066ms**, CM **141.483ms**, Guard **64.882ms**, Supervisor FSM **81.140ms**, Scan **190.864ms**, Odom **139.586ms**, Clock **105.497ms**. CM RMW source max **139.004ms**. 모두 원래 150/300ms 임계값 이내.
- 물리 Gazebo CLEAR 2.012m → SLOWDOWN 0.7489m → STOP 0.3962m, 실제 final Twist ZERO, Odom zero dwell **1.016659초** (원본 candidate round 1.017s).
- 실제 Nav2 exact Goal Cancel ACK 후 Navigation/Localization lifecycle 종료 ACK, CM clean process exit code 0, 원본 14-topic bag SQLite 및 해시, S02 native 34,819 tick 관측에 contact positive 0.
- First Guard latch 없음. **이 범위 내 1회 L2 PASS**. 기존 현장 불일치가 모든 환경에서 재발하지 않는다는 인과 증명은 아니며 WSLg·WSL2 스케줄러 등가성은 미검증.

## 2. RED → GREEN → REVIEW → COMMIT — Owner v2 고정
기존 공개 v1 P4/Owner 스크립트는 **그대로 보존**하고 새로운 v2 파일을 생성해 구버전 재실행 혼란을 방지했다.

| 항목 | RED | GREEN | 검증 범위 |
|---|---|---|---|
| 새 Public release P4 Owner source+tree/7채널 인수 | [#43693901706](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43693901706) FAIL | [#43694023013](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43694023013) PASS | 비공개 후보 exact SHA/Tree sealed checkout, 실제 `--self-check` 및 `--admission-check` NO ROS/Goal |
| 새 Owner v2 입장 판정 | [#43694177547](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43694177547) FAIL | [#43694275463](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43694275463) PASS | source SHA, 워크플로 SHA와 L2 실측, 첫 Guard latch, Nav2 shutdown/CM exit0, consent, no-TTY, 합성 원본 수집 보존 |
| 정확한 Public GitHub 단일 Bootstrap | [#43694386318](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43694386318) FAIL | [#43694440201](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43694440201) PASS | pinned public source/tree + 원본 GUI launcher byte 동일, 비대화형 Goal 차단, v2 Owner shell admission |

관련 GREEN 커밋: Release P4 Owner `6a5ffa4486d0f60a8d39838b8a939b2ff1abee88`, Public integration v2 Gate `8b9e44f4b622210831dd68055dad3efe8a293c92`, 최종 Release bootstrap `e0ecb7abe7a0ddc8beb38f706f5094024e1083c5`.

## 3. 파일 역할과 책임 경계
- `scripts/axia_g07_unified_p4_owner_once.sh` (Release): 기존 P4 원본 코드를 재사용하되 **새 CI PASS와 private SHA/Tree에만** admission 허가, 최종 Goal은 여전히 기존 비공개 Owner 수동 TTY 제어.
- `d06/live/g07_unified_final_owner_gate_v2.py`, `d06/acceptance/g07_unified_final_owner_ci_gate_v2.json`: 150/300ms TTL이 하나라도 초과/미증명, CM exit0/ACK 누락, 최초 latch 있으면 `HOLD`.
- `d06/scripts/g07_unified_final_owner_wsl2_v2_once.sh`: public release 고정 checkout, WSL2 전용, 실제 한 번의 Goal TTY 동의, new private source+tree, Xvfb와 동일 read-only GUI 프로세스 구조, 디버깅시 raw+GUI+G11 custody 원본 수집.
- `d06/live/g07_owner_evidence_bundle.py`: 로컬 `~/.axia_g07_owner_support/g07-*/`에 `support_evidence.tar.gz` + `manifest.json` + `SHA256SUMS` 생성. CI는 합성 파일로만 검증, 실제 사용자 WSL2 환경에서 수집 성공은 아직 미검증. 모든 데이터 비공개 로컬 유지, 자동 업로드 없음.
- `scripts/axia_g07_final_owner_v2_wsl2_bootstrap.sh`: GitHub Release commit 직접 내려받아 v2 Public source 및 Tree 고정. 이전 v1은 건드리지 않음.

## 4. 안전 REVIEW와 다음 인수
실행기 동일성은 코드 바이트·backend·CPU **역할 선택 규칙** 범위의 검증이다. CI는 4-core/Xvfb, WSL2는 예시상 8-core/WSLg라 최종 CPU 마스크와 커널 스케줄러/렌더러 부하가 달라질 수 있다. 최초 150ms TTL/120ms reconciliation 경계나 300ms Scan/Odom/Clock 한계를 완화하지 않는다.

**Owner WSL2: NOT_RUN, `AXIA_MVP_DEMO_ACCEPTED=HOLD`, certified E-Stop 아님**. 사용자의 1회 새 원샷 실행·원본 custody 확인까지 정식 인수 아님. 실패 시 원본 `support_evidence.tar.gz` 확보→최초 안전 상태 전이와 monotonic 첫 gap 분석→공개 CI RED→GREEN→실제 CI L2 재검, 같은 로컬 Goal 자동 재시도 금지. main 병합은 사용자 승인 필요.

교육 포인트: 과거 성공 SHA와 신규 후보 SHA를 임의로 혼용하지 말고, **같은 소스·같은 시나리오·다른 표시 환경**이라는 범위를 표시해야 CI PASS를 현장 인수의 근거로 정확히 사용할 수 있다.
