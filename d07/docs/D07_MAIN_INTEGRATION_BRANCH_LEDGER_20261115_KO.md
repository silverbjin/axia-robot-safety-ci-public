# D07 공개 CI main 통합 인계 — 2026-11-15

**기준:** 공식 ROS 2 Jazzy Nav2 `nav2_planner` / `NavfnPlanner` / `Costmap2D`의 실제 격리 ROS L1과 P4/G07/H01의 실제 이동 인수를 구분한다. 새 Nav2 planner/Controller/Safety Supervisor는 만들지 않는다.

## 개발 브랜치·PR 처리

| 브랜치 | PR 및 현재 상태 | 역할 | 통합 결정 |
|---|---|---|---|
| `feature/d07-nav2-human-aware-20261110` | [#35](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/35) MERGED | official PlannerServer·ObstacleLayer/InflationLayer/Scan→ComputePathToPose 3단계 격리 ROS L1, params, WSL2 SHA-pinned wrapper, L0 fixture | 이미 main에 포함, 원본 변경 불필요 |
| `feat/d07-h01-motion-lesson-20261114` | [#115](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/115) Draft/HOLD | H01 실제 Gazebo 장애물/물리 Contact, Costmap spatial clearing, CM→Guard TTL, 이동 Goal/P4 인수 스크립트 다수 포함 | **전체 main 병합 금지** (현재 main과 크게 diverged, 다른 P2/P4 안전 게이트 포함) |
| `release/d07-official-nav2-main-20261115` | 본 공개 CI 릴리스 PR | 최신 main에서 기존 검증된 `d07-official-nav2-planner-l1.yml` 재사용, D07 인계 문서·실제 공식 ROS L1 재실행 | 공개 Actions 소스 L0 및 real ROS L1 성공 후 병합 |

## 실제 검증과 잔여 조건

- [공식 Nav2 Planner Costmap ROS L1 #42661513782](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/42661513782): synthetic `/axia/d07/test/scan`으로 lethal cell **0→101→0**, 공식 Navfn `ComputePathToPose` poses **58→74→58**, 최소 인체 Proxy 경로 clearance **0.4727709m**. Test-only ROS graph `/cmd_vel` publisher **0**. **Gazebo 주행/ControllerServer/odom/Contact 미실행**.
- [2026-11-15 H01 실제 Gazebo Gate1 #43673228520](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43673228520): 실제 실물형 장애물 → Costmap Lethal 0→102→0, Planner 경로 detour 0.3849m, clearing 후 delta 0.0443m, scoped geometry PASS. **NO moving Goal**.
- 해당 H01 장면에서 **CM→Guard 150ms TTL**과 동적 주행 Contact-free, Nav2 `NavigateToPose`, odom stop dwell, 정상 lifecycle shutdown, 실제 WSL2 Owner L3는 **NOT_ACCEPTED/HOLD**다. Gate1을 moving L3 PASS로 승격하지 않는다.
- 이번 `main` 통합은 구형 ROS L1 코드를 **수정하지 않고**, 브랜치 인계 문서와 공개 CI Workflow 대상에 릴리스 브랜치를 추가하여 최신 main 기준으로 재실행한다. 원본 D07 제어코드 및 `nav2_costmap_2d` upstream은 유지한다.
- **SW Stop은 인증된 HW E-Stop이 아니다**. 강사용 정답·hidden tests는 private instructor 저장소에만 있고, 여기서 비공개 GitHub Actions나 보호 환경 비밀 토큰을 사용하지 않는다.

## 후속 D07 개발

```bash
git fetch origin main
git switch main
git pull --ff-only origin main
git switch -c feature/d07-next
```

성공한 공식 Nav2 격리 Planner L1은 재사용하며, **실제 moving H01 안전 인수는 #115/#163에서 별도 Gate**로 진행한다. 새 현장 오류는 최초 CM source/receive TTL 위반부터 공개 CI 회귀에 추가한다.
