# AXIA G07 개발 사이클 03 — Owner 최초 Guard 전이 및 공통 실행기·증거 원샷

- 기준: 2026-11-15 사용자 WSL2 G07 Owner 원본, 강사 P4 시작 SHA `db1eec05e01e1db0d0d2e0c05610806ef4e499f9`.
- 결론: **L0 PASS / 다음 실제 L2 검증 필요 / Owner 최종 인수 HOLD**.
- 원본 안전 정책: CM TTL **150ms**, Guard 불일치 ZERO-only grace **120ms**, Scan **300ms**. 인증된 E-Stop 아님.

## 1. 증상과 최초 안전 상태 전이
사용자의 실제 Owner G07에서 `CM_EXCEEDS_SUPERVISOR` 최초 래치가 발생했다. CM 입력 age는 **69.38474ms**, 최근 Supervisor 입력은 **43.692944ms**로, CM TTL 초과로 분류해서는 안 된다. 실제 불일치 조정 시작 `3903.631154036` → 최초 래치 `3903.756578606`: **125.424570ms**, ZERO-only 유예 120ms 초과. 당시 최신 CM (0.074427m/s, 0.183299rad/s)이 Supervisor (0.057661m/s, 0.098229rad/s)보다 컸고, Guard 출력은 안전하게 ZERO였다. 속도를 허용하거나 latch를 지워 성공 판정을 내릴 수 없다.

독립적인 계측: CM RMW source 간격 **1.470056234s**, Supervisor source **1.466053786s**로 공동 변화했으나 CM 호스트 monotonic 관측 간격은 **53.606801ms**이다. **공통 HOST_SYSTEM_CLOCK_STEP_CANDIDATE**이지 CM 프로세스가 1.47초 멈췄다는 확정 증거가 아니다. 서로 다른 절대 시계값을 빼지 않는다.

## 2. RED → GREEN
- 공개 비식별 fixture: `d06/tests/fixtures/g07_owner_20261115_cm_supervisor_mismatch_clockstep_sanitized.json`. **RED** [#43689306583](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43689306583), **GREEN** [#43689362501](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43689362501). 소스 `d06/live/d06_guard_first_mismatch_triage.py`: 불일치와 RMW 시계 불연속을 구분, fail-closed, `safety_pass=false`. 커밋 `708bb874`(RED), `bac79c59`(GREEN).
- 실제 CI는 headless Gazebo server에 `gz sim -g`/RViz2를 별도 실행하지만 당시 Owner는 내장 Gazebo GUI+RViz2였다. **같은 P4 Goal executor만으로는 GUI CPU/프로세스 parity가 아니다**.
- 비공개 강사 후보: `fix/g07-ci-owner-runtime-parity-20261115`. `scripts/p4_g07_shared_runtime.sh`의 headless selection과 `axia_g07_shared_gui_ready`를 CI/Owner 공통 진입점으로 만듦. 새로운 P4 소스 SHA는 별도 후보로만 취급, 성공한 기존 원본은 불변.
- 비공개 sealed L0 RED [#43689577854](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43689577854) → GREEN [#43689643931](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43689643931); GUI pre-Goal barrier GREEN [#43690073396](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43690073396).
- 공개 GUI 클라이언트 공통 실행기 `d06/scripts/g07_shared_gui_clients.sh`: 정확히 같은 `taskset/nice gz sim -g`, `rviz2`, `MarkerArray` 읽기 전용 관측기. Xvfb/WSLg는 DISPLAY만 다름, WSLg 화면 실물 확인은 Owner에 남음. 공개 GREEN [#43690121848](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43690121848).
- 실패 증거 원샷 `d06/live/g07_owner_evidence_bundle.py`: Owner raw + GUI + G11 custody를 `~/.axia_g07_owner_support/g07-*/`에 `support_evidence.tar.gz`, `SHA256SUMS`, `manifest.json`으로 보존. 공개 L0 GREEN [#43690335847](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43690335847), 합성 증거 기반. 실제 현장 수집 **아직 미검증**.

## 3. REVIEW 및 미검증
Guard·CM·Nav2 소스 자체, 120ms/150ms/300ms safety policy, Goal 수동 승인, 공식 TurtleBot3 모델/Map을 변경하지 않았다. CI/Owner 주행 엔진 둘 다 동일 비공개 `tools/p2_g07_ci_moving_goal.run()`, `scripts/p4_g07_shared_runtime.sh`/14-topic recorder를 사용한다. CI Xvfb 결과는 WSLg 품질/커널 스케줄링 동등성 증명이 아니며, 이 시점 본 변경 실제 L2는 미검증이다. Owner 기존 실패 원본 보관, 재시도 금지, main 병합 금지.

## 4. 교육 핵심
최종 `RAW_CAPTURE_INCOMPLETE`는 현상을 요약하지만 **첫 상태 전이는 Guard `CM_EXCEEDS_SUPERVISOR`**이다. 안전 유예를 늘리는 대신 시간 영역을 분리하고 CI가 재현 가능한 GUI·Goal 환경 차이를 먼저 제거해야 한다.
