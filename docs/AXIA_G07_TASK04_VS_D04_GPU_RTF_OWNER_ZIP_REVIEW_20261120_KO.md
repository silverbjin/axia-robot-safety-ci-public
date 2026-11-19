# AXIA G07 Task04 vs D04 — Owner WSL2 RTF 90%/20% 비교 분석

**분석일:** 2026-11-20 KST  
**범위:** 사용자가 제공한 ZIP 2개, 실행 명령, 공개 저장소의 실행기 소스.  
**원칙:** 사용자 GUI RTF 관찰값과 ZIP의 계측값을 혼동하지 않는다. 안전 프로세스/물리 시연을 재실행하지 않는다.

## 1. 원본 ZIP 검증

| 항목 | 첫 번째(약 90% 사용자 관찰) | 두 번째(약 20% 사용자 관찰) |
|---|---|---|
| 원본 파일 | `axia_wsl2_gazebo_rtf_gpu_audit.zip` | `axia_wsl2_gazebo_rtf_gpu_audit(1).zip` |
| ZIP SHA256 | `c6c5c4a0ba8c42c3ddd35d27cee1b4e35702b54071cac903c4cb6e2f88d13505` | `236e9bfeec598dd70eea9537cf9a6f77a6dd55eca20e7b68874c317f5f47a064` |
| 내부 SHA256SUMS | 7/7 일치 | 7/7 일치 |
| 측정 상태 | `NO_UNIQUE_GAZEBO_PARTITION` | `NO_UNIQUE_GAZEBO_PARTITION` |
| 실구간 RTF (ZIP) | `null`, 샘플 0 | `null`, 샘플 0 |
| `/world/.../stats` 원본 | 없음 | 없음 |
| 기본 glxinfo | D3D12 Intel Iris Xe | D3D12 Intel Iris Xe |
| NVIDIA 강제 glxinfo | D3D12 RTX 2060 Max-Q | D3D12 RTX 2060 Max-Q |
| 순간 nvidia-smi GPU | 17%, 289MiB | 1%, 65MiB |
| CPU pressure some avg10 | 82.45% | 47.69% |
| 메모리 available | 29,287,668 KiB | 29,449,980 KiB |

**판정:** 두 ZIP은 GPU 환경 차이의 증거이지만 90%/20% RTF의 독립 실측 증거는 아니다. CPU pressure는 CPU 사용률이 아니라 최근 10초에 CPU 대기로 영향을 받은 시간 비율이며, NVIDIA 순간 사용률도 평균 비교 지표가 아니다.

## 2. 대상 프로세스와 기존 세션 간섭

첫 번째 ZIP에서 서버 후보가 2개 감지됐다.

- 이전 세션 후보: PID 5805, domain 86 / partition `axia_p2_task04_86_5212_1795096446`, `LIBGL_ALWAYS_SOFTWARE=1`.
- 현재 GUI와 결합한 서버 후보: PID 13700, domain 46 / partition `axia_p2_task04_46_13387_1795100570`, `LIBGL_ALWAYS_SOFTWARE=1`.
- 이 partition과 일치하는 Gazebo GUI PID 14492 및 RViz2 PID 14493은 `GALLIUM_DRIVER=d3d12` + `MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA`.
- 별도 과거 RViz2 PID 4861이 다른 G07 partition으로 남아 있었다.

두 번째 ZIP:

- 과거 G07 서버 PID 5805와 RViz2 PID 4861이 그대로 감지된다.
- D04 대상 서버 후보 PID 15603, partition `axia_d04_student_15441_40`, domain 40. GPU 강제 환경값 없음.
- 동일 partition에서 Gazebo GUI wrapper 2개, YOLO 관련 프로세스 2개, image_view 관련 프로세스 2개, ROS launch가 감지된다.
- GLX 자식에서는 기본 Intel, NVIDIA 명시 시 RTX 2060이 확인되지만 실제 D04 서버 Ogre2 하드웨어 GPU를 측정한 것은 아니다.

**의미:** CPU/GPU 경쟁이 가능한 과거 세션이 남아 있으며, 진단기가 임의로 오래된 서버를 택하지 않도록 했던 기존 fail-closed 처리 자체는 옳다. 다만 동일 partition의 활성 서버와 GUI가 유일하게 짝지어지는 경우에도 측정을 차단한 것이 이번 계측 실패의 직접 원인이었다.

