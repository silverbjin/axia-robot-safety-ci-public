# AXIA Block C D09–D12 — Owner WSL2 최종 검수 및 출고 승인 요청 절차

- 상태: **원샷 스크립트 공개 CI 코드 계약 테스트 대상**. 실제 Owner WSL2의 `--run` 실행은 이 문서/공개 CI에서 수행하지 않음.
- 프로파일: `BLOCK_C_EDUCATION_MVP_D09_D12`, synthetic 데이터 교육용, 실제 생산 Safety Supervisor/Collision Monitor/Gazebo 정식 안전 인수와 별개.
- 정확한 소스 SHA: Instructor private `961b574e7623eede6ae94bf7b9cf06e62dc3674a`, Student public `dff7b4a2710525a72287f5416b7b613a9d979f1e`, Public CI baseline `18631cf070b4c2afb994aa49013fee69224d2aa1`.
- 기존 공개 CI 성공 근거: C-01 `43716783675`, C-05 Jazzy DDS L1 `43720178979`, C-06 학생 계약 `43725720019`. 원샷은 API에서 각 Run의 `conclusion=success`와 정확한 `head_sha`를 확인한다.

## 사전 조건

Windows 10/11 **WSL2 Ubuntu 24.04**, Python **3.12**, ROS 2 **Jazzy**, `colcon`, `git`, `curl`, `tar`, `sha256sum` 설치. GitHub private Instructor 저장소의 읽기 권한과 git credential helper 또는 `gh auth login` 완료. pip/CPU wheel 설치가 가능한 인터넷·저장공간이 필요하다. 스크립트는 승인 없는 `sudo` 설치나 기존 ROS 노드 종료를 수행하지 않는다.

권장 실행: **공개 CI의 검증된 commit SHA로 고정된 Raw GitHub 스크립트를 내려받아, SHA256 확인 → `bash -n` → `--self-check` → `--run`**. 배포 응답의 단일 명령 블록을 사용한다. `main` 병합 및 원격 저장소 수정은 하지 않는다.

## 일괄 검수 단계

1. 실제 WSL2와 Ubuntu Python3.12/ROS Jazzy/colcon 환경 확인. 비-WSL2에서는 `WSL2_REQUIRED`, exit nonzero, `HOLD`.
2. 기존 C-01/C-05/C-06 공개 CI 성공과 소스 SHA 고정 확인.
3. 인증된 로컬 Owner 계정으로 Instructor private clone, Student public clone. Student는 **Instructor checkout의 `student/`** 폴더에 두어 기존 강사용 C-06 테스트 상대경로를 재사용한다. 각 원격 HEAD가 고정 SHA와 다르면 중단.
4. 두 manifest의 **실제 각 파일 SHA256** 검증, synthetic fixture(8개)와 교육용 C-05 ROS transport(4개)의 Instructor↔Student 바이트 비교.
5. 실행별 venv(`--system-site-packages`) 설치. 스코프 고정: Python3.12, pytest8.3.5, NumPy2.2.6, scikit-learn1.8.0, python-pptx1.0.2, **CPU PyTorch2.10.0+cpu**. 현장 환경에 맞는 CPU wheel 설치가 실패하면 `HOLD`, 버전을 임의 변경하지 않음.
6. Instructor `--unit` 및 비공개 Hidden Test, Student `--unit` 실행. Student TODO의 미작성 기능시험 4건은 `EXPECTED_RED`로 보존.
7. C-02 EDA → C-03 IF → C-04 AE 기존 checkpoint → C-05 JSONL **실제 단계별 연결 실행**. 원본 유효성·train/valid/test 분리·UNKNOWN=4·score cutoff 출처 등을 검사한다. 재현 가능한 정답 성능이 아닌 수업용 synthetic metric만 보고한다.
8. 강사용 ROS `axia_block_c_diagnostics` 실제 `colcon build`, 패키지 실행파일 발견.
9. Instructor/Student 각각 Jazzy 교육용 `DiagnosticArray` DDS 발행·구독 8건, 실제 측정 period 기록. `cmd_vel` 발행자/Goal 없음.
10. 방금 생성한 AE 점수→JSONL 이벤트에서 네 레벨을 각각 2건 추출(원본 순서 보존)→**실제 Jazzy DDS 발행·수신** 8건 검증. 해당 통합은 교육용 진단 데이터 파이프라인이며 생산 Guard TTL과 무관.
11. 실행별 실패 단계, stdout/stderr, JSON/JUnit·원본 데이터 SHA를 `$HOME/axia_block_c_owner_acceptance/run-*/`에 보존. 증거 tar.gz 및 SHA256 생성.

## 성공 메시지와 판정

아래 메시지는 **기대 패턴**이며 실제 Owner WSL2 출력으로 아직 확인되지 않았다 (`EXPECTED_NOT_MEASURED`). 숫자형 timing 및 모델 혼동행렬은 현장 결과를 기록한다.

```text
BLOCK_C_INSTRUCTOR_MANIFEST_SHA256_PASS ...
BLOCK_C_STUDENT_MANIFEST_SHA256_PASS ...
BLOCK_C_SHARED_C01_C05_BYTES_IDENTICAL
BLOCK_C_INSTRUCTOR_PYTHON_L0_PASS ...
BLOCK_C_STUDENT_SCAFFOLD_PUBLIC_L0_PASS ...
BLOCK_C_STUDENT_TODO_EXPECTED_RED_4_CONFIRMED
BLOCK_C_PIPELINE_L0_PASS windows=424 valid_test=100 invalid_test=4 events=104
BLOCK_C_OWNER_COLCON_JAZZY_BUILD_PASS
BLOCK_C_OWNER_EDUCATION_ROS_L1_PASS ...
BLOCK_C_OWNER_MODEL_TO_JAZZY_DDS_L1_PASS samples=8 ...
BLOCK_C_OWNER_ACCEPTED=READY_FOR_OWNER_APPROVAL
BLOCK_C_RELEASE_APPROVED=false
BLOCK_C_OWNER_VERDICT=/home/.../verdict.json
BLOCK_C_OWNER_EVIDENCE=/home/.../AXIA_BLOCK_C_OWNER_EVIDENCE.tar.gz
```

어느 필수 단계든 실패하거나 출처·해시·ROS 주기 검증이 누락되면 `BLOCK_C_OWNER_ACCEPTED=HOLD`로 종료하며 자동 PASS나 승인 승격을 하지 않는다. `verdict.json`의 `last_stage`와 각 단계별 `evidence/*.log`에서 **최초 실패 경계**를 확인하고, 재현 가능한 문제는 공개 CI의 안전한 synthetic 회귀 RED→GREEN을 우선한다.

`READY_FOR_OWNER_APPROVAL`는 **기술 검수 적격/출고 승인 요청 상태**이며 자동 출고 승인이 아니다. 사용자 승인 후에만 `RELEASE_APPROVED`를 별도 선언하고, GitHub `main` 병합도 사용자 별도 승인이 필요하다. 실제 Gazebo 주행, 인증 E-Stop, 생산 안전 TTL, 4일 강의 12시간 리허설은 **이 프로파일에서 미검증**으로 표기한다.

## CI 검증 범위

공개 CI는 실행기를 `bash -n`, `--self-check`, 정적 보안·핀 계약, **비-WSL2에서 `HOLD`로 실패하는 경계**만 검증한다. **비공개 Instructor 체크아웃이나 실제 Owner WSL2 실행을 공개 CI가 수행했다고 주장하지 않는다.**
