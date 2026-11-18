# AXIA D08 — NO_GOAL 교육 시연 MVP 기능 완료 검토

**기준일:** 2026-11-18 KST. **원칙:** 교육용 NO_GOAL의 기능 완료와 제품 안전/운영/종료 최종 인수를 분리한다. 이 문서는 코드 변경이나 CI PASS 승격을 지시하지 않는다.

## 원본 증거

- 강사 WSL2 실행 소스 SHA: `342c6355b27af5b8b11a79b7e345820be18a581f`.
- `run_20261118T141633Z_OgyMwe.diagnostics.zip` SHA256 `f0f46d773eb6bbf1460ea623269df88a1a61b1a6d1fd899f12d7bed5ccd628d1`. 원본 `SHA256SUMS` 30/30 PASS.
- 실제 Gazebo world `READY` (2.886s), Waffle+사람 native Scene, RGB-D 640×480, Scan/Odom/Clock, AMCL/TF2 map→base_link, 공식 Nav2 `ComputePathToPose`, 장애물 before/intrusion/restored 세 단계, YOLO+D05 거리 VALID 약 0.704m/0.535m 및 UNKNOWN.
- 현장 실물 시뮬레이션에서 `D08_OWNER_GUI_REAL_OFFICIAL_PATH_CYCLE_PASS` **1~6회 성공**. 7번째 진행 중 Ctrl+C. `goal_sent=false`, `cmd_vel_published=false`, 인증 E-Stop 아님.
- 공개 CI 고정 소스 Run [#44310101993](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44310101993) 4 jobs SUCCESS.
- **반례 보존:** docs-only HEAD `58c085cc7766d6bbc82b28a3f60ce50f70245c46`의 Run [#44312306299](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44312306299)에서 같은 실제 Nav2 L2는 8회 반복 도중 `D08_FIRST_REAL_SCAN_RECEIVE_GAP_OVER_500MS`, **0.505365s** 발생으로 FAIL. GREEN 일부만 추려 전체 반복 안전성을 주장하지 않는다.

## 판정

| 항목 | 상태 | 이유 |
| --- | --- | --- |
| **D08 교육용 NO_GOAL 기능 구현** | **완료** | WSL2 실제 Scene/센서/AMCL/Path/YOLO+D05 및 연속 6회 시연 |
| 강사 통제하 제한적 교육 시연 | **조건부 가능** | 사용자 육안 GUI 픽셀 확인, 실측 500ms 수신 한도 감시, 실패 시 중단을 전제로 함 |
| D08 Owner L3 최종 인수 / 반복 시연 안정성 | **HOLD** | 원본 `verdict.json:BLOCKED`; Ctrl+C RCLError, Gazebo -11; 최근 공개 CI Scan 505.365ms |
| AXIA Robot Safety **제품 전체 MVP 인수** | **이 문서 범위 밖** | 안전 TTL·Goal·Guard/CM 최종 제어 성능/인증 E-Stop 미검증 |

### 최종 미검증

- 현장 종료 후 `rcl_shutdown already called`, Executor Destroyable callback 경합, Gazebo SIGSEGV -11, Nav2 Exit 1. 단순 종료 경고로 무시하지 않는다.
- `official_cm_active_scan_configured=true`는 CM 스캔 토픽 및 lifecycle 설정 확인이지 **안전 상태 전이·실제 정지·CM 내부 수신 TTL 검증**이 아니다.
- 실제 GUI 픽셀은 `gui_pixels_verified=false`, WSLg 전 구간 RTF는 사용자의 약 70~80% 관찰 외 자동 측정 없음. AMCL 짧은 구간 Clock RTF 0.9092는 전체 RTF 아님.
- `AXIA_Robot_Safety_MVP_Baseline_Scenario_Acceptance_v1_KO.md` 본문은 이번 대조에서 접근되지 않았으므로 정식 기준선의 모든 조항을 확인했다는 주장은 하지 않음.

### 기능 동결 제안

D08 NO_GOAL 교육 시연의 구조와 기능은 **기능 동결**한다. Goal/실제 주행·새 Planner·인증 E-Stop으로 범위를 확대하지 않는다. 강사가 화면의 Waffle/사람/Path를 직접 확인하며 제한적 시연을 진행할 수 있으나, 교육용 제한을 고지하고 안전 수신 위반 시 실패로 중단한다. 정식 학생 배포·무인 시연 및 최종 안전 인수 PASS 승격은 보류한다.

**후속 개선**은 [AXIA_D08_POST_MVP_STABILITY_PERFORMANCE_BACKLOG_20261118_KO.md](AXIA_D08_POST_MVP_STABILITY_PERFORMANCE_BACKLOG_20261118_KO.md)에서 별도 관리하며 본 기능 완료 판단을 임의 취소하거나 과장하지 않는다.

```text
D08_NO_GOAL_FUNCTIONAL_MVP=COMPLETE
D08_INSTRUCTOR_CONTROLLED_DEMO=CONDITIONALLY_FEASIBLE
D08_OWNER_L3_FINAL_ACCEPTANCE=HOLD
D08_SAFETY_TTL_END_TO_END=NOT_VERIFIED
AXIA_MVP_DEMO_ACCEPTED=HOLD
CERTIFIED_ESTOP=false
MAIN_MERGED=false
```
