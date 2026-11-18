# AXIA G07 Task04 — 강사 WSL2 Moving Goal L3 단일 시연 실행·인수 가이드

2026-11-18 KST / 실제 강사 WSL2 Moving Goal **NOT_RUN** / 배포는 공개 CI 범위 한정 L2 검증 후 / SW Stop ≠ 인증 E-Stop.

## 검증한 고정 공개 소스와 단계

| 항목 | 정확한 버전/증거 |
|---|---|
| 공개 CI PR | https://github.com/silverbjin/axia-robot-safety-ci-public/pull/169 |
| Student PR | https://github.com/silverbjin/axia-robot-safety-student/pull/46 |
| 단일 주행 소스 SHA | `d7ffec1ce73f0c4e672ea0fc51a1678139dc5a6f` |
| CI read-only 판정 소스 SHA | `08fef7f78459c915a29f15fe07a4a60b213b46d7` |
| 실제 Gazebo Harmonic + Nav2 + Waffle + RViz Xvfb L2 | https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44268914763 |
| 출고 Owner 원샷 Bootstrap L0 | https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44269770417 |
| L2 원본 공개 수치·SHA256 artifact | https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44268914763/artifacts/14411537039 |
| 강사 실제 WSL2 L3 | **실행 전, 미검증** |
| main | **병합 안 함** |

사전 성공인 NO_GOAL GUI나 Task03 기존 L2는 다시 실행하지 않는다. 이번 출고 후보는 공개 CI Run #44268914763에서 **하나의 실제 Moving Goal+GUI 통합 실행**으로 안전수치·정확 UUID CANCELED·Native Contact0·SQLite14·Nav2 Lifecycle ACK와 CM clean exit 검증을 마쳤다. 다만 공개 Xvfb는 Owner WSLg D3D12가 아니므로 L3 승격 불가.

기존 실행 명령에서 사용했던 원샷 커밋 `e56bbad873e0e37c83f34ecbcc206cc8a648e63d`은 WSLg D3D12 변수를 전역 export하는 이전 배포 후보이므로 **현장 신규 실행에 사용하지 않는다.** 새 고정 SHA는 동일 Student SHA의 공개 L2 및 원샷 Bootstrap L0를 통과했다.

## 강사 WSL2 복사·붙여넣기 명령 (하나의 블록)

다음은 **이 시점의 실증 공개 원샷 SHA `8a11485ed393ee80dadf0dc55aa21e2baf06fcd8`**를 고정한다. CI가 검증한 Student SHA는 내부에서 별도 확인한다. 무작위 main HEAD를 내려받지 않는다.

