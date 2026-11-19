# AXIA G07 Task04 — 강사 WSL2 Moving Goal L3 단일 시연 실행·인수 가이드

2026-11-19 KST / 실제 강사 WSL2 Moving Goal **NOT_RUN** / 배포는 공개 CI 범위 한정 L2 검증 후 / SW Stop ≠ 인증 E-Stop.

## 최신 n7 인수용 고정 공개 소스와 단계

| 항목 | 정확한 버전/증거 |
|---|---|
| 공개 CI PR | https://github.com/silverbjin/axia-robot-safety-ci-public/pull/182 |
| Student PR | https://github.com/silverbjin/axia-robot-safety-student/pull/61 |
| 단일 주행 소스 SHA | `dcd1299c03bf702712631dc025b868335cadd1c6` |
| CI read-only 판정 소스 SHA | `71b85c42ea474276fedd9f345521317b8c348b4e` |
| 실제 Gazebo Harmonic + Nav2 + Waffle + RViz Xvfb L2 | https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44433206283 |
| 출고 Owner 원샷 Bootstrap L0 | **신규 pin 8개 검증 중** |
| L2 원본 공개 수치·SHA256 artifact | https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44433206283/artifacts/14487965556 |
| 강사 실제 WSL2 L3 | **n7 원본 19/21 HOLD / 신규 timing 수정판 미실행** |
| main | **병합 안 함** |

기존 Task01~03 성공 증거를 보존하고 반복하지 않는다. 최종 수정판은 공개 CI #44433206283에서 **실제 Gazebo/Nav2 Moving Goal+GUI 21/21 안전 검증**을 완료했다. Xvfb CI는 Owner WSLg D3D12가 아니므로 L3 승격 불가.

과거 CI #44359652805의 이동 0.198562m, 정지 1.013681초, CM Source 59.330ms, Observer 86.805ms, Guard age 36.842ms는 **이전 실행의 보존된 기록**이다. 최신 #44433206283은 새 Student SHA의 21개 조건 true, first_failure=NONE, rc=0 및 GUI2를 확인하였으며 새 수치 JSON 아티팩트를 별도로 보존했다.

**현장 경계:** S75의 0.538428m/0.626332m 근거리 오검출은 n7 원본에서 1.414623m/2.523533m CLEAR로 개선되었다. 이번 n7의 남은 실패는 **엄격 CM Owner 스키마·Guard 내부 age 증거 누락 및 WSL2 RMW wall-clock step**이며 새 WSL2 실행은 아직 미검증이다.

기존 실행 명령에서 사용했던 원샷 커밋 `e56bbad873e0e37c83f34ecbcc206cc8a648e63d`은 WSLg D3D12 변수를 전역 export하는 이전 배포 후보이므로 **현장 신규 실행에 사용하지 않는다.** 새 고정 SHA는 동일 Student SHA의 공개 L2 및 원샷 Bootstrap L0를 통과했다.

## 강사 WSL2 복사·붙여넣기 명령 (하나의 블록)

다음은 **이 시점의 실증 공개 원샷 SHA `4cd36853358bb088263a0b73a0cfa6c8d5ec2d55`**를 고정한다. CI가 검증한 Student SHA는 내부에서 별도 확인한다. 무작위 main HEAD를 내려받지 않는다.

```bash
(
  set -Eeuo pipefail
  SOURCE_SHA='4cd36853358bb088263a0b73a0cfa6c8d5ec2d55'
  RUNNER="$(mktemp --suffix=.sh)"
  trap 'rm -f -- "$RUNNER"' EXIT
  curl -fLsS --retry 3 --max-time 90 \
    "https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public/$SOURCE_SHA/scripts/axia_g07_task04_owner_moving_l3_once.sh" \
    -o "$RUNNER"
  bash -n "$RUNNER"
  bash "$RUNNER" --self-check
  bash "$RUNNER" --run
)
```

