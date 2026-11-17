# AXIA G07 CM120 — S2 최종 작업보고서: 공식 Advanced TF off-CPU 원인 구분

- **기록일:** 2026-11-17 (KST)
- **선행 대화:** `05_P4_AXIA_G07_UNIFIED_MVP_4`
- **작업 목적:** S1에서 확인한 Advanced TF 함수 내부의 101ms 비CPU 경과시간을 추가 성능 튜닝 전에 **스케줄러 실행대기 vs 실제 sleep/블로킹**으로 구분한다.
- **최종 결론:** **진단기 구현·RED/GREEN·실제 NO_GOAL 및 단일 Moving Goal 분석 완료. S1 최초 실패창에서의 지배 원인은 미입증(HOLD).**
- **소스:** Public `silverbjin/axia-robot-safety-ci-public` / `fix/g07-cm120-s2-offcpu-provenance-20261117` / [Draft PR #156](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/156). 실제 시험의 S2 코드 pin `9bcdc5cb92ff4da61efb2eba1d2fd77c30dfff96`; Private Instructor 시험 pin `966886c4627deb2bb3b37111fe336eeee6b9ebb4`.

## 1. 요구사항·불변 조건

이번 S2는 병렬 성능개선 Cycle이 아니라 **첫 실패 원인 분석**이다. 공식 ROS 2 Jazzy Nav2/TB3 Waffle/TF/Collision Monitor, Gazebo Harmonic, 기존 Instructor Supervisor/Guard/Fault Injector, STOP 0.40m / SLOW 0.75m, Scan 및 Command 소유권, 토픽 체인, TF tolerance, `source_timeout`, CPU affinity, 안전 타이머/TTL은 바꾸지 않았다. CI/WSL2용 원본 실행기와 전용 안전 행동 변경 없음. **CM RMW source·Observer 120ms 릴리스 목표, Guard 내부 150ms, Scan/Odom/Clock 300ms** 기준을 완화하지 않는다. 모든 새 LD_PRELOAD 계측은 공인되는 성능 실험이 아닌 CI 시뮬레이션 측정이다.

## 2. S1 실제 실패와 S2 질문

기준: [S1 공식 one-Goal run #44011055816](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44011055816), 실증 CI FAIL.

| 동일한 S1 최초 실패 창의 계측 | 값 | 해석 |
|---|---:|---|
| CM RMW 최초 publisher/source 간격 | **139.723543ms** | 릴리스 목표 120ms 초과 |
| CM Observer 간격 | **123.527663ms** | 별도 120ms 초과 |
| 공식 CM callback elapsed | **102.456878ms** | 첫 source gap과 정확하게 연결 |
| `nav2_util::getTransform` Advanced 함수 elapsed | **101.682875ms** | callback wall의 약 99.24% |
| 동일 스레드 CPU time | **0.322830ms** | CPU가 계속 계산한 101ms 아님 |
| **TF wall − CPU = off-CPU** | **101.360045ms** | 무엇을 기다렸는지는 S1만으로 알 수 없음 |

공식 Jazzy `tf2_ros::Buffer::canTransform` 경로에는 10ms 단위 `sleep_for` 폴링이 존재한다. 단, 함수 이름·경과시간만으로 TF 변환 불가, OS 선점, 잠금/수면 중 무엇이 해당 최초 간격을 유발했는지 단정할 수 없다.

## 3. S2 RED→GREEN 구현·코드 리뷰

| 단계 | 실제 산출물 | 판정 |
|---|---|---|
| RED | S1 진단에 per-thread runqueue/context-switch/sleep 필드가 없다는 5개 S2 회귀 항목으로 결핍 확인. 기준 커밋 `46818d16e4d3deb52ccc56c7ba96bb2108cc5639` | 목적에 맞는 진단 격차 확인 |
| GREEN — 순수 분류 | `d06/diagnostic/classify_tf_non_cpu.py`: counter 불가·비논리적 sleep·미확인 Wait는 **fail closed**, Scheduler/Voluntary/Sleep은 관찰치 수준으로만 분리 | **PASS** |
| GREEN — 원본 함수 계측 | `d06/diagnostic/cm_tf_gettransform_preload.cpp`: 동일 공식 Advanced TF ABI 호출을 원본에 위임하고 전후 `CLOCK_MONOTONIC`, `CLOCK_THREAD_CPUTIME_ID`, per-thread `getrusage`, 조건부 `schedstat`, 중첩 배제 `nanosleep`/ `clock_nanosleep`을 측정 | **PASS** |
| GREEN — 동일 창 결합 | `d06/diagnostic/analyze_first_cm_tf.py`: 기존 LTTng CM subscription/callback PID·TID 및 최초 source gap과 TF interval을 정확히 결합해야만 원인 데이터를 출력 | **PASS (테스트)** |
| L0 정식 확인 | [공개 CI #44013410740](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44013410740): 5 offCPU + 4 exact join + 3 기존 S1 + 3 real sleep = **15 테스트**, 원본 Jazzy ABI 빌드, 실제 C++ `std::this_thread::sleep_for` interposition selftest | **completed/success, NO_GOAL** |

검사 코드: `d06/tests/test_g07_cm120_s2_offcpu_classification.py`, `test_g07_cm120_s2_exact_tf_offcpu_join.py`, `test_g07_cm120_s2_actual_sleep_provenance.py`. 공식 Jazzy TF 함수의 실행 순서·반환값·타임아웃·안전 정책 변경 없이 계측했다.

**커널 기법 한계:** CI 실제 `/proc/sys/kernel/sched_schedstats=0`. `/proc/thread-self/schedstat`의 runqueue nanoseconds는 사용 가능하다고 입증되지 않았다. **`UNAVAILABLE`로 판정하며, 0ms scheduler wait로 보고하지 않는다.** `getrusage` 문맥 전환 횟수는 대기 지속시간 자체를 제공하지 않는다. 이 때문에 커널 튜닝/성능 프로파일러 확장 없이, 실제 TF 내부 libc sleep 관찰을 최소 추가하였다.

## 4. 공식 실제 NO_GOAL L2 — 관찰 가능한 기구 확인

원본: [공개 CI #44013676608](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44013676608) **completed/success** (S2 코드 `9bcdc5cb...`, Instructor `966886c...`).

```text
AXIA_G07_S2_CM_PRELOAD_MAP_OBSERVED=1
actual_tf_call_count=477
tf_nanosleep_calls_total=427
tf_actual_sleep_wall_ms_total=4399.656895
startup_status=SMOKE_READY
goal_sent=false
navigation_ack=true
localization_ack=true
runner_rc=0
AXIA_G07_S2_REAL_CM_LOADER_AND_LOCALIZATION_NO_GOAL_PASS
AXIA_MVP_DEMO_ACCEPTED=HOLD
```

**직접 증명:** 실제 공식 Collision Monitor 프로세스에 계측기가 적재되었고, Advanced TF 함수 실행 구간 안에서 실제 libc 수면이 호출되었다. 4399.656895ms는 **서로 다른 477 TF 호출에 걸친 427회 수면 경과시간의 합**이다. 단일 지연 4399ms, 첫 source gap 내부 지연, 100% TF 버퍼 가용성 대기, 또는 순수 thread deschedule 시간으로 해석할 수 없다. 실제 libc sleep elapsed에는 타이머 만료 후 재스케줄링 지연도 포함될 수 있다.

## 5. S2 단일 Moving Goal L2 — 실제 실패 분석

원본: [공개 CI #44014107942](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44014107942) / Job `133807789938` / **completed/failure**. 테스트 코드 pin `9bcdc5cb92ff4da61efb2eba1d2fd77c30dfff96`, 실제 원본 Instructor `966886c4627deb2bb3b37111fe336eeee6b9ebb4`.

| 측정 또는 판정 | 결과 | 의사결정 |
|---|---|---|
| 최초 CM RMW source **>120ms** 초과창 | **해당 주행에서 비재현** | S1과 동일한 source 실패 구간에 TF/sleep 결합 불가 |
| `FIRST_CM_RMW_SOURCE_PAIR_UNVERIFIED_HOLD` | 실제 진단기 출력 | S2 정확한 원인 분리 미달 |
| CM **Observer 최대** | **121.776640ms** | 120ms 초과, 릴리스 **FAIL** |
| Source/Guard/Scan/Odom/Clock 기간 | Source 91.394802ms, Guard 62.292188ms, Scan 204.252238ms, Odom 121.693707ms, Clock 112.780975ms | 각 관측 채널 값일 뿐 Guard 내부 CM age의 충분조건 아님 |
| 콜백 트레이스 | 원본 이벤트 125,065, 해당 CM callback 2,692, 메타데이터 24 | 과거 100k overflow 우회 확인. 그러나 최초 source 위반창은 없음 |
| 로봇 행동 | CLEAR→SLOW→STOP, 이동 0.1921m, 정지 dwell 1.015s, Nav2 CANCELED | 부분 기능 관측. 모든 안전 게이트 통과 주장 금지 |
| Shutdown | Navigation ACK true (2.64552s), Localization `request_sent=true` 후 **25.000516s ACK 없음** | **`LOCALIZATION_SHUTDOWN_REQUEST_SENT_ACK_TIMEOUT`**, 독립 실패 |
| native Contact0/14-topic 원본·Stop·Guard 통합 인정 | 완결된 원본 결합 증거 미확보 | 시나리오 전체 인수 **HOLD** |

**첫 경계와 2차 경계를 분리:** Observer 121.777ms 초과는 확인되었으나 그것이 S1의 첫 publisher/source 139.724ms와 같은 현상이라는 증거는 없다. Localization 종료 실패는 후속 단계의 독립된 오류이지 앞선 Observer 초과의 원인으로 판정하지 않는다. `NO_FIRST_GAP_SCHEDULER_PROOF`, `C05_CM_CALLBACK_ROOT_CAUSE_UNPROVEN_HOLD`를 그대로 보존한다.

진단 Goal은 허용된 **1회만** 수행했다. S2 워크플로의 임시 release trigger는 실행 후 폐기했으며 추가 Goal은 실행하지 않았다. 원시 trace/임시 파일은 원본 CI cleanup에 따라 제거되었고 이 Goal Run에 공개 다운로드 artifact는 **0건**임을 GitHub API에서 확인했다. 과거의 독립 실행들을 임의로 같은 원본으로 결합하지 않는다.

## 6. 원인 가설과 증명 수준

| 주장 | 판정 | 이유 |
|---|---|---|
| TF 함수에서 101ms 비CPU가 실제 발생했음 | **S1 사실** | 같은 최초 source-gap 창에서 wall/CPU 측정 |
| 실제 공식 TF 경로는 libc sleep을 사용함 | **S2 NO_GOAL 사실** | 원래 CM 프로세스 427회 관찰 |
| S1의 첫 139.724ms gap 대부분이 그 sleep 때문임 | **미입증** | S1은 sleep 계측 없음, S2 Moving은 최초 source gap 비재현 |
| 그 gap에서 runqueue 스케줄러 선점이 주원인임 | **미입증** | schedstats disabled, 동일 first-gap 정량 수치 없음 |
| Guard150/Scan300·CM120 안전 릴리스 통과 | **실패/HOLD** | Observer121.777ms 및 lifecycle ACK 실패, 통합 증거 불완전 |
| 튜닝/매개변수 완화가 근거에 의해 정당화됨 | **아니오** | 지배 원인과 안전한 교정이 확정되지 않음 |

비용을 키우는 무제한 반복 Goal, 커널 sysctl 변경, BPF/perf/ptrace 계측 확장, 공식 TF 대기 로직 수정, CM source_timeout/TTL 변경, CPU-affinity 성능 실험은 **S2 범위 밖**이므로 진행하지 않았다.

## 7. S2 완료 범위·잔여 결정·교육 활용

**완료한 것:** S1 실제 첫 실패 보존 → S2 분류기 RED→GREEN(15/15) → 원본 Jazzy C++ ABI/real sleep 경로 확인 → 공식 NO_GOAL L2 PASS → 단일 Moving Goal FAIL 증거 확보 → 독립 원인·실패 경계 분류 → 개발 보고 및 후속 대화 인계.

**남은 것을 S2 성공으로 가장하지 않는다:** 최초 gap의 동일 실행 sleep/runqueue 분해, kernel scheduling 소요시간, TF wait의 우세 인과성, CM120 tracer-OFF release 측정, Owner WSL2 현장 인수, Localization ACK 원인 해결. 이는 별도의 작업 승인·실험 설계가 필요한 **미착수 문제**다.

차기 선택은 읽기 전용 원본 복기 후에 결정한다. 추가 계측이 필요하다면 **동일 first-gap 창, 동일 CM PID/TID, 원본 RTM/ROS clock 기준, sleep과 scheduler 수치를 동시에 측정할 수 있는 비침습적 방법**이 전제다. 첫 source gap이 없는 실행에서는 `CAUSE_UNPROVEN`으로 종료한다. Lifecycle ACK는 별도 이슈로 분리한다. 성능 튜닝 Gate C나 tracer-OFF Gate D를 자동 개시하지 않는다.

**교육용 핵심:** 측정한 **경과시간 ≠ CPU 실행시간 ≠ 대기 원인의 증명**이며, 동일 현상을 다른 실행에서 관측한 사실만으로 공통 인과관계를 확정할 수 없다. RED 테스트·실제 NO_GOAL의 관측 가능성·실제 Goal 실패·보수적 판정을 분리 기록한다.

## 8. 최종 판정과 참고 자료

```text
AXIA_G07_S2_DIAGNOSTIC_IMPLEMENTED=true
AXIA_G07_S2_L0=PASS_15_TESTS_AND_JAZZY_ABI
AXIA_G07_S2_REAL_NO_GOAL=SUCCESS_SLEEP_427_OF_TF_477
AXIA_G07_S2_REAL_MOVING_GOAL=EXECUTED_ONCE_FAILURE
AXIA_G07_S2_SOURCE_FIRST_GAP_MATCH=NOT_REPRODUCED
AXIA_G07_S2_OBSERVER_MAX_GAP_MS=121.776640
AXIA_G07_S2_LOCALIZATION_SHUTDOWN=ACK_TIMEOUT_25S
AXIA_G07_S2_SCHEDSTAT_RUNQUEUE=UNAVAILABLE
AXIA_G07_S2_FIRST_SOURCE_GAP_SLEEP_VS_SCHEDULER=UNPROVEN
AXIA_G07_GATE_C=NOT_STARTED
AXIA_G07_GATE_D=NOT_STARTED
AXIA_G07_CM120_RELEASE=HOLD
AXIA_MVP_DEMO_ACCEPTED=HOLD
OWNER_WSL2_L3=NOT_RUN
MAIN_MERGED=false
STUDENT_RELEASE=false
CERTIFIED_ESTOP=false
```

- [S1 원본 실제 증거](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44011055816)
- [S2 L0 실제 성공](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44013410740)
- [S2 공식 NO_GOAL 실증](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44013676608)
- [S2 실제 단일 Goal 실패](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44014107942)
- [S2 상세 중간·실행 증거 보고](https://github.com/silverbjin/axia-robot-safety-ci-public/blob/fix/g07-cm120-s2-offcpu-provenance-20261117/d06/docs/AXIA_G07_CM120_S2_OFFCPU_PROVENANCE_PROGRESS_20261117_KO.md)
- [Linux kernel schedstats](https://www.kernel.org/doc/html/latest/scheduler/sched-stats.html), [Linux getrusage(2)](https://man7.org/linux/man-pages/man2/getrusage.2.html), [공식 Jazzy tf2 buffer 구현](https://github.com/ros2/geometry2/blob/jazzy/tf2_ros/src/buffer.cpp).

**최종 S2 의사결정:** **작업보고 COMPLETE / 결함 원인 UNPROVEN / 릴리스 HOLD / Draft PR 유지 / 기존 원본을 보존하고 추가 Goal 반복 중단**.
