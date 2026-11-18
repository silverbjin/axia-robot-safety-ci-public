# AXIA D06/G07 — Intel D3D12 LiDAR 근거리 이상과 RTF 저하의 독립 검증

2026-11-18 KST · Jazzy/Harmonic/공식 Nav2/TB3 Waffle · 공개 CI · RED→GREEN→REFACTOR→REVIEW→COMMIT

## 1. 고객 실제 WSL2 원본 (실측·추정 엄격 구분)

- 실제 제출된 `d06-wslg-sensor-66nBP1EG.tar.gz` SHA256: **`8ccb54fe9ec7d9b9e6290002e8f6458ee6c18ca7a224d929e6b3f2dc212ad62d`**, 외부 .sha256 일치. native SHA256SUMS 41/41 PASS.
- 해당 세션의 `glxinfo -B`: **`D3D12 (Intel(R) Iris(R) Xe Graphics)`**, Mesa 26.2.6, OpenGL 4.1. 이것은 WSLg GL 클라이언트 렌더러의 측정으로서 Gazebo Ogre2 서버 내부 GL 상태와 구분해야 함.
- 실제 /safety/scan: 20.019초 구간에서 60개, 전방 중앙값 **0.525560m** (원래 >0.75m 위반), 측면 **0.630749m** (원래 >1.20m 위반), 360° 0.4~0.85m 비율 **1.0**, CLEAR 0/60. 원형 /scan 60개. 원래 GoAL은 0회이며 unsafe pregoal NO_GOAL HOLD는 정상.
- 실제 Host callback 수신 최대 간격: safety **0.788704s**, raw **0.786086s**. 원본 Scan 소스 stamp delta 최대 **0.102s**. 원래 300ms Sensor TTL 엄격 위반.
- **중요:** 이전 관찰로 약 3Hz Wall scan은 산출 가능하지만 이 TAR의 `/clock`은 메시지의 simulation stamp 1926개만 저장했고 `time.monotonic()` host receipt timestamp가 **없습니다**. 따라서 **Intel RTF≈0.3은 가설**이며, 이 원본으로 Gazebo의 정확한 RTF를 계산한 것처럼 보고해서는 안 됨.
- 기존 WSL2 종료에서 Gazebo/Collision Monitor `-11`, Supervisor `1`이 관찰되어 `P2_L2_GRACEFUL_TEARDOWN` 문자열만으로 종료 무결성이 증명되지 않음. 본 작업에서는 해당 문제를 별도 리스크로 보존하고 안전 TTL이나 프로세스 종료 정책을 억지 완화하지 않음.

## 2. 실험 설계 — 두 개의 독립 변수를 혼동하지 않는다

**거리 정확도 축:** 실제 `/safety/scan` 전방/측면 측정치와 360° 근거리 비율. 기존 물리 월드, Waffle SDF, 초기 Pose `[-2,-0.5,0]`, Occupancy Map hash, 전방>0.75m, 측면>1.20m를 그대로 사용. 실패해도 임의 거리 필터/안전 임계값 변경하지 않음.

**시간/RTF 축:** `/clock` 메시지 각각의 시뮬레이션 timestamp와 `time.monotonic()` 실제 host 수신 timestamp를 같은 스캔 측정 구간에서 동시에 저장. `RTF=(Clock sim_last-sim_first)/(clock host_receipt_last-host_receipt_first)`와 `Scan source Hz=(count-1)/ΔScan stamp`, `Scan host Hz=(count-1)/ΔScan host receipt`를 각각 기록. `ROS Clock 수신 기반 RTF`는 Gazebo native world stats와 구분하며 Gazebo 렌더러 GPU 원인 자체를 입증하지 않음.

| 독립 사례 | 거리 | ROS Clock RTF | 결론 |
|---|---|---|---|
| WSLg에서 전방위 비정상 거리 + RTF 저하 | FAIL | 낮음 | 두 증상 동시; 인과관계 미확정 |
| 거리 이상이나 RTF 정상 | FAIL | 약 1.0 | 거리/렌더·기하 문제를 별도 우선 검토 |
| 거리 정상이나 RTF 저하 | PASS | 낮음 | 성능·시뮬레이터 스케줄링 문제 별도 |
| 거리 정상·RTF 정상인데 Raw Scan 400ms 지연 | PASS | 약 1.0 | ROS Raw/DDS/Callback 전달 주기 별도 위반 |
| 호스트 Clock 수신 기록 없음 | 무관 | 미측정 | `RTF_UNMEASURED`, RTF 결론 금지 |

**GPU A/B는 동일 PC WSLg, 동일 Git SHA, 동일 world/waffle/init_pose/map, 동일 Gazebo GUI+RViz 부하, NO_GOAL**로 구성. `MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA` 및 `Intel` 선택은 실제 `glxinfo -B`의 `D3D12 (NVIDIA/Intel...)`을 검증하고, Gazebo Ogre2 `~/.gz/rendering/ogre2.log` GL_RENDERER 단서를 별도 보존. NVIDIA→Intel 각 1회 순서, 두 번째 전에 첫 실행 SIGSEGV가 남았다면 fail-closed. 같은 실험에서 GPU만 바뀌고 거리만/RTF만/둘 다 개선되는지 4분면으로 비교한다. `GPU_CAUSALITY_PROVEN=false` 강제.

## 3. RED → GREEN 공개 CI

