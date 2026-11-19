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

---

## 5. 2026-11-19 Owner NVIDIA 실측 첫 실패 분석 및 **단일 명령 자동 증거 번들** (후속 개발 사이클)

### 5.1 Owner 실측 (동일 세션의 원본 출력; 새 재실행 아님)

- 기존 로컬 세션: `~/axia_d06_g07_gpu_rtf_evidence/ab-no-goal-yBT9gFbJ`.
- NVIDIA 전용 `NO_GOAL`, `ros_clock_rtf=0.913157` (`RTF_NORMAL`), LiDAR source `9.999441Hz`, host safety `9.131648Hz`.
- **거리 정상화 후보:** Safety Scan `180/180 CLEAR`, front median `1.414687m`, side median `2.520466m`, all-azimuths-near false.
- **가장 먼저 검증된 차단 항목:** Safety `max_receipt_gap_sec=0.421172` (첫 위반 index 6), Raw `0.427761` (첫 위반 index 11). 첫 Raw host gap `0.390708`, 매칭 Safety `0.387036` (`BOTH_TOPIC_ACTIVE`). 두 토픽 공통의 수신 지연 후보이지만 Gazebo native 송신/DDS executor 원인은 원본 요약만으로 확정하지 않음.
- **별도 치명 종료 증거:** 기존 `nvidia.launch.log` 427번째 줄 `collision_monitor exit code -11`, 428번째 `gz sim -r -s exit code -11`. `P2_L2_GRACEFUL_TEARDOWN` 마커는 정상 자식 종료를 증명하지 못함.
- `goal_sent=false`; 충돌 모니터/서버 segfault의 백트레이스는 미확보. **전체 Moving/CM120/Guard150/종료는 HOLD**.
- **중요 진단 개선:** 기존 실행기는 `SENSOR_EXIT=3` 이후 종료 SIGSEGV 검사로 즉시 종료하므로 실제 센서 `reasons`를 요약 출력하지 못했음. 새 실행기는 첫 Safety/Raw TTL 차단 사유·첫 index/거리·RTF를 SIGSEGV 검사 **이전**에 출력하고, 실제 `-11`과 단순 Python `Traceback`을 구별.

### 5.2 추가 코드는 진단/증거 수집에만 한정

**변경 파일:** `d06/scripts/axia_d06_g07_wslg_gpu_rtf_compare_once.sh`; 신규 회귀 `d06/tests/test_d06_forensic_bundle_once.py`.

- `--analyze-existing` 옵션: 기존 가장 최근 NVIDIA NO_GOAL 원본에서 자동 분석. **ROS/Gazebo/Goal/추가 GPU 실험 실행 0**, `GITHUB_ACTIONS=true`/DISPLAY 없는 격리 L0 테스트에서도 오프라인 기능 시험.
- `--nvidia-only` 및 기존 `--compare`의 추후 실행: **성공 또는 실패 EXIT 모두** `collect_and_package`가 작은 증거 TAR+SHA256 생성. 원래 종료 코드를 유지하고 미검증을 PASS로 바꾸지 않음.
- 출력: `D06_FORENSIC_FIRST_SENSOR_FAILURE`, `D06_FORENSIC_PROCESS_CRASH`, `D06_FORENSIC_RTF`, `D06_FORENSIC_ARCHIVE`, `D06_FORENSIC_SHA256`.
- 압축에 포함: `summary.json`, 첫 Safety STOP 및 첫 시간 위반 전후 excerpt, SIGINT 및 `-11` 프로세스 종료 문맥, Owner NO_GOAL 요약, 렌더러, 로컬 원본 SHA 목록.
- 원래 Owner TAR 경로가 `nvidia.run.log`에 있으면 **해당 TAR의 SHA256 sidecar를 검사한 후** `clock_diagnostics.json`, `p2_graph_diagnostics.json`, `startup_verdict.json`, RViz/Gazebo GUI 렌더 오류 excerpt 및 `teardown.txt`를 소량 포함. 유효한 원본 TAR가 없다면 `source_archive_sha256_verified=false`로 기록하며 증거를 위조하거나 가정하지 않음.
- 거대 원본 `launch.log`·SDF·전체 원본 TAR은 작은 압축 안에 복사하지 않음. **원본은 기존 로컬 폴더에 보존**, 핵심 파일만 SHA 목록과 함께 봉인.
- 새 native Gazebo publisher나 센서/Goal/CM/Guard 기능 구현 없음; `Scan300ms`, `CM120ms`, `Guard150ms`, CLEAR 거리 임계값 모두 유지.

