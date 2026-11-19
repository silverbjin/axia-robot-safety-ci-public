# AXIA G07 Task04 — 현장 WSL2 GUI 실패 진단 및 공개 CI RED→GREEN 교육용 보고서

기준일: 2026-11-18 KST. 작업 판정: **Owner GUI 공개 CI L0 + 실제 Gazebo/RViz Xvfb L2 PASS**, 강사 WSL2/WSLg GUI 재검증 미수행, Moving Goal L3 미수행, AXIA_MVP_DEMO_ACCEPTED=HOLD.

## 1. 실패 원본과 무결성

강사 WSL2 원본 owner-gui-pregate-nacTiiJS.tar.gz와 별도 SHA256 문서를 대조했습니다.

- 압축 SHA256: **60794337c9dd346c08be41571fec7b84a931154b27d9a06566eaea835d587415**. 내부 SHA256SUMS **11/11 OK**.
- 정확 학생 소스: **01752add2e30c90c4d3286ef3a450f97746ecb55**, 이전 Task03 공개 Gazebo L2 **#44223320904 SUCCESS**.
- WSL2 kernel 6.18.40.1-microsoft-standard-WSL2. ROS 2 Jazzy, Gazebo Harmonic 8.15, 공식 패키지 25/25 및 공식 파일 5/5 **정확 패리티 PASS**.
- NVIDIA RTX 2060 Max-Q GPU 존재. WSLg 기본 OpenGL 렌더러는 **D3D12 Intel Iris Xe**. 이는 GPU 미존재 증거가 아니다.
- 실제 Gazebo와 Nav2 서비스 탐색, AMCL map pose, 공식 ComputePathToPose Free 경로 두 개, 두 Costmap 기준선은 정상.
- 첫 사용자에게 관찰된 geometry 치명적 예외: **D07_H01_GUI_RVIZ_PATH_SUBSCRIPTION_ABSENT**. 당시 RViz/Gazebo X11 창 감지는 0/0.
- 외부 실행기 **PUBLIC_NO_GOAL_GUI_RUNTIME_FAILED**는 최종 집계만 나타내며 원인 아님. 원본 압축에는 d07_gui_watcher.log, watcher 시작 ACK 및 child exit 증거가 없다.
- 목표 Goal은 미발행. certified E-Stop이나 Contact0를 주장하지 않음.

공개 CI에 원본 전체 WSL2 로그는 업로드하지 않았습니다. 재현 가능한 비밀 없는 요약 fixture는 tests/fixtures/g07_task04_owner_wsl2_first_failure_20261118.json에 원본 SHA256과 함께 기록했습니다.

## 2. 직접 확인한 첫 환경 오류 — Bash 특수 변수 오용

문제의 기존 공개 실행기는 ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST를 export한 직후, PID를 의도하여 **$_**를 사용했습니다. 그러나 Bash의 **$_는 마지막 명령의 최종 인수**입니다. 정확한 명령 순서를 동일하게 실행하면 다음 원본 문자열이 재현됩니다.

~~~text
axia_p2_task04_86_ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST1794975058
~~~

즉, Gazebo Transport에 전달되는 GZ_PARTITION에 equals 문자와 다른 환경변수 선언이 삽입됩니다. Gazebo 공식 Transport 문서는 **유효한 GZ_PARTITION과 서버·GUI 사이의 동일한 파티션을 필수 조건**으로 규정합니다.

**수정:** 명시적 Bash PID 변수인 **BASHPID**로 생성하고, Gazebo 실행 전에 GZ_PARTITION 문자 집합을 영문·숫자·underscore로 제한하고 길이 115 이하를 확인해 위반 시 fail-closed합니다. 같은 shell sequence를 CI에서 재현하는 자동 테스트가 다시 오염될 경우 즉시 실패합니다.

이 원인은 **잘못된 GZ_PARTITION 생성 자체에 대해서는 증명**됐습니다. 해당 오류가 전체 RViz 구독 실패의 유일한 인과관계라는 결론은 원본 GUI watcher 로그가 없어 단정하지 않습니다.

## 3. 실제 RViz 구독 실패의 일차 증거 보존

원래 NO_GOAL GUI 스크립트의 기본 inline watcher는 시작 ACK, 실패한 Gazebo child exit, 전송 토픽을 외부 아카이브에 남기지 않아 35초 뒤의 RViz DDS subscriber 부재만 최종 예외로 나타날 수 있었습니다.

Task04 공개 Owner 래퍼를 다음 범위에서만 수정했습니다.

1. 학생 소스에 이미 존재하는 **AXIA_D07_H01_GPU_GUI_TRIAL=1** watch program을 재사용합니다. 임의 신규 GUI 노드나 Nav2 Controller는 개발하지 않습니다.
2. WSLg 기본 Intel D3D12와 NVIDIA를 순차로 실제 GLX renderer 검사하여 성공한 어댑터만 선택합니다. CUDA/NVIDIA 장치가 존재한다는 정보만으로 렌더링 성공을 꾸며내지 않습니다.
3. 독립 Gazebo GUI child와 RViz child의 시작 ACK, Gazebo scene/pose Transport 진단, 첫 child 종료, RViz Path subscriber 실패를 별도 보존합니다. 전송 실패나 watcher의 early exit를 Geometry의 후속 오류와 구별합니다.
4. 원래 H01 native 실행기에 **AXIA_P2_SMOKE_RESULTS를 Owner 증거 폴더 내부로 연결**합니다. 이전처럼 source checkout 아래 results에만 남겨 archive에서 누락하지 않습니다.
5. 실행기 소유 세션만 종료하고, 모든 native log·GPU/WSLg renderer·패리티 증거를 한 tar.gz 및 SHA256으로 묶습니다. Global pkill·WSL 전체 종료 금지.
6. 실제 Goal 발행 권한은 여전히 **0**. Task03 CI-only GITHUB_ACTIONS 인증을 WSL2에서 위조하지 않습니다.

