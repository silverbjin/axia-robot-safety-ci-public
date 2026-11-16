# AXIA G07 Cycle 19 — 최초 CM source gap와 Native STOP RPC 중첩 원본 분석기

- 작성일: 2026-11-16 / 공개 CI 우선 / NO-ROS·NO-Goal 기존 Owner evidence 읽기 전용
- **판정:** 최초 실측 현장 Guard CM TTL 위반은 실재하며 **원인 해결 미검증**. 현장 Goal/새 Gazebo CI L2 없이 아카이브 원본 판별 도구 작성. `AXIA_MVP_DEMO_ACCEPTED=HOLD`.
- Branch `fix/g07-field-first-cm-gap-attribution-20261116`, `main` 미병합.
- 기준 실제 CI Gazebo L2 `43727149856`: Xvfb CM observer max `110.964002ms` PASS, Owner WSLg 대체 불가.
- 기준 과거 Owner L3 실패: private SHA `01d45d46b6eb6a05b1bd313d73f1fc3549575545`, archive `p2-l3-owner-A9IwJNZJ.tar.gz`, SHA256 `c2557e3269c5cb3f56d1842f8d39bcdc5d6ab0055180911fc492a5bc84a1f672`. 최초 `UPSTREAM_STALE_AFTER_MOTION`, Guard CM age `174.184617ms > 150ms`, CM RMW source `186.714207ms`, receive `189.45695ms`, Observer max `227.710904ms`, 같은 gap 안 Supervisor 4개 (최대 coverage `64.89631ms`).
- 기준 공개 field L0: Run `43783606253` 12/12 PASS, 실제 Goal 재시도 거부. 이전 실패된 원본·단일 시도 잠금 **보존**.

## 1. 원인 경계

현재 원본 G11 비식별 후기 자료로 확인되는 것은 **CM 발행 공백이 Subscriber의 지연보다 앞선다는 점** 및 **Supervisor 발행 자체는 해당 gap 중 계속됐다는 점**까지다. 그러나 관측자가 확인한 CM source gap의 정확한 monotonic 구간이 Gazebo Native STOP RPC 100~120ms 구간과 겹쳤는지, 기존 `/proc` bounded CM scheduler 계측이 있었는지 등은 **원본 ci_moving_goal_result.json + actual_ros_events.jsonl** 확인 없이는 확정 불가. CM 내부 CPU scheduling/TF/callback 원인이라고 단정하지 않는다.

## 2. RED→GREEN→REFACTOR→REVIEW→COMMIT

- `d06/live/g07_cycle19_first_cm_archive_readonly.py`: 기존 보관 원본 TAR의 SHA256과 private source SHA 검증, archive member read-only/no-extraction, RMW source·receive·observer **동일 종류 시계** 내 구간 계산, Supervisor 4개 발행·Guard 내부 최초 TTL 및 **monotonic** Native STOP RPC 중첩 여부만 비식별 JSON으로 출력.
- `d06/tests/test_g07_cycle19_first_cm_archive_readonly.py`: 합성 RMW first gap·Guard174.185ms·Supervisor4·가짜 STOP RPC 중첩; 빠진 RPC는 불명확 처리; CLOCK/sequence 비연속, 잘못된 archive SHA/멤버, goal 미증거 fail-closed; raw UUID/개인 원본 출력 금지.
- `scripts/axia_g07_cycle19_owner_existing_raw_readonly_once.sh`: **기존 SHA=c255...** TAR 또는 이전 G11 보관 SHA256 객체만 허용; 다운로드는 immutable public SHA `3b9ff7cb06805b297a204d7bd8ebe22d4d025508`에서만, 명령어는 `python3`/Tar 읽기뿐, ROS/Gazebo/Goal/아카이브 수정·외부 raw upload **없음**. 결과는 0600권한의 `~/.axia_g07_first_gap_readonly/g07-first-cm-gap-*.json`.
- CI `.github/workflows/axia-g07-cycle19-first-cm-owner-original-l0.yml`: Ubuntu 24.04 공개 러너, 합성 min event·field prior lock 12개 기존 회귀 및 실제 Owner 진단 entrypoint의 no-original fail-closed, `bash -n`; **실제 과거 원본 archive는 공개 CI에 반입하지 않음**.
- 최초 workflow RED: Run `43785168167` YAML 인용 오류로 jobs=0, 정확한 step label colon quote 수정. 이어 합성 L0 GREEN Run `43785250757` 8/8 + field12/12 PASS.
- 추가 검증된 G11 custody object fallback **RED** Run `43785334042`: 원본 tar basename은 없고 `objects/c2/<SHA256>`만 존재할 때 코드가 `ORIGINAL_ARCHIVE_HASH_OR_NAME_MISMATCH`로 실패. **GREEN** Run `43785402398`: 9/9 archive unit + 12/12 field unit PASS, 기존 원본 복사/추출 불필요.
- Owner 직결 로컬 entrypoint CI 검증: Run `43785542789`, 9+12 및 bootstrap `--self-check` PASS. 초기 원본 부재시 ROS/Goal 없이 HOLD하도록 추가 CI `43785684380` 실행. 결과는 Actions 상태를 별도 참조.
- 공개 branch는 아직 WSL2 Owner 원본을 받은 것이 아니므로 **실제 first STOP overlap 결과 없음**. No claim of timing fix, no CI L2 rerun without scoped safety change.

