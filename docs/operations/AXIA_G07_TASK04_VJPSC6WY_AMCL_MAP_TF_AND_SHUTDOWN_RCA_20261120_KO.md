# AXIA G07 Task04 — vJpsc6Wy 실제 WSL2 첫 오류, AMCL→실제 TF 대체 경로 및 종료 회귀 분석

**작성:** 2026-11-20 KST  
**계약:** 교육용 기존 baseline `AXIA-G07-T04-DEMO-BASELINE-20261119-CZObXAdP` 유지. 본 현장 실행의 Goal 자체는 **실행되지 않았으므로 완료라고 승격하지 않음**. 고도화 안전 타이밍 별도, 인증 E-Stop `false`.

## 1. 현장 원본 SHA / 실행

- `owner-moving-vJpsc6Wy.tar.gz` SHA256 `1dfea580b4e95ac1bf4e02be42e47fc5dc742a3b0e2118e6069e0326df794591`
- `owner-moving-vJpsc6Wy.diagnostics.zip` SHA256 `27b9c837b9a7b0797aa92055ff04789abb86e5acf9536ee1bd06c0bf06c27106`
- 각 sidecar 검증 및 TAR/ZIP 내부 manifest 검증 완료. 원본 rosbag, 민감 경로/명령줄은 현장 비공개로 보존하고 공개 저장소에는 올리지 않음.
- 원래 Owner 고정 Student SHA `954fc2f054c50df783bc81c4d0835a6ee6f8645d`, Public wrapper `6cfe6a51102d9a45420fa4f9ad4e9600130a7c56`, CLEAN `ROS_DOMAIN_ID=46`.
- `native_witness_build_profile.json` **HIT / 0.012초**; 기록상 Owner runner start +9.220초, first RViz window +9.257초, first Gazebo window +107.089초. 주의: 전체 X11 tree 감지는 해당 세션의 고유 PID 증거가 아니므로 첫 RViz 탐지가 이 실행에 속한 창인지까지는 증명되지 않음.
- `/clock` rosbag CDR **33,500개, 역행 0회**: 이전 Domain=86 오염이 이번에는 없었다는 증거. Nav2 Localization+Navigation Lifecycle START 서비스 ACK, MapServer·AMCL ACTIVE, `/set_initial_pose` ACK, GUI `rviz=1,gazebo=1`.

## 2. 최초 실질 오류 / 최초 안전 상태

`native/g07_ci_moving/ci_moving_goal_result.json`:
```text
status=BLOCKED
first_failure_preserved=RuntimeError:G07_AMCL_MAP_POSE_UNAVAILABLE_BEFORE_GOAL
goal_sent=false
first_guard_latch=null
```

- `actual_ros_events.jsonl` 약 4초 Goal Observer 창: 28 Scan / 65 Odom / 454 Clock / 74 Guard / 70 Supervisor, **AMCL pose=0**.
- 최초 Guard reason `NO_FRESH_PAIR`, `latched=false` (Goal 전 준비 구간에서 Guard ZERO/미전달; 실제 latch 아님). Goal/cmd authorization 실패 또는 물리 Stop 시나리오 단계는 도달하지 않음.
- 원본 `native/rosbag2/rosbag2_0.db3`의 실제 TF: `map->odom` **832개**, `odom->base_footprint` **2,791개**, `/clock` 지속 증가. 따라서 지도 TF 전체가 없는 것이 아니라 **새 Goal Observer의 AMCL 위치 수신/3초 freshness 경계**가 첫 실패임.
- ROS Context 종료 단계: `native/launch.log` Guard와 Supervisor 각 `rclpy._rclpy_pybind11.RCLError: failed to initialize wait set: the given context is not valid` 및 child exit1. 상위 `P2_L2_GRACEFUL_TEARDOWN` 마커는 자식 종료 0을 증명하지 않음.
- 첫 AMCL Pose 설정시 약 21ms 미래 TF extrapolation 경고는 이후 MapServer·AMCL START ACK와 실제 TF가 있으므로 **첫 실패 자체로 간주하지 않음**.
- RViz2 `indexed_8bit_image.frag` GLSL shader warning은 UI 렌더링 별도 문제, 실제 스크린샷 품질 확인 전 정상 렌더링 PASS 주장 금지. 원본 RViz 경고는 교육용 증거로 보존.

## 3. RED→GREEN 및 최소 소스 수정

