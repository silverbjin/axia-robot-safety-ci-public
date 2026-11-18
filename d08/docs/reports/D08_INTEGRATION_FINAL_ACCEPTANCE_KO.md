# AXIA D08 — 통합 인수 현황 / Owner L3 전 출고 HOLD (2026-11-18)

## 판정 및 출처
- Public CI 개발 브랜치 `feat/d08-unified-sensor-cm-path-20261118`, PR [#166](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/166), base main `62e366b51c64da25ad0216328fe1e019b78e0bef`, main 병합 NO.
- Student `feat/d08-integrated-no-goal-live-20261118` PR [#43](https://github.com/silverbjin/axia-robot-safety-student/pull/43) / Instructor private `docs/d08-unified-teacher-guide-20261118` PR [#212](https://github.com/silverbjin/axia-robot-safety-instructor/pull/212): main 병합 NO.
- 실제 [공개 Run #44245796892](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44245796892) **SUCCESS**, source SHA=GitHub Actions 실제 checkout SHA=`910d3a22291f0ab8a4585f8dab5501219408171b`, L0 `97 passed in 0.48s`; 원본 `d08-same-world-live-person-range-cm-nav2-evidence` artifact #14401772249 (보존 7일).
- World=`default`, SDF SHA256 `d70a7773cf13c5ea5678279e36ef719603010fefe9cce90761ddd06b8131a461`, Waffle=`axia_d08_ci_waffle`, human physical Proxy=`axia_p2_g07_obstacle`, ROS_DOMAIN_ID=69/GZ_PARTITION=`axia_d08_ci_12493`.

## 실증 범위
| Task | 실제 확인 | 범위 판정 |
|---|---|---|
| 00 | 공식 Waffle·한 Gazebo World·한 사람형 충돌 Proxy, source/clock/TF/Scan provenance | L2 PASS |
| 01 | 한 실행의 실제 RGB/Depth·원본 C++ YOLO+D05 Depth ROI VALID `0.704022m`, `0.534589m` (차이 `0.16943m` ≥0.12m), no-person UNKNOWN | L2 PASS |
| 02 | 실제 /scan, Costmap lethal `0→66→0`, 공식 ComputePathToPose before/intrusion/restored clearance `0.032872→0.334566→0.000266m`; observer Scan gap `0.220616s` (<0.5s) | 경로/센서 L2 PASS, **CM 직접 서비스 계측 PENDING** |
| 03 | G07 scoped public 숫자 PASS는 현재 D08 동일 moving world/E2E가 아니며, 별도 Goal/Contact/odom/Guard 인수 없음 | MOVING HOLD |
| 04 | 동일 Public Runner WSL2 원샷 --self-check/--doctor/--run, 공식 RViz Path 표시 overlay, Ctrl+C/소유 프로세스 종료, 학생 TODO·강사 private 분리 | L0 PASS/Owner WSLg L3 NOT_RUN |

### 최초 잔여 실패 경계
위 Run의 실제 ROS graph Scan 소비자 중 `_NODE_NAME_UNKNOWN_` 2개, `official_cm_scan_subscription_discovered=false`. 그러나 원본 `d08_official_nav2_one_world.log`에서 공식 CM은 실제 `[scan]: Creating Scan`/lifecycle `Activating`를 출력함. 이름 discovery 실패를 CM 데이터 수신 PASS라고 취급하지 않는다. 이번 최소 L0 RED→native `/collision_monitor/get_state`/ `get_parameters` GREEN→동일 SHA 실제 L2 검증 결과는 PR #166 댓글에 출처를 기록한다. 실제 CM 내부 RMW receive gap·Guard age·CM velocity/STOP 상태 출력은 NO_GOAL 시연에서 **NOT_VERIFIED/NOT_RUN**.

## 명령·증거
- 실제 L0: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q d08/tests/test_d08_task04_exact_sha_and_failclosed.py d08/tests/test_d08_task04_native_path_and_rviz.py`
- 실제 L2: `python3 -u d08/scripts/d08_public_gazebo_l2.py --actor /tmp/axia-d08-live-assets/walk.dae --out results/d08-live-person-nav2-e2e --official-nav2 --official-path-phases --live-person-range` (기존 pinned upstream yolo_ros가 동일 CI Job에서 실행 중이어야 함).
- 원본: `runtime_provenance.json`, `verdict.json`, `official_path_phases/path_phases.jsonl`, `live_person_range/{farther,stop,unknown}_live_d05.json`, native Gazebo/Nav2 logs, original RGB PPM + SHA256SUMS.
- WSL2/WSLg 실제 Gazebo/RViz 3D 픽셀은 아직 사용자 현장 L3를 실행하지 않았으므로 NOT_RUN. Xvfb/ROS L2 통과를 GUI 픽셀 PASS로 승격 금지.
- USER 승인 전 모든 저장소 main 병합 금지. SW Stop은 인증된 E-Stop이 아니다.

## 판정 문자열
```text
D08_UNIFIED_PLAN_COMMITTED=YES
D08_TASK00_BASELINE_VERIFIED=PASS
D08_TASK01_PERSON_RANGE=PASS
D08_TASK02_NO_GOAL_SAME_WORLD=HOLD_CM_DIRECT_PROOF
D08_LIVE_NO_GOAL_ACCEPTED=NO
D08_MOVING_E2E_ACCEPTED=HOLD
D08_OWNER_WSLG_VISUAL=NOT_RUN
D08_PUBLIC_CI_EXACT_SHA=910d3a22291f0ab8a4585f8dab5501219408171b
D08_STUDENT_MAIN_MERGED=NO
D08_INSTRUCTOR_MAIN_MERGED=NO
D08_PUBLIC_CI_MAIN_MERGED=NO
```
이 문서는 변경 소스 HEAD의 새 실제 CI 결과 전까지 합격을 선언하지 않는다. 최신 판정·커밋 SHA는 PR #166의 원본 실행 댓글을 우선 확인한다.