## 3. 사용자 WSL2에서 필요한 **최소 1회 읽기 전용 증거 수집**

- Ubuntu 24.04 변경 필요 없음. ROS 설치·Gazebo GUI·Goal 실행하지 않음.
- 아래 공개 script URL을 하나의 Bash 블록으로 실행. `SHA=879c7a6c3656c36a656f3bdfd5e65dfdba7030a2` 고정.
- 성공시 출력 `AXIA_G07_CYCLE19_OWNER_UPLOAD_ONLY_THIS_SANITIZED_JSON=/home/.../.json`. 그 JSON **하나만** 전달한다. TAR·rosbag·비공개 Instructor 코드 공개 업로드하지 않는다.
- 원본 없음/검증 실패시 `AXIA_G07_CYCLE19_ORIGINAL_OWNER_ARCHIVE_NOT_PRESENT_NO_ROS_NO_GOAL` 또는 SHA 오류와 `AXIA_MVP_DEMO_ACCEPTED=HOLD`; 무리한 재주행 금지.

```bash
(
  set -Eeuo pipefail
  SHA="879c7a6c3656c36a656f3bdfd5e65dfdba7030a2"
  SCRIPT="$(mktemp)"
  trap 'rm -f -- "$SCRIPT"' EXIT
  curl -fL --retry 3 -sS \
    "https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public/${SHA}/scripts/axia_g07_cycle19_owner_existing_raw_readonly_once.sh" \
    -o "$SCRIPT"
  bash -n "$SCRIPT"
  bash "$SCRIPT"
)
```

## 4. 재개 지점

기존 실패 자료의 반환값에서:
- `native_stop_rpc_overlaps_first_cm_gap_candidate=true`: 시간 중첩 후보, 인과 입증 아님. Native STOP blocking의 CM thread 실행 영향만 좁혀 **같은 CI/Owner runtime**에서 최소 재현.
- `false`: 최초 CM 공백은 RPC 밖. TF/CM executor/DDS/scheduler 첫 gap 계측을 Goal safety policy 변경 없이 추가.
- `null`: 원본에 STOP RPC monotonic 증거 없음. 부족한 증거 상태로 운용 변경 불가. 읽기 전용 기존 live JSON path 확인.
- `cm_scheduler_native_stop_window_available=false`: 소급해서 OS scheduler 원인 추측 불가.

새로운 가설 코드가 있으면 RED→GREEN→REFACTOR→REVIEW→COMMIT, 이후 **공개 CI 실제 Harmonic·Nav2 L2**에서 CM 120ms release, Guard 150ms hard, upstream/Safety scan·odom·clock 300ms 등 모든 TTL, S02 Contact0, exact Goal Cancel·Shutdown verify. 그 후에만 새로운 Instructor SHA로 WSL2 1회 Owner Goal을 검토한다. 학생 강사용/공개 분리, `main` 병합 사용자 승인 전 금지. Software stop != certified physical E-Stop.

**최종: `AXIA_MVP_DEMO_ACCEPTED=HOLD`; `OWNER_GOAL_RELEASE=BLOCKED`; 사용자에게 요구되는 작업은 기존 아카이브 무주행 1회 읽기뿐.**
