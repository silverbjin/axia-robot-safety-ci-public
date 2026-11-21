# AXIA D06 C25 — 강사 WSL2 읽기 전용 코어 진단 2건 중복 증거 분석 및 최신 C24 인수 경계

작성: 2026-11-21 KST · 공개 PR #177 · WSL2 Ubuntu 24.04 + WSLg D3D12 NVIDIA RTX2060 Max-Q · **main 미병합**

## 1. 입력 및 SHA256 무결성 (실제 원본 TAR 확인)

| 업로드 | TAR 크기 | TAR SHA256 및 함께 제출한 검증값 |
|---|---:|---|
| `readonly-nxj6poaa.tar.gz` | 822 bytes | `c1d52453ab9865cdcad1b0159f3fabc0a82714aa543247f4ddda189f4c77e049` — MATCH |
| `readonly-gnwhry3r.tar.gz` | 820 bytes | `71a425da442ef2859c0f187a1129dfc13d16bd5bd823b4a797af217631ab9592` — MATCH |

두 TAR의 압축 용량 및 SHA는 다르지만 **내부 3개 파일 이름·용량·바이트 내용이 완전히 동일**:
- `summary.txt`: 165 B, SHA256 `9b4bb36a06a1bc1f0205dac8058278dc3aece697b932ab4f3c4e16257bed35b1`
- `preflight.txt`: 308 B, SHA256 `4ebc0438b8e72ab61a073e18cec1f4c8baf5c315ce2f3e3edb38ae909237f4fb`
- `observation.json`: 403 B, SHA256 `ece1f2ef7975bfd9f0a06795c35f7a288824bc2d95a8d43bb35f4f99d6a99301`

## 2. 두 원본의 실제 관찰 경계

```text
D06_C23_NO_PID_RECORD_CURRENT_BOOT_HOLD_ROOT_CAUSE_UNKNOWN
D06_C23_NO_NEW_SIGSEGV_NO_GAZEBO
core_not_archived=true
AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false
kernel_core_pattern=|/usr/lib/systemd/systemd-coredump %P %u %g %s %t 9223372036854775808 %h %d
boot_id=3f362cbb-3d40-468e-9f77-01a5243b3fa6
systemd_socket_load=loaded
systemd_socket_active=True
storage_config=DEFAULT_OR_UNAVAILABLE
PID=1424 current boot query only; no evidence this is the same crash event
```

동일 `observation.json`:
```json
{
  "scope": "current_boot_read_only_pid_1424_not_verified_same_event",
  "pid": 1424,
  "socket_active": true,
  "journal_access": true,
  "journal_exact_pid_rows": 0,
  "journal_exact_segv_bash_rows": 0,
  "coredumpctl_exact_info": false,
  "verdict": "D06_C23_NO_PID_RECORD_CURRENT_BOOT_HOLD_ROOT_CAUSE_UNKNOWN",
  "core_not_archived": true,
  "gazebo_not_run": true,
  "root_cause": "UNCONFIRMED"
}
```

**실증할 수 있는 범위:** 두 조회가 동일한 WSL2 Boot ID에서 수행되었고, 조회 시 `systemd-coredump.socket`은 활성, journal은 읽을 수 있으나 PID1424의 현재 부트 기록이 0개였다. 새 SIGSEGV/Gazebo는 시작하지 않았다.

**실증하지 못한 범위:** 과거 C22 합성 Bash SIGSEGV 사건과 이 부트가 같았는지(기존 C22에는 boot_id 없음), 당시 socket이 활성인지, journald/외부 저장 정책, 과거 Gazebo server PID19280 exit-11의 호출 스택, Nvidia/OGRE2/D3D12/RMW 귀책.

두 번 같은 출력이 나왔다고 **독립 반복된 코어 저장 장애 2회**로 분류하면 안 된다. `storage_config=DEFAULT_OR_UNAVAILABLE`도 실제 설정이 기본이라는 확인 결과가 아니다.

## 3. 이미 존재하는 최신 코드 / 재개 지점

두 TAR 모두 **구형 C23 포맷**이다. 신규 C24가 도입한 `wsl2_layers`, `event_boot_known`, `D06_C24_WSL2_* ` 출력이 전혀 없다. 원본의 `D06_C23_NO_PID_RECORD_CURRENT_BOOT_HOLD_ROOT_CAUSE_UNKNOWN`은 이 C23 기준이고, C24 최신 도구는 과거 부트 미확인을 `D06_C24_WSL2_PREVIOUS_EVENT_BOOT_UNVERIFIED_HOLD`로 분리한다.

