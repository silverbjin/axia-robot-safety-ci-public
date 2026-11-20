# AXIA D06 C23 — C22 합성 SIGSEGV 종료139 / 코어 색인 미확보: 원인 경계 분리 및 읽기 전용 진단

작성: 2026-11-21 KST · 공개 PR #177 · **NO_GOAL/MOVING 인수 HOLD** · main 미병합

## 1. 원본 현장 자료 확인

강사 WSL2 제출 `probe-AuFytJyR.tar.gz` + `.tar.gz.sha256`.
- TAR 실제 SHA256: `3d255d6f4fe1d4b4be982c8d8288c49bb03af8a3510ae7ba378514f99fcd7f84`. 첨부 sidecar와 일치.
- TAR 크기 480 bytes; 내부 `summary.txt` 120 B, `preflight.txt` 247 B, `probe_result.txt` 42 B, `gdb_excerpt.txt` 0 B. 새 원본 raw core 없음.
- 원본:

```text
D06_C22_SYSTEMD_CORE_RETRIEVAL_NOT_PROVEN_HOLD_NO_GAZEBO
stage=CORE_INDEX synthetic_child_rc=139 core_not_archived=true
kernel_core_pattern=|/usr/lib/systemd/systemd-coredump %P %u %g %s %t 9223372036854775808 %h %d
parent_core_soft_limit=0
parent_core_hard_limit=unlimited
init_process=systemd
process_under_test=isolated_bash_subprocess
system_config_changed=false
synthetic_child_rc=139
synthetic_pid=1424
```

정확한 판정: **합성 Bash 하위 프로세스 종료139는 확인**되지만, 종료 시점 systemd-coredump의 journal record 또는 dump 파일이 실제 저장됐는지 미입증. C22는 `coredumpctl info 1424` 출력 원본을 보존하지 않고 PID/Signal/Executable 정규식으로만 판정했으므로 아래 두 가설이 구분되지 않음:
1. `systemd-coredump.socket`/journald/저장소 측에서 이벤트 자체가 저장되지 않았음.
2. 저널 기록은 있으나 C22의 PID/Signal/Executable exact grep 형식 또는 수집 타이밍이 맞지 않았음.

`parent_core_soft_limit=0`이 곧 실패 원인이라는 추론 금지. C22 자식은 별도 soft 65536 KiB 설정, 현재 `core_pattern`은 파이프 방식. Linux core(5)는 파이프 핸들러에서 RLIMIT_CORE 제한 미적용을 문서화함. 또한 Bash SIGSEGV 139는 원래 Gazebo server exit -11의 원인이 해결됐다는 증거가 아니다.

이전 실제 Owner `d06-forensic-ab-no-goal-1jvaRyCE`: Gazebo `gz sim -s` PID 19280 exit-11, Nav/Loc ACK/CM exit0, 준비 이후 dual Scan20.161s (raw271.130ms, safety237.858ms), READY 전 독립 ROS 수신 raw423.494ms와 safety418.905ms는 별도 미확정 첫 경계. Moving Goal 허가 없음.

## 2. 관련 브랜치·공식 문서 재검토

