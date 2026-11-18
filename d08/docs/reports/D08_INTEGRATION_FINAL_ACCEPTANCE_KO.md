# AXIA D08 — 교육용 NO_GOAL 센서·CM 설정·공식 Nav2 경로 통합 최종 L2 검증 및 L3 인수 대기

문서 상태: **실제 단일 World 공개 CI L2 PASS / Owner WSL2·WSLg 시각 L3 NOT_RUN / MOVING 별도 HOLD**  
검증 기준일: 2026-11-18 (KST). 본 보고서는 안전 인증이나 실제 주행 성공을 선언하지 않습니다.

## Git·소스·원본 인수 증거
| 저장소 | 대상 PR·개발 브랜치 | 코드/문서 HEAD 및 상태 |
|---|---|---|
| [Public CI #166](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/166) | `feat/d08-unified-sensor-cm-path-20261118` | 검증된 정확한 코드 SHA `a83629edd71ce51567e184451f2a76bafcf1318b`, main 병합 **NO** |
| [Student #43](https://github.com/silverbjin/axia-robot-safety-student/pull/43) | `feat/d08-integrated-no-goal-live-20261118` | 문서 커밋 `2db53d55c4f3640e0fb5d73c94f21fc4a512bf04`, main 병합 **NO** |
| Instructor 비공개 #212 | `docs/d08-unified-teacher-guide-20261118` | 강사 문서 HEAD `61dc409a55529108e2a64aecc9ba793522ec7810`, main 병합 **NO** |

원격 main (이번 조사): Public `62e366b51c64da25ad0216328fe1e019b78e0bef`, Student `bacd7d318f0703ba725fa7e3998a2df0d099ccfb`, Instructor `17cf4c023c82a641f586a8c527e5f8f9d5b456e4`. Student/Instructor main은 브랜치 기준선 이후 전진했지만 PR mergeable=true이며 사용자 승인 없이는 병합 금지.

- **최종 실제 L2**: [Public CI #44248098353](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44248098353), 결론 **SUCCESS**, Actions `pull_request` 실제 checkout/source SHA=`a83629edd71ce51567e184451f2a76bafcf1318b`(PR source HEAD와 동일), L0 **103 passed in 0.33s**, Gazebo sensor L2 SUCCESS, independent original YOLO replay L1 SUCCESS, 같은 World real YOLO+D05+CM native config+Nav2 3 Path L2 SUCCESS.
- 원본 보존: `d08-same-world-live-person-range-cm-nav2-evidence` GitHub Actions artifact **#14402713171**, `d08-main-real-no-goal-evidence` #14401709534, `d08-ui9-public-yolo-ros-replay-l1` #14402658330. 수명 7일. 이 보고서의 수치는 정확히 #44248098353의 원본 JSON/로그로만 구성했습니다.
- `runtime_provenance.json`: World=`default`, Waffle=`axia_d08_ci_waffle`, 실제 한 사람형 물리 Proxy=`axia_p2_g07_obstacle`, ROS_DOMAIN_ID=69, GZ_PARTITION=`axia_d08_ci_12494`, World SDF SHA256 `d70a7773cf13c5ea5678279e36ef719603010fefe9cce90761ddd06b8131a461`.

## Task별 판정
| Task | 실제 완료 범위 | 증거 수준·판정 |
|---|---|---|
| 00 | 단일 Gazebo World/Waffle/사람형 collision Proxy, 등록 RGB-D + LaserScan + 원본 SHA/TF/Clock | 공개 실제 L2 **PASS** |
| 01 | 같은 실행의 원본 C++ YOLO DetectionArray + 실제 RGB/Depth ROI median: 서로 다른 2 VALID와 사람 유실 1 UNKNOWN | 공개 실제 L2 **PASS** |
| 02 | 실제 `/scan`→공식 Global Costmap→공식 `ComputePathToPose` before/intrusion/restored; 공식 CM의 **native lifecycle ACTIVE + configured /scan source** 직접 서비스 조회 | 공개 실제 L2 **PASS (교육 NO_GOAL 범위 한정)** |
| 03 | G07 Moving Goal/실제 감속·정지·우회·Guard strict 타이밍·Goal terminal/Contact 동일 Run | **HOLD_G07_DEPENDENCY** |
| 04 | 공통 Public 정확한 SHA 원샷·공식 RViz Path read-only overlay·Student TODO/강사 비공개 가이드/보고서 | L0 및 headless L2 **PASS**, Owner WSLg L3 **NOT_RUN** |

### 원본 실제 관측값
- D05 `farther`: 사람 world (-1.20,-0.50,0.24)m, 실제 Scan **0.786540m**, 등록 Depth ROI **0.704022m VALID**, bbox 높이216px, RGB/Depth/YOLO 원본 stamp 일치 **25.200s**.
- D05 `stop`: 사람 world (-1.63,-0.50,0.24)m, 실제 Scan **0.356777m**, Depth ROI **0.534589m VALID**, bbox 높이80px, 세 입력 stamp **30.801s**. 두 median 방향·거리 차이 **0.16943m ≥ 0.12m**. 이 값은 LiDAR와 카메라가 절대적으로 같은 원점에 있다는 증거가 아니며 YOLO 사람이 CM에 직접 연결된 것도 아닙니다.
- D05 `unknown`: 실제 DetectionArray에는 person class가 없고 `NO_PERSON_CLASS_IN_ACTUAL_YOLO`(stamp **34.401s**). UNKNOWN≠CLEAR≠이동 허가. 원본 RGB PPM, 16개 실측 Depth ROI, stamps/SHA256SUMS 보존.
- 공식 Nav2 Path `before/intrusion/restored`: 실측 Scan **1.866673→0.567960→1.869093m**; Costmap lethal cell **0→66→0**; 원본 Path↔person 최소거리 **0.017043→0.325266→0.032872m**. 원본 `path_phases.jsonl` stamp/TF/좌표 출처로 검증. 이는 *계획 결과*이며 로봇이 해당 경로를 주행했다는 증거가 아닙니다.
- D08 read-only observer 실제 Scan callback sample **60**, 최대 host 수신 gap **0.228737s**(500ms 상한 이내), 최초 >500ms gap 없음. **CM의 내부 RMW-source gap 수치가 아닙니다.**
- 공식 CM 실제 ROS2 `/collision_monitor/get_state` 응답 `active`, `/collision_monitor/get_parameters` 응답 `observation_sources=["scan"]`, `scan.topic="scan"`; 원본 `official_cm_active_scan_configured=true`. ROS graph 단독 discovery `official_cm_scan_subscription_discovered=false`는 노드 이름 탐색 한계로 분리 기록. **CM 내부 rx gap, CM action state 및 Guard age는 false/NOT_VERIFIED**.
- `verdict.json`: `goal_sent=false`, `cmd_vel_published=false`, `certified_estop=false`; 실제 Waffle 속도 감속/Stop/No Contact drive는 시험하지 않았습니다.

## RED → GREEN → REFACTOR → REVIEW → COMMIT 핵심 과정 (교육용)
1. 초기 실제 Depth 거리 불일치 #44229304083에서 bbox 상단 부분 검출·거리 방향 역전을 발견 → 원본 RGB+16 Depth 샘플 보존, far 단계 1개 물리 후보 최소 조정 → #44236129868 two VALID+UNKNOWN L2 PASS.
2. 정지 로봇 AMCL one-shot Pose와 실시간 TF 동시-age 부적절한 가정 #44231766775 → 공식 Jazzy AMCL source와 최초 Pose/TF 분리 → real AMCL L2 GREEN.
3. GUI Path 표시 추가 후 ROS `Path` vs `pathlib.Path` 네임 충돌 #44239202179 → 별칭 `NavPath`와 RViz 공식 Path 토픽 overlay만 수정 → #44243971341 real Nav2 3 phase L2 GREEN.
4. PR 임시 merge SHA와 Owner PR HEAD의 불일치, GUI 반복 실패 후 이전 PASS 보존 가능성 RED #44245418250 → 정확한 checkout SHA + BLOCKED fail-closed 계약 → #44245796892 actual exact source L2 GREEN.
5. CM Scan graph에서 이름 미식별/구독자 이름 없는 증거 #44245796892 → **CM 실제 native 상태·파라미터를 읽기 전용 서비스로 조회**하는 RED [#44247821804](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44247821804) → GREEN [#44248098353](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44248098353). CM 내부 타이밍을 가짜 PASS로 치환하지 않았습니다.

소스 변경 경계: `d08/harness/d08_same_world_replan.py`, `d08/harness/d08_live_person_range*.py`, `d08/harness/d08_amcl_initial_pose.py`, `d08/harness/d08_one_world_official_nav2_launch.py`, `d08/scripts/d08_public_gazebo_l2.py`, `d08/scripts/d08_owner_no_goal_bootstrap.sh`, `.github/workflows/d08-main-no-goal-real-gazebo-l2.yml`; 공식 Nav2, CM, YOLO 엔진, Planner, Controller는 수정·재구현하지 않았습니다.

## 실제 명령 및 남은 인수
```bash
# 공개 CI 내부 원본 ROS 2 Jazzy/Gazebo Harmonic + pinned original yolo_ros 실행 중
python3 -u d08/scripts/d08_public_gazebo_l2.py \
  --actor /tmp/axia-d08-live-assets/walk.dae \
  --out results/d08-live-person-nav2-e2e \
  --official-nav2 --official-path-phases --live-person-range
```
Owner WSL2 원샷은 정확한 검증 코드 SHA `a83629edd71ce51567e184451f2a76bafcf1318b`를 `curl -fL` 후 `bash -n`, `--self-check`, `--doctor`, `--run`을 차례대로 한 블록에서 수행합니다. Student `block_B/day08/D08_UNIFIED_NO_GOAL_CLASSROOM_GUIDE_20261118_KO.md` 제7절과 private Instructor `training/block_B/instructor/D08_UNIFIED_NO_GOAL_INSTRUCTOR_GUIDE_20261118_KO.md` v0.2에 동일 명령이 기재돼 있습니다. 현장 WSLg Gazebo·RViz 실제 픽셀/화면/종료는 **NOT_RUN**. 헤드리스 Xvfb L2 SUCCESS는 WSLg 픽셀 인증이 아닙니다.

## 인수 문자열 (위에 근거 있는 판정만)
```text
D08_UNIFIED_PLAN_COMMITTED=YES
D08_TASK00_BASELINE_VERIFIED=PASS
D08_TASK01_PERSON_RANGE=PASS
D08_TASK02_NO_GOAL_SAME_WORLD=PASS
D08_TASK04_PUBLIC_CI_RELEASE_CANDIDATE=PASS
D08_LIVE_NO_GOAL_ACCEPTED=NO
D08_MOVING_E2E_ACCEPTED=HOLD
D08_OWNER_WSLG_VISUAL=NOT_RUN
D08_PUBLIC_CI_EXACT_SHA=a83629edd71ce51567e184451f2a76bafcf1318b
D08_STUDENT_MAIN_MERGED=NO
D08_INSTRUCTOR_MAIN_MERGED=NO
D08_PUBLIC_CI_MAIN_MERGED=NO
```
다음 사용자 개입은 **WSL2/WSLg 1회 시연 인수**와 **각 저장소 main 병합 승인**에 한정합니다. 최초 현장 오류가 발생하면 원본 trace/로그와 최초 상태 전이를 공개 CI 최소 회귀 RED로 편입한 후 재인수하고 동일 오류의 무작정 현장 재실행을 금지합니다.
