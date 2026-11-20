# AXIA D08 — Owner Gazebo 빈 장면·8번째 Scan 수신 공백·경량 증거 보존: 원인 분석과 공개 CI 인수 보고서

- 일자: 2026-11-18 KST
- 공개 CI: silverbjin/axia-robot-safety-ci-public, PR #166, `feat/d08-unified-sensor-cm-path-20261118`
- 현장 출발 소스 SHA: `e48b7124bd8e01bdc9f80631f65a69dbbc6742c1`
- 최종 공개 CI 검증 소스 SHA: **`81487f00ff9c20f2bc4e503548d43803297acc85`**
- 범위: D08 교육용 **NO_GOAL** Gazebo Harmonic + Waffle + ROS 2 Jazzy + 공식 Nav2 읽기 전용 경로. 실제 움직이는 Goal/로봇 cmd_vel 및 인증 E-Stop은 **실행하지 않는다**.

## 1. 현장 원본과 최초 오류: 뒤의 종료 오류와 혼동하지 않는다

업로드 `run_20261118T113915Z_FXDexn.zip`: 원본 SHA256 `4f0f731a0f4ad03178fdb8771204de0991ecc42f49e8dd5234971a11e207d3c1`. 3,457 항목, 압축 171,950,602 B (164.0 MiB), 해제 약 327.6 MiB. 자료에는 공식 Nav2 첫 실제 Path 14 points / 0.4 m, AMCL/TF2 localization, Collision Monitor inactive→active, 실제 640×480 RGB-D, YOLO/D05 수신과 최초 3-phase Path PASS가 남아 있다. Owner 반복 cycle 0000~0006 **7회 PASS**, cycle **0007**에서 첫 안전 타이밍 위반:

```
D08_FIRST_REAL_SCAN_RECEIVE_GAP_OVER_500MS
{"index":24,"gap_sec":0.546644}
```

500ms 안전 수신 경계를 실제로 초과했다. 이를 지우거나 안전 TTL을 변경해 통과시키지 않는다. 당시의 ROS Scan source header 간격이 기록되지 않았기에 해당 **546.644ms host gap**이 Gazebo 센서 발행 자체, ROS bridge DDS, Executor 지연, WSLg GPU/스케줄링 중 어디에서 발생했는지는 **증명되지 않았다**. 시작 단계의 Clock 관측 RTF 0.772788만으로 특정 시점의 원인을 특정할 수 없다.

이후 원본 Launch 종료 로그의 Gazebo server exit -11, RViz exit -6, `/tmp/nav2_*.sdf` 누락은 **첫 안전 위반 뒤 teardown에서 나타난 2차 오류**다. 이번 변경으로 WSLg Ctrl+C 안전 종료까지 검증했다고 보고하지 않는다.

## 2. 빈 GUI의 구조적 원인 확정

실제 현장 생성물 `live_evidence/actual_world.sdf`에는 Physics, UserCommands, Sensors 및 Contact plugin과 실제 model은 존재하지만 **SceneBroadcaster가 0개**였다. 상류 공식 Nav2 world Xacro에서는 `<xacro:arg name="headless" default="true"/>`와 `<xacro:unless value="$(arg headless)"> ... SceneBroadcaster ... </xacro:unless>`로 장면 방송 플러그인을 조건부 포함한다. 기존 D08 코드가 공식 Nav2 launcher에게 이미 확장된 SDF를 넘기기 전 `xacro world.sdf.xacro`를 **인자 없이** 실행했다. 따라서 `headless=true` 기본값으로 장면 방송이 제거됐다. 그 후 공식 Nav2의 `headless:=False`는 이미 제거된 플러그인을 복원하지 못한다.

ROS Scan, RGBD, 실제 Costmap/Path가 모두 정상 동작하면서 GUI의 3D 모델과 Entity Tree만 비어 보인 관찰을 이 원인이 일관되게 설명한다.

공식/유사 사례:
- Gazebo Architecture: https://gazebosim.org/docs/harmonic/architecture/ — SceneBroadcaster는 서버 world state를 GUI frontend로 보낸다.
- Gazebo Issue #2962: https://github.com/gazebosim/gz-sim/issues/2962 — SceneBroadcaster 미가동 시 빈 viewer.
- Nav2 official Jazzy source: https://api.nav2.org/nav2-jazzy/html/tb3__simulation__launch_8py_source.html — Xacro headless 조건.
- Nav2 issue #5350: https://github.com/ros-navigation/navigation2/issues/5350 — 임시 World SDF/GUI와 lifecycle 실행시 차이.

