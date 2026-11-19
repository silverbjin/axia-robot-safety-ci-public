# AXIA D06/G07 — r6YhIvPx Scan300·Gazebo SIGSEGV 조사 및 공개 통합 L2 최초 실패 보고

작성: 2026-11-19 · 공개 Draft PR #177 · NO_GOAL · 강사 WSL2 배포 **HOLD**

## 1. 작업의 안전 경계

기준 현장 TAR `d06-forensic-ab-no-goal-r6YhIvPx.tar.gz`, SHA256 `db6c130218bddbe19bec42a6cde7d46476e404b057e1b66b012beb621a574c98`; 원본 불변. TurtleBot3 Waffle/공식 Nav2 및 이미 성공한 Student 소스 `df911a88f88f70a7e622170b55678ee821423d8f` 재사용. 이번 작업은 **읽기 전용 timing 진단 및 기존 core 분석**만 추가. Goal/Velocity/Fault/TTL/Supervisor/Guard/CM 동작은 변경하지 않음.

- `D06_GAZEBO_LIVE_RELEASE=HOLD`
- `AXIA_MVP_DEMO_ACCEPTED=HOLD`
- `CERTIFIED_ESTOP=false`
- `MAIN_MERGED=false`

## 2. 실제 r6 WSLg 최초 첫 위반 — 검산된 정확한 source-stamp 쌍

- source stamp: 68.901000 → 69.000000 sim seconds.
- Gazebo native Scan receive 7964.013676 → 7964.301244 monotonic seconds = **287.568ms**.
- 독립 ROS Raw receive 7964.018297 → 7964.308777 = **290.480ms**.
- 독립 ROS Safety receive 7964.018692 → 7964.324221 = **305.529ms**.
- Student Safety receive 7964.014425 → 7964.317578 = **303.153ms (Scan300 위반)**.
- native Clock *같은 sim stamp* 수신 7963.970236 → 7964.248479 = 278.243ms wall / 99ms sim = **관측 RTF 약0.355804**. 이것은 **독립 Clock subscriber의 host 수신 기준**, Gazebo 내부 publisher의 실제 send 시간 증거가 아님.
- 독립 ROS Safety gap − native Scan gap = **17.961ms**. 300ms 제한을 넘는 **첫 ROS 관측 구간**에서 native 이미 287.568ms를 소비함. 이는 upstream native 수신의 낮은 여유와 후단 전달 간격 확대가 섞인 **시간 경계**이며 GPU/DDS/Linux scheduler의 단일 인과 원인은 아직 미확정.
- 원본은 Navigation/Localization ACK, CM exit0, Gazebo **exit-11**. 코어 백트레이스 없음. NVIDIA WSLg D3D12 렌더러 실측. `get_parameters` responsive라 하더라도 Gazette -11과 직접 인과관계 미증명.

## 3. 유사 브랜치 재사용

