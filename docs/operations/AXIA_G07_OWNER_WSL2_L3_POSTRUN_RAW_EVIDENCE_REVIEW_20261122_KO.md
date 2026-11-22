# AXIA G07 — 강사 WSL2 L3 실제 원본 사후 검수 보고서

검수일 2026-11-22 KST. 검수 방법: 사용자가 제출한 Owner WSL2 원본 TAR, compact ZIP, 각 .sha256 대조; 내부 해시 일치; JSON/로그 및 rosbag SQLite 실제 조회. **사용자 현장 실행은 이미 종료되었으며 ChatGPT가 그 환경을 직접 원격 제어해 실행한 것은 아니다.**

## 1. 핵심 결론과 정확한 판정 범위

- **L3_OWNER_NUMERIC_AND_LIFECYCLE_RAW_REVIEW=PASS_SCOPED**: 실제 강사 WSL2 실행 증거에서 동일 소스, 실제 이동 Goal, CLEAR→SLOW→STOP, exact UUID cancel, 1.026s odom ZERO dwell, 필수 안전 수신 TTL, Nav/Localization ACK, CM+Supervisor+Guard 포함 모든 21개 Launch 프로세스 정상 종료가 확인된다.
- 사용자는 본 검증이 **완료되었다고 직접 보고**했다. 원본 기록의 `gui_windows.txt`는 `rviz=1 gazebo=1`이며, GUI 프로세스/창 관측은 독립 확인. **실제 창의 시각적 콘텐츠(화면 캡처/영상)는 업로드되지 않아 독립 검수 불가**. 운영자 시각 확인과 시스템이 증명한 창 개수를 서로 혼동하지 않는다.
- 자동 생성 `task04_owner_verdict.json`의 `status=HOLD_RAW_REVIEW_AND_VISUAL_PENDING`, `owner_moving_l3_accepted=false`, `axia_mvp_demo_accepted=false`, `formal_safety_timing_accepted=false`는 당시 자동 실행기가 의도적으로 남긴 **사후 검수 전 보수적 레이블**이며 원본을 수정하거나 `PASS`로 바꾸지 않는다. **이 문서는 별도의 수동 RAW/운영자 완료 보고에 근거한 scoped 인수 검토 결과**이다.
- `native_shutdown_verdict.json`의 `native_actual_gazebo_exit0_proven=false`는 compact exporter의 미검증 상태. 실제 전체 `native/launch.log`에는 Gazebo `gz-4`, Nav2, CM, Guard/Supervisor 모두 `process has finished cleanly`가 **21개** 있다. `process has died`, `Traceback`, context invalid 메시지 모두 0. 실제 `native/g07_ordered_shutdown.json` Nav/Loc ACK true, `native/g07_shutdown_audit.json` CM exit_code 0. 따라서 **원본 종료 검수에서 정상 종료 확인**, compact 판정 필드는 그대로 둔다.
- 기존 실 CI 엄격 Native **2/2 PASS**: https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44965035965 (2026-11-22). 이는 별개 Public L2, 여기서는 동일 소스 실제 강사 WSL2 L3 1회 실행만 판정한다.
- 인증된 하드웨어 E-Stop 미검증; `certified_estop=false`; FastDDS 300–400ms 간헐 수신 지연 근본원인 `UNDETERMINED`. 신규 성능·안전 하드웨어 인증 주장 금지.

## 2. SHA 고정과 파일 검증 (공개 안전 숫자만)

- 실제 Student SHA: `f7edb2d126502eeeed58ae014adadc7a2096d41b`.
- 실제 Public 소스 검토 SHA: `64ba0161e66126b4743b4b12a859f4a5349ae58a`.
- 실제 Public Native L2 Run `44965035965`은 Cycle1/Cycle2 모두 success. Owner WSL2 `manifest.txt`, `source_sha.txt` 및 `task04_owner_numeric_review.json` 일치.
- Owner 원본 `owner-moving-u88ZXW8W.tar.gz`: SHA256 `1a5450a44aaee0852a4841b57fbb0a81541d3490eb53559172479d3924ff222f`; 외부 .sha256 일치, gzip/tar 무결성 PASS, `SHA256SUMS` **102/102** 일치, `native/SHA256SUMS` **76/76** 일치.
- `owner-moving-u88ZXW8W.diagnostics.zip`: SHA256 `02ecf321b1fa9fa8bd7453324029161a4b9beb82a37d68f08150e74dc7048087`; 외부 .sha256 일치, ZIP CRC 무결성 PASS, ZIP 내부 `SHA256SUMS` **31/31** 일치.
- ZIP은 진단 간추림 자료이며 원본 로컬 rosbag, GUI 이미지·원본 ROS 이벤트를 대체하지 않는다. **TAR/ZIP 원본을 GitHub 공개 저장소에 업로드하지 않았다.**

## 3. 실제 스코프별 안전 수치 (원본 `ci_moving_goal_result.json`)

| 검증 | WSL2 실측 | 기준 | 판정 |
| --- | ---: | ---: | --- |
| /scan callback max | 215.082877ms | 300ms 진단 + Sensor header/watchdog 불변 | PASS, 첫 간격 위반 null |
| /clock callback max | 95.138822ms | <300ms | PASS |
| /odom callback max | 149.593842ms | <300ms | PASS |
| /cmd_vel_pre_guard CM max | 71.460029ms | <120ms | PASS |
| CM source max | 60.080298ms | <120ms | PASS |
| Guard status callback max | 80.750400ms | <150ms | PASS |
| Supervisor status callback max | 68.610875ms | <150ms | PASS |
| 실제 Guard 내부 CM age max | **49.279328ms** | <150ms | PASS |
| Odom 실이동 | **0.129946523m** | 이동 >0.12m | PASS |
| Odom ZERO dwell | **1.026194649초** | >=1초 | PASS |
| Guard 예상 외 latch | false | 없어야 함 | PASS |
| 충돌 Contact 카운트 | 0 | 0 | PASS, 이번 세션에서 Positive Calibration은 수행하지 않음 |

