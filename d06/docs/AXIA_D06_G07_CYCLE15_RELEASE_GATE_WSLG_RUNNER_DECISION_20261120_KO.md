# AXIA D06/G07 — C15 인수 준비 현황 및 WSLg 동등 CI 러너 의사결정

작성일: 2026-11-20 KST | Draft PR #177 | 개발 확장 금지 | main 미병합

## 1. 목적

사용자 요청: "WSL2에서는 최종 확인만", "사용자 확인이 필요하기 전까지 자율 진행", "오류를 먼저 공개 CI 회귀에 편입". C11~C14 동안 첫 WSL2 `coredumpctl` 누락 오류를 전부 CI 의존성·진단 증거 검증으로 복구했지만, 대상 `WSLg D3D12 NVIDIA`에서 최초 Gazebo server SIGSEGV(-11) 스택은 아직 한 번도 확보하지 못했다. 이 미검증 구간이 다음 사용자 승인/환경 제공 없이 넘어갈 수 없는 경계다.

## 2. 실제 증거로 확인된 Gate

| Gate | 실제 증거 | 판정/한계 |
|---|---|---|
| G0 Source/Contract | C14 public [#44651428863](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44651428863) 155/155, SHA 4e5a410a60cf1bcace4ceaf884c41ca84620081c | PASS (ROS-free) |
| G1 clean Ubuntu 24.04 Dependencies | C13 [#44650542929](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44650542929), exact checkout, read-only mount, systemd-coredump/gdb/mesa CLI 실제 동작 | PASS (CLI만) |
| G1 real GDB evidence | C14 [#44651428861](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44651428861), 합성 SIGSEGV -> 실제 core -> 최초 GDB #0 -> SHA256 TAR, 원본 메모리 코어 제외 | PASS (실제 Ubuntu 합성 core) |
| G2 Jazzy+Harmonic+Waffle+Nav2 실제 Gazebo | C10 [#44568745545](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44568745545), code SHA 26a3a1b299e404d6e0fe9e69312578db356081ab | PASS, Linux Xvfb + Cyclone DDS NO_GOAL만 |
| G2 이후 코드 재사용 영향 | GitHub compare C10 SHA→C14 SHA : 추가 파일 12개가 C11–C14 core 진단·tests·docs·L0/L1 CI. 학생 Scan, ROS/Nav2, NO_GOAL L2 workflow의 기능 코드 변경 0건 | 기존 G2 성공 재사용. C14에서 Gazebo 새 시연 PASS 주장 금지 |
| G2 WSLg/GPU backend | 원본 r6YhIvPx: WSLg NVIDIA Gazebo server exit -11, 최초 core/stack 미확보 | HOLD |
| G3 동일 대상 OS/GPU 프로세스 정상 종료 | 강사 RTX 2060 WSLg D3D12와 동등한 실제 CI에서 Gazebo server exit0 및 최초 stack-root 수정 증거 없음 | NOT_VERIFIED |
| G4 Owner NO_GOAL/MOVING L3 | 강사 WSL2 최종 확인 미수행 | NOT_RUN |

C14 이후 공개 CI L0와 GitHub runner canary는 성공하지만, **L0/L1/G2 Linux PASS**만으로 G3 WSLg PASS를 생성하지 않는다.

## 3. 공식 플랫폼 문서에 따른 러너 대안

1. **표준 GitHub-hosted Ubuntu/Linux Xvfb**: 이미 현재 G2에 사용. WSLg D3D12가 없어 그 종료 크래시를 재현하지 못함.
2. **GitHub GPU larger runner Windows Tesla T4**: GitHub 공식 GPU larger runner 표에는 Windows/Linux Tesla T4가 명시되어 있음(https://docs.github.com/en/actions/reference/runners/larger-runners). 그러나 이는 RTX 2060이 아니며, Windows에서의 WSL2/WSLg/nested virtualization 사용 가능성과 D3D12 `glxinfo` 실제 렌더러 동등성은 **미확정**. GitHub 공식 가이드는 중첩 가상화가 기술적으로 가능해도 **공식 지원하지 않음**(https://docs.github.com/en/actions/concepts/runners/github-hosted-runners). GPU runner는 과금·계정/조직 권한 확인이 선행되어야 하며 현재 임의 생성/과금 금지.
3. **격리된 별도 Windows 11 + WSL2 Ubuntu24.04 + 실제 NVIDIA D3D12 WSLg 테스트 호스트**: 원본과 가장 가까운 환경. 안전상 ephemeral/isolated CI runner 권장. GitHub는 공개 저장소에 self-hosted runner 연결을 위험하다고 명시(https://docs.github.com/en/actions/reference/security/secure-use). 따라서 공개 PR/fork에 장치 접근을 무조건 허용하지 말고, 승인된 고정 SHA에 대해 1회 한정 환경 검증하며 원본 메모리 core를 공개 업로드하지 않는 분리된 보호 경계가 필요함. 호스트 제공/러너 구성·권한 변경은 사용자 승인이 필요함.

## 4. 조건부 최소 실행 계획 (사용자 승인 전 실행 금지)

A. 사용 가능한 *독립* Windows/WSLg NVIDIA GPU 테스트 러너 환경과 비용/보안 승인을 먼저 확보한다. 강사 수업/최종 WSL2를 임시 CI로 전용하지 않는다.

B. 실제 runner의 `wsl --status`, `/proc/sys/kernel/osrelease`, Ubuntu 24.04, ROS Jazzy, Gazebo Harmonic, WSLg `glxinfo -B` D3D12 renderer, NVIDIA GPU driver, `coredumpctl` 설치뿐 아니라 **core_pattern/journal backend 및 접근 권한**까지 preflight 실측한다. 원본 RTX 2060과 다르면 사유와 미등가 범위를 남긴다.

C. 승인된 공개 SHA를 다운로드하고 Git blob 검증한 기존 NO_GOAL/코어 진단만 수행. 이전 G2 Scan300/Clock/Nav/Loc/CM/Guard/Gazebo exit0를 같은 세션에서 증명하되 최초 server SIGSEGV가 재현된다면 첫 stack으로 B1 D3D12 TLS/B2 Gazebo teardown/B3 owner process order를 실제 증거로 구분. raw memory core는 외부 공개 금지.

D. 원인 확인 후 **가장 작은 단일 수정**: CI RED→GREEN, 실제 G2 재검증, 실제 동등 WSLg G3 SIGSEGV-free 정상 종료 증거 확보. CM120/Guard150 Moving Goal 후속 전달 주기를 별도 검사하기 전 전체 안정성 PASS 금지.

E. 위 Gate가 충분히 충족된 경우에만 강사 WSL2 **최종 인수 원샷** 제공. 실패하면 반복 현장 시도 대신 최초 로그/시각 쌍을 공개 CI 회귀에 이관.

## 5. 현재 STOP 조건과 사용자 결정이 필요한 유일한 항목

현재 연결된 GitHub 도구에서 **실제 Windows WSLg NVIDIA 동등 GPU 러너를 만들거나 사용할 권한/하드웨어가 확인되지 않았음**. 기존 공개 Ubuntu/Xvfb CI는 이 조건의 대체물이 아니다. 따라서 WSLg 최초 SIGSEGV 스택·진짜 server exit0는 당장 구현으로 완료할 수 없으며 원인을 추측하여 LD_PRELOAD/MESA/RMW/timeout을 수정하는 것은 금지.

필요한 결정: **별도 Windows/WSLg NVIDIA GPU 검증 러너 제공 및 1회 검증 권한(과금·러너 격리·로그 보안 포함)**. 제공 불가능하면 WSLg 출고 HOLD를 유지하고, 사용자 WSL2에서 하는 것은 사전 문제해결이 아닌 단일 최종 인수뿐이라는 기존 정책을 유지한다.

현재 결과:
C15_CODE_AND_CI_GATES_READY=true
C14_PUBLIC_REAL_GDB_CORE_EVIDENCE=PASS
C10_PUBLIC_REAL_GAZEBO_NO_GOAL_L2=PASS
WSLG_NVIDIA_SIGSEGV_ROOT_CAUSE=UNDETERMINED
WSLG_EQUIVALENT_CI_G3=NOT_AVAILABLE_OR_NOT_VERIFIED
OWNER_WSL2_L3=NOT_RUN
D06_GAZEBO_LIVE_RELEASE=HOLD
AXIA_MVP_DEMO_ACCEPTED=HOLD
CERTIFIED_ESTOP=false
MAIN_MERGED=false
