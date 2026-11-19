# AXIA D06/G07 Cycle 04 — 실제 L2 패키지 저장소 실패 최소 수정 및 Scan 최초 위반 회귀 (2026-11-19)

## 1. 최초 오류

- 소스 `566350e86f9d0b55de3fa86f3fe4e2c463ba5b15` 실제 L2 [#44534113749](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44534113749) FAIL.
- Actual Gazebo/Nav2 시작 **전** CI Docker 컨테이너 `apt-get update`: `E: Failed to fetch http://security.ubuntu.com/ubuntu/dists/noble-security/InRelease Connection failed`, exit100. 이 시점에서 `ROS_GAZEBO_L2=NOT_RUN`; 절대 Scan 성능 실패라고 판정하지 않음.

## 2. 기존 해결 재사용 및 가설

기존 GitHub Ubuntu 컨테이너 내부만 `/etc/apt/sources.list`/Ubuntu Deb822 `/etc/apt/sources.list.d/*.sources`를 HTTPS `security.ubuntu.com`, `archive.ubuntu.com`로 치환한다. 패키지 서명·Ubuntu Noble 배포 계열은 변경하지 않는다. `Acquire::Retries=2`, `Acquire::http::Timeout=20`은 CI 네트워크 fetch 한정으로, Safety/ROS TTL이나 WSL2 Owner 환경의 retry/timeout이 아님. 설치 패키지는 기존 `xvfb x11-utils ros-jazzy-rviz2` 및 native Gazebo Python 메시지 바인딩 그대로.

## 3. RED→GREEN→REFACTOR→REVIEW→COMMIT

- RED: `d06/tests/test_d06_l2_apt_https_bootstrap.py`, Git commit `77d3789d1e8c20deb2b2267473a3316e9d92160f`, public L0 [#44535703778](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44535703778) 실패 (CI-only HTTPS guard 미구현).
- GREEN: `.github/workflows/axia-d06-g07-native-nogoal-cm-clean-l2-20261119.yml` 내부 APT HTTPS 정규화 및 signed apt timeout options. 코드 커밋 `001e13c4cd082751d2910b7c709d507b522e9058`, 공개 L0 [#44535840207](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44535840207) **120/120 PASS**, runner canary [#44535840359](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44535840359) PASS.
- Review: 승인 없이 Ubuntu system packages 전역 downgrade/upgrade 없음, apt trusted=yes/서명 우회 없음; WSL2 source 변화 없음.

## 4. 같은 소스의 실제 Gazebo L2 결과

[**#44535830485**](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44535830485) 실행에서 APT 단계 및 진짜 Jazzy/Harmonic/Nav2/GUI/20초 센서 창/종료까지 진입해 기존 rc100 조기 종료 재현은 막았음. `AXIA_D06_G07_NATIVE_SHUTDOWN_SMOKE_RC=0 RVIZ=1 GAZEBO=1`, Student qualified 20초 `NO_GOAL_SENSOR_WINDOW_CLEAR_CANDIDATE` reasons=[], Nav2 Navigation/Localization **ACK/ACK**, CM exit0, 부모 GRACEFUL.

그러나 실제 Nav2 READY 이후 첫 source-stamp **34.302→34.401초**에서 Gazebo native Scan wall gap **300.409ms**, 독립 ROS Raw **300.898ms**, Safety **301.307ms**. 정확한 국소 native Clock 관측 RTF **0.374704**, 즉 Gazebo native sensor 이전부터 순간 simulator 진행 여유 부족. Strict Scan300 위반으로 실제 통합 L2 **FAIL**. 학생 qualified 이후 20초 PASS가 최초 위반을 지우지 않음.

이것은 Cycle03 Student Executor 분리 이후에도 **별도의 Gazebo sim-side 첫 native gap**이 남아 있음을 증명한다. ROS subscriber 콜백만 최적화해 이 원인까지 해결했다고 주장하지 않음.

## 5. 남은 조건

- CI APT(인프라) GREEN은 해결. Gazebo sim-side 순간 RTF slowdown 원인은 **UNDETERMINED**.
- NVIDIA WSLg core stack 원본 없음, WSL2 final acceptance NOT_RUN, G07 Moving Goal & CM120/Guard150 데이터 경로 미검증.
- 배포 `D06_GAZEBO_LIVE_RELEASE=HOLD`, `AXIA_MVP_DEMO_ACCEPTED=HOLD`, `CERTIFIED_ESTOP=false`.
- 다음 가설은 기존 공개 CI Xvfb llvmpipe에서 GUI viewer가 Gazebo server CPU를 경쟁하는지 **단일 후보**로 검사. safety TTL/센서 Hz/ROS QoS/official Nav2 변경 불가.
