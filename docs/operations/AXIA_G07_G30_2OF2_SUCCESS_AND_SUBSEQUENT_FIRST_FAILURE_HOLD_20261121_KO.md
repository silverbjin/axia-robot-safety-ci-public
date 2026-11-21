# AXIA G07 G30 — 동일 코드 실제 Gazebo 2/2 성공과 후속 간헐 회귀 실패의 분리 기록

**검증일:** 2026-11-21. **최종 출고 판단:** `WSL2_OWNER_RELEASE=HOLD`, `ROOT_CAUSE=UNDETERMINED`, `OWNER_L3=NOT_RUN`, `CERTIFIED_ESTOP=false`.

## 1. 먼저 획득한 **진짜** 엄격 L2 독립 2/2 성공 (출고 증거로 보존)

- 공개 Public source `5e944817cf22b7e0ff2ef53aa2b5d66640b3eab3`.
- Student source `d8ec1a50bdd5a9097530b0924709a6ee63ce4eb5`.
- [GitHub Actions #44876616579](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44876616579), `AXIA G07 Original Multi First Scan RMW Exact Pair Diagnostic Native L2`, **completed/success**, Ubuntu24.04 ROS2 Jazzy/Gazebo Harmonic 실제 Waffle/공식 Nav2+Collision Monitor, GUI RViz/Gazebo 둘 다 각 Cycle에서 X11 1/1, 실제 Moving Goal runner **RC=0 각각**.
- Cycle1 job `136762694162`: Guard internal CM age **max39.986006ms**, 132 sample, Guard/Supervisor child exit0.
- Cycle2 job `136762693985`: Guard internal CM age **max19.954137ms**, 126 sample, Guard/Supervisor child exit0.
- 첫 위반은 양쪽 `null`. 양쪽 `BOOT_SAFE→NORMAL` 관측, Guard latch 없음. 각 실제 Goal→CLEAR/SLOW/STOP→exact Cancel, Nav+Loc ACK, managed clean exit, original 14-topic SQLite bag checks는 **각 Job의 엄격 native workflow 성공 범위**. 인증 E-Stop은 검증 대상 아님.
- Cycle1 실제 후Goal callback max: Clock160.499ms, Guard92.952ms, Odom199.318ms, CM preGuard78.352ms, Scan206.102ms, Supervisor78.488ms. Cycle2: Clock106.585ms, Guard59.993ms, Odom139.684ms, preGuard61.780ms, Scan192.000ms, Supervisor62.774ms. 모든 기존 CM120/Guard150/Scan·Odom·Clock300ms 범위 이내.
- 아티팩트 #14696790264 ZIP SHA256 `ab09b740b62d29b4f042acaf48e313f9536c4e24f294176991d30e89c122dc8c` embedded checksum 7/7; #14695389513 ZIP SHA256 `72469ba0b43a898455d314ac457133142bdfef72ada8eaa8f1db50987ad97a68` embedded checksum 7/7.
- **2/2 성공은 정확한 해당 SHA의 scoped native 성공이지 영구적인 간헐 오류의 원인 해결을 보증하지 않음.**

## 2. 후속 같은 Student runtime의 G25 read-only 계측 SHA에서는 **0/2 실패**

- Public `e78b15580e4a8cf1607dc371237ad751af62e652`, Student 여전히 `d8ec1a50bdd5a9097530b0924709a6ee63ce4eb5`. 추가된 것은 읽기 전용 `d06/diagnostic/g07_managed_launch_first_roles.py`와 26초 종료 증거 upload 경로. 라이브 ROS 주행기 코드는 Student SHA 그대로.
- [Actions #44876964129](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44876964129) **0/2 FAIL**. Static Python [#44876969582](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44876969582) **329 PASS, 3 SKIP**, Runner Canary #44876969604 PASS, L0 #44876964216 PASS. L0는 실제 L2 안전성 PASS가 아님.
- Cycle1, job `136763680302`: 최초 Observer callback **Odom332.933231ms>300ms** at host-monotonic **331.975934028→332.308867259**; 같은 7채널 첫 실패 Scan391.469709ms, Clock332.585515ms, Guard358.099415ms, CM preGuard383.329551ms, Supervisor383.418984ms, supervised383.505964ms. **동일 CM publisher seq+1 Source48.558766ms, 원 Observer RMW Received380.607076ms, 독립 ROS RMW Received48.570903ms**. Observer writer lock0.317ms/flush1.392ms/json2.018ms/write1.652ms 수준; 독립 heartbeat 실행. Executor 첫 스택 `_wait_for_ready_callbacks`, 두 Worker `_worker` 유휴. 첫 Supervisor `BOOT_SAFE→NORMAL`은 위험 상태 전이가 아닌 정상 승인으로 최초 TTL 위반 이전 발생. 최초 악화 전이 미관측, Guard 최초 latch 미관측, root still unproven. 외부 CM callback gap이 Guard 내부 age 위반을 직접 증명하지는 않음.
- Cycle2, job `136763680244`: GUI가 있는 실제 물리 시연 후 formal shutdown `MVP_VISUAL_L2_PASS_FORMAL_SHUTDOWN_HOLD`, native runner RC=3, `localization_shutdown_ack=false`. 정확한 최초 서버/생존 프로세스 원인 미확정; visual scoped PASS를 formal release PASS로 승격 금지.
- G25에서 누락 없이 첫 26초 잔존 프로세스 역할 숫자만 기록. Process argv/PID/private 경로는 public artifact에서 제외. 실제 이 Run에서는 `MANAGED_EXIT_ROLE_SNAPSHOT`은 26s timeout 첫 사건이 없을 시 NOT_OBSERVED이지 종료 성공 증거가 아니다.
- **경계:** 최신 strict 2/2는 실패하였으므로 WSL2 실행기 배포 금지, 실제 L3 미실행. 첫 CM RMW Source vs Received와 독립 동시 Subscriber 차이를 재현 가능한 CI RED에 유지. 추가 Goal을 무작위로 반복하거나 TTL을 완화하지 않음.

## 3. 개발 트랙별 실제 결과

| 게이트 | 결과 |
|---|---|
| G00 기존 브랜치/artifact SHA 인벤토리 | PASS (문서만) |
| G10 DDS RMW actual source/received/wait-set origin | Partial classification; 원인 미확정 |
| G20 SLOW 전방 velocity/heading 수치 진단 | RED #44876124022→GREEN #44876203447, 실제 물리 SLOW/STOP 성공 Run #44876616579 |
| G25 Navigation/Localization lifecycle+managed process exit | 성공 Cycle 증거 보존, 후속 Cycle formal 종료 실패/원인 미확정 |
| G30 공개 Python/strict actual 2/2 | 특정 SHA #44876616579 2/2 PASS, 새 문서/계측 SHA #44876964129 **0/2 FAIL**, 안정성 미입증 |
| G40 SHA-pin Owner launcher | 신규 WSL2 명령 출고 HOLD |
| G50 강사 WSL2 L3 | NOT RUN |
| G60 main 병합 | 사용자 승인이 없으므로 하지 않음 |

**다음:** G10 CI-only existing Executor GuardCondition wake 단일 A/B는 정상 발행 대비 원 Observer RMW Received 재발을 증명하는 목적. RED #44877371784 재현, GREEN L0 #44877451955 PASS, full Python #44877528863 330 PASS/3 SKIP, native strict #44877524595 진행 중(본 문서 작성 시점). A/B 성공만으로 ROOT PROVEN 아님. 2/2 실패 시 기각하고 이 최초 사건을 기준으로만 다음 최소 수정을 결정한다.
