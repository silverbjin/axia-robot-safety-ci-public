# AXIA D06 C21 — 기존 Gazebo 서버 SIGSEGV 코어 미발견: 원본 TAR 분석

- 2026-11-21 KST · PR #177 개발 브랜치 `fix/d06-wslg-lidar-vs-rtf-ci-20261118` · main 미병합
- 현장 입력: `trace-svstYuu9.tar.gz`, `trace-svstYuu9.tar.gz.sha256`
- tar 실제 SHA256: `d86b18027abdd1ec89359e3a66c6e21acbdefb89fd9c3d30a97bc9ce01438141`; 첨부 sidecar와 **실제 일치**.

## 실제 5개 내부 파일

| 파일 | 크기 |
|---|---:|
| `summary.txt` | 178 bytes |
| `preflight.txt` | 122 bytes |
| `triage.log` | 0 |
| `owner_tail.log` | 0 |
| `gdb_backtrace.log` | 0 |

```text
D06_WSLG_CORE_ONCE_SERVER_CORE_ONLY
D06_WSLG_CORE_ONCE_EXISTING_ONLY_MISSING_CORE_NO_REPLAY
stage=FIRST_CORE_CHECK owner_rc=NOT_RUN root_cause=UNCONFIRMED core_not_archived=true
```

```text
kernel_core_pattern=|/usr/lib/systemd/systemd-coredump %P %u %g %s %t 9223372036854775808 %h %d
current_core_soft_limit=0
```

## 판단

1. 이전 C20의 `coredumpctl` 미설치 FAIL과 달리 이번에는 코어 목록 조회 경계 `FIRST_CORE_CHECK`까지 도달했습니다. 해당 사용자에게 보이는 시스템 코어 색인에서 최초 WSL2 NVIDIA Gazebo server PID 19280의 SIGSEGV 코어를 찾지 못했습니다. 전체 시스템 어디에도 core가 없다고 단정하지 않습니다.
2. **Gazebo/ROS 재실행 없음**: `owner_rc=NOT_RUN`, 빈 `owner_tail.log`. 이번 실행에서 또 SIGSEGV가 났다는 주장은 금지.
3. GDB #0 스택이 없으므로 RTX2060/Ogre2/D3D12/RMW 중 근본 원인 **미확정**.
4. 현재 코어 핸들러는 `systemd-coredump` 파이프입니다. 과거 충돌 시에도 이 핸들러가 활성화되었다는 증거는 없으며, 나중에 설치해도 과거 덤프가 소급 생성되지 않습니다.
5. Linux `core(5)` 공식 문서에 따르면 **`core_pattern` 파이프 핸들러에 `RLIMIT_CORE`가 적용되지 않으므로** `current_core_soft_limit=0`만으로 수집 실패 원인을 단정해서는 안 됩니다. 근거: https://man7.org/linux/man-pages/man5/core.5.html
6. 기존 `--existing-only` 분석기는 코어 미발견 시 재실행 없이 FAIL CLOSED 종료하는 계약을 **실제 현장에서 충족**했습니다. 새로운 코드 실패가 아니므로 불필요한 신규 RED/수정/CI 반복은 하지 않습니다.

## 보존된 이전 원본과 구분

기존 `d06-forensic-ab-no-goal-1jvaRyCE.tar.gz` SHA256 `541c47638528dbefc0258b51ff23d88e2406bb8e4b78be5e1f1812bd477bdb38`에서:
- 별도 20.161s dual Scan 창 raw 최대271.130ms, Safety 최대237.858ms, CLEAR165/165(Scan300 OK 후보).
- 세션 초기 독립 ROS 수신 raw 423.494ms / safety 418.905ms는 별도 pre-READY 범위, 학생 실제 첫 source pair 미입증.
- Navigation 및 Localization ACK, CM exit0, witness exit0.
- **Gazebo server PID19280 exit -11**; 부모 graceful marker로 종료 성공 처리 금지.

이는 *직전* 현장 원본에서 확보한 증거입니다. 이번 `trace-svstYuu9`가 원래 센서/안전 상태를 다시 검증한 것은 아닙니다.

## 다음 단계 / 인수 정책

- 독립 GPU 호스트 G3 **필수 제외** (C18) 유지. **현장 동일 오류 무작정 재실행 금지**.
- 기존 Linux/Xvfb 실 Gazebo L2 PASS 보존, NVIDIA WSLg native exit0 PASS로 승격 금지.
- 향후 새로운 실제 실행이 필요하다면 공개 CI에서 먼저 **최초 충돌/스택 캡처 경계를 재현하는 회귀**와 수집 준비를 확보한 뒤에만 WSL2에서 단일 계획된 시도를 승인.
- TTL Scan300/CM120/Guard150 및 E-Stop 정책 완화 없음, Goal 불허, main 미병합.

```text
C21_SHA256=PASS
C21_EXISTING_CORE_LOOKUP=COMPLETED_NO_MATCH
C21_GDB_FIRST_STACK=NOT_CAPTURED
C21_GAZEBO_REPLAY=NOT_RUN
C21_NEW_CODE_CHANGE=NONE
C21_NEW_CI=NOT_NEEDED
C19_CI_GREEN=44727931833
C20_CI_GREEN=44733717528
OWNER_WSL2_NO_GOAL=HOLD_GAZEBO_SERVER_EXIT_MINUS11
AXIA_MVP_DEMO_ACCEPTED=HOLD
CERTIFIED_ESTOP=false
MAIN_MERGED=false
```
