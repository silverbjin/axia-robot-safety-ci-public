# AXIA G07 Task04 — Owner WSL2 GUI 시작 2분 이상 병목 분석 및 최소 최적화

**작성일:** 2026-11-19  
**범위:** 교육용 MVP baseline의 시작 시간 최적화만 진행. ROS2 Jazzy/Gazebo Harmonic/공식 Nav2/Collision Monitor/Safety Supervisor/Guard 동작 변경 없음.  
**기준선:** `AXIA-G07-T04-DEMO-BASELINE-20261119-CZObXAdP` (교육용 인수 유지).  
**현장 신규 증거:** `owner-moving-8ULG28b7.tar.gz`, `.diagnostics.zip` 및 SHA256 sidecars.

## 1. 원본 증거 무결성

- TAR SHA256 `ebb651629f0ee5fb0b2352258b7a90bd808e10d6f2dd7935de7301d900d40a62`: 사용자 제공 sidecar와 일치
- 진단 ZIP SHA256 `354a4bfbf4bfb9dec4b48a3a6c55b27db194cc659f8276c7aab2971ed2c90d07`: 사용자 제공 sidecar와 일치
- 실제 런타임 Student SHA `954fc2f054c50df783bc81c4d0835a6ee6f8645d`; 원본 공식 패키지 25/25·공식 파일 5/5 패리티. 해당 증거는 공개 repo에 raw 업로드하지 않음.
- 원본 `native_build/CMakeCache.txt`의 `CMAKE_CACHEFILE_DIR`는 고유 증거 경로 `.../owner-moving-8ULG28b7/native_build`. 매 실행마다 새 디렉터리로 CMake 초기 탐색 반복.

## 2. 실제 시간 경계

| 단계 | 사용자 원본에서 관측 | 설명 |
|---|---:|---|
| `owner_parity.log` 파일 작성 | **23:02:11 KST** | ROS/공식 패키지 패리티 완료 (이전 시작 시간은 없음) |
| `native_build_config.log` 작성 | **23:04:21 KST** | 약 130초 경과. 내부 `Configuring done (116.4s)` |
| `native_build.log` 작성 | **23:04:36 KST** | 설정 완료 후 약 15초 추가 (파일 timestamp 기준 근사) |
| 실제 ROS launch 프로세스 시작 | **23:04:58 KST** | CMake 캐시 없는 증거 빌드가 화면 표시 이전에 차단 |
| `rosbag2` record 시작 | **23:04:59 KST** | 약 21개 ROS/Gazebo 노드 launch, source stamp wall-time |
| `staged_startup.log` 종료 | **23:05:10 KST** | Localization START 거부, 새 Goal 미발행 |
| 창 감지 최종 | `rviz=1\ngazebo=0` | **이번 실행에서는 Gazebo GUI 두 창 정상 출력까지 도달하지 않음** |

별도 사용자 패키지 `colcon build` 3개 패키지 **7.06s**, Clock probe **1.743s**, Nav2 planner pre-state **6.328s**, Localization START 검사 **5.013s**. 이 항목들은 최초 우선순위가 아님. 원본 CMake configure+빌드가 가장 큰 초기 지연 병목입니다. 정확한 실행 개시~창까지 전체 경과는 이 자료에 하나의 연속된 이벤트 시계로 남아 있지 않아 추정과 실측을 구분합니다.

이번 실패는 `LOCALIZATION_START: G07_NATIVE_LIFECYCLE_STARTUP_REJECTED:request_sent=True`, `goal_sent=false`. 이 오류는 신규 baseline 진단 별도 항목으로 보존하며, **시간 최적화 코드로 고쳤다고 주장하지 않습니다.**

## 3. 최소 수정 — 검증된 플러그인 persistent cache

변경 파일은 공개 CI의 `scripts/axia_g07_task04_owner_moving_l3_once.sh` 하나입니다.

