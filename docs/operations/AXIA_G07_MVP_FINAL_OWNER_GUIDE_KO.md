# AXIA G07 — 강사용 실행·인수 가이드 (NEW SHA 출고 보류)

작성 2026-11-21. **주의: 새 refactor SHA로 Moving Goal을 강사 WSL2에서 실행하지 말 것.** 동일 정확 SHA 실 Gazebo native 2/2 인수 기준 미달(0/2 FAIL).

## 1. 기존 시연과 새 변경을 구분

기존 jrCIgoGl 교육용 WSL2 시연: CLEAR→SLOW→STOP, 같은 Goal UUID Cancel, 실제 odom ZERO dwell 1.029446초, 14-topic SQLite rosbag, 21/21 범위 내 수치 PASS의 증거가 존재. 원본 파일: docs/operations/AXIA_G07_TASK04_JRCIGOL_OWNER_MVP_ACCEPTANCE_20261120_KO.md. 이는 강사 자료/Replay 교육에 재사용할 수 있지만 새 변경의 반복 안정성 PASS가 아님.

새 Student commit a04f9a7da8d54bbd9f944d05388792cb706adf28, Public native source commit 8e03ac0a912ca9b81bdddda70212e52e6d804389: CI run #44914827138 real Moving Goal 0/2 FAIL. L0 regression 성공을 Moving Goal PASS로 표시하지 않는다.

## 2. 공개 링크 (실제 검수 증거)

- Student Draft PR #105: https://github.com/silverbjin/axia-robot-safety-student/pull/105
- Student GREEN L0 #44914690178: 4 graph-shutdown unittest PASS, 기존 Block B 59 PASS.
- Student real Gazebo NO_GOAL #44914690240: 실제 GUI/Nav2 조건 통과, Goal 보내지 않음.
- Public Draft PR #229: https://github.com/silverbjin/axia-robot-safety-ci-public/pull/229
- Public Python #44914941704: 341 PASS / 3 SKIP.
- Public strict G07 Moving Goal #44914827138: 0/2 FAIL (Cycle1 preGoal Scan/Clock/Odom, Cycle2 postGoal Odom/CM/Guard).

## 3. 강사가 안전하게 확인할 수 있는 로컬 정적 테스트 (새 Goal 없음)

~~~bash
(
  set -Eeuo pipefail
  PIN=a04f9a7da8d54bbd9f944d05388792cb706adf28
  WORK="$(mktemp -d)"
  trap 'rm -rf "$WORK"' EXIT
  git clone -q https://github.com/silverbjin/axia-robot-safety-student.git "$WORK/student"
  git -C "$WORK/student" checkout -q --detach "$PIN"
  test "$(git -C "$WORK/student" rev-parse HEAD)" = "$PIN"
  python3 -m unittest discover     -s "$WORK/student/block_B/day07/h01_runtime/tools"     -p test_g07_context_graph_shutdown.py -v
)
~~~

위 명령은 실제 ROS/Gazebo/Goal을 실행하지 않는다. GitHub CI에서 검수됐고 이 문서를 작성한 ChatGPT는 사용자의 WSL2에 이 명령을 실제 실행한 적이 없다. 임시 checkout은 용량이 부족할 때 실행하지 말고 공개 CI 원본만 확인한다.

## 4. 새 Owner 원샷 인수 해제 조건

다음 전부 충족하기 전에는 새 WSL2 Goal 명령을 출고하지 않는다.
1. 같은 정확한 Public + Student SHA의 **실 Gazebo Moving 2/2**.
2. 첫 Scan/Clock/Odom 300ms, CM 120ms, Guard 150ms 경계를 실제 수신·메시지 freshness·FSM 전이로 입증.
3. 실제 물리 Gazebo LiDAR 10Hz, Depth OFF, official Nav2/CM, Goal 1개 및 TTY YES-P2-G07-GOAL 승인, 우회 cmd_vel 발행 없음.
4. CLEAR/SLOW/STOP, UUID Cancel, odom zero 1초, Nav/Loc ACK, 모든 필수 자식 exit0, contact/evidence.
5. 원본 14-topic rosbag 및 SHA256 원본 custody, GUI 실패와 안전 타이밍 실패 분리.
6. 새 현장 오류는 최초 상태전이·첫 타이밍 위반부터 공개 CI RED→GREEN. 현장 재시도 반복 금지.

그 이후에만 기존 Public Owner 원샷을 신규 정확 SHA로 고정하고 단일 Copy/Paste WSL2 명령을 안내할 수 있다. **지금 출고하지 않음**.

## 5. 강사 수업 운영 권고

검증된 jrCIgoGl 교육용 기존 Replay/원본 로그를 사용하여 CLEAR→SLOW→STOP, Goal Cancel, odom 정지, TTL, P/N/U 구분 실습을 진행한다. 강사용 비공개 정답은 instructor repo에만 보관, Student TODO와 분리. Software 보호 정지를 안전 인증 E-Stop으로 표현하지 않는다.

결론: 기존 교육용 baseline 보존. 새 리팩토링 L0 PASS, G07 Moving L2 FAIL 0/2, 새 Owner WSL2 L3 NOT_RUN, main NOT_MERGED.
