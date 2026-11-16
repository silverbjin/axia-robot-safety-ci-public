# AXIA G07 Cycle 20 — Owner WSL2 단일 진단 압축파일 및 CI/WSL2 실행기 동일화

작성일: 2026-11-16. **상태: 공개 CI L0 PASS; 실제 WSL2/Owner 추가 주행 NOT_RUN; 안전 원인 및 런타임 수정 미검증. `AXIA_MVP_DEMO_ACCEPTED=HOLD`**.

## 1. 사용자 첨부 결과와 최초 실패

기준 입력: `g07-first-cm-gap-yrPisAnp.json`, schema `axia.g07.owner_first_cm_rpc_attribution_v1`, 원본 같은 private Instructor SHA `01d45d46b6eb6a05b1bd313d73f1fc3549575545`.

- 최초 Guard 내부 CM age `174.184617ms` > hard 150ms → `UPSTREAM_STALE_AFTER_MOTION` (안전한 latch, **시연 인수 실패**).
- 첫 CM RMW source 간격 `186.714207ms`, receive 간격 `189.45695ms`, Observer callback 간격 `227.710904ms`.
- 해당 발행 공백에서 Supervisor 독립 메시지 `4회`, coverage gap 최대 `64.89631ms`.
- Native STOP RPC 자체 `107.021916ms`였지만 최초 CM gap과 **중첩하지 않음(`false`)**. 그러므로 STOP RPC가 *최초* TTL 위반을 만들었다는 시간 인과 가설을 해당 원본에서 기각.
- `cm_scheduler_native_stop_window_attribution=CM_SCHEDULER_VS_EXECUTION_UNDETERMINED`. 이 `/proc` 계측은 STOP RPC 구간에 대한 것이며 FIRST CM gap과 불일치하므로 CM 내부 CPU 스케줄링 직접 원인이라고 단정 불가.
- `host_clock_step_excluded=false` = 시계 영역 불연속 **배제 입증 불가**. RMW host system clock과 callback/STOP RPC monotonic은 서로 절대 비교 금지.
- 결과: **CM 자체 수신·콜백·TF 해석·CPU 스케줄러·RMW 발행 경계의 추가 시점 분리 필요**. 새 ROS/Goal은 실행하지 말 것.

## 2. RED→GREEN→REFACTOR→REVIEW→COMMIT

공개 브랜치: `fix/g07-cycle20-single-evidence-bundle-20261116`. 강사 정답/private raw 공개 금지, 학생 TODO 독립 유지, `main` 사용자 승인 전 미병합.

- RED [Run 43786898136](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43786898136): 통합 생성기 미구현 `ModuleNotFoundError: d06.live.g07_cycle20_single_bundle`.
- GREEN source `d06/live/g07_cycle20_single_bundle.py`: 기존 Cycle19 SHA256 검증된 Original archive와 source.sha를 검증하고 **읽기 전용**, 목표 전후 8채널 이벤트(종류당 16개 이하)의 callback 상대시간, RMW source/receive 상대시간, publication sequence 상대 번호, 150ms Guard 최초 전이, Supervisor 4회, Native STOP RPC 시간 관계, CM scheduler/스레드 **숫자 집계만** 생성. 현 WSL2 CPU/OS 제한 스냅샷은 `CURRENT_NOT_HISTORIC`으로 구분. ID/Goal UUID/비공개 개인 path/원본 bag/메시지 payload는 출력하지 않음.
- 출력물은 **단 한 개** `g07-cycle20-owner-evidence-*.tar.gz`이며 6개 내부 파일로 제한: `00_manifest.json`, `01_first_boundary.json`, `02_event_window.json`, `03_cm_scheduler.json`, `04_environment.json`, `SHA256SUMS`. 모든 멤버 SHA256 검증 및 내부 파일 200KB 이내/regular file 강제, 0600 퍼미션.
- WSL2 소스 `scripts/axia_g07_cycle20_owner_single_bundle_once.sh`: 배포된 Public exact commit SHA `6fe251c833f95f5484b79aa0f4c98bf9d6b76d7b` 및 tree `f6adcd1141b29f8c94f980a18f5d1e04cbe67c2a`로 원본 생성기를 체크아웃한다. 사용자의 최근 실행에서 성공한 기존 원본 TAR 또는 G11 SHA256 객체만 허용; 무주행·무관리자·no Goal·no original deletion·no field lock reset.
- `d06/tests/test_g07_cycle20_single_evidence_bundle.py`: 합성 Guard174ms/CM source186ms/Supervisor4/RPC 비중첩, 무결성 SHA256, 8채널 상한, 보안 ID/원본 경로 누출 금지, 시계 상태 불확정, 손상 archive/unsafe symlink fail-closed 등 **8개**.
- 초기 CI 테스트 checksum 방향·fixture 기대변수 오류 `43787287584`, `43787376210`, `43787458810`를 수정(실제 ROS/runtime 오류 아님).
- 최종 공개 CI [Run 43787811294](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43787811294) `success`. 실제 출력:
  ```text
  Ran 8 tests in 0.029s
  Ran 9 tests in 0.050s
  AXIA_G07_CYCLE20_SINGLE_BUNDLE_CI_L0_PASS_NO_ROS_NO_GOAL
  AXIA_G07_CYCLE20_SINGLE_BUNDLE_SELF_CHECK_PASS_NO_ROS_NO_GOAL
  AXIA_G07_CYCLE20_EXACT_PINNED_OWNER_SCRIPT_CI_PASS_NO_ROS_NO_GOAL
  ```
  Ubuntu24 러너에서 실제 배포용 **동일 WSL2 entrypoint**를 `--self-check` 및 **원본 없는 HOME**으로 실행, fail-closed / no ROS/Goal·원본/시도 잠금 생성 없음, immutable Python과 현 CI 후보 파일 byte-identical 검증.
