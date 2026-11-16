# AXIA 공개 CI 우선 — Owner WSL2 현장 실패 재현·검증 지침 (2026-11-16)

## 용도
Owner WSL2 현장 인수에서 새 오류를 발견하면 다음 **명령형 프롬프트 지침**을 적용한다.

> 당신은 ROS 2 Jazzy/Gazebo Harmonic과 AXIA 안전 교육 MVP 검증 책임자다. 
> **첫 실패**를 원본 증거 ZIP의 SHA256 확인 후 `stage_status.tsv`·`pytest.xml`·최초 traceback에서 찾고, 마지막 `HOLD` 메시지만으로 원인을 추정하지 마라.
> 안전 FSM/CM/Guard/Nav2/G00~G13의 계약은 건드리지 마라. 
> 원본 증거를 조작하거나 테스트를 무조건 PASS로 변경하지 마라.
> 해당 오류가 CI에서 재현 가능한 종류이면 **공개 CI에 먼저 RED 회귀**를 작성하여 실패 로그와 Run ID를 보존하라. 이후 가장 작은 변경으로 GREEN을 확인하고 REVIEW, 개발 보고서, Git COMMIT 순서를 지켜라.
> Instructor 답안·Hidden Test는 비공개 저장소에 유지한다. 공개 CI는 인가되지 않은 비공개 저장소를 checkout하지 않고, 합성·공개 시험 더블로 동일 실행기의 공유 검증 기능을 테스트한다.
> **CI와 Owner WSL2는 동일한 버전의 `axia_block_c_owner_final_once.sh`를 사용**한다. CI는 해당 파일의 `--ci-parity`로 정확히 같은 `check_manifests_and_source_parity`와 `run_step`을 호출하고, Owner는 `--run`으로 실제 WSL2 검증 범위를 수행한다. 모드 차이는 명시하고 CI PASS로 WSL2 PASS를 주장하지 않는다.
> 셸 `set -e`가 `if`/`||`로 호출된 함수에서 비활성화될 수 있음을 고려하여, 각 중대한 Python/CLI 명령 실패는 `|| return $?` 등으로 **명시적으로 전파**한다. Python traceback 이후 PASS가 출력되면 강제로 FAIL로 판정하라.
> 테스트는 개발자 `/mnt/data`, `/home/oai`, 임시 빌드 디렉터리의 절대경로를 참조하지 않는다. 원본 저장소 루트 또는 pytest `tmp_path`를 사용하고 공개 CI가 절대경로를 재현·차단하게 하라.
> Manifest 해시는 실제 바이트와 비교하고 데이터·소스·tests의 checksum 모두 검증한다. 코드 파일 변경 시 `RELEASE_MANIFEST.json`을 **같은 커밋에서** 갱신하고, 변경된 SHA와 원본 Git blob 및 검증 환경을 기록한다. 체크섬 경고를 억제하지 않는다.
> 처음 실패한 계층만 고치고, 수정 뒤 연관된 다른 단계의 경계를 검증하지 않았으면 전체 안정성을 미검증으로 표시한다. 안전 TTL(데이터 전달 주기 포함), ROS L1, Gazebo L2, Owner WSL2 L3를 구분한다. SW Stop을 인증 E-Stop으로 표기하지 마라.
> 보고서에는 경로, 실행 명령, RED/GREEN 로그, 수준, 미검증 항목, 정확한 브랜치/SHA, GitHub CI Run/Artifact를 기록한다. 기존 성공 원본 재실행을 최소화하고 새 오류를 현장에서 반복 재시도하지 마라.
> CI GREEN 후에만 GitHub의 **고정 SHA + SHA256 사전 검증** 방식으로 Owner 일괄 원샷을 제공하라. `main` 병합과 `release_approved=true`는 사용자의 별도 승인을 받아라.

## 실제 실패 원본(2026-11-16 Owner)
- `AXIA_BLOCK_C_OWNER_EVIDENCE.tar.gz` SHA256: `c2ecaaa96d4db1870277877db7b6749e8610587493e1c36148eb6cb9c744c360` — 사용자 업로드 원본.
- 첫 실패: `SHA256_MISMATCH_instructor:tests/test_ae.py`인데 `MANIFEST_SHA_AND_PARITY=PASS`로 기록 (Shell 명령 그룹 실패 누락).
- 후속: 강사 `pytest`에서 12 failed, 20 passed. 테스트의 `/mnt/data/axia_block_c_delivery/results/{c02,c03,c04}` 절대경로 때문에 `FileNotFoundError` 발생.
- 독립 검토: `tests/test_if.py`, `tests/test_ae.py`, `tests/test_diagnostics_adapter.py` 세 개의 **실제 저장소 버전**이 기존 Manifest SHA와 불일치. 초기에 작성된 Manifest SHA는 해당 테스트의 portable(상대경로) 구현과 일치하므로, 원본 테스트가 이전 authoring 경로 버전으로 들어간 구성 오류.
- 원본 판정 `HOLD` 유지. `INSTRUCTOR_PYTHON_L0` 이후 ROS·colcon·모델→DDS의 실제 Owner WSL2 합격 근거는 없음.

## 이번 최소 검증 게이트
1. 공개 CI: 동일 Owner 원샷 `--ci-parity`로 합성 공개 Instructor mirror + 고정 Student SHA 사용.
2. 정상 manifest → `MANIFEST_SHA_AND_PARITY=PASS`, 공개 CI여도 `owner_wsl2_verified=false`·`release_approved=false`.
3. 변조 checksum / 추적 파일 누락 / path traversal / 변경된 소스와 이전 hash / 개발 절대경로 → `MANIFEST_SHA_AND_PARITY=HOLD_RC_*`, `stage_status.tsv`에 PASS 없음.
4. 강사 비공개 테스트 3개는 repo root의 `reference_outputs` 상대경로만 사용하고 Release Manifest의 SHA를 확인.
5. 사전 검증 통과 후 Owner WSL2에서 단일 원샷으로 전체 모델/ROS 검수. 실제 ROS/Gazebo를 수행하지 않았다면 성공으로 보고하지 않는다.

## 제한
공개 GitHub Actions는 Instructor 비공개 정답과 Hidden Test를 checkout하지 않는다. 따라서 공개 CI의 checksum 모의 실험 PASS를 **강사용 Python 3.12 실제 통합 PASS나 Owner 현장 검수 PASS로 승격하지 않는다.** 현장 오류가 또 나오면 최초 실패를 공개 CI에서 재현 가능한 수준으로 줄여 새 RED 테스트부터 시작한다.
