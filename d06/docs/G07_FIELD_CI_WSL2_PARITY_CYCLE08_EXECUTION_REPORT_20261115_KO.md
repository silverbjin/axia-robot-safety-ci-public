# AXIA G07 — CI→WSL2 재현성 Cycle 08 실행 보고 (2026-11-15)

**판정: PUBLIC_L0_GREEN / PRIVATE_SEALED_L0_UNVERIFIED_INFRA_BLOCKED / NEW_REAL_GAZEBO_L2_NOT_RUN / OWNER_L3_NOT_RUN / AXIA_MVP_DEMO_ACCEPTED=HOLD**

## 1. 범위와 기존 증거 재사용

- 이전 CI 정확 원본: `#43693480829` = 실제 Jazzy/Harmonic/Gazebo GUI/RViz 단일 Goal 범위 한정 PASS. Instructor `bc270e28620c1909fcb34669e6036504b5cae951`, 기존 공개 L2 workflow `29dfd7a1a36e45d130d803e1b8a46cad191de50f`. **이번 수정 SHA의 합격 근거로 옮기지 않음**.
- 사용자 WSL2: 과거 `UPSTREAM_STALE_AFTER_MOTION`, Guard 내부 CM age `158.007666ms > 150ms`; 후속 재진입은 기존 시도 폴더로 `AXIA_G07_FINAL_OWNER_REPEAT_BLOCKED...` (PRE_GOAL / NO_GOAL). 1.5s RMW wall-clock 불연속은 별도 시계영역 후보. 원본 보존, 재주행 금지.
- 기존 L2의 CM callback max `141.482825ms`는 안전 150ms 이내지만 출고 목표 120ms를 초과: `CI_L2_PASS_LOW_MARGIN`. 운영 목표는 안전 TTL 변경 아님.

## 2. RED→GREEN 및 실행 결과