## 3. 실행기 코드 대조 — 동일한 시뮬레이션 부하가 아님

**첫 번째**: 공개 CI SHA `6cfe6a51102d9a45420fa4f9ad4e9600130a7c56`, `scripts/axia_g07_task04_owner_moving_l3_once.sh`.

- 재사용 Student SHA `954fc2f054c50df783bc81c4d0835a6ee6f8645d`.
- 공식 Nav2·LiDAR·CM·Guard·물리 장애물·Moving Goal 시나리오.
- Gazebo 서버는 `LIBGL_ALWAYS_SOFTWARE=1`; GUI와 RViz2만 NVIDIA D3D12를 opt-in한다.
- 이것은 성능 튜닝만이 아니라 이전 WSL2 gpu_lidar 스캔 이상을 회피하는 **안전 시연 데이터 유효성 제약**이다. D3D12를 서버에 일괄 적용하면 안 된다.

**두 번째**: Student `main` / `block_B/day04/run_student_gazebo_yolo_once.sh`.

- Waffle Pi RGB 카메라(640×480), 사람 visual Actor, C++ YOLO, 별도 `image_view` GUI를 사용한다.
- 공식 Nav2의 Gazebo 서버는 상위 셸의 GPU 환경을 상속한다. 기본 모드에서 NVIDIA 강제 설정은 없다.
- RGB/YOLO 렌더링 및 프레임 처리 비용이 첫 번째 시나리오와 다르다.

**현재 가능한 결론:** 90%와 20%는 동일 월드/동일 센서를 GPU만 다르게 하여 측정한 값이 아니므로 단순 NVIDIA/Intel 성능 비교로 해석할 수 없다. D04의 영상 렌더링·YOLO·중복 GUI 및 잔존 세션이 유력한 조사 지점이나 인과 비율은 미검증이다.

## 4. 실험 범위를 늘리지 않는 최소 수정

다음만 조정한다.

1. `choose_server`가 서로 다른 partition의 서버가 2개 이상 있어도, 현재 GUI와 **같은 GZ_PARTITION으로 유일하게 결합한 서버 1개**를 선택한다. 같은 partition의 GUI wrapper는 중복으로 보지 않는다.
2. 동시 활성 GUI-server partition이 2개 이상이면 자동 선택을 계속 거부한다.
3. G07 진단에서 무관한 최근 D04 SDF를 'G07 RGB-D'라고 잘못 기록하지 않는다. D04의 RGB 카메라 update_rate와 이미지 해상도는 실제 센서가 아닌 **디스크 후보**로만 수집한다.
4. 두 실행기 ZIP 비교 결과에 각 partition의 활성 YOLO / image_view 프로세스 수 및 RGB 카메라 주기 후보 차이를 추가한다.

**검증:** 공개 L0 회귀 테스트로 첫 ZIP과 둘째 ZIP의 프로세스 배치를 축약 재현한다. 실제 Gazebo/WSL2 성능 개선과 실센서 TTL을 CI L0 PASS로 승격하지 않는다.

## 5. Owner 다음 1회 증거 수집

각 실행기마다 기존 Gazebo GUI를 유지한 채 별도 터미널에서 최신 공개 진단기 사용:

```bash
env -u GZ_PARTITION python3 "$HOME/axia_gpu_rtf_diagnostics/bin/axia_wsl2_gazebo_rtf_gpu_audit_5d428e1a.py" --seconds 20
```

- 첫 실행기에서 ZIP A를 만들고 종료한 뒤, 두 번째 실행기에서 ZIP B를 만든다.
- 출력 `AXIA_RTF_GPU_AUDIT_CAPTURE_STATUS=CAPTURED` 및 `AXIA_GAZEBO_INTERVAL_RTF_PERCENT=` 실제 수치 확인.
- 둘 다 실행 시 CPU/WSLg 경쟁이 생길 수 있으므로 동시 시연은 금지.
- ZIP 재수집 후 비교하되, 동일 조건/작업량이 아니라는 경계는 계속 유지한다.

**미검증:** Owner WSL2 신규 RTF, 실제 Gazebo 서버 Ogre2 GPU 장치, 실제 RGB/YOLO/Scan 타이밍, CM/Guard TTL, certified E-Stop. **main 병합 사용자 승인 전 HOLD**.
