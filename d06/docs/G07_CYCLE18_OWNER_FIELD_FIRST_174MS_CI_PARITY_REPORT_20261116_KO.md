# AXIA G07 Cycle 18 — WSL2 실제 첫 Guard 174ms/CM 186ms 사건을 공개 CI에 편입

**날짜:** 2026-11-16. **판정:** Owner preflight·과거 실패 보호 **공개 CI L0 GREEN**, 실제 G07 안전 타이밍 개선/WSL2 재인수 **미완료**, `AXIA_MVP_DEMO_ACCEPTED=HOLD`.

## 1. 분석에 사용한 사용자 원본 및 Integrity

사용자가 업로드한 파일: `manifest.json`, `SHA256SUMS`, `support_evidence.tar(1).gz`, `axia_d06_gazebo_rviz_owner_QHJk7mIB.zip`. 지원 번들 SHA256 `1106efe4226d99a455c9a3c9f22762f47506120ec2c887ae0c368806b1306b1f`, 매니페스트에 기재된 **28/28 개별 파일 원본 해시 일치**. GUI ZIP은 0바이트 파일 한 개 외에 결과가 없음. Current call `no_ros_no_goal=true`, wrapper rc3, 원본 새 로봇 실행 없음.

**선행 실제 Owner Goal은 있음.** 동일 Instructor SHA `01d45d46b6eb6a05b1bd313d73f1fc3549575545`의 `2026-11-15T22:24:56Z` G11 custody와 joined review는 14 topic bag, Goal UUID·취소 관측, 최초 Guard `UPSTREAM_STALE_AFTER_MOTION` latch, 내부 CM age `174.184617ms>150ms`, 첫 CM RMW source 공백 `186.714207ms`, Supervisor publication 4개 내부 존재, Owner accepted=false를 증명함. archive SHA 및 Goal UUID는 공개 fixture에 포함하지 않음.

현재 `AXIA_G07_FINAL_OWNER_REPEAT_BLOCKED_CI_FIRST_REVIEW_REQUIRED_NO_GOAL`는 **정상 안전 보호**이고 바로 앞선 실제 안전 실패가 현장에 남아 있음을 뜻한다. `D06_RVIZ_NOT_CONFIRMED`는 sidecar 시작 전 차단된 데서 온 후속 출력이며 최초 원인이 아니다. 상위 CI Run `43727149856`에서 실제 GUI Gazebo L2 PASS 및 CM max `110.964002ms`였더라도 WSL2의 실제 186.714207ms 원본을 덮지 못함.

Ubuntu Noble 24.04 + ROS 2 Jazzy + Gazebo Harmonic은 공식 지원 조합이다. 이 호출은 ROS/Gazebo 시작 전 중단돼 24.04 비호환이 직접 원인일 수 없음. WSL2 스케줄링/TF/executor/RMW 송신 공백의 **인과는 미확정**.

## 2. RED→GREEN→REFACTOR→REVIEW→COMMIT