| 구분 | Run·원본 출력/결과 | 유효 범위 |
|---|---|---|
| Public RED | [#43707897165](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43707897165) FAILURE, 외부 HOME/Guard 첫 경계 계약 오류 | 공개 L0, NO ROS/Goal |
| Public GREEN | [#43707984699](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43707984699) SUCCESS | 공개 L0 |
| 최종 Public GREEN | [#43709192242](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43709192242), `Ran 10 tests in 0.071s\nOK\nAXIA_G07_FIELD_WSL2_L0_PASS_NO_ROS_NO_GOAL` | 공개 L0, persistent HOME, sanitized 158ms, margin, 외부 HOME CLI, 봉인된 NO_GOAL bootstrap |
| Private scheduler RED 시도 | [#43708224701](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43708224701) FAILURE | sealed job 실패; 테스트 RED 여부 **미확정** |
| Private scheduler GREEN 시도 | [#43708555902](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43708555902) FAILURE; [#43709192248](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43709192248) FAILURE | sealed job `steps=null`, 로그 조회 `BlobNotFound`, Artifact 없음. 원인·테스트 통과 미확정. **GREEN 보고 금지** |
| 보호 release CI 진단 | Public `release/p2-g06-cm-ttl-20261110` CI-only workflow commit `3b901075d27a99b0fbcaee7aabd9b7995de3329b` | Push Run을 사용 가능한 API에서 직접 확인하지 못함. 결과 `UNVERIFIED` |

## 3. 변경된 실제 소스 및 재사용 부분

**공개 브랜치:** `fix/g07-field-ci-wsl2-parity-20261115`, 이전 검토 HEAD `c6eb05e54a708cdf4b22dbbc577f6cb7e1efd0fa`.

- `d06/tests/fixtures/g07_field_first_guard_158ms_sanitized_v1.json`: 비식별 최초 안전 전이 수치.
- `d06/tests/test_g07_field_persistent_home_release_v3.py`: 10개 public L0 회귀.
- `d06/live/g07_owner_field_preflight_v3.py`: 기존 예약 상태·first Guard TTL·출고 여유를 read-only 분류. **항상 Goal 미허가**.
- `d06/scripts/g07_owner_field_readonly_preflight_v3.sh`: HOME 외부 실행, no ROS/no Goal.
- `scripts/axia_g07_field_readonly_wsl2_once.sh`: 검증 소스 `6d715227564de0ddab6cee8dfd6e156254f12266` exact checkout으로 사전 진단, 원본·잠금 삭제 안 함.
- `.github/workflows/axia-g07-field-wsl2-parity-l0.yml`: 10 테스트 실제 L0.
- `.github/workflows/axia-g07-field-private-cm-scheduler-l0.yml`: Instructor sealed L0 **현재 BLOCKED**.
- Draft Public PR [#127](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/127), release CI candidate Draft [#128](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/128). **미병합**.

**비공개 코드 후보 (아직 GREEN 아님):** `silverbjin/axia-robot-safety-instructor` 브랜치 `fix/g07-field-cm-delivery-cpu-headroom-20261115`, SHA `8a8cf5286d90eb2f41ea1c0d2465211add5fc395`.

- `tools/p2_g07_official_cm_cpu_affinity.py`: 기존 D06의 exact PID·thread affinity 적용/원복 후보 선택 이식.
- `tools/p2_g07_goal_observer_cpu_plan.py`: 4코어에서도 native prearmed STOP 2 CPU를 보존하며 CM CPU 예약.
- `scripts/p2_no_goal_smoke_ci.sh` 및 `scripts/p2_owner_l3_wsl2.sh`: **같은 official CM CPU helper**를 Goal 전 적용, Nav2 shutdown 전 복원하도록 연결.
- `tests/unit/test_g07_field_official_cm_cpu_parity_20261115.py`, `tests/unit/test_p4_g07_goal_observer_cpu_parity_20261115.py`: 최소 변경 경계 L0 후보.
- 공식 Nav2/CM/TurtleBot3 및 Guard 150ms·120ms grace·Scan/Odom/Clock 300ms·Supervisor 500ms·native STOP 2 CPU를 완화하지 않음. 새 코드 L0/L2가 미검증이므로 출고 불가.

## 4. 안전한 WSL2 진단만 허용

정확하게 검증된 공개 Bootstrap commit `c6eb05e54a708cdf4b22dbbc577f6cb7e1efd0fa`의
`scripts/axia_g07_field_readonly_wsl2_once.sh`는 외부 git 조회와 pure Python 분류만 수행하며, **ROS·Gazebo·Goal·기존 잠금 삭제가 없다**. 기존 실패를 유지하므로 `HOLD`와 종료코드 3이 정상적인 fail-closed 결과이다. 이것은 WSL2 **인수 주행이 아니다**.

## 5. 출고 전 필수 잔여

1. Sealed CI `steps=null`, 로그 `BlobNotFound`, Artifact 미생성 문제에 대해 GitHub Actions 환경/runner/권한을 복구하고 **정확한 private SHA**에서 실제 L0 GREEN 확인.
2. 변경된 **동일 private SHA**로 실제 Harmonic/Nav2 + 외부 Gazebo GUI/RViz 1 Goal L2를 수행하고 CM source→RMW receive→**Guard native callback**→Scan/Odom/Clock 및 prearmed STOP 2CPU, 첫 latch, zero dwell, S02 Contact 0, exact Goal Cancel, Nav2 Shutdown ACK, CM exit0 확인. 150/300ms HARD와 별도 운영 여유(120/240ms)를 분리.
3. 충분한 CI L2 증거를 확보한 뒤에만 **새 private SHA, public bootstrap SHA, tree, 실제 L2 run**으로 Owner one-shot v3를 출고. 이전 v2 사용자 잠금 삭제/재사용 금지.
4. 사용자 실제 WSL2 L3 raw+GUI+first timing 리뷰 및 최종 승인 전 `AXIA_MVP_DEMO_ACCEPTED=HOLD` 유지.
5. `main` 병합·학생용 비공개 정답 배포 없음. 인증된 hardware E-Stop 아님.

**이번 턴의 실제 Gazebo 새 실행: 0건, 실제 Owner WSL2 새 Goal: 0건.**
