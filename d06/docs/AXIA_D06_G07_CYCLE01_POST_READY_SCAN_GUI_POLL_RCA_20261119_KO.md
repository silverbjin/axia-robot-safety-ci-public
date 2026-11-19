# AXIA D06/G07 Cycle 01 — First READY Scan300 회귀 강화·Xvfb 가설 검증 중간 보고 (2026-11-19)

## 1. 문제와 원본 인수 기준
실제 공개 Gazebo L2 [#44528260284](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44528260284), 소스 SHA `2834eccf9822743159aceabced6f9b5dadd1467b`.
- /scan Student qualified 20.005s Raw max120.664ms/Safety121.503ms, 198/198 CLEAR.
- 그러나 **실제 Nav2_ACTION_READY 461.066 이후** 동일 source stamp31.200→31.302초 native301.441ms, ROS raw302.017ms, ROS safety302.538ms로 최초 Scan300 위반. 국소 Clock RTF 0.397999.
- Nav ACK2.135663초, Localization manage_nodes 30초 무응답 (get_parameters는 0.026005초 정상). CM/Gazebo child exit0.
- **원본의 최초 타이밍 위반이 후속 학생 qualified 20초 CLEAR로 은폐되지 않아야 함.**

## 2. 재사용·단일 가설·수정
- 기존 `d06/tools/d06_g07_scan_rx_witness.py`의 exact native/ROS same-pair 및 READY proxy 재사용. Safety TTL300ms/CM120ms/Guard150ms, Goal/Fault, 공식 Nav2 코드 변경 없음.
- `d06/tests/test_d06_g07_post_ready_first_breach_l2.py`: 정확한 31.200→31.302초 쌍 fixture와 fake-free L0 계약.
- 공개 `.github/workflows/axia-d06-g07-native-nogoal-cm-clean-l2-20261119.yml`: Nav2 READY부터 20초간 native/raw/safety 실제 JSONL의 수신 gap과 source stamp 선후 검증. 하나라도 gap>300ms면 실제 통합 FAIL, Student qualified PASS 무관.
- 단일 성능 후보: 기존 `xwininfo -root -tree`를 1초마다 수행하던 루프에서 **Gazebo 및 RViz 두 창을 확인한 뒤 더 이상 반복하지 않음**. 이것은 잠정 GUI/X-server 경쟁 가설이지 입증된 원인 수정이 아님.

## 3. RED→GREEN (L0)
- RED [#44531388235](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44531388235): `post_ready=paired["post_ready_proxy"]` 엄격 게이트와 GUI 조회 조기 종료 계약 누락.
- GREEN [#44531697432](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44531697432): **112/112 공개 L0 PASS**. 기준 변경 코드 SHA `ff8d61d6534992c7f29db5184bf0e92591d0b5e1`. BRANCH/PR `fix/d06-wslg-lidar-vs-rtf-ci-20261118` / [#177](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/177), main 미병합.

## 4. 실제 L2 가설 검증 = FAIL, 효과 미입증
- 소스 SHA `ff8d61d6534992c7f29db5184bf0e92591d0b5e1`, 실제 Linux Xvfb ROS Jazzy/Gazebo Harmonic/Nav2/Waffle: [#44531611496](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44531611496).
- 원본 artifact #14533782394, ZIP `axia-d06-g07-nogoal-cm-ordered-l2-44531611496`.
- 첫 READY 이후 **same stamp 38.700→38.802초**: Gazebo native **90.905ms**, independent ROS safety **394.226ms**, native→ROS peer after receipt 추가 **324.972ms** (before 21.651ms). 이 실행은 이전 native-first violation과 다른 **AFTER_NATIVE_TRANSPORT_RX** 경계입니다. 해당 구간 native Clock RTF 0.955665. 원인을 single GPU/ROS로 단정하지 않음.
- Student qualified Raw191개 max427.533ms, Safety192개 max429.686ms, Safety distance 192/192 CLEAR. Scan TTL FAIL.
- Navigation `manage_nodes` SHUTDOWN **40.000576초 SERVICE_TIMEOUT**, Localization 미시도. 공식 Nav2 관리자는 준비 상태였으나 종료 요청 ACK 없음.
- Collision Monitor **exit -11**, Gazebo native exit 별도 판단 필요. 부모 `P2_L2_GRACEFUL_TEARDOWN`는 성공 증거가 아님.
- **판정**: Xvfb `xwininfo` 반복 중단만으로 timing 문제가 해결되었다는 증거 없음. 더 이상의 동일 후보 현장 재시도 금지.

## 5. 공식 문서 및 검증된 범위
- 공식 Nav2 Jazzy `lifecycle_manager.cpp`는 `/manage_nodes`와 `/is_active`를 동일 MutuallyExclusive callback group 및 독립 service executor에서 처리함. `/get_parameters` 응답은 **이 group의 건전성 증거가 아님**: https://api.nav2.org/nav2-jazzy/html/lifecycle__manager_8cpp_source.html
- Goal/cmd_vel/fault injection 전혀 없음, SW 정지는 certified E-Stop이 아님.
- CI Linux Xvfb 결과는 NVIDIA WSLg D3D12 GPU 재현성이 아니며 WSLg Gazebo core SIGSEGV stack은 아직 없음.
- `AXIA_MVP_DEMO_ACCEPTED=HOLD`, `D06_GAZEBO_LIVE_RELEASE=HOLD`, `CERTIFIED_ESTOP=false`.

## 6. 다음 실패 경계
1. 상반된 실제 L2 source pair 두 개를 모두 회귀에 유지하여 native-first vs downstream-ROS-first를 혼동하지 않음.
2. Nav2 manager callback group 자체와 default parameter callback 경계를 동일 실제 종료 세션에서 read-only 측정 후 변경 후보를 좁힘.
3. ROS witness read-only 계측의 callback scheduling, Xvfb/Gazebo/ROS 프로세스 부하를 증거로 분리. 300ms를 완화하는 우회 금지.
4. core 부재 시 WSLg 최초 SIGSEGV 원인 `UNDETERMINED`; 공개 L2 통과 전 최종 Owner WSL2 인수 금지.