강사 WSL2 Ubuntu 24.04에서 실행. 실행기는 고정된 Student와 공개 CI 코드의 SHA를 확인하고, 기존 Nav2 공식 overlay(자동 발견 또는 `AXIA_NAV2_OVERLAY_SETUP` 지정), ROS 2 Jazzy/Gazebo Harmonic, 공식 25개 package/5개 SHA, D3D12 GPU 렌더러를 확인한다. **Gazebo gpu_lidar 서버는 공개 성공 L2와 같은 `LIBGL_ALWAYS_SOFTWARE=1`로 실행하고, D3D12 어댑터 환경변수는 Gazebo·RViz GUI 자식 프로세스에만 적용합니다.** GUI의 `env -u LIBGL_ALWAYS_SOFTWARE`가 서버의 렌더링 설정을 바꾸지 않습니다. 필수 Gazebo 개발 헤더가 없는 경우에만 `sudo apt`의 빌드용 패키지 설치를 요청할 수 있다. 그 외 별도 ROS 노드 실행 명령이나 GUI 디버깅 터미널은 불필요.

사전 준비가 끝나면 이미 정해진 ROS Domain/GZ Partition 안에 Gazebo 서버 **한 개**와 read-only GUI 클라이언트, RViz가 실행된다. 실물 로봇이 아닌 **시뮬레이션만** 대상이다.

**실제 주행 승인:** 실행기는 기존 Student 소스의 실제 `/dev/tty`로 `YES-P2-G07-GOAL`을 요구한다. 강사가 키보드로 정확히 입력해야 한다. 자동 응답·파이프·CI 환경변수로 대체하지 않는다. 실제 TTY 승인 이후에도 Goal 발행 전 기존 `admit_owner()`가 Supervisor/CM/Guard의 정확 PID·세션과 Student Git SHA를 재검증합니다. 이 검사에 실패하면 Goal을 전송하지 않습니다.

## 콘솔 기대 패턴

`--self-check` 성공은 ROS를 시작하지 않는 L0이다:

```text
AXIA_G07_TASK04_OWNER_MOVING_BOOTSTRAP_L0_PASS student_sha=dcd1299c03bf702712631dc025b868335cadd1c6 l2_run=44433206283 NO_ROS_NO_GAZEBO_NO_GOAL
AXIA_G07_TASK04_OWNER_MOVING_L3=NOT_RUN
AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false
```

**현장에서 실제로 성공한 뒤 기대할 패턴 (아직 실행 증거가 아님):**

```text
AXIA_G07_TASK04_STUDENT_SHA_VERIFIED=dcd1299c03bf702712631dc025b868335cadd1c6
AXIA_G07_TASK04_OWNER_CORE_PARITY_25_5_PASS
AXIA_G07_TASK04_WSLG_D3D12_GPU_SELECTED=...
AXIA_G07_OWNER_GAZEBO_LIDAR_SOFTWARE_RENDERER_SELECTED D3D12_GUI_ONLY
AXIA_G07_TASK04_OWNER_MOVING_BEGIN student_sha=...
[강사가 controlling TTY에 YES-P2-G07-GOAL 직접 입력]
AXIA_G07_TASK04_OWNER_NATIVE_RUNNER_RC=0
AXIA_G07_TASK04_OWNER_WSLG_GAZEBO_RVIZ_WINDOWS_PASS
AXIA_G07_TASK04_OWNER_SINGLE_NATIVE_NUMERICAL_CANDIDATE_PASS_SCOPED
AXIA_G07_TASK04_OWNER_VISUAL_AND_RAW_REVIEW_PENDING
AXIA_G07_TASK04_ARCHIVE=/home/.../owner-moving-XXXXXXXX.tar.gz
AXIA_G07_TASK04_SHA256=/home/.../owner-moving-XXXXXXXX.tar.gz.sha256
AXIA_G07_TASK04_DIAGNOSTIC_ZIP=/home/.../owner-moving-XXXXXXXX.diagnostics.zip
AXIA_G07_TASK04_DIAGNOSTIC_SHA256=/home/.../owner-moving-XXXXXXXX.diagnostics.zip.sha256
AXIA_G07_TASK04_OWNER_NUMERICAL_CANDIDATE=PASS_SCOPED_RAW_REVIEW_PENDING
AXIA_G07_TASK04_OWNER_MOVING_L3=HOLD
AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false
```

