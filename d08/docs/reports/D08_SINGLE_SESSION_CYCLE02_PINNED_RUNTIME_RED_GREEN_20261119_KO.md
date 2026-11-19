# D08 통합 Cycle 02 — G07 공식 World/SDF 결합 CI 인프라 실패 해결 (RED→GREEN→REVIEW→COMMIT)

기준일 2026-11-19 (KST). 단일 World 소스 결합 검증에 한하며 **실제 Gazebo/Goal/안전 런타임은 이 사이클에서 시작하지 않았다.**

## 최초 실패 / 환경
- 공개 Draft [PR #189](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/189), 브랜치 `feat/d08-d04-d07-single-session-20261119`.
- 이전 Run [#44478433872](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44478433872): `l0-human-proxy-red-green` success, `g07-official-source-sdf-adapter-l1` failure.
- 최초 오류 로그: `E: Failed to fetch http://archive.ubuntu.com/ubuntu/dists/noble/InRelease Connection failed [IP:185.125.190.82 80]`; 이어 `apt-get` exit **100**. D08/G07 Python adapter나 SDF 오류 메시지는 실행되지 않았다. **원인 CI 패키지 네트워크 의존성**, ROS 기능 오작동 주장 금지.

## 가설 / 최소 수정
- 기존 G07 Task04 **실제 Gazebo+Nav2 Moving GUI L2**에서 검증된 컨테이너 이미지 `ghcr.io/silverbjin/axia-g07-runtime@sha256:861ae1df0560f991698d8967193380b1619589ba7770b5e2ca91ea4ef31f0c8e`를 그대로 사용한다.
- 공개 CI `.github/workflows/d08-main-no-goal-real-gazebo-l2.yml`의 새 `g07-official-source-sdf-adapter-l1` job에서 **APT 설치만 제거**하고 `git`·`curl`·`xacro`·`ros2`·공식 `nav2_minimal_tb3_sim` 실행 전제검사로 대체한다.
- L0 기존 226 tests, G07 10Hz/안전 TTL/Goal 인증/원본 SHA 경계 변경 없음.

## 실제 GREEN
- 소스 수정 커밋: `e2292b641066ec075ae56246627ddc1730a5f5d2`.
- [공개 Run #44481091894](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44481091894) workflow **SUCCESS**.
- L0: **226 passed**, 정확한 본 소스 HEAD.
- 신규 공식 Jazzy/G07 xacro Source job **SUCCESS**. 실제 로그:
```text
D08_G07_PINNED_G07_RUNTIME_IMAGE_JAZZY_READY
AXIA_G07_DEMO_LIDAR_ONLY_5HZ_TO_10HZ_TEMP_SDF_PASS ORIGINAL_OFFICIAL_MODEL_UNCHANGED TTL_300MS_UNCHANGED GOAL_NOT_SENT CERTIFIED_ESTOP=false
D08_G07_SINGLE_WORLD_STATIC_OVERLAY_READY_NOT_GAZEBO_NO_GOAL {...}
D08_G07_REAL_OFFICIAL_XACRO_STATIC_L1_PASS_NOT_GAZEBO_NOT_MOVING
```
- artifact ID `14508850514` `d08-g07-official-source-only-not-real-gazebo.zip`, upload SHA256 `e255c595c63c08acaa8e9504446484fdedd8c8712a91163304d9f99ee51289c0`, 실제 파일 15021 bytes.
- 독립 Gazebo·YOLO L2 jobs **intentionally SKIPPED**, 앞서 성공한 독립 증거 보존. 이 job에서 Gazebo 서버/ROS node/Goal/실제 Safety TTL/WSLg 미실행.

## 검증 수준/향후 딱 두 개의 경계
- **L0 PASS + 실제 공식 Jazzy/G07 Xacro SOURCE 변환 PASS**.
- 다음 RED: `p2_no_goal_smoke_ci.sh`가 기존 G07 World/Robot launch argument를 D08 동일 source overlay로 **단 한번만** 교체하는가? 다른 launch, Goal 자동 승인, LiDAR 주기/CM/Guard TTL 변경이 없어야 함.
- 다음 실제 L2: YOLO DetectionArray + Depth ROI + CM/Guard + 공식 Nav2 Moving Goal+세 상 Path를 **동일 GZ_PARTITION/ROS_DOMAIN_ID/Gazebo World**에서 캡처, 주행 Scan 300ms와 CM/Guard 원래 기준으로 판정. 기존 Owner 최초 Scan 317.863ms (300ms 기준 초과) 회귀 필요.
- Owner WSL2 L3 NOT RUN. Public main/student main/instructor main 모두 미병합. 인증 E-Stop 아님.
