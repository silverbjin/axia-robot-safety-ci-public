# AXIA G07 Scan300 — 공개 CI 2/2 통합 PASS 및 강사 WSL2 L3 원샷 출고 근거 (2026-11-21)

## 판정
- `PUBLIC_CI_L0=PASS`, `PUBLIC_CI_L2=PASS_TWO_STRICT_REAL_GAZEBO_MOVING_GOALS`.
- `WSL2_PERFORMANCE_PREFLIGHT=NOT_RUN_NEW_SOURCE`; `OWNER_WSL2_L3=NOT_RUN`.
- `FIRST_SCAN_ROOT_CAUSE=CAUSE_UNDETERMINED`; `CERTIFIED_ESTOP=false`; `MAIN_MERGED=false`.
- **출고는 단 한 번의 강사 WSL2 조건부 L3 인수 실행기만 의미**합니다. 실제 NVIDIA WSLg에서 성공했다고 주장하지 않습니다.

## 재현 기준
기존 강사 `e96rL7BT`의 최초 Wall Scan gap 317.942691ms/최대 378.410075ms, 같은 LaserScan 헤더 Sim delta 102ms, 독립 bag /scan 약322.262ms와 /safety/scan 약320.522ms, 해당 구간 RTF 추정 약0.41. Gazebo-native publish monotonic pair 및 브리지 지연 분리는 근거 부족으로 보류합니다. 원본 bag은 비공개 강사 WSL2에만 보존합니다.

## RED → GREEN 증거
- Scan Wall/Sim 최초 증거 fixture: 공개 RED [#44762376515](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44762376515) → GREEN [#44762793950](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44762793950).
- 12초 Goal 전 읽기 전용 Scan/Clock/Odom 안전 사전검사: [GREEN #44772151429](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44772151429); 전역 최초 Clock/Odom/Scan 헤더 쌍 보존 RED [#44774575734](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44774575734) → GREEN [#44774786552](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44774786552).
- 독립 rosbag 최초 Scan 쌍 분석기 및 Clock/Odom 수신간격 fallback: RED [#44831132404](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44831132404) → GREEN [#44831224337](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44831224337), read-only L0. **해당 추가 진단기는 아래 실 Gazebo L2가 사용한 커밋 이후에 추가되었으므로** 그 실 Gazebo 실행 범위로 소급하지 않습니다.
- 첫 위반 numeric evidence 누락: RED [#44830833291](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44830833291) → 실 L2 동일 candidate에서 GREEN [#44830955961](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44830955961).
- Owner 원샷 진단 실행의 **이중 역슬래시로 인한 쉘 줄 연결 오류**: RED [#44831590025](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44831590025). 다음 GREEN은 출고 브랜치 HEAD의 공개 Owner L0 결과로 확인해야 합니다.

## 공식 실물 Gazebo L2: [Run #44830956042](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44830956042)
- 공개 Workflow SHA `a54c40c630b14bc2b71449f3030c5c194a5f8408`.
- Student 정확 SHA `891bf65349cf8dfb203bb8b97ffe0346b3fb8b3f`.
- **Cycle 1 PASS:** Native Moving runner RC0, RViz/Gazebo 2창, NO_GOAL 12s 검사, Scenario Move CLEAR→SLOW→STOP, Goal cancel, Guard·Supervisor child exit0, Navigation+Localization Lifecycle ACK, Numeric safety gate; Moving Scan 최대181.910519ms, Odom136.398468ms, Clock86.051518ms, Guard64.589735ms, 내부 CM age 최대22.406487ms. Nav Shutdown ACK 응답 1.952467s.
- **Cycle 2 PASS:** Native Moving runner RC0, GUI 2창, 같은 안전/취소/종료 계약; Moving Scan 최대218.790490ms, Odom137.430474ms, Clock110.143598ms, Guard72.016387ms, 내부 CM age 최대28.356359ms. Nav Shutdown ACK 응답 2.369993s.
- 같은 세션 Goal 전 RTF 추정 0.998837 / 0.999604. **강사 WSLg RTF~0.41 사건은 CI에서 재현된 것이 아닙니다.**
- 실제 Run은 독립 NVIDIA WSLg가 아닌 Ubuntu 24.04 Xvfb/Gazebo Harmonic 공식 Nav2입니다. 외부 GPU/호스트 성능 인증으로 확대 금지.
- software Stop은 인증된 물리 E-Stop이 아닙니다.

## 코드 및 권한
- 공개 개발 브랜치 `fix/g07-wsl2-first-scan300-20261121`, Draft PR [#207](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/207).
- 학생 개발 브랜치 `fix/g07-scan300-owner-pregoal-20261121`, Draft PR [#75](https://github.com/silverbjin/axia-robot-safety-student/pull/75).
- Owner WSL2 실행기 `scripts/axia_g07_stabilization_wsl2_final_once.sh`는 최초 GitHub API로 위 Run의 `id/head_sha/name/status/conclusion` 및 정확히 2개 matrix job 모두 success를 확인해야만 시뮬레이션 진입을 허용합니다. Rate-limit/403 포함 API 장애는 fail-closed, Goal 금지.
- 12초 같은 세션 NO_GOAL 검사에서 Scan300, Clock300, Odom300의 실제 수신 간격 위반이 발생하면 **TTY 승인·Goal 전에 HOLD**. 시연 중 Guard150/CM120, Scan300/Clock300/Odom300 및 원래 Stop/Cancel 계약 유지, 완화 없음.
- 원본 WSL2 tar/rosbag은 로컬 보존, 소형 6파일 JSON ZIP은 8MiB 상한 및 SHA256 기록. 강사 인증 L3 결과가 나오기 전에는 공식 인수 PASS를 발행하지 않습니다.

## 검증 명령
```bash
python3 -m unittest discover -s tests -p 'test_g07_scan300_owner_wrapper.py' -v
python3 -m unittest discover -s tests -p 'test_g07_stabilization_wsl2_release.py' -v
bash -n scripts/axia_g07_stabilization_wsl2_final_once.sh
bash scripts/axia_g07_stabilization_wsl2_final_once.sh --self-check
```

## 주의
1. 현장 단일 L3 시도에서 새 오류가 발생하면 **최초 전이·최초 타이밍 간격만** 로컬에서 가져와 공개 최소 숫자 회귀 RED→GREEN 이후 재출고합니다. 동일 현장 재시도 루프 금지.
2. 실제 사용자 Windows/WSL2 NVIDIA WSLg, GPU LiDAR 서버 렌더러, 최초 Scan RMW 지연의 인과분리는 미검증입니다. 공식 Nav2를 수정하지 않습니다.
3. `main` 병합은 별도 사용자 승인 전까지 금지합니다.