Student 기능 브랜치: `fix/g07-task04-owner-map-tf-and-clean-exit-20261120` [PR #69](https://github.com/silverbjin/axia-robot-safety-student/pull/69), 고정 HEAD `43a26a2f870c0fd99d66d06887cdf4e706b637b7`. `main` 기준 정확히 8파일 범위.

1. `block_B/day07/h01_runtime/tools/p2_l3_coordinate_frames.py`: `verified_live_map_tf_pose` 추가 — **실제** `map -> base_link` TF2 lookup에서 프레임, 로컬 시뮬레이션 시계와 3초 신선도, 공식 지도 출발점 좌표/자세/Quaternion 검증. 잘못된 프레임, 과거/미래, 범위 밖 좌표는 모두 거부. 이 3초는 Goal 전 관찰 제한이며 안전 Scan/CM/Guard TTL 완화가 아님.
2. `.../tools/p2_l3_live_session.py`: 기존 AMCL Pose 메시지가 없을 때만 **이미 생성된 TF listener**로 실제 `map -> base_link`를 조회. TF도 없으면 Goal을 **계속 차단**. 소스 provenance `tf_map_base_link` 또는 원래 `amcl_pose_map_transient_local` 명시. 새로운 TF 발행자, fake map pose, planner 없음.
3. `.../tools/p2_g07_ci_moving_goal.py`: 기존 정식 지도/월드 frame anchor 계약에 실제 provenance 전달. Goal 승인, CM, Guard, TTL 변경 0건.
4. `.../ros2_ws/src/axia_safety_supervisor/axia_safety_supervisor/p2_shutdown_context.py`(새 파일) 및 `p2_base_guard_node.py`, `p2_supervisor_node.py`: **ROS Context가 이미 종료된 상태**에서 나타나는 정확한 Jazzy WaitSet RCLError만 정상 종료 경로 처리. Context가 살아 있는 경우·그 외 예외는 그대로 재발시켜 문제를 숨기지 않음.
5. CI-only `AXIA_G07_CI_FORCE_MAP_TF_FALLBACK=1`은 GITHUB_ACTIONS=true/CI Goal 허용 및 Owner flag 미설정일 때에만 이 읽기 전용 Observer의 AMCL 구독을 생략. 실제 Nav2 AMCL publisher, TF, 물리 시연은 변경하지 않음. 실제 Owner에서 동작하지 않음.

### 테스트 증거

| Cycle | 공개 테스트 | 실제 결과 |
|---|---|---|
| 최초 RED | Student [#44552911381](https://github.com/silverbjin/axia-robot-safety-student/actions/runs/44552911381) | 새 실제 TF 검증 helper 미존재 회귀 재현 |
| TF + 종료 GREEN L0 | Student [#44553464222](https://github.com/silverbjin/axia-robot-safety-student/actions/runs/44553464222) | 6개 신규 + 3개 기존 PASS |
| CI-only 실물 TF 재현 RED | Student [#44555195704](https://github.com/silverbjin/axia-robot-safety-student/actions/runs/44555195704) | CI 강제 /amcl_pose 누락 경로 미지원 확인 |
| CI-only GREEN L0 | Student [#44555340520](https://github.com/silverbjin/axia-robot-safety-student/actions/runs/44555340520) | 7개 신규 + 3개 기존 PASS |
| 기존 AMCL 자동 경로 실제 Gazebo | Public [#44554334827](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44554334827) | 실제 Gazebo+RViz+Nav2 Moving Goal runner rc0, scoped L2 SUCCESS |
| 실제 TF 강제 경로 + 자식 종료 게이트 1차 | Public [#44556547289](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44556547289) | 실제 Moving Goal runner rc0, GUI 2/2, **p2_supervisor_node child exit1** → L2 FAIL; 기존 parent marker로 통과시키지 않음 |
| 동일 소스 실제 TF 강제 경로 최종 | Public [#44557868822](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44557868822) | **SUCCESS**: 실제 Goal 발행/시나리오 runner rc0, Gazebo·RViz 2/2, 실제 TF fallback 표식, Guard와 Supervisor **각 child exit0**, 원래 Native 21-gate review PASS |
| 새로운 강사용 고정 SHA 원샷 RED | Public [#44558954361](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44558954361) | 기존 Student SHA/CI run 불일치 탐지 |
| 새 고정 SHA GREEN | Public [#44559053963](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44559053963) | 9 기존 Owner + 5 native cache static + 4 actual cache shell mock + 6 foreign clock = **24/24 PASS**, `--self-check` 고정 Student `43a26...`, CI #44557868822 |

**재발 성능/안정성 한계:** #44556547289의 실제 child exit1과 #44557868822의 exit0는 동일 수정 소스의 서로 다른 실행이므로, **SIGINT 종료 경쟁의 반복 안정성은 아직 완전히 입증되지 않았습니다**. 원래 현장 WaitSet 오류만 제한 처리했고 운영 중 예외는 숨기지 않았습니다. 반복 현장 실험을 요구하지 않고 기존 성공과 최초 오류 증거를 보존합니다.

## 4. Owner 배포 경계와 남은 확인

Public CI release 브랜치 `fix/g07-vjpsc6wy-owner-release-20261120` (PR은 공개 기획용, `main` 미병합). 원샷 `scripts/axia_g07_task04_owner_moving_l3_once.sh`의 Student SHA를 `43a26a2f870c0fd99d66d06887cdf4e706b637b7`, 실제 엄격 Gazebo Moving L2 Run을 `44557868822`로 고정. 기존 플러그인 CMake 빌드 캐시, WSL2 GUI 진단, 사용 가능한 새 ROS Domain 자동 선택, `YES-P2-G07-GOAL` 수동 승인은 보존.

**강사 WSL2 새 SHA로 실제 Moving Goal L3 NOT_RUN**. 첫 실행에서 Student SHA가 변경돼 네이티브 witness cache가 한 번 **MISS**될 수 있으며 다음 동일 SHA 실행부터 HIT 예상. CLI 요청과 시연 동작을 실제 사용자가 직접 확인하기 전에는 현장 PASS 보고 금지.

**고도화 별도:** Scan 300ms 경계 사건은 원본 수치 보존하고 교육용 타이밍 감시로 분리. GPU/WSLg RViz 셰이더 경고 및 불규칙 SIGINT child 종료 재발은 독립 유지. 인증된 E-Stop 아님.

## 5. 완료 보고 규칙

- 정적 코드/계약: 공개 L0 GREEN.
- 실제 ROS 2/Gazebo Harmonic Xvfb: 공개 CI L2 GREEN (직전 실패 포함).
- 강사 WSL2 WSLg: 실제 신규 SHA Owner L3 **미검증**.
- 기존 교육용 Baseline `ACCEPTED`, 이번 새로운 현장 원본은 `Goal 미발행`, 혼동 금지.
- `main` 병합은 사용자 재승인 필요.
