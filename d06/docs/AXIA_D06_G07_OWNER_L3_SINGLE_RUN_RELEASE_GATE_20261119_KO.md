# AXIA D06/G07 — WSL2 NVIDIA NO_GOAL 단일 재진단 출고 게이트 및 회귀 보고서

- 기준: 2026-11-19 · 공개 CI `silverbjin/axia-robot-safety-ci-public`, Draft PR #177, 브랜치 `fix/d06-wslg-lidar-vs-rtf-ci-20261118`.
- 학생 실행 코드 SHA `8e19742fd7bd80db73a37dc7b1d798768dc33e2a`, Student Draft PR #62. main 미병합.
- 외부 WSL2 실행기: `d06/scripts/axia_d06_g07_wslg_gpu_rtf_compare_once.sh`, 구현 commit `58af8370a1ffc178c04807dabcb3c83482fee659`, Git blob `7d0243fb05b6b175b1b4a2ae8442dd27f66923a5`.
- 내부 immutable Owner 스크립트 SHA `3e2e9f2abc694a1183634c06b558efe85e976474` / Git blob `8fa030fd2e87907b758075c7a88b61caa8b9bb42`.
- 공식 Waffle, Nav2, Collision Monitor, Gazebo, Safety TTL Scan300ms/CM120ms/Guard150ms, E-Stop 관련 로직 변경 없음. NO_GOAL, No Twist, No Fault. SW STOP은 인증 E-Stop이 아님.

## 1. 최초 오류와 RED 가설

현장 원본 ZOAgryLW에서 Nav2 navigation/localization ACK, CM child exit0에도 **Gazebo 서버 exit -11** 기록. 공개 실제 Gazebo에서는 센서가 CLEAR지만 Navigation shutdown 응답 TIMEOUT/CM exit -11인 세션도 존재. 즉 `P2_L2_GRACEFUL_TEARDOWN` 부모 마커와 정상 센서 값만으로 전체 native 종료 성공을 보고할 수 없음.

기존 강사 외부 원샷은 센서 성공과 `exit -11` 문자열 부재에 의존하였으며 **Nav2 ACK·CM 자식 실제 exit0·Gazebo 서버 긍정적 exit0의 독립 검사 누락**이 존재했다. 사용자 WSL2 현장 재실행 없이 실제 CI L2 산출물 스키마를 바탕으로 tar fixture를 만들고 먼저 RED 등록.

