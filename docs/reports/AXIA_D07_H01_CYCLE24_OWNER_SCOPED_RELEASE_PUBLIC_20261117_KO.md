# AXIA D07-H01 Cycle24 — 공개 CI·Owner WSL2 한정 시연 릴리스 보고

**2026-11-17 / 목적:** TB3 Waffle + Jazzy/Harmonic + 공식 Nav2 `ComputePathToPose` 경로를 실제 Gazebo 장애물 Before→Intrusion→Restored 단계에서 RViz2로 읽기 전용 표시. 강사용 비공개 정답은 포함하지 않음. 안전 인증 또는 실제 움직이는 Goal 시연이 아님.

## 1. 검증된 공개 개발 과정

| CI 테스트 | 결과·의미 |
|---|---|
| 최초 실제 Gazebo L2 [#43866354976](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43866354976) | 공식 Waffle LaserScan→Costmap→ComputePathToPose 3단계 실물 ROS/Gazebo PASS |
| Lifecycle 응답 유실 RED [#43909699852](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43909699852) | 정적 회귀 전 원인 가시화, 의도적 실패 |
| Controlled-no-ACK L0 [#43911609258](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43911609258) | **10 tests PASS**: D07 무주행 범위·연속 Manager+map_server+amcl ACTIVE·fail-close |
| 실제 Gazebo end-to-end [#43912555634](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43912555634) | **PASS**: 공식 Nav2 STARTUP 한 번 실제 실행→CI 전용 클라이언트 응답 결과를 TIMEOUT으로 합성→READONLY ACTIVE 2회 확인→Gazebo/RViz2 Path 3단계; **실제 DDS 유실이 아님** |
| 최종 Owner 원샷 L0 [#43913758909](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43913758909) | **7 tests PASS** + `--self-check`. `NO_ROS_NO_GAZEBO_NO_GOAL` 범위의 정확한 소스 고정 검사 |

## 2. Owner 실제 WSL2 제출본 검토

원본 이름 `d07-h01-owner-kCqVL7Gc.tar.gz`, 사용자 제출 sidecar와 로컬 계산 SHA256 **`9200af2e7d071a683e41e99c05035f5e5f2ddbe75751a7645d67a37b3a138d63`** 일치. 바깥 SHA256SUMS **78/78**, real-l2 **59/59** PASS. **개인 로컬 경로·원본 TAR·XWD·토큰은 공개 저장소에 업로드하지 않는다.**

Owner 스코프 결과: 정상 Localization ACK 2.062342s, Navigation ACK 4.520812s, staged startup `SMOKE_READY`, `P2_L2_SMOKE_RC=0`, 실제 Gazebo obstacle/scan/Costmap·official Path before/intrusion/restored 각각 **52 poses**, 경로 편차 0.3659m, 신규 lethal 92개, 제거 후 최초 master Costmap와 SHA256 일치(잔차 0). `goal_sent=false`, `motion_admitted=false`, `robot_moved=false`. 사용자 실제 시연 성공 관찰.

**범위 제한:** 자동 `D07_H01_OWNER_GUI_VISUAL_HOLD`가 그대로 남으며 Gazebo 픽셀 독립 확인은 미완료(해당 XWD에 RViz 중첩 관찰). 종료 도중 Supervisor의 `publisher's context is invalid` 예외 및 watcher rc=3을 확인했고, clean shutdown PASS로 취급하지 않는다. 실제 RMW 유실 복구·종단 간 Scan→Supervisor→CM/Guard TTL은 미검증. `AXIA_MVP_DEMO_ACCEPTED=HOLD` 유지.

## 3. 범위 제한 본류(main) 병합 계획

공개 검증 브랜치와 main은 **971 commits ahead / 280 behind**로 갈라져 있어 전체 G07/P3 기능 체인을 병합하지 않는다. 최신 main에서 `release/d07-h01-classroom-main-20261117`을 만들고 정확하게 아래 세 파일만 공개 이력에 반영한다.

1. `scripts/axia_d07_h01_gpu_gui_owner_wsl2_once.sh` — 검증된 원본 SHA `f3d203612800d06c3be922cc3cd707e0bba78825`와 **내용/Blob SHA 동일**, private source `5376fbf15acc6d6539b99f5387bbfade04f7ee62`를 checkout. ROS_DOMAIN_ID와 WSLg GPU preflight가 포함된 기존 단일 원샷.
2. `tests/test_axia_d07_gpu_gui_owner_contract.py` — 위와 동일 검증 소스의 정적 테스트(7개).
3. `docs/reports/AXIA_D07_H01_CYCLE24_OWNER_SCOPED_RELEASE_PUBLIC_20261117_KO.md` — 이 범위·증거·보류 항목만 문서화.

CI 재검용 워크플로 1개를 추가하는 경우도 공개 L0 한정이며, 민감한 Instructor 소스는 sealed 환경에서 exact SHA 조회 후 제거한다. **본류에 private 코드·정답·moving Goal 스크립트 추가 금지**. 예전 owner/source SHA는 변경하지 않는다.

## 4. 실행 방법과 기대 출력

```bash
(
  set -Eeuo pipefail
  SHA="f3d203612800d06c3be922cc3cd707e0bba78825"
  SCRIPT="$(mktemp --suffix=.sh)"
  trap 'rm -f -- "$SCRIPT"' EXIT
  curl -fL --retry 3 -sS "https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public/$SHA/scripts/axia_d07_h01_gpu_gui_owner_wsl2_once.sh" -o "$SCRIPT"
  bash -n "$SCRIPT"
  bash "$SCRIPT" --self-check
  bash "$SCRIPT" --run
)
```

정상 조건: `AXIA_D07_H01_OWNER_PRIVATE_SOURCE_VERIFIED`, `D07_H01_GUI_WATCHER_SPAWN_ACK_VERIFIED`, `D07_H01_GUI_H01_GEOMETRY_RETURNED_NO_GOAL`, `P2_L2_SMOKE_RC=0`. 자동 GPU 픽셀 L3는 원본의 보수적 HOLD를 유지한다.

## 5. 릴리스 판정

**D07-H01 읽기 전용 강의 시연 실제 Owner 로봇 센서·공식 계획 경로 한정 PASS.**  
**GUI 자동 픽셀, 자연 발생 서비스 응답 유실, 종료 clean shutdown, Scan 종단간 TTL, 이동·정지·접촉 회피, 인증된 HW E-Stop: 미검증.**  
**전체 AXIA MVP: HOLD.** GitHub main 병합은 사용자의 명시 승인에 의해 위 선택 파일에 한정하며, 안전·이동 기능 범위 확대 금지.