물리 한 시나리오 출력: CLEAR front=2.048107m, CM vx=0.062925m/s, BaseGuard final vx=0.037684m/s; SLOW front=0.674758m, CM vx=0.004810m/s, final vx=0.003422m/s; STOP front=0.396788m, CM vx=0.0m/s, final vx=0.0m/s. **Goal 취소 ACK/종결 status=5** 같은 Goal UUID `11e4c440bcf64405958c9dbbcdaaa9be`. `native/g07_ci_moving.log`와 raw JSON 일치. `task04_owner_verdict.json`의 **20/20 필수 `native_checks=true`**와 독립 대조.

## 4. ROS2/Gazebo 실행·원본 rosbag·종료

- 프리Goal `native/g07_ci_scan_pregoal.json`: real /scan 및 /safety/scan 각 117 samples; wall max 128.822593/128.796592ms, header Sim gap 102ms; Clock max10.843725ms, Odom max62.427026ms, RTF 추정 0.984375; 첫 위반 없음.
- `native/rosbag2/rosbag2_0.db3`: SQLite 원본을 직접 조회해 **14개 토픽·총 54,641개 메시지** 검증, `task04_owner_numeric_review.json` 14개 topic counts와 모두 완전히 일치. `/scan` 1055, `/safety/scan` 1051, `/odom` 2928, `/cmd_vel_pre_guard` 313, `/axia/p2/base_guard` 2172, `/clock` 35140. SQLite SHA256 `09066e1fe45488b796f2a9e535b9231fd80dae80115e848070cee75e4f886461`은 report와 일치.
- `native/g07_ordered_shutdown.json`: Navigation ACK true (3.156094s), Localization ACK true (0.330114s), 실제 RMW `rmw_fastrtps_cpp`. `native/g07_shutdown_audit.json`: CM exit_code=0. `native/teardown.txt`: `P2_L2_GRACEFUL_TEARDOWN`.
- `native/launch.log`: Gazebo `gz-4`, Nav2 lifecycle managers, planner/controller/velocity_smoother, Collision Monitor, Supervisor, BaseGuard, Injector 등 **총 21개 Process `finished cleanly`**, crash/traceback/rcl context-invalid 0. `native_runner.log`: `P2_L2_SMOKE_RC=0`.
- `gui_windows.txt`: RViz=1, Gazebo=1; `native/g07_gui_diagnostic.txt`: BOTH_CLIENTS_STARTED, GUI diagnostic-only. 창이 열렸다는 증거는 화면 안 시나리오를 촬영·판독한 증거와 다르다.
- `native_depth_absence` 및 `g07_demo_waffle_manifest`: 10Hz LiDAR, session-only Depth OFF, 공식 모델 원본 유지.

## 5. 남겨둔 미검증 및 승인 범위

- Native CI에서 통과한 **특정 2주기**와 WSL2 Owner에서 통과한 **한 주기**에 한정된 교육용 Safety MVP 시연이며, 모든 WSL2/GPU 환경의 장기 반복 안정성은 검증하지 않았다.
- FastDDS/RMW 최초 지연 근본 원인, Gazebo native→bridge→원 Subscriber 최초 packet 세그먼트는 `NOT_MEASURED/ROOT_UNDETERMINED`; 정상 시연에 최초 위반이 없었으므로 원인 입증했다고 보고하지 않는다.
- `native_contact_positive_calibration_this_run=false`; 이전 성공된 positive contact calibration을 재수행하지 않았고 이번 세션은 contact=0만 검증.
- 자동 `owner_moving_l3_accepted=false`를 억지로 바꾸지 않음. 사용자 완료 선언 + 이 사후 RAW 직접 검사 + 실제 실행 수치에서 **WSL2 L3 교육용 MVP scoped numerical/lifecycle acceptance 조건 충족**으로 기록하되, 독립 시각 화면 내용 검수는 미실시라고 명기한다.
- Instructor 비공개 정답/Student TODO 유지, Main 브랜치 병합 없음. 사용자 명시 승인 후에만 병합한다.

## 6. 최종 상태

`PUBLIC_L2=2_OF_2_PASS`; `OWNER_L3_RAW_NUMERIC=PASS_SCOPED`; `OWNER_L3_ACTUAL_ROS_GAZEBO=YES`; `OWNER_L3_LIFECYCLE=PASS_RAW_21_CLEAN_EXIT`; `OPERATOR_REPORTED_VALIDATION_COMPLETE=true`; `INDEPENDENT_GUI_CONTENT_REVIEW=NOT_PROVIDED`; `FORMAL_AUTOMATED_VERDICT=HOLD_RAW_REVIEW_AND_VISUAL_PENDING_PRESERVED`; `ROOT_CAUSE_RMW=UNDETERMINED`; `CERTIFIED_ESTOP=false`; `MAIN=NOT_MERGED`.

검토자 판단: **기존 AXIA G07 교육용 MVP의 신규 SHA는 주어진 공개 Native 2/2 및 WSL2 1회 안전/Goal/Shutdown 수치 인수 범위 충족**. 새로운 기능 구현·성능/DDL 변경·현장 추가 반복 없이 동결 가능. 전체 아카이브 원본은 사용자 로컬/제출 첨부에 보존.
