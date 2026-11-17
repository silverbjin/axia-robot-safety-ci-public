# AXIA G07 통합 MVP — `05_P4_AXIA_G07_UNIFIED_MVP_5` 인계 및 재개 기록

> 기준: 2026-11-17 KST. 공개 CI 증거 재조회 기반. **전체 `AXIA_MVP_DEMO_ACCEPTED=HOLD`.** 이 문서는 성공했다고 주장하는 인수서가 아니라 다음 작업자를 위한 정확한 인계 기준이다.

## 1. 범위·정책·기준선

- 대상: ROS 2 Jazzy, Gazebo Harmonic, TurtleBot3 Waffle, **공식 Nav2**, Safety Supervisor/CM/Fault Injector/Verifier.
- Task01: **최초 CM publisher source 간격 >120ms**의 TF polling, ROS Clock, 스케줄러 및 네트워크/전달 시계 인과 분리.
- Task02: 입증된 단일 원인에 한정한 최소 수정(아직 BLOCKED).
- Task03: 진단 Tracer **OFF** 상태의 실제 Gazebo GUI+Nav2 Moving Goal, CLEAR→SLOW→STOP, 7계층 데이터 전달·안전 시간 및 정확한 Goal UUID 종료, Navigation+Localization native shutdown ACK, CM exit0, 원본 물리 증거의 **동일 세션** 검증(아직 NOT_RUN).
- Task04: 상기 **동일 SHA** 공개 CI L2 합격 후 강사 WSL2/WSLg 실제 Gazebo+RViz Live L3 일괄 검수(아직 NOT_RUN).
- 강사용 비공개 원본 소스는 private `silverbjin/axia-robot-safety-instructor`, 공개 CI/수치 허용목록 진단은 public `silverbjin/axia-robot-safety-ci-public`, 학생용은 독립 repository. **공개 CI만 사용하고 private Actions를 요구하지 않는다.** 기존 sealed read-only checkout만 사용; private write Secret 추가 금지.
- 공식 Nav2/TF 동작, CM120ms, Guard 150ms, Scan/Odom/Clock 300ms, CM source_timeout, STOP/SLOW 지오메트리, 안전 정책, CPU affinity를 원인 없이 변경하지 않는다. SW STOP은 인증 E-Stop이 아니다. `main` 병합·학생 출고는 별도 승인 전까지 금지.

## 2. 정확한 인계 Git 기준