- 공개 작업 브랜치: `fix/g07-owner-real-first-ttl-ci-parity-20261116` (`main` 미병합).
- 지침: `d06/docs/G07_OWNER_WSL2_FIRST_FAILURE_CI_PARITY_AGENT_INSTRUCTIONS_20261116_KO.md`
- 공개 비식별 사실 계약: `d06/tests/fixtures/g07_cycle17_wsl2_guard_174ms_rmw_186ms_sanitized.json`. 개인 원본을 공개 업로드하지 않음.
- RED 단위·현장 상태 시뮬레이션: `d06/tests/test_g07_cycle18_field_first_owner_parity_v5.py`. [Run 43782312499](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43782312499) FAIL, 신규 verdict 및 출고용 입구 미구현. [Run 43782732413](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43782732413)에서 실제 wrapper 출고 순서 계약 RED.
- GREEN 순수 첫 안전 상태/출고 진단: `d06/live/g07_cycle18_field_owner_admission_v5.py`. 같은 private SHA/CI Run의 과거 **실제 Guard TTL 위반이면 lock 존재 여부와 무관하게** `FIELD_PREVIOUS_GOAL_CM_TTL_BREACH_HOLD`, `manual_attempt_allowed=false`, `no_ros_no_goal=true`. 중복 잠금이나 field 원본 누락, symlink/손상 JSON은 별도 HOLD. 150ms hard 및 120ms release 기준 유지.
- Owner 실제 실행기 코드 `d06/scripts/g07_cycle16_owner_wsl2_once.sh`는 **실제 CI-only ADMITTED 메시지와 원자적 attempt 예약 이전**에 현장 안전 이력 검사. `--field-preflight` 옵션은 ROS·Gazebo·Goal 없이 동일 판정 실행. `scripts/axia_g07_cycle16_owner_wsl2_bootstrap.sh`의 신규 코드도 CI-only gate보다 해당 검사를 우선함. 기존 불변 SHA의 배포 코드는 소급 변경되지 않음.
- Read-only 사용자 경로: `scripts/axia_g07_cycle18_owner_readonly_preflight.sh` 및 불변 `scripts/axia_g07_cycle18_field_readonly_wsl2_bootstrap.sh` (출고 SHA `1527a5080e2e7d417696aae79aab615c02e49b5d`, tree `003801443d192ba6e1f6298d55eea08989307d2c`).
- CI workflow `.github/workflows/axia-g07-owner-real-field-first-ttl-l0.yml`: **Ubuntu 24.04** 공개 runner에서 기존 실패 HOME을 만든 후 **실제 동일 read-only bootstrap을 Git SHA/Tree checkout부터 실행**한다. `RC=3`은 기대값. HOME 안전 원본 보존/ROS 미호출/거짓 CI-only ADMITTED·RViz 실패 메시지 부재까지 검사.
- 세부 중간 실패: `43782485611`, `43783254503`은 합성 `source.txt`의 `\\n` fixture 줄바꿈 실수이며 runtime 사고나 OS 24.04 문제가 아님; 정확한 Bash newline로 수정.
- 최종 GREEN [Run 43783327944](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43783327944): `Ran 12 tests in 0.092s`, `AXIA_G07_FIELD_PREVIOUS_CM_TTL_BREACH_CI_L0_PASS_NO_ROS_NO_GOAL_OWNER_RELEASE_HOLD`, `AXIA_G07_CYCLE18_FIELD_PUBLIC_SHA_TREE_VERIFIED=1527...`, `AXIA_G07_FIELD_OWNER_RELEASE_V5 {..."first_guard_cm_age_ms":174.184617,"first_cm_rmw_source_gap_ms":186.714207,"manual_attempt_allowed":false,"status":"FIELD_PREVIOUS_GOAL_CM_TTL_BREACH_HOLD"...}`, `AXIA_G07_FIELD_OWNER_SAME_PINNED_WSL2_BOOTSTRAP_CI_PASS_NO_ROS_NO_GOAL`.

## 3. 재검증 범위 및 출고 차단

- PASS: 실제 Owner bundle 무결성 검사, 공개 12개 L0 계약, Ubuntu24에서 사용자 부트스트랩/현장 잠금 읽기 재현, 최초 안전 위반 구분, WSL2 릴리스의 잘못된 `manual_attempt_allowed=true` 안내 수정(새 브랜치 코드).
- **미검증:** 174.184617ms 첫 Guard TTL 초과의 실제 원인(공식 CM callback, TF, DDS, CPU/WSLg), RMW 최초 CM source 186.714207ms가 새 수리로 줄었는지, 실제 Gazebo L2 추가 수정, 사용자 WSL2 Owner 재인수. 현장 재시도/원본 lock 삭제 전혀 하지 않음.
- 현재 공개 CI-L2 `43727149856` PASS 증거는 기존 별도 시뮬레이션 조건만 설명한다. 기존 Instructor SHA를 동일하게 다시 돌려서 새 Owner 시도를 출고하지 않는다.
- 다음 **최소 CI 사이클**: 사용자가 이미 보유한 선행 실제 Owner G07 원본 아카이브에서 첫 CM source gap의 C++ 실행/TF/스케줄링 원인을 사전에 정의한 **한 경계**로 판별하고, 공개 CI에 재현 가능한 형태로 RED를 편입. 안전 런타임을 수정했다면 새 Instructor SHA로 실제 GUI Gazebo L2에서 CM<120ms headroom, Guard<150ms, Scan/Odom/Clock, S02, exact Cancel, orderly shutdown 모두 확인. WSL2는 이 단계가 끝난 뒤 1회만. 이 오류는 아직 안전하게 수리된 것이 아니라 현장 재실행이 정확히 차단된 상태임.
- 과거 시도 lock·Owner raw·G11 custody 전체 보존. 원본은 비공개에만 보관. 명시적 사용자 승인 없이 `main` 병합 금지. SW STOP은 인증된 E-Stop이 아님.

**현 최종 상태:** `AXIA_MVP_DEMO_ACCEPTED=HOLD`; `OWNER_MOVING_GOAL_RELEASE=BLOCKED_FIRST_FIELD_GUARD_TTL`.