- 관련 공개 이슈 [#186](https://github.com/silverbjin/axia-robot-safety-ci-public/issues/186), [#185](https://github.com/silverbjin/axia-robot-safety-ci-public/issues/185): Gazebo server -11과 CM -11은 각각 다른 프로세스 경계. 기존 shutdown 개선은 Nav/CM만 통과시켰고 Gazebo 종료 -11을 해결했다는 증거 없음.
- 기존 C12/C13: Ubuntu24.04 `systemd-coredump` 패키지/CLI 검증 PASS. C14: GDB로 **생성한** 합성 코어→GDB/TAR PASS. 실제 WSL2 kernel→systemd/journal backend는 C22에서 최초 시도했으나 HOLD.
- systemd 공식 문서:
  - https://www.freedesktop.org/software/systemd/man/255/systemd-coredump.html
  - https://www.freedesktop.org/software/systemd/man/255/coredumpctl.html
  - https://www.freedesktop.org/software/systemd/man/255/coredump.conf.html
  - https://man7.org/linux/man-pages/man5/core.5.html
- systemd-coredump는 커널 파이프 핸들러, socket-activated service, journald 및 외부 storage 각각 역할이 다름. `core_pattern`만으로 서비스/색인/원본 core 저장 성공을 보장하지 않는다.
- 유사 WSLg/Ogre/D3D12 문제는 원본 Gazebo 서버 GDB #0가 없어 이번 작업의 수정 근거가 아님. Mesa/RMW/TTL/드라이버 변경 금지.

## 3. 이번 조치: 실제 현장 재충돌 없이 읽기 전용 C23 진단

- 신규 도구 `d06/tools/d06_c23_core_index_readonly_doctor.py`.
- 신규 회귀 `d06/tests/test_d06_c23_core_index_readonly_doctor.py` 6개.
- 기존 공개 L0 `.github/workflows/axia-d06-g07-wslg-lidar-rtf-isolation-l0-20261118.yml`에 두 파일과 테스트 연결.
- `--self-check`: 파일/코드 검사, 시스템 접근/프로세스 종료 없음.
- `--doctor`: 강사 Ubuntu24.04 WSL2에서만 실행; **새 SIGSEGV·Gazebo·ROS 실행 없음**. systemctl에서 `systemd-coredump.socket` 상태 읽기, `sudo -v`로 1회 read-only system journal 조회 권한 확인, 같은 부트의 `journalctl --boot COREDUMP_PID=1424` 필드, `coredumpctl info 1424` 메타데이터 읽기, `systemd-analyze cat-config systemd/coredump.conf` 유효 항목 일부 확인. 민감한 원본 저널/코어는 TAR에 포함하지 않고, **PID 1424 일치 통계·socket 상태·설정값·verdict**만 작은 SHA256 TAR로 보존.
- 같은 boot인지 확인할 원본 C22 boot_id가 없으므로 `CURRENT_BOOT_ONLY_PID_1424`로만 표시. 오래된 실행을 새 부트에서 찾지 못했다고 **WSLg 코어 저장 경로 자체가 불가능하다고 단정하지 않음**.
- CLI 분류:
  - `D06_C23_SOCKET_NOT_LISTENING_HOLD`: 현재 socket 비활성 후보. 자동 활성화/설정 변경 금지.
  - `D06_C23_JOURNAL_PERMISSION_UNVERIFIED_HOLD`: 권한 때문에 자료 부족.
  - `D06_C23_JOURNAL_RECORD_PRESENT_INFO_MISSING_HOLD`: 정확한 SIGSEGV Bash journal row는 있으나 coredumpctl info 일치 없음.
  - `D06_C23_INFO_PRESENT_C22_MATCHER_OR_TIMING_CANDIDATE_HOLD`: 현재 info는 일치, 과거 C22가 놓쳤을 가능성(확정 아님).
  - `D06_C23_NO_PID_RECORD_CURRENT_BOOT_HOLD_ROOT_CAUSE_UNKNOWN`: 현재 부트에서 검색되지 않음. 이벤트 당시 journald 문제/부트 차이 미분리.
- raw core, `sudo sysctl`, 패키지 설치, ROS, Gazebo, Goal, RMW 전환, TTL 완화 없음.

## 4. 실제 공개 CI — RED → GREEN → REFACTOR → REVIEW → COMMIT

- **RED** 신규 테스트/workflow commit `e042bee33b610aa55321c517fc10cf1663bf3833`; 공개 [Run #44766437135](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44766437135) **5 FAIL+1 ERROR**, 신규 도구 파일 미존재. 예상된 계약 실패이며 ROS/Gazebo 실패가 아님.
- **GREEN** 신규 도구 commit `cf4da444e887779db70a5f72bbf8a4e32b177321`, Git blob `3c8dc6bb407afd6c14eff99ac3a534702f66c0ce`. 공개 [L0 Run #44766744065](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44766744065) completed SUCCESS. C23 6/6 `ok`, 전체 D06 L0 workflow 성공.
- 같은 SHA [Runner Canary #44766744060](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44766744060) SUCCESS. [Ubuntu 24.04 CLI #44766744023](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44766744023)는 이전 C12/C13 패키지 및 합성 core 경로의 재확인용(현장 WSL2 전체 종단 아님).
- **REFACTOR/REVIEW**: 기존 C22 자식 충돌 코드는 그대로 보존. 진단 목적만 추가해 FAIL CLOSED, 6개 오프라인 조건별 판정 확인. `--doctor`는 CI 호스트에서 원천 차단, `--classify-fixture`는 OFFLINE/HARDWARE_NOT_PROVEN만 출력. 사용자 현장 실제 systemd 저널·코어 재검증 **NOT_RUN**.
- 주의: `sudo -v`가 인증을 위해 터미널에서 암호를 요청할 수 있으나 뒤의 `journalctl`/`coredumpctl`은 읽기 전용이다.

## 5. 강사 WSL2에서 다음에 실행할 단일 읽기 전용 명령

```bash
(
  set -Eeuo pipefail
  SHA="cf4da444e887779db70a5f72bbf8a4e32b177321"
  BLOB="3c8dc6bb407afd6c14eff99ac3a534702f66c0ce"
  SCRIPT="$(mktemp --suffix=.py)"
  trap 'rm -f "$SCRIPT"' EXIT
  curl -fLsS --retry 3 --max-time 90 \
    "https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public/$SHA/d06/tools/d06_c23_core_index_readonly_doctor.py" -o "$SCRIPT"
  test "$(git hash-object "$SCRIPT")" = "$BLOB"
  python3 -m py_compile "$SCRIPT"
  python3 "$SCRIPT" --self-check
  python3 "$SCRIPT" --doctor
)
```

- 실 코어/저널에서 이벤트가 발견되어도 **지난번 Gazebo 크래시 근본 원인을 고쳤다는 뜻 아님**. C23 진단의 최종 exit3은 정상 HOLD 신호.
- `D06_C23_FORENSIC_ARCHIVE=...` 와 `D06_C23_FORENSIC_SHA256=...` 두 경로만 제출. journalctl 전체 로그, raw memory core 공개 업로드 금지.

## 6. 인수 상태

```text
INDEPENDENT_WSLG_G3_REQUIRED=false
C22_REAL_WSL2_SYNTHETIC_CHILD_SIGSEGV=EXIT139
C22_REAL_WSL2_SYSTEMD_CORE_PIPELINE=NOT_PROVEN (CORE_INDEX)
C23_PUBLIC_L0=PASS (6 NEW)
C23_REAL_WSL2_READONLY_DOCTOR=NOT_RUN
GAZEBO_FIRST_GDB_STACK=NOT_CAPTURED
OWNER_WSL2_NO_GOAL=HOLD_GAZEBO_SERVER_EXIT_MINUS11
MOVING_CM120_GUARD150_E2E=NOT_RUN
AXIA_MVP_DEMO_ACCEPTED=HOLD
CERTIFIED_ESTOP=false
MAIN_MERGED=false
```
