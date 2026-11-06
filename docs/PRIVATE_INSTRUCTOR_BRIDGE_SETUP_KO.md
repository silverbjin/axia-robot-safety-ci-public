# AXIA 강사용 비공개 소스 — 공개 Cloud Runner 격리 시험 브리지

상태: **부트스트랩**. 공개 Runner 성공은 비공개 강사용 코드 PASS와 다르다. main 병합은 사용자 승인 전 금지.

## 고정 및 권한

- 공개 실행 저장소: silverbjin/axia-robot-safety-ci-public
- 별도 개발 브랜치: feat/secure-instructor-cloud-bridge (스택 PR, main 아님)
- 비공개 코드: silverbjin/axia-robot-safety-instructor
- 비공개 목표 HEAD: ef948de0298fdf057a34601c5e5cbc310f5517f5 (PR #38)
- workflow_dispatch는 Workflow가 default branch에 존재해야 가능하므로, main 병합 전에는 **위 고정 개발 브랜치의 push 이벤트**를 사용한다.
- pull_request, pull_request_target, workflow_run 이벤트로 비공개 토큰을 전달하지 않는다.
- GITHUB_TOKEN: 공개 저장소 contents:read. 별도 PAT는 PRIVATE Checkout step에만 주입.

## 사용자가 GitHub UI에서 할 필수 작업 (비밀값은 채팅에 제출하지 않음)

1. GitHub Settings → Developer settings → Personal access tokens → Fine-grained tokens에서 7일 이내 만료 토큰 생성. **Only select repositories**로 **silverbjin/axia-robot-safety-instructor** 하나만 선택, Contents: Read-only만 부여한다. Metadata 자동 권한 외 별도 권한을 추가하지 않는다.
2. 공개 CI 저장소 Settings → Environments → axia-instructor-sealed 생성(Workflow 최초 시도 시 자동 생성되었을 수도 있음). Required reviewers에 silverbjin 추가, 단독 관리자이면 Prevent self-reviews OFF. Deployment branch 제한을 **feat/secure-instructor-cloud-bridge**로 설정한다.
3. 위 Environment의 **Environment secrets → Add secret** 이름 **AXIA_CLOUD_CI**, 값은 fine-grained PAT. Repository secret이 아니라 Environment secret으로 지정한다.
4. 설정 완료만 알려준다. PAT 문자열을 이 대화에 올리지 않는다. 승인 대기 시 GitHub의 Review deployments에서 지정한 Job을 승인한다. 연결된 GitHub 도구로 실패 Job 재실행이 가능할 때는 별도 반복 명령을 요구하지 않는다.
5. 종료 시 GitHub Fine-grained PAT revoke, 해당 Environment secret 삭제.

## 민감정보 경계와 검증 한계

- GitHub Actions는 공개 저장소이므로 Job 로그 및 Artifact를 누구나 볼 수 있다.
- 개인 액세스 토큰은 고정된 비공개 저장소의 읽기 권한만 가지며 checkout은 fetch-depth=1, persist-credentials=false.
- Runner에서 강사용 pytest stdout/stderr/traceback/JUnit/rosbag2를 직접 출력하거나 공개 Artifact·cache에 업로드하지 않는다.
- 공개 출력은 stage명, 종료 코드, 테스트 개수/실패 개수, gate_accepted=false 등 allowlist 필드만 제공한다.
- 원본 비공개 테스트 출력은 RUNNER_TEMP 하위의 임시 디렉터리에 두고 종료 시 파기한다. **증거 보존이 아직 없으므로 최종 인수 PASS로 승격하지 않는다.**
- 최초 실행은 강사용 S01~S04 Python Unit과 실제 Jazzy 노드 테스트에 한정한다. 이 게이트 완료 후 안전한 증거 보존을 확보하고 강사용 Gazebo 3회/10회 및 실제 Goal/Fault/odom 시험을 차례로 연결한다.
- 비공개 코드가 명시된 SHA와 일치하지 않으면 BLOCKED. 인증된 HW E-Stop 아님.
- 사용자의 main 병합 승인 전 모든 신규 커밋은 개발 브랜치에만 유지한다.

### 실제 실행 명령 (GitHub-hosted runner 내부)

python3 -m unittest discover -s tests -p test_private_ci_bridge.py -v

python3 scripts/private_ci_bridge.py --private-root _instructor_private --gate unit-middleware

향후 동일 고정 HEAD에 대해 `--gate fake-faults`, `--gate gazebo3`, `--gate gazebo10`를 단계적으로 도입하되, 이를 G00/G03/G04 실제 Goal/Stop/Gazebo 통합 인수로 오인하지 않는다.

## 공개 Runner 보호 한계

Environment Secret, Required Reviewer, SHA 고정, 최소 권한, raw 출력/Artifact 금지는 유출 가능성을 줄이지만 완전히 없애지 못한다. 실행 승인 전 공개 Workflow diff를 점검한다.


## 2026-11-06 16:05 승인 후 첫 실측과 수정

- Environment 승인 성공; `AXIA_CLOUD_CI` 토큰 인증 및 고정 비공개 SHA Checkout 성공.
- 원본 Run #42178521795: UNIT **75/75 PASS**, Jazzy 3 skipped / rc=5, 테스트 0 실행. 전체 FAIL(차단).
- 분석: 기존 브리지가 `PYTHONPATH` 전체를 덮어써 `pytest.importorskip("rclpy")`가 전부 skip. 수정: private 패키지 경로에 **기존 Jazzy PYTHONPATH를 보존**해 추가한다.
- 부가 수정: `ros2 run`을 포함한 미들웨어 종료 테스트에 앞서 private Supervisor/Fault Injector ament_python 패키지를 임시 디렉터리에 colcon 빌드하고 `install/setup.bash`를 source 한다.
- 새 회귀 테스트는 ROS 경로 보존, overlay argv 구성, build 결손 시 fail-closed 검사를 포함. ROS/Gazebo 실제 PASS는 새 Runner 결과가 나오기 전까지 표시하지 않는다.

## 다음 단계 (SHA 고정, 공개 Runner에서 원본 강사 코드 실행)

- 이전 Run #42179543953에서 UNIT 75/75, Jazzy 6/6, private colcon build 전부 실제 PASS.
- 현재 보호된 단일 Job 순서: UNIT + Jazzy → fake ROS Goal/Cancel/Fault → Gazebo 3회 read-only → Gazebo 10회 read-only.
- Gazebo 3/10은 **강사용 실제 패키지**를 포함한 기동/종료/scan/RTF/RTM 사전 검증으로, real Goal·Fault·odom-stop 최종 통합을 수행하지 않는다.
- 어느 한 단계라도 실패하면 뒤 단계는 실행하지 않고 전체 BLOCKED (fail-closed). 공개 로그에는 stage 상태·합계만 출력하며 민감한 JUnit·rosbag2 원문은 업로드하지 않는다.
- Environment Required Reviewer는 각 Workflow Push 실행에 재승인이 필요하다. 사용자 승인 전 작업 시작 불가.
- 최종 로컬 인수는 G00 Goal, G02/G03/G04 fault 및 Nav2 Cancel·odom 근거에 대한 실제 Cloud E2E 검증 이후에만 승인 대상이 된다.

## 2026-11-06 Gazebo 3회 Cloud 사전 인수 현황
- Run #42180837685: private Unit 75 PASS, Jazzy middleware 6 PASS, ROS synthetic Goal/Cancel/Fault **18 PASS**. Official patched Nav2 overlay PASS.
- Private real Gazebo read-only 3x `GAZEBO_READONLY` 종료코드 2 — BLOCKED. 10x 미실행. 공개 원본 로그 노출 방지 때문에 실패한 세부 게이트의 원본은 일시 디렉터리 종료 시 파기됨.
- 공개 브리지가 enum allowlist 및 인원/초과간격 카운트만 출력하는 `private_evidence_diagnostics`를 추가해 재시험. 제안된 Scan watchdog 0.5s를 자동 완화하지 않으며, rosbag receive gap은 Supervisor callback gap을 대체하지 않음.
- 검증 실패를 PASS로 승격하지 않음. Raw rosbag/Hidden Tests/JUnit/Private logs 공개 upload 없음.

## Cold-start Clock 실측 결함 대응 (고정 비공개 SHA)

기존 #42182765806: 1/3 STARTUP/CLOCK_READY BLOCKED, 2/3 startup+Supervisor+shutdown OK이나 /scan rosbag 0.5초 gap 2건, 3/3 startup+Supervisor+shutdown+scan contract OK. 이 샘플은 전체 READY가 아니다.
비공개 강사용 PR #38 수정 SHA `ef948de0298fdf057a34601c5e5cbc310f5517f5`으로 pin 갱신. 초기 Clock phase 최장 45초와 runtime 0.5초 Scan watchdog 분리, 실제 ROS clock progress 2회 전진 조건 불변. clock_diagnostics.json reason은 공개 허용 고정 enum만 출력한다.

## S02/S03 상대 시간계측 — 민감정보 없는 공개 진단

강사 고정 SHA `ef948de0298fdf057a34601c5e5cbc310f5517f5`: 기존 rosbag2 receive gap 외에 Supervisor 실제 `time.monotonic()` Scan 콜백 간격 통계와 독립 `/clock` RTF를 읽기 전용 prestart에서 수집. 공개 브리지는 callback 횟수/0.5s 초과 수/최대값·RTF 범위만 allowlist로 출력. 비공개 State JSON, 스택·로그·raw rosbag 절대 출력/Artifact 업로드 금지. S05 성공 임계값은 아직 원래 정책 유지하고, callback/RTF 측정만 추가한 것이며 합격 주장 금지.

## S04 원본 증거 판정기 Callback/RTF 강화 및 실행 기록

실측 Run #42185904860: Private Unit 80/80 PASS, Jazzy 6/6, fake ROS fault 18/18 PASS. Gazebo 3x: rosbag /scan receive gap 모두 0, Supervisor 실제 monotonic callback over 0.5s는 0/0/1, 마지막 max=0.5379s. RTF 단기 관측=1.257/1.001/0.980. 실제 안전 감시 지연을 확인해 전체 BLOCKED. 해당 재현이 기존 S04에서 충분히 분류되지 않는 상황을 막기 위해 private SHA `ef948de0298fdf057a34601c5e5cbc310f5517f5`에서는 callback 실제 gap=0 + 유효한 RTF 관측을 추가로 필요로 한다. Safety threshold 0.5s 그대로. Public log에서 RTM 실패 코드는 고정 allowlist만 출력하고 증거 파일명/사설 스택 trace는 삭제.
