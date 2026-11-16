# AXIA Block C — Owner WSL2 첫 현장 오류 R01 원인·RED/GREEN·CI/WSL2 실행기 일치 보고

**상태 (2026-11-16):** `R01_PUBLIC_CI_REGRESSION_GREEN / R01_OWNER_WSL2_RECHECK_NOT_RUN / RELEASE_HOLD`.

## 원본 증거와 첫 실패

- 사용자 업로드 `AXIA_BLOCK_C_OWNER_EVIDENCE.tar.gz` (SHA256 `c2ecaaa96d4db1870277877db7b6749e8610587493e1c36148eb6cb9c744c360`), `verdict.json`, `.sha256` 실제 확인.
- 최초 오류는 `MANIFEST_SHA_AND_PARITY` 내 Python의 `AssertionError: SHA256_MISMATCH_instructor:tests/test_ae.py`.
- **동일 단계가 PASS로 오판**된 이유: `run_step`에서 명령 실패를 `... || rc=$?`로 수집하므로 Bash의 `errexit`가 내부 함수에서 억제될 수 있고, 검증 Python 뒤에 `cmp` 성공 및 마지막 `echo`가 발생하면서 함수가 rc=0을 반환했다. 처음 실패를 기록하지 않은 것이 핵심 인수 경계 위반.
- 다음 `INSTRUCTOR_PYTHON_L0`: 실제 pytest `12 failed, 20 passed in 4.44s`, 파일 경로 `/mnt/data/axia_block_c_delivery/results/c02|c03|c04`를 참조하다 `FileNotFoundError`. 모델 탐지 성능 오류라고 증명된 것은 아님.
- 강사 소스 원본 `961b574e7623eede6ae94bf7b9cf06e62dc3674a`에서 `tests/test_if.py`, `tests/test_ae.py`, `tests/test_diagnostics_adapter.py`의 실질 파일 SHA256이 릴리스 Manifest와 모두 불일치. 원본 Manifest에 이미 기재된 SHA는 **상대경로 테스트 수정본과 정확히 일치**하므로 Manifest의 임계값을 완화하지 않고 소스 3개를 맞췄다.

## 최소 변경

- Instructor private `silverbjin/axia-robot-safety-instructor`, `plan/block-c-d09-d12-freeze-20261115`: 수정 커밋 **`eb91a334ab8ad826eb863afbb56a55f0b4991a53`**.
  - `training/block_C/tests/test_if.py`: `FEATURES=ROOT/'day09'/'reference_outputs'`.
  - `training/block_C/tests/test_ae.py`: 특징/IF 평가 경로를 강사 저장소 상대경로로 수정.
  - `training/block_C/tests/test_diagnostics_adapter.py`: AE 점수 경로를 강사 저장소 상대경로로 수정.
  - `training/block_C/release/RELEASE_MANIFEST.json`: 보유된 SHA256 정상값과 수정본의 **실제 바이트 해시가 일치**함을 확인. 해시 값 임의 변경이나 오류 무시는 하지 않음.
- Public CI `silverbjin/axia-robot-safety-ci-public`, `feat/block-c-owner-final-wsl2-20261116`:
  - `block_c/scripts/axia_block_c_owner_final_once.sh` **단일 실행 파일**로 `--run`(Owner WSL2 원본 검수)과 `--ci-parity`(공개 CI 합성 Instructor mirror) 제공. 핵심 `run_step`과 `check_manifests_and_source_parity` 함수는 양 모드에서 **동일 구현을 호출**.
  - Manifest Python의 실패 시 `|| return $?` 추가; C02→C05 모델·colcon·ROS 검증 명령의 실패 전파 명시. `tests/test_*.py`에 개발 전용 절대경로가 있으면 해시가 정상이어도 `BLOCK_C_AUTHORING_ABSOLUTE_PATH` 실패.
  - 정확한 Instructor 새 SHA `eb91a334...`로 원샷 고정; 공개 CI는 비공개 Instructor를 checkout하지 않는다.
  - `block_c/tests/test_owner_field_parity_public.py`: 정상 Manifest, 변조 SHA, 파일 변경, path traversal, 일치 SHA의 개발 절대경로, 추적 파일 누락 및 안전/핀 계약을 동일 실행기로 점검.
  - `.github/workflows/block-c-owner-field-parity.yml`: Ubuntu 24.04/Python3.12.16, 공개 Student 고정 `dff7b4a...`만 checkout하고 합성 교사 Mirror 생성.

## TDD와 CI 실행 원본

