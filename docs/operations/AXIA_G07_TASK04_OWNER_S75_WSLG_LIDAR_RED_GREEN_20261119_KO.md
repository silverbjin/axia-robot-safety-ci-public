# AXIA G07 Task04 — S75 현장 GPU LiDAR 근거리 환영(의심)·최초 안전 전이·RENDERER PARITY RED→GREEN

2026-11-19 KST · 공개 CI PR #169 / Student PR #46 · *시뮬레이션 전용*, 인증 E-Stop 아님.

## 1. 원본 확보와 SHA256

강사 제공 `owner-moving-S75nb4Eh.tar.gz`의 SHA256: `74b421838d7d04da64a2da574aea0f77a31c28a7e6097b1f85d9d139dd6d2376`.
소형 `owner-moving-S75nb4Eh.diagnostics.zip`의 SHA256: `a5aac7562c68a23d893766a867c71c5d60e0895e4a99143d061c2893b987ab3b`.
두 압축파일 모두 사용자 제공 체크섬과 직접 재계산한 SHA256이 일치했다. **원본 TAR·SQLite는 공개 저장소에 올리지 않았다.** 이번 보고서의 수치는 실제 사용자 제출 14-topic rosbag/진단 JSON에서 계산한 비식별화 요약이다.

소스: 이전 Owner Student `ef6ffe58ddacb89ed37b225279f8e86453cf82b7`, domain 86, GZ partition `axia_p2_task04_86_2431_1795021173`.
25개 공식 패키지 버전과 5개 공식 파일 SHA는 Owner parity `CORE_PARITY_PASS`; 이는 GPU/WSLg/커널 동등성을 의미하지 않는다.

## 2. 최초 실패와 데이터 경로

- FIRST 오류: `OWNER_PREGOAL_NOT_CLEAR_BEFORE_FIXTURE`. 최상위 `NATIVE_RUNNER_FAILED_REVIEW_RAW`는 **2차 래퍼 결과**이며 근본 실패가 아니다.
- baseline SIM stamp `34.101`, `/safety/scan` front `0.5384279489517212m` (기준 `>0.75m`), side `0.6263315677642822m` (기준 `>1.20m`): fail-closed `BLOCKED`. `/scan`에서도 동일 거리, frame `base_scan`.
- **bag 전체의 `/scan` 377개와 `/safety/scan` 377개는 각 메시지의 CDR 원본 바이트까지 377/377 동일**. 경로상 Fault Injector가 새 거리값을 합성했다는 증거는 없으며, Gazebo `gpu_lidar`/브리지부터 수치가 생성됐다.
- 실제 Gazebo `gz model --pose` 조회: Waffle `(-2.000520,-0.500000,0.010007)`, yaw 약 0; preloaded cylinder `(-0.580000,-0.500000,0.240000)`, 반경 `0.07m`. 중심거리 `1.42m`. **이 원통 하나는 360도 0.5m 링 전체를 설명하지 못한다.**
- 실제 ROS bag에서 sim `0.006s`에 0.4~0.7m 광선 `177/360`, sim `0.102s`에 `353/360`, sim `37.602s`에 `353/360`. 약 `37.6` sim s 동안 근거리 환형 응답이 지속. **원본 물리 월드 형상과 센서 드라이버의 최종 구분은 미확정**.
- Nav2 Goal `0`, `/cmd_vel_pre_guard` 비영 속도 `0/174`, `/cmd_vel_supervised` 비영 속도 `0/1277`, 실제 이동 0. 최초 차단은 목표 전송을 막는 안전 동작이다.

## 3. 최초 안전 전이와 타이밍