실패하면 rc≠0 및 `AXIA_G07_TASK04_FIRST_FAILURE=...`이 출력되며, 확보된 원본 TAR/SHA256와 `task04_owner_verdict.json`의 `HOLD`을 유지한다. 최초 Goal 시각·최초 안전 FSM 상태 이상·최초 CM 발행/Observer 전달 지연·Guard 내부 age·Scan/Odom/Clock 수신 간격·최초 latch·정확 ActionStatus·Nav2 종료 순서로 진단한다. **실패 즉시 같은 현장 실행을 반복하지 않는다.**

## 증거 보존·민감정보

- 로컬 경로: `$HOME/axia_g07_task04_owner_moving/owner-moving-XXXXXXXX/`
- 로컬 원본 압축: 같은 접두사의 `.tar.gz`, `.tar.gz.sha256`
- **디버깅 제출용 소형 ZIP**: 같은 접두사의 `.diagnostics.zip`, `.diagnostics.zip.sha256`. 허용목록 JSON/짧은 로그/실제 Pose 조회 및 별도 SHA256SUMS만 포함합니다. 전체 SQLite rosbag·빌드/소스 디렉터리는 포함하지 않습니다.
- 압축 내부: `manifest.txt`, `owner_parity.json`, D3D12 GLX 원본, 네이티브 Contact 증거/실행 로그, 실제 SQLite14 rosbag/metadata, Goal/CM/Guard raw event, Lifecycle 종료 원본, `task04_owner_numeric_review.json`, `task04_owner_verdict.json`, `first_failure.txt`, `SHA256SUMS`.
- 원본 출력은 **강사 HOME에만 비공개**로 보관. 사용자 개인 경로·rosbag 전체를 공개 GitHub/CI artifact에 올리지 않는다. 현장 산출물 제출 시 암호/개인 경로 등 민감정보를 비식별화하고 전달 범위를 확인한다.

## 이후 사용자 인수

강사의 실제 화면과 원본 archive/SHA256 제출 이후, `sha256sum -c`·SQLite `quick_check`·Goal UUID/status·RMW source 120ms/Observer 120ms·Guard 내부 TTL150ms·Scan/Odom/Clock300ms·1초 이상 odom ZERO·Contact0·Navigation/Localization ACK·CM clean exit·최초 타이밍 위반 NONE을 **동일 Owner 실행 원본 기준**으로 재검수한다. 그 때만 `AXIA_G07_TASK04_OWNER_MOVING_L3=PASS`, `AXIA_MVP_DEMO_ACCEPTED=PASS` 최종 인수 보고서를 작성한다. 그 전까지는 모두 HOLD. SW 정지는 인증된 E-Stop이 아니므로 항상 `CERTIFIED_ESTOP=false`.

### 브랜치 정책

개발 결과는 공개 CI PR #169 및 Student PR #46의 기능 브랜치에만 보관한다. 강사용 실행기와 학생 TODO 저장소 역할을 혼동하거나 main에 자동 병합하지 않는다.

## 과거 S75 실측 실패 분석 및 이전 배포판 증거 (2026-11-19)

이번 원샷은 현장 S75의 `/scan` 377/377 `/safety/scan` 동일, 353/360 근거리 0.5m 링, 약 4.4초 WSL2 호스트 일시정지, 안전 최초 `BOOT_SAFE`, Goal 미전송을 분석한 후 배포한 **새 소프트웨어 센서 렌더러 후보**입니다. 최초 오류 기록을 외부 래퍼의 generic 실패로 덮지 않고 `pregoal_baseline.json`에서 직접 복원합니다.