- Public `fix/d06-wslg-lidar-vs-rtf-ci-20261118` / Student `fix/g07-nogoal-ordered-cm-shutdown-20261119`: 실제 NO_GOAL native ordered shutdown 및 same-session /clock,/scan 관측, 기존 L2 PASS #44503070174 재사용. 다만 NVIDIA WSLg GPU 인수는 아님.
- `rollback/g07-dual-gui-20261115-proven-xvfb`: CI Xvfb llvmpipe / WSLg native EGL 분리를 그대로 보존.
- Student `perf/d08-wslg-rtf-sensor-profile-20261118`: D08 RGB-D 렌더 부하 연구 선례만 참고. D06 기존 10Hz LiDAR, 300ms Scan TTL을 변경하지 않음.
- `fix/g07-c31-localization-shutdown-ack-evidence-20261117`, `fix/g07-c32-localization-server-stage-20261117`: 관리자 서비스 단계의 원본 타이밍 구분을 재사용. 비검증 timeout 변경이나 재호출 금지.
- upstream [microsoft/wslg #1533](https://github.com/microsoft/wslg/issues/1533), [#1497](https://github.com/microsoft/wslg/issues/1497), [gazebosim/gz-sim #3335](https://github.com/gazebosim/gz-sim/issues/3335) — WSLg D3D12/TLS/Gazebo 크래시 가능성의 배경. **원본 core stack 없이 root로 승격 불가**.

## 4. RED → GREEN → REFACTOR → REVIEW → COMMIT

### Task A — 최초 pair 진단 로직

변경:
- `d06/tools/d06_g07_scan_rx_witness.py`의 기존 `classify_student_first`에 **선택적** `native_clock` 근거 추가. source-stamp가 동일한 경우에만 관측 RTF 및 native-to-peer gap 차이를 기록. 연계 시각 없음 → `None`, `root_cause_proven=False`, `release=HOLD`.
- `d06/tests/test_d06_g07_student_first_receipt_pair.py`: r6 실제 수치로 정밀 회귀, 불일치 stamp 음성 테스트.
- RED [#44527399240](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44527399240): `unexpected keyword argument 'native_clock'`. 최초 잘못된 테스트 import를 정정한 뒤의 의도한 RED.
- GREEN [#44527470151](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44527470151): **106/106 L0 PASS**, 기존 회귀 포함.
- **제한:** ROS-free 분석기의 GREEN이지 실제 WSLg 지연 해소 아님.

### Task B — 기존 Gazebo core 분석 준비

신규:
- `d06/scripts/axia_d06_g07_wslg_existing_core_once.sh`: WSL2 **기존** 코어/대상 바이너리만 GDB batch로 열어 첫 SIGSEGV stack과 all-thread 최대 15-frame, shared-library/maps 수집. 새 Gazebo 실행·global GPU 설정 변경·LD_PRELOAD·core 원본 공개 업로드 금지. 출력 archive + SHA256; root `UNCONFIRMED`.
- `d06/tests/test_d06_existing_gazebo_core_triage.py`: --self-check, invalid core fail-closed, core_not_archived, safety HOLD 계약.
- RED [#44527896385](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44527896385): 누락된 triage 스크립트.
- GREEN [#44528154114](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44528154114): 기존 공개 L0 통과.
- **제한:** 현재 r6 원본에 core 없음. 강사 WSL2에서 새 core를 확보하거나 기존 WSL2 core 발견 전까지 Gazebo 최초 stack `NOT_CAPTURED`, B1/B2/B3 **UNDETERMINED**. 이 도구는 인수용 런처가 아님.

## 5. 새로운 실제 Gazebo L2 — 명확히 FAIL, 재시도 금지

정확한 공개 소스 SHA `2834eccf9822743159aceabced6f9b5dadd1467b`의 실제 Jazzy/Harmonic/Nav2/Waffle Xvfb 통합 Run:
https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44528260284

원본 artifact #14531957185: `axia-d06-g07-nogoal-cm-ordered-l2-44528260284`; native JSONL / launch.log / shutdown ack 원본 존재.

**시간상 최초 알려진 위반은 Lifecycle 종료보다 이전의 센서 수신 gap:**
- Student의 dual-topic qualified 20.005초 구간은 **Raw198 최대120.664ms / Safety198 최대121.503ms / CLEAR198/198**. 기존 `NO_GOAL_SENSOR_WINDOW_CLEAR_CANDIDATE`는 이 구간에만 해당.
- 같은 실제 세션, **Nav2 READY 후** 독립 native+ROS witness의 더 이른 source stamp **31.200→31.302초** 구간: Gazebo native **301.441ms**, 독립 ROS raw **302.017ms**, 독립 ROS safety **302.538ms**. 동일 구간 관측 Clock RTF **0.397999**. 이 구간은 Student의 dual-topic qualified 시작(호스트 monotonic 약467.033s) 이전임. 학생 이후 20초 PASS는 이 최초 타이밍 위반을 무효화하지 못함.
- Student 본연 warmup Safety 구간에도 `pre_ready_safety_first_gap_sec=0.425612`가 별도 기록. 주행 허가 근거가 아님.

**후속 두 번째 실패: Lifecycle 관리 서비스 구분**
- Navigation Manager SHUTDOWN **ACK 2.135663s**.
- Localization `/manage_nodes` SHUTDOWN **request sent, ACK 없음, 30.000372s TIMEOUT**.
- 같은 manager의 독립 read-only `/get_parameters` 응답 **0.026005s** (`node_names` 1 value). **서비스 전체 소실/일반 DDS 단절로 단정 불가**, 특정 Lifecycle 관리 콜백/상태 전이/클라이언트 전달 경계 원인은 미확정.
- Localization manager 최초 shutdown 전이 로그는 없고, 신호 후 rcl preshutdown 및 child exit0.
- CM exit0, Gazebo server exit0, Guard/Supervisor exit0, native witnesses unsubscribe exit0 및 Xvfb Gazebo/RViz 관측은 실제 로그에서 확인.
- `P2_L2_SMOKE_RC=3`; 전체 L2 **FAIL**. 한 실행에서 Sensor-qualified PASS와 정상 프로세스 exit0이 나오더라도 READY 전 통합 계층 timing 위반+Local Manager ACK 실패로 **전체 통합 PASS 금지**.

**중요:** #44528260284에서 Gazebo server exit0은 공개 Ubuntu Xvfb 결과이며 NVIDIA WSLg SIGSEGV 해결 증거가 아님.

## 6. 이번 단계 검증과 미완료

- 최종 공개 L0 [#44528268427](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44528268427) **SUCCESS** / runner canary [#44528268545](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44528268545) **SUCCESS**.
- 동일 SHA 공개 실제 Gazebo L2 [#44528260284](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44528260284) **FAIL**.
- **WSL2 D3D12 새 실행 없음.** Moving Goal, CM120/Guard150, certified E-Stop 모두 미검증.
- 원래 런처/Student/공식 Nav2/Goal/TTL/ROS publisher 미수정. 새 GDB triage는 원본 core가 없으면 HOLD로 종료하고 Gazebo를 시작하지 않음.
- 원본 및 CI artifact 보존. 새로운 동일 세션을 원인 가설 없이 반복 실행하지 않음.

## 7. 다음 단일 원인 가설 및 작업 입구

1. **Scan first boundary:** 실제 READY→dual-qualified 경계의 native301.441ms/ROS302.538ms가 왜 qualified 120ms와 다른지 원본 동일 세션 관측을 보존하여 simulator Clock 느린 구간(0.398 RTF)과 렌더·스케줄링 원인을 분리. 안전 TTL/센서 Hz 변경 금지. 공개 CI에서 이 실제 READY 경계도 반드시 엄격 FAIL로 판정하도록 회귀 포함.
2. **Localization timeout:** `/get_parameters` 정상(26ms)과 `/manage_nodes` timeout(30s)을 구분한 최초 서비스 경계에 집중. 공식 Nav2 manager/service 실행·callback 및 원본 `map_server`, `amcl` 종료 전이를 별도 계측하기 전 retry/timeouts 확대 금지.
3. **WSLg Gazebo exit-11:** 기존 core 발견 시 private GDB read-only 추출. 없다면 공개 CI 사전 검증을 거친 **별도 원인 진단**에서 최초 core stack 확보 (최종 WSL2 L3 시연과 별개). 스택 없이는 D3D12/TLS 우회 적용 금지.
4. 위 실제 계층 모두 녹색 확인 후 한 번의 공개 real same-session L2를 다시 실행. 그 뒤에만 SHA/blob pinned 강사 WSL2 원샷 L3 배포.

## 8. 작업 보고 범위

Git 공개 Draft PR #177 브랜치에만 파일 반영, `main` 미병합. Student PR #62는 변경하지 않음. **원인 완치 또는 로봇 시연 최종 인수 선언 금지**.
