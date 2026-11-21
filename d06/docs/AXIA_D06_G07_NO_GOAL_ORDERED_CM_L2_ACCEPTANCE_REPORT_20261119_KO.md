# AXIA D06/G07 — NO_GOAL 공식 Nav2 순서화 종료·Collision Monitor 자식 exit0 실제 L2 인수 보고서

- 작성: 2026-11-19
- 목적: 강사 WSL2 NVIDIA NO_GOAL 동일 계측 재시도 전, 공개 CI에서 **종료 경계만** 재현·수정·검증
- 공개 CI: `silverbjin/axia-robot-safety-ci-public`, PR #177 `fix/d06-wslg-lidar-vs-rtf-ci-20261118`
- 학생 런타임: `silverbjin/axia-robot-safety-student`, PR #62 `fix/g07-nogoal-ordered-cm-shutdown-20261119`
- NO_GOAL source pin `835a5285c49300a8d9943d2e19d0c07f3fa06901`, 원본 대비 수정된 script blob `5a4a97078aacc7f5b382d1c2ebdcdee82d8f09e1`
- 확인 대상: Nav2 공식 lifecycle ACK+launch child process exit0, 센서 결과는 동일 세션에서 별도 HOLD. Moving/Guard timing 최종 인수 아님.

## 1. 현장 증거·최초 경계

### 두 개의 물리 실패를 분리
- 원본 강사 NVIDIA UCMOonHr SHA256 `4d374b1caf58ffe113dcecffd315a84356834cd4c8bac2a3143251ae03d4ed3e`.
- Gazebo native /scan 첫 동일 source timestamp 쌍 Gap **314.467ms**, ROS /scan 312.642ms, ROS /safety/scan 322.424ms. Scan TTL **300ms FAIL**. 동일 native /clock 구간 sim0.135s/wall0.339038s, RTF 약0.398. 전체 RTF 평균0.873921로 순간 저하를 가려서는 안 된다.
- `launch.log` 429행 **collision_monitor exit code -11**, `P2_L2_FORCED_TEARDOWN`; 초기 WSL2에는 순서화 Nav2 shutdown 이전에 launch-wide SIGINT 발생. SIGINT과 CM의 crash 인과성은 stack 증거가 없어 **가설**.
- 강사에 재진단을 요구하기 전에, 같은 공식 Nav2/Gazebo 런타임의 공개 CI에서 가능한 가설을 검증.

## 2. 최소 구현

- Student `block_B/day07/h01_runtime/scripts/p2_no_goal_smoke_ci.sh`에 opt-in `AXIA_G07_NO_GOAL_ORDERED_SHUTDOWN=1` 추가.
- 필수 기존 NO_GOAL guard `AXIA_G07_OWNER_SENSOR_TRUTH_NO_GOAL=1`와 함께만 사용. 학생 기본 실습·기존 G07 Goal 경로는 변경하지 않음.
- **기존** `tools/p2_g07_ordered_shutdown.py`로 Navigation Lifecycle Manager shutdown ACK → Localization Lifecycle Manager shutdown ACK. 그 뒤 launch process SIGINT. **기존** `tools/p2_g07_owner_shutdown_audit.py`로 실제 collision_monitor child exit0 확인; `P2_L2_GRACEFUL_TEARDOWN` 마커 단독으로는 CLEAN 금지.
- 센서 probe가 Scan300 위반으로 rc3이어도 순서화 shutdown 수행. CM exit0이더라도 rc3 유지(진단/안전 분리).
- OS 프로세스 종료 최대 26초 유예는 Scan300/CM120/Guard150 safety TTL 변경이 아님.
- 새로운 로봇 제어, Global Planner, CM/Supervisor 내부 수정 및 Goal/cmd_vel/fault-injection 없음.

## 3. RED → GREEN → REFACTOR → REVIEW → COMMIT

