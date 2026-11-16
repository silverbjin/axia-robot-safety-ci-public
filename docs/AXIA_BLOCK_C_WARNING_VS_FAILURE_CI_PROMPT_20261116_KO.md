# AXIA Block C — Owner 인수 증거의 경고/실패 구분 및 공개 CI 회귀 프롬프트

적용일: 2026-11-16. 교육용 Block C D09~D12 / ROS 2 Jazzy / Ubuntu 24.04 WSL2. 기존 기준선 및 Safety Guard 소스는 변경하지 않는다.

## 다음 개발 담당자에게 그대로 사용할 프롬프트

> 당신은 ROS 2 Jazzy, Gazebo Harmonic, Nav2, Python 및 AXIA Robot Safety MVP의 개발/검증 책임자다. Owner WSL2 로그에 `WARNING`, `ERROR`, `stderr`, `failed` 문자열이 있더라도 **문자열 존재만으로 실패 또는 성공을 판단하지 마라**.
>
> 1. 첨부 증거 TAR/체크섬/판정 JSON의 실제 바이트를 확인해 SHA256을 대조하고, TAR의 위험 경로·링크·중복 구성요소를 거부하라. `verdict.json`, `stage_status.tsv`, JUnit, ROS DDS probe raw 결과를 서로 대조하라.
> 2. **최초 위반 게이트를 추적**하라. `STAGE_PASS`인데 해당 단계 로그에서 처리되지 않은 Python `Traceback`/`AssertionError`/`FileNotFoundError`가 발견되면 게이트 false-PASS로 간주하고 `HOLD`로 분류하라. 별도 stage 실패 후 최종 PASS는 인정하지 마라.
> 3. `pip`가 시스템 영역의 `sympy`/`mpmath`를 제거하지 못하는 알림, `pybind11` 메타데이터 경고, optional `torch` 사전 탐지 실패, `types-seaborn` 같은 교육 범위 외 패키지 의존성 충돌, `colcon`의 byte-compiling 생략 경고는 **최종 의존성 버전·정식 코드 import/테스트·빌드 종료코드가 성공하는지 확인**한 뒤 `NON_BLOCKING_ENV_NOTICE`로 별도 기록하라. 문제를 숨기거나 `pip` 실패를 무조건 0으로 바꾸지 마라. 동일 경고가 필수 import/노드 동작에 영향을 주면 그때 최소 재현 CI RED를 작성하라.
> 4. 강사·학생 단위시험 성공과 학생 과제의 **의도적 `4 failed`**는 구분하라. 학생 TODO 미구현의 EXPECTED_RED를 강사 배포 실패로 집계하지 마라. 기대 외 실패 건수는 `HOLD`로 표시하라.
> 5. `C-05` 교육용 진단 DDS의 강사/학생/실제 AE 이벤트 각각에서 publisher return code 0, 8개 수신, 상태 0/1/2/3, 주기 범위, `/cmd_vel*` 발행자 0, `goal_sent=false`, `control_authority=false`를 검증하라. `ros_actual=true`는 교육용 ROS L1에만 적용하고 Gazebo·생산 Guard TTL·인증 E-Stop 인수로 확장하지 마라.
> 6. 공개 CI에는 절대로 실제 Instructor 비공개 코드, Hidden Test, Owner 원본 증거 TAR, 사용자 홈 경로/토큰을 업로드하지 마라. **공개 합성 증거**를 만들어 동일 공개 검증기 `block_c/scripts/axia_block_c_evidence_audit.py`로 무결성·중간 실패 은폐·주기 위반·잘못된 출고 승인 등 최소 경계를 RED→GREEN으로 검증하라.
> 7. **실행기 일치:** 현장 `block_c/scripts/axia_block_c_owner_final_once.sh --run`과 공개 CI `--ci-parity`는 동일한 파일/검증 함수를 사용한다. 후처리 시 공개 CI와 Owner 로컬은 동일한 `axia_block_c_evidence_audit.py`를 사용하되, CI에는 synthetic archive만 입력한다. 현장 ROS 실제 실행은 CI synthetic PASS로 대체하지 않는다.
> 8. RED→GREEN→REFACTOR→REVIEW→COMMIT 순서를 지켜, 결과 로그·CI Run ID·증거 SHA·Git HEAD·검증 수준·미검증 사항을 한국어 개발 보고서에 기록하고 커밋하라. 사용자 승인 없는 `main` 병합 및 `RELEASE_APPROVED=true` 승격을 금지하라. 이미 원본 인수가 PASS라면 새로운 현장 반복 주행을 요구하지 말고 기존 증거를 재사용하라.

## 2026-11-16 R02 최초 현장 상태

- 사용자가 업로드한 `AXIA_BLOCK_C_OWNER_EVIDENCE.tar.gz` 원본 SHA256: `6fb997c9a684def1fcf629b88ba2a548071f2c0e270c0576ad76b81769c13ebb`. 함께 받은 체크섬 파일과 일치.
- 실제 `verdict.json`: `status=READY_FOR_OWNER_APPROVAL`, `exit_code=0`, `owner_wsl2_verified=true`, `release_approved=false`.
- 13개 필수 단계 모두 PASS. 강사 JUnit 32/0/0/0, 학생 JUnit 5/0/0/0, 학생 TODO 4 EXPECTED_RED.
- C-02~C-05 pipeline 424 windows, test 100 VALID + 4 INSUFFICIENT_DATA, 104 events; IF TP1/FP2/FN17/TN80, AE TP18/FP4/FN0/TN78. 합성 교육 데이터로만 검증.
- 실제 WSL2의 강사·학생·AE 모델→ROS DDS, 각각 8개 DiagnosticArray 수신, 구간 99.407758–100.669715ms / 99.463166–100.523436ms / 99.681494–100.642019ms. 인증 안전 TTL 검증 아님.
- 진단 로그의 `types-seaborn`, `pybind11`, `sympy`/`mpmath`, `torch` 초기 probe, setuptools byte-compiling 경고는 실제 설치·테스트·ROS 빌드 결과와 대조한 **관찰 가능한 비차단 메시지**. 해당 시스템 패키지 구성이 완전히 정상임을 보증하는 것은 아니다.

## 이번에 추가한 공개 CI 회귀 범위

- 공개 합성 증거만 생성하고 **동일한 후처리 감사기** 실행; Owner raw archive·Private 정답은 CI로 보내지 않는다.
- 정상 PASS; SHA256 변조; 로그 속 은폐된 traceback; stage TSV/verdict 불일치; `/cmd_vel` publisher; DDS period 900ms 위반; 학생 TODO 실패 건수 이상; 무승인 `release_approved=true` → 각각 fail-closed 검증.
- 소스: `block_c/scripts/axia_block_c_evidence_audit.py`, `block_c/tests/test_owner_evidence_audit.py`, `.github/workflows/block-c-owner-evidence-audit.yml`.
- 실제 Owner 원본과 같은 감사기로 로컬 재검사 PASS. **여기서 새로운 ROS/Gazebo 실행을 수행하지 않았음**.
- 시험 결과가 `PASS_SCOPED_OWNER_EDUCATION_MVP`여도 정식 출고와 `main` 병합에는 Owner 별도 승인 필요.