### 5.3 RED → GREEN → REVIEW → COMMIT 실측 CI 이력

| 단계 | 커밋/Actions | 실제 결과 |
|---|---|---|
| RED-1: 기존 원본 한 번에 분석·패키징 미지원 | [`34ef0ede`](https://github.com/silverbjin/axia-robot-safety-ci-public/commit/34ef0ede2426918386c00ebea0186025cb39a253), [#44429176804](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44429176804) | 신규 3건 예상 FAIL, 원인 기능 누락 |
| GREEN 후보: 내장 증거 수집 및 판정 순서 | `cc588949`→`dc106822` | 기능 추가, 기존 셸 가드가 HOME 미설정 시 먼저 실패하는 회귀 발견 |
| GREEN-1: 기존 CI 가드 유지 | [`36426e92`](https://github.com/silverbjin/axia-robot-safety-ci-public/commit/36426e924420de2ef5e64c9204a0420ecc182004), [#44429988242](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44429988242) | L0 SUCCESS |
| RED-2: 원래 Owner TAR의 추가 원인 문맥 | [`b0a4ea6b`](https://github.com/silverbjin/axia-robot-safety-ci-public/commit/b0a4ea6bf2130fb133be8bc7e34c2c91cc310dc0), [#44430293395](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44430293395) | 추가 실패 재현 |
| GREEN-2: SHA 검증한 native 핵심 로그 포함 | [`bef5189a`](https://github.com/silverbjin/axia-robot-safety-ci-public/commit/bef5189ac8a75aa685eabb109df13dcab65b8781), [#44430425020](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44430425020) | **L0 25/25 PASS** (9+7+5+3+1); 오프라인 실제 tarfile fixture + checksum/아카이브 콘텐츠 검증. 실제 ROS/Gazebo는 실행하지 않음 |

### 5.4 Owner WSL2 한 번의 명령 (기존 증거 재사용)

최종 공개 CI가 통과한 **정확한 HEAD와 Git blob**을 확인한 뒤, 이 스크립트 한 개를 내려받아 다음 옵션으로 실행합니다.

```bash
bash <SHA256/GIT-BLOB-verified-public-script.sh> --analyze-existing
```

기대 출력:
```text
D06_FORENSIC_EXISTING_NO_SIM_REPLAY=<실존 로컬 증거 디렉터리>
D06_FORENSIC_FIRST_SENSOR_FAILURE=SAFETY_RECEIPT_TTL_300MS_BLOCKED
D06_FORENSIC_PROCESS_CRASH=collision_monitor,gazebo_server
D06_FORENSIC_RTF=0.913157
D06_FORENSIC_ARCHIVE=<실제 로컬 경로>.tar.gz
D06_FORENSIC_SHA256=<실제 로컬 경로>.tar.gz.sha256
D06_GAZEBO_LIVE_RELEASE=HOLD CERTIFIED_ESTOP=false
```

**이제 강사에게 동일 시뮬레이션을 재시도하거나 수동 로그 추출 명령을 여러 번 요청하지 않습니다.** 새로운 WSLg 물리 실행이 필요해질 경우에도 원샷의 실패 시 자동 증거 보존을 유지하고 원인별 공개 CI 회귀를 먼저 수정합니다. Git main 병합 없음.