**이미 공개 CI GREEN이므로 동일 코드 변경·동일 CI 회귀 반복 불필요.**
- C24 RED [#44768027525](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44768027525): WSL2 계층/부트 구분 누락 2 FAIL/2 ERROR.
- C24 GREEN [#44768278710](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44768278710): 신규 4/4 및 D06 L0 전체 PASS.
- 같은 코드에 대한 Ubuntu 24.04 CLI [#44768278702](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44768278702) PASS, Canary [#44768278636](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44768278636) PASS; WSL2 물리 backend 실행을 증명하지 않음.
- 정확한 C24 소스 SHA `b6cb297e4a7c54b5d7e2d07c732a4b528084c8c2`, 파일 `d06/tools/d06_c23_core_index_readonly_doctor.py`, Git blob `aa60806e50973a9d7d997caa319afc5066bb8926`.

## 4. 최소 다음 조치: C24 WSL2 읽기 전용 계층 정보 단 1회

C23 과거 PID의 단순 `info/list` 재실행 금지. 다음 한 블록은 WSL2 Ubuntu 24.04에서 실제 `/dev/dxg`, `/mnt/wslg`, NVIDIA D3D12 renderer, PID1 systemd, `/run/log/journal` vs `/var/log/journal`, 현재 boot ID를 함께 기록하는 **C24로 소스 전환**하는 절차다. Goal, Gazebo, SIGSEGV 생성, 시스템 전역 설정 변경 없음.

```bash
(
  set -Eeuo pipefail
  SHA="b6cb297e4a7c54b5d7e2d07c732a4b528084c8c2"
  BLOB="aa60806e50973a9d7d997caa319afc5066bb8926"
  SCRIPT="$(mktemp --suffix=.py)"
  trap 'rm -f "$SCRIPT"' EXIT
  curl -fLsS --retry 3 --max-time 90 \
    "https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public/$SHA/d06/tools/d06_c23_core_index_readonly_doctor.py" -o "$SCRIPT"
  test "$(git hash-object "$SCRIPT")" = "$BLOB"
  python3 -m py_compile "$SCRIPT"
  python3 "$SCRIPT" --self-check
  RC=0
  python3 "$SCRIPT" --doctor || RC=$?
  echo "AXIA_C24_EXPECTED_DIAGNOSTIC_HOLD_EXIT=$RC"
  test "$RC" -eq 3
)
```

- 제출: 출력된 `D06_C23_FORENSIC_ARCHIVE`의 TAR와 `D06_C23_FORENSIC_SHA256`의 sidecar만.
- 예상되는 최신 판정 `D06_C24_WSL2_PREVIOUS_EVENT_BOOT_UNVERIFIED_HOLD`은 **실패가 아니라 기존 이벤트 부트 미확정의 올바른 경계**다.
- 이 결과도 core backend 성공을 증명하지 않는다. 추가 코어 수집 실증이 필요해질 경우에는 단일 부트에서 event PID+boot ID+시간을 함께 보존하는 방식을 공개 CI 계약에 먼저 넣고, 재현할 이유가 분명한 **한 번의 계획된 검증만** 시행한다.
- 전체 Gazebo 재실행/Moving Goal은 이번 조회와 무관하며, 원래 `gz sim -s` exit -11이 해결되지 않은 동안 금지.

## 5. 결과 / 검증 등급 / HOLD

```text
C25_UPLOAD_SHA256_BOTH=PASS
C25_INNER_FILE_CONTENT_ALL_IDENTICAL=true
C25_DISTINCT_CORE_FAILURE_REPRODUCTIONS=NOT_PROVEN
C25_CORE_SOCKET_CURRENT_BOOT=ACTIVE
C25_EXACT_PID1424_CURRENT_BOOT_RECORDS=0
C25_C24_LAYER_FIELDS_IN_UPLOAD=ABSENT_OLD_C23_FORMAT
C25_NEW_RUNTIME_CHANGE=NONE
C25_NEW_CI=NOT_REQUIRED (C24 REGRESSION ALREADY GREEN)
C25_ACTUAL_WSL2_C24=NOT_RUN
C25_GAZEBO_SERVER_EXIT_MINUS11=UNRESOLVED
C25_MOVING_CM120_GUARD150=NOT_RUN
INDEPENDENT_WSLG_G3_REQUIRED=false
AXIA_MVP_DEMO_ACCEPTED=HOLD
CERTIFIED_ESTOP=false
MAIN_MERGED=false
```
