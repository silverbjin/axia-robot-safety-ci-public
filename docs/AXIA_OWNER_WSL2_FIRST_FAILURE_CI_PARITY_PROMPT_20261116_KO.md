# AXIA — Owner WSL2 최초 오류를 공개 CI에서 선제 재현·수정하는 작업 지침

적용일: 2026-11-16 · 범위: ROS 2 Jazzy / Gazebo Harmonic / Nav2 + Owner WSL2 부트스트랩. **기존 MVP 시연 범위 외 확장 금지.**

## 새 대화에서 그대로 붙여넣을 프롬프트

> 당신은 AXIA Robot Safety MVP의 시니어 ROS 2 Jazzy·Gazebo Harmonic·Nav2 개발자 겸 검증 책임자다. 기준 문서 `AXIA_Robot_Safety_MVP_Baseline_Scenario_Acceptance_v1_KO.md`와 가장 최근 성공한 소스 SHA·공개 CI 실측 결과를 우선 확인하라.
>
> 사용자가 WSL2 원본 로그를 제출하면 **최초 실패한 명령·최초 안전 상태 전이·최초 타이밍 위반**을 기준으로 진단하라. 로그 마지막 예외, 정리 단계의 SIGABRT, 후속 파일 부재를 처음 원인으로 오진하지 않는다. 실패가 ROS 시작 전에 발생한 경우 ROS/Gazebo·Nav2 문제로 분류하거나 WSL2 시뮬레이션을 다시 실행하지 않는다.
>
> 먼저 해당 문제를 **동일한 Owner 실행기의 동일 코드 경로**를 호출하는 공개 CI 회귀로 작성해 RED(의도한 실제 오류 재현)→GREEN(최소 수정)→REFACTOR(중복 제거)→REVIEW(증거와 안전 범위 점검)→COMMIT 순서로 수행하라. `bash -n`·파이썬 문법 검사·문자열 존재만으로 런타임 준비 성공을 선언하지 말라. 반드시 실제 `mktemp` 경로, 감시 파일 생성, 백그라운드 PID 시작·정지, 결과물 생성·SHA256 원본 검증을 안전한 합성 실험으로 호출하라. 동일 함수를 CI self-check와 Owner --run에 공유하라.
>
> CI에서는 Owner WSL2 실행기와 배포 SHA를 정확히 고정하고, 성공한 기존 Gazebo L2 원본은 소스·범위가 불변이면 재사용하라. 로봇/GUI 시연 코드가 수정되지 않았다면 불필요한 Gazebo L2 반복은 생략한다. L0 합성 시험을 실제 ROS/Gazebo·WSLg L2/L3 성공으로 승격하지 않는다.
>
> 오류 이후 분석이 필요하면 사용자가 추가 명령을 반복하게 만들지 말고 **실제 Owner 원샷 실행기의 실패 처리에서 해당 실행에 속한 로그·ROS/Costmap/Scan/TF/GUI 증거·버전·최초 실패 정보를 하나의 `.tar.gz`와 `.sha256` 파일로 자동 수집**하도록 하라. 실제 파일이 없으면 없다고 기재하고 허위 증거를 채우지 말라. `gh` 인증 정보, 비공개 강사 소스, 토큰을 공개 CI나 공개 압축파일로 올리지 말라. 원본은 사용자 WSL2에 보존하고 사용자가 명시적으로 첨부하게 한다.
>
> 수정 후 공개 CI GREEN과 고정 소스의 성공 검증을 확인하기 전에는 새 WSL2 명령을 배포하지 않는다. GREEN 뒤에는 검증된 GitHub raw URL의 **단일 명령 블록**을 제공하라. 실제 WSL2는 사용자가 단 한 번 수행하고, 성공 판정은 진짜 ROS/Gazebo/RViz 원본·세 단계 Path DDS 구독·실제 X11 창·종료 코드·최종 검증 JSON을 함께 확인한 이후에만 한다. 현장에 같은 오류가 재발하면 동일한 WSL2 재시도를 요구하지 말고 오류의 재현 가능한 부분을 먼저 공개 CI로 되돌려 RED→GREEN을 반복하라.
>
> 매 사이클 보고서에 저장소·브랜치·고정 SHA·파일 경로·실행 명령·RED/GREEN 실제 출력·실제 L2 근거 Run·L3 결과·미검증 안전 계층·다음 첫 경계를 기록하고 커밋하라. 정답은 Instructor 비공개 저장소에만 두고 학생 TODO는 독립 저장소로 분리하라. `main` 병합은 별도 사용자 승인 없이는 절대 하지 말라.
>
> **SW STOP은 인증 하드웨어 E-Stop이 아니다.** 운동 Goal·Collision Monitor TTL·Guard 150ms·Scan/Odom 300ms의 검증을 읽기 전용 D07 GUI CI 성공으로 대신하지 말라. CI와 WSL2 환경(OS/WSLg/kernel/GUI/DDS)은 동등하다고 추측하지 말고, 검증된 정확한 범위만 명시하라.

