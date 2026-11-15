# AXIA Robot Safety MVP — 공개 CI 우선 검증 지침 (2026-11-15)

## 승인된 운영 규칙

- **PUBLIC_CI_ONLY**: 새 구현/수정의 공식 자동 회귀 검증은 `silverbjin/axia-robot-safety-ci-public`의 공개 GitHub Actions를 기본 게이트로 사용한다. 학생 독립 저장소 CI는 추가 공개 증거다. C-01 검증은 비공개 Runner 복구를 기다리지 않는다.
- **PRIVATE_CI_NOT_RELEASE_GATE**: 기존 Instructor 저장소의 비공개 Actions 및 비공개 Environment/Runner 결과는 앞으로 인수 필수 조건이 아니다. C-01 전용 Private CI workflow는 개발 브랜치에서 제거한다. 단, 다른 과제의 기존 워크플로·branch protection이 남아 있다면 자동 중지/해제되었다고 주장하지 않는다. 관련 변경은 별도 승인을 거친다.
- **NO_PRIVATE_CHECKOUT**: 공개 CI에서 Instructor 비공개 저장소, Hidden Tests, 강사 정답, 인증정보, WSL2 원본 비공개 로그를 체크아웃·출력·아티팩트로 유출하지 않는다. 공개 CI에서는 재현 가능한 synthetic fixture, 공개 인터페이스 계약 및 비밀을 제거한 재현기만 사용한다.
- 강사 정답·Hidden Tests는 Instructor 비공개 Git 이력에 계속 보존한다. 필요한 강사 전용 코드 검토는 비공개 로컬 정적 검토/테스트로 기록하되, 그 결과를 '공개 CI에서 검증된 private code'라고 주장하지 않는다. 공유 가능한 generator/검사기/CSV는 각 저장소의 Git Blob SHA 일치 여부를 별도로 확인한다.

## RED → GREEN → REFACTOR → REVIEW → COMMIT 규칙

1. 최초 위반/재현 가능한 범위로 공개 테스트를 작성해 실제 RED 출력(rc≠0)을 보존한다. 비공개 데이터가 필요한 경우 개인 데이터를 그대로 공개하지 않고 일반화한 synthetic fixture와 경계 조건만 반출한다.
2. 최소 코드로 GREEN 전환 후 **동일 CI 실행기**로 재검증한다. 기존 PASS를 반복하지 않고 관련된 가장 작은 회귀만 실행한다.
3. REFACTOR 후 변경 범위/안전 불변조건 리뷰, 원본 stdout·stderr·JUnit·JSONL·체크섬·정확한 소스 SHA를 남기고 커밋한다.
4. 공개 CI PASS는 실제 **실행된 수준·원본 commit·데이터 전달 주기/TTL 검증 범위**를 명시한 경우에만 그 범위의 인수 준비 근거로 사용한다. 학습용 단위시험을 ROS·Gazebo 실측으로 승격하지 않는다.
5. Owner WSL2에서 새로운 오류가 발견되면 재현 가능한 부분을 공개 CI에서 RED → GREEN 회귀로 먼저 처리한다. 안전 오류는 최종 예외가 아니라 최초 안전 상태 전이와 최초 타이밍 위반을 기준으로 진단한다. G07 및 다른 안전계층의 데이터 전달 주기·Guard TTL은 실제 연결된 노드 간 경계를 확인해야 하며, 검증하지 않았으면 전체 안정성 미검증으로 기록한다.

## 검증·출고 권한

- C-01: PUBLIC CI의 Python 3.12 CPU L0 — 데이터 생성 결정성, schema/units/10Hz, SHA256 인벤토리, trace-level train/valid/test split, 결측·샘플 누락·stamp regression·drift 품질 처리, Owner clone→pin→test 경로가 범위다. ROS·Gazebo·안전제어는 미검증이다.
- D12 ROS L1의 경우 실제 Jazzy pub/sub 주기와 원본 로그를 추가해야만 `ROS_VERIFIED`를 표시할 수 있다. G07/P4 등 물리 시연의 L2/L3는 별도의 실제 Gazebo/Owner 증거가 필요하다.
- **OWNER_WSL2_NOT_VERIFIED**: Owner 실제 WSL2를 실행하지 않은 CI에는 WSL2 인수 상태를 성공으로 쓰지 않는다. 성공적인 CI 재현은 현장 실행 성공을 보장하지 않는다.
- **APPROVED_BASELINE_UNCHANGED**: 기존 Baseline v1 및 안전 Supervisor, Nav2/Collision Monitor/Watchdog, Stop/Recovery, G00~G13, 인증 E-Stop 구분은 변경하지 않는다. 교육용 SW Stop이 인증된 E-Stop으로 간주되지 않는다.
- **NO_MAIN_MERGE_WITHOUT_APPROVAL**: 공개 CI PASS 후에도 강사/학생/공개 CI의 각 `main` 병합과 최종 학생 출고는 사용자 명시 승인 전까지 금지한다.

## C-01 공개 CI 인수 근거

- 고정 Student SHA: `766ef987fc0357fdf171fa0926dbef65c6aae972` (독립 학생 TODO 저장소).
- 검증 기준 공개 CI 소스: `9701867dfe2ac4015bd8498d45495cd1e4dd712d`의 [Run #43715693111](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43715693111); Ubuntu 24.04 / Python 3.12.16; bootstrap 3 tests + data 10 tests PASS, clone/HEAD pin 검사, 46 traces/4,599 rows; 공개 증거 Artifact #14162760717.
- C-01 신규 정책 검증 후 **새 공개 CI HEAD의 Run으로 최종 게이트 갱신**. 위 Run은 정책 자체 테스트 이전의 유효한 데이터/실행기 증거다.
- 비공개 Instructor Actions의 `runner_id=0,steps=[]` 실패는 역사적 `INFRA_BLOCKED`로만 보존한다. 더 이상 새 C-01 릴리스를 차단하는 게이트가 아니다. 숨겨진 강사용 알고리즘 정답이 공개 검증됐다는 뜻도 아니다.
