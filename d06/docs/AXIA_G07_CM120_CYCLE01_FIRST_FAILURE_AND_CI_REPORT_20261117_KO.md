# AXIA G07 CM120 Cycle 01 — 최초 경계 및 CI 인수 보고 (2026-11-17)

## 검증 기준/범위
- 실제 실패 C37 Run #43898345608 (https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43898345608): CM source=128.644215ms, Observer=128.318661ms > 120ms 출고 margin, 원래 hard 150ms 자체는 위반하지 않음.
- 동일 실행 Supervisor, Guard, Scan, Odom, Clock 원본 <= 기존 150/300ms; Contact/Goal/Cancel/ACK 구분 필요. 이전 Owner Guard 158.008ms >150ms 별도 첫 실측 실패 보존.
- 실제 C37 workflow .github/workflows/axia-g07-cycle37-headless-scene-moving-goal-l2.yml, original run SHA cfa95fd4041882f9c74e694e253a726005d48643. Original Instructor 966886c4627deb2bb3b37111fe336eeee6b9ebb4, public 352ea7c2197b937e8566ba90cd4d8fff46dd9f88.

## 제한된 단일 원인 후보
- 기존 Goal Python runner는 ROS 안전 노드와 별개의 procfs 진단 스레드 두 종류를 50/15ms 주기로 실행한다. 이 observer load가 실제 CM first gap에 기여했는지는 UNPROVEN.
- 변경 Instructor branch fix/g07-cm120-acceptance-no-proc-probe-20261117, SHA 795130709e7af695351bbc11b512d40d2242c4e1: 주행 중 비안전 procfs sampler 기본 off, AXIA_G07_PROC_DIAGNOSTICS=1 진단 opt-in. 원래 RMW/Guard ROS 수신, Goal/Stop, Safety 120/150/300ms, Nav2/CM/TurtleBot3 소스 불변. PRIVATE Draft PR #193.

## RED→GREEN 첫 공개 CI와 최초 실패 분류
- Run #43980886964: baseline 기존 진단 실행 상태 RED2 재현, 새 코드 GREEN2 PASS; ROS Jazzy unit/runtime preflight 다른 항목 PASS.
- **최초 실패는 PRE-GOAL의 잘못 선택된 legacy unified workflow**: pin된 public source에 test_g07_cycle23_cm_marker_role_conflict.py 부재로 0 tests, exit5. 그 후 FIELD_NO_REAL_GOAL_CANNOT_RELEASE는 downstream 오류. 실제 Gazebo Goal은 보내지지 않음. 이 결과를 CM 타이밍 실패로 취급하지 않는다.
- 올바른 기존 C37 exact workflow로 변경: public dev commit e2beecec2a7feec8679d2443cf8597af5082225a. Legacy wrong workflow는 public Draft PR에서 원복 commit 6a54a2a947cb9dfb105ab34213beb5e935346a94.
- 공개 release 동일 C37 workflow만 exact source로 시험하도록 pin: commit 4c8a6dc26acb559f96241c4f506ead78320112e7, 실제 L2 Run #43981875149 https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43981875149. 해당 L2 결과는 후속 보고 갱신 필요.

## 중단/출고 게이트
- 실제 동일 C37 Goal에서 7채널 interarrival, CM RMW source <=120ms, CM Observer <=120ms, Guard/CM hard150ms, Scan/Odom/Clock300ms, 물리 STOP+odom dwell, S02 Contact0, 실제 14-topic, Cancel+Nav2 clean shutdown을 일괄 확인한다.
- 기존 채널 PASS 재사용; 첫 실패 있으면 false PASS 및 WSL2 Owner 같은 SHA 현장 반복 금지.
- Owner WSL2 moving Goal NOT RUN, final acceptance HOLD, certified E-Stop false, public PR #138 / private #193 Draft, main merge blocked.

## Cycle01 실제 종료: 정확한 C37 Gazebo 단일 Goal L2 (2026-11-17)
- 정확한 공개 실제 [Run #43981875149](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43981875149), release source commit 4c8a6dc26acb559f96241c4f506ead78320112e7: completed/failure, 비공개 후보 SHA 795130709e7af695351bbc11b512d40d2242c4e1, public visual source 352ea7c2197b937e8566ba90cd4d8fff46dd9f88.
- 실제 L0: 기존 966886... source RED2 재현, 새 후보 GREEN2; 기존 ROS/CPU/Lifecycle/GUI preflight PASS.
- 실제 L2: Gazebo Harmonic Waffle/Nav2 one Goal CLEAR→SLOW→STOP, odom displacement_m=0.2004, stopped_dwell_s=1.01; 원본 Cancel/ordered Navigation+Localization Shutdown ACK와 CM exit0 검사 PASS.
- 변경 후 CM RMW source first gap **133.658796ms** (기존 128.644215ms), Observer **131.488230ms** (기존 128.318661ms), 120ms RELEASE FAIL. 이번 원본 `CM_SOURCE_GAP_EXCEEDS_120MS`, publication sequence delta1, gap 사이 Supervisor 발행2건, upstream max coverage51.036ms.
- 그 외 실측 최대 interarrival (모두 s): Clock0.082442771, Supervisor0.089637059, upstream source0.089689998, Guard0.088470879, Odom0.082431029, Scan0.17391162. 기존 hard Guard/CM 150ms 및 Scan/Odom/Clock 300ms 경계는 이 관측 범위에서 초과 증거 없음. 첫 Guard latch 흔적 없음 (`NO_FIRST_GUARD_LATCH_TRACE`); latch 없음은 인증/Owner PASS 아님.
- STOP native RPC 중 `/proc` sampler는 실제 0회: `CM_PROC_SAMPLING_SKIPPED_FOR_ACCEPTANCE_HYPOTHESIS`, root cause UNPROVEN. 주행 중 proc sampling omission이 120ms를 해결하지 못함; 같은 튜닝 실험으로 현장/CI Goal 반복 금지.
- 실제 실패 로그: `AssertionError: CM120_RMW_SOURCE_GAP_HOLD_CM_SOURCE_GAP_EXCEEDS_120MS_0.133658796` 및 `AssertionError: FIELD_CI_L2_PASS_LOW_MARGIN_OWNER_NOT_READY`.
- **Cycle01 stop rule 적용**: CI_PUBLIC_L2=FAIL, OWNER_WSL2_GOAL=BLOCKED, ROOT_CAUSE=UNPROVEN. 이번 후보 배포 불허. Original C38 GUI-only 성공은 보존, C39 L0 동작 관련 변경은 별도 PR #136. SW STOP은 인증 E-Stop 아님.
- 신규 모듈·장시간 스케줄러 추적·임계값 완화·두 번째 실제 Goal 실험 없이 종료. G07 후속 원인 분석은 기존 자료에서 최초 CM callback input→output과 executor 타이밍을 직접 구분할 수 있는 경우에만 별도 계획으로 재개할 것.
