# AXIA D05 공개 GitHub Actions `main` 통합·브랜치 이력 (2026-11-15)

**공개 CI 원칙:** D05는 공식 ROS 2 Jazzy / Gazebo Harmonic의 Waffle RGB-D/YOLO 관찰과 소스·증거 검증을 수행하는 read-only 교육 범위다. 강사 정답·hidden tests는 private instructor repo에만 남겨둔다. **비공개 저장소의 GitHub Actions는 사용하지 않으며, 이번 병합은 어떠한 비공개 checkout, 보호 환경, Goal 또는 안전제어 재실행도 수행하지 않는다.**

## D05 브랜치와 누락 여부

| 브랜치 | PR / 처리 상태 | 기능 / 역사 | 현재 `main`에서의 결정 |
|---|---|---|---|
| `feature/d05-sealed-l0-l1-20261109` | 초기 protected D05 L0/L1 staging | 비공개 Instructor SHA를 `axia-instructor-sealed` 보호 환경에서 가져오는 과거 CI 분리 시도 | `main`과 diverged, ahead 1. 현재 `main`에도 **별도 수정된 `d05-private-sealed-l0-l1.yml`**이 이미 존재함. 구형 브랜치 전체 merge **제외**; 비공개 자격증명 우회 금지 |
| `feature/d05-real-rgbd-l2-20261110` | [#28](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/28) MERGED | 동일 카메라 `rgbd_camera`, 실제 YOLO `person`, ROS Depth ROI 실측·Validity/UNKNOWN oracle, evidence sanitization, Owner WSL2 공개 Wrapper, Python L0/L2 | `main` 대비 `ahead_by=0`; 공개 D05 실제 RGB-D 핵심 4파일은 PR HEAD와 `main` Git blob SHA 동일. 추가 merge 불필요 |

## 이번 D05 통합에서 보존한 실제 기능

- `scripts/d05_rgbd_gazebo_scene.py`: 공식 Gazebo RGB-D와 human Actor scene 생성.
- `scripts/d05_real_rgbd_l2_gate.py`: real ROS RGB/Depth/YOLO와 D05 관찰 판정, 중간값·stamp·UNKNOWN 확인.
- `scripts/d05_rgbd_sensor_preflight.py`: 실제 camera image/registered Depth 사전 조건.
- `scripts/axia_d05_rgbd_wsl2_once.sh`: 기존 Owner 실행기 및 정확한 app/Observer SHA 추적.
- `scripts/d05_l2_safe_export.py`: 민감 강사 코드/가중치 제외하고 안전한 JSON/PNG evidence 추출.
- `tests/test_d05_real_l2_contract.py`, `tests/test_d05_owner_wsl2_once.py`, `tests/test_d05_rgbd_scene.py`, `tests/test_d05_safe_export.py`: 기존 source-only 계약.
- 기존 Workflow: `d05-l2-source-contract.yml`, `d05-owner-wsl2-wrapper-contract.yml`, `d05-real-rgbd-sensor-preflight.yml`.
- 구형 `d05-private-sealed-l0-l1.yml` 및 `d05-real-rgbd-sealed-l2.yml` 파일이 기존 `main`에 존재할 수 있지만, **이번 검증에서 실행하지 않고** 이를 오늘의 D05 Owner·Gazebo 승인 근거로 사용하지 않는다. 향후 새로운 공개 CI 검증은 공개 소스/고정 SHA만으로 허용되는 경로를 사용한다.

## 공개 CI와 WSL2 인수의 경계

- [실제 sensor-only Gazebo preflight #42644462764](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/42644462764): 공식 RGB-D 카메라, 640×480 registered RGB/Depth, 3개 정합 timestamp, 실제 약 2.125m.
- [이전 L2 #42646086413](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/42646086413): **49 pytest PASS, upstream yolo_ros 5패키지, D05 Observer 1패키지**, 실제 Gazebo YOLO `person` confidence **0.9005**, real ROI **2.179178m**, 유효 픽셀 **46267/57620=80.2968%**, Depth만 정지했을 때 `UNKNOWN/STALE_INPUT/null` (RGB/YOLO 지속). 이 실행은 **당시** 공개 CI 보호 경로를 사용했으며, 정책이 변경된 지금의 정기적 CI 재실행을 의미하지 않는다.
- [Owner Wrapper 정적 시험 #42649245483](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/42649245483): bash -n/self-check, 10 pytest PASS, 실제 Owner Goal/ROS/Gazebo는 NOT_RUN.
- 사용자 원본 WSL2 인수는 Instructor PR #76/#124에서 기록된 **이전 관찰 코드**의 RESULT이며, 2026-11-13 `VALID` 90초 유지 후 Depth 차단 순서 수정판의 새 WSL2 종단 인수나 0.5초 데이터 전달 주기·TTL 전체 안정성을 증명하지 않는다.
- **D05 실습 결과는 read-only 센서 관찰이다.** 안전 정지 성능/CM·Guard TTL/Goal 취소/충돌 회피, 인증된 하드웨어 E-Stop에 대한 PASS 주장이 아니다.

## 새 작업 기준

```bash
git fetch origin main
git switch main
git pull --ff-only origin main
git switch -c feature/d05-next-task
```

이 문서는 D05 관련 브랜치 역할을 기록하기 위한 **문서 추가만** 수행한다. D05 런타임·공식 Nav2·Safety TTL·Instructor 정답·모델 파일의 변경이 없으므로 기존 L2를 중복 실행하지 않는다. 필요 시 재현 가능한 실패 경계에서만 공개 CI RED→GREEN 회귀 추가 후 인수한다. **main 병합은 사용자가 명시적으로 승인한 D05 이력 정리 범위에 한정**한다.