- Supervisor state는 처음부터 `BOOT_SAFE`. 최초 건강 이탈 `SCAN_TIMEOUT` → 정상 Scan 후 `BOOT_SAFE / HEALTH_OK`; 이후 호스트 수신 시각 `1795021312.979`에 `BOOT_HEALTH_BAD / SCAN_TIMEOUT`, `1795021313.080`에 복귀. 전 구간 `BOOT_SAFE` 유지, 안전 FSM이 주행상태로 승격된 증거 없음.
- Guard `NO_FRESH_PAIR`→`FORWARDING_MONITORED_CM`→`NO_FRESH_PAIR`을 반복했으며 `latched=false`; Goal 없이 유효한 명령은 0.
- ROS bag **호스트 timestamp** 최대 격차: `/scan=4444.76ms`, `/clock=4317.66ms`, `/odom=4351.29ms`, `/axia/p2/base_guard=4365.41ms`. 최대 /scan 호스트 격차 동안 sim stamp는 `10.002→10.101s`로 `0.099s`만 진행. WSL2 스케줄러/렌더링/시뮬레이션 지연 여부를 별도로 판별해야 하며, 이 사실만으로 물리 안전 TTL 수치를 PASS 처리하지 않는다.
- 해당 현장 실패는 주행 Goal 전 검사에서 발생했으므로 **120ms CM 전송·150ms Guard·300ms Scan/Odom/Clock 전계층 주행 안정성은 해당 Owner 세션에서 미검증**.

## 4. 단일 재현 가능 가설 및 공식 근거

