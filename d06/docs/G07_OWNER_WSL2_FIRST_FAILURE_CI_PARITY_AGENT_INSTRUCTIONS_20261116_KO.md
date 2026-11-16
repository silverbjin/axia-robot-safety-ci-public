# AXIA G07 Owner WSL2 최초 실패 → 공개 CI 회귀 우선 지침 (2026-11-16)

**목표:** 한 번의 실제 GUI Gazebo CI L2 성공을 사용자 WSL2 안전 인수와 혼동하지 않고, 실제 최초 현장 실패가 재현되기 전에는 Owner Goal을 재출고하지 않는다. MVP 범위를 벗어난 개발 확대 금지.

## 사실과 증거

- 마지막 공개 실제 L2 Run `43727149856` PASS, private Instructor `01d45d46b6eb6a05b1bd313d73f1fc3549575545`, CI CM Observer 최대 `110.964002ms` (120ms 출고 여유).
- 사용자가 업로드한 SHA256 검증된 support bundle: 28개 파일 integrity PASS, 현재 실행은 `no_ros_no_goal=true`, `AXIA_G07_FINAL_OWNER_REPEAT_BLOCKED...`에서 중단. GUI ZIP은 빈 디렉터리 + 0바이트 SHA256SUMS. `D06_RVIZ_NOT_CONFIRMED`는 후속 로그이므로 첫 원인 아님.
- 같은 private SHA의 **이전 실제 WSL2 Goal 시도**가 2026-11-15T22:24:56Z custody에 존재. 14-topic ROS bag, exact Goal UUID 및 cancel 관측, 최초 Guard 내부 CM age `174.184617ms` >150ms, CM RMW source gap `186.714207ms`, gap 안 Supervisor 발행 4회, 최초 전이 `UPSTREAM_STALE_AFTER_MOTION`. Owner L3 FAIL.
- 따라서 기존 SHA+CI Run의 단일 시도 잠금은 **정당**. 만료/자동삭제/새 릴리스 SHA로 재시도 우회 금지. 현재 종료는 24.04 호환성 오류가 아님.
- Ubuntu 24.04 Noble / ROS2 Jazzy / Gazebo Harmonic은 ROS·Gazebo 공식 권장 조합. WSLg·실제 RMW 지연의 원인은 별도 계측 전 미확정.

## 에이전트 실행 지침 (다른 대화에도 그대로 사용)

1. **증거 우선:** 업로드된 Original·manifest의 SHA256, private SHA·CI Run·Goal UUID·최초 Guard latch·최초 source/receive 간격·upstream 발행 주기를 서로 결합한다. 최종 예외·GUI 로그·최근 유리한 CI PASS로 첫 안전 위반을 덮지 않는다.
2. **CI-first:** 현장 첫 CM 174.185ms/186.714ms 및 Supervisor 4회를 *비식별 fixture*로 공개 CI에 편입한다. 원본 rosbag·개인 HOME·Goal UUID·private repo 코드는 공개 저장소에 게시하지 않는다. 새 회귀가 실패하는 RED를 먼저 확보한다.
3. **출고 게이트 두 단계:** `CI_L2_EVIDENCE_VALID`와 `FIELD_PREVIOUS_GOAL_HISTORY_CLEAR`는 다른 조건이다. 이전 같은 private SHA+CI Run의 Goal 또는 Guard TTL 위반이나 불명확한 예약이 있으면 `OWNER_FIELD_RELEASE_HOLD`, `manual_attempt_allowed=false`; **GUI/ROS 시작 및 Owner attempt 예약 이전**에 차단한다.
4. **안전 상태 기계:** `READONLY_PREFLIGHT → GUI/ROS_READY_VERIFIED → GOAL_RESERVATION → TTY_CONSENT → SINGLE_GOAL → EVIDENCE_REVIEW`. 기존 attempt lock을 삭제하거나 결과를 합성하지 않는다. 예약은 가능한 마지막 승인 경계에서 원자적으로 수행하고, 모든 이전 단계 실패는 신규 Goal 시도로 보고하지 않는다.
5. **실제 배포 동형성:** Ubuntu24 GitHub runner에서 같은 entrypoint의 no-ROS read-only preflight를 **깨끗한 HOME와 기존 실패 HOME** 양쪽에서 subprocess로 검증한다. symlink/손상 원본, 불완전한 field 증거는 fail-closed. No ROS/Goal 시 발생한 출력에서 `RVIZ_NOT_CONFIRMED`와 원본 없음이라는 후속 예외를 최초 원인으로 승격하지 않는다.
6. **타이밍 안전:** Guard CM 150ms hard TTL, CM 운영 출고 여유 120ms, Scan/Odom/Clock 300ms hard 경계를 완화하지 않는다. 안전 제어에 변경이 있으면 L0 RED→GREEN 후 실제 Gazebo L2에서 첫 Guard 전이, source→CM→Guard 주기, S02 contact0, exact Goal cancel, Nav2 ack/CM exit를 관찰한다. 1회 CI L2 PASS만으로 WSL2 원인 제거를 주장하지 않는다.
7. **인수 보류:** 현장 첫 `UPSTREAM_STALE_AFTER_MOTION`의 재현 가능 경계에 대한 CI 수정·검증과 현장 이력의 엄격한 별도 승인 전에는 **어떤 새로운 Owner moving Goal도 배포하지 않는다.** `AXIA_MVP_DEMO_ACCEPTED=HOLD`로 유지한다.
8. **제출:** 파일 경로, 실행 명령, 원본 테스트 출력, L0/L1/실제 L2/WSL2 L3 검증 수준, 미검증 항목, SHA/branch/Run, 각 디버깅 사이클의 보고서를 커밋한다. `main` 병합은 사용자 승인 후. SW 시뮬레이션 STOP은 인증된 E-Stop이 아니다.

## 이번 회귀 대상

- 우선 L0: 기존 같은 SHA/Run 잠금이 있는 HOME, 원본 field Guard TTL 위반, 7채널의 120/150ms 경계, CI RUN PASS이지만 field FAIL인 상태를 재현하여 현재의 잘못된 `manual_attempt_allowed=true` 출력 경계를 정정한다.
- 미해결 L1/L2: 실제 WSLg에서 CM source 186.714207ms 공백의 스케줄러/TF/RMW 원인, Supervisor가 4회 계속 발행하는 동안의 안전 경계. 원인 진단 전에는 새 Goal 재시도 금지.
- 별도 문서: `AXIA_G07_CI_FIRST_FIELD_FAILURE_PARITY_STANDARD_20261116_KO.md` (사용자 제공 문서 버전, 동일 원칙 상세).

**현재 인수 판정: `AXIA_MVP_DEMO_ACCEPTED=HOLD`.**