이 문제는 앞서 D07-H01에서 조사했던 headless Xacro + GUI-only 상태 누락과 같은 경계다. 다른 Ogre2 / GPU 문제가 **추가로 없다는 뜻은 아니며** 실제 WSLg 화면 확인은 L3에서 수행한다.

## 3. 최소 구현

- `d08/scripts/d08_public_gazebo_l2.py` — D08에서만 pre-expanded World Xacro에 `headless:=false`를 명시하여 단일 `gz::sim::systems::SceneBroadcaster`를 보존. Nav2/ROS 설치 파일 변경 없음. 진짜 `/world/default/scene/info` service의 응답에서 `axia_d08_ci_waffle`, `axia_p2_g07_obstacle` 모델 존재 검사. GUI window/process만 떠 있어도 모델 누락이면 BLOCKED.
- `d08/harness/d08_scene_broadcaster.py` — 최종 SDF의 장면 broadcaster 0/2개, 이름/filename 불일치 FAIL-CLOSED; 실제 native model list 판정. Pixel/WSLg PASS로 승격하지 않는다.
- `d08/harness/d08_same_world_replan.py` — 기존 첫 host Scan gap과 함께 실제 ROS source header sim-time gap, 이전/현재 stamps 기록. 이는 원인 분류 증거이고 sensor.publisher/RMW 간격은 별도 미계측으로 명시. 500ms Scan 한도 불변.
- `d08/scripts/d08_public_gazebo_l2.py` / 공식 Nav2 CI job — `--ci-owner-repro`는 `GITHUB_ACTIONS=true`, Xvfb, NO_GOAL에서만 허용. 단일 기존 Gazebo server에 GUI-only client `gz sim -g` 하나 연결 후 **8회 연속 기존 3-phase physical replan 관찰기 재사용**. 어느 회차든 Scan gap >500ms, CM/Costmap/Path 실패, GUI client 종료 시 fail-closed.
- `d08/scripts/d08_compact_evidence.py` / `d08/scripts/d08_owner_no_goal_bootstrap.sh` — Owner 완료 및 실패 종료 때 private 경량 진단 ZIP과 SHA256 파일을 자동 생성. 모델/ONNX Runtime NuGet/YOLO build/install/.git/checkout 전체를 archive에 넣지 않는다. 첫 성공·최종 성공·최초 실패 cycle, 실제 World SDF, Scan/AMCL timing, Scene service proof, verdict, error-context 로그/필요한 앞뒤 로그와 SHA256SUMS만 보존. 원본 실행 폴더는 안전을 위해 자동 삭제하지 않는다.
- `d08/tests/test_d08_owner_blank_scene_and_compact.py` — 과거 누락 plugin RED, duplicate plugin 차단, 실제 모델 없는 scene 거부, 원본 Scan gap 546.644ms host-vs-source 이력, 거대 파일 배제/압축 SHA/8회 L2 경계 회귀.

## 4. RED → GREEN → REFACTOR → REVIEW → COMMIT 증거

