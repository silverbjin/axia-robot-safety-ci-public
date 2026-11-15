# D08 공개 CI `main` 통합·브랜치 인계 및 인수 경계 (2026-11-15)

**최종 범위:** 강사 D08 온라인 합성 교육은 별도 private Instructor / public Student의 `main`에 둔다. 이 공개 저장소는 (a) 학생 fixture/ZIP public L0, (b) **실제 Gazebo Waffle NO-GOAL L2** 근접→복귀, (c) 동일 실제 RGB 픽셀의 **C++ upstream `yolo_ros` DetectionArray replay L1**만 재현한다. **이동 Goal·P2 Guard 안전 TTL·WSL2 실시간 YOLO+D05의 승인과 완전히 분리**한다.

## 1. 공개 CI D08 브랜치·PR별 역할과 main 포함 여부

| 브랜치 | PR / 원래 역할 | 이번 통합 결과 |
|---|---|---|
| `feature/d08-online-integration-ci-20261110` | [#39](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/39) **MERGED**, 학생 D08 Python fixture·ZIP 계약과 공개 CI 격리 | 이미 main 포함, 재병합 금지. 과거 sealed teacher job을 새 승인·회귀 경로로 사용하지 않음 |
| `feature/d08-gazebo-live-ci-20261110` | [#42](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/42), 초기 단일 world Gazebo RGBD/Contact + Owner bootstrap | main 대비 ahead=0인 오래된 단계, 재병합 불필요 |
| `fix/d08-g07-acceptance-ci-20261110` | [#43](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/43), Owner 종료·Contact·Gazebo 마지막 오류 | Owner Goal·CM/Guard 결합 미인수 부분 별도 HOLD |
| `fix/d08-human-contact-positive-ci-20261110` | [#44](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/44), 하나의 사람/충돌 물체 + Gazebo 비로봇 positive Contact | **독립된 정적 Contact 사전근거**로만 보존; 움직이는 로봇 비접촉 인수 아님 |
| `fix/d08-single-visual-rgbd-ci-20261110` | [#45](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/45), 이중 T-pose 시각 및 registered RGB-D header | 후속 UI9 no-Goal 검증에 필요한 동작만 선별 반영 |
| `release/d08-g07-lidar-owner-20261110` | [#48](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/48) + [#49](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/49) **MERGED** 릴리스 리뷰, GPU LiDAR·Owner 원샷 | #49가 기본 공개 D08 소스를 main에 통합. 최신 Owner 안전 승인 의미는 아님. #48 중복 병합 금지 |
| `fix/d08-grounded-human-ci-20261111` | [#50](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/50), 실제 COLLADA 발높이·검은 pole 제거 | 최신 실측 no-Goal 단일 mesh 동작과 L0 기대값 선택 반영 |
| `release/d08-grounded-owner-wsl2-20261111` | [#51](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/51), 강사 Owner SHA-pinned WSL2 bootstrap | **별도**, 새 private Owner SHA를 main에서 임의 배포하지 않음 |
| `fix/d08-foot-short-step-ci-20261111` | [#52](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/52), 6cm 발·7cm 물리 이동·CM 수신 타이밍/STOP 판정 | No-Goal L2 측정 및 회귀만 수용, 이동 인수·TTL 변경 제외 |
| `fix/d08-bgyntv7-actual-person-ci-20261112` | [#55](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/55), 실제 Gazebo RGB의 고정 ONNX `person` positive 검증 | 불변 모델 SHA와 실제 근접 프레임 추론 경로 반영 |
| `ci/d08-dns-parity-20261112` | [#56](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/56), GitHub Runner DNS 구분 진단 | 인프라 조사 이력 보존, 핵심 D08 시연 런타임과 병합하지 않음 |
| `ci/d08-ubuntu-mirror-20261112` | [#57](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/57), Canonical 서명 APT 미러 fallback 실제 검증 | 과거 DNS 복구 증거만 기록, 신규 job은 `APT::Update::Error-Mode=any`로 인프라 실패를 구분 |
| `fix/d08-ui9-pre-goal-vision-ci-20261112` | [#58](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/58), 근접 사람 `person=0`의 조건 분석, native `set_pose` 후 LiDAR/RGB-D, 원복 ACK, 실제 C++ `yolo_ros` ROS 재생 | **7개 검증된 공개 source blob만** 최신 main으로 이식. Owner private/Goal/보호 Workflow 원천 제외 |
| `release/d08-public-no-goal-ci-main-20261115` | D08 교육용 public no-Goal 릴리스 | 7개 source, 단일 사람/충돌 test 최신 기대값, L0 source/no-Goal 테스트 및 **same-run L2→L1 공개 Workflow**와 본 이력 문서만 main 병합 |

## 2. 새 public main 실행기 경로

- `d08/harness/d08_live_world.py`, `d08/harness/d08_live_readonly_probe.py`, `d08/harness/d08_visible_person_frame.py`: 공식 Waffle Gazebo registered RGB-D / 사람 메시 / native LiDAR read-only 계측. 이미 검증된 #58 Git blob과 정확히 같은 소스.
- `d08/scripts/d08_public_gazebo_l2.py`: 실제 Gazebo `/world/default/set_pose` 근접 `x=-1.63m` → `/scan`, 640×480 등록 RGB-D → 원래 `x=-0.58m` ACK·`/scan`. 로봇 Goal 전송 없음. 복구 실패 시 fail closed.
- `d08/scripts/d08_real_nav2_cm_l1.py`: **공식 Nav2 Collision Monitor** native 노드의 callback/종료 검증. STOP 스캔은 실제 Gazebo에서 측정한 거리의 **합성 재생**이며 private Guard 실행 아님. CM `stop_pub_timeout=1s` 이후 `Guard TTL=150ms`의 실제 fail-close 검증 미수행.
- `d08/scripts/d08_actual_rgb_onnx_probe.py`: 실제 640×480 Gazebo RGB 프레임에 고정 ONNX 원시 class0 후보 검증. NMS 후 yolo_ros DetectionArray와 별개.
- `d08/scripts/d08_ui9_yolo_replay_probe.py`: 동일 Gazebo 픽셀을 ROS `sensor_msgs/Image`로 재생, **고정 upstream C++ `yolo_ros`의 실제 DetectionArray** 관찰. 라이브 Gazebo 센서 처리 시간·WSLg 검증 아님.
- `.github/workflows/d08-main-no-goal-real-gazebo-l2.yml`: public GitHub Actions 소스 L0 → **실제 Gazebo L2** → 이 실행의 서명된 아티팩트 **같은 실행 내** 다운로드 후 C++ ROS L1. Secret/private Instructor checkout/Owner Goal 없음.
- `d08/tests/test_d08_main_public_only_contract.py` 및 개정 `test_d08_g07_lidar_visible_proxy.py`: 초기 RED(옛 검은 shin visual 기대/오라클 검색 잘못) 뒤 실제 grounded mesh 한 개 및 source/no-Goal 요구를 GREEN으로 검증.
- **기존 `d08/scripts/axia_d08_live_gazebo_wsl2_once.sh`, `axia_d08_instructor_wsl2_once.sh`의 공개 Owner pin을 갱신하지 않음**: private Owner 교체·actual Go/Stop 인수는 별개.

## 3. 과거 실제 실행 근거와 새 인수 기준

- [사람 near→far 실제 Gazebo #43117842587](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43117842587): near 약 **0.359203m**, far 약 **1.412149m**, native set_pose ACK, registered RGB-D skew 0ms, 로봇 Goal 미전송.
- [실제 `yolo_ros` replay #43118537433](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43118537433): near RGB의 `DetectionArray person=3`, 최대 **0.549731**.
- 이번 새 `main` 브랜치 공개 Actions [#43676658454](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43676658454)에서 선행 RED `2 failed,17 passed`을 확인 후 L0 GREEN→Gazebo L2 재실행. 실제 near **0.361795m**, restore **1.420888m**, ONNX class0 최고 **0.549549**. ROS replay L1은 최종 job 결과를 확인해야 최종 PASS를 선언한다.
- **오류 분석 기준:** WSL2 첫 영상에서 RGB80/Depth155, `person=0 / umbrella=64`; 최근 프레임 최소 skew 198ms (>50ms). 거리가 유일한 원인이라는 증명은 없다. CM→Guard 전달 주기·가장 이른 안전 latch를 우선 분석한다.
- CI PASS라도 **WSL2 Owner GUI 실시간 YOLO+D05, 이동 G07/Nav2 Goal, Contact-free·STOP odom dwell·CM source/receive 150ms TTL 전체, certified E-Stop은 미검증/HOLD**다.

## 4. 새로운 작업의 기준

```bash
git fetch origin main
git switch main
git pull --ff-only origin main
git switch -c feature/d08-next
```

성공한 공개 L2/L1 증거와 exact blob을 유지한다. 다음 현장 오류는 그대로 재시도하지 말고 최초 안전 상태 전이·최초 sensor/CM TTL 위반을 공개 CI RED로 추가한 뒤 GREEN을 통과시킨다. **SW 보호정지는 인증된 HW E-Stop이 아니다**.
