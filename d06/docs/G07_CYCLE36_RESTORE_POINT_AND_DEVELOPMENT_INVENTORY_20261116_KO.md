# AXIA G07 — GUI 복구 전 기준선 / Cycle 36까지 개발 이력·재사용 원장

- 기준일: 2026-11-16
- **이 문서는 Cycle36 코드 변경 이전에 작성 및 커밋한 이력 동결본**이다. Cycle36은 아직 구현/검증하지 않았으며 아래 개선 항목은 계획이다.
- 전제: `AXIA_Robot_Safety_MVP_Baseline_Scenario_Acceptance_v1_KO.md`, 별도 승인된 축소 `AXIA_MVP_DEMO_ACCEPTED` 프로파일; 공식 ROS 2 Jazzy·Gazebo Harmonic·TB3 Waffle·Nav2 재사용.
- 소유: private Instructor 정답/원시 증거; public CI 비식별 검증/문서; Student 별도 TODO 패키지.
- 사용자 조건: **Owner WSL2 최종 검수 1회만**. 모든 재현·수정·실제 Gazebo L2는 공개 CI에서 먼저 수행. 안전 TTL/Goal/Guard 정책 완화·자동 Goal 동의·원본 삭제·main 병합 금지.
- 수집 근거: 공개 CI `43824411236`, `43828818188`, Cycle35 비공개 지원 번들 분석 보고서 및 아래 정확한 원격 SHA의 실행 소스. 커밋 메시지는 코드 확인 없는 동작의 PASS 증명이 아니다.

## 1. 복구 지점을 혼동하지 않는 SHA 고정

| 구분 | 소스/ref | 검증된 내용 | 복구/재사용 규칙 |
|---|---|---|---|
| **GUI 복구 참조점** | private `db1eec05e01e1db0d0d2e0c05610806ef4e499f9`; `scripts/p4_g07_shared_runtime.sh` | `owner-gui`에서 `headless=False`로 공식 Gazebo 통합 GUI 실행; 종전 P4 실제 Goal L2 `43674784552`는 GUI/WSLg 성공의 완전한 자동 증거가 아님 | **이 파일의 GUI 구성만 참고**. private 전체를 이 SHA로 되돌리지 않는다 |
| **GUI 회귀 경계 A** | private `319f327c32f786ad331526110fd39af5a97235d1` | `AXIA_G07_UNIFIED_GUI_SIDECAR=1`이면 Owner `headless=True` | 이 조건만 구분하여 검토 |
| **GUI 회귀 경계 B** | public `30599879c12c7f3a1a12c14b8b39b656362fc5ed` | 공용 `gz sim -g` + RViz2 + Marker Sidecar; `LIBGL_ALWAYS_SOFTWARE=1`, `GALLIUM_DRIVER=llvmpipe`, render/rviz 동일 CPU | Owner EGL 경고와 빈 화면의 **유력 원인 후보**; 코드변경 이력 확인. 단일 인과는 미증명 |
| **복구 전 최신 기능 소스** | private `420fd276ec1018f7fcc3f14873693cad02f080b4` tree `5ca77fb0bedd597b89b791e0931b42ea5a9cbdc9` | CI 실제 Gazebo L2 `43824411236`에서 CLEAR→SLOW→STOP 및 원본 안전·정지·물리 증거 | Cycle36 private 새 브랜치는 이 기능 소스에서 시작; **GUI 최소 변경 외 기능 보존** |
| **복구 전 Owner 공개 release** | public `f4b05a1d593385445308acd43af57a9faad1c788` tree `f4dbe38e071b168baaa7ed1f4cd967ed968978fc` | 강사 원샷 public checkout의 정확한 pinned tree | 원본 보존, 사용자에게 이전 실패 SHA 재실행 지시 금지 |
| **Cycle34 bootstrap fix** | public `42d78b41b62d8d7153bbb0b67dc360d7b87f2169`; CI `43828818188` | v3/v4 오기 → 실제 v1 Gate/Checker, no-ROS 10 tests PASS | 유지. `NO_ROS_NO_GOAL`만 증명 |
| **Cycle35 진단 보고서** | public `0648222d947670d76fd37b4bb1918d95a29c8adf` | Owner L3 초기 실패, GUI 회귀 및 RMW clock-step 분석 | Cycle36 분석의 우선 증거, 새 러너로 바꾸는 이유가 아님 |
| **원격 main 기준** | 별도 private/public main을 동결 시점에 확인; 현재 지시상 main 변경 금지 | Cycle36 기능/문서는 분리 브랜치·PR 후보로만 유지 | 사용자 승인 전 병합 금지 |

## 2. Cycle별 개발 성과 인벤토리 (개략)

한 Cycle의 모든 커밋이나 인수 조건이 같지는 않다. 아래는 추후 재사용해야 하는 검증된 기능과 진단 아이디어를 분류한 것이다.

