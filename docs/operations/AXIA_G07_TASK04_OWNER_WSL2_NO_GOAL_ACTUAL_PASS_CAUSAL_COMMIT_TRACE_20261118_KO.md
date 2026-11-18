# AXIA G07 Task04 — 강사 WSL2 NO_GOAL GUI 현장 PASS 및 최초 실패 원인 추적 보고서

**2026-11-18 KST · 공개 CI / 교육용 포렌식 보고서 · 인수 범위 고정**

> **판정:** 강사 WSL2/WSLg **NO_GOAL GUI 자동 사전검증 PASS**. 실제 Gazebo·공식 Nav2 경로 계산·Costmap 장애물 반영·RViz Path DDS 구독까지 확보. 하지만 화면 픽셀/3D 렌더링 육안 검증 **PENDING**, 실제 Owner Moving Goal L3 **NOT_RUN**, 전체 `AXIA_MVP_DEMO_ACCEPTED=HOLD`, `CERTIFIED_ESTOP=false`. 여기의 NO_GOAL PASS를 주행·안전 인증으로 승격하지 않는다.

## 1. 재현 가능한 원본 증거와 무결성

이번 보고서는 사용자가 제공한 **신규 실제 Owner WSL2 원본** `owner-gui-pregate-lxXToFIk.tar.gz`와 대응 `.sha256`를 직접 검사한 결과이다. 이전 실패 원본과 혼동하지 않는다.

| 원본 증거 | 실제 확인 | 유효 범위 |
|---|---|---|
| 신규 Owner `tar.gz` | SHA256 `4e69c1a43f3623104da0425211dd2cd20c90c2d986750c66196ee397756defb2` | 첨부 .sha256의 본문 값과 동일 |
| 최상위 `SHA256SUMS` | **73/73 OK** | 모든 명시된 파일 바이트 무결성 |
| `native/SHA256SUMS` | **59/59 OK** | Native 세부 증거 파일 무결성 |
| `manifest.txt`, `native/source_sha.txt` | Student `01752add2e30c90c4d3286ef3a450f97746ecb55` | 정확 공개 Student 원본 |
| `owner_core_parity.json` | `CORE_PARITY_PASS`, 25 ROS/Gazebo 패키지, 공식 파일 5개 일치 | Ubuntu 24.04/WSL2 사용자 공간의 이 범위만 비교 |
| `window_status.txt` | `run_rc=0`, `rviz_window=1`, `gazebo_window=1`, `xwininfo_available=1` | X11 창 존재 자동 검사 |
| `first_failure.txt` | `NONE` | 상위 원샷 판정 |
| `native/teardown.txt` | `P2_L2_GRACEFUL_TEARDOWN` | no-goal world 종료 경로, Nav2 moving-Goal lifecycle ACK 아님 |

원본 ZIP·원시 로그·사용자 경로는 **공개 저장소에 업로드하지 않는다**. 공개 보고서는 이 수치·해시·코드 위치만 사용한다. 이 SHA256은 내용 무결성 비교이지 외부 저장소에 원본이 보존되었다는 주장이 아니다.

### 실제 강사 WSL2 런타임 원본 요약

- `ROS_DOMAIN_ID=86`, `GZ_PARTITION=axia_p2_task04_86_11058_1794977846`. 정규식 `^[A-Za-z0-9_]+$`에 적합하며 과거의 `=LOCALHOST` 오염이 없음. `native/runtime.txt`의 동일 파티션과 대조함.
- `wslg_glxinfo_adapter_NVIDIA.txt`: **D3D12 NVIDIA GeForce RTX 2060 with Max-Q Design**, `OpenGL renderer string` 및 OpenGL 4.6 확인. GPU 선택 및 실제 GLX context 확인이라는 뜻이며, GUI 장면 픽셀의 정상 렌더링 검증은 아님.
- `native/startup_verdict.json`: 실제 Gazebo/ROS 공식 Nav2 시작 `SMOKE_READY`, 지도·AMCL·TF 기반 준비 증거. `native/d07_gui_pregoal/owner_pregoal_l2.json`: 물리 배치 ACK, 전방 약 2.041m, 측방 약 0.723m, `goal_sent=false`.
- `native/d07_h01_geometry/d07_h01_geometry.json`: `status=D07_H01_REAL_NAV2_GEOMETRY_READY_NO_GOAL`, `real_nav2=true`, `real_laser_scan=true`, `actual_costmap_obstacle_observed=true`, `path_changed=true`, `obstacle_restored_away=true`. `goal_sent=false`, `owner_l3_accepted=false`, `formal_accepted=false`.
- 실제 `phase_evidence.jsonl`은 정확히 세 행. 모두 `source=official_compute_path_to_pose`, `frame=map`, `native_action_result_relayed=true`, `visualization_only=true`, `goal_sent=false`, `robot_moved=false`.