```bash
(
  set -Eeuo pipefail
  SOURCE_SHA='8a11485ed393ee80dadf0dc55aa21e2baf06fcd8'
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

강사 WSL2 Ubuntu 24.04에서 실행. 실행기는 고정된 Student와 공개 CI 코드의 SHA를 확인하고, 기존 Nav2 공식 overlay(자동 발견 또는 `AXIA_NAV2_OVERLAY_SETUP` 지정), ROS 2 Jazzy/Gazebo Harmonic, 공식 25개 package/5개 SHA, D3D12 GPU 렌더러를 확인한다. **D3D12 어댑터 환경변수는 Gazebo·RViz GUI 자식 프로세스에만 적용하고, Gazebo 물리·센서 서버 및 ROS 안전 노드에는 전역 적용하지 않는다.** 필수 Gazebo 개발 헤더가 없는 경우에만 `sudo apt`의 빌드용 패키지 설치를 요청할 수 있다. 그 외 별도 ROS 노드 실행 명령이나 GUI 디버깅 터미널은 불필요.

사전 준비가 끝나면 이미 정해진 ROS Domain/GZ Partition 안에 Gazebo 서버 **한 개**와 read-only GUI 클라이언트, RViz가 실행된다. 실물 로봇이 아닌 **시뮬레이션만** 대상이다.

**실제 주행 승인:** 실행기는 기존 Student 소스의 실제 `/dev/tty`로 `YES-P2-G07-GOAL`을 요구한다. 강사가 키보드로 정확히 입력해야 한다. 자동 응답·파이프·CI 환경변수로 대체하지 않는다. 실제 TTY 승인 이후에도 Goal 발행 전 기존 `admit_owner()`가 Supervisor/CM/Guard의 정확 PID·세션과 Student Git SHA를 재검증합니다. 이 검사에 실패하면 Goal을 전송하지 않습니다.

## 콘솔 기대 패턴

`--self-check` 성공은 ROS를 시작하지 않는 L0이다:

```text
AXIA_G07_TASK04_OWNER_MOVING_BOOTSTRAP_L0_PASS student_sha=d7ffec1ce73f0c4e672ea0fc51a1678139dc5a6f l2_run=44268914763 NO_ROS_NO_GAZEBO_NO_GOAL
AXIA_G07_TASK04_OWNER_MOVING_L3=NOT_RUN
AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false
```

**현장에서 실제로 성공한 뒤 기대할 패턴 (아직 실행 증거가 아님):**

```text
AXIA_G07_TASK04_STUDENT_SHA_VERIFIED=d7ffec1ce73f0c4e672ea0fc51a1678139dc5a6f
AXIA_G07_TASK04_OWNER_CORE_PARITY_25_5_PASS
AXIA_G07_TASK04_WSLG_D3D12_GPU_SELECTED=...
AXIA_G07_TASK04_OWNER_MOVING_BEGIN student_sha=...
[강사가 controlling TTY에 YES-P2-G07-GOAL 직접 입력]
AXIA_G07_TASK04_OWNER_NATIVE_RUNNER_RC=0
AXIA_G07_TASK04_OWNER_WSLG_GAZEBO_RVIZ_WINDOWS_PASS
AXIA_G07_TASK04_OWNER_SINGLE_NATIVE_NUMERICAL_CANDIDATE_PASS_SCOPED
AXIA_G07_TASK04_OWNER_VISUAL_AND_RAW_REVIEW_PENDING
AXIA_G07_TASK04_ARCHIVE=/home/.../owner-moving-XXXXXXXX.tar.gz
AXIA_G07_TASK04_SHA256=/home/.../owner-moving-XXXXXXXX.tar.gz.sha256
AXIA_G07_TASK04_OWNER_NUMERICAL_CANDIDATE=PASS_SCOPED_RAW_REVIEW_PENDING
AXIA_G07_TASK04_OWNER_MOVING_L3=HOLD
AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false
```

실패하면 rc≠0 및 `AXIA_G07_TASK04_FIRST_FAILURE=...`이 출력되며, 확보된 원본 TAR/SHA256와 `task04_owner_verdict.json`의 `HOLD`을 유지한다. 최초 Goal 시각·최초 안전 FSM 상태 이상·최초 CM 발행/Observer 전달 지연·Guard 내부 age·Scan/Odom/Clock 수신 간격·최초 latch·정확 ActionStatus·Nav2 종료 순서로 진단한다. **실패 즉시 같은 현장 실행을 반복하지 않는다.**

## 증거 보존·민감정보

- 로컬 경로: `$HOME/axia_g07_task04_owner_moving/owner-moving-XXXXXXXX/`
- 로컬 압축: 같은 접두사의 `.tar.gz`, `.tar.gz.sha256`
- 압축 내부: `manifest.txt`, `owner_parity.json`, D3D12 GLX 원본, 네이티브 Contact 증거/실행 로그, 실제 SQLite14 rosbag/metadata, Goal/CM/Guard raw event, Lifecycle 종료 원본, `task04_owner_numeric_review.json`, `task04_owner_verdict.json`, `first_failure.txt`, `SHA256SUMS`.
- 원본 출력은 **강사 HOME에만 비공개**로 보관. 사용자 개인 경로·rosbag 전체를 공개 GitHub/CI artifact에 올리지 않는다. 현장 산출물 제출 시 암호/개인 경로 등 민감정보를 비식별화하고 전달 범위를 확인한다.

## 이후 사용자 인수

강사의 실제 화면과 원본 archive/SHA256 제출 이후, `sha256sum -c`·SQLite `quick_check`·Goal UUID/status·RMW source 120ms/Observer 120ms·Guard 내부 TTL150ms·Scan/Odom/Clock300ms·1초 이상 odom ZERO·Contact0·Navigation/Localization ACK·CM clean exit·최초 타이밍 위반 NONE을 **동일 Owner 실행 원본 기준**으로 재검수한다. 그 때만 `AXIA_G07_TASK04_OWNER_MOVING_L3=PASS`, `AXIA_MVP_DEMO_ACCEPTED=PASS` 최종 인수 보고서를 작성한다. 그 전까지는 모두 HOLD. SW 정지는 인증된 E-Stop이 아니므로 항상 `CERTIFIED_ESTOP=false`.

### 브랜치 정책

개발 결과는 공개 CI PR #169 및 Student PR #46의 기능 브랜치에만 보관한다. 강사용 실행기와 학생 TODO 저장소 역할을 혼동하거나 main에 자동 병합하지 않는다.