| 기간 | 개발·진단 성과 | 복구 시 취급 |
|---|---|---|
| P4 통합 이전 | 공식 Nav2/TB3, Supervisor→CM→Guard, G07 실제 움직이는 Goal, 14-topic bag, **prearmed native STOP**, ACK 순서, S02 contact witness, async EvidencePump, Guard40ms | **KEEP** — 안전·주행 코어 교체 금지 |
| Cycle02 | D06 read-only RViz Sidecar; Goal 소유권은 P4 하나 | **KEEP** RViz 읽기 전용; 새 Goal runner 추가하지 않음 |
| Cycle03 | Goal 전 GUI receipt; Headless 서버/외부 GUI `gz sim -g` 및 공통 CPU/GL 정책 | **GUI 복구의 비교 대상**. receipt는 창 존재가 아니라 World/entity/render 준비를 증명하도록 개선 |
| Cycle04~06 | Nav2 shutdown service discovery, Goal Observer CPU 분리, native STOP용 최소 2 CPU 예약 | **KEEP / RETEST CHANGED BOUNDARY** |
| Cycle10~16 | CM thread STOP RPC 관측, TF wait 원인 가설과 되돌림, STOP RPC의 fresh CM 조건, localization start/shutdown 진단, 첫 120ms CM source/Guard 범위 검토 | **KEEP**; 시도 후 잘못된 TF20ms 단독 가설은 복구하지 않음 |
| Cycle20~26 | 최초 CM source/receive·Callback 지연 분리, CM 독점 코어 후보, scheduler /proc read-only 계측, 다중 채널 최초 gap 및 레이턴시 진단 | **FORENSIC KEEP**, 소스/Observer 신호를 실제 안전 통과로 오판하지 않음 |
| Cycle27~32 | 첫 120ms RPC overlap 분류, native STOP 우선순위 nice10, LTTng intrusive diagnostic 별도 분리, 실제 L2 GUI safety와 trace 분리 | **KEEP** 원본 진단·성공증거; 계측으로 시연 지연이 생기면 진단 분리 |
| Cycle33 | 임시 공식 Waffle SDF LiDAR 5→10Hz, Odom 30→100Hz, Owner용 소스/CI receipt pin, 한 번의 TTY Goal; 공식 설치 SDF 원본 불변 | **KEEP AS CANDIDATE**; CPU 부하/Scan 잔여 위반은 분석 후에만 변경 |
| Cycle34 | Owner bootstrap의 존재하지 않는 gate_v3/checker_v4 의존성 발견·RED→GREEN `43828695371→43828818188` | **KEEP**; Safety/GUI 실행은 해당 L0에서 검증하지 않음 |
| Cycle35 | Owner 최초 Nav2 FollowPath ACK timeout, Scan/Supervisor 관찰 초과, CM RMW host clock-step 후보, GUI Cycle03 회귀 경계·WSLg EGL 경고, Owner 원본 SHA 검증 | **실패 근거 영구 보존**. `first_guard_latch=null`을 안전 성공으로 해석하지 않음 |
| **Cycle36 (계획만)** | 아래 GUI 최소 복구, Nav2 ACK timing 계측, 안전 전달 first boundary 회귀, 최종 같은-SHA 실제 GUI Goal CI 후 Owner 1회 인수 | **NOT_IMPLEMENTED** — 이후 단계의 개별 commit/CI Run과 연결하여 갱신 |

## 3. Cycle35 현장 원본 실패의 증거 단위

- Owner Run: `p2-l3-owner-owoToEYU`; 제공 비공개 지원 번들에 SHA256 59/59 일치. 원시 증거를 public으로 올리지 않는다.
- **최초 Scan Observer 초과**: Goal+1.167s 때 308.184ms, Goal 중 최대 369.482ms(4건). 네이티브 Supervisor Scan TTL 위반으로 자동 승격 불가.
- **RMW 교차 시계 후보**: Goal+4.960s, CM source 2.234885s와 monotonic callback 0.055515s; Supervisor source 2.223023s. Clock-step 후보이며 CM 실제 2.2s 발행 중단 아님.
- **Supervisor Observer 최초 150ms 초과**: Goal+5.346s, 150.282ms. 네이티브 Guard 소스 수신 TTL 동일 증거는 아님.
- **Navigation 최초 확증 실패**: Goal+12.295s, `Timed out while waiting for action server to acknowledge goal request for follow_path` → `NavigateToPose ABORTED=6`.
- **후행 CM Observer 지연**: Goal+12.972s, 187.532ms; 이미 Nav2 종료 이후이므로 최초 주행 실패 원인으로 주장 금지.
- `first_guard_latch=null`, `first_safety_transition=null`, 후행 RAW/Goal cancel/종료 증거 미완성. `AXIA_MVP_DEMO_ACCEPTED=HOLD` 유지.
- GUI `Entity 0`, EGL `Not allowed to force software rendering when API explicitly selects a hardware device`; Sidecar `real_gazebo_gui_window=null`; **화면이 시연 중 비었는지, 서버 종료 후 캡처인지 미확증**.

