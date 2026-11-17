# AXIA G07 Task 01 최종 증거 판정 — 원인 미증명 / 보존 증거 소진에 따른 조건부 종료

- 판정일: **2026-11-17 KST**
- 범위: **Task01 최초 CM RMW publisher source >120ms의 공식 TF sleep 대 OS Scheduler 인과 분리**. Task02 성능 수정, Task03 tracer-OFF 릴리스, Task04 WSL2 L3는 본 판정에 포함하지 않음.
- 판정 용어: **`TASK01_EVIDENCE_REVIEW=COMPLETE`**, **`TASK01_ROOT_CAUSE=UNPROVEN`**, **`TASK01_CLOSURE=EVIDENCE_EXHAUSTED_HOLD`**. 해당 Task는 사용자 정의 완료 조건 중 *“현재 증거와 허용된 계측으로는 증명 불가능하다는 근거를 확정하고 Task02를 차단”* 경로로만 마감한다. **`TASK01_CAUSE_PROVEN`, `CM120_TRACER_OFF_RELEASE=PASS`, `AXIA_MVP_DEMO_ACCEPTED=ACCEPTED`가 아님.**
- 공개 저장소: `silverbjin/axia-robot-safety-ci-public`, 기존 개발 브랜치 `fix/g07-cm120-task01-clock-firstgap-causality-20261117`, Draft [PR #161](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/161). 기존 PR #158 및 S1/S2/C34의 검증 SHA는 **변경·재실행·서로 합성하지 않음**.
- 제품 계약: 공식 ROS 2 Jazzy/Nav2/TB3 Waffle/Gazebo Harmonic, `base_shift_correction=true`, `source_timeout=1.0s`, TF tolerance0.02s, STOP0.40m/SLOW0.75m, CM RMW source/Observer 각각120ms, Guard hard TTL150ms, Scan/Odom/Clock300ms. SW STOP은 **인증된 E-Stop 아님**. main 병합하지 않음.

## 1. 최초 실패 시점, 데이터와 각 경계

| 실제 같은 Moving Goal 실행 | 원본 | 시간/안전 판정 |
|---|---|---|
| [#44049067368](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44049067368), job `133921996670` | **CM RMW SYSTEM source 첫 gap129.299071ms**, 동일 seq+1 Observer MONOTONIC gap128.391951ms | CM120 **FAIL**; same window Supervisor 실제 발행2회·max source 내 upstream gap50.201478ms, 따라서 상류 입력 완전 단절이라고 주장할 수 없음. 같은 run 중 Scan/Guard/Clock/odom 등 다른 채널의 독립 위반은 별도 보존 |
| 동일 첫 Observer pair | Advanced TF 최대 약91.733ms, 공식 libc 10ms sleep **9회, 요청90.000000ms/실제91.416406ms**, sleep wake-up elapsed excess1.416406ms | **TF 실제 polling 존재**. 그러나 정확한 9 sleep이 **동일 TF invocation**에 포함되었는지 원본 공개 자료에 call start/end가 없으며, RMW publisher source gap 시간 자체와 TF 함수 실행시각을 직접 정합했다고 주장할 수 없음. 1.416ms는 sleep 벽시계 초과시간일 뿐 동일 스레드의 scheduler wait 시간 상계가 아님 |
| 동일 run의 CPU 스케줄러 관측 | `AXIA_G07_FIRST_CM_SOURCE_GAP_SCHEDULER_WINDOW` 첫 Observer pair에 scheduler samples **1**, `scheduler_wait_delta_ms=null`, `scheduler_run_delta_ms=null`, `host_clock_step_excluded=false`, `source_gap_clock_domain=RMW_SYSTEM_RELATIVE_ONLY` | **`SCHEDULER_RUNQUEUE=UNAVAILABLE`**. 별도 전구간 CM proc 수치 `wait_sec=0.028793375`는 최초 source pair와 직접 결합되지 않은 집계로, 최초 gap에 28.793ms scheduler wait가 있었다고 역산 금지. `sched_schedstats=0`인 기존 진단에서 scheduler 실제 대기를 0으로 간주하지 않음 |
| 해당 실제 ROS/Jazzy 빌드 로그 | CMake `rmw_fastrtps_cpp: 8.4.4`; `Using RMW implementation 'rmw_fastrtps_cpp' as default` | **빌드의 기본 RMW 확인**. 다만 각각의 원본 publisher에 수신측 CLOCK_REALTIME calibration이 적용됐다는 증명은 아님 |
| [#44059005075](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44059005075), 다른 SHA의 1 Goal | source 최대117.210ms, Observer117.861ms, first gap **미재현** | no first breach; 이번 실행 TF·Clock으로 이전 run의 시간창 인과 보강 금지 |
| [#44072394317](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44072394317), NO_GOAL | 공식 Advanced TF 589회, 실제 0ms TF entry=false→exit=true **478회**, libc sleep 511회, probe max0.460882ms, Nav/Loc ACK | Native TF 가용성 검사와 10ms sleep이 **실제 공식 ROS에서 동작**하는 것은 입증. **NO_GOAL**이므로 Moving 최초 source gap 원인 미증명 |
| [#44073078458](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44073078458), 다른 진단 Moving | first source gap **미재현** (RMW source 최대117.998ms; Observer118.261395ms); exact UUID `0048321280154b189a764c27e7c8736f` CANCELED | CM120 인과 테스트에서는 source 최초 위반이 없어 조건 불충족. 뒤따른 **Navigation Native ACK timeout 40.000372s**는 독립 최초 종료 실패로 [Issue #163](https://github.com/silverbjin/axia-robot-safety-ci-public/issues/163) 추적. C34 다른 SHA의 ACK 성공과 합성 금지 |

**S1 이전 최초 위반** [#44011055816](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44011055816)도 RMW source139.723543ms / Observer123.527663ms / 공식 Advanced TF101.682875ms / thread CPU0.322830ms를 보여주지만, 상세 sleep 원본 없음. S2 [NO_GOAL #44013676608](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44013676608)은 427회 실제 sleep이 다른 실행에 관측된 것임. [Moving #44014107942](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44014107942)는 첫 source breach 자체가 미재현. **서로 다른 실행을 하나의 근본 원인 증거로 합치지 않음**.

## 2. GitHub 원본 보존 수준과 복구 가능성 검증

GitHub Actions artifacts API를 직접 조회한 결과:
- Runs `44011055816`, `44013676608`, `44014107942`: 다운로드 가능한 artifact **각 0개**.
- 실제 첫 source gap `44049067368`: 공개 sanitized timing-only artifact **ID `14313016879`, ZIP 1216B**. 동일 숫자형 JSON을 `d06/evidence/g07_cm120_task01/run_44049067368_first_gap_sanitized.json`과 SHA256SUMS로 commit 및 검증. JSON에는 실제 source/observer gap과 14 sleep 상대 span, 10 TF call **duration 목록만** 존재. `tf_calls.spans`(정확한 per-call start/end), `tf_availability`, `tf_internal_clock`, scheduler per-thread wait **없음**. 최초 source↔MONOTONIC `sender_clock_domain_proven=false`.
- `44059005075`: 공개 timing-only ZIP **ID `14317213107`, 783B**, source>120ms 최초 위반 **없음**. 저장 JSON `first_gap=null`.
- `44073078458`: 공개 availability timing-only ZIP **ID `14323023706`, 644B**, source>120ms 최초 위반 **없음**.
- 기존 개인/비공개 원시 custody의 새 증거 확보를 위해 만들었던 [NO_GOAL 사전검사 #44043200646](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44043200646)와 [#44045232799](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44045232799)는 private remote canary push/readback **실패**: 당시 최소권한 쓰기 credential 미검증. **현재 secret 설치 여부는 이 검토에서 조회하지 않았으므로 미확정**. 사전 원본 보존 검증 없이 새 Goal을 보내는 편법 금지.
- 비공개 Instructor 원본 소스 또는 raw trace/로봇 실측 pose/Gazebo contact 원본은 공개 artifact로 업로드하지 않음. GitHub job logs에는 요약 verdict만 있어 이전 삭제된 raw per-call 이벤트를 역으로 복원할 수 없다.

## 3. 공식 ROS/TF/DDS·커널 근거로 검증한 원인 후보

| 자료 | 정확히 말해주는 것 | AXIA 증거와의 연결 / 판단 |
|---|---|---|
| [geometry2 Jazzy tf2_ros Buffer](https://github.com/ros2/geometry2/blob/jazzy/tf2_ros/src/buffer.cpp) | `canTransform`은 TF clock의 `now()`로 timeout을 측정하며, 실제 루프에서 `std::this_thread::sleep_for(10ms)` 실행 | 동일 Observer pair의 libc sleep9회는 공식 함수 경로와 일치. 하지만 왜 해당 시점 TF를 기다렸는지 / 같은 source gap을 야기했는지 미증명 |
| [Nav2 Jazzy Collision Monitor source.cpp](https://github.com/ros-navigation/navigation2/blob/jazzy/nav2_collision_monitor/src/source.cpp), [nav2_util robot_utils.cpp](https://github.com/ros-navigation/navigation2/blob/jazzy/nav2_util/src/robot_utils.cpp) | `base_shift_correction=true`가 Advanced fixed-frame `lookupTransform` 경로를 사용 | 실제 Advanced ABI/함수·poll 계측으로 경로는 지지. 원본 센서-시각 정합을 손실시킬 Simple TF 옵션 즉시 채택 금지 |
| [Nav2 공식 Issue #3402](https://github.com/ros-navigation/navigation2/issues/3402), [병합 PR #3412](https://github.com/ros-navigation/navigation2/pull/3412) | 기존 Advanced TF 지연 사례와 Simple TF로 성능-정확도 절충 가능 | 2023 Rolling/TB3 Gazebo와 AXIA Jazzy/Harmonic/STOP0.40m 조건 다름. 직접 원인 판정은 보류 |
| [eProsima Fast DDS SampleInfo](https://fast-dds.docs.eprosima.com/en/2.x/fastdds/api_reference/dds_pim/subscriber/sampleinfo.html) 및 [Fast DDS DataWriter](https://fast-dds.docs.eprosima.com/en/2.14.x/fastdds/api_reference/dds_pim/publisher/datawriter.html) | DDS `source_timestamp`는 **DataWriter가 제공**하며, 타임스탬프가 명시 공급되는 경우도 있음 | 수신자 `clock_anchor.wall_minus_mono` 시작/끝 drift 1ns만으로 source publisher **SYSTEM epoch ↔ host MONOTONIC 일치** 자동 증명 불가 |
| [Linux Scheduler Statistics](https://www.kernel.org/doc/html/latest/scheduler/sched-stats.html) | 실제 runnable wait는 일치하는 thread 및 구간의 신뢰 가능한 /proc 수치가 필요 | 첫 gap 단일 sample, null delta. 집계 wait 값을 첫 publisher source 지연의 scheduler 원인으로 주장 금지 |

## 4. OBSERVE → HYPOTHESIZE → RED → GREEN → REVIEW → COMMIT

이 문서는 새로운 기능 개발이나 성능 수정 사이클이 **아닌 증거 판정 완료 기록**이다. 이미 성공한 검사를 재실행하지 않았다. 기존 증거 해석의 fail-closed 결함 두 종류는 같은 현재 개발 브랜치에서 공개 CI로 RED→GREEN을 실제 완료했다.

| 범위 | 실제 RED | 실제 GREEN / commit |
|---|---|---|
| First source breach가 없는데 TF readiness 후보 표시 | [#44083601997](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44083601997) 실패 2 case | [#44083837619](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44083837619), `8a170246551ef936ad9fb55d3d52f47e655cabac`, **L0 36/36 PASS** |
| 같은 CM PID/TID라도 first Observer pair **밖**의 인접 콜백 가용성 오인 | [#44089012960](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44089012960) 실패 2 subcase | [#44089226512](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44089226512), `95b99f58b66ee20ac921d7a09d1d7790f4a0ed9e`, **L0 37/37 PASS**, pinned public JSON `sha256sum: OK` |

- 실제 테스트 명령: `python3 -m unittest discover -s d06/tests -p 'test_g07_task01_tf_zero_timeout_availability.py' -v`, 기존 workflow `.github/workflows/axia-g07-task01-real-firstgap-polling-bounds-l0-20261117.yml`의 7개 테스트 집합+py_compile+실제 공개 SHA256SUMS 검증. **테스트는 GitHub Actions에서 실행; Owner WSL2나 이 문서 작성 시 추가 ROS/Gazebo 실행 없음**.
- 코드 최종 검증 SHA `95b99f58b66ee20ac921d7a09d1d7790f4a0ed9e`; 직전 보고서-only HEAD `b4123380ab15cabbe73eba64932922bd976ebe09`. 이 최종 **문서 커밋의 SHA는 테스트 실행 SHA와 다르므로 L2 성공으로 승격하지 않는다**.
- 수정/검토 파일은 기존 `d06/diagnostic/classify_tf_availability.py`와 `d06/tests/test_g07_task01_tf_zero_timeout_availability.py`에만 한정. 본 판정에서는 **새 code/test/workflow 추가 없음**. Task01 정확한 같은 최초 gap의 TF wait 및 Scheduler 원인을 증명하는 데 필요한 raw 정보를 만들지 않았음.
- REVIEW: 데이터 없음⇒`UNPROVEN`, ROS clock/rmw SYSTEM/observer MONOTONIC 구별, `sched_schedstats=0`⇒runqueue UNAVAILABLE, Goal owner·native ACK·서로 다른 run SHA 합성 금지. 안전 계층 이웃 전달 및 Guard/Scan/odom/Clock 시간 경계의 동적 인수는 **아직 미검증**. 보안상 private 원본/강사 정답 공개 금지.

## 5. Task01 조건부 마감 결정 및 다음 **한 단계**

### 정확한 판정

현재 보존된 원본 자료에 대해 가능한 모든 유효한 인과 연결을 판정하면:

1. **`TF_FUNCTION_SLEEP_OBSERVED=true`** — 실제 공식 Advanced TF 경로가 10ms 단위 libc sleep을 반복한다.
2. **`TF_FUNCTION_ELAPSED_DOMINANT=OBSERVED`** — source gap으로 선택한 first Observer pair의 TF 경로는 수십 ms 장시간 실행 관찰.
3. **`TF_BUFFER_AVAILABILITY_WAIT_PROVEN_FOR_SAME_FIRST_SOURCE_GAP=false`** — same source-gap exact TF invocation + ROS internal Clock + transform availability 기록 부재.
4. **`SCHEDULER_WAIT_PROVEN_FOR_SAME_FIRST_SOURCE_GAP=false`** — 신뢰 가능한 최초 동일 thread runnable interval 부재.
5. **`SOURCE_SYSTEM_TO_HOST_MONOTONIC_ALIGNMENT_PROVEN=false`** — host clock anchor만 존재, sender clock domain readback 부재.
6. **`ROOT_CAUSE_PROVEN=false`** — 어느 한 원인을 안전 변경의 근거로 택할 수 없다.

**Task01의 “현 증거/허용된 계측으로는 인과 증명 불가” 완료 경로를 채택하되, 이는 원인 해결이나 CM120 안정화 완료가 아니다.** 이미 통과한 NO_GOAL/ABI/L0를 반복하거나 의미 없는 신규 analyzer/trace 프레임워크를 만들지 않는다.

### 작업 재개를 위한 유일한 추가 실험 (현 시점 **미실행**)

Task01을 **원인 증명 경로로 다시 열려면** 기존 공개 진단기/공식 runner만 재사용하여:
- **사전** 비공개 raw per-call TF/ROS Clock/프로세스·RMW 인과 증거를 원본 형태로 보존할 수 있는 GitHub Actions private SHA256 remote round-trip **NO_GOAL preflight GREEN** 확인. 공개 저장소에 민감 raw 업로드 금지.
- 그 다음에만 **사용자의 추가 진단 Moving Goal 1회 명시 승인**을 받아 Goal 실행; `source >120ms` 최초 breach가 실제 나타나지 않으면 반복하지 않고 FAIL-CLOSED 종료.
- 나타난다면 source publisher timestamp 제공 경로+clock-domain 확인, 같은 CM PID/TID의 원본 callback, official Advanced TF, 개별 10ms sleep 구간, `canTransform` 가용성, 실제 tf2 Buffer Clock, 가능할 경우 scheduler readback, Scan/TF/Odom/Clock freshness 및 Guard 최초 상태 전이를 **같은 세션**에 결합. `sched_schedstats=0`이면 scheduler 원인은 계속 UNAVAILABLE이지 0ms가 아님.
- 해당 첫 경계가 입증되었을 때만 **Task02 한 가지 안전 영향 검토가 끝난 최소 수정**을 RED→GREEN, 그 뒤 Task03 tracer-OFF 공개 실제 Gazebo L2, Task04 Owner WSL2 L3로 진입.

현재 신원/토큰/새 Goal 승인과 원본 보존 시계열이 검증되지 않았으므로 새 Goal은 **발행하지 않는다**. 기존 공개 시간 데이터와 실제 원본을 합성하지 않는다. 이 Task 종료는 원인 해결 대체물이 아니라 **증거 소진에 따른 작업 차단과 명확한 재개 조건**이다.

```text
AXIA_G07_TASK01_EVIDENCE_REVIEW=COMPLETE
AXIA_G07_TASK01_CLOSURE=EVIDENCE_EXHAUSTED_HOLD
AXIA_G07_TASK01_TF_10MS_POLLING=OBSERVED_REAL
AXIA_G07_TASK01_TF_BUFFER_WAIT_CAUSE=UNPROVEN
AXIA_G07_TASK01_SCHEDULER_RUNQUEUE_CAUSE=UNAVAILABLE
AXIA_G07_TASK01_SENDER_SYSTEM_MONO_JOIN=UNPROVEN
AXIA_G07_TASK01_ROOT_CAUSE_PROVEN=false
AXIA_G07_TASK01_LAST_PUBLIC_L0=PASS_37_44089226512
AXIA_G07_TASK01_NEW_MOVING_GOAL=NOT_RUN
AXIA_G07_TASK02=BLOCKED_CAUSAL_EVIDENCE
AXIA_G07_TASK03_TRACER_OFF=NOT_RUN
AXIA_G07_TASK04_OWNER_WSL2=NOT_RUN
CM120_TRACER_OFF_RELEASE=HOLD
AXIA_G07_PUBLIC_L2_ACCEPTED=false
AXIA_G07_OWNER_WSL2_L3_ACCEPTED=false
AXIA_MVP_DEMO_ACCEPTED=HOLD
MAIN_MERGED=false
CERTIFIED_ESTOP=false
```