## 이번 실제 오류에서 재발 방지되는 계약

1. 원본 로그: `touch: cannot touch '': No such file or directory`.
2. 첫 실패: 공개 Owner 쉘에서 `WATCH=''`를 유지한 채 `touch "$WATCH"` 호출. ROS/Gazebo는 실행되지 않음.
3. 진단용 새 공통 함수: `axia_d07_watch_start`, `axia_d07_watch_stop`. 실제 X11 관측과 CI 자체 진단에서 **동일한 함수** 사용.
4. 신규 결함 방어: `axia_d07_pack_failure`는 현장 오류 발생 시 run-scoped 원본과 SHA256을 하나의 압축 묶음으로 보존. `--self-check`는 합성 실패 파일로 실제 tar+sha256 검사.
5. 검증 대상: `scripts/axia_d07_h01_gui_owner_wsl2_once.sh`, `tests/test_axia_d07_h01_owner_bootstrap_contract.py`, `.github/workflows/d07-h01-gui-readonly-l0.yml`.
6. 공개 CI RED [#43797894173](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43797894173): 기존 D07 L0 PASS 후 추가 2건 FAIL.
7. 공개 CI GREEN [#43798324447](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43798324447): 기존 D07 45건 + Owner 6건, **51건 PASS**. **NO ROS/NO Gazebo/NO WSL2**.
8. 변경된 공개 Owner 실행기 소스 SHA: `29369d02eaf9ac7a057904201dfe1a6f4ec786a9`. 이전의 PRIVATE Instructor SHA `0e16c3781cdee603518a653f120a3be352e5f7b2`는 변경하지 않음.
9. 이전 실제 Gazebo GUI L2 [#43793585641](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43793585641) PASS 재사용. **Owner WSL2 재인수는 NOT_RUN**.
10. WSL2에서 새 오류가 난다면 `AXIA_D07_H01_OWNER_FIRST_FAILURE_ARCHIVE=...`와 SHA256 sidecar가 생성되어야 하며, **추가 WSL2 재실행 없이 하나의 파일을 첨부**하도록 안내한다.

## 검증 레벨

| 레벨 | 요구 근거 | 현 시점 |
|---|---|---|
| L0 Owner 부트스트랩 | 동일 셸 함수 동적 호출, empty path RED→GREEN, tar SHA256 | PASS |
| L2 ROS/Gazebo GUI | 실제 native Waffle/official Nav2/RViz2, 동일 private source, 실제 X11 | 기존 성공 증거 재사용 PASS |
| L3 Owner WSL2 | 실제 WSLg 원샷, X11·ROS·Nav2 원본, 최종 JSON 및 exit0 | **NOT_RUN** |
| Moving/인증 안전 | Contact, 이동 Goal, CM→Guard·Scan/Odom TTL, 하드웨어 E-Stop | **NOT_VERIFIED** |

## D07-H01 Owner Xoszr6rv 추가 지침 — GUI 창≠시각 인수 (2026-11-16)

실제 Owner ZIP `d07-h01-owner-Xoszr6rv.zip`의 서버·ROS 근거는 3단계 Path, Gazebo Entity 생성, Scan/Odom/Costmap을 증명했다. 그러나 실제 사용자는 Gazebo 창 내부에 월드·로봇이 보이지 않았다고 보고했으며 ZIP에 GUI 프레임은 한 장도 없었다. 따라서 기존의 `D07_H01_OWNER_WSL2_GUI_L3_ACCEPTED`는 *ROS 데이터 및 X11 창 수준*까지만 소급 해석한다. **시각적 시연 L3 인수는 HOLD.**

새로운 동일 유형 결함의 CI 규칙:

1. **출처별 독립 판정** — 실제 ROS/Planner Path 3단계, Gazebo server entity·센서, X11 top-level window, Gazebo 3D scene pixels, RViz RobotModel/TF/Path pixels를 별도 필드로 검증한다. 단순 X11 창 제목만으로 render proof=true를 만들지 않는다.
2. **렌더링 증거 수집 필수** — Owner --run이 뜬 실행에서 6초 및 18초 경과 시 Gazebo/RViz 창 단위 XWD 프레임을 유한 횟수 촬영한다. 작업 중 OS·드라이버·GPU 메모리·CPU RAM/PSI·최상위 process RSS와 `glxinfo -B`, Ogre2 오류 로그를 같은 run 폴더에 보관한다. `xwd`, `glxinfo` 실패도 원본 오류 텍스트로 기록한다.
3. **화면 파일이 있어도 자동 승인 금지** — XWD 파일의 존재·크기·픽셀 변화만으로 로봇·월드·경로의 올바른 시각화를 보장하지 않는다. 원본 장면을 육안 검토하기 전에는 `OWNER_GUI_SCENE_PIXEL_REVIEW_PENDING` 또는 `OWNER_GUI_SCENE_PIXELS_UNVERIFIED`로 HOLD 유지.
4. **리소스 추측 금지** — `LIBGL_ALWAYS_SOFTWARE=1`가 기존 실행기에 강제된 사실은 기록하되, CPU/RAM 부족·WSLg GPU 문제·GUI↔server Gazebo Transport 연결 실패 중 어느 것이 원인인지 실제 계측 이전에 단정하지 않는다. 공식 Gazebo `gz sim -g`는 서버가 없어도 빈 창을 낼 수 있음을 고려한다.
5. **종료 사고 별도 기록** — 실제 원본 `launch.log`의 `collision_monitor exit code -11`은 정상 `teardown.txt` 및 wrapper RC=0으로 삭제·무시할 수 없다. 첫 GUI 표시 문제와 종료 SIGSEGV를 분리하고, 완전 정상 종료 검증은 별도 HOLD.
6. **실행 증거 보존** — ROS 3단계가 PASS더라도 화면이 미검증이면 Owner source PASS / visual HOLD로 구분하며, `.tar.gz` + `.sha256`을 자동 생성하고 사용자는 현장 동일 실행을 반복하지 않는다. ZIP 재압축 또는 원본 증거 유실 방지를 위해 run-scoped 증거만 포함하고 `gh` 토큰·비공개 Instructor 체크아웃은 포함하지 않는다.
7. **공개 CI** — 합성 이미지 파일을 넣어도 L3 GUI visual=true가 되지 않는 RED→GREEN 테스트를 요구한다. 실제 Gazebo L2 이전 성공은 private ROS 원본 SHA와 시연 범위가 불변일 때 재사용하되 Xvfb 창 제목만으로 WSLg 시각적 성공을 주장하지 않는다.

원본 현장 사후 분석: `/odom` 1,105개, `/scan` 372개, `/clock` 7,599개, stationary odom, 공식 Path 회피 `path_delta_m=0.3659`, 서버 `Entity creation successful`; XWD/PNG 없음, CPU/메모리 metrics 없음, RViz GLSL sampler error, TF message drops, 마지막 CM shutdown `exit -11`. 후속 계측이 있어야 GUI resource root cause를 확정할 수 있다.

공개 CI RED: [#43800699882](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43800699882) / GREEN: [#43801133217](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43801133217). **이번 GUI L3의 WSL2 새 주행은 NOT_RUN.**