**목적:** 기존 RViz 구독 실패의 재발 가능성을 줄이고, 재발해도 최초 GUI 실행 경계를 압축 원본 안에서 분석할 수 있도록 합니다. WSLg D3D12 GUI는 공개 Ubuntu Xvfb와 다르기 때문에 Owner PC 성공을 사전 보장할 수는 없습니다.

## 4. 실제 공개 CI의 인과적 개발 과정

| 단계 | 공개 실행 및 실제 결과 | 판단 |
|---|---|---|
| 원본 RED | [#44237062643](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44237062643) | 정확한 Bash $_ 재현, 잘못된 GZ_PARTITION 발생. 6개 회귀 중 4개 FAIL |
| GREEN | [#44237386904](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44237386904) | 이전 L0 4 + 현장 원인 L0 6 = **10/10 PASS** |
| 첫 실제 GUI L2 RED | [#44237948105](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44237948105) | 실제 Gazebo/RViz X11 창 **둘 다 확인**, 원본 NO_GOAL runner **rc=0**. 그러나 판독기에서 **KeyError: phase**로 워크플로 실패 |
| 보조 판독기 회귀 | tests/test_g07_task04_native_path_stage_schema.py | 공식 학생 소스의 실제 Path 증거 필드명은 **stage**임을 확인. 잘못된 phase 필드 참조를 CI 방지 테스트에 편입 |
| 실제 GUI L2 GREEN | [#44238643061](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44238643061) | **12/12 L0 PASS + 실제 Jazzy/Gazebo Harmonic/Waffle/Nav2/RViz Xvfb GUI 2개·3단계 공식 경로 DDS Path 구독 PASS**. 원본 runner rc=0 |

최신 실제 Xvfb L2 실행의 **워크플로 코드 SHA = 5bb0cd72086f2f1a057f382649b773fff106f1f9**, GitHub job **134580794869**; artifact **14399100936** (공개 simulation 숫자/ACK만). 강사 원본 Student **01752add...**는 수정하지 않았습니다.

Xvfb actual native sensor/world/official ComputePathToPose Path의 BEFORE→INTRUSION→RESTORED 3단계 GUI 릴레이와 RViz 실제 subscriber count **각 단계 1 이상**을 동일 실행에서 판정했습니다. 단 Xvfb software GL이므로 **WSLg GPU D3D12 Owner 화면은 미인수**입니다. 새 코드를 CI 성공과 구분 없이 출고하지 않고 실제 L2가 GREEN임을 확인한 후 사용합니다.

## 5. 원본 실행기, 명령, 증거 범위

- Git: Public CI 저장소의 fix/g07-task04-owner-wsl2-public-pregate-20261118 브랜치, 공개 Draft PR #169.
- 원샷: scripts/axia_g07_task04_public_owner_wsl2_pregate_once.sh. 실제 L2 통과된 소스 SHA **5bb0cd72086f2f1a057f382649b773fff106f1f9**로 fetch 가능.
- 실측 공개 CI: tests/test_g07_task04_owner_public_wsl2_pregate.py 4개, tests/test_g07_task04_owner_field_regression_20261118.py 6개, tests/test_g07_task04_native_path_stage_schema.py 2개 + pinned Student exact ROS/Gazebo/RViz execution.
- 실행기 외부: docs/operations/AXIA_G07_TASK04_OWNER_WSL2_PUBLIC_GUI_PREGATE_20261118_KO.md.
- 임시 GUI world와 Waffle 임시 SDF만 생성하며 /opt/ros에 있는 공식 Nav2/TB3 파일을 덮어쓰지 않습니다. Supervisor/Collision Monitor/Guard 시간 경계나 인증 범위는 변경하지 않았습니다.
- 재발 시 가장 먼저 검사할 파일: owner archive 내부 native/d07_gui_watcher_started.txt → native/d07_gui_watcher.log → native/d07_gui_watcher_exit.txt → native/d07_gui_transport_topics.txt → native/d07_h01_geometry.log → launch.log / WSLg ogre2 log. 최초 시점·상태 전이·GUI spawn 경계가 우선이며, 마지막 예외만 보고 임의 재실행하지 않습니다.

## 6. 미검증 및 변경하지 않은 계약

- WSL2 GPU real rendering/실제 창 콘텐츠: 사용자 현장 **재실행 결과 미접수**.
- Task04 Moving Goal, 그에 따른 native S02 Contact0, CM source120ms·Observer120ms, Guard CM age150ms, Scan/Odom/Clock300ms, exact Goal CANCELED, Bag14, Navigation/Localization ACK, CM clean exit: **NOT_RUN** (단 Task03 공개 Gazebo CI 단일 Goal에서 이미 검증한 기존 성능은 그대로 보존).
- 전체 AXIA MVP 데모 인수: **HOLD**, main 병합 미수행, 인증된 E-Stop 아님.
- 공식 문서: https://gazebosim.org/api/transport/15/messages.html (파티션), https://gazebosim.org/docs/harmonic/getstarted/ (GUI server/client), https://docs.ros.org/en/jazzy/Concepts/Intermediate/About-Quality-of-Service-Settings.html (실제 QoS matched subscription).