- 공개 CI RED Run **#44300745947**: 새 Owner blank scene/compact L0에서 `ModuleNotFoundError: d08_scene_broadcaster`. L2는 skipped — RED가 ROS/Gazebo 실행이었음을 가장하지 않는다.
- 후속 구현 중 RED Run #44301212360: 일부 코드 추가 후 워크플로 native scene 승인 텍스트가 빠진 L0 1 failed/115 passed; 조기 탐지 후 해당 계약을 공개 CI에 연결.
- 출고 HEAD **`81487f00ff9c20f2bc4e503548d43803297acc85`**, 공개 CI **[Run #44302370736](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44302370736)**: completed SUCCESS, 관련 4개 job ALL SUCCESS.
- L0 결과 **117 passed in 0.54s**.
- 실제 Gazebo Harmonic+Nav2 Xvfb L2: `D08_GENERATED_WORLD_SCENE_BROADCASTER_PRESENT`; `D08_REAL_GAZEBO_SCENE_BROADCASTER_L2_PASS`(native service robot/person 모델), `D08_CI_GAZEBO_GUI_CONNECTED_SCOPED_L2`; `D08_OFFICIAL_SAME_WORLD_THREE_PHASE_PATHS_L2_PASS_NO_GOAL`; `D08_CI_REAL_GUI_EIGHT_REPEAT_PATHS_L2_PASS`.
- **실제 GUI client 연결 중 8회 재계획 성공**, 각 회차 Scan host 최대 gap (초): **[0.448326, 0.235403, 0.245529, 0.244176, 0.232649, 0.235904, 0.247947, 0.234019]**. 500ms 한도는 그대로이며 최대 값의 여유가 **51.674ms**로 크지 않음을 기록한다.
- 해당 실행의 native [L2 artifact #14426548243](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44302370736/artifacts/14426548243) ZIP SHA256 `e33fd1328d10f223cfa933c3c761a8bd37af321daeba42ff0923dd780e9131eb`. 내부 SHA256SUMS **15/15 OK**.
- 동일 source별 Gazebo RGBD/physical LiDAR job SUCCESS.
- 동일 World live YOLO+D05+Nav2 job SUCCESS. 실제 far VALID 0.704022m, stop VALID 0.534589m, UNKNOWN `NO_PERSON_CLASS_IN_ACTUAL_YOLO`, 3-phase Path PASS. 이는 독립 CI job이므로 8회 GUI stress job에서 YOLO를 동시에 실행했다는 주장은 금지.

## 5. 현장 로그 패키지 축소 검증

원본 ZIP 171,950,602 B → 실제 추출된 최소 진단 ZIP **77,784 B (76.0 KiB), 25개 파일**, 전송 용량 **99.9548% 감소**. 진단 ZIP SHA256 `68cb9976dd38644998c87bce9ab265ca971cd9712267dd2d9c8291caafba945b`; 내부 SHA256SUMS **24/24 PASS**.

이 ZIP에는 첫 Scan 수신 위반 증거와 실제 생성 World SDF, AMCL timing 및 최소 Nav2 로그가 포함된다. 가장 큰 원본 파일인 NuGet `microsoft.ml.onnxruntime.1.20.0.nupkg` 약 103.4 MiB 압축분, 모델 파일, 중복 라이브러리 및 3천여 빌드/소스 파일은 전송하지 않는다. 신규 Owner 실행에서는 같은 원칙을 자동 적용한다.

## 6. 출고 대상과 미검증 항목

검증된 동일 SHA만 Owner에게 전달한다. Run #44302370736 GREEN과 D08 Owner 소스의 blob 동일성을 검증하고 docs-only HEAD와 구분할 것.

~~~bash
(
  set -Eeuo pipefail
  SHA='81487f00ff9c20f2bc4e503548d43803297acc85'
  SCRIPT="$(mktemp --suffix=.sh)"
  trap 'rm -f -- "$SCRIPT"' EXIT
  curl -fLsS --retry 3 --max-time 90 \
    "https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public/$SHA/d08/scripts/d08_owner_no_goal_bootstrap.sh" \
    -o "$SCRIPT"
  bash -n "$SCRIPT"
  export AXIA_D08_PUBLIC_SHA="$SHA"
  bash "$SCRIPT" --self-check
  bash "$SCRIPT" --run
)
~~~

성공 시 기대(현장 미실측): `D08_OWNER_WSLG_NVIDIA_D3D12_VERIFIED`, `D08_GENERATED_WORLD_SCENE_BROADCASTER_PRESENT`, `D08_REAL_GAZEBO_SCENE_BROADCASTER_L2_PASS`, `D08_OWNER_GUI_REPLAN_LOOP_READY`, Ctrl+C 후 `D08_OWNER_COMPACT_EVIDENCE=...diagnostics.zip`. 첨부할 것은 경량 ZIP+SHA256만이며, 대용량 원본 폴더를 다시 압축하지 않는다.

**한계:** 공개 CI Xvfb Scene service/GUI process는 실제 WSL2 WSLg GPU 화면 픽셀 PASS와 다르다. 이동 중 CM 120ms/Guard150ms/Scan300ms·인증 E-Stop도 범위 밖. 현장 546ms Scan 공백의 발행자 대 DDS/Executor 원인은 이력에 source-time이 없어 확정되지 않았고, 새 로그가 분류를 돕는다. Gazebo/RViz -11/-6과 Nav2 임시 SDF Ctrl+C 종료 정상성도 현장 L3 재검증이 필요하다. 반복 현장 실패가 생기면 첫 원시 Scan source-vs-host 경계를 CI RED로 편입 후 최소 수정해야 하며, 500ms threshold를 바꾸어 무효화할 수 없다.

```
D08_PUBLIC_L0=PASS
D08_REAL_GAZEBO_SCENE_L2=PASS_SCOPED
D08_REAL_GAZEBO_GUI_8_CYCLE_L2=PASS_SCOPED
D08_PUBLIC_YOLO_D05_L2=PASS_SCOPED
D08_OWNER_WSLG_L3=HOLD
D08_RELEASE=READY_FOR_OWNER_ONLY
AXIA_MVP_DEMO_ACCEPTED=HOLD
CERTIFIED_ESTOP=false
MAIN_MERGED=false
```
