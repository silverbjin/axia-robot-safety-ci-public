# AXIA D06/G07 — TCljt2Qc 초기 실행 실패·증거 누락 근본 원인 및 최소 복구

기준: 2026-11-19. 현장 WSL2 NVIDIA **NO_GOAL** 신규 계측 파일. 실제 ROS2/Gazebo/CM/Guard 동작을 성공 판정하지 않으며, 원본 보존을 최우선으로 한다.

## 1. 사용자 원본의 사실 (추측 금지)

- 수신 파일: `d06-forensic-ab-no-goal-TCljt2Qc.tar.gz`, 크기 약 **1.3KB**, SHA256 `9e89dfe44e2d02e2315d16920b5318a7825bbe6799733eb887d3643f8c6296a2`. 수신 `.sha256` 사이드카와 일치.
- 실제 내부에는 `forensic/summary.json`, `first_stop_and_timing.txt`, `shutdown_context.txt`, `owner_verdict_excerpt.txt`, `renderer_excerpt.txt`, `source_hashes.txt` **6개 파일만** 존재함.
- `summary.json`의 `source=FUTURE_RUN_SAME_SESSION`, `sensor_status=UNMEASURED`, `first_sensor_failure=EVIDENCE_INCOMPLETE`, `goal_sent=UNVERIFIED`, `raw={}, safety={}`, `source_archive_sha256_verified=false`, `native_no_goal_navigation_ack=null`, `native_no_goal_cm_exit_code=null`. 이것은 센서 이상이나 정상 종료의 증거가 아님.
- `source_hashes.txt`는 원본 로컬 `nvidia.run.log`의 SHA256 **`9c6304511b5c148016e17c1949ac5811490856e0d3ea0da7413da47afe9312be`**를 기록. 하지만 파일의 텍스트와 최초 예외 메시지는 업로드 TAR에 없음. **직접적인 ROS/Gazebo 최초 실패 원인 미확정.**
- 원래 외부 실행기는 `nvidia.run.log`를 Owner 셸 실행 중 생성하므로, 그 해시가 있다는 것은 적어도 해당 실행 로그가 로컬에 존재했다는 점을 시사함. 로봇 시뮬레이터의 시작 여부, crash 및 TTL 상태는 그 로그가 없으므로 확인할 수 없음.
- 전체 인증 상태: NO_GOAL 진단 실패 계층 미확정, `AXIA_MVP_DEMO_ACCEPTED=HOLD`, `CERTIFIED_ESTOP=false`.

## 2. 명확히 확인된 코드 결함 (forensic 경계)

1. `d06/scripts/axia_d06_g07_wslg_gpu_rtf_compare_once.sh`의 종료 시 압축기 `collect_and_package`는 초기 실패가 나도 실행되지만, 원본 `nvidia.run.log` 내용은 **해시만 보존**하고 첫 오류 줄을 압축하지 않음. `owner_verdict_excerpt` 검색 정규식은 일부 후반 성공/종료 상태 메시지만 대상으로 하므로 초기 Python import / Git checkout / 환경 / ROS 오류를 보존하지 못함.
2. 기존 `--analyze-existing`는 `nvidia.g07_wslg_sensor_truth.json`이 **반드시 있는 폴더만 선택**하므로, 실제 센서가 시작하지 못한 TCljt2Qc 같은 폴더를 오프라인에서 재분석할 수 없는 모순이 있었음.
3. 새 진단기로 같은 파일을 다시 분석하면 이름이 같은 `d06-forensic-ab-no-goal-TCljt2Qc.tar.gz`를 **덮어써** 원본 custody를 훼손할 위험이 있었음.

이는 **진단/증거 수집 코드의 확정된 원인**이며, ROS/Gazebo 실제 실패 자체의 원인까지 규명한 것으로 오인하면 안 됨.

## 3. RED → GREEN → REFACTOR → REVIEW → COMMIT

