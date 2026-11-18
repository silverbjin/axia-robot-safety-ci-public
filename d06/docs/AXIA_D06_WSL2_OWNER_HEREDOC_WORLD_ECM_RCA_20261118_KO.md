# AXIA D06 — Owner Here-document 오류와 네이티브 Gazebo 월드 오버레이 최초 실패 회귀 보고서

문서: 2026-11-18 KST · 범위: 강사 WSL2 Gazebo+RViz+단일 Nav2 Goal MVP · 안전 Gate 완화 없음

## 1. 실제 실패 원본과 무결성

- 강사 원본 파일: `d06-moving-Y6t5sJp4.tar.gz`, 외부 SHA256 **`013aff14a3319b6dafd2f08efb87f50c0621d60fd269da5e27e6bd780181955b`**, 함께 전달된 `.sha256` 텍스트와 일치.
- 제출된 TAR를 실제 열어서 내부 `SHA256SUMS` 상위 **13/13 PASS**, `native/SHA256SUMS` **5/5 PASS** 확인. 강사 원본은 공개 GitHub에 업로드하지 않고 비식별 오류 유형/검증 수치만 커밋.
- 원본 최초 Owner 환경은 `owner_parity.json` **CORE_PARITY_PASS**, `mode=owner`, packages25/25, official files5/5, WSL2 true, mismatch={} 확인.
- 먼저 D06 래퍼가 `python3 - "$out/owner_parity.json" <<'PY' ||` 뒤의 다음 줄 `hold ...`를 실제 Python STDIN에 붙여서 `IndentationError: unexpected indent` 발생. **더 심각하게도 이 실패를 HOLD로 전이하지 않고** `D06_G07_OWNER_PIN_VERIFIED` 및 G07 자식 시작까지 진행함. 실제 정합 검사는 성공할 수 있었더라도 실행기 종료 규칙에 결함이 있음.
- 다음 G07 자식의 **첫 실제 시뮬레이션 전 실패**: `G07_PHYSICAL_WORLD_OVERLAY_BLOCKED`, 원본 `native/g07_world_overlay.log`는 정확히 `P2_G07_WORLD_OVERLAY_BLOCKED:ValueError` 한 줄. 뒤의 `OWNER_PARITY_BAG_METADATA_MISSING`는 자식 cleanup이 실제 rosbag 시작 전에 증거 누락을 출력한 **후속 오류**이지 최초 world 오류 원인이 아님.
- 이번 Owner 세션에서 **Goal 전송 0, 실제 Gazebo·RViz 주행/STOP/CM/RMW/Guard TTL/Navigation ACK 미실행**. 성공으로 절대 보고하지 않음.

## 2. 코드 수준 원인 두 개

**원인 A — Bash Here-document 연결 구문 실수**

기존 소스는 실패 처리 `||`를 Python HEREDOC 줄 끝에 두고 `hold`를 다음 줄에 배치. Bash가 `hold ...` 줄을 Python 표준입력으로 처리했으며, 후속 승인 상태 출력까지 진행해 fail-closed 불변 조건을 위반.

해결: `python3 - ... <<'PY' || { hold D06_G07_OWNER_CORE_PARITY_REPORT_INVALID_NO_GOAL; }` 형태로 동일 줄에 완전한 Bash 실패 분기를 배치. 검증기는 원본 `CORE_PARITY_PASS`, Owner mode, WSL2 true, packages 25, official files 5, mismatch {}를 계속 검사. Python 오류나 잘못된 JSON이 들어오면 **RC3/NO_GOAL/HOLD로 즉시 종료**.

**원인 B — 네이티브 Contact witness의 CI-only 권한과 Owner 모드의 불일치**

고정 G07 Student `1129cd8804954fd6481d1b6b4ebf0e0b98c68c3c` `tools/p2_l3_world_overlay.py`에는 `AXIA_G07_TASK03_ECM_WITNESS=1`인 경우 `GITHUB_ACTIONS=true`, `AXIA_G07_CI_SIM_GOAL_ALLOWED=1`이 요구됨. 하지만 D06 WSL2 Owner는 **의도적으로** `GITHUB_ACTIONS!=true`, CI Goal 권한 0을 설정하므로 네이티브 world overlay는 Owner에서 항상 `ValueError` 차단. 이 정책을 Owner가 CI를 위장해 우회하는 것은 절대 금지.

해결: Student `tools/p2_l3_world_overlay.py` **이 한 파일의 native witness 삽입 admission**에 G07 Task04 실제 Owner 예외를 최소 추가. `GITHUB_ACTIONS!=true`, `AXIA_G07_CI_SIM_GOAL_ALLOWED=0`, Owner 전용 `AXIA_G07_TASK04_OWNER_MOVING_L3=1`, Owner startup/physical/bag parity, 실제 TTY (`os.isatty(0)`), 정확한 새 Student git SHA `git rev-parse HEAD == AXIA_G07_TASK04_EXPECTED_STUDENT_SHA` 일치시만 **읽기 전용 Contact Witness plugin 삽입** 허용. 권한 부재/가짜 SHA/TTY 부재/CI Owner overlap은 계속 차단. 공식 Gazebo Contact, Nav2, CM, Guard, 안전 TTL, Goal 제어기 코드는 건드리지 않음. 실제 Goal은 기존 Student `YES-P2-G07-GOAL` 수동 승인·Supervisor/CM/Guard 3 PID 검증 후에만 진행.

