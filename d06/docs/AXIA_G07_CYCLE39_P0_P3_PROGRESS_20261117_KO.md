# Cycle39 범위 동결 최종 종료 판정 — 2026-11-17

**이 절은 아래의 기존 P0~P3 개발 기록보다 우선하는 최종 범위 결정이다.** 아래 과거 기록의 '신규 L2/검사기'는 종료된 실험 개발 이력이며 현재 출고 필수 조건이 아니다.

## 변경 전 승인 계획
- 선행 계획: [AXIA_G07_C39_SCOPE_FREEZE_PLAN_20261117_KO.md](AXIA_G07_C39_SCOPE_FREEZE_PLAN_20261117_KO.md); 계획 commit `7e3690f8ae50f8152d83f3093c62f93a23f7b06f`.
- 대상: 공개 Draft PR [#136](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/136), `fix/g07-cycle39-rviz-scan-timing-20261117` → `fix/g07-cycle38-d07-wslg-gpu-xcb-capture-20261117`. C38 성공 증거, G07 주행/CM/TTL 기준 원본 보존.
- 실제 최종 목표: P0 RViz 보조화면 설정 + P1 교육용 front_distance 0..2π wrap 수정만 보존. P1 물리 원통 기하 검증·P2 clock 분류기·실험용 L2는 범위 밖.

## RED → GREEN → REFACTOR → REVIEW → COMMIT 결과
| 단계 | 공개 증거 및 결과 |
|---|---|
| RED | 기존 불변 C38 소스 `c4dca31b210d28037116e49fe39d8d0b5aebdc34`에 범위 축소 4개 회귀 적용. **2건 실패 예상/검증**: TF arrows 표시, 전방 2π 경계 거리 |
| GREEN | [Public L0 Run #43975995004](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43975995004) `completed/success`, Git SHA `5e99bd4afcc7f055b90623401143e844d5d1c8bc` |
| REFACTOR | `d06/live/d06_readonly_monitor.py`에는 wrapped front angle diff만 보존. 추가한 네 가지 stamp/logging 필드 삭제. 기하 판정기·clock 진단기·Cycle39 전용 Gazebo L2 workflow를 Draft PR에서 삭제 |
| REVIEW | 실제 PR diff: 안전 제어 관련 소스 변경 0건. 변경 소스는 `d06/live/d06_readonly_monitor.py`의 전방 angle wrap과 `d06/rviz/d06_safety_bubble.rviz`의 표시 설정뿐. 새로운 Goal/cmd_vel publisher 0 |
| COMMIT | 범위 축소를 각 파일별로 커밋했고 다음에 최종 결과 문서만 커밋. Draft 상태 유지; main 미병합 |

## 실제 공개 CI 로그 발췌
```text
AXIA_G07_C39_SCOPED_RED_TWO_ORIGINAL_FAILURES_CONFIRMED
test_front_wrap_includes_both_sides_of_2pi ... ok
test_invalid_scan_stays_unknown ... ok
test_monitor_publishes_only_educational_markers ... ok
test_rviz_clarity_preserves_readonly_frame_and_scan ... ok
Ran 4 tests in 0.007s
OK
AXIA_G07_C39_MVP_SCOPED_PUBLIC_L0_PASS_4_OF_4_NO_ROS_NO_GOAL
AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false
```
최초 RED 단계의 작업 완료 결과는 기존 코드 두 개 실패 판정 확인이다. GREEN은 ROS/Gazebo 없는 단위·정적 L0 결과이며 실제 Gazebo 신동작 검증을 뜻하지 않는다.

## 남긴 경로
- `d06/rviz/d06_safety_bubble.rviz`: `TF Show Arrows=false`, Marker Scale 축소, 카메라 시점 조정. LaserScan=`/scan`, Fixed Frame=`odom`, RobotModel off.
- `d06/live/d06_readonly_monitor.py`: front angle wrap 수정만 유지, 공식 CM 정책·안전 기능 변경 0.
- `d06/tests/test_g07_cycle39_display_scan_timing.py`: 교육용 표시+전방 검출+UNKNOWN+읽기 전용 publisher 검증 4개.
- `.github/workflows/axia-g07-cycle39-display-scan-l0.yml`: 공개 RED 2/GREEN 4 최소 계약.
- 계획/보고 문서는 추적·교육용으로 보존.

## 제거한 경로
- Draft PR #136: `d06/live/g07_cycle39_scan_geometry.py`, `d06/live/g07_cycle39_scan_timing.py`, `.github/workflows/axia-g07-cycle39-gazebo-scan-snapshot-l2.yml` 모두 제거.
- 임시 공개 release 브랜치 `release/p2-g06-cm-ttl-20261110`에 추가했던 위 Cycle39 L2 workflow도 **그 파일만** 삭제, cleanup commit `68742938e68e6f9e1151bd07563d44f004c6a89c`. 원래 Cycle38 real Gazebo L2 workflow는 그대로 존재함을 재조회 확인.

## 보존 및 미인수 판정
- 이전 C38 Owner WSLg GUI-only 화면 실측 성공은 그대로 인정하며 현장 재실행하지 않았다.
- 변경된 C39 RViz 개선본의 WSLg 시각 확인은 **NOT_RUN**. 실제 source/bridge/supervisor scan 전달주기·물리 Geometry 완전 일치도 **UNVERIFIED**; 이번 GUI-only 배포 필수 요구로 확대하지 않는다.
- G07 Moving Goal 통합 인수는 원본 CM native RMW source gap `128.644215ms >120ms` 릴리스 마진 때문에 **HOLD**. 원래 `150ms` TTL 위반 자체의 확증은 아님. 해당 원인·실제 안전 계층의 통합 L2/Owner 인수는 **별도 G07 작업**.
- 이 작업에서 새 ROS 실행/Gazebo L2/Owner WSL2/Goal 실행은 하지 않았으며 실제 성공 보고 금지.
- 강사 비공개 정답·학생 저장소 및 main 병합 없음. 소프트웨어 정지를 인증 E-Stop으로 설명하지 않음.

```text
AXIA_G07_C39_SCOPE_FREEZE=COMPLETE
AXIA_G07_C39_PUBLIC_L0_RED=2_EXPECTED_FAILURES_PROVEN
AXIA_G07_C39_PUBLIC_L0_GREEN=PASS_4_OF_4
AXIA_G07_C39_NEW_GAZEBO_L2=NOT_RUN_AFTER_SCOPE_FREEZE
AXIA_G07_C39_NEW_OWNER_WSLG=NOT_RUN
AXIA_G07_MOVING_GOAL_L3=HOLD
CM_120MS_RELEASE=HOLD
AXIA_MVP_DEMO_ACCEPTED=HOLD
CERTIFIED_ESTOP=false
MAIN_MERGED=false
```

---

# AXIA G07 Cycle39 — P0→P3 증거·개발·최초 경계 보고 (2026-11-17)

## 기준선 및 범위
- Owner Cycle38 실측 GUI PASS: ZIP `axia_g07_c38_gui_evidence_cVOAPhet.tar.gz`, SHA256 `e4975c17da1b84f9658846589150ca138ab428d8ed13b4efec1f1679cd4ad70b`. 내부 29/29 체크섬 일치. `GUI_ONLY_EXIT_RC=0`, 원본 관찰 `YES-G07-GUI-VISIBLE`.
- 실제 ROS2 Jazzy/Gazebo Harmonic Waffle + Xvfb 두 GUI 선행 L2 [#43905300294](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43905300294) 성공. **새 Scan 형상·TTL·Owner Moving Goal의 합격 증거 아님.**
- 별도 공개 저장소 후보 브랜치: `fix/g07-cycle39-rviz-scan-timing-20261117` (기준 `c4dca31b210d28037116e49fe39d8d0b5aebdc34`), Draft [PR #136](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/136). 메인 및 강사 비공개 정답/학생 저장소 미수정.
- 안전상 금지: 원본 CM, Guard, Supervisor, 공식 Nav2 및 TTL 기준 변경 금지. 정식 인증 E-Stop 주장 금지. Owner Goal 재시도 반복 금지.

## P0 — 표시-only 변경
- `d06/rviz/d06_safety_bubble.rviz`: TF Show Arrows=true→false, Marker Scale .45→.22, Orbit Distance 4.6→4.2, Pitch .9→1.05, Yaw .8→0.0.
- 유지: LaserScan `/scan`, Fixed Frame `odom`, Target Frame `base_footprint`, RobotModel `Enabled=false`. Gazebo 원래 3D 메시를 RViz에서 동일하게 그린다는 주장은 하지 않음.
- P0 구현 커밋: `62ae93f62831896a3381646f0daa56b45fab5ae2`.
- 실제 WSLg 새 화면: **NOT RUN after this change**.

## P1 — 2D LaserScan 형상 후보와 동시각 실측
- 원본 Waffle `gpu_lidar`: 360 샘플, 0~6.28rad, Gazebo sim-time 10Hz. 원본 전방 거리 교육 관찰기 `abs(angle)<=0.18`는 2π 부근 전방 절반을 배제할 수 있어 `atan2(sin(angle),cos(angle))` wrap으로 변경.
- `d06/live/d06_readonly_monitor.py` 변경 커밋 `7f82fb35707572a3034eaf520d32a506effe14a2`.
- `d06/live/g07_cycle39_scan_geometry.py`: same-stamp world→scan pose, scan frame, 실제 원통 collision 반경을 입력으로 계산하는 fail-closed 2D ray/circle witness. **synthetic unit only**. 다른 월드 물체가 먼저 광선을 막는 경우는 즉시 물리 오류로 단정 금지.
- G07 정적 원통: center=(-0.58,-0.5), z=[0.00,0.48]m, radius=.07m; 정확한 로봇 세계좌표·동일 시각 TF·전체 ranges가 기존 Owner ZIP에 없어서 기하 일치는 `UNVERIFIED`.
- geometry 커밋 `283246e50fb6cd6dcead0242c841b040f5ae0803`.
- 새 Gazebo 캡처 CI는 원본 ROS `/scan`, `/tf`, native Gazebo `/world/default/pose/info`를 증거로 수집하나, 단순 개별 snapshot은 **동일 시각 정합을 증명하지 않음**.

## P2 — Scan 데이터 전달 주기 최초 위반 후보
- 원본 읽기 전용 관찰기 236 scans / 53.47 wall s, 최초 interarrival >.3s = `0.4107s`, max sampled age `0.3489s`. Sim sensor 설정 10Hz와 wall observer 4.41Hz는 RTF 미검증 상태에서 비교 불가.
- 읽기 전용 `d06_readonly_monitor.py`에 `scan_header_stamp_sim_s`, `scan_header_delta_sim_s`, `scan_interarrival_wall_s`, `scan_frame_id` 4개 증거 필드를 추가. 신규 제어 publisher 0. 신규 safety node 0.
- `d06/live/g07_cycle39_scan_timing.py`에서는 source/bridge/supervisor wall-clock gap을 **동일한 검증된 clock domain**에서 전달해야만 증거 분류. 원본 observer 0.4107s만으로 `Guard 300ms TTL breached` 판정 **금지**. 진단 코드 커밋 `4851f69c92b4fb928d60608b57078eafe8a6ada7`.
- **미검증:** Gazebo 발행 wall period, ROS bridge wall receive, Supervisor 실제 subscription period, 첫 safety transition. 현장 410.7ms는 observation-only 경고이며 safety acceptance로 승격 금지.

## P0/P1/P2 공개 CI 및 RED→GREEN 근거
- 회귀 RED 요구사항 커밋: `600cfe21a6b03ee53957b17059f2c689671b3e58`. 실제 공개 [RED→GREEN Run #43916055772](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43916055772): 기존 불변 기준선 `c4dca31...` 테스트 **RED = 2 failures + 5 errors / 총 9건**(TF Show Arrows=true, 0..2π sample 1.8≠0.45, 새 기하/타이밍 모듈 없음). 같은 Job의 변경 소스 **GREEN = 9/9 PASS**. 실제 출력 `AXIA_G07_C39_ACTUAL_RED_BASELINE_REPLAY_CONFIRMED_NO_ROS_NO_GOAL` 및 `AXIA_G07_C39_P0_P1_P2_PUBLIC_L0_PASS_NO_ROS_NO_GOAL_NO_L3`. RED는 안전 제어 실행이 아닌 L0 소스 회귀.
- 공개 L0 [Run #43914494204](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43914494204) `completed/success`: 실제 출력 `Ran 9 tests in 0.010s\nOK\nAXIA_G07_C39_P0_P1_P2_PUBLIC_L0_PASS_NO_ROS_NO_GOAL_NO_L3`. P0 표시, 0/2π wrap, negative-π regression, geometry synthetic, no-TF UNVERIFIED, observer-only timing, clock mismatch tests.
- 공개 PR 기반 L2 [Run #43914494162](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43914494162) `completed/failure`. Job step list empty; 로그 조회 오류 BlobNotFound. **실제 Gazebo 소스 실패인지 environment/runner admission인지 현 단계에서 원인 확정 금지**.
- 공개 release CI에서 기존 성공한 `axia-instructor-sealed` 경로 재사용: `release/p2-g06-cm-ttl-20261110` workflow-only commit `fdae0206b34807d358f41213046791eebe0a78b1`. 정확한 변경 소스 `4851f69c92b4fb928d60608b57078eafe8a6ada7` pin; 새 L2 실측 판정은 **재조회 필요**. 성공 전 Owner rollout 금지.
- 교차 검증 수준: Public L0 RED→GREEN replay 및 9/9 PASS; actual new Gazebo P1/P2 L2 NOT VERIFIED; Owner new RViz NOT RUN.

## P3 — 기존 CM 120ms 릴리스 마진 별도 HOLD
- 실제 Moving Goal CI [Run #43898345608](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43898345608): 최초 native RMW source gap `128.644215ms`, observer callback gap `128.318661ms`; `120ms` release criterion FAIL (단, 이 관측만으로 원본 `150ms` TTL violation이라고 단정 금지).
- upstream Supervisor publications inside source gap=2; scheduler sample coverage=51.212ms, samples=2, host clock step excluded=false; `FIRST_CM_120MS_GAP_SCHEDULER_VS_EXECUTION_UNDETERMINED` 그대로.
- 필요한 최소 다음 계측: 첫 source→CM callback entry/exit→RMW emit→Guard receive의 **같은 실행** timestamp/counter와 scheduler coverage. 한 원인을 바꾸면 Scan/Guard 타이밍 경계 함께 확인. 차단된 field 동일 오류 반복 금지.
- CM/Guard/TTL/CPU-affinity 임의 튜닝 및 새 ROS/Gazebo Goal 실행: 이번 cycle **NOT RUN**.

## 다음 실행 게이트
1. 공개 release L2의 정확한 Run ID, 최초 실패/성공 원본 증거를 확인한다. FAIL이면 가장 앞선 실패만 재현·수정하고 RED→GREEN.
2. 새 real /scan/TF/native pose의 time/frame 정합이 충족되기 전까지 `SCAN_WORLD_GEOMETRY_CONSISTENCY=UNVERIFIED`.
3. source/bridge/Supervisor 연결 주기를 입증하기 전까지 `SCAN_GUARD_TTL=UNVERIFIED`.
4. GUI-only WSLg 원샷 업데이트와 Owner 1회 검수는 공개 CI GREEN 이후. Goal은 별도의 승인/120ms 게이트 전까지 금지.
5. main 병합은 Owner 승인 이전 금지.

```
AXIA_G07_C39_PUBLIC_L0=PASS_9_OF_9
AXIA_G07_C39_NEW_REAL_GAZEBO_L2=HOLD
AXIA_G07_C39_NEW_OWNER_WSLG=NOT_RUN
SCAN_WORLD_GEOMETRY_CONSISTENCY=UNVERIFIED
SCAN_GUARD_TTL=UNVERIFIED
CM_120MS_RELEASE=HOLD
AXIA_MVP_DEMO_ACCEPTED=HOLD
CERTIFIED_ESTOP=false
MAIN_MERGED=false
```
