# AXIA G07 통합 개발 — 사이클 02 중간 보고서 (교육용)

- 일자: 2026-11-15 KST
- 상태: **공개 CI L0 GREEN / 고정 WSL2 부트스트랩 공개 CI PASS / Owner L3 NOT_RUN**
- 단일 Instructor P4 소스: `db1eec05e01e1db0d0d2e0c05610806ef4e499f9` / Tree `005cc352d63067beb9d34397e51b51f7974ce7ef`
- CI 근거: 실 Gazebo+RViz Xvfb L2 [#43685818018](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43685818018), CI workflow SHA `2bb0a46dd1eccdce364ccc9faeb4d5650bfb99f2`
- 최종 부트스트랩 Release SHA: `91e033a39da2e1295416d2c8d55deb52e10c2469`
- Owner 정식 인수: **아직 아님**. WSLg 및 실제 안전 TTL/정지/원본 증거는 최종 Owner 확인이 필요함.

## A. 문제 정의 — CI PASS와 현장 인수의 차이

Cycle01에서는 동일 P4 코드로 CLEAR→SLOWDOWN→STOP, 7채널 TTL, odom 1.025초, native S02 contact0, 14-topic rosbag, Nav2 shutdown ACK/CM exit0, Gazebo+RViz Xvfb 실창 동시 실행이 **한 번** 통과했다.

그러나 당시 WSL2에서 **동일한 GUI/WSLg 스케줄링이 검증된 것은 아니고**, 이전 사용자 Owner 실제 실패(Guard upstream CM TTL 169ms, 후속 CM source 184ms)의 재발 여부는 미지수다. 최종 Owner는 단일 수동 TTY Goal만 허용하며 자동 입력/재시도/인수 승격은 안 된다.

### 요구되는 안전 인수 경계

- 정확한 Instructor SHA/Tree, CI L2 Run/Workflow SHA 및 원본 P4 release 실행기 모두 검증.
- 150ms CM/Guard, 300ms Scan/Odom/Clock 한계를 변경하지 않음.
- 실패·누락·모호한 증거는 Goal 이전 차단 또는 Owner 결과 HOLD.
- GUI/RViz는 읽기 전용 MarkerArray만 발행; 실제 모터/Goal의 소유권은 P4 실행기.
- 최초 실패 발생 시 CI 회귀 RED→GREEN 먼저 수행하고 동일 WSL2 재시도 금지.

## B. 재사용 전략

직접 안전제어 구현을 **추가하지 않았다**. 기존 P4 `scripts/axia_p4_mvp_final_owner_once.sh`를 정확한 Release SHA로 재사용한다. D06의 다음 파일은 필요한 범위에서만 포트한다.

| 파일 | 역할 |
|---|---|
| `d06/live/d06_readonly_monitor.py` | 기존 public main과 동일한 순수 읽기용 ROS Marker 관측기, blob `62419327268adb28de110bb1415dc5871cd0dc79` |
| `d06/rviz/d06_safety_bubble.rviz` | 기존 public main의 RViz 레이아웃, blob `9259ef57a70e5fca78fc62e17b2c5c5244a0d1a7` |
| `d06/scripts/d06_rviz_sidecar.sh` | 기존 D06 Owner 세션 추적·Nav2 startup 이후 시각화; 렌더러/관측기 CPU 분리. P4 CM CPU 고정은 입증되지 않았으므로 해당 오해 표현 제거 |
| `d06/live/d06_g07_field_triage.py`, `d06/live/d06_guard_cm_first_latch_join.py` | 기존 원본 Owner/Guard/RMW를 읽기 전용으로 진단; 공용 자료에는 원본 메시지/UUID를 올리지 않음 |
| `d06/live/g07_unified_final_owner_gate.py` / `d06/acceptance/g07_unified_final_owner_ci_gate.json` | 실제 GUI L2 원본 SHA와 7채널 실측·ECM·shutdown 조건을 확인하는 fail-closed admission |
| `d06/scripts/g07_unified_final_owner_wsl2_once.sh` | 수동 TTY, WSL2, GitHub 비공개 인증, 소스 PIN, 1회 시도 원장, D06 sidecar+P4 Owner 실행 |
| `scripts/axia_g07_final_owner_wsl2_bootstrap.sh` | 공개 GitHub에서 고정 Public SHA/Tree를 1회 가져와 Owner 스크립트 실행 |

## C. RED → GREEN → REFACTOR → REVIEW → COMMIT

1. **RED** [#43686425821](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43686425821): final admission 검사/실행기 누락, 기대한 L0 실패.
2. **GREEN 후보 실패** [#43686595067](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43686595067): 6개 신규 검사 중 5개 PASS, 1개 FAIL. **원인:** 재사용 D06 wrapper에서 이전 `d06_g07_final_owner_ci_gate.json` 경로가 남아, 새 통과 근거를 읽지 못해 Goal 이전에 차단.
3. **수정 GREEN** [#43686636084](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43686636084): 정확한 신규 Gate 경로 사용. 5+7+6개 회귀 PASS.
4. **확대 검증** [#43686702295](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43686702295): Owner `--self-check`와 `--admission-check` 실제 Bash CLI 무ROS 통과.
5. **부트스트랩 RED** [#43686772075](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43686772075): 고정 Public Tree/TTY 정책을 갖춘 1회 진입 스크립트 누락을 확인.
6. **부트스트랩 GREEN** [#43686831615](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43686831615): 5+7+8 = **20 L0 검사 PASS**.
7. **공개 Release 실제 검증** [#43686905395](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43686905395): git blob `6643cd472a97c20ccbdb3cb824822fbf5cda695d`, `--self-check`, no-TTY 차단, WSL2 Gate CLI 및 원본 P4 Owner `--admission-check` 모두 PASS. 출력: `AXIA_G07_FINAL_OWNER_BOOTSTRAP_CI_NO_ROS_NO_GOAL_PASS_OWNER_L3_NOT_RUN`.
8. **REVIEW:** P4 소스/안전제어 변경 없음. main·학생 저장소 변경 없음. GUI 관측기는 모터 명령 publisher가 아님. 1회 시도는 WSL2의 `~/.axia_g07_final_owner_attempts`에 atomic `mkdir`로 등록; 현장 실패 시 자동 재시도하지 않음.
9. **COMMITS:** Owner gate/sidecar/원본 재사용 `3a7e1dba`, stale gate 경로 수정 `606a0a3a`, 정적 CLI 검증 `3259ad99`, bootstrap `d957d47c`, Release 배포 `91e033a3`.

## D. 검증 수준

| 항목 | 판정 |
|---|---|
| 기존 P4 headless 실제 L2 | PASS_SCOPED #43674784552 (재실행 생략) |
| 신규 GUI Xvfb 실제 L2 | PASS_SCOPED #43685818018 |
| 최종 Owner bootstrap Release L0 | PASS #43686905395 (실제 WSL2/Gazebo/Goal 없음) |
| read-only monitor 및 RViz 원본 | 기존 Public main과 blob 동일; 과거 별도 실제 Jazzy L1 증거만 재사용 |
| 새 WSL2 Owner Goal·WSLg RViz 화면 | NOT_RUN |
| `AXIA_MVP_DEMO_ACCEPTED` | HOLD until actual Owner original evidence |
| 실제 인증된 E-Stop | 인증 주장 없음, SW Stop만 수행 |

## E. WSL2 단일 최종 확인으로 인계

고정된 [원샷 사용 가이드](./G07_FINAL_OWNER_WSL2_ONE_SHOT_GUIDE_20261115_KO.md)를 따른다. 실제 원본 로그·rosbag 및 WSLg Gazebo/RViz 화면을 **한 번만** 검수한다. 실패 시 최초 상태 전이와 최초 타이밍 위반을 CI 비식별 fixture로 추가하며 현장 반복 시도 금지.

**교육 포인트:** 세 가지 PASS를 혼동하지 않는다. ① 컴파일/계약 L0 성공, ② 시뮬레이터+노드 연결 실제 L2 성공, ③ 로컬 Owner WSLg L3 최종 인수. 이 보고서 시점은 ②까지 증명되었고 ③은 남았다.