- 실제 RED: [센서 렌더러 CI #44356202944](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44356202944), [최초 실패 코드 전파 #44357055395](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44357055395)
- 새 Student 수정 SHA: `c4cc2a7adc0309d9107e35f31d8f3dd95fa8dac2`
- GREEN: 실제 [No-Goal Gazebo #44359662336](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44359662336), 실제 [Moving+GUI #44359652805](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44359652805), 최종 [Owner Bootstrap #44360531447](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44360531447)
- 교육용 근거 보고서: [S75 WSLg GPU LiDAR 진단과 RED→GREEN](AXIA_G07_TASK04_OWNER_S75_WSLG_LIDAR_RED_GREEN_20261119_KO.md)

**주의:** CPU 센서 렌더러 수정이 동일 강사 WSL2의 실제 0.5m 링 및 4.4초 지연까지 해결했는지는 아직 확인하지 않았습니다. 이 새 원샷의 L3 결과는 무조건 HOLD로 시작하며, 한 번의 실제 WSL2 검수 후에만 판정합니다. 실패 시 현장 재실행을 반복하지 않고 소형 진단 ZIP + 원본 TAR를 보존합니다.

## 최종 Pose 파서 회귀와 검수한 배포본

본 인계의 **최종 Student**는 `c4cc2a7adc0309d9107e35f31d8f3dd95fa8dac2`입니다. S75 원본 `gz model --pose`가 출력하는 `[-2.000520 -0.500000 0.010007]`의 실제 공백 구분 좌표가 기존 파서의 `|` 구분만 허용하는 버그로 누락됐습니다. 이를 최초 장애 지점 근거 기반 테스트 [RED #44358905525](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44358905525) → 허용 형식 최소 수정 → 실제 [Gazebo No-Goal L2 #44359662336](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44359662336) 및 [Moving Goal+GUI L2 #44359652805](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44359652805) **SUCCESS**까지 검증하였습니다.

이번 수정은 **진단 기록의 정확성 개선**이며, 처음 S75에서 발생한 WSLg gpu_lidar 근거리 환형 스캔과 4.4초 호스트 공백이 실제 Owner PC에서 해결되었다는 뜻은 아닙니다. 새 원샷은 반드시 강사 WSL2에서 한 번 최종 확인하고, 재발하면 재실행을 반복하지 말고 최초 실패와 최초 안전 TTL 이탈을 정리합니다. `AXIA_MVP_DEMO_ACCEPTED=HOLD`를 유지합니다.

## n7 최초 엄격 검증 실패와 2026-11-19 최종 수정판

- 실제 n7 현장에서는 이동·정지·Goal 취소 성공, 19/21 판정 통과. CM Owner 스키마 불일치 및 Guard 내부 age 미발행이 최초 안전 증거 실패. [근거 보고서](AXIA_G07_TASK04_OWNER_N7_WSL2_RMW_CLOCK_AND_GUARD_DIAGNOSIS_20261119_KO.md).
- RMW seq 483→484에서 raw source 2964.069ms, RMW receive 2964.057ms, monotonic observer 38.418ms. 수정판 숫자 JSON에는 `cm120.source_raw_gap_max_ms`, `clock_step_evidence`, `host_external_clock_verified=false`를 남긴다.
- 최신 Student `dcd1299c03bf702712631dc025b868335cadd1c6`, 공개 판정 `71b85c42ea474276fedd9f345521317b8c348b4e`, 실제 L2 [#44433206283](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44433206283) SUCCESS 21/21. CLI 원샷 `4cd36853358bb088263a0b73a0cfa6c8d5ec2d55`는 이 두 커밋과 L2 Run을 고정.
- Owner `--self-check` = L0, 실제 WSL2 `--run` = 아직 미실행. Guest monotonic 기반 CLOCK_REALTIME 보정은 **안전 인증 아님**; 실제 Windows 호스트 일시정지 부재를 증명하지 못하므로 `host_external_clock_verified=false`. CM/Guard 진짜 지연, 첫 latch 및 감속/정지는 원본으로 다시 검토해야 한다.
- 검증 전에 `AXIA_MVP_DEMO_ACCEPTED=PASS`를 출력하지 않는다. 실패하면 동일 현장 재실행보다 첫 실패·첫 타이밍 위반을 공개 CI 회귀로 먼저 편입한다. 인증된 HW E-Stop으로 보고하지 않는다.
