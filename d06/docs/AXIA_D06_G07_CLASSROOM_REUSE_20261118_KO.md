# AXIA D06 — G07 Task03/Task04 성공 재사용 강사용 Live Demo 개발 보고서

작성 2026-11-18 KST · **현재 범위: 신규 D06 실행기 L0 및 실제 G07 GUI 연결(Goal 없음)**

## 사용자가 원하는 강의 장면

Gazebo Harmonic 3D Waffle이 기존 공식 Nav2의 단일 승인 Goal로 실제 움직이고, CLEAR → SLOWDOWN → STOP을 수행하는 동안 RViz2에서 /scan, /odom, Costmap/Path와 교육용 Safety Bubble을 설명한다. 새 Nav2/CM/Safety Supervisor/Guard 구현 없음. G07 CM/Guard root cause 연구는 D06에서 반복하지 않는다.

## 재사용 원본(서로 다른 검증 세션을 합산하지 않음)

- **주행:** [G07 Task03 실제 Gazebo L2 #44223320904](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44223320904), exact Student runtime `01752add2e30c90c4d3286ef3a450f97746ecb55`, workflow `6bc8b0711ab056e63e100f3eede2c5f06cdf3856`. 공식 Jazzy/Harmonic/Nav2/Waffle, CM 56.642455ms/120ms, Guard CM age 53.971531ms/150ms, displacement 0.2111m, CLEAR/SLOWDOWN/STOP, odom stopped dwell 1.013s, native obstacle Contact0, Cancel status5, Nav2 ACK, CM exit0, SQLite 14/14. 오직 CI 시뮬레이션 범위 한정.
- **시각:** [G07 Task04 실제 Gazebo+RViz Xvfb #44238643061](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44238643061), SHA `5bb0cd72086f2f1a057f382649b773fff106f1f9`. 실제 Owner WSLg NO_GOAL GUI VISUAL [#169](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/169) PASS_SCOPED (Gazebo 물리월드와 RViz Costmap/Path 화면). 해당 코드의 `scripts/axia_g07_task04_public_owner_wsl2_pregate_once.sh` blob `a15cf37e1a1d2a0253029c0a1dd8e2530e307c25`를 고정.
- **이전 D06 통합 근거:** [#43667573251](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43667573251) 실제 Xvfb moving Goal+RViz 성공. 이후 WSL2 Owner에서 Guard CM age 169.168ms와 CM RMW source 184.415ms로 안전 래치 발생했으므로 구 Owner 스크립트 재실행 금지.
- G07 Task02의 official Simple TF `base_shift_correction=false`는 저속 Gazebo 단일 시나리오의 CI-전용 검증 프로파일이다. TF motion time-shift correction을 생략하므로 하드웨어·범용 주행 안전 검증이 아님.

## 신규 구현 범위

- `d06/scripts/axia_d06_g07_classroom_once.sh`: Task03/04 원본 run/source SHA 검증, Task04 검증된 GUI 스크립트의 git blob hash 검증 후 WSL2에서 실제 Gazebo+RViz GUI 원샷을 **그대로 위임**. `--self-check`(오프라인), `--ci-status`(GitHub Actions 동일 SHA·success 조회), `--doctor`(Owner preflight), `--gui-only`(실제 NO_GOAL Gazebo+RViz), `--live`(실제 Moving Owner 출고 전 **명시적 HOLD**).
- `d06/tests/test_d06_g07_classroom_reuse.py`: 계약 테스트 6개, GitHub Actions에서 GUI/Goal 권한 위장 및 불법 publisher 금지.
- `.github/workflows/axia-d06-g07-classroom-reuse-public-l0-20261118.yml`: 공개 Ubuntu L0만, 외부 앱 인증·ROS/Gazebo 없이 6개 회귀 실행.
- 공식 Nav2, Student 원본, CM/Guard TTL, /cmd_vel publisher, 물리 Collision Monitor를 변경하지 않음. **새 Owner Moving Goal 실행기는 이 커밋에 포함되지 않는다.** 기존 G07 Task04가 실제 WSL2 Moving Goal을 아직 배포하지 않았기 때문이다.

## RED → GREEN → REFACTOR → REVIEW → COMMIT (실제 출력)

1. RED: 신규 실행기가 없는 상태에서 `python3 -m unittest discover -s d06/tests -p 'test_d06_g07_classroom_reuse.py' -v` → `FAILED (failures=4, errors=2)`.
2. 초기 GREEN 후보: 테스트 5/6; CI 환경 차단에서 `GH_CLI_REQUIRED`가 먼저 발생해 `test_owner_gui_path_rejects_github_actions_before_download`가 실패.
3. 최소 수정: GUI 모드는 `GITHUB_ACTIONS` 검사 후 `gh`/네트워크 검사하도록 순서 교정.
4. GREEN (local Python3, ROS 미실행):

```text
Ran 6 tests in 0.012s
OK
```

5. REFACTOR/REVIEW: 강사용 wrapper는 새 Goal 발행 0, CI-only `GITHUB_ACTIONS=true` 위장 0, 후속 task가 Owner Moving 인수되지 않았을 때 `D06_G07_CLASSROOM_MOVING_OWNER_NOT_RELEASED`로 즉시 실패. 소스 tree SHA/CI run pin은 기존 성공 증거를 재사용. 공개 CI Actions의 실제 실행 결과는 별도로 확인한다.

## 사용 명령

검증된 D06 공개 SHA로 checkout한 뒤:

```bash
bash d06/scripts/axia_d06_g07_classroom_once.sh --self-check
bash d06/scripts/axia_d06_g07_classroom_once.sh --ci-status
# WSL2 Owner에서만: 기존 Task04 실제 GUI-only Gazebo + RViz 실행
bash d06/scripts/axia_d06_g07_classroom_once.sh --gui-only
```

`--live`는 **아직 사용하지 않는다**. 공개 Student의 기존 단일 Goal은 `GITHUB_ACTIONS=true`를 요구하므로 Owner WSL2에서 이를 위조할 수 없다. G07 Task04의 정식 single-owner-Goal runner가 release되면 그 정확 SHA만 얇게 D06 wrapper에 연결한다. D06 자체의 120ms CM 튜닝, LTTng 연구, ROS 안전제어 확장 금지.

## 판정 경계와 후속 필요 작업

- 과거 Task03 **진짜 Gazebo 주행 L2 PASS**, Task04 강사 **WSLg NO_GOAL GUI PASS_SCOPED**: 각각 유효하나 하나의 통합 Moving Goal L3로 승격 금지.
- 신규 D06 실행기 L0: 로컬 6/6 PASS, 공개 CI 결과 별도 확인. 이번 턴에 새 Gazebo/WSL2 수행 없음.
- **D06 같은 세션의 Gazebo+RViz Moving L2 및 강사 Moving Owner WSL2 L3: NOT_RUN / BLOCKED_WAITING_G07_OWNER_MOVING_RELEASE.**
- Fail-closed: Guard 150ms, Scan 300ms, 최초 안전 상태 전이, Stop odom ≥1s, Contact 0, 동일 Goal Cancel ACK를 유지. 오류 발생하면 현장 재시도 대신 기존 G07 공개 CI 회귀로 인계.
- 전체 `AXIA_MVP_DEMO_ACCEPTED=HOLD`, `CERTIFIED_ESTOP=false`, 사용자 승인 없는 main 병합 금지. SW stop을 인증된 E-Stop으로 주장하지 않음.