- 예전에는 `cmake -S ... -B "$OUT/native_build"`처럼 매번 고유 증거 디렉터리에 CMake 의존성 탐색을 처음부터 수행.
- 새 방식은 HOME 내부 `~/.cache/axia/g07_task04_native_witness/<sha256>` 사용. 키 = **고정 Student SHA + 두 CMake/C++ 소스 파일 SHA256 + 고정 소스 경로 + 설치된 Gazebo 개발/런타임 패키지 버전 + 컴파일러 버전 + CMake 버전 + 아키텍처**.
- **MISS** = 최초 빌드·변경된 도구체인/소스·오염된 binary. 원본 CMake 설정/컴파일을 그대로 수행.
- **HIT** = 기존 CMake+컴파일 단계 호출하지 않음. `sha256sum -c`로 플러그인 무결성 재확인.
- `flock`으로 동시 캐시 변조 방지, 잘못된 SHA의 캐시 사용 거부. 기존 플러그인 `.so`는 실행마다 고유 `$OUT/native_build/`로 복사하고 SHA를 기록하여 증거 독립성 유지.
- 자동 시나리오 변경 **0개**: 원래 학생 런타임 SHA·Nav2/CM/Guard/Scan/Supervisor·TTL·Goal 승인 `YES-P2-G07-GOAL` 그대로.
- 별도 작은 진단 ZIP에 `native_witness_build_profile.json` (MISS/HIT, ABI fingerprint, 실제 빌드 단계 소요 시간, binary SHA)과 `startup_timing.tsv` (pinned source/환경/GLX/native ready/runner start/처음 RViz/처음 Gazebo 탐지/종료 이벤트) 추가. ROS bag·사생활 파일은 여전히 작은 ZIP에서 제외.

## 4. 실제 RED → GREEN → REVIEW

| 검증 | 결과 |
|---|---|
| 공개 [RED L0 #44541220909](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44541220909) | 새 캐시 기능 관련 계약 **의도된 FAIL**, 원본 무캐시 CMake 구문 재현 |
| 공개 [GREEN L0 #44542130701](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44542130701) | 5개 소스 계약 + **실제 셸 블록 mock 빌드 4개** + 기존 Owner Bootstrap 9개, **18/18 PASS**. Cold→Warm, ABI 변경, 소스 변경, 캐시 binary corruption 모두 검증 |
| 실제 동일 소스 Gazebo8 네이티브 ABI [Cold/Warm L1 #44542395793](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44542395793) | **SUCCESS**, 최초 `MISS 4.217초`, 동일 환경 두 번째 `HIT 0.002초`, `saved 4.215초`. 네이티브 플러그인 .so SHA 동일 |
| 기존 실제 Gazebo+RViz Moving L2 [#44478344652](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44478344652) | 이전 동일 Student SHA (시나리오 코드 불변)에서 **SCOPED PASS**, 이번 캐시 wrapper로 WSL2/실제 GUI 재실행 증명은 아님 |

**시간 비교 해석:** 공개 CI의 4.217초는 CI CPU/컨테이너 수치로 강사 WSL2 116.4초와 동일 성능이라고 가정하지 않습니다. 그러나 이미 동작하는 CMake를 **동일한 조건에서 아예 호출하지 않는 캐시 HIT**는 WSL2에서도 반복 컴파일/의존성 탐색을 회피하는 구조적 개선입니다. 강사 WSL2 첫 새 캐시 MISS는 재빌드가 필요하여 느릴 수 있고, 두 번째 HIT에서 단축 효과를 실측해야 합니다. 사용자 WSL2의 남은 ROS/Nav2/GUI 구간은 새 `startup_timing.tsv`로 분리 측정합니다.

## 5. 사용자 WSL2 단일 실행·증거·상태

공개 CI에 커밋된 본 브랜치 `perf/g07-task04-owner-native-witness-cache-20261119`의 불변 SHA를 사용합니다. 예전 `main`은 최적화 이전 코드이므로 패치 검증 전에는 사용하지 않습니다.

`--self-check`는 `AXIA_G07_TASK04_NATIVE_WITNESS_CACHE_V1=AVAILABLE_FIRST_WARM_RUN_UNMEASURED`를 출력하나 실제 ROS/Gazebo는 실행하지 않습니다.

`--run`은 원래대로 강사 실제 /dev/tty 수동 Goal 동의와 안전 준비 절차를 보존합니다. 실행 후 작은 진단 ZIP+SHA만 전달하면 **캐시 HIT/MISS, 초기 116초 병목 제거 여부, RViz/Gazebo 첫 윈도우 관측 시각, 별도 Localization 상태**를 평가할 수 있습니다.

**현재 상태:** 공개 L0+네이티브 ABI L1 PASS, 강사 WSL2 캐시 경로 실증 **NOT_RUN**, 새 wrapper로 통합 실제 Gazebo Moving L2 **NOT_RUN**, `main` 미병합. 사용자가 승인한 기존 교육용 MVP Baseline은 변경·철회하지 않으며 공식 안전 타이밍 인수와 인증 E-Stop을 주장하지 않습니다.