**차이**: 기존 공개 성공 [#44344038055](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44344038055)는 Gazebo 센서 서버를 `LIBGL_ALWAYS_SOFTWARE=1`로 구동했고, 기존 Owner Student shell은 `OWNER_MOVING`에서 이를 `unset`해 Mesa D3D12/WSLg 렌더러로 동작시켰다. 실제 현장 GLX는 `Microsoft Corporation / D3D12 (NVIDIA GeForce RTX 2060 with Max-Q Design)`. 패키지·SDF·TF 설정을 무작정 변경하지 않고 **센서 렌더러 parity를 첫 가설**로 채택한다.

Gazebo 공식 Harmonic troubleshooting: https://gazebosim.org/docs/harmonic/troubleshooting/ (OpenGL/가상화 문제의 소프트웨어 렌더링 대안).
유관 원인 범주의 공식 이슈: https://github.com/gazebosim/gz-sensors/issues/504 및 https://github.com/gazebosim/gz-rendering/issues/662. **해당 이슈가 이번 0.5m 수치의 동일 원인을 직접 증명한 것은 아니다.**

## 5. RED→GREEN→REFACTOR→REVIEW→COMMIT

### RED — 실제 공개 CI
- Student 새 L0: `block_B/day07/h01_runtime/tools/test_g07_task04_owner_sensor_renderer_parity.py`, RED 테스트 커밋 `0913440c83ea251bd4b7e1304b0ca3ec92afdd4a`.
- 공개 CI [#44356202944](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44356202944) **FAIL(의도한 L0)**: Owner 센서 서버 소프트웨어 렌더러/GUI 독립성 2건 불충족. 실제 Gazebo는 L0 실패로 SKIPPED.
- 추가 Owner 최종 오류 전파 RED [#44357055395](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44357055395): 외부 래퍼가 최초 PREGOAL 실패를 덮는 결함.

### GREEN — 최소 수정 후 공개 검증
- Student 소스 GREEN `725b6168b381554e29add26e0dcc85a0e2fce8e7`: `scripts/p2_no_goal_smoke_ci.sh`의 Owner/Moving 조건에서 Gazebo/ROS launch 환경 `LIBGL_ALWAYS_SOFTWARE=1`을 명시하고 D3D12·adapter 변수는 서버에 전달하지 않는다. 오직 `gz sim -g` / `rviz2` GUI 자식만 `env -u LIBGL_ALWAYS_SOFTWARE GALLIUM_DRIVER=d3d12 ...`로 GPU를 이용한다. 정지 거리/CM/TTL, Nav2, 공식 Waffle/월드 원본은 **그대로**.
- 공개 실제 Gazebo No-Goal [#44356630025](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44356630025) **SUCCESS**, 동일 Student SHA, `/safety/scan` front `1.4256961345672607m`, side `2.5276055335998535m`, `first_failure=NONE`, `goal_sent=false`; 이후 기존 원통 set_pose ACK + 새 실제 LaserScan 검증.
- 공개 실제 Gazebo+RViz Moving Goal [#44356618739](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44356618739) **SUCCESS**, 원샷 `rc=0`, `RVIZ_X11=1`, `GAZEBO_X11=1`, 동일 Student SHA, 상태 `TASK04_REAL_GAZEBO_MOVING_GUI_L2_SCOPED_PASS`. 원본 수치 아티팩트 [#14452776963](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44356618739/artifacts/14452776963) SHA256 JSON `5d9885f5f0f847b37502556a1e388d9620b50cfe052c6bb65da7ee2807a65d2f`.
- 실제 Moving 세션 21/21 checks TRUE: `odom_moved_m=0.19725068658952746`, `stopped_dwell_sec=1.0111256630000298`, `native_contact_count=0` (`26033` witness iterations), Goal UUID `6ef4be38cf124959aa668f625655d4d2` 정확 취소. CM source gap `56.416857ms`/120, observer gap `67.261442ms`/120, Guard internal age `24.373515ms`/150, Scan/Odom/Clock 각 300ms, SQLite 14 topics, Lifecycle Nav/Loc ACK와 CM clean exit, first_timing_violation_none.
- 외부 실패 메시지 GREEN: `scripts/axia_g07_task04_owner_moving_l3_once.sh`가 실패 시 먼저 `native/g07_ci_pregoal/pregoal_baseline.json`의 `first_failure`를 확인하고 검증된 `OWNER_PREGOAL_*` 코드를 보존. [Bootstrap L0 #44357221355](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44357221355) 성공.
- 최종 Runner pin: Student `725b6168...`; CI source `99ddd89758...`; native L2 run `44356618739`; 마지막 공개 Bootstrap L0 [#44357547131](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44357547131) **SUCCESS**.

### REFACTOR / REVIEW
렌더러 설정/최초 실패 전파만 국소 변경; 새 Planner/Supervisor/Fault Injector 구현 없음. 스캔 거리 임계값 `front>0.75m`, `side>1.20m`·CM120/Guard150/Scan300 등 안전 계약 불변. 공개 정적 테스트는 실제 센서 측정의 대용이 아니라 실제 L2의 사전조건. 원본 bag/소스 전체를 GitHub Actions 아티팩트로 외부 배포하지 않음.

## 6. 검증 수준 및 인수 HOLD

```ini
OWNER_FIELD_OLD_L3=BLOCKED_FIRST_PREGOAL
PUBLIC_CI_L0=PASS_AFTER_RED_GREEN
PUBLIC_CI_REAL_GAZEBO_NO_GOAL_L2=PASS
PUBLIC_CI_REAL_MOVING_GOAL_GUI_XVFB_L2=PASS_21_OF_21
OWNER_WSL2_NEW_RUNNER_L3=NOT_RUN
OWNER_WSLG_LIDAR_RENDER_FIX=HYPOTHESIS_PENDING_L3
OWNER_TIMING_4S_STALL=UNRESOLVED
AXIA_MVP_DEMO_ACCEPTED=HOLD
CERTIFIED_ESTOP=false
MAIN_MERGED=false
```

**남은 유일한 현장 검수**: 고정 공개 Owner 원샷으로 동일 강사 WSL2에서 한 번 실행하고, 주행 화면·LiDAR baseline·최초 상태/타이밍·1초 stop dwell·실제 Goal UUID 취소·CM/Guard end-to-end 안전 TTL·shutdown·원본 증거 SHA를 동일 세션으로 검수한다. 새 실패면 같은 현장 재실행부터 하지 않고 첫 실패/최초 타이밍 위반을 좁혀 공개 CI RED 회귀로 되돌린다. Main 병합은 별도 승인까지 금지.
