# AXIA G07 Task04 — Owner WSL2/WSLg 공개 GUI 사전검증 인계

2026-11-18 KST. Task04 상태: PUBLIC_GUI_PREGATE_L0_AND_NATIVE_XVFB_L2_PASS_SCOPED, 실제 Owner L3 NOT_RUN, MVP HOLD.

## 근거와 실행 범위

공개 CI 실제 Task03 Gazebo L2 [#44223320904](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44223320904) 완료, 원본 Public CI SHA 6bc8b0711ab056e63e100f3eede2c5f06cdf3856, 공개 Student SHA 01752add2e30c90c4d3286ef3a450f97746ecb55. Contact0·CM120·Guard150·SQLite14·정확 Goal CANCELED·Nav2 ACK 성공은 이 CI 단일 실행의 증거이지 Owner WSL2 L3 증거가 아니다.

본 Task04 1차 작업은 비공개 Instructor 없이 정확 public Student SHA만 다운로드해 Owner WSL2 Ubuntu24.04/ROS Jazzy/Gazebo Harmonic/Nav2 userspace 25 package·5 official file, WSLg GUI/RViz/Gazebo 실화면을 NO_GOAL로 점검한다. Student 기존 CI-only Moving Goal 권한을 Owner에서 위장하지 않는다. 소프트웨어 정지는 인증 E-Stop이 아니다.

## RED→GREEN→REVIEW→COMMIT

- RED: [public #44232883070](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44232883070), 신규 WSL2 GUI 실행기 부재로 4개 테스트 실패(3 ERROR, 1 FAIL).
- GREEN: [public #44233533697](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44233533697), 4/4 PASS. bash syntax/selfcheck, GitHub Linux에서 Owner --doctor fail closed, exact SHA, no private repo and CI Goal authority spoof 금지, WSL2·WSLg·GPU·공식 패리티·한 파일 증거 계약.
- 검증 수준: 공개 Ubuntu ROS-free L0만 실제 실행됨. Gazebo/RViz는 Github에서 새롭게 실행하지 않았으며 User WSL2/WSLg L3는 아직 NOT_RUN. 이전 Task03 L2의 원본 증거 그대로 보존.
- 변경 파일: scripts/axia_g07_task04_public_owner_wsl2_pregate_once.sh, tests/test_g07_task04_owner_public_wsl2_pregate.py, .github/workflows/axia-g07-task04-owner-wsl2-pregate-public-l0-20261118.yml, 본 문서.
- Review: ROS official/Student 원본 수정 없음, Guide만 공개 CI 개발 브랜치에 추가. USER 현장 L3 및 main 병합 미수행.


## 2026-11-18 실제 현장 실패 수정 및 출고 게이트

**이전에 발행한 실행기 SHA 4db31c90afe568282bc9d49713e053bf70b43152는 폐기합니다.** 원본 사용자 WSL2 압축 SHA256은 60794337c9dd346c08be41571fec7b84a931154b27d9a06566eaea835d587415, 내부 11/11 무결성 PASS입니다.

- 최초 확인 오류: D07_H01_GUI_RVIZ_PATH_SUBSCRIPTION_ABSENT. 추가로 실제 GZ_PARTITION에 ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST가 섞여 있었습니다. Bash 특수 변수 $_가 이전 export 마지막 인수로 해석된 정확한 원인을 확인하고 PID 생성 코드를 수정했습니다.
- 공개 RED [#44237062643](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44237062643) → 공개 L0 GREEN [#44237386904](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44237386904): **10/10**. GZ_PARTITION 문자열 오염 재현/차단.
- 공개 실제 Gazebo/RViz Xvfb RED [#44237948105](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44237948105): 원본 GUI runner rc=0, 창 2개 관찰. CI reviewer의 stage 대신 phase 필드 접근 오류를 확인·회귀로 편입.
- 공개 실제 Gazebo/RViz Xvfb 최종 GREEN [#44238643061](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44238643061): **L0 12/12 + 실제 3단계 ROS/Gazebo/Nav2/RViz DDS Path subscriber L2 PASS**, 원본 rc=0, X11 RViz/Gazebo 창 2개. WSLg GPU 승격 금지.
- 수정된 원샷은 별도 GPU GUI watcher 시작 ACK/조기 종료·Gazebo native 전송 토픽·RViz Path 구독 로그를 **Owner 단일 TAR.GZ 내부에 모두 보존**합니다. D3D12 NVIDIA/Intel GLX를 실제 확인 후 선택하고 실패 시 fail closed합니다.
- [정식 교육용 오류 RCA 및 실험 기록](./AXIA_G07_TASK04_WSL2_GUI_FIRST_FAILURE_RCA_20261118_KO.md).

**다음 현장 실행은 오직 위 최종 GREEN SHA 5bb0cd72086f2f1a057f382649b773fff106f1f9로 수행**하십시오. GUI만 검증하며 Moving Goal L3, 전체 MVP 및 E-Stop 인증은 아닙니다.

## Owner WSL2 — 복사·붙여넣기 단일 명령

~~~bash
(
  set -Eeuo pipefail
  SOURCE_SHA='5bb0cd72086f2f1a057f382649b773fff106f1f9'
  SCRIPT="$(mktemp --suffix=.sh)"
  trap 'rm -f -- "$SCRIPT"' EXIT
  curl -fLsS --retry 3 --max-time 90 \
    "https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public/$SOURCE_SHA/scripts/axia_g07_task04_public_owner_wsl2_pregate_once.sh" \
    -o "$SCRIPT"
  bash -n "$SCRIPT"
  bash "$SCRIPT" --self-check
  bash "$SCRIPT" --run
)
~~~

이 명령은 실제 ROS 2·Gazebo·RViz GUI를 구동하지만 Moving Goal은 발행하지 않는다. 따라서 FULL TASK04 Owner L3 PASS를 절대로 출력하지 않는다. 기본 ROS_DOMAIN_ID=86; 별도 도메인이 필요하면 AXIA_G07_TASK04_DOMAIN_ID를 지정. 기존 Nav2 overlay는 자동 검색하며 AXIA_NAV2_OVERLAY_SETUP 절대경로도 허용한다.

현장 첫 실행에는 WSL2 Ubuntu24.04, ROS Jazzy·Gazebo Harmonic·Nav2/TB3, WSLg DISPLAY와 XDG_RUNTIME_DIR, GitHub public 네트워크가 준비돼야 한다. 25 package/5 official 파일 패리티 불일치면 안전하게 중단한다.

성공 기대 패턴(아직 WSL2 실제 결과 아님):

~~~text
AXIA_G07_TASK04_PUBLIC_OWNER_BOOTSTRAP_L0_PASS ...
AXIA_G07_TASK04_PUBLIC_STUDENT_SHA_VERIFIED=01752add2e30c90c4d3286ef3a450f97746ecb55
AXIA_G07_TASK04_WSL2_CORE_PARITY_25_5_PASS
AXIA_G07_TASK04_GUI_PREGATE_RUNTIME_RC=0 RVIZ_X11=1 GAZEBO_X11=1 XWININFO_AVAILABLE=1
AXIA_G07_TASK04_WSL2_GUI_NO_GOAL_AUTOMATED_PREGATE_PASS
AXIA_G07_TASK04_ARCHIVE=/home/.../owner-gui-pregate-XXXXXXXX.tar.gz
AXIA_G07_TASK04_SHA256=/home/.../owner-gui-pregate-XXXXXXXX.tar.gz.sha256
AXIA_G07_TASK04_OWNER_MOVING_L3=NOT_RUN
AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false
~~~

결과는 Owner HOME 아래 한 개의 tar.gz 및 sha256으로 보존한다. 첫 화면 오류는 최종 exception 대신 원본 logfile·GPU/WSLg GL·첫 실패를 확인한다. xwininfo가 없으면 GUI 창 존재 자동 검사가 불가능하므로 visual contents는 별도 확인해야 한다. 이 stage가 통과했다고 Contact0·Moving Goal·Nav2 종료까지 L3 PASS라고 주장하지 않는다.

## 후속 인수 경계

Task04 공개 사전검증 실행기 READY, 실제 Owner WSL2 실행 NOT_RUN. 실제 Moving Goal을 위해서는 공개 Student에서 정확한 Owner controlling-TTY/세 프로세스 PID/Goal UUID/정식 Guardian CM+Guard/14-topic bag 인수 기능의 Owner 전용 실행 경로가 필요하다. CI-only Goal을 WSL2로 복제하기 위해 GITHUB_ACTIONS 값을 위조하거나 watchdog TTL을 늘리지 않는다. 이후 공개 CI RED→GREEN을 완료해야 Owner WSL2에서 한 번에 통합 인수한다. Owner L3가 확인되기 전 AXIA_MVP_DEMO_ACCEPTED=HOLD, main 병합 없음.

## 2026-11-18 실제 강사 WSL2 화면 최종 검수 완료 (후속 인수 판정)

위의 원샷은 **강사 WSL2에서 실제로 실행됐으며**, 원본 TAR/SHA256과 제출된 화면을 대조한 결과 \`NO_GOAL_GUI_VISUAL_ACCEPTED=PASS_SCOPED\`입니다. 기존 안내의 **"성공 기대 패턴/아직 WSL2 실제 결과 아님"** 문구는 최초 배포 시점의 안내였으며 현재 현장 인수 결과가 아닙니다.

- 현장 원본 \`owner-gui-pregate-lxXToFIk.tar.gz\` SHA256 \`4e69c1a43f3623104da0425211dd2cd20c90c2d986750c66196ee397756defb2\`, 내부 73/73 및 native 59/59 무결성 PASS.
- 실제 \`run_rc=0\`, RViz/Gazebo 각 1개 X11 창, Nav2 Path 3단계 DDS subscriber 각 1개, WSLg D3D12 NVIDIA GLX PASS.
- 사용자가 제출한 1861×868 화면에서 Gazebo 월드와 RViz Costmap/Path 표시를 직접 확인. PNG SHA256 \`46f9d35283f7164f6724226a6b82542350bad222a8e65ea320adc37d073716c2\`. 원본 화면은 로컬 경로를 포함하므로 공개 Git에 저장하지 않음.
- **NO_GOAL GUI 사전 인수는 종료**. 단, 실제 Owner Moving Goal L3 NOT_RUN 및 전체 MVP HOLD, SW Stop≠인증 E-Stop, main 미병합.

[최종 범위 확정 보고서](./AXIA_G07_TASK04_OWNER_NO_GOAL_GUI_VISUAL_FINAL_ACCEPTANCE_20261118_KO.md)부터 확인하고, 과거 실패한 SHA를 재실행하지 마십시오.
