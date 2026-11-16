# AXIA G07 통합 MVP — Cycle 34 인계 및 부트스트랩 회귀 수정 보고서

- 기준 시각: 2026-11-16 KST
- 원 대화: `05_P4_AXIA_G07_UNIFIED_MVP_2`
- 권위 있는 인수 기준: `AXIA_Robot_Safety_MVP_Baseline_Scenario_Acceptance_v1_KO.md` 및 승인된 축소 `AXIA_MVP_DEMO_ACCEPTED` 프로파일
- 대상: ROS 2 Jazzy / Gazebo Harmonic / 공식 TurtleBot3 Waffle·Nav2 / WSL2 Ubuntu 24.04
- **인수 판정: `AXIA_MVP_DEMO_ACCEPTED=HOLD` — 강사 WSL2 신규 소스 실제 L3 주행 미실행**
- 하드웨어 인증 E-Stop이 아닌 시뮬레이션 SW 정지. 임의 Goal·재시도·안전 TTL 완화 불허.

## 1. 출처가 고정된 최신 기준선

| 항목 | SHA·Run·범위 |
|---|---|
| 검증된 P4 구형 기능 기준선 | Instructor `db1eec05e01e1db0d0d2e0c05610806ef4e499f9`; 기존 Gazebo L2 #43674784552 성공(새 GUI와 다른 소스) |
| 현재 G07 Cycle 33 실제 Gazebo L2 | public Run [43824411236](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43824411236), conclusion=success; workflow SHA `f96add0db55ffba28943c5d3739703c3fc503a0b` |
| 현재 L2 Instructor 동일 소스 | `420fd276ec1018f7fcc3f14873693cad02f080b4`, tree `5ca77fb0bedd597b89b791e0931b42ea5a9cbdc9` |
| 최신 Owner 공개 소스 고정점 | `f4b05a1d593385445308acd43af57a9faad1c788`, tree `f4dbe38e071b168baaa7ed1f4cd967ed968978fc` |
| Cycle 34 검증된 부트스트랩 수정 | `42d78b41b62d8d7153bbb0b67dc360d7b87f2169`, 브랜치 `release/g07-cycle33-owner-wsl2-20261116` |
| 이전 통합 Instructor 브랜치 | `integration/g07-mvp-consolidated-20261115` @ `db1eec05e01e1db0d0d2e0c05610806ef4e499f9`; 전체 변경 일괄 merge 금지 |
| 이전 통합 공개 CI 브랜치 | `integration/g07-unified-ci-20261115` @ `5073beb09eb3b18ed4383814e953d454d4a3035b` |
| 아직 독립 보존되는 P4 PR | Instructor [#176](https://github.com/silverbjin/axia-robot-safety-instructor/pull/176) Draft; main 미병합 |

일치하는 SHA끼리만 증거를 합산한다. 구형 D06 실패 #43676794777과 구형 P4 성공 #43674784552를 새 통합 소스의 반복시험으로 계산하지 않는다.

## 2. 실제 L2에서 성공한 것과 아직 검증되지 않은 것

[공개 Actions #43824411236](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43824411236)은 한 Gazebo/Nav2 시뮬레이션 Goal에서 CLEAR→SLOW→STOP, 물리 LiDAR, Odom 정지 지속 약 1.009초, 목표 Cancel ACK, Navigation/Localization shutdown ACK, CM exit 0, 14-topic bag, Gazebo ECM Contact 0/28,087 iterations를 검증했다. 실측 7채널 최대 관찰 간격(ms)은 clock 101.835, CM 118.762, Guard 76.289, Odom 114.867, Scan 212.874, Source 80.786, Supervisor 80.772이고 native CM RMW source 최대는 119.499ms이다.

- **증명된 범위**: 위 정확한 Instructor SHA/tree, 공개 CI의 container/Xvfb·CPU 배치, 한 번의 실제 Gazebo 주행과 정지.
- **검증되지 않은 범위**: 강사 WSLg Gazebo/RViz 화면, GPU 렌더링, WSL2 커널·DDS 스케줄링, 실제 Owner 첫 CM/Guard 전이, 장애 재발률, 여러 번의 독립 주행. #43824411236 성공은 이 항목의 PASS가 아님.
- **원인 규명 보류**: 이전 Owner 첫 Guard TTL 위반(예: 174ms)을 신규 변경이 인과적으로 제거했는지 증명되지 않았다. 최신 CI 분류기도 `g07_timing_resolved=false`를 표시한다. 해당 값은 자동 인수 근거로 쓰지 않는다.
- **S02 Contact 범위**: 동일 Goal의 Native Contact 0은 *충돌 없음* 증거다. 충돌 감지 positive-control의 별도 검증과 동일시하지 않는다.
- **다른 안전 계층**: 150ms CM/Guard/Supervisor 및 300ms Scan TTL 등 원래 정책은 그대로 유지한다. 한 계층의 개선만으로 통합 안정성을 보증하지 않는다.
- **정식 v1 vs 축소 프로파일**: v1 G11 15회·G13 다중 PC·G12 학생 배포는 별도이다. 축소 프로파일이라도 S01~S05 각각 적격 근거, G02~G04 증거 서명, G07 최초 타이밍 및 S02 증거, 강사 WSL2 최종 인수는 면제되지 않는다.

## 3. 이번 Cycle 34 — 재현 가능한 최초 결함 및 최소 수정

**최초 차단 지점**: 공개 Owner 부트스트랩 `scripts/axia_g07_cycle33_owner_wsl2_bootstrap.sh`가 실제로 고정한 Git SHA `f4b05a1d...`의 워크트리에서 `d06/acceptance/g07_cycle33_owner_ci_gate_v3.json`, `d06/live/g07_cycle33_owner_ci_gate_v4.py`를 요구함. 해당 파일은 존재하지 않으며, 동일 커밋에 실제 검증된 `..._v1.json`, `..._v1.py`는 존재한다. 기존 CI는 해당 실행기 `--self-check`와 Owner 서브스크립트의 preflight만 검증해 이 불일치를 놓쳤다. **모든 분기는 Goal 전 단계에서 차단되었지만 현장 운영을 막는 릴리스 오류**다.

| 순서 | 내용 | 실제 결과 |
|---|---|---|
| RED | `d06/tests/test_g07_cycle33_owner_release.py`에 고정 체크아웃의 Gate·Checker·Owner 파일 존재를 요구하는 시험 추가 | Run [43828695371](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43828695371) failure; `Ran 10 tests`, `FAIL ... missing GATE: ...v3.json`; RED SHA `02b40d06362207c1afc7be80b1b5da1261e9af69` |
| GREEN | `scripts/axia_g07_cycle33_owner_wsl2_bootstrap.sh`의 2개 경로를 실제 v1 계약으로 수정 | commit `42d78b41b62d8d7153bbb0b67dc360d7b87f2169` |
| REVIEW/검증 | 같은 공개 브랜치의 Ubuntu 24.04 CI에서 unit 10개, `bash -n` 3개, 실제 L2 live GitHub receipt, 고정 공개 SHA fetch, 기존 Owner 실행 이력 보존·재실행 차단 | Run [43828818188](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43828818188) **success**, `Ran 10 tests ... OK`, `AXIA_G07_CYCLE33_EXACT_OWNER_PUBLIC_FETCH_OLD_FAILED_LOCK_NO_ROS_NO_GOAL_PASS` |

이전 실수로 구문 오류가 들어간 초안 RED #43828563427은 결함의 유효한 재현 시험으로 계산하지 않는다. 수정된 실제 missing-GATE RED #43828695371만 인용한다. **이번 코드 변경은 실행기 경로 두 개뿐**이며 안전 정책, Goal 전송, Guard, TTL, 공식 패키지는 변경하지 않았다.

## 4. Owner WSL2 단일 실행 — 공개 CI GREEN 후 한 번만

기준 환경: WSL2 Ubuntu 24.04, ROS 2 Jazzy, Gazebo Harmonic, WSLg `DISPLAY`, `git`, `gh`(private Instructor 읽기 권한으로 로그인). **실제 사람의 터미널에서만 실행**. 아래 명령은 스스로 Goal에 동의하지 않으며, 기존 동일 SHA+Run 시도가 있으면 재실행을 거부한다.

```bash
(
  set -Eeuo pipefail
  PUBLIC_SHA="42d78b41b62d8d7153bbb0b67dc360d7b87f2169"
  SCRIPT="$(mktemp)"
  trap 'rm -f -- "$SCRIPT"' EXIT
  curl -fL --retry 3 -sS \
    "https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public/${PUBLIC_SHA}/scripts/axia_g07_cycle33_owner_wsl2_bootstrap.sh" -o "$SCRIPT"
  bash -n "$SCRIPT"
  bash "$SCRIPT"
)
```

예상 preflight: `AXIA_G07_CYCLE33_PUBLIC_SHA_VERIFIED=f4b05a...`, `AXIA_G07_CYCLE33_CI_REAL_GUI_L2_PASS_RUN=43824411236`, `AXIA_MVP_DEMO_ACCEPTED=HOLD`. 실 Goal 수행 여부는 물리 TTY에서 `YES-P2-G07-GOAL`을 직접 입력해야만 결정된다. 이 명령을 실행하지 않았다면 `L3_NOT_RUN`이며, 명령 성공/CI GREEN만으로도 `AXIA_MVP_DEMO_ACCEPTED=PASS`로 승격하지 않는다.

## 5. 최종 인수의 판정표 — 다음 작업의 정확한 시작점

1. **Owner WSLg 단 한 번**: 진짜 Gazebo 환경·Waffle·RViz에서 로봇 이동, CLEAR/SLOW/STOP, 최초 CM/Guard 안전 타이밍, 목표 ACK 및 Clean shutdown을 실측하고 캡처한다. CI Xvfb가 대체할 수 없다. 새 source + CI L2 run의 동일 시도 잠금은 유지한다.
2. **증거 자동 보관**: 현장 Runner가 `~/axia_p2_private_evidence` 원본, `~/axia_d06_gazebo_rviz_owner_*` 진단, SHA256/지원 번들을 수집한다. 원본을 공개 CI나 학생 저장소에 업로드하지 않는다.
3. **최초 오류 우선**: 실패 시 최초 `Guard` 상태 전이·CM source/receive·RMW sequence·Supervisor/Scan/Odom TTL의 최초 경계를 먼저 분석한다. 후속 `SHUTDOWN`, `GOAL` 예외는 최초 원인으로 단정하지 않는다.
4. **재실행 금지**: 동일 소스/Run에서 이미 Goal 시도했다면 재시도를 권하지 않는다. 재현 가능한 첫 실패 경계를 **공개 CI 회귀**에 편입해 RED→GREEN→REVIEW→COMMIT 후 새 SHA로 인수해야 한다.
5. **종합 판단**: 강사 화면, 첫 안전 전이, 타이밍, 충돌 및 원본 증거, G02~G04와 S01~S05 증거 원장을 검토해 `AXIA_MVP_DEMO_ACCEPTED`를 별도로 결정. G11/G12/G13을 축소 프로파일의 조건인 것처럼 추가하지 않는다.

### 분리해 유지할 저장소/정책

- Private Instructor: `silverbjin/axia-robot-safety-instructor`, 정답·원본·비공개 테스트.
- Public CI: `silverbjin/axia-robot-safety-ci-public`, 실행 계약·비식별 회귀·공개 보고서.
- Student: `silverbjin/axia-robot-safety-student`; 이번 Cycle 34 변경 없음.
- `main`에 **병합하지 않았다**. 병합은 명시적 사용자 승인 이후에만 수행한다.

## 6. 후속 개발창에 전달할 지시

```text
AXIA G07 Cycle34 GREEN 인계: 이 문서의 SHA/Run을 먼저 다시 확인하라.
실제 Gazebo L2 #43824411236 PASS와 Owner 릴리스 L0 #43828818188 PASS는
검증 범위가 서로 다르며, 강사 WSL2 L3는 아직 NOT_RUN이다.
신규 private SHA=420fd276ec1018f7fcc3f14873693cad02f080b4;
Owner bootstrap 공개 배포 SHA=42d78b41b62d8d7153bbb0b67dc360d7b87f2169.
원본 실패·시도 lock 보존, 동일 Goal 재실행 금지. 150/300ms TTL 변경 금지.
가능하면 새 기능 개발을 중지하고 Owner 단일 WSLg 인수 검증에서 시작한다.
첫 오류 발생 시 PUBLIC CI 재현 가능한 최초 Guard/CM 안전 경계만
RED→GREEN 검증 후 새 pinned 릴리스로 교체하라.
AXIA_MVP_DEMO_ACCEPTED=HOLD, E-Stop 인증 주장 금지, main 병합 금지.
```

**정리:** Cycle 34의 부트스트랩 결함은 공개 CI RED→GREEN으로 해결. 새로운 전체 주행의 마지막 필수 단계인 강사 WSL2 L3는 **미실행/HOLD**. 단일 자동 현장 Goal 및 무근거 승격은 수행하지 않음.
