# AXIA G07 — 최소 리팩토링 작업 계획 및 승인 기준

기준: 2026-11-21 KST, Student Draft PR #105, Public Draft PR #229. 목표는 신규 기능 없는 실제 결함 제거. 기존 jrCIgoGl 교육용 증거와 Baseline 보존.

## 문제별 우선순위

| 우선순위 | 확정 근거 | 허용하는 최소 수정 | 금지 |
| --- | --- | --- | --- |
| P0 | Native #44912769355 종료 시 Supervisor graph RCLError exit1 | 기존 shutdown classifier에 context_ok=False 및 정확한 RCLError만 추가 | 활성 Context 예외 무시/except pass |
| P0 HOLD | Native #44914827138 preGoal Scan·Clock·Odom와 postGoal CM/Guard 수신 위반 | 원본 첫 위반·첫 FSM 전이 보존, 별도 원인 입증 전 release HOLD | TTL 상향/추정에 의한 Executor 교체 |
| P1 | ROS 2 4패키지 표준 구성 정상 | 파일/종속성·Launch·환경 책임 문서화 | 전체 폴더 대이동 |
| P1 | 실행 Shell 약1293줄, 3 Shell + 114 tools Python | 활성 호출 관계 확인, 기존 단일 진입점 유지 | 무근거 대규모 스크립트 통합 |
| P1 | CI/Owner/GUI 환경변수 프로필별 구분 | source pin/ROS_DOMAIN/GZ_PARTITION/TTY 권한 유지 | CI Goal 권한을 Owner에 복사 |
| KEEP | 공식 Nav2, Waffle, CM, Supervisor/Guard, 실물 scan | 동일 안전 제어 그래프 유지 | 신규 노드, 신규 middleware/worker |
| P2 | 임시 /tmp YAML, ScenarioVerifier 소스 ROOT 추정 | 잠재 부채로 기록 | 시연과 무관한 변경 확대 |
| REJECT | Public lean PR #228 실제 Native 0/2 | 성능 미입증 후보로 보존 | 입증 없이 기본값 승격 |

## 실제 RED→GREEN→REFACTOR→REVIEW→COMMIT

Student:
1. test RED commit 7592fb3df908705b30b69a87a9cc59151fb570d5: tools/test_g07_context_graph_shutdown.py, 4개 경우.
2. 기존 CI에 호출 연결 commit 11529591ae3db2f798de0657e097bb46a79be128; #44914584695 실제 1 FAIL + 2 ERROR + 1 PASS.
3. GREEN commit a04f9a7da8d54bbd9f944d05388792cb706adf28: p2_shutdown_context.py에 정확한 context 종료 classifier, p2_supervisor_node.py에서만 연결, 다른 safety/runtime 무변경.
4. Student #44914690178 L0 GREEN, 4/4 unittest + 59 Block B PASS.
5. Student #44914690240 실제 D07 H01 Gazebo GUI NO_GOAL L2 success, G07 Moving 검증으로 승격 금지.

Public:
1. Native workflow exact Student a04f9a7 고정 commit 8e03ac0a912ca9b81bdddda70212e52e6d804389; 기존 2 cold cycles, Safety TTL/Contact/rosbag/Goal/cleanup 그대로.
2. 이전 frozen Owner release와 새 미인수 Student SHA를 하나로 묶는 테스트를 분리한 commit 8daaa1a734edfb54126b7e2d5ecadfb3ca4b89f1.
3. Public #44914941704 Python 341 PASS / 3 SKIP; Native #44914827138 실제 0/2 FAIL.

## 인수 기준과 범위 동결

L0: ROS-free graph classifier 정확한 오류만 통과, 실시간 오류 실패, 기존 테스트 PASS.
L1: colcon 빌드/설치형 ros2 pkg prefix, pkg executables, ros2 launch --show-args 및 TF/params 확인. 이번 실제 G07 runtime 일부 실행 외 별도 전패키지 설치 검수 미완료.
L2: 실제 Jazzy/Harmonic 2/2 Moving Goal CLEAR→SLOW→STOP, Goal UUID Cancel, odom zero≥1s, 보호 노드 CM120/Guard150/Clock-Odom300 및 실제 Scan freshness, Nav/Loc shutdown ACK, child exits0.
L3: L2 통과 후에만 기존 Owner script를 정확 SHA로 출고, 명시 TTY YES-P2-G07-GOAL, 단일 WSL2 실행. 현재 미출고/미실행.

첫 실패가 있으면 같은 현장 재시도 금지. 원본 첫 safety FSM 전이와 첫 timing breach 분석 후, 재현 가능한 부분을 공개 CI RED→GREEN으로 편입. 이번 수정으로 Scan/RMW 장애가 해결되지 않았으므로 신규 인수 HOLD. main 병합 사용자 승인이 있어야 함.