- **RED**: [#44466701947](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44466701947), 원본처럼 센서 JSON 누락/Owner 로그 SHA만 존재하는 재현 fixture에서 초기 실패 텍스트를 보존하지 못하는 테스트 실패.
- 중간 재현 [#44466967948](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44466967948): 첫 오류 excerpt는 구현됐지만 **오프라인 selector가 센서 JSON을 요구하여** 실제로 복구하지 못함. 재현 후 최소 수정.
- **GREEN** [#44467131799](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44467131799), 초기 로그만 있는 경우를 오프라인 분석 대상에 포함, 최초 원본 오류 line/원래 Owner RC/실패 stage를 compact forensic에 추가.
- 별도 **원본 비파괴 회귀** 등록 [#44467498366](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44467498366): 원본 아카이브 덮어쓰기 위험 검증 후, 기존 파일이 있으면 `-recovered-XXXXXXXX.tar.gz` 신규 아카이브를 사용하도록 수정.
- 최종 **GREEN L0 87/87** [#44467550994](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44467550994), [public canary #44467550908](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44467550908). 신규 회귀는 원본 TAR 비파괴, 초기 로그만 있는 경우, 최초 오류 excerpt, 명시적 폴더 선택, 이름 경로 traversal 거부 등을 확인.
- 수정된 실행기 Git commit `956acc29be2ac07a274d06c94f89fedcc7cb8321`, Git blob `6cdf520938baad82d42063162ca78c8787e92a7a`; 분기 `fix/d06-wslg-lidar-vs-rtf-ci-20261118`.
- **REVIEW**: Safety 300/120/150ms, 공식 TB3/Nav2/CM, 런치 신호, 로봇 Goal/속도/센서 입력은 변경하지 않음. 로그의 민감한 API 토큰 일부 패턴은 redaction, excerpt 최대 17KB, 원본 로그는 사용자 WSL2에 남기고 작은 추출물만 업로드.

## 4. 강사 WSL2에서 원본 TCljt2Qc **오프라인만** 다시 분석

이 명령은 `--analyze-existing`만 호출한다. **Gazebo/ROS/Nav2를 시작하거나 Goal을 보내지 않고**, 기존 `$HOME/axia_d06_g07_gpu_rtf_evidence/ab-no-goal-TCljt2Qc/nvidia.run.log`를 검색하여 실패 원문을 포함한 **새 복구 TAR + SHA256**을 만든다. 처음 받은 TAR는 덮어쓰지 않는다.

```bash
(
  set -Eeuo pipefail
  SHA='956acc29be2ac07a274d06c94f89fedcc7cb8321'
  BLOB='6cdf520938baad82d42063162ca78c8787e92a7a'
  SCRIPT="$(mktemp --suffix=.sh)"
  trap 'rm -f "$SCRIPT"' EXIT
  curl -fLsS --retry 3 --max-time 90 \
    "https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public/$SHA/d06/scripts/axia_d06_g07_wslg_gpu_rtf_compare_once.sh" \
    -o "$SCRIPT"
  test "$(git hash-object "$SCRIPT")" = "$BLOB"
  bash -n "$SCRIPT"
  AXIA_D06_FORENSIC_TARGET='ab-no-goal-TCljt2Qc' \
    bash "$SCRIPT" --analyze-existing
)
```

새 출력 `D06_FORENSIC_ARCHIVE=...-recovered-XXXXXXXX.tar.gz` 및 `D06_FORENSIC_SHA256=...sha256` **두 파일만** 업로드하면 first_owner_failure_marker/first_failure_stage/원본 로그 앞뒤 최소 excerpt를 확인하여 실제 최초 오류를 분류할 수 있다. 원본 로그가 현장에서 삭제됐으면 삭제 사실을 명시하고 성공이나 특정 원인을 추측하지 않음.

## 5. 인수·다음 조치

- 이번 새 GREEN은 **L0 오프라인 진단/아카이브 계약**만 증명. WSL2 실 Gazebo/NVIDIA 재실행은 **NOT_RUN**.
- 기존 NO_GOAL 통합 Gazebo L2 2회 성공 [#44461092763](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44461092763), [#44461627846](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44461627846)의 성공 증거는 보존. 이번 TCljt2Qc가 그 성공을 무효화하거나 실 WSL2 인수로 승격시키지는 않음.
- 복구한 진짜 `first_owner_failure_marker`가 ROS import 오류/패키지 누락/WSLg 환경/네트워크 또는 원본 launch 오류 중 무엇인지 판명되는 경우에만, **해당 경계 한 건을 공개 CI RED→GREEN에 편입**하고 최소 수정한 뒤 다음 실제 Gazebo L2/현장 인수 단계로 진행.
- main 브랜치 병합은 사용자 승인이 있기 전까지 금지. `AXIA_MVP_DEMO_ACCEPTED=HOLD`, `CERTIFIED_ESTOP=false`.
