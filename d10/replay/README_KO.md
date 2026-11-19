# AXIA D10-LIVE-REPLAY-01 — 오프라인 합성 파형 관제 데모

- **기능:** C01 `test_mixed.csv` + C03 `if_scores_test.csv`를 **기록 데이터로 재생**하는 단일 HTML 생성기.
- **학습 목표:** ① Isolation Forest 기반 이상신호 탐지 구조 이해, ② 정상 패턴 기준 이상탐지 및 조기 경고 검증 실습.
- **비기능:** ROS2/Gazebo 실행, 새 AI 모델 학습·추론, 실시간 센서 수신, 안전제어·Stop·Goal·`cmd_vel` 발행 없음.
- **공개 코드:** 표준라이브러리 Python 3.12로 검증하며 `build_replay.py`, `replay_template.html`, `test_replay.py`, `owner_one_shot.sh`만 보존. **강사 비공개 정답·점수 CSV·생성된 강사용 HTML을 공개 CI에 올리지 않음**.

## 1. 강사 WSL2 원샷 — 공개 CI 확인된 40자리 SHA 사용

강사 저장소 접근권한이 필요합니다. 이미 `~/axia_d10_course/axia-robot-safety-instructor` 또는 `~/axia_d09_course/axia-robot-safety-instructor`를 클론했다면 재클론하지 않습니다. 다음 예시에서 `<CI_GREEN_PUBLIC_SHA>`를 해당 PR의 **검증된 40자리 커밋 SHA**로 바꾸십시오. 첫 설치 시 비공개 GitHub 인증이 필요할 수 있습니다.

```bash
(
  set -Eeuo pipefail
  export AXIA_D10_REPLAY_PUBLIC_SHA="<CI_GREEN_PUBLIC_SHA>"
  SH="$(mktemp --suffix=.sh)"
  trap 'rm -f "$SH"' EXIT
  curl -fLsS --retry 3 --max-time 90 \
    "https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public/$AXIA_D10_REPLAY_PUBLIC_SHA/d10/replay/owner_one_shot.sh" \
    -o "$SH"
  bash -n "$SH"
  bash "$SH"
)
```

**기준 성공 패턴:**

```text
D10_REPLAY_L0_PASS ... traces=14 windows=104 valid=100 quality=4 tp=1 fp=2 fn=17 tn=80 ... ros_actual=false gazebo_actual=false
D10_REPLAY_OWNER_GENERATED=/home/.../AXIA_D10_LIVE_REPLAY_INSTRUCTOR.html
```

**출력:** `~/axia_d10_course/AXIA_D10_LIVE_REPLAY_INSTRUCTOR.html` (단일 파일), `axia_d10_replay_build.log`, `axia_d10_replay_minimal_logs.tar.gz` (작은 로그만). Windows의 Edge/Chrome에서 생성 HTML을 열면 **인터넷 없이 동작**합니다. `explorer.exe` 자동 열기는 환경마다 다르므로, 열리지 않으면 직접 더블클릭하십시오.

별도 경로의 비공개 클론을 사용할 때에는 실행 전에 다음 환경변수만 지정하십시오.

```bash
export AXIA_D10_INSTRUCTOR_BLOCK_C="$HOME/other/axia-robot-safety-instructor/training/block_C"
export AXIA_D10_REPLAY_OUT="$HOME/axia_d10_course/my_demo.html"
```

## 2. 화면 조작 / 10분 수업 시나리오

1. **TST_A_00**을 선택하고 `재생`(1×/2×/4×) 또는 `다음 Window`로 5.9초(W5)까지 이동합니다. 먼저 학생에게 Warning 발생 위치를 **예측**시킵니다.
2. **AI 판정 공개**를 클릭하면 W5의 참양성 WARNING과 기준 점수 `0.10201593 > 0.10199750`이 나옵니다.
3. **정답·오차 해설 공개**를 누르면 4.0~6.9초 주입 구간과 **합성 첫 탐지 지연 1.9초**가 보입니다.
4. **TST_A_02**로 바꾸면 자동으로 정답을 숨긴 상태로 처음부터 시작합니다. 토크가 점점 상승하더라도 주입 중 WARNING이 없는 **미탐(FN)**을 확인합니다.
5. **TST_A_04**의 W8로 이동해 AI 판정→정답을 차례로 공개하면, 이상 주입 종료 후 정상 라벨 윈도우의 **FP**를 확인합니다.
6. **TST_Q_00**을 선택하고 마지막으로 이동하면 `INSUFFICIENT_DATA`를 볼 수 있습니다. 이 Trace는 정상/경고 점수를 내면 안 됩니다.

`다시 숨기기`는 학생 예측 모드로 돌아가고, Trace를 바꾸면 재생 시각과 정답 공개 상태를 초기화합니다. 재생 위치를 이동하는 것은 **합성 기록의 시간 탐색**이며 실시간 물리 실행이나 추론이 아닙니다.

## 3. 공개 CI 검증 범위

공개 CI는 학생의 공개 C01 fixture 고정 SHA를 체크아웃하여, **AI 정답이 아닌 독립 가상 점수**를 생성합니다. 6개 회귀 테스트로 단일 HTML 출력, 104점수·4품질의 조인, 위험점수 판정 불일치·타임스탬프 오염 차단, 오프라인 구성 및 `node --check`를 확인합니다. 강사 비공개 IF 코드/점수/HTML을 공개 CI에서 실행하지 않습니다.

강사용 로컬 검증(본 작업의 산출물)은 두 원본 파일의 Git Blob과 SHA256을 기존 저장소와 정확히 대조했고, Chromium headless에서 Window 이동·AI 판정·정답·품질·재생/일시정지 및 모바일 렌더를 시험한 것입니다. 실제 강사 WSL2 Edge 화면·Windows Office·ROS/Gazebo·Guard TTL은 **미검증**입니다.

## 4. 실패 경계

- `D10_PUBLIC_SHA_INVALID` → 공개 CI로 확인한 **정확한** 40자리 SHA를 지정합니다. 브랜치나 `main` 이동값을 사용하지 마십시오.
- `D10_PRIVATE_SOURCE_NOT_FOUND`/`D10_PRIVATE_AUTH_HOLD` → 강사 비공개 클론/자격증명 확인. 강사용 점수 CSV를 공개 저장소로 복제하지 마십시오.
- `D10_REPLAY_CONTRACT_FAIL` → 첫 raw/score SHA, Trace/window/timestamp/quality/prediction 오류를 확인; 원본을 조작하거나 Test cutoff를 재튜닝하지 마십시오.
- `D10_BROWSER_OPEN_HOLD` → 생성된 HTML을 Edge/Chrome으로 직접 엽니다. 생성 성공을 브라우저 GUI 실행 성공으로 승격하지 마십시오.

제품 MVP 범위를 유지합니다. 합성 리플레이의 WARNING은 **비인증 교육용 판단**이며 Safety Supervisor·FSM·실제 E-Stop과 혼동하지 마십시오.
