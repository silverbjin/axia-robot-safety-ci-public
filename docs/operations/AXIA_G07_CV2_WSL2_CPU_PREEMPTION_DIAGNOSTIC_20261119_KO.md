# AXIA G07 Task04 CV2U3T4v — WSL2 호스트 CPU 선점 가설 검증 및 1회 인수 원샷 진단 보고서

작성: 2026-11-19 KST. 개발 브랜치: `fix/g07-task04-owner-timing-evidence-20261119`. 스크립트·계측 도구만 추가, 실제 Supervisor/CM/Guard/Scan TTL/World/Goal/기존 Owner 코드는 **수정하지 않음**. 강사 WSL2 L3 미실행·HOLD.

## 1. 문제와 가설

원본 `owner-moving-CV2U3T4v` 최초 안전 타이밍 위반은 실제 Observer `/scan` gap `308.441ms > 300ms` (`CROSSES_STOP`). 원본 SQLite bag Scan 실제 수신 327.168ms, LaserScan stamp 시뮬레이션 99ms, `/safety/scan` 326.571ms, 동일 국소 `/clock` 약 실제 322ms에 시뮬레이션 87ms 진행(국소 비율 약 0.27). 그 외 최초 Goal·이동·SLOW/STOP 증거 존재. 평균 Gazebo GUI RTF 90%가 국소 저하를 배제하지 못한다.

사용자 가설: Windows 11에서 WSL2 Linux VM이 CPU 실행 기회를 잠깐 잃어 Gazebo sim-time 진척이 느려진 것이다. **가능성 있음, 아직 단독 원인 확정 아님**. Linux `/proc/stat` steal=0이어도 Hyper-V 호스트 선점을 배제하지 못함. Linux `/proc/PID/schedstat`은 주로 Linux 게스트 런큐 대기이며 Hyper-V 가상 CPU 대기 전체를 직접 보여주지 않는다. 프로세스 단위 `schedstat`은 thread-group leader만 검사하므로 Gazebo 작업 스레드 대기가 따로 있을 수 있다.

공식 근거:
- Microsoft WSL 설정: https://learn.microsoft.com/en-us/windows/wsl/wsl-config
- Linux schedstat: https://www.kernel.org/doc/html/latest/scheduler/sched-stats.html
- Gazebo Harmonic RTF: https://gazebosim.org/docs/harmonic/sdf_worlds
- Gazebo 센서 시뮬레이션 update_rate: https://gazebosim.org/docs/harmonic/sensors

## 2. MVP 범위 진단 구현

공개 CI 소스:
- `scripts/axia_g07_wsl2_cpu_preemption_once.sh`: 사용자 WSL2 TTY 원샷, 고정 기존 Owner SHA `cd8c23c52588f5efd6295b6904e15b1aa54496e7`을 **한 번만 호출**. `--self-check`는 ROS/Gazebo/Goal 미기동. `--run`은 기존 단일 Owner와 기존 수동 `YES-P2-G07-GOAL` 승인 요구를 그대로 수행.
- `scripts/axia_g07_wsl2_sched_probe.py`: 표준 Python3, 40ms 간격 WSL2 `CLOCK_MONOTONIC`/real time/boottime, 누적 `steal` jiffies, CPU/memory PSI, 선택적 Gazebo·Bridge·Guard 등 프로세스 leader의 schedstat 실행/대기 ns를 private JSONL로 기록. ROS 구독·publish 없음.
- `scripts/axia_g07_windows_host_cpu_probe.ps1`: Windows native `GetSystemTimes` CPU 사용율, `VmmemWSL` 프로세스 CPU 시간, Windows 독립 샘플 지연 (150ms) 기록. Win32 API를 읽기 전용으로 호출. CPU affinity/priority, 전원 설정, `.wslconfig` 수정 없음.
- 원래 Owner rosbag SQLite `/scan` 수신 timestamp+LaserScan CDR sim header, `/safety/scan`, `/clock`을 첫 `first_timing_violation` 게스트 monotonic 시간과 정렬해 국소 RTF를 비교. 원본 가변 파일을 절대 변경하지 않고 read-only SQLite 연결.
- Windows 프로브 파일이 실재하고 샘플을 기록했음을 **Owner run 시작 전 확인**. WSL ↔ Windows PowerShell / UNC interop가 실패하면 `AXIA_G07_CV2_HOST_SAMPLER_PRECHECK_FAILED_NO_OWNER_RUN`, Owner 자체는 시작되지 않으므로 현장 1회 실행 기회를 소비하지 않음.
- 완료 후 private `$HOME/axia_g07_task04_owner_moving/probe-CV2-XXXXXXXX.diagnostics.zip`와 SHA256 생성. 전체 민감 rosbag은 이 ZIP에 포함하지 않고 기존 Owner가 TAR/SHA256으로 별도 보존. 자동 업로드 없음.
- 분리 진단 스크립트가 성공해도 **`HYPERVISOR_CPU_PREEMPTION=HOST_CPU_PREEMPTION_UNCONFIRMED`**로 표기. 엄밀한 Hyper-V 스케줄러 선점의 확증은 별도 Windows 호스트 ETW 계측 없이는 보장할 수 없으므로 과잉 판정 금지.

