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
- 회귀 RED 요구사항 커밋: `600cfe21a6b03ee53957b17059f2c689671b3e58`. 당시 소스에서는 TF Arrow OFF 기대 불충족, 0..2π wrap sample 불충족, 새 검증 모듈 부재(예상 RED); **별도 RED Actions verdict는 확보하지 않음**.
- 공개 L0 [Run #43914494204](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43914494204) `completed/success`: 실제 출력 `Ran 9 tests in 0.010s\nOK\nAXIA_G07_C39_P0_P1_P2_PUBLIC_L0_PASS_NO_ROS_NO_GOAL_NO_L3`. P0 표시, 0/2π wrap, negative-π regression, geometry synthetic, no-TF UNVERIFIED, observer-only timing, clock mismatch tests.
- 공개 PR 기반 L2 [Run #43914494162](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43914494162) `completed/failure`. Job step list empty; 로그 조회 오류 BlobNotFound. **실제 Gazebo 소스 실패인지 environment/runner admission인지 현 단계에서 원인 확정 금지**.
- 공개 release CI에서 기존 성공한 `axia-instructor-sealed` 경로 재사용: `release/p2-g06-cm-ttl-20261110` workflow-only commit `fdae0206b34807d358f41213046791eebe0a78b1`. 정확한 변경 소스 `4851f69c92b4fb928d60608b57078eafe8a6ada7` pin; 새 L2 실측 판정은 **재조회 필요**. 성공 전 Owner rollout 금지.
- 교차 검증 수준: Public L0 9/9 PASS; actual new Gazebo P1/P2 L2 NOT VERIFIED; Owner new RViz NOT RUN.

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