## 4. Cycle36 실행·개발 요소 및 인수 단계

### Phase A — RED 최초 실패 분류 L0
- Owner 비식별 fixture에서 Nav2 FollowPath ACK timeout이 최종 verdict보다 우선; Scan 308ms/Supervisor 150ms, RMW clock domain, 후행 CM gap의 순서를 정확히 판정.
- 구형 소스/GUI·CI와 새 소스의 동일 SHA/tree 혼합 크레딧 금지.
- 최소 테스트만, 기존 P4·D06 테스트 중복 구현 금지.

### Phase B — GUI 회귀 복구 (첫 번째 수정)
- 기본 복구 후보: 이전 `owner-gui → headless=False`와 **독립된 read-only RViz** 조합.
- CI에서도 실제 World/model entity 및 3D Scene 연결까지 검증; `Xvfb`의 window PID만으로 PASS 금지.
- `WSLg` 소프트웨어 GL 강제 제거 후보 및 render affinity 단일 코어 집중 완화 후보는 각각 **원인 확증 후 하나만 적용**.
- CI의 기존 Goal 소유자·ROS graph·Safety Guard·TTL·Contact/Cancel/Shutdown 무변경.
- 실패시 원래 `headless+gz sim -g` 유지한 채 GZ_PARTITION, GUI world attachment, EGL 경로를 실제 No-Goal CI로 검사하고 가장 작은 수정을 선택.

### Phase C — Action / timing 경계 회귀 (다음 수정)
- `FollowPath` request, server accept, BT timeout의 **실제 파라미터/시간 출처** 측정. 근거 없이 BT/Controller timeout 증대 금지.
- 동일 실제 Goal에서 Scan publisher→Bridge→Safety Supervisor→CM→Guard, CM source/receive, odom, /clock 최대 interval·네이티브 최초 latch·S02 Contact 검증.
- 최초 문제 해소 후 다른 안전 계층 최초 TTL/주기 검증 없으면 통합 MVP = **HOLD**.
- CPU/GL, LiDAR10/Odom100 오버레이는 유효 원인이 입증된 경우에만 최소 변경. 공식 원본 SDF 불변.

### Phase D — 실제 공개 CI 및 Owner 1회 최종
- L0 고정 source/tree + 실제 Gazebo no-Goal GUI World/Entity/renderer 계약 → 실제 Gazebo+Nav2 **한 Goal** CLEAR→SLOW→STOP, Nav2 ACK, 14-topic bag, S02 Contact0, odom dwell>=1s, 7-channel+native RMW, exact Cancel ACK, clean lifecycle shutdown까지 PASS.
- 공통 display source와 Owner 환경변수 파라미터 검증. *Xvfb PASS*는 WSLg hardware renderer PASS가 아님.
- Owner 검수는 **하나의 최종 실행기**에서 환경/렌더 준비 → 물리 TTY 승인 → Goal → 자동 원본 증거 보관. 이전 Owner 실패 SHA의 재시도 금지.
- 승인할 시점: 공개 CI가 시연과 직접 관련되는 모든 조건을 증명하고, SHA/tree·runtime digest 고정. 실패하면 Owner를 호출하지 않는다.
- 실험/성능 스트레스 확장, GUI 새 기능, 학생 정답 배포, v1 15회 반복, main merge **범위 밖**.

## 5. 후속 재개 시 잃지 말아야 할 우선순위

1. Cycle36 GUI 수정이 성공했더라도 Cycle33의 오버레이 및 Cycle25~28의 CPU/STOP 기능을 **무조건 재구현·재적용하지 않는다**. 기존 HEAD에 남아 있는지 파일 SHA로만 확인.
2. 최초 안전 위반과 첫 Nav2 Action 실패를 하나의 원인으로 합치지 않는다.
3. 공개 CI 실제 Gazebo의 clean Goal, Contact0, ROS 전달 주기, 정지 증거가 부족하면 Owner 최종 인수를 요청하지 않는다.
4. 강사 정답과 원시 Owner bag는 private로만 유지. Student 변경 없음.
5. **main 병합은 사용자 승인 후만**.
6. 매 Cycle `RED→GREEN→REFACTOR→REVIEW→COMMIT`에서 실제 GitHub Run URL, 검증 수준, 비검증 내용을 보고서에 기록. CI fake/stub이나 No-ROS 테스트를 Gazebo PASS로 보고하지 않는다.

## 6. 복구 기준의 결론

`db1eec05`는 **GUI 동작을 비교하는 복구 참조점**, `420fd276`은 **현재 기능을 잃지 않아야 하는 시작 기준선**, `30599879`와 `319f327`은 **GUI 회귀 도입 의심 코드 경계**이다. Cycle36부터는 GUI-only 변경과 Nav2·안전 timing 변경을 별도로 검증·커밋하고, 공통 CI 시연 재검증 전 복구 성공을 단정하지 않는다.
