# AXIA D06 C29 — 공개 CI 최대 수행 → 강사 WSL2 단일 최종 인수 작업계획

**검토일:** 2026-11-21 (KST). **적용 환경:** Windows + WSL2 Ubuntu 24.04 + WSLg D3D12 NVIDIA RTX 2060 Max-Q + ROS 2 Jazzy / Gazebo Harmonic / 공식 Nav2. **정책:** MVP 범위 유지, RED→GREEN→REFACTOR→REVIEW→COMMIT, 공개 CI GREEN 후 최종 WSL2 1회, main 승인 전 병합 금지, SW STOP != 인증 E-Stop.

## 0. 결론과 이 계획의 검증 수준

**WSL2에서 개발 중간 실험을 매번 실행할 필요 없음.** ROS-Free 계약/증거 분석은 L0, 실제 ROS2 상호작용은 L1, 실제 Gazebo/공식 Nav2/CM/NO_GOAL 통합과 native child 종료는 공개 Linux Ubuntu24.04 CI L2에서 수행한다. 강사 WSL2는 **Windows GPU/WSLg D3D12/커널 스케줄링 특성의 최종 인수 L3 단 1회**로 한정한다.

단, 현재 **최신 C27 Student SHA를 공식 Nav2/CM/TB3 동시 실행한 STRICT L2 2/2는 NOT_RUN**. C27의 기존 실제 Gazebo L2 [#44866813322](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44866813322)는 실제 `gz sim -s empty.sdf` ServerControl→native exit0, **Nav2/TB3/CM/Scan20초 없음**. 검증 범위 혼합 금지.

## 1. 근거와 재사용할 기존 성공 CI

### 동결할 현장 최초 실패 경계

User compact `compact-20261121T042832Z-3465.tar.gz`, 검증 SHA256 `6ecc04c081ca975f73585a9b0b18cbd489a785f8f33792371b93384dadab778b`:
- Goal/Fault 미실행, WSLg D3D12 NVIDIA RTX2060 Max-Q.
- **첫 RAW Scan TTL:** 316.032ms > 300ms, exact student pair Native 286.837ms, independent ROS305.729ms, student316.032ms. 원인 미확정. RAW 최대358.830ms.
- 다른 시간창 **첫 Safety Scan TTL:** 357.472ms >300ms, Safety 최대357.472ms. 별도 post-READY native314.483ms / independent ROS raw405.396ms, local RTF0.268223. 평균 RTF0.604076. 하나의 원인으로 병합 금지.
- Supervisor `SCAN_TIMEOUT`과 CM bond 4000ms lost는 **후행 안전 상태**. Navigation ManageLifecycleNodes 응답 `40.000851s SERVICE_TIMEOUT`, Nav/Loc ACK false, CM exit0 미확인, `P2_L2_FORCED_TEARDOWN`. Gazebo 서버의 native exit0/-11은 구형 compact로 **미측정**; 이전 발생 Gazebo SIGSEGV와 현장 최신 실패를 혼동 금지.

### 이미 해결 또는 준비된 코드를 중복 작성하지 않음

| 기능 | 검증 소스 / 성공 증거 | 현재 한계 |
|---|---|---|
| C28 최초 오류 JSON 분리 및 전체 launch.log EOF 소형 재압축 | Public SHA `ffe0d467e159efcf1b60da6263203d3cee86f9d5`, [L0 #44866661745](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44866661745), Git blob `cefe00b6304c7bab0265b7b5d660cfb9a909a3a3` | WSL2 로컬 기존 raw TAR는 아직 새 압축기로 재분석하지 않음 |
| C27 `stop:true` ACK 후 실제 Gazebo exit0 확인 | Student SHA `6c79c09d91f13c81961492eb30e66d99d307831c`, Draft [Student PR #87](https://github.com/silverbjin/axia-robot-safety-student/pull/87), [실제 빈 월드 L2 #44866813322](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44866813322) | 빈 월드/Headless only, WSL2 NVIDIA Ogre2 종료 미검증 |
| D06 실제 Gazebo/TB3/Nav2/CM 20초 Strict NO_GOAL 통합 | `.github/workflows/axia-d06-g07-native-nogoal-cm-clean-l2-20261119.yml`, 예전 [L2 #44503070174](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44503070174) | **학생 구 SHA `0565e580...`, CI 전용 `rmw_cyclonedds_cpp`**로 고정. 새 C27와 Owner 기본 Fast DDS를 검증하지 않음 |
| 실제 G07 Moving Goal 2-cycle 엄격 안전 시연 | G07 Scan300 Public PR #207 / [2-cycle 실물 L2 #44830956042](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44830956042), Student `891bf65349cf8dfb203bb8b97ffe0346b3fb8b3f` | 이 SHA와 C27 NO_GOAL 최신 SHA는 달라, 전체 시연 통합 인수로 결합 금지 |
| 최초 Scan RMW/MessageInfo와 정확한 native/rosbag 페어 | Public #215; Jazzy MessageInfo 2-인자 콜백 정정 Student PR #89, [실제 Jazzy L1 #44865731221](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44865731221) 35/35 metadata | 실제 최초 WSL2 300ms 원인 확정 아님. 이벤트 발생 때만 진단용으로 재사용, new Executor 개발 금지 |
| D08 CM GetState/GetParameters 분리 실 Gazebo A/B | D08 Branch `feat/d08-cm-service-ab-isolation-20261121`, [실제 8-cycle #44768100012](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44768100012) | WSL2/CM TTL 증명이 아닌 비교 실험, B의 프로세스 생성 지연 때문에 production 기본 반영 금지 |

## 2. CI 전용 후속 작업 (WSL2 실행 없이 완료 가능)

| 우선순위 | 개발 단위 | 변경 파일·활용 소스 | 필수 RED / GREEN 검증 | 종료 조건 |
|---|---|---|---|---|
| P0 | **C29-01** 정확한 C27+Public 핀 통합 매니페스트 | 신규 `d06/ci/c29_source_manifest.json`, 검증 테스트; 기존 C28 public, Student C27, 공식 Jazzy/Harmonic 파일 핀 | RED: 잘못된 Student SHA/ROS RMW/미검증 L2를 PASS로 처리 시 실패. GREEN: 정확한 SHA, blob, run ID/검증 범위를 fail-closed 확인 | 같은 바이너리/설정 아닌 CI PASS를 Owner WSL2 인수 증거로 승격하지 않음 |
| P0 | **C29-02** 과거 실측 최초 위반 안전 상태 회귀 | 기존 `d06/tests/test_d06_c28_actual_wsl2_compact_eof_and_safety.py`, `d06/tools/d06_g07_scan_rx_witness.py` 재사용 | 316.032/357.472ms 정확 수치, 300ms FAIL, 각 topic host mono 비교, Nav40s timeout/CM bond loss/forced teardown 분리, Gazebo exit0 없는 상태 HOLD. C28 기성 테스트 재사용, 빠진 연결만 보완 | 최초 이상 및 후행 실패를 구분하고 결측 로그도 PASS 승격 금지 |
| P0 | **C29-03** 실제 **동일 Gazebo 세계** NO_GOAL/Nav2/CM/C27 exit0 통합 L2 | **기존** `.github/workflows/axia-d06-g07-native-nogoal-cm-clean-l2-20261119.yml`의 테스트 본문 재사용, 새 별도 C29 workflow 복제/핀 변경, Student C27 `6c79...` | 실제 Jazzy+Harmonic+TurtleBot3 Waffle+공식 Nav2+CM+20초 Raw/Safety Scan, nav/local ACK, CM exit0, ServerControl 응답과 별도 실제 Gazebo child exit0, no forced teardown, Goal=false. **독립 cold-run 2/2**, 각각 SHA 및 evidence bundle | 2/2 실제 CI PASS와 전 조건 통과 없으면 L3 출고 금지 |
| P0 | **C29-04** Owner와 같은 RMW 경계 재검증 | 기존 Fast DDS owner와 CI CycloneDDS 증거 활용, 실제 ROS2 L1 / full NO_GOAL L2의 `RMW_IMPLEMENTATION` 명시 | **첫 검증은 실제 Owner 기본 RMW**에 맞춤(`rmw_fastrtps_cpp`인지 런타임 실측). CycloneDDS는 **A/B 별도 진단**; 성공 결과 대체 금지. peer/native와 학생 같은 header pair, sim header와 mono 수신 경계를 구분 | Owner와 RMW 동일 source의 20초 실제 Scan300 위반 0. 또는 미해결 HOLD |
| P1 | **C29-05** 4초 CM bond loss / 40초 Nav shutdown timeout **회귀** | 기존 lifecycle manager/CM shutdown 스크립트·단위 fixture 재사용. 별도 가짜 ROS 응답/종료 상태로 fault path 한정 | 무응답/CM process loss→`navigation_ack=false`, `cm_exit_code=null`, 강제 teardown, `gz` 상태 미확인 시 FAIL-CLOSED. 정상 실제 L2에서는 nav/loc ACK와 CM child0/ Gz0 필수 | 40초 타임아웃 연장이나 CM bond timeout 완화 없이 정확한 첫 실패·안전 종료 처리 |
| P1 | **C29-06** WSL2 저 RTF 재현 가능한 성능 스트레스와 기존 첫 Scan L1 진단 재사용 | WSL2 RTF 0.604/국소0.268을 바탕으로 CI의 CPU 제한 시나리오를 선택적 A/B로 사용; 변경 최소 | 지터가 발생하면 반드시 Scan300 FAIL/HOLD, 첫 동일 header pair 캡처. 저성능 CI가 우연히 PASS했다고 WSL2 GPU 안정성 인정하지 않음 | Fail-closed 안전 계약 확인. 성능 동일성 증명 아님 |
| P0 | **C29-07** 통합 release gate, 원샷, 최소 증거 압축 | `d06/scripts/...`에 pinned Owner 최종 실행기(필요시 단일 신설); C28 `--compact-only` 재사용 | L0, real L1 (해당시), strict full L2 cold-run 2/2, SHA/blob, Fast DDS 실제 적용, Scan300, Nav2/CM/Gz0, Goal authority, compact TAR+SHA 모두 자동 확인. public CI 전부 GREEN 후에만 SHA 고정 | **WSL2 L3에 1회 배포 가능**; 사용자 중간 수동 진단 불필요 |

**축소 원칙:** 위 항목은 이미 있는 테스트/러너/진단기를 조합하는 작업이다. 공식 TB3/Nav2/Collision Monitor나 Safety Supervisor/Guard core 알고리즘을 고치지 않는다. 같은 기능이 다른 PR에서 통과한 경우 그 exact SHA/run을 명시적으로 재사용한다. User WSL2 실패를 CI에서 재현할 수 없을 때는 범위를 분리해 HOLD; 현장 무한 반복 금지.

## 3. 강사 WSL2에 남길 최종 1회 작업

**C29-01~07 공개 CI 통과 후** 강사 WSL2에서 실행할 불변 pinned 명령 하나. 세부 코드는 CI 최종 source SHA가 확정된 후 출고한다 (현재 **새 최종 실행기 미출고**).

1. 환경 확인: WSL2 kernel, Ubuntu 24.04, ROS 2 Jazzy/Gazebo Harmonic, GUI/WSLg, `glxinfo -B` D3D12 NVIDIA, 장치와 RMW 정보, CI artifact exact provenance, Git blob.
2. **기존 원본 TAR가 존재하면 C28 `--compact-only`를 자동 실행**하여 실제 종료 EOF 복구. 사용자의 별도 중간 검수 요구하지 않는다. 원본 TAR가 없으면 기존 C28 작은 업로드만 유지, 해당 과거 종료 결과는 미확정이라고 기록.
3. 동일 터미널/동일 GZ_PARTITION의 NO_GOAL 센서 약20초, 실제 Gazebo native/ROS 학생 exact pair, Scan300·Clock/Odom300 중 해당 시나리오 안전 경계, Nav2 lifecycle ACK, CM native exit0, Gazebo native exit0 확인. 반드시 **첫 safety-state transition**과 첫 TTL 위반으로 보고. TTY/Goal/Fault/Moving 권한 없음.
4. 원본 원격/로컬 custody SHA256 확인, **작은 TAR+SHA256 한 쌍만** 회수. 화면/gui 확인 필요 시 1번만 진행. 성공해도 **D06 NO_GOAL 범위 PASS**이지 아직 별개 Moving CM120/Guard150 전체 인수/인증 E-Stop은 아님.
5. 실제 WSL2에서 새 결함 재발 시 현장 재시도하지 않고 **CI 재현 가능 부분을 먼저 RED→GREEN**하여 출고 버전을 교체한다. 전체 시연 안정성은 모든 안전 계층 검증 전까지 미검증 표시.

## 4. CI와 실제 WSL2 동등성의 한계

- GitHub-hosted 일반 Ubuntu/Docker/Xvfb는 **Linux 서버 타이밍, 실제 Nav2/CM 코드, Gazebo Harmonic 및 ROS2 RMW 기능 검증**에 적합하나, Windows Windows GPU 드라이버→WSL kernel→WSLg system distro→Mesa D3D12 NVIDIA에 의존하는 실제 GPU/스케줄러 경로를 그대로 재현하지 못한다.
- GitHub-hosted Windows에서 WSL2를 요구하는 중첩 가상화는 GitHub가 **공식 지원하지 않음**, 따라서 무료 일반 hosted runner에서 NVIDIA WSLg L3 자동 보장 불가. 공식 https://docs.github.com/en/actions/concepts/runners/github-hosted-runners
- GPU-optimized larger runners는 별도 유료 기능 및 물리 GPU/드라이버/WSLg 동등성 차이. 이번 MVP 무료 CI 인수 필수 범위로 넣지 않는다.
- 별도 **자가 호스팅 Windows/WSL2 NVIDIA GPU Runner**가 있다면 자동 L3는 기술적으로 가능하나, 본 프로젝트에는 제공된 호스트가 없다. 기존 강사 WSL2를 상시 self-hosted runner로 설정하는 것은 *사용자 최종 인수만*이라는 목표와 충돌하므로 권고하지 않는다.
- 출처: GitHub hosted runner 공식 문서와 Microsoft WSLg https://github.com/microsoft/wslg/blob/main/README.md.

## 5. 검증 및 상태

**이번 작업은 기존 증거·코드·브랜치 감사 및 개발 계획 문서 제출만. 새 C29 실행 코드/CI 작업을 PASS로 보고하지 않는다.**

```text
C28_PUBLIC_L0=PASS #44866661745
C28_REPORT_SHA=4fd31b87de381b3c72d2cde02bebf309ce683f63
C27_EMPTY_WORLD_REAL_GAZEBO_L2=PASS #44866813322
G07_OTHER_BRANCH_MOVING_2_COLD_L2=PASS #44830956042
C29_LATEST_C27_FULL_NAV2_CM_GZ_L2_TWO_COLD_RUNS=NOT_RUN
C29_OWNER_MATCHED_RMW_FASTDDS_L2=NOT_RUN
C29_RELEASE_MANIFEST=NOT_CREATED
C29_OWNER_FINAL_ONESHOT=NOT_RELEASED
LOCAL_WSL2_DIAGNOSTIC_REPEAT=NOT_REQUIRED_NOW
LOCAL_WSL2_FINAL_ACCEPTANCE=NOT_RUN
AXIA_MVP_DEMO_ACCEPTED=HOLD
MAIN_MERGED=false
CERTIFIED_ESTOP=false
```
