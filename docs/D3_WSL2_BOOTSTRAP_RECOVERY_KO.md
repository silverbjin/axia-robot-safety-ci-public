# AXIA D3 v2 — WSL2 반복적 No such file 오류 자동 복구

- 생성: 2026-11-09
- 공개 배포 위치: silverbjin/axia-robot-safety-ci-public 의 fix/d3-wsl2-bootstrap-safe-20261109 브랜치
- 대상 비공개 소스 SHA: 0be687ee033233fcd53be1190e0b2f9e86730fc9
- 범위: Instructor D3 소스 경로 검사, 안전한 체크아웃·빌드·preflight. Goal/Fault/GUI 실행 없음
- **중요:** CI에서 Git 회귀시험을 통과하기 전에는 이 스크립트를 최종 배포본으로 판정하지 않는다.

## 원인

이전 명령은 ~/axia_d3_classroom/axia-d3-instructor/.git 존재 여부만 검사했다.
기존 디렉터리가 D03 브랜치 또는 더 오래된 HEAD인 경우에도 clone을 건너뛰고
존재하지 않는 training/d03/d3_demo/scripts/d3_wsl2_prepare_once.sh 를 실행했다.
대화형 터미널 자체에 set -euo pipefail 을 적용하여 오류 코드 127에서 터미널도 종료됐다.

## 안전한 일괄 복구

다음 명령은 원격 GitHub에 게시된 별도 bootstrap을 **자식 Bash 프로세스**에서 실행한다.
대화형 셸에는 set -e를 적용하지 않는다. SHA256을 검사한 후 실행한다.
**CI에서 확인한 불변 커밋 URL로 교체해 사용할 것.**

~~~bash
bash -c '
set -euo pipefail
tmp="$(mktemp)"
trap "rm -f -- \"$tmp\"" EXIT
curl -fL --retry 3 -sS -o "$tmp" \
  "https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public/<PUBLIC_CI_VERIFIED_COMMIT_SHA>/scripts/d3_wsl2_bootstrap_safe.sh"
printf "%s  %s\n" "<PUBLISHED_SCRIPT_SHA256>" "$tmp" | sha256sum -c -
bash "$tmp" --prepare
'
~~~

이미 내려받은 뒤에는 언제든 다음 한 명령으로 재진입한다.

~~~bash
bash "$HOME/axia_d3_classroom/axia-d3-prepare.sh" --prepare
~~~

정상 단계 출력:
- [PRESERVE] : 이전 경로를 건드리지 않고 격리 폴더로 복구 (필요한 경우에만)
- [SOURCE_PIN_VERIFIED] : Instructor 소스 브랜치와 정확한 SHA 확인
- [READY] D3_V2_SOURCE_BUILD_SESSION_PREFLIGHT : ROS2 빌드·preflight 완료. GUI·실주행 통과 아님

## 이후 강사 터미널

~~~bash
source "$HOME/axia_d3_classroom/d3_checkout.env"
cd "$AXIA_D3_REPO_ROOT"
source "$HOME/axia_d3_classroom/d3_session.env"
bash training/d03/d3_demo/scripts/run_d3_instructor.sh --launch
~~~

가상 사람 모델 이동은 별도 터미널에서 현재 Gazebo world·좌표를 확인한 뒤 기존
training/d03/d3_demo/docs/RUNBOOK_D3_V2_WSL2_KO.md 의 preview/live 절차를 사용한다.
단, 모든 경로는 하드코딩 대신 위 AXIA_D3_REPO_ROOT를 사용한다.

## 보호 규칙

1. 기존 checkout의 브랜치·원격·청결성·필수 파일을 확인한다.
2. 조건이 다르면 기존 checkout을 **삭제/강제 reset/강제 switch 하지 않는다.**
3. 별도 경로 axia-d3-instructor-v2-0be687ee 를 우선 사용한다.
4. 정확한 Instructor SHA가 아닐 경우 PIN_MISMATCH로 중지하며 임의 최신 커밋을 실행하지 않는다.
5. 결과 경로는 $HOME/axia_d3_classroom/d3_checkout.env 에 저장한다.
6. Fault Injector와 Nav2 Goal은 실행하지 않는다. 인증 HW E-Stop과 혼동하지 않는다.
7. 비공개 Instructor 정답 및 Hidden Tests는 공개 CI에 포함하지 않는다.

## 테스트 범위

RED: 스크립트가 없을 때 9개 중 8개 실패.
GREEN+REFACTOR: 임시 로컬 Git bare 저장소 기반 11/11 PASS.
GitHub Actions는 별도의 d3-bootstrap-safe-tests.yml 에서 bash -n 및 11개 회귀 검증.
ROS2 Jazzy, Gazebo Harmonic, WSL2 실제 GUI 동작은 여기서 실행하지 않으며 별도 Owner 검증이 필수.
