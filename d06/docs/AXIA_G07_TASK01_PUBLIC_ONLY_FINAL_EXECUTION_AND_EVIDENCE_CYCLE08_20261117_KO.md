# AXIA G07 Task 01 — Cycle 08 공개 CI 전환·실제 Gazebo 진단·최종 증거 판정

작성일: 2026-11-17 KST.

**최종 판정: Task01 증거 검토 완료 / 첫 CM source gap 원인 미증명(EVIDENCE_EXHAUSTED_HOLD).** Task02 성능수정 차단, Task03 tracer-OFF L2 및 Task04 Owner WSL2 L3 미실행. 이는 사용자 인수 계약의 두 번째 Task01 종료 경로(증명 불가능의 근거 확정)이며 CM120 안정화 성공 또는 인증 E-Stop이 아니다. main 병합 없음.

## 1. 범위·원본 소스

- 공개 CI: silverbjin/axia-robot-safety-ci-public, 브랜치 fix/g07-cm120-task01-clock-firstgap-causality-20261117, [Draft PR #161](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/161).
- 공개 G07 학생용 원본: silverbjin/axia-robot-safety-student, 불변 SHA **6a3047b5aa219687f5fc918e467cea5115d3d482**. 실제 실행 파일 block_B/day07/h01_runtime/scripts/p2_no_goal_smoke_ci.sh 및 G07 기존 Supervisor/Guard/Goal/Lifecycle/Scenario Verifier/Fault Injector 패키지만 재사용. 학생 main 변경 안 함.
- 공개 Docker OCI digest: ghcr.io/silverbjin/axia-g07-runtime@sha256:861ae1df0560f991698d8967193380b1619589ba7770b5e2ca91ea4ef31f0c8e. 실제 CI ROS Jazzy/Nav2 25 package / 5 official SHA256 parity PASS. 원래 Instructor 프로그램의 실행 소스 SHA와는 다르므로 결과 혼합 금지.
- 모든 신규 workflow는 공개 repo 둘만 checkout. **비공개 리포지토리·비밀 토큰·비공개 환경 사용 0회**. ROS2 Jazzy, Gazebo Harmonic, 공식 Nav2, TB3 Waffle. 단일 Goal은 기존 CI-only simulation gate GITHUB_ACTIONS=true, AXIA_P0_SIM_ONLY=1, AXIA_G07_CI_SIM_GOAL_ALLOWED=1, 격리 ROS_DOMAIN_ID/GZ_PARTITION 하에서 원본 실행기로만 발행. Owner TTY 우회나 실제 HW 시연 없음.
- 공식 CM publisher/Observer 최대120ms, Guard150ms, Scan/Odom/Clock300ms, base_shift_correction=true, source_timeout=1.0s, TF tolerance0.02s, STOP0.40m/SLOW0.75m 유지. TTL, Goal 소유권, QoS, 정지 영역, original Nav2 코드 변경 0. 모두 tracer-ON 진단이고 tracer-OFF 출고 결과 아님.
- 민감 raw ROS/TF/LTTng trace, geometry, PID/TID, 원본 bag는 공개 업로드하지 않음. 숫자형 허용목록 JSON, SHA256SUMS와 환경 패리티 JSON만 artifact로 업로드. Artifact ZIP을 다시 다운로드하여 SHA256 independent 재검은 이번 작업에서는 미검증.

## 2. 실제 공개 CI Gazebo 결과 — 런 간 합성 금지

| 실제 GitHub Actions run / 코드 SHA | 실제 첫 안전·타이밍 경계와 주행 | 후속 Native 종료 / 진단 |
|---|---|---|
| [44094357749](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44094357749) / 6d091fec699fc6de5abf3f094548054b2422fbf9 | 공식 G07 실물 Gazebo CLEAR→SLOW→STOP 실제 관측. CM Observer 최대 **136.737250ms >120ms**. Publisher CM RMW source gap은 exporter 실패로 미확인. 로봇 실제 0.2156m, ZERO dwell1.008초, 단일 UUID e399dd3ded54419f84f2711fcbc01385 EXECUTING. Source node 최대59.874ms, Supervisor59.935, Clock101.644, Scan192.859ms. | Navigation manager /get_parameters 서비스 미발견, native ACK 실패, G07 Goal runner rc3. 숫자 증거 exporter 원인 유형 미제공 HOLD. 14-topic bag의 필수 센서·Safety 토픽 실제 기록. Artifact ID **14332413148**. 전체 FAIL. |
| [44096074139](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44096074139) / 5839722655a115e865a91b24bfc94171739baec5 | 동일 공식 주행에서 **CM RMW publisher source gap 141.647057ms**, Observer gap **142.057082ms**, 모두 release FAIL. CLEAR→SLOW→STOP, 이동0.2166m, ZERO dwell1.004초. Clock53.690/Guard83.553/Odom138.095/Scan201.916ms, Supervisor65.631ms. | Goal/Navigation/Localization native ACK PASS, P2_L2_SMOKE_RC=0. 그러나 TF native 최초 함수와 sleep을 연결하는 exporter는 **EXACT_SOURCE_TF_ALLOWLIST_JOIN** 경계에서 실패. Numeric independent source/Observer interval만 보존하고 root cause=false. Artifact ID **14334127173**. 전체 workflow FAIL. |
| [44097553946](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44097553946) / c06e77788238ccfa7fea35f21a10b7a0449b9fce | 새 TF Clock bounded 전처리를 적용. 주행 CLEAR→SLOW→STOP, 이동0.2284m, ZERO dwell1.009초. 이번 CM Observer **최대91.180837ms**, 120ms 최초 CM publisher source gap **NOT REPRODUCED**; Clock102.462/Odom133.227/Scan198.632/Guard57.275ms. | Navigation ACK PASS, Localization **SERVICE_TIMEOUT**. 원본 숫자 exporter 정상 **FIRST_RMW_SOURCE_GAP_NOT_REPRODUCED**, RMW first_gap=null; 후속 TF span을 과거 최초 gap에 소급 결합 금지. Artifact ID **14335121401**. 전체 FAIL. |

첫 런과 마지막 런의 Native 서비스 오류는 주행 이후의 독립 종료 경계이다. 중간 런은 Navigation/Localization ACK 자체가 성공했으므로 세 번의 후속 종료 오류를 동일한 root cause로 묶지 않는다. 기존 원래 최초 gap [44049067368](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44049067368) 129.299071ms, Observer128.391951ms와 9회 실제 libc 10ms sleep (요청90ms, 실측91.416406ms)도 **다른 Instructor 소스 실행**이므로 본 공개 student source 최초 141.647ms와 동일 원인으로 합성할 수 없다.

## 3. 공식 자료 Research

- [geometry2 ROS2 Jazzy tf2_ros Buffer](https://github.com/ros2/geometry2/blob/jazzy/tf2_ros/src/buffer.cpp): canTransform polling에서 TF clock now와 실제 std::this_thread::sleep_for(10ms) 사용 확인. 관측한 실제 sleep 횟수는 TF 함수 경로와 정합하지만 정확한 publisher source epoch↔MONOTONIC first-call overlap 및 TF availability는 아직 미증명.
- [Nav2 Jazzy Collision Monitor source](https://github.com/ros-navigation/navigation2/blob/jazzy/nav2_collision_monitor/src/source.cpp) + [nav2_util](https://github.com/ros-navigation/navigation2/blob/jazzy/nav2_util/src/robot_utils.cpp): base_shift_correction=true일 때 Advanced fixed-frame 조회. 구성 불변.
- [Nav2 Issue #3402](https://github.com/ros-navigation/navigation2/issues/3402) + [merged PR #3412](https://github.com/ros-navigation/navigation2/pull/3412): simple TF는 성능 이득 대신 이동 중 시간 보정 정확도 손실 가능. Rolling/TB3 Gazebo 사례를 Jazzy/Waffle CM120 STOP0.40/SLOW0.75 안전 여유에 그대로 적용하지 않음.
- [Nav2 Jazzy Lifecycle Manager](https://github.com/ros-navigation/navigation2/blob/jazzy/nav2_lifecycle_manager/src/lifecycle_manager.cpp): node_names parameter 및 manager services 존재. [rclcpp NodeOptions](https://github.com/ros2/rclcpp/blob/jazzy/rclcpp/include/rclcpp/node_options.hpp): parameter services 기본 활성. 실제 /get_parameters 미발견과 Localized ACK timeout의 직접 원인은 그래프·세션 추적 부족으로 미확정; CM source root cause와 구분.
- [Linux sched-stats](https://www.kernel.org/doc/html/latest/scheduler/sched-stats.html): 첫 source gap과 정확히 결합된 CM thread runnable wait stats 필요. 과거 sched_schedstats=0/sample1/null delta이므로 Scheduler wait=0 가정 금지.

## 4. 실제 OBSERVE→HYPOTHESIZE→RED→GREEN (공개)

### 4-1. 공개-only 실행 계약

신규 d06/tests/test_g07_task01_public_only_execution_contract.py 5 cases, 공개 student SHA 고정·두 공개 checkout·private secret 미사용·한 번의 격리 Goal·숫자형 SHA256 artifact·tracer-ON HOLD. [RED 44093709665](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44093709665) **4/5 FAIL**, 신규 공개-only workflow 구현 뒤 실제 #440943 정적 5/5 PASS. 첫 중첩 checkout에는 ModuleNotFoundError: d06로 [44094112286](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44094112286) FAIL→최소 PYTHONPATH 수정 SHA 6d091fec... 후 동일 소스 ROS/ZJazzy 사전검증 PASS.

### 4-2. 실제 raw CTF 실패 시 독립 RMW 숫자 보존

최초 공개-only 실제 #440943에서는 exporter 예외를 묻어 첫 RMW interval까지 소실. 기존 adapter d06/scripts/g07_task01_extract_public_gap.py에 고정 오류 stage enum과 기존 MessageInfo consecutive seq RMW source/Observer interval만 fall back 보존. 다른 raw 필드/PID/자세/예외 문자열 유출 없이 root_cause=false. [RED 44095571709](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44095571709): 실패 KeyError failure_stage; [GREEN 44095859876](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44095859876): **38/38 ROS-free PASS** + 원본 sanitized JSON sha256. 수정 코드 SHA **20fec6f0e512822b8bd370a693493aa996335758**. 그 다음 실제 #440960에서 source141.647057ms/Observer142.057082ms를 보존하고 exporter 정확한 최초 실패 단계 EXACT_SOURCE_TF_ALLOWLIST_JOIN까지 좁힘. 단 TF sleep 원인은 계속 UNPROVEN.

### 4-3. 2분 전체 TF Clock raw 초과와 최소 최초 gap window

단일 반증 가설: 전체 TF Clock 로그가 20,000행 이상이어도 최초 Observer interval±200ms 안의 정확한 TF rows만 필요하다. 이미 가지고 있는 d06/scripts/g07_task01_extract_public_gap.py에서 최초 MessageInfo pair의 Observer-MONOTONIC window를 선별하여 불필요한 먼 TF_CLOCK/TF_SLEEP/TF_ADV/TF_AVAIL rows 제거; 그 이후 기존 strict CM PID/TID/handle·순서 및 상한 검증을 그대로 재사용. **이 수정이 #440960의 실제 exporter 실패 원인 전체를 해결했다는 주장은 금지**, 해당 원본 예외 상세 코드 미보존.

- 신규 기존 테스트 d06/tests/test_g07_task01_public_evidence_adapter.py의 **20,001개 실제 형식 TF_CLOCK out-of-first-gap 반례**.
- [RED 44097212608](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44097212608): old exporter PUBLIC_EVIDENCE_EXTRACTION_UNVERIFIED_HOLD, 1 expected failure.
- [GREEN 44097395031](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44097395031): 정확한 source 코드 SHA **70d9cb4f1b970b7cc9d642dbcbeb8c09d7dfabcb**, 원본 증거 SHA256 및 공개 **39/39 L0 PASS**.
- [실제 검증 44097553946](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44097553946): extractor는 정상 정상 source gap 없음 판정했으나 실제 최초 source 위반 미재현으로 해당 가설의 동일 gap TF causality는 미증명. 같은 Goal을 추가 무제한 재시도하지 않음.

## 5. 파일·실제 실행·Git REVIEW

수정된 공개 파일:
- .github/workflows/axia-g07-task01-public-only-one-diagnostic-l2-20261117.yml
- d06/tests/test_g07_task01_public_only_execution_contract.py
- d06/scripts/g07_task01_extract_public_gap.py
- d06/tests/test_g07_task01_public_evidence_adapter.py
- .github/workflows/axia-g07-task01-real-firstgap-polling-bounds-l0-20261117.yml

재사용 및 변경하지 않은 제품 파일: 공개 학생 G07 runtime의 모든 ROS 노드/launch/Guard/Supervisor/official Nav2, 공식 G07 CM YAML, 기존 TF preload library d06/diagnostic/cm_tf_gettransform_preload.cpp (빌드/계측만). 본 Task에 새 서비스 노드/퍼블리셔나 AI 모델 추가 없음.

실제로 공개 Actions에서 실행한 명령:
- python3 -m unittest discover -s ci/d06/tests -p test_g07_task01_public_only_execution_contract.py -v
- python3 -m unittest discover -s ci/d06/tests -p test_g07_task01_tf_zero_timeout_availability.py -v
- python3 -m unittest discover -s ci/d06/tests -p test_g07_task01_public_evidence_adapter.py -v
- cmake -S ci/d06/diagnostic -B /tmp/axia_task01_public_abi -DCMAKE_BUILD_TYPE=RelWithDebInfo
- cmake --build /tmp/axia_task01_public_abi --parallel 2
- timeout --signal=TERM --kill-after=10s 900s bash scripts/p2_no_goal_smoke_ci.sh
- sha256sum first_gap_sanitized.json > SHA256SUMS.txt

별도 공개 검사기 [44097395031](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44097395031) stdout 실제 합계 5+2+6+10+6+5+5 = **39/39 PASS**; actual old numeric artifact sha256sum: OK. 실제 Gazebo 세 런 모두 전체 workflow **FAIL**였으므로 안전 릴리스/Owner WSL2 성공 보고 불가.

Review: 임계값 완화 없음, source SYSTEM과 Observer MONOTONIC을 절대 시계로 혼용하지 않음, TF call duration과 실제 TF wait 원인 구분, per-run student source SHA 고정, raw private 유출 없음, Guard·Scan/Odom/Clock·ACK는 실제 해당 런에서 관찰한 부분만 명시하고 **전체 안정성은 미검증**. 성공한 native 종료와 실패한 소스 gap을 같은 합격으로 묶지 않는다. 원시 BAG/Zip의 SHA256 별도 다운로드 재검 미검증.

## 6. 완료 판정·재개 조건

**Task01을 두 번째 사용자 정의 종료 경로로 조건부 마감한다.** 실물 Gazebo에서 동일 first CM source>120ms 발생을 확보했음에도, 해당 최초 gap에 대응하는 exact native CM PID/TID TF invocation 내 sleep 및 canTransform availability, publisher SYSTEM↔host MONOTONIC 직접 인과와 runnable wait(ns)를 동일 런에서 증명하지 못했다. 수정된 exporter를 검증한 다음 런에서는 first gap 자체가 없었다. 따라서 다음 단계의 성능 옵션이나 CPU scheduler 튜닝을 안전 근거 없이 결정할 수 없다.

향후 근본 원인 해결 작업을 다시 여는 경우, 기존 원시 추출 stage를 정확한 **safe fixed error reason**으로 공개 CI에서 분리하고, 원본 첫 source>120ms를 동일 run에서 재현하는 **새롭고 반증 가능한 실험**만 1회 수행해야 한다. 새로운 성능 튜닝, Goal 무한 반복, 추측성 simple TF, Guard/CM TTL 변경은 금지.

결론:
- TASK01_EVIDENCE_REVIEW=COMPLETE
- TASK01_CLOSURE=EVIDENCE_EXHAUSTED_HOLD
- TASK01_FIRST_SOURCE_GAP=REAL_141.647057MS_RUN_44096074139
- TASK01_DIRECT_TF_VS_SCHEDULER_CAUSALITY=UNPROVEN
- TASK01_PUBLIC_L0=PASS_39_RUN_44097395031
- TASK01_PUBLIC_GAZEBO_ONE_GOAL_RELEASE=FAIL
- TASK02=BLOCKED_CAUSAL_EVIDENCE
- TASK03_TRACER_OFF_L2=NOT_RUN
- TASK04_OWNER_WSL2_L3=NOT_RUN
- CM120_TRACER_OFF_RELEASE=HOLD
- AXIA_G07_PUBLIC_L2_ACCEPTED=false
- AXIA_G07_OWNER_WSL2_L3_ACCEPTED=false
- AXIA_MVP_DEMO_ACCEPTED=HOLD
- MAIN_MERGED=false
- CERTIFIED_ESTOP=false
