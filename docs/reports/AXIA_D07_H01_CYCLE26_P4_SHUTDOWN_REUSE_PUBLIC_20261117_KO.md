# AXIA D07-H01 Cycle26 — P4 재사용 종료 결함 수정: 공개 CI 릴리스 범위

2026-11-17 KST. ROS2 Jazzy / Gazebo Harmonic / 공식 Nav2 Waffle **No-Goal** GUI 수업용.

## 재사용·발견

- 기존 P4 G07: `tools/p2_g07_ordered_shutdown.py` 공식 Navigation→Localization Lifecycle SHUTDOWN ACK, CM clean exit 0 감사. 기존 범위 실제 L2 #43674784552 PASS였으나 P2 Supervisor 자식 종료는 미검증.
- 이전 D07 실제 Owner: Supervisor context-invalid RCLError exit 1인데 launch 부모만 종료됐다고 `P2_L2_GRACEFUL_TEARDOWN` 출력. 후속 코드에서 자식 종료까지 명시적으로 검사.
- 비공개 강사 코드에서 P1과 동일한 조건부 RCLError 종료 처리만 P2에 재사용. D07 무주행에만 ordered shutdown과 Supervisor/Guard/FaultInjector/CM exit0 감사 추가. 기존 G07 moving Goal, ROS Safety TTL, 공식 Nav2 변경 없음.

## 검증 기록

| 검증 | 공개 GitHub Actions | 결과 |
|---|---|---|
| RED 원본 | [#43993759139](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43993759139) | strict child auditor 누락 ImportError, 예상 실패 |
| L0 GREEN | [#43994125321](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43994125321) | 7 unit PASS + bash syntax |
| 실제 Jazzy/Harmonic/Xvfb L2 | [#43994275942](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43994275942) | Nav2 Path 3단계, 공식 manager shutdown ACK, Supervisor·Guard·FaultInjector·CM 실제 child exit0, 엄격 teardown PASS |
| 새 Owner 실행기 L0 | [#43994851897](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43994851897) | 5 public-only tests, exact Git blob, --self-check PASS |

### 새 Owner 실행기 exact pins

- Instructor runtime source: `a2ea5bbebf7c24137353773f88984dd4cf6d9383` (**기능 코드 SHA**, 비공개 보고서 후속 커밋과 다름).
- Public Owner one-shot source: `scripts/axia_d07_h01_gpu_gui_owner_wsl2_once.sh`, 테스트 `tests/test_axia_d07_gpu_gui_owner_contract.py`.
- Public L2 proof `43994275942`, public L0 proof `43994125321`.
- 새 브랜치: `fix/d07-h01-owner-p4-teardown-c26-20261117`; 과거 `main` SHA와 이전 Owner 성공 증거 보존. main 병합은 사용자 승인 대기.

## 기대와 한계

`D07_H01_NAV2_ORDERED_SHUTDOWN_ACK_BEFORE_SIGINT` → `D07_H01_CHILDREN_CLEAN_AFTER_ORDERED_SHUTDOWN` → `P2_L2_SMOKE_RC=0`. 비정상 자식 종료/ACK 누락이면 `D07_H01_CHILD_SHUTDOWN_BLOCKED`, rc=3; 부모 종료만으로 clean을 주장하지 않는다.

이 릴리스는 **GitHub CI Xvfb 실물 Gazebo L2 + 공개 Owner L0** 범위다. 개선판 Owner WSL2 실측 NOT_RUN, 자연발생 RMW ACK-loss, 실제 주행 중 Scan→Supervisor→CM→Guard TTL, 자동 GUI 픽셀은 UNVERIFIED. Software Stop은 인증 E-Stop이 아니며 전체 `AXIA_MVP_DEMO_ACCEPTED=HOLD` 유지.