| 순서 | Run | 판정 | 검증 범위 |
|---|---|---|---|
| RED | [43780774408](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43780774408) | **failure, 8 failed** | 기존 원샷의 CI parity 미구현·실패 은폐 재현 |
| GREEN 1 | [43781043083](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43781043083) | **success, 8 passed** | `--ci-parity` + 동일 Manifest stage 함수 및 오류 경계 |
| GREEN 확정 | [43781182867](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43781182867) | **success, 8 passed** | 강사 핀 정합 후 동일 공개 CI 회귀 |
| 원샷 계약 | [43781182793](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43781182793) | **success, 10 passed** | syntax, no release, no private checkout, fail-closed |
| 기존 C01 회귀 | [43781182788](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43781182788) | **success** | 고정 학생 fixture checksum/10 public tests |
| Runner canary | [43781182790](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43781182790) | **success** | 공개 Runner 정상 |

다른 세부 수정은 RED→GREEN 수준에 필요한 부분으로 제한. 테스트 PASS는 실측 결과이며, **Owner WSL2 수정본 실행 결과는 없다**.

## 검증 수준 / 미검증

- PUBLIC CI parity GREEN: `SAME_PUBLIC_SCRIPT_MANIFEST_STAGE_CONFIRMED=true`.
- `OWNER_WSL2_VERIFIED=false`, `INSTRUCTOR_PYTHON312_NATIVE_RECHECK=false`, `GAZEBO_VERIFIED=false`, `PRODUCTION_SAFETY_TTL_VERIFIED=false`, `CERTIFIED_ESTOP=false`.
- 공개 CI는 강사 정답이나 Hidden Test를 시험할 수 없다. 수정된 강사 소스는 비공개 GitHub에서 원본 내용을 확인하고 테스트 상대경로·Manifest SHA를 대조했지만 실제 WSL2 실행은 **새 원샷을 통해 검증 필요**.
- 새 WSL2 오류 발생시 최초 위반을 증거로 수집하고 공개 CI에 재현 가능한 경계를 RED로 추가 후 GREEN. 동일 오류를 현장에서 반복 재시도하지 않음.
- 세 저장소 `main` 병합/정식 출고는 사용자 별도 승인 전 금지. 기존 `RELEASE_APPROVED=false` 유지.

## 재실행 및 전달

공개 CI의 `block_c/scripts/axia_block_c_owner_final_once.sh`를 **검증된 Git commit SHA에 고정해 SHA256 검증 후 `--run`** 한다. 성공 시 `BLOCK_C_OWNER_ACCEPTED=READY_FOR_OWNER_APPROVAL`만 도출하며 자동 승인하지 않는다. 실패 시 `BLOCK_C_STAGE_HOLD=<최초 실패>`/`BLOCK_C_OWNER_ACCEPTED=HOLD`와 증거 보존을 유지한다.

지침: `docs/AXIA_PUBLIC_CI_FIELD_ERROR_PARITY_STANDARD_20261116_KO.md`.

## 추가 회귀: 이동하는 Instructor 브랜치 (원격 별도 RED→GREEN)

- 교육 보고서 커밋 등으로 Instructor 또는 Student 개발 브랜치 HEAD가 이동해도 **불변 소스 SHA 검증을 유지**해야 한다. 공개 Owner 실행기는 두 저장소를 clone한 후 각각 지정된 정확한 `INSTRUCTOR_SHA`/`STUDENT_SHA`를 `git fetch --depth 1` 및 `git checkout --detach`로 복원한다. 실패하면 BLOCKED로 처리한다.
- RED 커밋 `f7c6102c83b6ae195159d8474d6cba4740360612`의 [Run 43781933456](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43781933456) failure → GREEN `600f240d2995fafed283e739e06a333d0b5e9ac3`.
- 해당 **코드 커밋** 공개 CI: [현장 회귀 Run 43782000245](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43782000245) `9 passed`; [원샷 계약 Run 43782000243](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43782000243) `10 passed`; [C01 Run 43782000236](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43782000236) success; [canary Run 43782000275](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43782000275) success.
- 고정된 배포 실행기: `block_c/scripts/axia_block_c_owner_final_once.sh` at **`600f240d2995fafed283e739e06a333d0b5e9ac3`**, raw SHA256 **`141b60f9736d7619ac4df8af302130ef85eeed00dadb0e049c8b9ef0cb0db8d5`**.
- 추가 읽기 전용 내용 감사: Instructor `eb91a334...`의 Manifest 49개 항목 중 UTF-8 소스/문서 등 **44/44** 실제 SHA256 일치; 이전 생성 원본 PPTX **4/4** SHA256 일치. AE checkpoint 바이너리는 본 별도 원격 읽기 감사에서 bytes를 확보하지 못해, 실제 Owner 원샷의 Manifest hash 검사로 최종 확인할 것.
- 이 CI 결과는 합성 공개 Instructor mirror 기반 **공유 실행기/Manifest 단계 parity**다. Private 정답 Python3.12/실제 Owner WSL2 및 ROS 단계는 미실행, **출고 판정 HOLD 그대로**.
