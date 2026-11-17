# AXIA G07 CM120 — Task 01 후속 실행: 공식 Jazzy TF clock/10ms sleep 근거 및 NO_GOAL 증거 회수 판정

> 2026-11-17 KST · 상태: **READ-ONLY OFFICIAL SOURCE/PR + HISTORIC CI EVIDENCE REVIEW COMPLETE** · 실제 신규 ROS/Goal/WSL2 실행 **없음** · `CM120_TRACER_OFF_RELEASE=HOLD`
>
> 이 문서는 성능 수정 제안서가 아니라 **Task 01에서 새 Moving Goal 승인 없이 가능한 근거 수집을 수행하고, 어디서 차단되는지를 확인한 실행 보고서**다. 사용자 허가 없이 진단 Goal을 추가 실행하지 않는다.

## 1. 원격 기준선 및 증거 신원 재확인

| 대상 | 지금 확인한 ref 또는 실제 실행 소스 | 무결성 범위 |
|---|---|---|
| Task01 공개 PR [#158](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/158) | `fix/g07-cm120-task01-first-gap-tf-overlap-20261117`, 재조회 시작 HEAD `c32a8a1e842814415c4f467b8ad9d3f6429ac182`, Draft/open/unmerged | 새로운 진단기 시간영역 가드; 본 문서가 추가되면 HEAD 갱신 |
| S2 공개 PR [#156](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/156) | branch HEAD `b32c6be7a4205b81ae04a8d68b5cfaec619a1f2b`; Draft/open/unmerged | S1/S2 이전 진단과 Task01의 부모 |
| C34 private [#208](https://github.com/silverbjin/axia-robot-safety-instructor/pull/208) | private HEAD `d4afbc9ed14b86ff080c4dd9522f6ba7e982b83a`; 실제 C34 L2 테스트한 코드 `49f38d7912bf8930a331577090522ccf52337fba`; Draft/open/unmerged | Native Goal terminal→Navigation/Localization ACK 검증. **CM120 결과 아님** |
| Original private instructor | S1/S2 실제 Goal 소스 `966886c4627deb2bb3b37111fe336eeee6b9ebb4` | C34 코드와 같다고 간주 금지 |

- **공개 CI L0 성공 원본:** [#44036795558](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44036795558), workflow run HEAD `4c9575403d06732a54235aada1abfdfa26be5716`, `completed/success`, 4+4+3+3 = **14/14** 순수 회귀 및 `py_compile` (ROS/Gazebo 미실행).
- 기존 기대 RED: [#44035728070](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44035728070), `FAILED(failures=1,errors=2)`, TF가 source-gap-selected **Observer** 창 밖에서 끝나도 callback이 겹치면 TF 지배처럼 분류된 문제. 해당 코드 결함은 Task01 L0에서 수정됨.
- **S1 실제 diagnostic Moving Goal:** [#44011055816](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44011055816), workflow `e684c1f6f46f0d5462dce8e93891a909af090176`, `completed/failure`. 같은 콜백에 TF wall101.682875ms/CPU0.322830ms, first RMW source139.723543ms, Observer123.527663ms. 이 숫자들은 **첫 RMW source 발행 시각과 TF 함수의 같은 clock absolute interval에 대한 완전한 증명이 아니다**.
- **S2 공식 NO_GOAL:** [#44013676608](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44013676608), workflow `65769ad477d61215e925005dc2d9fbf0ffd7d0a1`, `completed/success`; Advanced TF 호출477, libc sleep427, 누적 sleep4399.656895ms. 이 합계를 첫 source gap에 대입 금지.
- **S2 Moving Goal:** [#44014107942](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44014107942), workflow `fe57ee49edcde2b7a03080177b8148f917486cf2`, `completed/failure`; **최초 RMW source>120ms pair 미재현**, Observer121.776640ms >120ms, Localization shutdown request ACK timeout25.000516초. 단일 원인으로 묶지 말 것.
- **C34 독립 실제 Gazebo L2:** [#44030235323](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44030235323), `completed/success`, 공개 workflow `f26342cf72dddbb7d15ddfaf393372049d0c471d`. 기존 150/300ms + ACK 결과만 인정.

## 2. 이번에 **직접 재검토**한 공식 Jazzy 원본과 결정적 조건부 가설

### A. 공식 Nav2의 실제 TF 호출 체인

`ros-navigation/navigation2` **jazzy branch**:

1. [collision_monitor_node.cpp](https://github.com/ros-navigation/navigation2/blob/jazzy/nav2_collision_monitor/src/collision_monitor_node.cpp) 는 TF Buffer를 **`std::make_shared<tf2_ros::Buffer>(this->get_clock())`** 로 만든다(해당 branch 소스 52행). 이후 cmdVelInCallbackStamped → process.
2. [source.cpp](https://github.com/ros-navigation/navigation2/blob/jazzy/nav2_collision_monitor/src/source.cpp) 135~153행, `base_shift_correction=true` 이면 sensor stamp → current time → fixed frame을 사용하는 advanced `nav2_util::getTransform` 경로.
3. [nav2_util robot_utils.cpp](https://github.com/ros-navigation/navigation2/blob/jazzy/nav2_util/src/robot_utils.cpp) 124~140행의 advanced 함수는 `tf_buffer->lookupTransform(target_frame,target_time,source_frame,source_time,fixed_frame,transform_tolerance)`를 사용한다.
4. [geometry2 jazzy tf2_ros/src/buffer.cpp](https://github.com/ros2/geometry2/blob/jazzy/tf2_ros/src/buffer.cpp) 138~165행은 advanced `Buffer::canTransform` 안에서 **`clock_->now()`로 변환 대기 timeout을 판단하고, 반복 사이에 `std::this_thread::sleep_for(10ms)`를 사용한다**.

**이번에 구체화한 단일 조건부 가설 H1:**
`use_sim_time`이 실제 CM 실행 프로세스에서 켜져 있고 TF Buffer가 노드 clock을 사용한다면, Gazebo `/clock` 진행·TF availability와 호스트 스레드 실제 sleep/wakeup 시간이 달라질 때 advanced TF 함수 **벽시계 지연**이 `transform_tolerance=0.02s`보다 길게 관측될 가능성이 있다. 실제 S1의 TF wall101.683ms/CPU0.323ms은 이러한 형태와 **양립**한다. 그러나 S1 첫 source gap의 실제 TF 폴링 횟수, `/clock` 시각창 및 스케줄러 wakeup은 원시 기록 부재로 확인되지 않았다.

- **H1의 반증 기준:** 해당 TF 호출과 같은 첫 source-gap 이벤트에서 `clock_->now()`가 설정 timeout 안에 정상 진행하고, 실제 TF availability wait/sleep이 매우 짧으며, **runqueue wait/receiver/exec queue 지연이 주된 공백**임이 증명되면 H1 기각.
- **H1의 진입 조건:** 정확한 installed Jazzy binary/overlays의 `use_sim_time`, TF Buffer clock type, actual `/clock` stamps/receives 및 TF function **개별** sleep/wakeup 시각을 같은 실제 run과 같은 clock domain으로 결합. 이 조건 충족 이전에는 `H1_PROVEN=false`.
- `clock_->now()`는 버퍼에 주입된 clock이고 무조건 ROS_SIM_TIME이라고 단정할 수 없다. 현재 이번 소스 조회는 Jazzy branch이며, 사용자가 설치한 **패키지 binary와 byte-exact 동일 SHA**를 검증한 것은 아니다.
- [Nav2 Issue #3402](https://github.com/ros-navigation/navigation2/issues/3402) 는 advanced TF 조회에서 fixed-frame transform 대기·지연 사례, [PR #3412](https://github.com/ros-navigation/navigation2/pull/3412)는 simple/advanced 옵션을 성능·좌표 정확도 절충으로 제공한다. **AXIA 원인 확정이나 `base_shift_correction=false` 변경 승인은 아님**.
- [Nav2 Issue #4863](https://github.com/ros-navigation/navigation2/issues/4863)은 timestamp mismatch 논의로, 다른 하드웨어의 문제이며 AXIA CM120과 동일 원인이라고 취급하지 않는다.
- [Linux schedstats](https://www.kernel.org/doc/html/latest/scheduler/sched-stats.html)와 [getrusage(2)](https://man7.org/linux/man-pages/man2/getrusage.2.html): per-thread runqueue time은 실제 활성화와 유효성을 확인해야 하고, `ru_nvcsw/ru_nivcsw`는 전환 **횟수**이지 sleep/선점 **시간**이 아니다. 기존 공개 S2 runner `sched_schedstats=0`; 없는 수치는 0ms로 승격 금지.

## 3. 기존 증거 보존 가능성 검수 (추가 Goal 없음)

**공개 GitHub Actions API를 지금 읽기 전용으로 재조회했다.**

- S1 #44011055816: artifacts **0**
- S2 NO_GOAL #44013676608: artifacts **0**
- S2 Moving #44014107942: artifacts **0**
- C34 #44030235323: artifacts **0** (성공 여부는 원래 로그로만 판단)
- Task01 L0 #44036795558: artifacts **0** (pure-test output만 로그에 보존)

기존 S1/S2 Moving job 로그에서 `TF_ADV pid=<...> mono_start_ns=<...>` 형태의 **개별 원시 행은 확인되지 않았고**, `AXIA_G07_CM120_GATE_B_REAL_TF_CALLBACK_TIME` 등의 집계 요약만 확인된다.

S2의 이전 public 진단 workflow `.github/workflows/axia-g07-cm120-s2-one-diagnostic-moving-l2.yml`는 private `actual_ros_events.jsonl`, `/tmp/axia_g07_cm120_tf_diag.log`, LTTng trace를 사용한 뒤 마지막 **`Delete all Instructor source and raw ROS / Gazebo evidence`** 절에서 경로를 삭제하며, 별도의 검증된 private 원본 업로드 영수증/다운로드 artifact는 현재 확인되지 않는다. GitHub 워크플로의 원본 삭제는 정상 비공개 관리 동작일 수 있으나, 당시 S1 첫 실패를 재정렬할 원시 기록이 현재 접근 가능한 곳에 남아 있다고 **주장할 수 없다**.

사용자의 연결된 Google Drive를 표제 검색으로 제한 확인: `44011055816`, `44014107942`, `axia_g07_cm120_tf_diag`, `cm120` 검색에 직접 매칭하는 보존 파일 없음. 일반 `G07` 검색에서 진단 raw와 식별 가능한 매칭은 확인되지 않음. **이는 다른 외부 저장소나 Owner WSL2 로컬에 파일이 없다는 증명이 아님.** 현재 연결에서 복구 가능한 raw 증거 `NOT_FOUND_IN_CHECKED_SURFACES`.

**결론:** 기존 S1/S2의 같은 최초 source violation에서 개별 TF `nanosleep` 시각+runqueue nanos와 sender-time anchor를 다시 계산할 수 있는 원시 행이 확보되지 않았다. 새로운 단정/가짜 데이터 생성 금지.

## 4. 무엇을 더 수행했으며, 무엇을 실행하지 않았는가

### 이번 turn에 수행한 명령/도구에 상응하는 검사

- GitHub API: `GET /repos/silverbjin/axia-robot-safety-ci-public/git/ref/heads/fix/g07-cm120-task01-first-gap-tf-overlap-20261117` 및 S2 parent branch.
- GitHub PR: public `#158`, `#156`, private Instructor `#208` 정확한 HEAD·base·draft 상태.
- GitHub Actions: `GET /repos/silverbjin/axia-robot-safety-ci-public/actions/runs/{44011055816,44013676608,44014107942,44030235323,44036795558}`, 각 `artifacts` 조회.
- Github sealed original S1/S2 job 로그에서 JSON 원시 표본 존재 여부 확인, historical data facts 재검토.
- 공식 Jazzy 소스: geometry2/Navigation2 저장소의 위 C++ 파일 실제 조회, Issue #3402/PR #3412/Issue #4863 공개 근거 확인.
- 연결된 Drive의 *정확한 Run ID 및 진단 파일명* 검색, match 여부 조회.

### 의도적으로 실행하지 않음

- 이미 완료한 14개 L0 unit 테스트를 같은 SHA에서 다시 실행하지 않음. [원본 CI GREEN](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44036795558) 그대로 인용.
- 신규 Moving Goal 미발행, 새로운 Jazzy/Gazebo L2 및 Owner WSL2 L3 미실행.
- 공식 Nav2/CM/TF2 소스 변경, ROS /clock 발행, TF/CPU 설정 조정, `base_shift_correction` 변경, `source_timeout` 변경, safety TTL 완화 없음.
- Private Instructor/Student/main 병합 없음. C34 shutdown gate 재개발 없음.

## 5. 다음 한 번의 최소 실험은 무엇이어야 하는가? (아직 허가 전, 실행 금지)

현재 H1은 실제 진단 가능성이 높지만 **추가 Moving Goal을 별도 승인받지 못했다**. 그대로 Goal을 발행하지 않는다.

**향후 별도 승인 시에도 먼저 NO_GOAL/L0에서** 다음 다섯 경계를 fail-closed 검증해야 한다.

1. 기존 bounded official TF shim의 원본 ABI/CM process-map readback, C05 exact callback pointer, ROS/TF 정상 시작과 Goal 권한 확인. 이미 통과한 동일 테스트는 SHA 동일 시 원본 증거 재사용.
2. **원본 증거 private custody 사전검사**: 저장 디렉터리/권한, 승인된 비공개 목적지, 최소 canary 전송·readback SHA256, 실패하면 Goal을 차단; private TF/ROS raw를 공개 Actions artifact로 배포하지 않음.
3. 현재 S2 원래 `TF_ADV` 한 호출의 `sleep_ns` 합계만 기록한다. **sleep의 개별 시작/끝 시각**과 sleep 반환 후 실행재개 사이의 관계를 구분할 수 있는 최소 진단 계측이 사전에 정적/NO_GOAL로 검증돼야 한다. 개별 sleep wall도 kernel preemption을 포함할 수 있으므로 TF buffer wait이 자동 증명되지는 않는다.
4. 단일 원본에서 `rmw_source_ns` source publisher SYSTEM, RMW received SYSTEM, observer MONOTONIC 및 공식 CM callback/TF MONOTONIC 간 **시계영역·sender host/offset/drift**를 결합하는 계약을 검증. `use_sim_time`과 실제 `/clock` 진행/TF availability는 별도 clock으로 기록.
5. `sched_schedstats=0`이면 정확한 runqueue 대기를 측정 불가능으로 판정하고, **그 불확실성으로도 같은 첫-gap에서 가설을 반증할 수 있는지** 목표를 재설정한다. 커널 계측 권한·환경을 임의로 변경하지 않는다.

이 다섯 검사가 GREEN이고 새 증거를 제공할 실험임이 확인될 때만, **추가 단일 Moving 진단 Goal**에 대한 명시적 사용자 승인을 얻어 새 source SHA로 한 번 수행한다. First source gap이 다시 재현되지 않으면 `CAUSE_UNPROVEN` 그대로 종료, 더 이상 동일 조건 재주행하지 않음. Tracer-ON 결과로 tracer-OFF 릴리스 PASS 금지.

## 6. Task 01~04 게이트 판정

| Task | 실제 완료/차단 | 후속 착수 규칙 |
|---|---|---|
| **Task01** | 기존 callback/observer 시간창 guard RED→GREEN **L0 PASS**. 공식 Jazzy 코드·S1/S2/CI·Drive read-only 조사 **COMPLETE**. 그러나 첫 RMW source gap의 TF sleep vs scheduler **CAUSE_UNPROVEN** | 기존 raw 복구 또는 승인받은 최소 source-locked 진단 1회에서 동일 첫 경계·시계축·TF/sleep+runqueue 확보 |
| **Task02** | **NOT_STARTED_CAUSE_UNPROVEN** | 원인 증명 후 단일 수정과 공개 회귀 RED→GREEN |
| **Task03** | **NOT_STARTED_TRACER_OFF** | Task02 GREEN 및 CM source+Observer <=120, Guard150/ScanOdomClock300, S02/Goal UUID/Native ACK/CM exit0/14topic 동일-run 증거 |
| **Task04** | **NOT_RUN_OWNER_WSL2** | Task03 동일 source 실제 L2 통과 후 수동 Owner TTY 승인; 현장 실행 없으면 PASS 금지 |

**이번 보고서는 신규 기능 개발이나 성능 릴리스 성과가 아니다.** 추가 권한 없이 할 수 있는 Task01 증거 복기와 공식 코드 가설 검토를 완료해 차단 사유를 구체화했다. 실패를 성공으로 승격하지 않았다.

```text
AXIA_G07_TASK01_OFFICIAL_JAZZY_CLOCK_POLL_CODE=SOURCE_CONFIRMED
AXIA_G07_TASK01_H1_SIM_CLOCK_VS_10MS_SLEEP=HYPOTHESIS_NOT_PROVEN
AXIA_G07_TASK01_RAW_SOURCE_SLEEP_SCHED_SAME_RUN=NOT_RECOVERED
AXIA_G07_TASK01_L0_REGRESSION=PASS_14_EXISTING_RUN
AXIA_G07_TASK01_CAUSE=UNPROVEN
AXIA_G07_TASK02=BLOCKED_CAUSE_UNPROVEN
AXIA_G07_TASK03_TRACER_OFF=NOT_STARTED
AXIA_G07_TASK04_OWNER_WSL2=NOT_RUN
AXIA_G07_CM120_RELEASE=HOLD
AXIA_MVP_DEMO_ACCEPTED=HOLD
CERTIFIED_ESTOP=false
MAIN_MERGED=false
```
