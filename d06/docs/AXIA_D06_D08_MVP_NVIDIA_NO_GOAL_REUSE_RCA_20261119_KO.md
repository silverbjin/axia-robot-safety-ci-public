# AXIA D06/G07 — D08·MVP 선행 해결 이력 재사용: NVIDIA NO_GOAL 센서·RTF 단일 진단

- 작성: 2026-11-19 KST
- 범위: ROS 2 Jazzy / Gazebo Harmonic / TurtleBot3 Waffle / WSL2 WSLg, **NO_GOAL only**
- 작업 브랜치: `fix/d06-wslg-lidar-vs-rtf-ci-20261118`, 공개 PR #177
- 안전 판정: `D06_GAZEBO_LIVE_RELEASE=HOLD`, `AXIA_MVP_DEMO_ACCEPTED=HOLD`, `CERTIFIED_ESTOP=false`
- 개발 목표: 이미 개발된 GPU/RTF A/B 실행기에서 NVIDIA만 단일 실행, 불필요한 Intel 재시도 생략. Goal/CM/Guard/TF/안전 TTL/공식 Nav2 불변

## 1. 현장 원본 및 최초 안전 경계

업로드: `d06-wslg-sensor-vX1ipNh3.tar.gz`, 외부 SHA256 `e5e88375f28238a1bd0123a22b8b8ca700de11bc03cb113b413bc73c3def4958`; 바깥 checksum 일치, `native/SHA256SUMS` **41/41** 일치.

실제 `native/g07_wslg_sensor_truth.json`:
- 20.038s: Raw Scan70 / Safety Scan69 / Odom194 / Clock2283; SDF LiDAR 10Hz, Odom 30Hz.
- Raw `max_receipt_gap_sec=0.534773`, Safety `0.434745` (고정 안전 300ms 위반), 원래 `source_stamp_delta_sec <=.102`는 호스트 callback 간격과 다른 축.
- `front_median=0.52804m (<0.75)`, `side_median=0.629209m (<1.20)`, Safety CLEAR **0/69**, `near_ring_fraction_median=1.0`. 기존 `OWNER_PREGOAL_NOT_CLEAR_BEFORE_FIXTURE`는 정확한 NO_GOAL 안전 차단.
- `renderer.txt`에서 **D3D12 Intel Iris Xe / Mesa 26.2.6** / `REQUESTED_MESA_D3D12_ADAPTER=INHERITED_DEFAULT`. 사용 가능한 NVIDIA GPU가 있어도 Gazebo 서버에서 실제로 NVIDIA 사용했다는 원본 증거 없음.
- Clock의 host monotonic receipt 쌍이 없어 현재 파일만으로 `RTF=.34` 확정 **금지**. 기존 평균 3.5Hz 수신은 RTF 저하 *가설*이며, source와 전달을 분리한 최신 Student `e4c200...` 계측 재사용.
- `native/launch.log`: 첫 안전 STOP `AXIA_StopFront` → 후속 Scan timeout → 종료 시 `collision_monitor exit -11` 및 `gz sim -s exit -11`. `teardown.txt=P2_L2_GRACEFUL_TEARDOWN`은 자식 종료 코드 0을 보증하지 못한다. 두 SIGSEGV 발생의 직접 근본 원인(백트레이스)은 미확정.

## 2. 이미 해결된 D08·MVP 사례별 적용 범위

### D08 성능 복구 — **직접 재사용 대상**