1. **RED 계약**: [#44443045828](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44443045828), SHA `54396dc228b383f19fd0949af46af7baf0059dba`. 기존 NO_GOAL에는 lifecycle-before-SIGINT 및 CM child exit0 감사 없음. 최초 실패를 테스트로 등록.
2. **GREEN L0**: [#44443348889](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44443348889), SHA `74403eca112023643e15f29487115bd47bff9099`. 학생 새 SHA pin과 기존 hard TTL/Goal denial 계약 통과.
3. **최초 REAL L2 CI 오류**: [#44443519321](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44443519321), L2 이전 계약 테스트가 `ci/student`를 찾아 FileNotFoundError. 실제 Actions checkout은 형제 `ci/` + `student/`. 본 오류는 Gazebo crash가 아닌 **CI 경로 계약 결함**.
4. **REFACTOR**: L0와 container L2 두 레이아웃만 지원하도록 테스트 경로 최소 수정. 동일 성공 증거 반복 없이 **실제 Gazebo 검사**로 진행.
5. **GREEN 실제 L2**: [#44443813171](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44443813171), commit `bc4f17bc340744ead0593581ab0cd4909318c0d8`, L2 official Nav2/Gazebo Harmonic + Xvfb Gazebo/RViz 1개씩. 실제 출력:

```text
AXIA_D06_G07_NATIVE_SHUTDOWN_SMOKE_RC=3 RVIZ=1 GAZEBO=1
AXIA_D06_L2_FIRST_SENSOR_STATUS=NO_GOAL_SENSOR_UNSAFE_HOLD reasons=['RAW_RECEIPT_TTL_300MS_BLOCKED']
AXIA_D06_L2_NAV2_SHUTDOWN=NAV2_LIFECYCLE_SHUTDOWN_ACK nav_ack=True loc_ack=True
AXIA_D06_L2_CM_PROCESS_AUDIT=SHUTDOWN_CLEAN_CANDIDATE cm_exit_code=0
AXIA_D06_L2_TEARDOWN=P2_L2_GRACEFUL_TEARDOWN
AXIA_D06_G07_ACTUAL_NAV2_CM_CHILD_EXIT0_L2_PASS_NO_GOAL_SENSOR_TTL_INDEPENDENT
```

6. **증거 보존**: [L2 artifact #14491434864](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44443813171/artifacts/14491434864), 원본 launch/CM audit/Nav2 ACK/teardown/sensor report. 뒤의 제한적인 후보 판정을 위한 파일을 임의로 재생성하지 않음.
7. **정확한 증거 게이트 강화**: `d06/scripts/axia_d06_g07_wslg_gpu_rtf_compare_once.sh`의 `collect_and_package`는 원본 TAR SHA256 검증 후 `native_nav2_ordered_shutdown.json`, `native_cm_shutdown_audit.json`, `native_nav2_ordered_shutdown.log`를 경량 포함. 원본 launch에 CM exit -11이 있으면 **감사 JSON이 clean을 주장해도 실패**. 반대로 CM native exit0을 확인했지만 Scan TTL rc3인 경우에는 `NO_GOAL CM clean candidate`만 기록, 전체 acceptance 불가.
8. **검증**: 계약용 새 RED [#44444431330](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44444431330)와 복합 거짓 CLEAN fixture 발견 [#44444551644](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44444551644) 이후 계약 정정. GREEN [#44444782607](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44444782607), **L0 44/44 PASS**. 이는 실제 L2 결과와 별개 범위.

## 4. 공식 문서·GitHub Issue와 한계

- 공식 Nav2 Lifecycle Manager는 managed node들을 순서대로 시작하고 종료 시 역순 전이를 관리함. 공식 문서: https://docs.nav2.org/jazzy/configuration_and_development/configuration_guide/core_servers/configuring_lifecycle_manager/
- Nav2 Jazzy lifecycle code source: https://api.nav2.org/nav2-jazzy/html/lifecycle__manager_8cpp_source.html
- 독립된 다른 구성(composition)에서 shutdown segfault 이슈 #6690도 존재하지만 이번 단일 CM 실행의 원인으로 단정하지 않음: https://github.com/ros-navigation/navigation2/issues/6690
- 현재 CM exit -11은 **공개 CI의 동일한 source/환경에서 재현되지 않고 exit0로 개선**. 강사 WSLg NVIDIA에서 실제 종료 안정성은 아직 미검증.
- **Raw Scan TTL300ms는 실제 L2에서도 FAIL**. 따라서 종료 L2 성공을 전체 기능 L2/Goal 인수로 승격 금지. 원인 경계: native Gazebo short RTF slowdown 현장 증거; 장시간/반복 시연 안정성 미검증.
- Guard150ms·CM120ms의 동작 구간, Moving Goal 및 Stop/Cancel은 이번 NO_GOAL scope 미검증. 기존 G07 Task04 성공 L2 결과는 별도 이력으로 보존.
- `D06_GAZEBO_LIVE_RELEASE=HOLD`, `AXIA_MVP_DEMO_ACCEPTED=HOLD`, `CERTIFIED_ESTOP=false`, `MAIN_MERGED=false`.

## 5. 강사 재진단 출고 조건

- 본 보고서 포함 최종 PUBLIC L0 HEAD GREEN 후만 `--nvidia-causal` **1회**, NVIDIA WSLg/Gazebo+RViz NO_GOAL 모드 배포.
- 같은 세션에서 native Gazebo LaserScan, ROS Raw/Safety, Clock 짧은 구간, Nav2 ACK, CM 실제 child exit 및 원본 SHA256을 **자동 수집해 단일 작은 TAR+SHA256** 생성.
- 여전히 Scan300ms 위반이나 CM/Gazebo `-11`가 있으면 즉시 HOLD 및 기존 실패 근거로 재현 가능한 CI 회귀를 먼저 추가. 원인 파악 없이 현장 반복 실행 금지.
- Main 병합 및 Moving Goal 허가는 강사의 별도 승인 전 수행하지 않음.