- 기존 Cycle19 분석 L0 9개 PASS 재사용. 단일 package의 실제 Owner 내용 자체는 사용자 WSL2에서만 생성 가능하므로 그 부분 `NOT_RUN`.

## 3. 사용자 WSL2 단 한 번 실행

WSL2 Ubuntu 24.04에서 다음 블록을 **그대로 한 번만** 실행한다. 개인 원본·14topic rosbag·Instructor source를 별도로 전달하지 않는다. `SHA=06584bd510fed0efeac1943e843cc3a5d2696914`는 검사 완료된 원샷 Script의 고정 commit이다.

```bash
(
  set -Eeuo pipefail
  SHA="06584bd510fed0efeac1943e843cc3a5d2696914"
  SCRIPT="$(mktemp)"
  trap 'rm -f -- "$SCRIPT"' EXIT
  curl -fL --retry 3 -sS \
    "https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public/${SHA}/scripts/axia_g07_cycle20_owner_single_bundle_once.sh" \
    -o "$SCRIPT"
  bash -n "$SCRIPT"
  bash "$SCRIPT"
)
```

예상 마지막 출력:
```text
AXIA_G07_CYCLE20_ORIGINAL_SHA256_VERIFIED_NO_ROS_NO_GOAL
AXIA_G07_CYCLE20_PUBLIC_SOURCE_SHA_TREE_VERIFIED_NO_ROS_NO_GOAL
AXIA_G07_CYCLE20_ONE_SANITIZED_BUNDLE_SHA256=<64hex>
AXIA_G07_CYCLE20_UPLOAD_ONLY_THIS_ARCHIVE=/home/.../.axia_g07_owner_single_evidence_bundles/g07-cycle20-owner-evidence-*.tar.gz
AXIA_G07_CYCLE20_READONLY_NO_ROS_NO_GOAL_NO_RAW_ORIGINAL
AXIA_MVP_DEMO_ACCEPTED=HOLD
```

**`UPLOAD_ONLY_THIS_ARCHIVE=` 경로의 파일 하나만** 사용자에게 첨부 요청. TAR 내부 전체 6개는 압축파일 안에 자동 포함돼 추가 명령 불필요.

## 4. 새 evidence 후 즉시 이어갈 판단

1. 최초 Guard latch와 150ms/186ms source gap이 일치하는지; 8채널 first-gap 주변 상대시간, RMW source vs received vs callback의 추가 지연 2.74ms / 41ms를 구분.
2. RPC 최초 gap 중첩 false이므로 재차 STOP RPC 타이밍 변경 금지. 그 전 구간의 입력-처리-출력(공식 CollisionMonitor subscriptions/TF lookup/executor/DDS)의 최소 원인 후보를 단일 CI 재현 경계로 전환.
3. `03_cm_scheduler.json`은 Native RPC 구간이며 **FIRST CM gap 스케줄링 증명 불가**. 현 Host snapshot도 과거 CPU 상태 증거가 아님. 파일 안에 과거 first-gap scheduler 기록이 없다면 해당 경계는 원본으로 재구성 불가라고 명시.
4. 새로운 원인 가설이 과학적으로 재현 가능할 때만 최소 수정, RED→GREEN→REFACTOR→REVIEW→COMMIT, 실제 Gazebo Harmonic/Nav2 CI L2 (CM<120ms target, Guard TTL150ms, Scan/Odom/Clock TTL, exact Goal Cancel/Shutdown, S02 contact0) 검증 후 WSL2 1회 Owner 재인수.
5. CI L0는 통합 package의 생성 계약만 PASS. **실제 WSL2 source/TF/scheduler 문제 해결 성공으로 보고 금지**.

`AXIA_MVP_DEMO_ACCEPTED=HOLD` / `OWNER_L3_NOT_RUN` / certified physical E-Stop 아님.
