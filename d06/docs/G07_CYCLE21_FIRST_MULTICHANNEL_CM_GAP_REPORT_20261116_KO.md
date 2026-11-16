# AXIA G07 Cycle 21 — 사용자 업로드 압축파일 최초 CM 안전 위반 교차 분석

작성일: 2026-11-16. **최종 상태: 공개 CI L0 26/26 GREEN; 실제 새 Gazebo L2 / WSL2 L3 미실행; AXIA_MVP_DEMO_ACCEPTED=HOLD.**

## 1. 업로드 원본 및 무결성

입력: g07-cycle20-owner-evidence-20261116T014955Z-f95ae8fd.tar.gz.
archive SHA256: 1a4625cdc0445b81a81b4aaece2380c45e2e04f7650dbe1fbd4f80be5d7dceff.
내부 6개 regular files, 진단 JSON 5개 SHA256 5/5 일치. original bag/Instructor 소스 미포함. 모두 **보존된 단 한 번의 과거 Owner Goal** 증거. 신규 ROS/Gazebo를 실행하지 않았다.

## 2. 최초 안전 실패의 정확한 시간 분해

- 첫 Guard UPSTREAM_STALE_AFTER_MOTION: CM age **174.184617ms**, CM hard TTL 150ms 초과.
- CM RMW source gap **186.714207ms**, receive gap **189.456950ms**, Observer callback gap **227.710904ms**. CM publication sequence delta=1.
- receive-minus-source gap **2.742743ms**, Observer-minus-source interval **40.996697ms**. 서로 다른 clock domain의 절대 시각을 빼지 말고 구간 길이로만 비교. host_clock_step_excluded=false.
- CM source 발행 공백 동안 Supervisor RMW 발행 **4회**, 최대 연속 발행 간격 **64.896310ms**.
- 동일 Supervisor publication 연속 쌍: RMW source gap **47.358422ms**, Observer callback gap **102.003221ms**, 차 **54.644799ms**. CM 출력 source gap과 별도로 Observer callback 지연 후보가 존재함.
- 선택된 일곱 관측 채널의 공통 이벤트 공백 **88.144560ms**. Observer 공유 실행 지연 후보일 뿐 전체 CPU freeze를 증명하지 않음. Selected Scan callback gap **284.361886ms**, Odom **256.774796ms**. 이는 센서 stamp TTL 판정이 아님.
- Native STOP RPC duration **107.021916ms**. 첫 CM source gap은 STOP RPC 종료 **435.347732ms 이후**이며 중첩하지 않음. RPC 실행 중 블로킹이 이 최초 gap과 동시 발생했다는 설명은 배제, 후속 간접 영향은 미검증.
- Native STOP RPC 중 CM thread /proc 집계: run 12.3835ms / wait 32.474ms, thread count 16, sample 5. FIRST CM GAP 때가 아니므로 그때의 CM scheduler 증거로 승격 금지.
- 환경 스냅샷: 현재 WSL Ubuntu 24.04, 8 allowed CPU, WSLg. **역사적 주행 시점 CPU 상태 아님**. 공식 Jazzy/Harmonic 권장 Ubuntu 24.04 조합.

## 3. 공식 Nav2와 정확한 미계측 경계

공식 Jazzy CollisionMonitor는 입력 velocity 구독 callback에서 process()로 source/TF collision 계산을 거쳐 publishVelocity()로 출력을 내보낸다.
참조: https://api.nav2.org/nav2-jazzy/html/collision__monitor__node_8cpp_source.html

원본은 Supervisor INPUT pub와 CM OUTPUT pub만 측정한다. **CM 내부 INPUT 수신 콜백 진입, Executor 실행, TF 조회 전후, publish 호출** 시각이 없으므로 CM_INPUT_DDS / CM_CALLBACK_EXECUTOR / TF / CM_OUTPUT_SCHEDULING 중 단일 원인을 입증하지 못한다. Guard 150ms hard, CM120ms release, source_timeout 정책을 임의 완화하지 않는다.

## 4. RED→GREEN→REFACTOR→REVIEW→COMMIT 및 공개 CI

공개 브랜치 fix/g07-cycle21-multichannel-first-gap-20261116. main 미병합.

- numeric fixture: d06/tests/fixtures/g07_cycle21_first_cm_8channel_sanitized.json — 절대시간/개인정보/Goal UUID/원본 rosbag 없음.
- pure 분석기: d06/live/g07_cycle21_first_gap_parity.py — 정확한 CM RMW source/receive/observer 간격 및 동일 Supervisor RMW seq-pair, 7채널 선택 공통 quiet window, fail-closed.
- 직접 Cycle20 6파일 archive reader를 엄격히 SHA256 검증한 뒤 동일 분석기로 전달한다.
- tests: d06/tests/test_g07_cycle21_multichannel_first_gap.py 9개, Cycle20 bundle 8개, Cycle19 original archive 9개.
- 공개 Ubuntu24 CI: .github/workflows/axia-g07-cycle21-first-multichannel-gap-l0.yml.
- RED Run 43789324867 (순수 분석기 미구현); GREEN Run 43789485084 (초기 7개).
- 추가 RED Run 43789831926 (실제 압축 직접 리더 미구현); 최종 GREEN Run 43790013225 **9+8+9=26/26 PASS**. 출력 AXIA_G07_CYCLE21_FIRST_MULTICHANNEL_GAP_CI_L0_PASS_NO_ROS_NO_GOAL. CI L0는 실제 Gazebo Goal이 아님.

## 5. 미검증과 다음 한 가지 경계

최초 CM source gap 시점의 실제 CM INPUT subscriber callback/TF lookup/Publisher 시각이 현장 보존 데이터에서 미계측. CI에서 공식 Nav2 코드를 수정하지 않고 기존 passive ROS trace/read-only 계측만 사용해 이 **단일 내부 지연 경계**를 판별하는 최소 실험이 우선. 4-CPU Xvfb CI와 8-CPU WSLg Owner의 CPU affinity·실행 부하 차이도 구분해야 하며 근거 없이 TF·Guard·CM 안전 정책을 바꾸지 않는다. 코드가 변경되면 CI RED→GREEN 후 실제 Gazebo L2 CM<120ms, Guard<150ms, Scan/Odom/Clock TTL, S02 contact0, exact Goal Cancel and ordered shutdown을 검증해야 한다. 그 뒤에만 새로운 Instructor SHA로 Owner WSL2 단 한 번 시연 인수 준비.

기존 raw / Goal attempt lock 보존. 소프트웨어 정지는 인증된 E-Stop이 아니다.
**현재 AXIA_MVP_DEMO_ACCEPTED=HOLD / OWNER_GOAL_RELEASE=BLOCKED. 추가 사용자 WSL2 실행은 요구하지 않는다.**
