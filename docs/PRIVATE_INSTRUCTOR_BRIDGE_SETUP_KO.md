# AXIA 강사용 비공개 소스 — 공개 Cloud Runner 격리 시험 브리지

상태: **부트스트랩**. 공개 Runner 성공은 비공개 강사용 코드 PASS와 다르다. main 병합은 사용자 승인 전 금지.

## 고정 및 권한

- 공개 실행 저장소: silverbjin/axia-robot-safety-ci-public
- 별도 개발 브랜치: feat/secure-instructor-cloud-bridge (스택 PR, main 아님)
- 비공개 코드: silverbjin/axia-robot-safety-instructor
- 비공개 목표 HEAD: 72596eff4ad801054f27a3cae1cc60f305a1e6bf (PR #38)
- workflow_dispatch는 Workflow가 default branch에 존재해야 가능하므로, main 병합 전에는 **위 고정 개발 브랜치의 push 이벤트**를 사용한다.
- pull_request, pull_request_target, workflow_run 이벤트로 비공개 토큰을 전달하지 않는다.
- GITHUB_TOKEN: 공개 저장소 contents:read. 별도 PAT는 PRIVATE Checkout step에만 주입.

## 사용자가 GitHub UI에서 할 필수 작업 (비밀값은 채팅에 제출하지 않음)

1. GitHub Settings → Developer settings → Personal access tokens → Fine-grained tokens에서 7일 이내 만료 토큰 생성. **Only select repositories**로 **silverbjin/axia-robot-safety-instructor** 하나만 선택, Contents: Read-only만 부여한다. Metadata 자동 권한 외 별도 권한을 추가하지 않는다.
2. 공개 CI 저장소 Settings → Environments → axia-instructor-sealed 생성(Workflow 최초 시도 시 자동 생성되었을 수도 있음). Required reviewers에 silverbjin 추가, 단독 관리자이면 Prevent self-reviews OFF. Deployment branch 제한을 **feat/secure-instructor-cloud-bridge**로 설정한다.
3. 위 Environment의 **Environment secrets → Add secret** 이름 **AXIA_INSTRUCTOR_READ_TOKEN**, 값은 fine-grained PAT. Repository secret이 아니라 Environment secret으로 지정한다.
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
