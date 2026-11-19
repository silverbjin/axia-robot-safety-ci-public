# D08 통합 Cycle 04 — 실제 G07 주행 최초 안전 상태 전이 RED, 단계별 원인 보존

**2026-11-19 KST / 정지 동작의 안전 TTL 실패를 PASS로 바꾸지 않는다 / 실제 통합 L2 HOLD**

## 경로 및 정확한 원본
- 공개 Draft PR #189, Public `feat/d08-d04-d07-single-session-20261119`; Student PR #63 SHA `8f5e262151f570e02d23646487504dafaa169b63`, G07 read-only strict oracle SHA `71b85c42ea474276fedd9f345521317b8c348b4e`.
- **첫 번째 실제 L2 RED #44482729736**: G07 원본 판정기가 참조하는 `d06.diagnostic`이 D08 브랜치에 없어 L0 import 실패, Gazebo NOT RUN. 테스트를 무력화하지 않고 별도 공개 read-only oracle 소스 SHA를 checkout→PYTHONPATH 연결, 소스 코드 복제 없음.
- **두 번째 실제 L2 RED #44483057090**: L0 및 Contact witness 빌드 성공, 주행 시작 전 `AXIA_G07_ENV_PARITY_BLOCKED mismatches=packages.libgz-transport13`. APT 빌드 헤더 `libgz-sim8-dev`가 G07 Owner lock의 **13.6.0-1~noble**을 13.7.0-1~noble로 업그레이드. `OWNER_PARITY_BAG_METADATA_MISSING`은 후속 결과이지 최초 장애 아님.
- 최소 수정 `.github/workflows/d08-single-session-moving-l2.yml`: Native Witness를 독립 disposable `build-native-witness` CI job에서 빌드해 SHA256 artifact로 전달, 실제 런타임에는 dev-header 설치 없이 `libgz-transport13=13.6.0-1~noble` 강제 확인. Commit `7db4dfcce2035d866b859d0fa173cf8b972106f8`.

## 수정 후 처음 도달한 실제 주행 안전 실패

[공개 Run #44483897411](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44483897411):
- 독립 Contact Witness 빌드 **SUCCESS**. 기존 리뷰 소스와 Student L0, 13.6 런타임 parity **PASS**.
- 기존 G07 소유 단일 Gazebo World에 D08 사람 Mesh/640×480 registered RGB-D를 붙여 실 실행, Gazebo/RViz 두 GUI X11 확인.
- 공식 Nav2 `NavigateToPose` UUID `74c3310d44ca4c328424f6e625c34a87` 실제 EXECUTING.
- CLEAR: front 2.041688m, CM/final 0.034919m/s, PASS.
- SLOW: front 0.744058m, CM/final 0.007499m/s vs supervisor 0.024995m/s, PASS.
- 물리 STOP intrusion native ACK duration **0.448526s**, target world(-1.357668422,-0.352362585).
- **최초 실패는 GUARD 안전 차단**: `UPSTREAM_STALE_AFTER_MOTION`, Guard 자체 internal CM recv age `0.169428615s > 0.150s` (초과 19.429ms); first latched `tick_monotonic=305.78414571`, last real CM recv `305.614717095`; latest Supervisor age `0.022853581s`, state NORMAL, goal authorized.
- read-only observer last CM `t=305.616951` / last output zero, 다음 CM callback 전 Guard latch; observer gap bracket right-censored, CM publisher 자체가 멈췄는지, executor/RMW 수신이 멈췄는지 **미확정**.
- 최종 `AXIA_G07_PUBLIC_CI_MOVING_GOAL_BLOCKED RuntimeError:GUARD_LATCH_DURING_STOP:UPSTREAM_STALE_AFTER_MOTION`; 이후 `P2_L2_SMOKE_RC=2`, 부수 ROS shutdown exception. **최종 예외 대신 첫 안전 latch를 근본 실패 경계로 보존**.
- 이 L2는 NO YOLO/NO D05; source camera만 추가된 L2. `D08_SINGLE_SESSION_MOVING_E2E_ACCEPTED=HOLD`.

## 공식 코드 관찰 / 최소 가설
- Gazebo Harmonic Sensors 문서: `<always_on>true`면 RGB-D가 지정 주기로 지속 갱신. Official GZ Sensors rendering loop uses `HasConnections()` to avoid needless rendering when no subscribers. 출처:
  https://gazebosim.org/docs/harmonic/sensors/
  https://github.com/gazebosim/gz-sim/blob/main/src/systems/sensors/Sensors.cc
- D08 기존 generated camera uses `<always_on>1</always_on>`, even though current moving test has no camera consumer. **가설**: D08 추가 RGB-D 렌더링/CPU 부하가 STOP intrusion 전후 CM callback delivery scheduling margin을 악화. 증명되지는 않았음.
- 공식 Nav2 `stop_pub_timeout`은 장시간 zero publishing 중단 조건이며, 현재 native readback `5.0s`. 이번 실제 약 169ms CM internal age가 이 파라미터만으로 설명된다고 단정하지 않는다. https://api.nav2.org/nav2-jazzy/html/collision__monitor__node_8cpp_source.html

## 다음 RED→GREEN 최소 범위와 미검증
- RED: G07 단일 World adapter에서 **실제로 이미지가 구독되지 않는 이동 구간**의 RGBD `always_on` 옵션이 기존 값 그대로여서 불필요한 렌더 부하 후보. 새 opt-in overlay에서만 `<always_on>false</always_on>`로 하고 실제 RGBD 이미지 subscriber가 붙을 때만 렌더하도록 구조적 검증. D08 original NO_GOAL default 유지, LiDAR 10Hz/CM/Guard TTL 불변.
- GREEN 조건은 **실제 공개 Gazebo Moving L2의 CM/Guard 원래 주기, STOP, terminal, 21조건**으로 한정. L0나 SDF XML만으로 안전 PASS 선언하지 않는다.
- 같은 증상 재발 시 최초 Guard CM age와 최초 CM publish/receive 타이밍을 수집하고 공개 CI에 재현 데이터를 편입. 단순 현장 재실행 금지.
- 원본 검증 수준: public actual Moving Goal L2 **HOLD** (first Guard TTL breach), Student/Instructor main 미병합, WSL2 Owner L3 NOT RUN, certified E-Stop 아님.
