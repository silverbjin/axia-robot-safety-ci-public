# AXIA G07 Cycle 22 — 8 CPU WSL2 CM 전용 코어 가설과 실제 L2 실패

날짜: 2026-11-16. **결론: 새 CPU 배치 단위 L0 GREEN이나 공개 실제 Gazebo L2의 120ms 출고 여유 미달. Owner WSL2 주행 원샷 배포 금지, AXIA_MVP_DEMO_ACCEPTED=HOLD.**

## 원본·최초 위반

이전 사용자의 실제 G11 Owner 원본 첫 Guard `UPSTREAM_STALE_AFTER_MOTION`: CM age 174.184617ms > Guard hard TTL 150ms; CM RMW source 첫 gap 186.714207ms, Supervisor 원본 발행 4회(최대 gap 64.89631ms). STOP RPC 107.021916ms는 first gap과 중첩하지 않음. CM 내부 callback/TF 직접 원인은 미확정.

최초 8CPU WSL2 CM 코어 {1,2}는 Goal observer {2,3,4,5}와 2번을 공유하고 있었음. 4CPU 실제 CI CM {1,2}, Goal observer {2,3}; Marker 역할은 이 Cycle 시점에 검증 누락(다음 Cycle23 참고).

## RED→GREEN→REFACTOR→REVIEW→COMMIT

- Instructor 개발 브랜치 `fix/g07-cycle22-cm-exclusive-sixplus-cpu-20261116`.
- 정확한 Instructor 후보 SHA `124edc82c84ea5c248afb7ba6299b28dbf777092`, tree `67f81138f01a8e58ba93512470dbae4193740759`.
- 수정 `tools/p2_g07_official_cm_cpu_affinity.py`: CPU >=6인 경우 CM {second, second-last}로 두 코어 확보; 실제 8CPU {1,6}, 6CPU {1,4}. Goal observer 별도. 4CPU CI는 기존 {1,2} 그대로, Guard/Supervisor/공식 Nav2 소스/TF/TTL 변경 없음. 기존 exact PID verification and restore 유지.
- `tests/unit/test_g07_cycle22_wsl2_cm_exclusive_cpu_first_gap_20261116.py` 6개 및 과거 CPU/Goal 9개를 수정·검증.
- 공개 sealed L0 RED Run [43792422692](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43792422692): `TEST_CYCLE22_CM_CPU_RC=1`, 총 6개 신규 기대 계약 중 다수 불충족.
- 공개 sealed L0 GREEN Run [43792670891](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43792670891): `TEST_CYCLE22_CM_CPU_RC=0`, `TEST_FIELD_RC=0`, 12개 회귀 그룹 전체 GREEN. Ubuntu 24.04, NO ROS/Goal.
- 테스트 권한 경로 참고: 새 기능 브랜치 직접 sealed 실행 43792260016은 환경 승인 제한으로 **러너 미할당·steps=[]**; RED가 아니므로 기존 승인된 공개 `release/p2-g06-cm-ttl-20261110`의 sealed L0를 재사용함.

## 실제 GUI+RViz/Gazebo Harmonic/Nav2 한 Goal — 명시적 실패

Run [43792753212](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43792753212), public workflow commit `eac617b83d6fea19736460dff4c756fff93f0726`, private SHA 위와 동일.

- CLEAR front 2.049218m → SLOWDOWN 0.748401m → STOP 0.396339m; STOP 직전 실제 CM age 1.102587ms.
- 정확 Nav2 Goal cancel/shutdown, navigation and localization ACK, CM clean exit 모두 수행, `P2_L2_SMOKE_RC=0`.
- 첫 120ms CM RMW source gap **142.776465ms**, Supervisor 발행 3회/최대 coverage 50.079263ms. 원본 발행 간격 자체가 120ms 목표 위반.
- 7채널 Callback 최대(ms): source 60.563430, supervisor 63.010260, CM **142.466318**, Guard 54.876858, scan 204.536234, odom 135.604237, clock 104.691414.
- **최초 출고 실패:** `AssertionError: FIELD_CI_L2_PASS_LOW_MARGIN_OWNER_NOT_READY`; 기존 Guard hard 150ms는 넘지 않았더라도 별도 120ms 출고 목표 미달. CI 상태 `failure`.
- 이 실제 4CPU L2에서는 private affinity 기존과 동일하므로 8CPU 전용 수정이 실제 WSL2 성공했다고 해석하지 않는다. 기존 43727149856에서 110.964ms 성공한 4CPU 조건도 여전히 지터 가능성을 보여준다.

## 다음 Cycle23 단일 원인 후보

역할 전체 코어 배치 점검 결과 **D06 read-only Marker observer**는 4CPU에서 core2(공식 CM1,2 및 Goal2,3과 공유), 8CPU에서 core6(새 CM1,6과 공유). 따라서 CM/Goal 분리만으로는 CM과 Marker 간 경합이 남음. 다음 Cycle23은 사용자 접근이 없는 같은 GUI/Marker 실행기의 CPU 역할 배치만 변경해 공개 CI L0 RED→GREEN 후 실제 Gazebo L2를 검증. 안전 정책이나 공인 E-Stop 혼동 없음.

**검증 범위:** CPU L0 PASS, 실제 L2 FAIL, Owner WSL2 L3 NOT_RUN. 기존 원본·1회 잠금 보존; `main` 병합 미수행. `AXIA_MVP_DEMO_ACCEPTED=HOLD`.
