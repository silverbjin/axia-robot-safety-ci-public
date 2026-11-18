# AXIA D06/G07 — 최신 G07 Task04 Owner 소스 정합성 회귀 및 WSLg GUI 경계 보고서

- 작성: 2026-11-19 KST
- 대상: 공개 PR #170, 브랜치 `feat/d06-g07-classroom-reuse-20261118`
- 작업 범위: **기존 L2 성공 재사용 + D06 Owner 실행기 SHA/WSLg GPU 어댑터 계약 최소 갱신**
- 상태: **공개 L0 GREEN, 역사적 동일 세션 실제 Gazebo L2 재사용, 강사 WSL2 L3 NOT_RUN, AXIA MVP HOLD**
- 공식 Nav2, CM, Safety Guard, TTL, Goal 권한 변경: **없음**

## 1. 선행 증거/최초 실패 경계

- 기존 D06 실제 Gazebo+RViz+Goal 테스트 [#44253212332](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44253212332)는 STOP/Cancel 성공 뒤 최초 최종 차단 `BLOCKED_LIFECYCLE_NAVIGATION_SERVICE_TIMEOUT`으로 FAIL. 따라서 정상 종료 PASS로 간주하지 않는다.
- G07 Task04 기존 **동일 세션** native 성공: [#44249348860](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44249348860), Student `1129cd8804954fd6481d1b6b4ebf0e0b98c68c3c`, 진짜 Gazebo+RViz Xvfb 두 창, 단일 Goal, S02 Contact0, CM120/Guard150, STOP odom ≥1s, UUID Cancel, Navigation/Localization ACK, CM clean exit, SQLite 14개, `first_failure=NONE`. 성공 세션 자체는 보존한다.
- 그 후 G07 PR #169에서 WSLg GUI 자식에게만 D3D12 렌더러를 적용하는 Student 수정 [`d7ffec1ce73f0c4e672ea0fc51a1678139dc5a6f`](https://github.com/silverbjin/axia-robot-safety-student/commit/d7ffec1ce73f0c4e672ea0fc51a1678139dc5a6f)가 이루어졌다. 수정은 Gazebo physics/sensor 서버와 ROS safety 노드의 전역 GPU 환경 오염을 방지한다.
- 최신 native L2 [#44268914763](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44268914763) (workflow SHA `08fef7f78459c915a29f15fe07a4a60b213b46d7`, Student `d7ffec1ce73f0c4e672ea0fc51a1678139dc5a6f`)는 실제 Gazebo+RViz Xvfb+Goal 원샷 rc=0, 두 창 확인, native reviewer `TASK04_REAL_GAZEBO_MOVING_GUI_L2_SCOPED_PASS`, `first_failure=NONE`, artifact `14411537039`. **Owner WSLg D3D12 픽셀 검증은 해당 CI로 증명할 수 없다.**
- 이전 D06 PR #170 L0 성공 [#44258204623](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44258204623)은 옛 Student `1129cd...`에 고정되어, 최신 Student의 `AXIA_G07_TASK04_GUI_D3D12_ADAPTER` 명시 계약을 제공하지 않았다.

## 2. RED → GREEN → REFACTOR → REVIEW → COMMIT

**RED**: 소스 핀과 WSLg 어댑터 계약만 좁힌 테스트 `d06/tests/test_d06_g07_classroom_reuse.py`를 먼저 갱신. Commit [`e5c164fe8b4d4a050e543635e5ccd50b5f69d107`](https://github.com/silverbjin/axia-robot-safety-ci-public/commit/e5c164fe8b4d4a050e543635e5ccd50b5f69d107), 공개 [CI #44337830279](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44337830279) 결과 **15개 중 4개 FAIL**. 이전 pin을 요구하던 CI 모의 영수증 2건, native L2 새 source-pin 1건, Owner GUI-child-only D3D12 어댑터 계약 1건. 기존 안전 기능 실패가 아니라 버전 정합성 실패.

**GREEN**: `d06/scripts/axia_d06_g07_classroom_once.sh`를 최소 수정. Commit [`2c365d6d0a9313c480212c3674edbe9e5f145899`](https://github.com/silverbjin/axia-robot-safety-ci-public/commit/2c365d6d0a9313c480212c3674edbe9e5f145899), 공개 [CI #44338066562](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44338066562) **15/15 PASS**. Bash 문법/기존 TTY·Owner 보호/거부/무결성/어댑터 문자열 계약만 실행했다. ROS/Gazebo/실제 Goal은 새 D06 CI에서 실행하지 않았다.

- 변경: Native L2 Run `44268914763`, workflow `08fef7f...`, Student `d7ffec1...`와 원본 런타임 3개 blob에 정확히 고정한다.
- 변경: Owner `glxinfo -B`의 **OpenGL renderer string**을 검사하고 `D3D12 (NVIDIA` 또는 `D3D12 (Intel`만 `AXIA_G07_TASK04_GUI_D3D12_ADAPTER`로 전달한다. 기타 렌더러는 **Goal 이전 HOLD**.
- 변경: 부모 환경에 들어온 `GALLIUM_DRIVER`와 `MESA_D3D12_DEFAULT_ADAPTER_NAME`을 해제한다. 실제 렌더러 설정은 최신 G07 원본이 Gazebo/RViz GUI 자식 프로세스에만 적용한다.
- **불변**: `YES-P2-G07-GOAL` 실제 사용자 TTY 승인 및 원본 세 PID 검사, Supervisor/CM/Guard 안전 제어, TTL 120/150/300ms, 원본 주행/Goal/Shutdown, `AXIA_MVP_DEMO_ACCEPTED=HOLD`, Certified E-Stop 금지.
- REFACTOR: 테스트 건수 receipt `FOURTEEN_TESTS`를 `FIFTEEN_TESTS`로 맞춤. Commit [`cf8e9c753ed1b29de2f92e7f2fbf0da21e67a869`](https://github.com/silverbjin/axia-robot-safety-ci-public/commit/cf8e9c753ed1b29de2f92e7f2fbf0da21e67a869), 공개 [CI #44338101552](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44338101552) **SUCCESS**.
- REVIEW: 검증된 G07 스크립트/Goal 엔진/종료 엔진의 Git blob hash를 GitHub 공개 Student 원본에서 대조했다. 이전 D06 L2 종료 실패를 새 CI 성공으로 재해석하지 않았다. `main` 미병합. 새 D06 L2 반복하지 않음.

## 3. 파일 및 검증 범위

- `d06/scripts/axia_d06_g07_classroom_once.sh` — 공개 Owner launcher, `--self-check|--ci-status|--doctor|--gui-only|--live`.
- `d06/tests/test_d06_g07_classroom_reuse.py` — 15개 ROS-free L0 회귀.
- `.github/workflows/axia-d06-g07-classroom-reuse-public-l0-20261118.yml` — 공개 GitHub Actions L0.
- 이 문서 — 교육용 원인·증거·수정·한계 기록.

실제 테스트 출력 핵심:
```text
# RED #44337830279
test_ci_status_rejects_stale_green_source_receipt ... FAIL
test_ci_status_uses_exact_three_success_run_receipts ... FAIL
test_last_green_task04_pinned_with_all_native_l2_gates ... FAIL
test_wslg_d3d12_owner_adapter_is_explicit_and_gui_children_only ... FAIL

# GREEN #44338066562
Ran 15 tests in 0.030s
OK
D06_G07_CLASSROOM_REUSED_SAME_SESSION_NATIVE_CI=44268914763
D06_G07_CLASSROOM_PINNED_OWNER_SOURCE=d7ffec1ce73f0c4e672ea0fc51a1678139dc5a6f
AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false
```

## 4. 잔여 인수 및 판정

- 신규 D06 변경 사항: **L0 PASS** (기존 실행기 소스 계약, TTY 거부, 최신 SHA/무결성 고정, GUI 어댑터 문자열).
- 실제 ROS L1: 이번 갱신에서 **NOT_RUN**. 과거 ROS L1 성공과 혼동 금지.
- 동일 세션 Gazebo+RViz+Moving Goal/CM·Guard/Nav2: **기존 G07 공개 L2 #44268914763 PASS_SCOPED, 동일 Student 소스 재사용**. 이번 D06 wrapper 자체로 새 native 주행을 수행했다고 주장하지 않는다.
- 강사 WSL2/WSLg D3D12 GPU GUI, 소스 RMW 전달, 최초 안전 시간 위반, Goal/Cancel, Nav2 종료 및 원본 bag 리뷰: **L3 NOT_RUN**.
- 공개 CI 성공 후 단 한 번의 Owner 원샷으로 인수하고, 오류가 나면 **최초 안전 전이·최초 타이밍 위반**을 CI 재현 계약에 먼저 편입한다.
- 최종 판정: `AXIA_MVP_DEMO_ACCEPTED=HOLD`, `CERTIFIED_ESTOP=false`, `MAIN_MERGED=false`.

**강사용 실제 실행:** 공개 SHA-고정 실행기 다운로드 후, 직접 TTY에서 `bash <script> --live`로 실행한다. 수동 동의는 기존 원본의 `YES-P2-G07-GOAL` 입력을 유지한다. 로그/원본은 `~/axia_d06_g07_owner_evidence/`에 보존한다.