- [D08 Student 성능 보고 commit `4ac64a45a2aa0e0474f6f5ff76ae48d7a6a2d88e`](https://github.com/silverbjin/axia-robot-safety-student/commit/4ac64a45a2aa0e0474f6f5ff76ae48d7a6a2d88e): WSLg Intel 기본과 NVIDIA D3D12을 구분하고 RGB-D 30→10Hz 한정 프로파일과 함께 RTF 구간 평균 **15.04%→91.86%** 증거. 이는 **두 조건이 함께 바뀐 이전 D08 현장 결과**이며 GPU만의 순수 인과효과/ D06 LiDAR 개선 증거가 아님.
- [D08 GUI RED `3d131ceb`](https://github.com/silverbjin/axia-robot-safety-student/commit/3d131ceb225f86c893adbb0daf8a0422174f9b8b) → [GREEN `3dd04abb`](https://github.com/silverbjin/axia-robot-safety-student/commit/3dd04abb830117d9f28060b24a9d0fb8fdcc7dc4): `gz sim -g --render-engine ogre` **GUI만** Ogre1로 바꾸고 센서 서버는 유지. D08 WSLg 화면 복구 증거는 존재하나 D06의 360° 거리 오류/ `gz sim -s` 종료 -11 해결책이라고 혼동하지 않음.

### MVP/D07 기존 분리 사례 — 그대로 보존

- [D07-H01 Cycle27 SIGSEGV 보고 commit `7ce9c841`](https://github.com/silverbjin/axia-robot-safety-instructor/commit/7ce9c84107d82b44fc475a337e8ae1da2a44f00a): GPU 기반 **`gz sim -g` GUI 자식** rc139에만 소프트웨어 `llvmpipe` 사용, 원래 Nav2/Gazebo 센서 서버·안전 TTL 유지. D06 이번 **서버 `gz sim -s` rc -11 및 Collision Monitor -11**과는 다른 최초 실패 경계.
- 기존 G07 ordered shutdown 코드를 삭제하거나 새 구현을 만들지 않는다. 이번 NVIDIA NO_GOAL 측정에서 서버/CM 종료가 안전하게 되는지 원본 `launch.log`로 확인한다. -11이 재발하면 해당 종료 시점과 첫 안전 경계를 별도 CI 회귀로 분리한다.

## 3. RED → GREEN → REFACTOR → REVIEW → COMMIT

- 기존 공개 PR #177의 [L0 20/20 #44327138409](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44327138409) 및 기존 A/B 비교기·NO_GOAL Owner wrapper·Student `e4c2007064bec2103bb743bd27cdbdf0955961b7`를 재사용했다.
- RED 계약 작성 [`acdd324e`](https://github.com/silverbjin/axia-robot-safety-ci-public/commit/acdd324ef387190d68496171bb57beaf12cb801e), 이후 이전 A/B 테스트와 충돌을 해결한 테스트 [`7364103b`](https://github.com/silverbjin/axia-robot-safety-ci-public/commit/7364103be4a175bebb30db0c89d412075e929622). **이 RED 커밋에 대해 공개 Actions 실패 실행은 확보되지 않았다**(Runner canary 외 없음). 테스트는 옛 소스의 `--nvidia-only` 부재를 탐지하도록 먼저 작성됨.
- GREEN 최소 구현 [`489da56b`](https://github.com/silverbjin/axia-robot-safety-ci-public/commit/489da56b4689d5cdef24dbe75ff845650f1ff2a0): 기존 `d06/scripts/axia_d06_g07_wslg_gpu_rtf_compare_once.sh`에 `--nvidia-only` 추가. NVIDIA 실제 `glxinfo` 확인, Student/Owner immutable SHA·blob 재검증, 단 1회 NO_GOAL Gazebo+RViz 센서 window, /clock host RTF, all-scan CLEAR와 300ms Raw/Safety TTL 검사, native `exit code -11`/SIGSEGV 즉시 HOLD. `--compare` 기존 두 GPU A/B 기능과 사용법은 보존.
- 공개 workflow 수정 [`4a9388c3`](https://github.com/silverbjin/axia-robot-safety-ci-public/commit/4a9388c3e50d337a754a048e8121060ea4c53edc): PR-trigger 및 Bash -n + self-check. **[공개 CI #44355362302](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44355362302) SUCCESS**: Student L0 9/9 + Public evidence7/7 + GPU runner5/5 + Raw first gap1/1 = **22/22 PASS**, bash -n/self-check PASS. `AXIA_D06_G07_LIDAR_RTF_ISOLATION_L0_PASS_NO_ROS_NO_GAZEBO_NO_GOAL`.
- REFACTOR/REVIEW: 구 A/B와 NVIDIA 단일 모드를 분리. 녹색 NVIDIA 센서 JSON이라도 GUI 픽셀·GPU 서버 자체 렌더러·CM120/Guard150·Moving L3는 **증명하지 않는다**. Goal/Twist/Fixture 이동 발행기 신규 추가 0, 안전 TTL/공식 소스 변경 0, private 원본 GitHub 업로드 0.

## 4. 검증 수준 및 출고 게이트

| 범위 | 현재 |
|---|---|
| 원본 TAR/SHA256 및 최초 거리·주기 실패 | PASS (증거 유효) |
| D08 및 MVP 선행 패치 실제 SHA 확인 | PASS (적용 범위 구분) |
| 공개 CI 새 NVIDIA-only 문법·계약 L0 | **PASS 22/22** |
| D06 신규 NVIDIA GPU + 20초 물리 /scan 현장 WSLg | **NOT_RUN** |
| 새로운 서버 측 GPU-LiDAR 거리·RTF 정상화 | **NOT_RUN** |
| 동일 세션 CM120→Guard150 + 종료 ACK/exit0 | **NOT_RUN / 기존 -11 실패** |
| Owner Moving Goal/WSLg L3 최종 인수 | **HOLD** |
| `main` 병합 | **미수행** |

### Owner WSL2 최종 단일 진단

**최종 소스 HEAD/Git blob을 확인한 후** 다음 immutable public script를 한 번만 내려받아 `--nvidia-only`로 실행한다. 기존 현장 실패가 재발하면 같은 모드 재시도 대신 최초 출처·SafeScan/Raw 시차·RTF/거리와 `launch.log` SIGSEGV를 근거로 공개 CI에 회귀를 편입한다.

Expected pattern (실제 NVIDIA WSLg 출력 아님):
```text
D06_GPU_RTF_NVIDIA_ONLY_NO_GOAL OWNER_L3_NOT_ACCEPTED
D06_GPU_RTF_AB_CASE_START=NVIDIA DOMAIN=86 GOAL_NOT_SENT
D06_GPU_RTF_CLOCK_MEASURED <actual> <class>
D06_GPU_RTF_NVIDIA_ONLY_FIRST_BLOCK=NONE  # 실제 20초 충족시에만
D06_GPU_RTF_NVIDIA_SENSOR_CANDIDATE_NOT_ACCEPTED
D06_GAZEBO_LIVE_RELEASE=HOLD CERTIFIED_ESTOP=false
```