- `d06/tests/test_d06_owner_full_native_gate.py`: 정상 TAR, CM SIGSEGV, Gazebo SIGSEGV, Nav2 ACK 부재, Raw434ms, 거리 미달, 20초 미달, 관찰자 ACK 누락, 부모 마커만 있는 경우 포함 10건.
- RED [public #44463206946](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44463206946) 의도된 실패: native 전체 안전 게이트 미구현.

## 2. GREEN → REFACTOR → REVIEW → COMMIT

외부 `--nvidia-causal` 단일 실행의 원본 TAR에서 **추가 시뮬레이션 없이** 다음 증거를 직접 확인하도록 수정했다.

1. `native/g07_wslg_sensor_truth.json`: NO_GOAL, 두 토픽 실제 수신 뒤 full 20초 wall-time, Raw/Safety 최대 host receipt gap 각 300ms 이하, 최초 TTL 초과 없음, 모든 Safety CLEAR 및 정적 물리 거리(front > 0.75m, side > 1.20m).
2. `native/g07_ordered_shutdown.json`: navigation/localization ACK true 및 CM이 navigation manager 관리 대상임.
3. `native/g07_shutdown_audit.json`: CM 실제 exit0. `native/launch.log`에서 CM과 Gazebo 서버 **각각** `process has finished cleanly` 확인, 어느 쪽이라도 `process has died` 존재하면 FAIL. "GRACEFUL" 부모 마커만으로 PASS 금지.
4. `native/teardown.txt`의 종료 마커 및 `native/g07_gz_world_pause.log`의 `data: true` 요구.
5. `--nvidia-causal`에서는 `native/g07_witness_probe_complete.signal` + `native/g07_witness_stopped.ack`를 통해 read-only ROS/Gazebo observer가 Lifecycle shutdown 전에 정지했음을 확인.
6. **fail-closed**: `D06_OWNER_NO_GOAL_NATIVE_GATE_BLOCKED=<reason>` 및 비영(非零) 종료 코드. 기존 EXIT trap에서 compact TAR + SHA256 자동 보존.
7. 성공은 `D06_OWNER_NO_GOAL_NATIVE_COMPLETE_CANDIDATE ... NO_MOVING_L3 CERTIFIED_ESTOP=false` **후보**일 뿐 Moving L3 승인 아님.

실제 공개 **GREEN L0 81/81 unittest + Bash self-check** [#44463408367](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44463408367), [canary #44463409784](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44463409784) SUCCESS. 해당 10개 회귀는 tar bytes 직접 파싱을 테스트하며 실제 ROS/Gazebo는 L0에서 실행하지 않음.

## 3. 기존 실제 Gazebo L2 성공 증거 보존

- [Run #44461092763](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44461092763): Raw max142.175ms, Safety max141.016ms, dual-topic20.005초, CLEAR191/191, Nav2 ACK, CM child0, Gazebo server0, 두 관찰기 shutdown 전 ACK.
- [Run #44461627846](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44461627846): Raw max127.526ms, Safety max125.545ms, dual-topic20.003초, CLEAR196/196, Nav2 ACK, CM child0, Gazebo server0, Gazebo/RViz 동일 세션 창 확인.
- 본 외부 판정기 수정은 이미 확보한 실제 L2의 ROS/센서/종료 시퀀스를 변경하지 않음. 검증 수준은 공개 CI L0 신규 81/81 + 기존 독립 Gazebo L2 x2.
- **WSL2 NVIDIA D3D12 실제 현장 NO_GOAL 새 실행 NOT_RUN**. 공개 Xvfb 소프트웨어 렌더링 L2는 WSLg NVIDIA를 보장하지 않음.
- Moving Goal·CM120ms·Guard150ms·Stop/Cancel 안전 통합 테스트 NOT_RUN/기존 증거 별도. `AXIA_MVP_DEMO_ACCEPTED=HOLD` / `D06_GAZEBO_LIVE_RELEASE=HOLD` / `CERTIFIED_ESTOP=false`, **main 미병합**.

## 4. 강사 WSL2 최종 준비 — 정확히 1회 실행

필요한 로그는 스크립트에서 자동 생성하여 압축하고, 기존 Intel 또는 Gazebo 재실행/수동 grep 반복 불필요. WSL2 Ubuntu 24.04에서 GUI가 열리는 원래 환경을 사용.

```bash
(
  set -Eeuo pipefail
  SHA='58af8370a1ffc178c04807dabcb3c83482fee659'
  BLOB='7d0243fb05b6b175b1b4a2ae8442dd27f66923a5'
  SCRIPT="$(mktemp --suffix=.sh)"
  trap 'rm -f "$SCRIPT"' EXIT
  curl -fLsS --retry 3 --max-time 90 \
    "https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public/$SHA/d06/scripts/axia_d06_g07_wslg_gpu_rtf_compare_once.sh" -o "$SCRIPT"
  test "$(git hash-object "$SCRIPT")" = "$BLOB"
  bash -n "$SCRIPT"
  bash "$SCRIPT" --self-check
  bash "$SCRIPT" --nvidia-causal
)
```

결과에 `D06_FORENSIC_ARCHIVE`의 tar.gz와 `D06_FORENSIC_SHA256`의 sha256을 생성. **두 파일만 공유**하면 최초 Scan timing 및 Nav2/CM/Gazebo 원본 shutdown 증거 확인 가능. 실패하면 현장 동일 반복 대신 이 원본부터 공개 CI 회귀 RED→GREEN 수정 후 다시 시도.

최종 강사 WSL2 NO_GOAL 인수가 끝나더라도 **Moving Goal CM120/Guard150ms 노드 간 안전 전달 주기, 안전 TTL 및 정지/취소 실제 시연 조건**이 검증되기 전 전체 MVP 인수는 HOLD. main 병합에는 별도 사용자 승인 필요.