## 3. 공개 CI RED→GREEN 실측

| 단계 | 실제 GitHub Actions | 판정 |
|---|---|---|
| 도구 존재·샘플 생성 RED | [#44461376014](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44461376014) | 5 FAIL, 3 ERROR — 진단 도구가 원래 없음을 확인 |
| Linux 기본 샘플 GREEN | [#44461961282](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44461961282) | 5/5 PASS |
| 첫 Scan 위반-호스트 시간 정렬 RED | [#44462073763](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44462073763) | 1 ERROR, 시간창 정렬 필드 부재 |
| Windows/게스트 국소 시간 정렬 GREEN | [#44462184668](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44462184668) | 6/6 PASS |
| 호스트 모니터 미기동 시 Owner 재실행 방지 RED | [#44462643941](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44462643941) | Linux job FAIL, 준비 검사 부재 |
| 최종 Linux/Windows/원격 SHA 고정 자가검사 | [#44462753457](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44462753457) | **Linux 7/7 PASS, Windows native 실계측 14 samples PASS, 공개 원본 URL 다운로드 및 self-check PASS** |

최종 script commit `adb56a1fa07ad80ed7cde9af4042f9d0cfebd09a`; 실제 공개 Green 실행은 이 commit에 고정됨. Linux test의 `SIMULATED_350MS_GAP_FOUND`는 합성 회귀 fixture이므로 **사용자 WSL2 선점 실측 결과가 아님**. Windows GH runner에서 14 samples는 Windows P/Invoke 구현 검증이며 **사용자 Windows 호스트/WSL2의 실제 간섭 실측이 아님**.

## 4. 사용자 WSL2 1회 재검 진단

WSL2 Ubuntu24.04의 **원래 로봇 시연용 터미널**에서 수행:

```bash
(
 set -Eeuo pipefail
 SHA='adb56a1fa07ad80ed7cde9af4042f9d0cfebd09a'
 F="$(mktemp --suffix=.sh)"
 trap 'rm -f -- "$F"' EXIT
 curl -fLsS --retry 3 --max-time 90    "https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public/$SHA/scripts/axia_g07_wsl2_cpu_preemption_once.sh"    -o "$F"
 bash -n "$F"
 AXIA_G07_CV2_PROBE_REF="$SHA" bash "$F" --self-check
 AXIA_G07_CV2_PROBE_REF="$SHA" bash "$F" --run
)
```

- 원래 고정 Owner SHA만 실행, Goal 승인/물리 STOP 시나리오 변경 없음. Gazebo/RViz가 뜨면 원래 터미널에 포커스, 180초 이내 `YES-P2-G07-GOAL` 입력.
- 호스트 모니터가 준비되지 않는다면 Owner는 실행되지 않고 `HOST_SAMPLER_PRECHECK_FAILED_NO_OWNER_RUN` 발생. 파일 `$HOME/axia_g07_task04_owner_moving/probe-CV2-XXXXXXXX/windows_monitor.log`에 진단이 남으므로 인수용 Owner 반복 실행 금지.
- 사용자는 Owner TAR+SHA256, 기존 Owner diagnostics ZIP+SHA256, 새 CPU probe diagnostics ZIP+SHA256을 사적으로 전달. JSONL·Windows 로그에 개인 경로가 있는지 확인. 공개 GitHub에 업로드 금지.
- Scan 300ms 실패 시 즉시 동일 WSL2 테스트 반복하지 않고, **첫 Scan TTL 위반의 guest monotonic과 Windows independent host samples ±0.6초**를 비교.

## 5. 해석 기준 및 임계값 정책 의사결정

| 실제 현장 관측 | 원인 판단 | 조치 |
|---|---|---|
| Scan 위반 ±0.6s에 Windows 호스트 모니터/WSL2 sampler 모두 큰 wake-up gap, Windows CPU 포화/압박 및 시뮬레이션 진척 저하 | Windows 또는 Hyper-V 스케줄링 압박을 강하게 의심. **Hypervisor CPU 선점의 단독 확증은 아님** | Windows 백그라운드 작업/전원/WSL2 CPU 메모리 경계의 단일 최소 변경 후보를 고르고 동일 조건 공개 CI 회귀 확인 |
| Windows sampler 정상, WSL2 scheduler wait/PSI만 증가 | WSL2 게스트 내부 실행 큐/프로세스 경쟁 가능성 | ros_gz_bridge/gz sim process 대기 및 CPU overcommit 확인 |
| Windows/WSL2 sampler 정상인데 Sim Clock만 국소 27% 수준, Scan sim stamp 정상 | Gazebo 물리/센서·stop set_pose·렌더 부하 가능성 우선 | 장애물 변경/센서 콜백에서 실제 느린 경계 추가 계측 |
| /clock 시간과 scan sim stamp 정상 속도인데 오직 /scan wall receipt 증가 | Bridge/DDS/Observer 전달 지연 | ROS graph 간 데이터 전달 경계 진단 |
| Windows 호스트 samples 없음 또는 시간 정렬 실패 | 단독 원인 분리 불가 | Owner 다시 실행하기 전 host sampler 연결 수정; 무근거 CPU 선점 확정 금지 |

**Scan wall-time 300ms 완화·무시 판단은 이번 진단 실측 후 별도 승인.** 동일 현상에서 LaserScan Sim time stamp 10Hz 정상이고 실제 Gazebo sim clock이 늦게 진행했다면, *숫자 인수 검증기*에서만 `WSL2_SIM_RTF_LIMITATION` 식으로 환경 원인을 별도 기록한 scoped 예외를 검토할 수 있다. 이를 정규 `21/21 PASS`나 안전 인증으로 승격하지 않으며, 실제 Safety Supervisor/Collision Monitor/Guard의 센서 stale → SW STOP 방어 및 CM120ms·Guard150ms·Contact0 계약은 그대로 유지한다.

현재 변경은 **진단 전용**, 원본 300ms 기준/인수 판정기/안전제어를 단 한 줄도 완화하지 않았다.

```ini
PUBLIC_DIAGNOSTIC_L0_LINUX=PASS_7_OF_7
PUBLIC_DIAGNOSTIC_L0_WINDOWS=PASS_14_NATIVE_SAMPLES
OWNER_ORIGINAL_SHA=cd8c23c52588f5efd6295b6904e15b1aa54496e7
OWNER_WSL2_SCHEDULER_L3_RECHECK=NOT_RUN
WINDOWS_VCPU_PREEMPTION=UNVERIFIED
SCAN_TTL_300MS=UNCHANGED
AXIA_MVP_DEMO_ACCEPTED=HOLD
CERTIFIED_ESTOP=false
MAIN_MERGED=false
```
