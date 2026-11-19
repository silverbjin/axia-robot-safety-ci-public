# AXIA G07 Task04 — 강사 WSL2 Moving Goal L3 단일 시연 실행·인수 가이드

2026-11-19 KST / 실제 강사 WSL2 Moving Goal **NOT_RUN** / 배포는 공개 CI 범위 한정 L2 검증 후 / SW Stop ≠ 인증 E-Stop.

## 최신 HFbmAW8N TTY 승인 수정판 출고 증거

| 항목 | 정확한 버전/증거 |
|---|---|
| 공개 CI PR | https://github.com/silverbjin/axia-robot-safety-ci-public/pull/182 |
| Student PR | https://github.com/silverbjin/axia-robot-safety-student/pull/61 |
| 단일 주행 소스 SHA | `efff0fb8bf941de74572336d1988dfb0005e11f7` |
| CI read-only 판정 소스 SHA | `71b85c42ea474276fedd9f345521317b8c348b4e` |
| 실제 Gazebo Harmonic + Nav2 + Waffle + RViz Xvfb L2 | https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44455960504 |
| 출고 Owner 원샷 Bootstrap L0 | [#44456593223 — 8/8 PASS](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44456593223) |
| L2 원본 공개 수치·SHA256 artifact | https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44455960504/artifacts/14497697039 |
| 강사 실제 WSL2 L3 | **HFbm 원본 Goal TTY 승인 180초 대기에서 종료 / 최신 TTY 수정판 미실행** |
| main | **병합 안 함** |

기존 Task01~03 및 Xacro/Localization 종료 성공 증거를 보존한다. 최신 TTY 승인 개선 수정판은 공개 CI #44455960504에서 **실제 Gazebo/Nav2 Moving Goal+GUI 21/21 안전 검증**을 완료했다. Xvfb CI는 Owner WSLg D3D12가 아니므로 L3 승격 불가.

과거 CI #44359652805의 이동 0.198562m, 정지 1.013681초, CM Source 59.330ms, Observer 86.805ms, Guard age 36.842ms는 **이전 실행의 보존된 기록**이다. 최신 #44455960504은 새 Student SHA의 21개 조건 true, first_failure=NONE, rc=0 및 GUI2를 확인하였으며 새 수치 JSON 아티팩트를 별도로 보존했다.

**현장 경계:** 기존 S75 LiDAR, n7 CM/Guard 계측, oZG Xacro/SDF 및 Localization 종료 문제는 각각 별도 코드/CI 증거로 보존했다. 최신 HFbm 원본은 Gazebo/Nav2/PREGOAL이 정상인 뒤 **Goal 승인 입력의 180초 TTY 대기에서 중단**됐고, 출력된 최초 코드는 TIMEOUT/EOF 미분리, 외부 first_failure는 generic으로 은폐했다. 이번 소스는 공개 PTY 18/18 및 실제 Gazebo 21/21 PASS이지만 강사 WSL2의 최신 수동 입력·안전 타이밍은 아직 미검증이다.

기존 실행 명령에서 사용했던 원샷 커밋 `e56bbad873e0e37c83f34ecbcc206cc8a648e63d`은 WSLg D3D12 변수를 전역 export하는 이전 배포 후보이므로 **현장 신규 실행에 사용하지 않는다.** 새 고정 SHA는 동일 Student SHA의 공개 L2 및 원샷 Bootstrap L0를 통과했다.

## 강사 WSL2 복사·붙여넣기 명령 (최신 HFbm TTY 수정판, 하나의 블록)

다음은 **이 시점의 실증 공개 원샷 SHA `cd8c23c52588f5efd6295b6904e15b1aa54496e7`**를 고정한다. CI가 검증한 Student SHA는 내부에서 별도 확인한다. 무작위 main HEAD를 내려받지 않는다.

```bash
(
  set -Eeuo pipefail
  SOURCE_SHA='cd8c23c52588f5efd6295b6904e15b1aa54496e7'
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

**실제 주행 승인:** Gazebo/RViz 창이 뜬 뒤 **원래 원샷을 실행한 WSL2 터미널을 다시 클릭해 포커스**하십시오. PTY 승인 대기 시 터미널 종소리·굵은 구분선·`YES-P2-G07-GOAL` 안내가 표시됩니다. **180초 이내 정확히 입력하고 Enter**를 눌러야 합니다. 자동 응답·파이프·CI 변수로 승인하지 않습니다. 원본 `native_runner.log`에는 입력 내용이 아니라 `OWNER_GOAL_CONSENT_PENDING`/결과/경과 시간만 보존됩니다. 승인 후에도 기존 `admit_owner()`가 PID/세션/SHA를 검증하고, 새 Observer Scan/Odom/Guard/Clock 수신이 300ms 이내인지 START 직전 및 Goal 발행 직전에 다시 확인합니다. 최신 안전 데이터가 부족하거나 Guard latch가 있으면 Goal을 보내지 않습니다.

## 콘솔 기대 패턴

`--self-check` 성공은 ROS를 시작하지 않는 L0이다:

```text
AXIA_G07_TASK04_OWNER_MOVING_BOOTSTRAP_L0_PASS student_sha=efff0fb8bf941de74572336d1988dfb0005e11f7 l2_run=44455960504 NO_ROS_NO_GAZEBO_NO_GOAL
AXIA_G07_TASK04_OWNER_MOVING_L3=NOT_RUN
AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false
```

**현장에서 실제로 성공한 뒤 기대할 패턴 (아직 실행 증거가 아님):**

```text
AXIA_G07_TASK04_STUDENT_SHA_VERIFIED=efff0fb8bf941de74572336d1988dfb0005e11f7
AXIA_G07_TASK04_OWNER_CORE_PARITY_25_5_PASS
AXIA_G07_TASK04_WSLG_D3D12_GPU_SELECTED=...
AXIA_G07_OWNER_GAZEBO_LIDAR_SOFTWARE_RENDERER_SELECTED D3D12_GUI_ONLY
AXIA_G07_TASK04_OWNER_MOVING_BEGIN student_sha=...
[원래 실행한 WSL2 터미널에서 알림·180초 프롬프트 확인 후 직접 입력]
OWNER_GOAL_CONSENT_PENDING timeout_sec=180 goal_sent=false  (native_runner.log)
OWNER_GOAL_CONSENT_ACCEPTED elapsed_sec=...  (native_runner.log)
AXIA_G07_TASK04_OWNER_MANUAL_CONTROLLING_TTY_GOAL_CONSENT_PASS  (native_runner.log)
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

실패하면 rc≠0 및 `AXIA_G07_TASK04_FIRST_FAILURE=...`이 출력됩니다. 승인 실패는 `OWNER_GOAL_CONSENT_TIMEOUT`, `OWNER_GOAL_CONSENT_EOF_OR_TTY_ERROR`, `OWNER_GOAL_CONSENT_DENIED`, `OWNER_GOAL_CONSENT_TTY_UNAVAILABLE`로 구분되며, 확보된 원본 TAR/SHA256와 `task04_owner_verdict.json`의 `HOLD`을 유지한다. 최초 Goal 시각·최초 안전 FSM 상태 이상·최초 CM 발행/Observer 전달 지연·Guard 내부 age·Scan/Odom/Clock 수신 간격·최초 latch·정확 ActionStatus·Nav2 종료 순서로 진단한다. **실패 즉시 같은 현장 실행을 반복하지 않는다.**

## 증거 보존·민감정보

- 로컬 경로: `$HOME/axia_g07_task04_owner_moving/owner-moving-XXXXXXXX/`
- 로컬 원본 압축: 같은 접두사의 `.tar.gz`, `.tar.gz.sha256`
- **디버깅 제출용 소형 ZIP**: 같은 접두사의 `.diagnostics.zip`, `.diagnostics.zip.sha256`. 허용목록 JSON/짧은 로그/실제 Pose 조회 및 별도 SHA256SUMS만 포함합니다. 전체 SQLite rosbag·빌드/소스 디렉터리는 포함하지 않습니다.
- 압축 내부: `manifest.txt`, `owner_parity.json`, D3D12 GLX 원본, 네이티브 Contact 증거/실행 로그, 실제 SQLite14 rosbag/metadata, Goal/CM/Guard raw event, Lifecycle 종료 원본, `task04_owner_numeric_review.json`, `task04_owner_verdict.json`, `first_failure.txt`, `SHA256SUMS`.
- 원본 출력은 **강사 HOME에만 비공개**로 보관. 사용자 개인 경로·rosbag 전체를 공개 GitHub/CI artifact에 올리지 않는다. 현장 산출물 제출 시 암호/개인 경로 등 민감정보를 비식별화하고 전달 범위를 확인한다.

## 이후 사용자 인수

강사의 실제 화면과 원본 archive/SHA256 제출 이후, `sha256sum -c`·SQLite `quick_check`·Goal UUID/status·RMW source 120ms/Observer 120ms·Guard 내부 TTL150ms·Scan/Odom/Clock300ms·1초 이상 odom ZERO·Contact0·Navigation/Localization ACK·CM clean exit·최초 타이밍 위반 NONE을 **동일 Owner 실행 원본 기준**으로 재검수한다. 그 때만 `AXIA_G07_TASK04_OWNER_MOVING_L3=PASS`, `AXIA_MVP_DEMO_ACCEPTED=PASS` 최종 인수 보고서를 작성한다. 그 전까지는 모두 HOLD. SW 정지는 인증된 E-Stop이 아니므로 항상 `CERTIFIED_ESTOP=false`.

### 브랜치 정책

개발 결과는 공개 CI PR #182 및 Student PR #61의 Draft 기능 브랜치에만 보관한다. 강사용 실행기와 학생 TODO 저장소 역할을 혼동하거나 main에 자동 병합하지 않는다.

## 과거 S75 실측 실패 분석 및 이전 배포판 증거 (2026-11-19)

이번 원샷은 현장 S75의 `/scan` 377/377 `/safety/scan` 동일, 353/360 근거리 0.5m 링, 약 4.4초 WSL2 호스트 일시정지, 안전 최초 `BOOT_SAFE`, Goal 미전송을 분석한 후 배포한 **새 소프트웨어 센서 렌더러 후보**입니다. 최초 오류 기록을 외부 래퍼의 generic 실패로 덮지 않고 `pregoal_baseline.json`에서 직접 복원합니다.

- 실제 RED: [센서 렌더러 CI #44356202944](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44356202944), [최초 실패 코드 전파 #44357055395](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44357055395)
- 새 Student 수정 SHA: `c4cc2a7adc0309d9107e35f31d8f3dd95fa8dac2`
- GREEN: 실제 [No-Goal Gazebo #44359662336](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44359662336), 실제 [Moving+GUI #44359652805](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44359652805), 최종 [Owner Bootstrap #44360531447](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44360531447)
- 교육용 근거 보고서: [S75 WSLg GPU LiDAR 진단과 RED→GREEN](AXIA_G07_TASK04_OWNER_S75_WSLG_LIDAR_RED_GREEN_20261119_KO.md)

**주의:** CPU 센서 렌더러 수정이 동일 강사 WSL2의 실제 0.5m 링 및 4.4초 지연까지 해결했는지는 아직 확인하지 않았습니다. 이 새 원샷의 L3 결과는 무조건 HOLD로 시작하며, 한 번의 실제 WSL2 검수 후에만 판정합니다. 실패 시 현장 재실행을 반복하지 않고 소형 진단 ZIP + 원본 TAR를 보존합니다.

## 최종 Pose 파서 회귀와 검수한 배포본

이전 S75 배포판의 **당시 최종 Student**는 `c4cc2a7adc0309d9107e35f31d8f3dd95fa8dac2`였습니다. S75 원본 `gz model --pose`가 출력하는 `[-2.000520 -0.500000 0.010007]`의 실제 공백 구분 좌표가 기존 파서의 `|` 구분만 허용하는 버그로 누락됐습니다. 이를 최초 장애 지점 근거 기반 테스트 [RED #44358905525](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44358905525) → 허용 형식 최소 수정 → 실제 [Gazebo No-Goal L2 #44359662336](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44359662336) 및 [Moving Goal+GUI L2 #44359652805](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44359652805) **SUCCESS**까지 검증하였습니다.

이번 수정은 **진단 기록의 정확성 개선**이며, 처음 S75에서 발생한 WSLg gpu_lidar 근거리 환형 스캔과 4.4초 호스트 공백이 실제 Owner PC에서 해결되었다는 뜻은 아닙니다. 새 원샷은 반드시 강사 WSL2에서 한 번 최종 확인하고, 재발하면 재실행을 반복하지 말고 최초 실패와 최초 안전 TTL 이탈을 정리합니다. `AXIA_MVP_DEMO_ACCEPTED=HOLD`를 유지합니다.

## n7 최초 엄격 검증 실패와 2026-11-19 최종 수정판

- 실제 n7 현장에서는 이동·정지·Goal 취소 성공, 19/21 판정 통과. CM Owner 스키마 불일치 및 Guard 내부 age 미발행이 최초 안전 증거 실패. [근거 보고서](AXIA_G07_TASK04_OWNER_N7_WSL2_RMW_CLOCK_AND_GUARD_DIAGNOSIS_20261119_KO.md).
- RMW seq 483→484에서 raw source 2964.069ms, RMW receive 2964.057ms, monotonic observer 38.418ms. 수정판 숫자 JSON에는 `cm120.source_raw_gap_max_ms`, `clock_step_evidence`, `host_external_clock_verified=false`를 남긴다.
- 최신 Student `dcd1299c03bf702712631dc025b868335cadd1c6`, 공개 판정 `71b85c42ea474276fedd9f345521317b8c348b4e`, 실제 L2 [#44433206283](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44433206283) SUCCESS 21/21. CLI 원샷 `4cd36853358bb088263a0b73a0cfa6c8d5ec2d55`는 이 두 커밋과 L2 Run을 고정.
- Owner `--self-check` = L0, 실제 WSL2 `--run` = 아직 미실행. Guest monotonic 기반 CLOCK_REALTIME 보정은 **안전 인증 아님**; 실제 Windows 호스트 일시정지 부재를 증명하지 못하므로 `host_external_clock_verified=false`. CM/Guard 진짜 지연, 첫 latch 및 감속/정지는 원본으로 다시 검토해야 한다.
- 검증 전에 `AXIA_MVP_DEMO_ACCEPTED=PASS`를 출력하지 않는다. 실패하면 동일 현장 재실행보다 첫 실패·첫 타이밍 위반을 공개 CI 회귀로 먼저 편입한다. 인증된 HW E-Stop으로 보고하지 않는다.

## oZGSnDD1 현장 Gazebo 임시 월드 실패 → CI L2 Localization 종료 실패 → 최종 수정판 (2026-11-19)

- 최초 현장 원본 `owner-moving-oZGSnDD1.tar.gz` SHA256 `316183965070fab7ffdf0c1621d4cacc9fe4d6d5f674aa125791908a90a19569`, 첫 원인은 `gz sim -r -s /tmp/nav2_*.sdf` exit 255. Guard BOOT_SAFE/NO_FRESH_PAIR, `/cmd_vel=0`, Goal 미발행.
- Student H01의 `OnProcessExit` 보호를 Task04 Owner/공개 CI에 재사용, Xacro exit 0과 실제 유효한 SDF XML/World/SHA256 확인 후 Gazebo를 딱 한 번 시작. RED [#44439674602](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44439674602), L0 GREEN [#44440787429](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44440787429) 5/5, 실제 ROS Launch L1 [#44440794690](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44440794690) 3/3.
- 실제 L2 [#44440932197](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44440932197) 및 [#44442176276](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44442176276)에서 Goal·STOP·정확한 cancel 모두 성공했으나 Localization SHUTDOWN ACK가 30.001s, 30.003s에 TIMEOUT. `main` 병합이나 현장 재실행 대신 공개 회귀 테스트 추가. 안전 제어 계층의 타이밍을 완화하지 않음.
- RED [#44443257191](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44443257191), GREEN [#44443374979](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44443374979): Navigation 및 Localization Native Service의 재사용 클라이언트 상태 가능성을 최소 재현. 새 `rclpy` 요청 노드를 각각 독립 할당하되, 기존 Native Client·실제 ACK·30s 한계·1회 요청 조건 보존. Student 최종 commit `6579e2eef7e99691da558cd2de1964fd26a04621`.
- 실제 Gazebo/Nav2 Moving GUI L2 [#44449459417](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44449459417) **SUCCESS, 21/21**, rc=0, Gazebo/RViz GUI2, `first_failure=NONE`, Contact/정지/CM·Guard/Lifecycle 종료 동일 세션 PASS. Source 6579 SHA가 정확히 고정된 결과.
- 실행기 pinned SHA `1816fbbbfdb972e52c5168ade26c768167998556`는 Student 6579, strict review `71b85c42ea474276fedd9f345521317b8c348b4e`, 실제 공개 L2 #44449459417을 고정한다. 공개 Bootstrap [#44450173850](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44450173850) **8/8 PASS**.
- 근거 보고서: `AXIA_G07_TASK04_OZGSnDD1_GAZEBO_WORLD_XACRO_RACE_RED_GREEN_20261119_KO.md`, `AXIA_G07_TASK04_OZG_LOCALIZATION_SHUTDOWN_ACK_RED_GREEN_20261119_KO.md`. 이전 n7 배포판 SHA 4cd368은 기록으로만 남기며 **더 이상 현장에 사용하지 않는다**.
- **L2 PASS는 Owner WSL2/WSLg 실측이나 인증된 E-Stop이 아니다.** Owner L3 원본 TAR/SQLite/ZIP에 실제 Guard 내부 CM age, CM RMW raw 보정 근거, 최초 안전 상태 전이·타이밍 위반 및 Lifecycle ACK를 확인하기 전 최종 인수 HOLD.

```ini
PUBLIC_CI_L0_WORLD_XACRO_ORDER=PASS_5_OF_5
PUBLIC_CI_L1_REAL_ROS_LAUNCH=PASS_3_OF_3_NO_GAZEBO
PUBLIC_CI_L0_SHUTDOWN_ACK_CLIENT=PASS_6_OF_6
PUBLIC_CI_MOVING_GAZEBO_NATIVE_L2=PASS_21_OF_21
OWNER_BOOTSTRAP_L0=PASS_8_OF_8
OWNER_WSL2_L3=NOT_RUN
AXIA_MVP_DEMO_ACCEPTED=HOLD
CERTIFIED_ESTOP=false
MAIN_MERGED=false
```

## HFbmAW8N — 180초 Goal 승인 프롬프트 미인지·첫 오류 은폐 → 실제 PTY 및 Gazebo 회귀 → 최종 출고

- 원본 `owner-moving-HFbmAW8N.tar.gz` SHA256 `a7d8b83c3a86c77dc47bdbd3dbebf76188669c656a0992dbe1c72df7aa1623e1`, `diagnostics.zip` SHA256 `68d55a7f752dbeb81d3457d0294a4b929a186faa08455953c0ae47edd8d1dcd3`. 실제 Gazebo/PREGOAL 성공, `native_runner.log`의 최초 `G07_TASK04_OWNER_TTY_APPROVAL_TIMEOUT_OR_EOF_NO_GOAL`, Goal 0. 원본 최종 `first_failure.txt`는 generic `NATIVE_RUNNER_FAILED_REVIEW_RAW`.
- 공개 PTY 테스트 RED [#44454786009](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44454786009)에서 12개 회귀 실패. 첫 테스트 하네스가 GREEN 오표기한 것은 별도 원인으로 보존하고, 명시적 `exit 1`로 CI false GREEN을 제거했다.
- 새 Student helper `tools/p2_g07_owner_tty_consent.sh`에서 수동 `/dev/tty` 180초 한 번 읽기 + 잘 보이는 프롬프트/종소리 + TIMEOUT/EOF/DENIED/TYY_MISSING 구분. 입력한 문자열은 로그에 기록하지 않는다. Goal 직전 real Scan/Odom/Guard/Clock 유효성 300ms, Guard latch false를 다시 확인. 기존 CM/Guard 안전 TTL 및 Nav2/Goal 취소 알고리즘 변경 없음.
- 기존 shell contract도 helper 실제 소스와 호출자 연결을 모두 검사하도록 강화. 공개 [#44455880013](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44455880013) **18/18 PASS** (Owner first failure 5/5 + 실물 PTY/TTL 8/8 + 기존 실행기 shell 5/5).
- 정확한 최종 Student SHA `efff0fb8bf941de74572336d1988dfb0005e11f7`, 공개 CI 실제 Gazebo/Nav2+Waffle+Moving Goal+GUI2 L2 [#44455960504](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44455960504) **SUCCESS 21/21**, `runner_rc=0`, `first_failure=NONE`, 실제 Contact/CM/Guard/Goal·정지 및 정상 종료 같은 세션에 검증.
- 최종 immutable Owner 실행기 SHA **`cd8c23c52588f5efd6295b6904e15b1aa54496e7`**는 Student `efff0fb...`, 공개 판정 `71b85c42...`, 성공 L2 `44455960504` 고정. CI [#44456593223](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44456593223) **Owner Bootstrap 8/8 PASS**. TTY 헬퍼 존재·문법 검사도 Goal 전에 추가.
- 강사용 오류 해결 교육용 보고서: `AXIA_G07_TASK04_HFBMAW8N_TTY_CONSENT_RED_GREEN_20261119_KO.md`. 이전 oZG/T08 SHA를 신규 실행에 사용하지 않는다.
- 실제 강사 WSL2에서는 프롬프트를 출력하는 **원래 터미널 창**에 포커스를 주고, Goal 전 지정 문구를 직접 입력한다. 입력 못하면 Goal 0·HOLD이며 새 ZIP/TAR 분석 전 현장 재시도 반복 금지.

```ini
PUBLIC_CI_HFBM_PTY_L0=PASS_18_OF_18
PUBLIC_CI_REAL_MOVING_GAZEBO_L2=PASS_21_OF_21_RUN_44455960504
OWNER_BOOTSTRAP_L0=PASS_8_OF_8_RUN_44456593223
OWNER_WSL2_L3=NOT_RUN
AXIA_MVP_DEMO_ACCEPTED=HOLD
CERTIFIED_ESTOP=false
MAIN_MERGED=false
```
