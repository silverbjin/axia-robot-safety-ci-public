# AXIA G07 Cycle37 — Owner WSLg GUI만 선검수하는 1회 NO_GOAL 원샷

작성일: 2026-11-17 KST. **자동 GUI 검증 완료 ≠ WSLg 실제 픽셀 확인 ≠ 최종 G07 L3 인수.**

## 결론과 분리된 기준

- **CM 전달 간격 120ms**는 Moving Goal의 **공개 CI 출고 여유 기준**. GUI World·3D 렌더링·RViz2 관찰에 필요한 선행 조건이 **아님**. 150ms Guard hard TTL도 GUI-only에서 합격으로 주장할 수 없음.
- GUI-only는 Goal·물리 장애물 이동·`/cmd_vel` 외부 publisher를 실행하지 않으므로 CM 120ms 판단을 아예 수행하지 않음.
- GUI-only 확인 대상: 공식 Jazzy/Harmonic Waffle/World, 정확히 1개의 무조건적 SceneBroadcaster, optional `state_hertz=25`, live `/world/default/scene/info`, `/world/default/pose/info`, 분리된 `gz sim -g`와 RViz2 실제 WSLg 표시.
- 프라이빗 Instructor HEAD는 개발 보고서 수정으로 변할 수 있으므로 **실제 GUI 기능 pin `966886c4627deb2bb3b37111fe336eeee6b9ebb4`** 고정. 이 SHA에서 GUI-only L2 성공함. public GUI `352ea7c2197b937e8566ba90cd4d8fff46dd9f88`, read-only RViz `0f66059d9110f8e667200bbca22396bd0c78c02e`.

## 실측 검증 표

| 단계 | 원본 | 결과 | 권한 / 범위 |
|---|---|---|---|
| 신규 GUI-only 실제 Gazebo L2 | [Public CI #43900946956](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43900946956), workflow SHA `2d35c673b20586fa1f113585503737be5170b7fd` | **PASS** | 4 legacy tests + 5 rollback tests + 8 Instructor Scene tests + 4 Marker tests; real World/Waffle, scene+pose, Gazebo GUI+RViz Xvfb, no Goal |
| Owner WSLg 실행기 L0 | [Public CI #43902040357](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43902040357), private/visual/CI source locked | **PASS** | 쉘 구문, `--self-check`, 명령·Goal 미전송·출고 기준 분리 정적 계약; **ROS·WSLg 미실행** |
| Owner WSLg 실제 3D 화면 | 강사 WSL2에서 아래 실행 후 사람이 화면 확인 | **NOT_RUN** | GUI-only 시각 검수; 실제 WSLg 픽셀 자동 검증 아님 |
| CM 120ms Moving Goal 출고 여유 | GUI-only 실행에서 검사하지 않음 | **NOT_TESTED** | 마지막 Moving L2 #43898345608 CM 약 128.319ms >120ms, **HOLD 유지** |

실제 GUI-only L2 원본 성공 메시지:
```text
AXIA_G07_C37_SESSION_SCENE_SOURCE_SHA256_VERIFIED
AXIA_G07_C37_REAL_XACRO_HEADLESS_SCENE_BROADCASTER_CONFIRMED
AXIA_G07_C37_REAL_GAZEBO_WORLD_WAFFLE_SERVICES_PASS_NO_GOAL
AXIA_G07_C37_REAL_GAZEBO_SCENE_POSE_TRANSPORT_TOPICS_CONFIRMED_NO_GOAL
AXIA_G07_C37_WSLG_PREGATE_ACTUAL_GUI_SCENE_25HZ_CI_SOURCE_PROVEN_NO_GOAL
AXIA_G07_C37_GUI_PRECHECK_REAL_GAZEBO_RVIZ_XVFB_L2_PASS_OWNER_WSLG_PIXELS_NOT_VERIFIED_NO_GOAL
AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false
```

## 사용자 WSL2 단일 실행 명령

원샷 공개 소스 자체를 SHA `ccf3abed7d59e3bdca5aba1e47bad46762883b6a`로 고정한다. 공개 release 브랜치가 앞으로 변경돼도 실행 내용은 불변.

```bash
(
  set -Eeuo pipefail
  SHA="ccf3abed7d59e3bdca5aba1e47bad46762883b6a"
  SCRIPT="$(mktemp)"
  trap 'rm -f -- "$SCRIPT"' EXIT
  curl -fL --retry 3 -sS \
    "https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public/${SHA}/scripts/axia_g07_cycle37_gui_only_wslg_precheck_once.sh" \
    -o "$SCRIPT"
  bash -n "$SCRIPT"
  bash "$SCRIPT" --self-check
  bash "$SCRIPT" --admission-check
  bash "$SCRIPT"
)
```

- Ubuntu24.04 WSL2, Jazzy/Harmonic, 기존 `gh auth login` 권한·WSLg DISPLAY가 필요. 설치/소스 업그레이드 없음. CI에서 source SHA·실제 GUI L2 출처를 고정 조회.
- **Nav2 Goal을 생성하지 않음.** 공식 launch는 `autostart:=false`; 별도 `p2_g07_shared_staged_startup.sh`, `p2_owner_l3_wsl2.sh` 및 장애물 이동 로직은 호출하지 않음.
- 화면을 확인할 때 Gazebo 3D World/로봇/장애물/Entity Tree, RViz2 창/가능한 LaserScan을 확인. 로봇 이동이나 Nav2 path는 요구하지 않음.
- 정상 표시된 경우에만 `YES-G07-GUI-VISIBLE` (Goal 승인이 아닌 **화면 관찰 확인 문자열**) 1회 입력; 실패하면 Enter만 누르고 **HOLD**. 스크린샷은 표시 중 Windows Win+Shift+S로 사용자가 캡처 가능.
- 실행 종료 시 `~/axia_g07_c37_gui_evidence_XXXXXXXX` 폴더와 `SHA256SUMS`, `G07/g07_gui_scene_world_manifest.json`, `G07/c37_scene_topics_pregoal.txt`, `G07/gz_services.txt`, `visual/display_attestation.json`, `visual/gz_gui.log`, `visual/rviz.log`, `visual/gui_user_observation.json` 및 `G07/launch.log` 보존. 비공개 원본 GitHub 업로드 금지.
- 비정상 시 **같은 현장 명령 반복 금지**. 최초 실패 메시지와 `EVIDENCE` 폴더를 먼저 분석하고 재현 가능한 부분만 공개 CI RED로 편입한다.

## 검증 상태·브랜치

- 공개 스크립트: `scripts/axia_g07_cycle37_gui_only_wslg_precheck_once.sh`, SHA `ccf3abed7d59e3bdca5aba1e47bad46762883b6a`.
- 공개 L0: `.github/workflows/axia-g07-cycle37-owner-gui-only-precheck-static-l0.yml`, Run #43902040357.
- 공개 실제 L2: `.github/workflows/axia-g07-cycle37-owner-wslg-gui-pregate-l2.yml`, Run #43900946956.
- 현재 개발용 공개 브랜치: `release/p2-g06-cm-ttl-20261110`; main 병합 없음. 비공개 Instructor 기능 원본/강사 답안 분리 유지.
- **WSLg 결과는 사용자 입력/원본 증거가 있을 때만** `GUI_WSLG_USER_VISUAL_CONFIRMED_NO_GOAL_NOT_FORMAL_L3`; GUI receipt·CI Xvfb만으로는 확인 아님.
- `AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false`, Owner Moving L3 미실행, Scan/CM/Guard safety release 미검증.