| 단계 (`stage`) | 공식 Path pose 수 | RViz DDS 구독자 | 실제 ROS Scan stamp | 실제 Costmap stamp |
|---|---:|---:|---:|---:|
| `before` | 52 | 1 | 66.402 | 64.428 |
| `intrusion` | 52 | 1 | 86.802 | 86.772 |
| `restored` | 52 | 1 | 99.402 | 101.499 |

Obstacle 삽입 시 실제 Costmap **신규 lethal 92개**가 기록됐으며, Path 차이는 약 **0.3659m**, 장애물 기준 우회 경로 최소 거리 약 **0.3598m**로 기록됨. 철거 후 `costmap_natural_drift.status=SPATIAL_BASELINE_EXACT_NO_GOAL`, `natural_drift_cells=0`, `post_restore_diff_cells=0` 및 원본 baseline grid SHA256 복귀가 확인됨. 이는 **공식 경로의 시각화·장애물 반영** 증거이며 로봇 실제 이동/무충돌 증거가 아니다.

## 2. 실패 원인을 어떻게 좁혔는가: 최초 현장 증거 → 가설 → 실험 → 결론

### Cycle A: 기존 Task03 성공은 현장 GUI 성공이 아님 — 범위 분리

- 기존 실제 ROS2 Jazzy/Gazebo Harmonic Moving Goal 공개 CI [#44223320904](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44223320904): Task03 S02 Contact0, CM publisher 120ms, Guard 150ms, Bag14, 정확 Goal CANCELED, Nav2 ACK의 **동일 CI Run 내** 성공. SHA `6bc8b0711ab056e63e100f3eede2c5f06cdf3856`, Student SHA `01752add2e30c90c4d3286ef3a450f97746ecb55`.
- **문제:** 이 원본은 headless 공개 CI의 실제 Gazebo L2이지 **강사 WSL2/WSLg 화면** 검증이 아니다.
- [`6cac07cb`](https://github.com/silverbjin/axia-robot-safety-ci-public/commit/6cac07cbf9dab75f3fd7db02c12bf0950798c18c) + [`8cd961c3`](https://github.com/silverbjin/axia-robot-safety-ci-public/commit/8cd961c3a324a5b26c0e12f7e1fcd6190d592fcd): 최초 공개 L0 계약 **RED** [#44232883070](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44232883070).
- [`37a9cfdf`](https://github.com/silverbjin/axia-robot-safety-ci-public/commit/37a9cfdf456c352e79e40714ad314acd624e29cd): Public Student 원본 고정·WSLg 사전검사·NO_GOAL 원샷·단일 evidence archive 도입. [`4db31c90`](https://github.com/silverbjin/axia-robot-safety-ci-public/commit/4db31c90afe568282bc9d49713e053bf70b43152): 최초 공개 L0 GREEN [#44233533697](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44233533697), **4/4**. 이 단계에서 실제 강사 GUI 실행을 PASS라고 주장하지 않음.

### Cycle B: 실제 Owner WSL2 첫 실패 — 최종 예외 대신 최초 파티션 오염 분석

- **이전 실패 원본** (이번 신규 성공 archive가 아님) SHA256 `60794337c9dd346c08be41571fec7b84a931154b27d9a06566eaea835d587415`, 내부 11/11. 현장 첫 관측 `D07_H01_GUI_RVIZ_PATH_SUBSCRIPTION_ABSENT` 및 창 0/0. 기본 watcher의 시작·첫 종료 로그가 원본 압축에 빠져 있었음.
- [`f73ca3d8`](https://github.com/silverbjin/axia-robot-safety-ci-public/commit/f73ca3d885396cf360540bdaf74e57995c2461ff): 최초 실패 수치·SHA·오염된 파티션을 비밀 없는 fixture로 고정.
- **가설:** 셸 변수 `$_`를 PID로 잘못 사용했으며, 직전 `export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST`의 마지막 인수가 `GZ_PARTITION` 안으로 들어갔다.
- **증거:** 원본 `GZ_PARTITION=axia_p2_task04_86_ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST1794975058` 안에 실제 환경변수 대입과 `=` 문자가 포함됨. 정확한 Bash 명령 시퀀스를 재생해 같은 종류의 오염을 재현.
- [`5a67bf09`](https://github.com/silverbjin/axia-robot-safety-ci-public/commit/5a67bf0974bfe2e3bce4c2037c94c4881a4715b2), [`3ade1748`](https://github.com/silverbjin/axia-robot-safety-ci-public/commit/3ade1748bab93821757e1bd9e6cfc3d9af055a21): 회귀 RED [#44237062643](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44237062643) (6개 신규 계약 중 4개 실패).
- [`1a5334a4`](https://github.com/silverbjin/axia-robot-safety-ci-public/commit/1a5334a4de4f8126693c098aff1f7c47bdc1eebc): `BASHPID`로 교체하고 파티션 문자/길이 검사, 실제 별도 GPU GUI watcher·ACK·child first-exit·Transport topic·로그 보존을 최소 수정. 공개 GREEN [#44237386904](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44237386904) **10/10**.
- **증명된 결론:** 최초 셸의 `GZ_PARTITION` 오염은 재현·수정됨. 단, **원본 누락된 watcher 로그 없이 이것만으로 이전 RViz 구독 실패의 유일한 원인을 증명한 것은 아니다.**

### Cycle C: 공개 실제 GUI L2 첫 실패 — 실행 오류가 아니라 후처리 스키마 오류

- [`ffbc4e13`](https://github.com/silverbjin/axia-robot-safety-ci-public/commit/ffbc4e13dd03fae92167c51b2bba31f4d8dbfeaa): 동일 Student SHA의 실제 Ubuntu/Gazebo Harmonic/TB3/공식 Nav2/RViz Xvfb L2 추가, **NO_GOAL**.
- 실제 [RED #44237948105](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44237948105): 원본 native GUI runner **rc=0**, Gazebo/RViz X11 **1/1**, 하지만 CI 후처리 Python `KeyError: 'phase'`. 이는 원본 Path 메시지의 실패가 아니라 **reader가 `phase`를 요구하고 producer가 `stage`를 기록한 스키마 불일치**.
- [`c0b90102`](https://github.com/silverbjin/axia-robot-safety-ci-public/commit/c0b9010235f2aa5d4fccde25217179d441ce598b): 정확한 Student 원본 `validate_official_path(...)`에서 `stage` 키를 확인하는 2개 회귀 **RED**.
- [`5bb0cd72`](https://github.com/silverbjin/axia-robot-safety-ci-public/commit/5bb0cd72086f2f1a057f382649b773fff106f1f9): 후처리 판독만 `p["phase"]→p["stage"]`로 수정. 실제 새 [GREEN #44238643061](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44238643061), Job `134580794869`: **L0 12/12 + 실제 Gazebo/Nav2/RViz Xvfb 세 단계 Path DDS 구독 성공**, runner rc0, 두 창 감지. Student/Nav2/CM/Guard 수정 없음.
- **결론:** GUI 창을 띄운다는 사실과 Path 구독 판정을 구분하고, 원본 producer 스키마에 맞게 검증기를 바로잡은 결과 실제 공개 L2가 완료됨. 이 CI 성공을 WSLg GPU로 승격하지 않음.

### Cycle D: 범용 공개 Python CI만 실패 — checkout 레이아웃 분리

- 실제 [RED #44238649926](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44238649926): **227 passed / 1 failed**. 범용 `pytest tests`는 CI repo만 체크아웃하는데, native 전용 schema 테스트가 `../student/.../d07_h01_path_visual.py` 실파일 존재를 무조건 요구함. 최초 실패 `AssertionError: False is not true`.
- [`ef855371`](https://github.com/silverbjin/axia-robot-safety-ci-public/commit/ef855371ee4cfe2d6a30c092bb3b338dd631e5c3): 범용 job은 native workflow의 **정확 Student SHA/checkout/검증기 호출 계약**을 정적으로 검사하고, 실제 native `ci/` checkout에서 Student 파일이 없으면 여전히 fail-closed. 모든 native 원본 Path 함수 테스트와 실제 DDS 증거 검사 유지.
- 실제 GREEN [#44240074839](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44240074839) **228/228**, 보고서 포함 최종 [#44240373775](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44240373775) **228/228**. [`4daa6714`](https://github.com/silverbjin/axia-robot-safety-ci-public/commit/4daa6714e3165d26b59a5dd3f39fdc12b6922824)에서 교육용 보고서 커밋.
- **결론:** 주행·GUI 실패가 아니라 **unit/native 검증 실행 레이아웃 불일치**. native GUI를 다시 실행하거나 안전 TTL을 완화할 이유가 없었음.

### Cycle E: 이번 강사 WSL2 실제 신규 현장 재검증 (현재 인수)

- **실제 사용한 수정 실행기**: [`5bb0cd72` 고정 SHA의 공개 WSL2 원샷](https://github.com/silverbjin/axia-robot-safety-ci-public/blob/5bb0cd72086f2f1a057f382649b773fff106f1f9/scripts/axia_g07_task04_public_owner_wsl2_pregate_once.sh), 원본 Student 정확 SHA 고정. 과거 문제 스크립트 SHA `4db31c90...`는 사용하지 않음.
- **최초 오염 재발 여부:** 현재 manifest/runtime `GZ_PARTITION` 모두 유효하고 동일. `D07_H01_GUI_RVIZ_PATH_SUBSCRIPTION_ABSENT` 재발 없음.
- **새 증거:** 정확히 3개 `stage`, 공식 Nav2 Path 52 pose와 RViz subscriber 1개씩, 비용지도 장애물/복귀 및 WSLg NVIDIA GLX renderer. `P2_L2_SMOKE_RC=0`, 원샷 `run_rc=0`, 상위 `first_failure=NONE`.
- **판정:** 이 증거만으로 **Owner WSL2 NO_GOAL GUI 자동 사전검증의 실패 경계가 해소되었음**을 인정. 현장 화면 픽셀 정상 여부 및 실제 Moving Goal 안전 검증은 아직 인정하지 않음.

## 3. 상위 PASS와 모순돼 보이는 진단 로그를 숨기지 않음

### (a) GUI watcher 단독 `rc=3`

`native/d07_gui_watcher_started.txt`에는 `2026-11-18T04:58:38Z` 시작 ACK가 있음. `native/d07_gui_watcher_exit.txt`에는 `rc=3`, `2026-11-18T05:00:00Z`. watcher 로그 마지막에 `D07_H01_GUI_CHILD_TERMINATED_BEFORE_PHASE_COMPLETE first_exit_rc=0` 기록.

정확한 고정 Student 소스 `tools/d07_h01_gpu_gui_watcher.sh`는 `wait -n "$gz_pid" "$rviz_pid"`에서 **첫 GUI child 종료가 일어나면 원인 구별 없이 `exit 3`**을 호출한다. 반면 부모 `scripts/p2_no_goal_smoke_ci.sh`는 geometry 검증 뒤 `exit 0` 시 소유 세션에 SIGINT 종료를 요청하고, child watcher의 종료 코드는 `wait ... || true`로 흡수한다. 실제 상위 `gui_run.log`에는 `D07_H01_GUI_H01_GEOMETRY_RETURNED_NO_GOAL` → `P2_L2_SMOKE_RC=0`, shutdown 증거에는 `P2_L2_GRACEFUL_TEARDOWN`.

**해석:** 이는 이번 NO_GOAL 경로의 상위 성공을 뒤집는 *시나리오 미달* 증거는 아님. 시나리오 종료 시 정상적인 GUI child 종료가 watcher의 generic `exit 3`을 유발했을 가능성이 높다. 단, watcher 파일만으로 SIGINT의 정확한 선후관계를 확증할 수 없어 **WATCHER_EXIT_AFTER_SCENARIO=DIAGNOSTIC_AMBIGUITY**로 남긴다. Moving Goal L3의 shutdown clean PASS로 사용하지 않는다. 새로운 범용 watchdog 개발로 확대하지 않는다.

### (b) 3D 화면 관련 RViz/OGRE 렌더링 경고

`native/d07_gui_watcher.log`에 RViz `GLSL link result: active samplers with a different type refer to the same texture image unit` 오류가 있고, 보존한 WSLg `ogre2` 로그에는 `Fixed Function pipeline is no longer allowed nor supported` 예외가 있음. 동시에 Gazebo GUI MinimalScene/scene creation 및 RViz OpenGL 4.6/2개 X11 창, 실제 DDS Path subscription은 확인됨.

**해석:** 3D 모델/지도/경로가 사람이 보는 화면에서 올바르게 렌더링되었다는 직접 픽셀/스크린샷 증거는 **없음**. GLX 선택 성공과 X11 창 검출만으로 시각 품질까지 PASS라고 판정하면 안 됨. 현장 화면이 검은 화면/누락으로 관찰된다면 **최초 렌더링 오류를 별도 단일 회귀**로 다루고, 문제가 없는 경우 기존 성공을 보존하여 MVP Goal 인수로 진행한다.

### (c) NO_GOAL 충돌 및 안전 시간 계약

`contact_native_metadata`는 `NATIVE_CONTACT_TYPE_ADVERTISED_ONLY_NO_GOAL`, `contact_ground_truth_ready=false`; `goal_sent=false`, `motion_admitted=false`, `formal_accepted=false`. 이 원본은 **Contact0를 증명하지 않고**, CM source/Observer 120ms·Guard age150ms·Scan/Odom/Clock300ms 주기·Goal CANCELED·Navigation/Localization 종료 ACK·SQLite14를 실제 움직임에서 시험하지 않음. 이 항목은 이전 Task03의 한 실행에서 검증한 증거를 보존하되 Owner L3로 옮겨 주장하지 않는다.

## 4. 추적 가능한 변경 파일·브랜치·Git 커밋

- 공개 CI 저장소: `silverbjin/axia-robot-safety-ci-public`
- 개발 브랜치: `fix/g07-task04-owner-wsl2-public-pregate-20261118`; [Draft PR #169](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/169)
- 최초 계측·사전검증 실행기: `scripts/axia_g07_task04_public_owner_wsl2_pregate_once.sh` (현재 실제 Owner 실행은 immutable `5bb0cd720...` 사용)
- 현장 실패 재현: `tests/fixtures/g07_task04_owner_wsl2_first_failure_20261118.json`, `tests/test_g07_task04_owner_field_regression_20261118.py`
- 최초 RED/GREEN L0: `.github/workflows/axia-g07-task04-owner-wsl2-pregate-public-l0-20261118.yml`
- 실제 native Xvfb L2: `.github/workflows/axia-g07-task04-public-native-gui-xvfb-l2-20261118.yml`
- producer schema 회귀: `tests/test_g07_task04_native_path_stage_schema.py`
- 기존 교육 RCA: `docs/operations/AXIA_G07_TASK04_WSL2_GUI_FIRST_FAILURE_RCA_20261118_KO.md`
- public-unit 격리 보고서: `docs/operations/AXIA_G07_TASK04_SCHEMA_PUBLIC_UNIT_ISOLATION_RED_GREEN_20261118_KO.md`
- 이번 현장 인수 보고서: **본 파일**, 증거 ZIP 자체는 공개 Git에 없음
- 원본 Student 수정 **없음**, 공식 Nav2 fork **없음**, CI Goal 권한 위장 **없음**, 안전 TTL/정지 zone 완화 **없음**, private Instructor/CI **미사용**, **main 미병합**.

## 5. 다음 원래 MVP 복귀 작업 — Task04 Owner Moving Goal L3만 남김

**즉시 복귀 목표: WSL2에서 정확히 한 번의 안전한 Gazebo Moving Goal L3 최종 인수.** 반복되는 NO_GOAL 검사·성공한 공개 Task03 L2를 다시 개발하지 않는다.

1. **시각 검토 게이트:** 강사 화면의 Waffle/월드/RViz Path/Costmap이 실제로 보이는지만 확인. 미확인이거나 오류가 보이면 위 GLSL/OGRE 로그의 최초 실패 경계에 한정하여 공개 CI 회귀 후 최소 수정. 시각 문제가 없다면 추가 GUI 개발 생략.
2. **Owner 정식 Goal 권한 경로를 공개 CI 개발 브랜치에서 최소 구현:** Student 기존 실제 Goal·CM·Guard·ordered shutdown 코드를 재사용하되, Owner WSL2 **controlling TTY 승인**, 정확 Student SHA, 목표 UUID, 사전 부팅/물리 배치 ACK, 실제 소유 PID·프로세스 그룹, 원시 증거·SHA custody. `GITHUB_ACTIONS=true` 위조·CI-only Goal 플래그 우회·global `pkill` 금지. 승인 없는 Goal 전송은 fail closed.
3. **공개 CI RED→GREEN 및 실제 Gazebo L2 범위 선언:** 최초 현장 오류 경계의 계약을 CI에 편입. 실제 Moving Goal 단일 Run에서 CLEAR→SLOW→STOP/zero odom dwell≥1.0s, 대상 S02 native Contact=0, CM publisher+observer 각≤120ms, Guard CM age≤150ms **첫 비영속도 이후**, Scan/Odom/Clock≤300ms, 정확 UUID ActionStatus5=CANCELED, 14개 SQLite 토픽+SHA, Navigation/Localization ACK, CM child clean exit, 최초 실패 없음. **성공한 이전 Run을 합쳐 PASS 합성하지 않는다.**
4. **강사 WSL2 L3 원샷 1회:** GitHub 공개 브랜치의 immutable SHA에서 실행기를 내려받아 한 번 실행하며, 증거 archive 1개·SHA256·최종 판정 자동 생성. 실제 화면과 물리 장애물/로봇 움직임도 육안 확인. 미검증 항목은 HOLD 유지하고 재발한 첫 안전 전이/첫 timing 위반만 대상으로 회귀.
5. **최종 승인:** `AXIA_MVP_DEMO_ACCEPTED`는 실제 현장 조건과 모든 필수 안전 시간 경계가 확인된 경우에만 PASS 후보로 변경. 강사·학생 정답 분리 및 SW 정지≠인증 E-Stop 유지. `main` 병합은 사용자의 별도 명시 승인 후 수행.

## 6. 교육용 한 페이지 결론

**증상** `RViz Path subscriber absent` → **원본 추적** 파티션에 `ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST`가 들어간 비정상 값, watcher 원본 누락 → **재현 테스트** 동일 Bash `$_` 확장 → **원인 확정** 환경변수 마지막 인수 오염 → **최소 수정** `BASHPID` + 파티션 검증 + watcher ACK/로그 → **다음 실패 분리** 실제 native GUI는 rc0, CI 후처리만 `phase/stage` mismatch → **후처리 회귀 수정** → **별개 CI checkout 단언 실패 정리** → **공개 CI 실제 L2 PASS** → **이번 Owner WSL2 증거 73/73·59/59, Nav2 3단계 DDS, native runtime rc0, NONE**.

이번 결과의 정확한 문구는 **`AXIA_G07_TASK04_OWNER_WSL2_GUI_NO_GOAL_AUTOMATED_PREGATE_PASS`**이며 **`AXIA_G07_TASK04_OWNER_MOVING_L3=NOT_RUN`** 및 **`AXIA_MVP_DEMO_ACCEPTED=HOLD`**가 동시 참이다.

## 7. 후속 현장 육안 검수 종결 (2026-11-18, 본 문서의 당초 PENDING 판정 이후)

**최신 판정:** \`AXIA_G07_TASK04_OWNER_WSL2_GUI_NO_GOAL_VISUAL_ACCEPTED=PASS_SCOPED\`입니다. 당초 본문에서 \`VISUAL_CONTENT_REVIEW_PENDING\`이라고 기록한 것은 **이전 스냅샷 시점의 사실**이며, 사용자가 추가로 제출한 실제 Gazebo/RViz 화면과 직접 육안 검수로 해당 항목이 해소되었습니다.

- 이미지 파일 SHA256 \`46f9d35283f7164f6724226a6b82542350bad222a8e65ea320adc37d073716c2\`.
- RViz 화면에서 \`Global Status: Ok\`, 표시된 Costmap·official Path, LaserScan/TF/Odometry 항목 확인. Gazebo 화면에서 3D 월드·장애물·바닥 grid 확인. 두 창 동시 표시.
- 기존 Owner 자동 PASS의 73/73, 59/59, native 세 단계 Path/DDS subscriber 1개씩, \`run_rc=0\`, \`FIRST_FAILURE=NONE\`와 모순 없음.
- 기존 GLSL/OGRE 경고는 별도 보존. 이 한 화면은 전체 장시간 GPU 안정성·모든 shader·Moving Goal의 물리 충돌 및 안전 TTL을 증명하지 않습니다.
- **원래 MVP 복귀:** NO_GOAL GUI 디버깅 종료. Task04 **Owner Moving Goal L3**의 안전 인수 경로만 최소 개발·공개 CI 검증·강사 WSL2 실제 인수.
- 전체 \`AXIA_MVP_DEMO_ACCEPTED=HOLD\`; \`CERTIFIED_ESTOP=false\`; \`main\` 미병합.

[별도 최종 시각 인수 증거·MVP 복귀 보고서](./AXIA_G07_TASK04_OWNER_NO_GOAL_GUI_VISUAL_FINAL_ACCEPTANCE_20261118_KO.md)
