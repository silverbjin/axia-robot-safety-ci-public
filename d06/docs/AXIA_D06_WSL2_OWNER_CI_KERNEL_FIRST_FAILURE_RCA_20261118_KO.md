# AXIA D06 — WSL2 Owner CI 커널 패리티 오진으로 인한 Live Demo 사전 차단 RCA

작성: 2026-11-18 KST | 실습 MVP | RED→GREEN→REFACTOR→REVIEW→COMMIT

## 1. 입력·원본 증거 보관

- 제출된 강사 로컬 원본: `d06-moving-jJpydD7n.tar.gz`, **압축 SHA256 = `9f1c8bb10469ea6f3e803180d1804984b182dbc06b336e9451eb80f2096c4f46`**. 동봉된 `.sha256`과 일치.
- 전체 TAR 내부 `SHA256SUMS` **11/11 PASS**, 중첩 `native/SHA256SUMS` **3/3 PASS**. 원본 bag/로그/환경의 로컬 저장 경로와 프로세스 정보는 공개 저장소에 업로드하지 않음.
- 원본 `owner_parity.json`: `status=CORE_PARITY_PASS`, `mode=owner`, `wsl_detected=true`, `checked_packages=25`, `checked_official_files=5`, `mismatch={}`, `goal_sent=false`.
- 원본 `native/g07_userspace_parity.json`: `status=PARITY_BLOCKED`, `mode=ci`, `wsl_detected=true`, `mismatch={"ci_kernel":"CI_NOT_WSL2_REQUIRED"}`, 동일한 정확 패키지 25/25·공식 파일 5/5, `goal_sent=false`.
- **최초 오류**: `AXIA_G07_ENV_PARITY_BLOCKED mismatches=ci_kernel` → `P2_G07_NO_GOAL_CI_USERSPACE_PARITY_BLOCKED`.
- **후속 오류**: 종료 정리 중 `OWNER_PARITY_BAG_METADATA_MISSING`(Goal 이전/rosbag 작성 전 런타임 중지 후 cleanup에서 출력). 이 후속 예외를 최초 결함으로 보고하지 않음.
- WSLg `glxinfo`: 실제 `D3D12 (Intel Iris Xe)`, accelerated=true. NVIDIA GPU 미선택은 이번 첫 커널 패리티 실패의 원인이 아님.
- 실제 Gazebo/ROS 노드 동작, Guard CM age 150ms, RMW 발행 120ms, Navigation ACK, STOP/odometry는 **해당 Owner 실행에서 미측정/NOT_RUN**. 리포트에는 이를 PASS로 쓰지 않음.

## 2. 원인: 잘못된 환경 플래그 한 개

고정된 G07 Task04 성공 Student runtime commit `1129cd8804954fd6481d1b6b4ebf0e0b98c68c3c`의 `block_B/day07/h01_runtime/scripts/p2_no_goal_smoke_ci.sh`는 다음 조건을 가짐:

```bash
if [[ "${AXIA_P2_G07_OWNER_PARITY_CHECK:-0}" == 1 ]]; then
  python3 tools/p2_g07_owner_env_parity.py --mode ci ...
fi
```

직전 D06 강사 래퍼가 Owner WSL2 환경에서 `AXIA_P2_G07_OWNER_PARITY_CHECK=1`을 내보냈기 때문에 **CI 전용** `--mode ci` 커널 검사까지 실행됨. 비교 함수 `assess_snapshot`은 CI에 WSL 커널이 보이면 의도대로 `CI_NOT_WSL2_REQUIRED`를 반환함. 이는 CI 검사기의 결함이 아니라 **D06이 CI 검사 모드를 잘못 선택한 연결 결함**. Owner 환경 검사 `--mode owner`는 이미 같은 정확한 원본 SHA와 25/5 패키지·파일에서 통과한 상황.

## 3. 최소 수정 및 원형 재사용

