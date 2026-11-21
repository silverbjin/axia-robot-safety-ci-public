# AXIA D06/G07 — TCljt2Qc 소스 고정값 불일치: 증거 기반 RCA 및 최소 수정

- 작성: 2026-11-19 / 단계: RED → GREEN → REFACTOR → REVIEW → COMMIT
- 공개 CI: `silverbjin/axia-robot-safety-ci-public` / `fix/d06-wslg-lidar-vs-rtf-ci-20261118` / Draft PR #177
- 강사 WSL2: Ubuntu 24.04 + ROS 2 Jazzy + Gazebo Harmonic + NVIDIA WSLg
- 학생 코드: `silverbjin/axia-robot-safety-student` **변경 없음**, immutable commit `8e19742fd7bd80db73a37dc7b1d798768dc33e2a` (학생 Draft PR #62)
- 인수: 원본 NO_GOAL 시뮬레이션 자체 **NOT_RUN**. Moving L3 **HOLD**. Safety SW Stop ≠ 인증 E-Stop.

## 1. 강사 원본의 최초 실패

강사에서 기존 NO_GOAL Nvidia 실행 후 제출한 1.3KB 초기 TAR는 `EVIDENCE_INCOMPLETE`만 포함. 오프라인 보존/복구 기능을 보강한 뒤 받은 원본:
- `d06-forensic-ab-no-goal-TCljt2Qc-recovered-ZyNCQrxV.tar.gz`
- 사용자 제공 SHA256 사이드카와 일치: `328fca1b36febcd23a4cffc241f606581a50b8536781b6e940fb11ba774f2574`
- `forensic/summary.json`: `first_owner_failure_marker=D06_WSLG_FROZEN_SOURCE_BLOB_MISMATCH_NO_GOAL`, `sensor_status=UNMEASURED`, `goal_sent=UNVERIFIED`, `source_archive_sha256_verified=false`, CM/Gazebo 종료 정보 없음.
- `forensic/first_preflight_or_owner_failure.txt`: 정확히 1행 `D06_WSLG_FROZEN_SOURCE_BLOB_MISMATCH_NO_GOAL`.
- `first_failure_stage=UNKNOWN_ORIGINAL_STAGE`: 구 버전 실행기에는 단계 기록 없음. 로그와 소스 비교 결과 실행기는 학생 소스 checkout의 blob 검증 위치에서 exit3. **Scan300 지연이나 Gazebo crash가 재발했다는 근거는 없음**.
- `forensic/source_hashes.txt`: 현장 원본 `nvidia.run.log` SHA256 `9c6304511b5c148016e17c1949ac5811490856e0d3ea0da7413da47afe9312be`. 원본 로그 전체는 증거 TAR에 실리지 않음.

## 2. 고정 커밋의 실제 Git blob 대조

강사 내부 Owner 실행기:
`d06/scripts/axia_d06_g07_wslg_sensor_no_goal_once.sh`

고정 학생 SHA:
`8e19742fd7bd80db73a37dc7b1d798768dc33e2a`

| 학생 파일 (상대 경로: `block_B/day07/h01_runtime/`) | 기존 Owner 기대 blob | 실제 GitHub 동일 SHA 파일 blob | 판정 |
|---|---|---|---|
| `tools/g07_wslg_no_goal_sensor_probe.py` | `f7534b191b78cba4f20aac55e9d227268504a25f` | `cb38a2b288b9bf9db80def7b1fe37d975db2cdfa` | **MISMATCH** |
| `scripts/p2_no_goal_smoke_ci.sh` | `9cb5baf6c766a79cf6fd5134707981e32bb23e85` | 동일 | PASS |
| `ros2_ws/src/axia_safety_bringup/launch/axia_tb3_p2.launch.py` | `b2886cdf509d99ea62528cd013669258764b05e0` | 동일 | PASS |

**확정 원인:** 강사 배포 실행기의 Probe blob 고정값만 해당 immutable 학생 commit의 파일과 불일치. 내부 검증이 fail closed로 작동하여 ROS/Gazebo 시작 전에 종료됨. 학생 파일이나 저장소 자체의 손상이라는 증거는 없음.

## 3. 실제 개발 및 공개 CI

### RED
- `d06/tests/test_d06_gpu_rtf_runner_safety.py::test_tcljt2qc_student_source_probe_hash_matches_actual_checkout`를 추가.
- 공개 CI는 지정된 학생 SHA를 실제 checkout한 뒤 `git hash-object`로 세 파일을 순회하여 강사 스크립트의 `readonly *_BLOB`와 비교.
- [Run #44468895569](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44468895569): **예상한 실패** 한 건:
```text
AssertionError: 'f7534b191b78cba4f20aac55e9d227268504a25f'
              != 'cb38a2b288b9bf9db80def7b1fe37d975db2cdfa'
D06_TCLJT2QC_PIN_DRIFT_PROBE_BLOB tools/g07_wslg_no_goal_sensor_probe.py
```

### GREEN / 최소 수정
1. 내부 Owner `d06/scripts/axia_d06_g07_wslg_sensor_no_goal_once.sh`의 `readonly PROBE_BLOB` 한 줄을 실제 `cb38a2...`로 변경. 기타 기능 변경 없음.
   - 커밋: `6f23e8258582958fa37aef9a5f7bca0eb572586c`
   - Git blob: `28788ea5bf4076286f02637905e5f7b9f66dddd7`
2. 외부 원샷 `d06/scripts/axia_d06_g07_wslg_gpu_rtf_compare_once.sh`의 **OWNER_SHA + OWNER_BLOB**만 최신 immutable 값으로 변경.
   - 커밋: `840be130a26919ac356a0516e96f2328759264b0`
   - Git blob: `0f512841b86a9bc3911f38dc61bf325d55a2a4b2`
3. 기존 핀 계약 테스트를 최신 blob로 갱신하고 위 실제 파일 해시 회귀를 유지.
   - 커밋: `16665f4943660eb7b4a5e630d4175c1b455f0dde`
4. [Run #44469125853](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44469125853): **L0 88/88 PASS**, 공개 runner canary [#44469126005](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44469126005) PASS.

### REFACTOR / REVIEW
- 고정 학생 SHA 변경 없음, Probe의 실제 측정·Safety 300ms 로직 변경 없음.
- 같은 센서/월드/공식 Nav2/Gazebo 코드를 쓰는 기존 공개 NO_GOAL 실제 Gazebo L2 통합 PASS [#44461092763](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44461092763) 및 [#44461627846](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44461627846)는 그대로 보존.
- 이번 고정값 복구 자체는 **L0**에서 검증했고, 실제 NVIDIA WSLg에서 최초 기능 실행은 아직 미검증. 앞선 필드 실패를 본 수정으로 해결했다고 보고할 수 있는 범위는 checkout hash 비교까지임.

## 4. 강사 WSL2 다음 확인 (1회; 자동 증거 보존)

공개 CI가 최종 HEAD에서 GREEN일 때만 다음과 같이 임시 파일을 다운로드, Git blob SHA 검증 후 `--nvidia-causal` 한 번 실행한다.

```bash
(
  set -Eeuo pipefail
  SHA="840be130a26919ac356a0516e96f2328759264b0"
  BLOB="0f512841b86a9bc3911f38dc61bf325d55a2a4b2"
  SCRIPT="$(mktemp --suffix=.sh)"
  trap 'rm -f "$SCRIPT"' EXIT
  curl -fLsS --retry 3 --max-time 90 \
    "https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public/$SHA/d06/scripts/axia_d06_g07_wslg_gpu_rtf_compare_once.sh" \
    -o "$SCRIPT"
  test "$(git hash-object "$SCRIPT")" = "$BLOB"
  bash -n "$SCRIPT"
  bash "$SCRIPT" --self-check
  bash "$SCRIPT" --nvidia-causal
)
```

실제 L3에서 원본이 또 실패하면 `D06_FORENSIC_ARCHIVE`와 `D06_FORENSIC_SHA256` 두 파일만 전달. 다시 실행하여 성공을 추정하지 말고 **처음 실패한 안전 전이·데이터 전달 주기·종료 프로세스**를 확인하고 CI 회귀 RED→GREEN으로 재현할 것.

## 5. 인수 상태

- **소스 고정 검증 실패 원인:** 확정/수정, 공개 CI 88/88 PASS.
- **ROS2/Gazebo 실제 WSL2 재시도:** NOT_RUN.
- **NO_GOAL Scan300ms + 종료 계층:** 기존 공개 Gazebo L2 x2 보존, 이번 필드에서는 미검증.
- **Moving Goal, Collision Monitor120ms, Guard150ms 실제 노드 간 TTL, Stop/Cancel:** 이번 범위 미검증 → 전체 MVP 인수 HOLD.
- `D06_GAZEBO_LIVE_RELEASE=HOLD`, `AXIA_MVP_DEMO_ACCEPTED=HOLD`, `CERTIFIED_ESTOP=false`, main 브랜치 병합 금지.
