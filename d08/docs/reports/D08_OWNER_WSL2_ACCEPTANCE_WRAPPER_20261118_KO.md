# AXIA D08 — Owner WSL2/WSLg NO_GOAL 인수 원샷 (2026-11-18)

## 고정 증거와 릴리스 경계

- 공개 CI 소스 SHA: `342c6355b27af5b8b11a79b7e345820be18a581f`
- 실제 Gazebo L2 성공: [Run #44310101993](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44310101993), 4 jobs SUCCESS. AMCL discovery 실제 Scan/Odom/Clock callback 19/55/92개, 최대 host gap 0.137154/0.051925/0.034780초. 실제 TF, 공식 Nav2 원본 three-phase Path 및 no-Goal 검증.
- 기존 공식 Owner bootstrap: `d08/scripts/d08_owner_no_goal_bootstrap.sh`, Git blob `bad5b738e57827a102ebe56595d3b4b7dc3e6f83`.
- 기존 AMCL 파일 blob: `f44ffe3aa67bbbde03a28319d0db3587742b6f52`. 변경하지 않음.
- 이 릴리스 브랜치는 검증된 기존 런타임 SHA에서 출발하여 **WSL2 인수 래퍼·L0 테스트·이 문서·CI만 추가**. 현재 main 병합 금지.

## RED → GREEN → REFACTOR → REVIEW → COMMIT

1. RED: `d08/tests/test_d08_owner_wsl2_acceptance_wrapper.py`를 먼저 작성. 래퍼 없는 상태에서 로컬 `python3 -m unittest discover -s d08/tests -p test_d08_owner_wsl2_acceptance_wrapper.py -v` 결과 `FAILED (failures=2, errors=1)`, `D08_OWNER_WRAPPER_MISSING_RED`. RED 커밋 `3b827d91d8dc113d8bfaccde7b17d376421d33f4`.
2. GREEN: `d08/scripts/d08_owner_wsl2_acceptance_20261118.sh` 최소 추가. 로컬 재실행 `Ran 3 tests in 0.006s; OK`; `--self-check` 출력 `D08_OWNER_WRAPPER_L0_PASS_NO_ROS_GAZEBO_RUN`. GREEN 커밋 `7603eae4ef82f2a6dd291c04b25c4bfc4da1b212`.
3. REFACTOR/REVIEW: immutable public SHA/raw URL, `git hash-object` 고정 blob 검사, `bash -n`, `set -Eeuo pipefail`, 로그/상태 fail-closed, 3단계 `--self-check|--doctor|--run`. 원본 bootstrap의 누락된 공식 패키지 설치/YOLO 및 GPU D3D12 검사/소유 프로세스 정리/압축 증거만 재사용. 새로운 Goal/Velocity·TTLs·ROS/Nav2/CM/World/YOLO/Planner 로직 변경 없음.
4. 공개 CI: `.github/workflows/d08-owner-wsl2-acceptance-l0.yml`에서 bash 문법·고정 원본 bootstrap Git blob·Python unittest 3개·non-ROS self-check만 재검. **실제 공개 CI 실행 전/검증 전에는 GREEN 주장 금지**. 이전 source SHA의 실제 Gazebo L2 성공은 보존하며 릴리스 래퍼용 L0과 혼합하지 않음.

## 사용자 WSL2 사용

공개 CI가 PASS한 릴리스 브랜치 **정확한 커밋**에서 이 파일을 `curl -fL`로 다운로드하고, 래퍼 파일 Git blob 검증 후 `bash ... --run`을 실행한다. `--run`은 먼저 Doctor, 이어 기존 exact-source 공식 ROS/Gazebo/RViz2 및 pinned C++ YOLO를 실행한다. `sudo apt` 누락 공식 패키지 설치에는 sudo 암호가 요청될 수 있다.

- 러너는 `D08_OWNER_ACCEPTANCE_DIR`, `D08_OWNER_ACCEPTANCE_RUN_LOG`를 남기고 기존 bootstrap은 `D08_OWNER_COMPACT_EVIDENCE` 경량 ZIP과 SHA256을 만든다.
- `D08_OWNER_RUNTIME=PASS_CANDIDATE_NO_GOAL_ONLY`도 자동 시각 L3 PASS가 아니다. Gazebo 실제 사람형 Proxy/로봇 화면, RViz 공식 3 Path, TF/Scan/Odom/Clock 지속성, Ctrl+C 소유 정리 상태는 사용자 WSLg에서 직접 확인해야 한다.
- `D08_OWNER_WSLG_VISUAL=OWNER_CONFIRM_REQUIRED`, `D08_MOVING_E2E_ACCEPTED=HOLD`, CM 내부 RMW gap·Guard 120/150ms `NOT_VERIFIED`, SW stop ≠ certified E-Stop.
- 현장 실패 시 재시도 반복하지 않는다. 첫 Scan/Odom/Clock/TF 수신/시간 위반 및 최초 상태 전이와 경량 ZIP을 CI 회귀에 먼저 편입한다.

## 검증 수준

- L0: 로컬 3 PASS, 공개 CI GREEN 실행 결과 별도 추적.
- L1: 변경 없음, pinned 기존 근거만 인정.
- L2: 기존 정확한 342c... SHA에 대해서만 실제 Gazebo PASS (#44310101993). 래퍼 추가 커밋에서 Gazebo 새 실행 없음.
- L3: Owner WSL2/WSLg NOT_RUN.
- Git: 공개 브랜치 `release/d08-wsl2-owner-acceptance-20261118`, main 병합 없음.

## 추가 회귀 — PR synthetic merge checkout 경계

- 첫 경량 공개 CI [#44324664874](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44324664874) 성공, `Ran 3 tests in 0.005s; OK`, `D08_OWNER_WRAPPER_PUBLIC_CI_L0_PASS_NO_ROS_GAZEBO_NOT_L3`. 그러나 checkout 실제 SHA `830a1343b50eea913d638ecb335f69a82d4a24b8`은 PR synthetic merge로서 릴리스 HEAD `182c462c1cd67b20488b3de7c0869ea1d9d49101`와 다름.
- 단일 RED 가설: Actions checkout이 PR merge commit을 기본 사용. 새 L0 회귀는 `ref: ${{ github.event.pull_request.head.sha || github.sha }}`가 없으면 FAIL하도록 추가. 로컬 RED `Ran 4 tests; FAILED (failures=1)`; GREEN 동일 소스에서 `Ran 4 tests; OK`.
- 최소 수정: 기존 Owner 런타임·AMCL 파일/모든 TTL 불변, wrapper workflow checkout만 정확한 PR HEAD로 핀하고 `AXIA_D08_RELEASE_EXPECTED_SHA` 비교. 새 공개 CI 결과와 릴리스 최종 SHA는 PR #178의 run에 기록. main 병합하지 않음.
