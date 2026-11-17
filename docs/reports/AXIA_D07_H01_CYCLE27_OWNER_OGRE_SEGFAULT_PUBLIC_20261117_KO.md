# AXIA D07-H01 Cycle27 — Owner WSLg Ogre SIGSEGV 139 공개 수정 보고

**범위:** ROS 2 Jazzy / Gazebo Harmonic / 공식 Nav2 / Waffle **No-Goal GUI 시연만**. 이동 명령, Safety Supervisor/CM/Guard/TTL 미변경.

## 최초 원인과 증거

- Owner zoKAxNwF 원본 SHA256: **7ebd99abb525301237f3e9979a55fb3a0c517b638027b16cf5d93298a45416d2**. manifest 77/77, real-l2 60/60 PASS. 원본 개인 파일 및 WSL2 경로는 공개 저장소에 올리지 않음.
- **첫 치명 오류:** Gazebo GUI gz sim -g가 OGRE-Next GL3Plus → Mesa Gallium 26.2.6 → WSL D3D12/NVIDIA 경로에서 native SIGSEGV 139. Watcher rc3, 이어서 RViz Path subscription absence / geometry BLOCKED / cleanup blocked. 원인과 후속 증상을 구분.
- 같은 GPU/Mesa D3D12 스택으로 과거 여러 번 성공한 증거가 있으므로 특정 업그레이드 단정 금지. 당시 소프트웨어 glxinfo에서 llvmpipe 별도 확인, RAM 부족 증거 없음.
- 구 Owner first failure parser가 WATCHER_PROCESS_ENTERED(단순 시작 정보)를 장애로 인식하던 false-priority 문제도 정정.

## 최소 기능 수정

- Private watcher 기능 SHA: **7306b27bc1d146d99d1657308549db45c9878407**. 새 Owner flag AXIA_D07_H01_OWNER_GZ_SOFTWARE_ONLY=1은 **Gazebo GUI에만** LIBGL_ALWAYS_SOFTWARE=1, unset GALLIUM_DRIVER/adapter 지정. RViz D3D12 유지, Gazebo 서버/Nav2 그대로. No-Goal+SIM-only+격리 partition 외에는 작동 안 함.
- CI software mode와 Owner software mode 충돌 금지. 새 first child PID/rc139 marker를 가장 먼저 기록. 종료 이후 자동 재실행 및 허위 성공 없음.
- 공개 launcher scripts/axia_d07_h01_gpu_gui_owner_wsl2_once.sh는 새 모드를 자동 적용, startup info를 first error로 고르지 않음. 이전 성공 실행기 SHA 보존.

## RED→GREEN CI 검증

| 구간 | Run | 결과 |
|---|---|---|
| 원본 Renderer RED | [#43997380644](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43997380644) | 신규 5개 중 3개 의도 FAIL |
| Renderer GREEN | [#43997532528](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43997532528) | 5 신규 + 9 기존 = **14 PASS** |
| 실제 Jazzy/Gazebo Xvfb L2 | [#43997663084](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43997663084) | 실제 공식 Nav2 Path 3단계, 소프트웨어 Gazebo GUI, ordered ACK, 네 자식 exit0 **PASS** |
| Owner 오류 우선순위 RED | [#43997806884](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43997806884) | 소프트웨어 flag 미적용 예상 FAIL |
| 새 Owner 실행기 GREEN | [#43998138463](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43998138463) | 5 public tests + hash + --self-check **PASS** |

L2 실제 출력:
- AXIA_D07_C27_GUI_REAL_OWNER_RUN_RC=0
- AXIA_D07_C27_REAL_GAZEBO_NAV2_PATH_L2_PASS_NO_GOAL
- AXIA_D07_C27_REAL_SUPERVISOR_CHILD_EXIT0_AND_P4_ORDERED_ACK_L2_PASS
- AXIA_D07_C27_REAL_TEARDOWN_VERDICT_CHILD_PROOF_PASS

## 검증 제외

CI Xvfb는 WSLg D3D12 장치를 제공하지 않으므로 **Owner WSL2 혼합 Gazebo llvmpipe + RViz D3D12 실제 구동은 미검증**. 렌더 소프트웨어 CPU 부담이 Scan 안전 TTL에 미치는 영향도 UNVERIFIED. 인증된 E-Stop 또는 실제 Goal 인수는 아님. **AXIA_MVP_DEMO_ACCEPTED=HOLD**.

**검증된 실행기 및 테스트:** 공개 기능 브랜치 fix/d07-h01-owner-wslg-gz-software-c27-20261117, Instructor runtime SHA 7306b27bc1d146d99d1657308549db45c9878407. Main 병합 전 사용자 승인 필요. 실패 증거를 보존하고 새 현장 오류는 최초 프로세스/TTL 경계부터 CI 재현.
