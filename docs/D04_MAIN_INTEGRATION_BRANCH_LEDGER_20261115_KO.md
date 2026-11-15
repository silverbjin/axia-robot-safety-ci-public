# D04 공개 CI `main` 통합·브랜치 역할·검증 경계 (2026-11-15)

**범위:** 공개 CI 코드와 D04 배포 실행기 관리. 공개 ROS 2 Jazzy/Gazebo Harmonic/YOLO 근거는 아래 명시한 실제 Actions job에 한하며, 사용자 WSL2 WSLg 실제 인수·Nav2 Goal·Guard 종단 안전을 자동 승인하지 않는다.

## D04 기존 PR 처리 완료 목록

| 소스 브랜치 | PR / 상태 | 역할 및 결정 |
|---|---|---|
| `preflight/d04-gazebo-rgb-20261108` | [#7](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/7) **CLOSED NOT MERGED** | 구형 기본 Waffle RGB discovery. 현재 main보다 diverged이며 신규 3개 파일만 별도로 남음. 이후 공식 Waffle Pi/YOLO 검증이 대체: MVP 불필요 중복, **제외** |
| `preflight/d04-waffle-pi-rgb-20261108` | [#8](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/8) **MERGED** | 공식 ROBOTIS Waffle Pi 실제 카메라 RGB ROS Image/CameraInfo/Stamp/manifest |
| `preflight/d04-yolo-person-20261108` | [#9](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/9) **CLOSED, SUPERSEDED** | 실제 사람 Actor→RGB→고정 upstream `yolo_ros` bbox/confidence; main 대비 ahead=0, 중복 병합 금지 |
| `preflight/d04-p1-yolo-integration-20261108` | [#11](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/11) **CLOSED, NOT MERGED** | P1 동시 sidecar/YOLO 반복 안정성; main에 포함되지 않은 유일한 잔여 변경은 `d05-private-sealed-l0-l1.yml` 비공개 Actions 경로. **비공개 Actions 금지 정책에 따라 제외** |
| `feature/d04-yolo-ros-package-20261109` | [#14](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/14) **MERGED** | 강사 ROS 패키지의 공개 소스 대조, Jazzy colcon/launch 검증·공개 WSL2 원샷 |
| `fix/d04-course-field-preflight-20261112` | [#59](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/59) **MERGED** | WSL2 Python 의존성/잘못된 cwd/학생 RED 오류 회귀 진단 |
| `fix/d04-owned-gui-shutdown-20261112` | [#61](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/61) **CLOSED, SUPERSEDED** | Gazebo 창 닫을 때 image_view 재생성 문제, 소유 프로세스 종료·정리. #62 통합본이 모든 커밋 포함(`ahead_by=0`), 중복 병합 금지 |
| `feat/d04-instructor-single-image-20261112` | [#62](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/62) **MERGED** | 강사 단일 이미지 실제 추론·bbox/class/confidence PNG/HTML + 종료 감사 + 최종 공개 CI 계약 |

GitHub REST `compare(main...head)` 대조: #8/#9/#14/#59/#61/#62는 `ahead_by=0`; #7의 구식 독립 preflight(3파일)와 #11의 비공개 환경 Workflow(1파일)만 앞선 변경이 남아 있어 **의도적으로 main에 추가하지 않는다**.

## D04 공개 CI 대표 근거

- Waffle Pi 실제 Gazebo RGB → upstream YOLO: [#43166114547](https://github.com/silverbjin/axia-robot-safety-student/actions/runs/43166114547) (별도 학생 저장소의 public GitHub Actions, 실제 Gazebo headless).
- Gazebo/YOLO 두 창 Xvfb GUI 확인: [#43166756309](https://github.com/silverbjin/axia-robot-safety-student/actions/runs/43166756309) (WSLg 실화면은 별도).
- 강사용 image_view 소유권 종료: [#43172990347](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43172990347) — 실제 ROS Jazzy image_view Xvfb 창, 부모 종료 후 자식 미재생성.
- 원본 `--single-image` CPU YOLO: [#43179962136](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43179962136) — 공식 `yolo26n.pt` / bus.jpg, person 4명, 출력 좌표·class/confidence 및 PNG/HTML.
- D04 최신 계약: [#43180616144](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43180616144) — 39 PASSED. **과거 소스의 L0/L1 증거**를 이 문서만으로 최신 WSL2 runtime PASS로 승격하지 않는다.

## 새 작업의 원칙

1. 다음 D04 작업은 public CI 저장소의 **`main`에서 새 브랜치**를 생성하고 기존 `scripts/axia_d04_classroom_wsl2_once.sh`, `scripts/axia_d04_instructor_single_image_once.sh`를 재사용한다. 별도 중복 D04 계층을 만들지 않는다.
2. **강사 정답**은 private instructor repo에서만 보관하고, **학생 TODO**는 independent public student repo에서만 관리한다. 공개 CI runner로 가능한 검증만 하며 **비공개 Actions/보호 환경 우회를 하지 않는다**.
3. 새 현장 장애는 **최초 실패 PID·최초 잘못된 안전 상태 전이·최초 전달 주기 위반**을 공개 CI 재현 가능한 범위에 먼저 RED로 반영한다. 안전 TTL/공식 Nav2/Supervisor 또는 E-Stop 인증 범위를 임의 확장하지 않는다.
4. 이번 게시 파일은 문서만 추가한다. 기존 D04 ROS/Gazebo/ONNX 테스트 성공 증거와 런타임 소스를 **그대로 유지**한다. 새 실행기의 실제 ROS/Gazebo test PASS를 주장하지 않는다.

## 재현 및 main 병합 검토

```bash
git clone --branch main https://github.com/silverbjin/axia-robot-safety-ci-public.git
cd axia-robot-safety-ci-public
git log --oneline -- .github/workflows/d04-course-docs-regression.yml
# 신규 수정 시 main에서 별도 PR, 공개 Actions 재검증
```

본 문서의 브랜치 역할/커밋 포함 여부는 GitHub PR 상태와 `compare_commits`로 확인했다. `main` 병합은 사용자의 이번 요청으로 명시 승인된 **D04 정리 범위에 한정**한다.