- Student branch `fix/g07-wslg-lidar-vs-rtf-ab-20261118`에서 순수 ROS Clock RTF/거리 분리 6테스트를 먼저 추가. 이전 코드에 `analyze_timing_separately()`가 없어 공개 RED [#44304718412](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44304718412)에서 실제 ImportError.
- 최소 GREEN: 기존 `tools/g07_wslg_no_goal_sensor_probe.py`에 `clock_receipts`와 읽기 전용 `rtf_diagnostics`만 추가. 기존 `assess_window`의 NO_GOAL 판정, 0.75/1.20m CLEAR, Host Scan TTL300ms, 초기 Gazebo/RViz 준비 및 run-owned Cleanup 불변. 공개 6/6 [#44304974780](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44304974780), 실제 Intel 현장 archive의 RTF 미측정을 명시한 비식별 fixture 포함 후 12/12 [#44305669651](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44305669651).
- 공개 비교기 `d06/tools/axia_d06_lidar_rtf_compare.py`: 6 독립 상황(둘 다 회복, RTF만 회복, 거리만 회복, NVIDIA GPU 실측 실패, Intel 역사적 RTF 미측정, 현장 원본)을 검사. 언제나 `moving_goal_approved=false`, `certified_estop=false`, `release=HOLD`.
- 공개 WSL2 A/B 원샷 `d06/scripts/axia_d06_g07_wslg_gpu_rtf_compare_once.sh`: 원본 G07 Owner 20s NO_GOAL 스크립트 SHA+Git blob을 재사용, `glxinfo`에서 실제 두 D3D12 GPU 가용 여부 선행 검사, NVIDIA 다음 Intel 각각 딱 한 번, 원본 archive/SHA 검증 및 동일 world+waffle SDF+초기 pose+map 비교. 센서 unsafe RC3도 유효한 증거로 보존하고 Goal은 절대 발행하지 않음. NVIDIA first case에서 Gazebo SIGSEGV가 발견되면 Intel을 시작하지 않음.
- 공개 Python 16회귀: RTF 6 + 비교 A/B 6 + script immutability/NO_GOAL 3 + 실제 Raw Scan 간격 회귀 1개. Runner source hash와 CI 비WSLg 실행 거부를 검증.

## 4. 실제 Gazebo CI 타이밍에 대한 새 관측 및 정직한 FAIL

- 신규 **실제 NO_GOAL L2** [#44306415620](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44306415620), Student 정확 SHA `f541c36a3984aa65a13de03ef60861103718afb1`: real Gazebo+RViz GUI X11 각각1, 20초 실제 Scan. 최초로 **RTF 0.984428을 ROS Clock host receipt 기반으로 실측**, /safety/scan sim/source **9.998964Hz**, host **9.991273Hz**, 정면1.413879m 측면2.520307m, safety 최대 gap119.380ms. 이 계측은 기존 Linux Xvfb 환경에서 거리 이상도 저 RTF도 관찰되지 않았다는 근거.
- **하지만 이 Run은 FAIL**. Raw `/scan` 세 번째 callback이 0.400119초까지 지연되어 original Scan TTL 300ms 경계 위반. 동시에 /safety/scan은 119.380ms로 정상이고 ROS Clock RTF도0.984428임. 현장 Intel 0.789초 수신 지연을 RTF 하나로 설명해서는 안 되며 **ROS raw callback/DDS 지연이라는 독립 축**을 반드시 측정. `RAW_RECEIPT_TTL_300MS_BLOCKED`로 NO_GOAL/HOLD 유지.
- 이 실제 CI 첫 Raw 지연을 `test_d06_native_raw_scan_ttl_boundary.py`에 0.400119s vs source 0.100s/RTF.984428로 고정. TTL을 0.4s 이상으로 변경하지 않고 ROS RTF 정상이라도 raw gap 위반 시 HOLD 유지. 따라서 이후 시연 안정성은 해당 native L2 GREEN 이전까지 미검증.
- 기존 동일 Student SHA의 **실제 Gazebo+RViz+Moving Goal/CM/Guard/Cancel/Nav2 lifecycle L2** [#44306470216](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44306470216) completed/success, source CM120ms/Guard age150ms/Scan300ms/Contact0/odom dwell1s/UUID cancel/SQLite14/Nav+Loc ACK/CM clean exit0의 전체 21게이트 PASS. Linux 시뮬레이션 증거이며 Owner WSLg acceptance가 아님.

## 5. 판정과 미검증

- 소스 및 기존 퍼블릭 CI L0는 GREEN; 모든 원본과 이전 G07 성공 증거 보존.
- Intel에서 실제 Clock receipt 기반 RTF **NOT_RUN**; NVIDIA D3D12 WSLg A/B **NOT_RUN**. 원본 GPU별 렌더러와 성능의 인과관계는 **UNVERIFIED**.
- 실제 GPU LiDAR 오류 개선이 관찰되더라도 실제 현장 Scanner TTL300ms 및 CM/Guard120/150ms, STOP, 종료 인수가 별도로 통과하지 않으면 Moving L3 인정 금지.
- 읽기 전용 NO_GOAL A/B 스크립트 출고 전 새로운 타이밍 경계 공개 L2의 상태를 확인해야 하며, 미완료/실패 시 출고 후보 `HOLD`.
- `main` 승인 전 병합 금지. 강사 정답은 private, 학생용 TODO는 별도 public. SW Stop은 인증 E-Stop 아님. `AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false`.