| 대상 | 기준 |
|---|---|
| Public repo | `silverbjin/axia-robot-safety-ci-public` |
| 작업 브랜치 | `fix/g07-cm120-task01-clock-firstgap-causality-20261117` |
| 인계 전 코드·진단 HEAD | `86ac6ef2b466d2e24157f8f4f66c1d2893b61dd1` |
| Public Draft PR | [#161](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/161) — `main` 아님, 오픈/HOLD |
| 실제 Gazebo에서 READ한 original private Instructor source | `966886c4627deb2bb3b37111fe336eeee6b9ebb4` |
| 기준 관측 자료 | `d06/evidence/g07_cm120_task01/run_44049067368_first_gap_sanitized.json` 및 `SHA256SUMS.txt` |
| NO_FIRST_GAP 대조 자료 | `d06/evidence/g07_cm120_task01/run_44059005075_first_gap_sanitized.json` 및 `SHA256SUMS.txt` |

**엄격한 SHA 해석:** 보고서/문서 추가 커밋은 이전 실제 L2 runtime pass를 자동 상속하지 않는다. C32/C34 등 다른 private SHA의 성공 또한 현재 private `966886c...`의 native ACK 성공 증명이 아니다.

## 3. 실제 CI 실행 기록과 검증 범위

| CI Run | 사실 | 검증 수준 |
|---|---|---|
| [#44049067368](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44049067368) | 공식 Moving Goal 첫 RMW CM source gap **129.299071ms**, Observer gap **128.391951ms**; 동일 Observer 창 Advanced TF 약91.753ms, 10ms libc sleep 9회/실측 **91.416406ms**. 원본 cross-node 전달 최대 source344.101/CM335.077/Supervisor335.095/Guard372.483/Clock333.515/Odom346.212/Scan365.053ms. **전체 L2 FAIL**. | tracer ON, 원인 미확정 |
| [#44071779545](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44071779545) | 정확한 첫 gap 보존 자료/TF 호출 경계·Clock·TF 가용성 허용목록 Python **34/34 PASS** | 공개 L0, ROS/Gazebo 미실행 |
| [#44072012680](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44072012680) | 정식 Jazzy C++ ABI, sleep_for, Clock C/C++/cross DSO, zero-timeout Buffer availability **PASS** | 실제 Jazzy ABI L0, no Goal |
| [#44072394317](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44072394317) | 실제 Gazebo **NO_GOAL PASS**, official TF 호출589, 원본 시작 불가→종료 가용478, sleep511, 추가 0ms query 최대 overhead **0.460882ms**, Navigation/Localization shutdown ACK=true | 공식 runtime L2, **주행 인수 아님** |
| [#44073078458](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44073078458) | 실제 GUI+Moving Goal **FAIL**. CM source 최대 **117.998ms**, Observer 최대 **118.261395ms**라 첫 >120ms 재현 없음. CLEAR→SLOW→STOP, 0.1928m 이동, odom ZERO dwell1.025s, 동일 UUID CANCELED는 관측. 그러나 Navigation native SHUTDOWN **40.000372s timeout**, Localization 호출 전 차단, CM 정상 종료·물리 원본 최종 ACK 미검증. | tracer ON, 전체 L2 FAIL |

`#44065863682`의 이전 Jazzy Clock C++ ABI selftest 실패는 후속 `#44072012680`에서 해당 L0 범위를 GREEN으로 재검증하였다. **이 L0 GREEN은 40초 native ACK 결함이나 tracer-OFF 성능을 해결하지 않는다.**

## 4. 최초 위반과 독립 후속 실패 — 섞지 말 것

1. **실제 #44049067368의 최초 기준 위반:** RMW publisher source 129.299071ms > CM120ms. 동일 창의 TF polling 9×10ms는 *관찰된 동작*이나 해당 source SYSTEM 타임스탬프와 Observer MONOTONIC 정합의 확정 증거가 없으므로 **첫 source-gap 원인 입증은 UNPROVEN**. Kernel `sched_schedstats=0`이면 runnable 대기는 `UNAVAILABLE`(0ms가 아님).
2. **별도 실제 #44073078458에서의 실패:** CM120 source 초과는 없음. exact Goal 취소가 완료된 뒤 Navigation ManageLifecycleNodes(SHUTDOWN) 요청 전송은 되었지만 원본 ACK가 40.000372s 내 없음. graph는 보이고 서비스도 advertised; 이것은 **응답 성공 증거가 아니다**. Localization은 호출조차 되지 않음. 이전 C34의 'terminal gate 누락'과 동일 원인으로 오판하지 않는다.
3. 즉 두 실패를 합쳐서 "TF 고치면 native shutdown도 해결"이라고 결론 내릴 수 없다. 최신 Goal의 CM source 수치 여유는 약 **2.002ms**, Observer 여유는 약 **1.739ms**에 불과하며 tracer ON이다.
4. 출고 판단은 처음 발생한 Guard/CM/Scan/Odom/Clock 안전 상태 전이와 타이밍 위반을 기준으로 수행하며, 후속 SIGSEGV나 최종 timeout 문구만으로 원인 단정하지 않는다.

## 5. 다음 실행 순서 — MVP 최소 작업, 재시도 금지

### A. 다음 우선순위(지금 시작할 항목)
- 기존 공개 CI #44073078458 원본 로그와 기존 C32/C34 회귀를 **입력 증거로 재사용**한다. 신규 Goal을 그냥 반복하지 않는다.
- native shutdown의 첫 경계만 분리한다: **exact UUID terminal → Navigation ManageLifecycleNodes 요청 수신 → server callback 진입/종료 → 응답 발신/클라이언트 수신**. 현재 확증은 `request_sent=true`, graph/service advertised=true, 40.000372s timeout뿐이다. 서버 callback 유무/지연 원인은 **NOT_MEASURED**.
- 새 실패 재현의 **ROS-free 최소 L0 반례**는 "service advertised지만 ACK 없음", "ACK 가짜/다른 단계", "terminal 이후 request 전송"에 대해 fail-closed 유지 여부만 검증한다. 기존 검사가 이미 충족하면 새 중복 테스트를 만들지 않는다. 새로운 원인 경계를 밝힐 *1개*의 증거가 필요할 때만 read-only 계측을 추가한다.

### B. Task01 원인 완료 판정
- 기존 실제 #440490 first-gap JSON의 SHA와 S2/TF raw 한계를 보존한다.
- 공식 TF entry false→exit true의 **NO_GOAL** 관측은 478회지만 **동일 Moving first source gap**에서 입증되지 않았다. `Task01=PARTIAL_CAUSALITY_ONLY`.
- 다음 공식 Moving 계측은 기존 증거로 대체 불가한 특정 최소 가설·증거 필드를 먼저 정의하고, 공개 CI L0 RED→GREEN 후 **1회만** 실행한다. gap이 미재현이면 결과 자체를 HOLD로 보존하고 동일 CI 재시도를 반복하지 않는다.

### C. Task02→03→04 인수 문턱
- Task02: 실제 최초 120ms 원인이 재현 가능한 증거로 확인됐을 때만, 공식 Nav2/안전 TTL을 유지하는 **한 개**의 최소 수정 후보를 RED→GREEN→REFACTOR→REVIEW→COMMIT한다.
- Task03: 수정 후 **tracer-OFF** 공개 실제 Gazebo Moving Goal 동일 SHA에서 source≤120ms 및 기존 Guard150/7계층 300ms 이하, CLEAR→SLOW→STOP, odom dwell, exact UUID terminal, Navigation+Localization native ACK, CM exit0, 원본 contact/14-topic rosbag 검사 **모두 같은 세션** PASS일 때만 통합 L2 후보.
- Task04: 그 다음에만 Owner WSL2 한 번의 GUI Gazebo+RViz, 실제 이동과 감속·정지, 정확한 PID/SHA/TTY 및 원본 증거 최종 인수를 안내한다. 현재 원샷 재배포·L3 시도 금지.

## 6. 후속 작업용 실제 실행 명령과 경로

공개 기준 소스에서 코드·자료 검증을 다시 수행할 경우:
```bash
git fetch origin fix/g07-cm120-task01-clock-firstgap-causality-20261117
git checkout fix/g07-cm120-task01-clock-firstgap-causality-20261117
git rev-parse HEAD
cd d06/evidence/g07_cm120_task01
sha256sum -c run_44049067368_SHA256SUMS.txt
cd ../../..
python3 -m unittest discover -s d06/tests -p 'test_g07_task01_actual_first_gap_polling_bounds.py' -v
python3 -m unittest discover -s d06/tests -p 'test_g07_task01_tf_zero_timeout_availability.py' -v
python3 -m unittest discover -s d06/tests -p 'test_g07_task01_real_no_first_gap_custody.py' -v
```
이 명령들은 **재현용**이다. 이 인계 문서 작성 과정에서 강사 로컬 WSL2의 ROS/Gazebo를 실행했다는 뜻이 아니다.

주요 파일:
- `d06/diagnostic/cm_tf_gettransform_preload.cpp` — **CI 전용** 기존 공식 TF read-only ABI/sleep/availability probe
- `d06/diagnostic/analyze_first_cm_tf.py`, `classify_tf_availability.py` — source/Observer/TF strict boundary
- `d06/diagnostic/export_public_cm120_first_gap.py` — 비공개 raw 없이 숫자만 공개
- `d06/tests/test_g07_task01_tf_zero_timeout_availability.py` 등 — L0
- `d06/docs/AXIA_G07_TASK01_BUFFER_AVAILABILITY_READONLY_CYCLE05_20261117_KO.md` — 상세 최신 개별 실패 보고
- 비공개 Instructor 종료 측 `tools/p2_g07_lifecycle_service.py`, `scripts/p2_no_goal_smoke_ci.sh` — **후속 server callback 원인 조사 대상**, 공개 전 원본 유출 금지

## 7. 인계 판정 및 필수 출력

```text
AXIA_G07_TASK01_PUBLIC_L0_FIRSTGAP_REGRESSION=PASS_34
AXIA_G07_TASK01_REAL_JAZZY_ABI=PASS_44072012680
AXIA_G07_TASK01_REAL_NO_GOAL_AVAILABILITY=PASS_44072394317
AXIA_G07_TASK01_REAL_MOVING_DIAG=FAIL_44073078458
AXIA_G07_TASK01_ORIGINAL_FIRST_SOURCE_GAP_CAUSE=UNPROVEN
AXIA_G07_REAL_MOVING_NAV_SHUTDOWN_ACK=TIMEOUT_40.000372S
AXIA_G07_REAL_MOVING_LOCALIZATION_ACK=NOT_REQUESTED
AXIA_G07_TASK02=BLOCKED_CAUSAL_EVIDENCE
AXIA_G07_TASK03_TRACER_OFF_L2=NOT_RUN
AXIA_G07_TASK04_OWNER_WSL2_L3=NOT_RUN
AXIA_MVP_DEMO_ACCEPTED=HOLD
MAIN_MERGED=false
CERTIFIED_ESTOP=false
```

문서 자체의 신규 Git 커밋에 별도 실제 Gazebo 검증 결과를 부여하지 않는다. **현재 완료한 것은 GitHub 원격 증거 재확인·최초 실패 경계 분류·인계 보고이며, 코드 문제 해결/Owner 최종 인수는 미완료다.**
