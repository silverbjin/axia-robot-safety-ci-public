# AXIA G07 Task04 — 강사 WSL2/WSLg NO_GOAL GUI 최종 시각 인수

**판정일:** 2026-11-18 KST  
**저장소:** `silverbjin/axia-robot-safety-ci-public`, Draft PR [#169](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/169)  
**판정 범위:** `OWNER_WSL2_NO_GOAL_GUI_VISUAL_ACCEPTED=PASS_SCOPED`  
**제품 전체:** `AXIA_MVP_DEMO_ACCEPTED=HOLD` · `OWNER_MOVING_L3=NOT_RUN` · `CERTIFIED_ESTOP=false`  
**정책:** Student 원본·공식 Nav2·CM/Guard/TTL 변경 없음. private Instructor/CI 미사용. `main` 미병합.

## 1. 왜 지금 최종 GUI 인수 가능한가

기존 공개 CI의 실제 Gazebo+RViz Xvfb L2 [#44238643061](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44238643061)는 **WSLg GPU/사람이 보는 장면**을 확인하지 못했다. 이어 제출된 실제 강사 WSL2 NO_GOAL 원본 archive는 물리 월드와 공식 Nav2 Path 통합 및 X11 창을 확인했지만, 마지막에 `AXIA_G07_TASK04_VISUAL_CONTENT_REVIEW_PENDING=true`를 유지했다.

**새 증거:** 사용자가 2026-11-18 첨부한 정지 화면 `image(20261118-051749).png`와 **사용자의 직접 육안 확인 완료**를 인수 기록으로 받았다. 화면에는 다음 요소가 동시에 표시됨.

- **RViz2:** 왼쪽 Displays의 `Global Status: Ok`, Ground/TF/LaserScan/Odometry, `Official Global Costm...`, `Official ComputePath...` 항목, 표시된 다색 Costmap grid와 경로 선. 즉 Path/Costmap 화면 콘텐츠 자체가 존재함.
- **Gazebo Sim:** 세계 바닥 grid, 녹색 구조물/검은 벽·장애물 및 장면 렌더링. 창이 회색 빈 화면만 보였던 기존 실패 증상과 구별됨.
- **화면 배치:** RViz와 Gazebo가 동시 표시됨. 이미지의 오른쪽 하단에 약 82%의 Gazebo 실시간 비율 표시가 있지만 이는 **움직임의 안전성이나 CM/Guard 타이밍 증거가 아님**.

이로써 마지막 **화면 내용 존재/육안 확인 게이트**를 완료한다. 단일 정지 화면으로 기구학적 움직임, 시간에 따른 레이트, 서보 안전, 모든 3D shader 동작을 판정하지 않는다.

**스크린샷 원본 SHA256**: `46f9d35283f7164f6724226a6b82542350bad222a8e65ea320adc37d073716c2` (RGB PNG, 1861×868, 452665 bytes). 해당 이미지에는 현장 사용자 경로가 포함돼 있으므로 **공개 Git에는 이미지를 업로드하지 않고 SHA256·관찰 요약만 등록**한다. 업로드 원본은 이 대화에 보관된다.

## 2. 현장 자동 검사와 이미지 관찰을 교차 검증한 근거

이전 실제 Owner 원본 `owner-gui-pregate-lxXToFIk.tar.gz`와 별도 `.sha256` 파일은 직접 SHA256 대조 완료. 원본 tar SHA256:

```text
4e69c1a43f3623104da0425211dd2cd20c90c2d986750c66196ee397756defb2
```

- 압축 내부 `SHA256SUMS` **73/73 OK**, `native/SHA256SUMS` **59/59 OK**.
- 정확 Student SHA `01752add2e30c90c4d3286ef3a450f97746ecb55`; 공식 환경 패리티 **25 packages / 5 official files PASS**.
- `GZ_PARTITION=axia_p2_task04_86_11058_1794977846`: 인자 오염 및 비허용 문자 없음.
- `wslg_glxinfo_adapter_NVIDIA.txt`에서 NVIDIA RTX 2060 Max-Q **D3D12 OpenGL 4.6** 실제 GLX 렌더러 선택 확인.
- `window_status.txt`: `run_rc=0`, `rviz_window=1`, `gazebo_window=1`, `xwininfo_available=1`; `first_failure.txt=NONE`.
- `native/d07_h01_geometry/d07_h01_geometry.json`: `D07_H01_REAL_NAV2_GEOMETRY_READY_NO_GOAL`, `real_nav2=true`, `real_laser_scan=true`, `actual_costmap_obstacle_observed=true`, `path_changed=true`, `obstacle_restored_away=true`, `goal_sent=false`, `formal_accepted=false`.
- `native/d07_h01_geometry/phase_evidence.jsonl`: `stage=before/intrusion/restored` 세 행. 각 행의 공식 Path `pose_count=52`, RViz `rviz_subscription_count=1`, `goal_sent=false`, `robot_moved=false`. 3단계 실제 Costmap·Scan 시각 연계를 자동 검증한 증거.
- `native/teardown.txt`: `P2_L2_GRACEFUL_TEARDOWN`. 이 증거는 NO_GOAL world cleanup이며 Moving Goal의 Navigation/Localization Lifecycle ACK를 대체하지 않음.

### 잔존 렌더러 로그 해석

이전 원본의 RViz GLSL link 경고와 Gazebo OGRE fixed-function 메시지는 그대로 **원본에 보존**한다. 사용자가 제공한 화면에서는 Gazebo 3D 월드와 RViz Costmap/Path가 실제로 보이므로 **이번 교육 시연 범위에서는 화면 부재 BLOCKER가 아니다**. 그러나 스크린샷 외 모든 shader 패스나 장시간 GPU 안정성 전체를 PASS라고 선언하지 않는다.

Watcher가 `rc=3`으로 기록된 이력은 별도 분석 보고서처럼 종료 시 child `wait -n`와 상위 `run_rc=0`의 차이로 기록하고, 전체 안전 종료 L3로 승격하지 않는다. 현장 최초 실패/타이밍 위반이 재발하지 않는 한 watcher 구조를 확장 개발하지 않는다.

## 3. 과거 오류 → 검증 가능한 원인 → 최소 수정 → 이번 시각 PASS의 커밋 추적

| 단계 | 증거·커밋 | 결론과 한계 |
|---|---|---|
| NO_GOAL 실행기 RED | [`6cac07cb`](https://github.com/silverbjin/axia-robot-safety-ci-public/commit/6cac07cbf9dab75f3fd7db02c12bf0950798c18c), [Run #44232883070](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44232883070) | 공개 WSL2 사전 게이트 계약 부재 |
| 최초 실행기 GREEN | [`4db31c90`](https://github.com/silverbjin/axia-robot-safety-ci-public/commit/4db31c90afe568282bc9d49713e053bf70b43152), [Run #44233533697](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44233533697) | L0 4/4만 성공; 이후 이 SHA는 현장 버그로 폐기 |
| 원본 현장 첫 실패 고정 | [`f73ca3d8`](https://github.com/silverbjin/axia-robot-safety-ci-public/commit/f73ca3d885396cf360540bdaf74e57995c2461ff) | RViz Path 구독 부재와 손상된 `GZ_PARTITION`, watcher 로그 누락을 분리 |
| Bash `$_` 회귀 RED→GREEN | [`5a67bf09`](https://github.com/silverbjin/axia-robot-safety-ci-public/commit/5a67bf0974bfe2e3bce4c2037c94c4881a4715b2) → [`1a5334a4`](https://github.com/silverbjin/axia-robot-safety-ci-public/commit/1a5334a4de4f8126693c098aff1f7c47bdc1eebc), [#44237062643](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44237062643) → [#44237386904](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44237386904) | `$_`가 직전 export 인수를 붙여 partition 값을 오염시키는 현상 **직접 재현**. `BASHPID`와 fail-closed, watcher ACK/진단 증거 |
| 실제 Xvfb GUI L2 후처리 RED→GREEN | [`c0b90102`](https://github.com/silverbjin/axia-robot-safety-ci-public/commit/c0b9010235f2aa5d4fccde25217179d441ce598b) → [`5bb0cd72`](https://github.com/silverbjin/axia-robot-safety-ci-public/commit/5bb0cd72086f2f1a057f382649b773fff106f1f9), [#44237948105](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44237948105) → [#44238643061](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44238643061) | GUI 원본 rc0와 리뷰어 `phase`/producer `stage` mismatch 분리. 실제 공개 native Xvfb L2 성공 |
| 범용 unit checkout 레이아웃 실패 RED→GREEN | [`ef855371`](https://github.com/silverbjin/axia-robot-safety-ci-public/commit/ef855371ee4cfe2d6a30c092bb3b338dd631e5c3), [#44238649926](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44238649926) → [#44240074839](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44240074839) | CI unit checkout 없음과 native 원본 검사 분리, 228/228 PASS |
| 첫 실제 강사 WSL2 NO_GOAL 성공 | [원인 추적 보고서 `a8c6e161`](https://github.com/silverbjin/axia-robot-safety-ci-public/commit/a8c6e161a0c6c27ac477ade95074dfb42ffd9e6d) | archive 원본 무결성·실제 세 단계 Path DDS·X11 및 D3D12 확인; 육안은 당시 미결 |
| **이번 최종 시각 확인** | PNG SHA256 및 강사 육안 확인, **본 인수 문서** | Gazebo 장면·RViz Costmap/Path 존재 확인. 기존 `VISUAL_CONTENT_REVIEW_PENDING` 해제 |

오염된 `GZ_PARTITION`의 생성 원인은 직접 검증되었지만, 이것이 이전 RViz 구독 오류의 **유일한 인과 원인이라고 단정하지 않는다**. 현장 후속 정상 스크린샷과 공식 DDS 3단계 증거가 성공 복구를 지지한다.

## 4. 최종 범위 판정과 다음 MVP 작업

| Gate | 최종 상태 |
|---|---|
| Task01 최초 CM 퍼블리셔 gap root cause | 기존 증거 보존 |
| Task02 공개 저속 sim-only Simple TF | 기존 scoped L2 PASS 보존 |
| Task03 실제 공개 Gazebo Moving Goal L2 (#44223320904) | 기존 scoped PASS 보존 |
| Task04 실제 공개 Gazebo/RViz Xvfb NO_GOAL L2 | 기존 PASS 보존 |
| **Task04 강사 WSL2/WSLg NO_GOAL GUI 자동+육안 인수** | **PASS_SCOPED — 이번 최종 완료** |
| 강사 WSL2 실제 Moving Goal/동일 실행 안전 TTL+Contact0+SQLite14+종료 ACK | **NOT_RUN** |
| 실제 인증된 E-Stop | **NOT_CLAIMED** |
| 프로젝트 전체 `AXIA_MVP_DEMO_ACCEPTED` | **HOLD** |

**다음 개발 복귀 지점은 오직 Task04 Owner Moving Goal L3입니다.** Student 공식 Nav2·기존 Task03 CM/Guard/Goal·ordered shutdown을 재사용하며, 공개 CI에서 정확 Student SHA·Owner controlling TTY 승인·run-owned PID·일회 Goal UUID·fail-closed 증거 산출 경로만 최소 구현합니다. CI-only Goal 허가값을 Owner WSL2에서 위조하지 않습니다.

공개 CI RED→GREEN 뒤 실제 L2가 필요한 변경 범위를 검증하고, **강사 WSL2 한 번의 Moving Goal**에서 실제 FIRST 안전 전이·최초 TTL 위반 시점, CM source+observer 각각 ≤120ms, Guard 수신 age ≤150ms, Scan/Odom/Clock ≤300ms, CLEAR→SLOW→STOP, odom ZERO dwell ≥1초, S02 Contact=0, 목표 UUID CANCELED, SQLite14 quick_check/각 토픽 count/SHA256, Navigation+Localization Lifecycle ACK, CM clean exit를 모두 판정합니다. 이전 별개 Run의 성공을 합쳐 Owner PASS로 승격하지 않습니다.

**반복 금지:** 성공한 GUI/Task03를 재실행하거나 새로운 renderer/전역 GUI watchdog을 추가하지 않습니다. 만약 현장 Moving Goal에서 새로운 문제가 생기면 최초 실제 타이밍 경계/안전 상태 전이에 대한 최소 공개 CI RED→GREEN만 수행합니다.

```text
AXIA_G07_TASK04_OWNER_WSL2_GUI_NO_GOAL_AUTOMATED_PREGATE_PASS=true
AXIA_G07_TASK04_OWNER_WSL2_GUI_VISUAL_ACCEPTED=PASS_SCOPED
AXIA_G07_TASK04_OWNER_MOVING_L3=NOT_RUN
AXIA_MVP_DEMO_ACCEPTED=HOLD
CERTIFIED_ESTOP=false
MAIN_MERGED=false
```