- 공개 소스 개발 브랜치 `fix/d06-wsl2-owner-parity-first-boundary-20261118`, 수정 대상은 **D06 wrapper `d06/scripts/axia_d06_g07_classroom_once.sh` 한 파일**.
- WSL2 Owner 분기에서 `AXIA_P2_G07_OWNER_PARITY_CHECK=0`으로 지정하여 **중복된 CI 전용 커널 검사를 실행하지 않음**. 별도 `p2_g07_owner_env_parity.py --mode owner` 검증은 삭제하지 않고, 그 JSON의 `CORE_PARITY_PASS`, `mode=owner`, `wsl_detected=true`, 패키지 25/25, 공식 파일 5/5, `mismatch={}`를 실제 다시 검사하여 Goal 전에 실패 시 차단.
- 기존 G07 Student Goal·CM·Guard·Nav2·Collision Monitor·Native S02 Contact C++·TF·안전 TTL·Goal UUID cancel·rosbag14·Nav/Loc ACK·정상 종료 코드 변경 **0**. `GITHUB_ACTIONS=true` 위조, CI 전용 Goal 승인 부여, 자동 사람 승인 **없음**.
- 예전 검증된 G07 Task04 진짜 한 세션 native L2 [#44249348860](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44249348860) (`Student 1129cd...`, public workflow `6b98a18...`, Gazebo GUI+RViz+Moving Goal, CM RMW 120ms, Guard internal age150ms, Scan, S02 Contact0, exact cancel, SQLite14, Navigation/Localization ACK, CM exit0) 그대로 고정. 새로운 안전 로직·재구축 Goal 엔진 없음.

## 4. 공개 CI RED → GREEN

1. 실제 Owner 스냅샷의 **비식별 사실만** 추출하여 새 `d06/tests/test_d06_g07_owner_mode_field_regression.py`를 작성. 공개 CI가 고정된 Student exact SHA를 checkout하여 **진짜 `p2_g07_owner_env_parity.assess_snapshot()`**을 호출, 동일한 WSL2 커널/동일 패키지/공식 파일 입력에서 Owner 통과·CI 차단을 모두 재현. 잘못된 전 래퍼 플래그를 검출하도록 테스트 설정.
2. **RED 공개 CI [#44260328678](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44260328678)**: 기존 14/14 PASS, 신규 4개 중 3 PASS / **1 FAIL**: `test_d06_owner_selects_validated_owner_mode_not_ci_only_gate`에서 전 래퍼 `AXIA_P2_G07_OWNER_PARITY_CHECK=1` 확인. 사전 검사 L0이며 ROS/Goal 실행 없음.
3. 최소 수정: 위 D06 Owner 플래그 및 Owner 25/5 검증 불변조건. 다른 원본 소스 변경 없음.
4. **GREEN 공개 CI [#44260462052](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44260462052)**, source commit `3ae9a29911580a3bc4354a9ef6993878165fe523`: `Ran 14 tests ... OK`, `Ran 4 tests ... OK`, 총 **18/18 PASS**, `D06_G07_CLASSROOM_PUBLIC_L0_PASS FOURTEEN_PLUS_FOUR_OWNER_PARITY_TESTS NO_ROS_NO_GAZEBO_NO_GOAL`. 실제 Linux CI에서 WSL2 커널 스냅샷을 **모의**하여 해당 모드 분기를 검증했으며 WSLg 실제 물리 화면은 별도.
5. 재확인: 3개 G07 원본 CI Run/SHA 정확 일치·bad SHA 거부·진짜 TTY 필수·Owner `--mode owner` preflight·원본 TAR/SHA256·코드 문법·Guard 내부 age checker Python 문법 모두 기존 L0 회귀 범위 유지.

## 5. 과거 D06 주행/시각화 브랜치 조사

| 저장소/브랜치 | 시연에 쓸 수 있는 기존 증거 | 채택 판단 |
|---|---|---|
| Public `feature/d06-gazebo-rviz-owner-20261114` / [PR #108](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/108) | 실제 ROS L1 MarkerArray 16개, /cmd_vel publisher 0, 읽기 전용 RViz sidecar; 기존 G07 Goal+RViz 동시 native Gazebo L2 [#43667573251](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43667573251) 성공 | D06 교육 시연 목표/화면 구성 재사용 근거. 현재 Owner 실행 경로에 별도 Marker publisher 추가하지 않음 |
| Public `release/d06-g07-observer-owner-20261115` | G07 공용 Goal 보호 CI pin + 원본 custody | 역사적 증거 보존; 구형 pre-CM120 Owner runner 미재사용 |
| Instructor `fix/d06-g07-bag-priority-20261114` [#172](https://github.com/silverbjin/axia-robot-safety-instructor/pull/172) | 실제 Gazebo Goal 3회 CI #43609296371 성공; 이후 간헐 CM gap 회귀 및 종료 타이밍 등 | 비안전 rosbag 부하 완화 실험 결과만 참고; 신규 CPU 정책 확장 금지 |
| Public `feat/d06-g07-classroom-reuse-20261118` [#170](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/170) | 동일 성공 Student/CI SHA 직접 재사용, 수동 TTY one-shot; **이번 사용자 현장 WSL2 CI kernel 모드 실패** | 기준 부모. 수정은 별도 Draft 브랜치 |
| Public G07 Task04 success SHA | 실제 동일 세션 Gazebo/RViz/Goal/CM/Guard/취소/종료 통합 L2 완주 | **선택된 단일 런타임**, Student 소스 변경 금지 |

## 6. 검증 및 출고의 경계

- L0 **18/18 GREEN**는 실제 사용자 WSL2 원본을 모델화한 패리티 모드 회귀 검증. G07 Task04 **기존 L2 GREEN**은 실제 Linux Xvfb Gazebo+RViz+Goal·안전 TTL·Nav2/CM 종료.
- 이번 수정은 D06 Owner wrapper 분기에만 적용되므로 원형 G07 Task04 CI L2를 재실행할 이유가 없음. 다만 **동일 WSL2 환경의 새 Owner L3 성공까지 보장하는 것은 아님**. 사용자 강사 WSL2 최초 확인은 로봇 Goal 1회만 수행, 첫 실패 증거 TAR/SHA256 보관, 문제 발생 시 CI regression 선행.
- 본 원본에서는 Goal이 나가지 않았으므로 **지난 실행을 주행 실패나 Guard 안전 위반으로 카운트하지 않음**. 새 Owner 주행이 실제 진행된 뒤에만 Guard 150ms/Scan300ms/RMW120ms 판단.
- Docker CI와 WSL2/WSLg GPU·CPU scheduler의 동일성은 미증명. `AXIA_MVP_DEMO_ACCEPTED=HOLD`, 인증 E-Stop 아님, main 미병합.
- 출고 후 기대 구문은 `D06_G07_OWNER_CORE_PARITY_PASS_PACKAGES25_FILES5_WSL2` 이후 실제 Gazebo/Nav2 단일 Goal 요청 단계. 결과는 `OWNER_NUMERICAL_CANDIDATE_REVIEW_REQUIRED`까지만 자동 보고하며 독립 원본 검토 이전 최종 PASS 주장 금지.