## 3. 재현 가능한 테스트와 실제 공개 CI 결과

| 단계 | 실제 CI/소스 | 판정 |
|---|---|---|
| Here-doc 구문 RED | [#44264145850](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44264145850) · 원본 D06 | 3/3 **FAIL**: Python `IndentationError`, 종료 코드 0으로 잘못 진행, Bash `unexpected end of file` |
| Here-doc 최소 수정 GREEN | [#44264215699](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44264215699) | 추가 **3/3 PASS**, 실제 Bash·Python positive/negative subprocess 실행 |
| 실제 이전 G07 월드 RED | [#44263681518](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44263681518), Student old `1129cd...` | `test_reproduce_old_ci_only_ecm_rejection_on_owner` 실패, 정확 `P2_G07_WORLD_OVERLAY_BLOCKED:ValueError` 재현 |
| G07 네이티브 월드 GREEN | 같은 Run · Student `e9adb73d658859a53976d9848aa75bd5be710def` | 5/5 PASS: PTY/정확 SHA Owner만 Contact witness 삽입, no TTY/bad SHA/Actions Owner 거부, 일반 NO_GOAL 동작 유지 |
| **실제 전체 Gazebo+RViz+Goal L2** | [#44263904176](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44263904176), CI SHA `7487dde355543f2a92e412ab79788f4a39a34abb`, Student exact `e9adb73d658859a53976d9848aa75bd5be710def` | **completed/success**, `TASK04_REAL_GAZEBO_MOVING_GUI_L2_SCOPED_PASS`, `first_failure=NONE`, Gazebo/RViz X11 **2 창**, 실제 native Goal runner RC0. Task04 기존 strict 21-gate viewer: CM RMW<=120ms, Guard age<=150ms, Scan, Contact0, SQLite14, STOP odom>=1s, goal UUID cancel, Nav2 Navigation+Localization ACK, CM clean exit |
| D06 공개 연결부 L0 최종 | [#44264873146](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44264873146), CI SHA `f56cbde64aabb0a3dc7865b762d21e095929e962` | Python **15+5+3=23/23 PASS**, 새 Student SHA/새 native L2 CI Run·shell here-doc execution·Owner/CI 잘못된 권한 거부 포함 |

테스트 단계는 첫 원본 실패 증거 확보 → RED → 최소 구현 GREEN → 원본 G07 기능 불변 검증 → 사용자 현장 실행기 소스 고정 → 리뷰·커밋을 따름. 과거 성공 1129cd/44249348860은 역사적 증거로만 보존하며 **새 Owner source e9adb**의 CI L2 합격으로 임의 승격하지 않고, 실제 새 SHA를 [#44263904176](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44263904176)에서 **다시 검증한 뒤에만** 연결함.

## 4. D06과 예전 강의 코드의 역할 분리

- 과거 `feature/d06-gazebo-rviz-owner-20261114` [공개 PR #108](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/108)은 CLEAR/SLOW/STOP 주행 관찰, 읽기 전용 RViz2 sidecar 및 교육용 bubble marker와 실제 Gazebo+RViz L2 [#43667573251](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43667573251) 근거. 수업 내용과 화면 구성의 참조용으로 보존. 해당 구형 CM age 169ms 실패 Owner 런타임을 실행하지 않음.
- 현재 실제 Goal/공식 Gazebo+RViz는 G07 Task04 **원래 headless Gazebo 서버 + 별도 GUI/RViz 클라이언트**와 수동 TTY 승인 경로를 재사용. D06은 새 Goal/CM/Guard publisher를 만들지 않음.
- 기존 Task04 Native L2는 CI host Xvfb이고 Owner PC는 WSLg D3D12. CPU executor·GUI 렌더·실제 DDS 주기의 동일성은 미검증. Owner 원본 1회 검수 이전 `AXIA_MVP_DEMO_ACCEPTED=HOLD`.

## 5. 작업 경계, 추가 현장 테스트

- 새 Student public fix branch `fix/g07-task04-owner-ecm-world-admission-20261118` [PR #52](https://github.com/silverbjin/axia-robot-safety-student/pull/52) (학생 TODO와 강사 정답 분리, main 미병합).
- D06 공개 fix branch `fix/d06-wsl2-owner-parity-first-boundary-20261118`; 기존 소스 SHA 검사·수동 TTY Goal·Nav2/Guard TTL·Scan·RMW·원본 TAR와 SHA256 custody 계속 유지.
- **새 강사 WSL2 실제 Goal L3 아직 NOT_RUN**. 한 번 실행 후 원본 `d06-moving-XXXXXXXX.tar.gz`과 `.sha256` 제출해 최초 안전 상태 전이/최초 타이밍 위반 및 WSLg 두 실제 화면·Nav2 정상 종료 확인. 최초 실패가 새로 발생하면 재시도하지 않고 CI 회귀부터 편입.
- SW 정지는 실제 인증된 하드웨어 E-Stop이 아님. `main` 병합은 사용자 승인 없음. 새로운 교육용 커스텀 안전 계층 추가 금지.
