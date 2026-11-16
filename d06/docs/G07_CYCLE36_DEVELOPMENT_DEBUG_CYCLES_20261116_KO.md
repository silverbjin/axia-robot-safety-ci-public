# AXIA G07 Cycle 36 — 복구·주행·안전 타이밍 개발/디버깅 기록

- 작성: 2026-11-16 KST
- 원장: [G07_CYCLE36_RESTORE_POINT_AND_DEVELOPMENT_INVENTORY_20261116_KO.md](G07_CYCLE36_RESTORE_POINT_AND_DEVELOPMENT_INVENTORY_20261116_KO.md) (코드 수정 **이전** GitHub commit `8acc937fbce03856a04d52b370b6892d82a5763a`)
- 운영: 공식 ROS 2 Jazzy·Gazebo Harmonic·TurtleBot3 Waffle·Nav2 재사용. Safety Supervisor/CM/Guard 속도 제한·TTL·FSM 변경 없음. `AXIA_MVP_DEMO_ACCEPTED=HOLD`. 시뮬레이션 SW 정지, 인증된 E-Stop 아님.
- Owner WSL2 현장 실주행: **이번 주기에서 실행하지 않음**; 강사 최종 한 번만 검수하는 조건 유지. 비공개 Owner 원본·기존 재시도 잠금 삭제/업로드 금지.
- main: **미병합**. 공개 릴리스 워크플로 브랜치 `release/p2-g06-cm-ttl-20261110`는 actual L2 전용 경유지이며 main과 다름.

## 1. HEAD/역할 (매 후속 작업 시 다시 조회)

- Instructor 안전/주행 기능 시작: `420fd276ec1018f7fcc3f14873693cad02f080b4`
- GUI 이전 정상 실행 구조 **참조점**: `db1eec05e01e1db0d0d2e0c05610806ef4e499f9` (`owner-gui → headless=False`); 소스 전체 롤백 금지
- GUI 회귀 도입 의심: Instructor `319f327c...`, Public `30599879...` (분리형 `gz sim -g`, WSLg software EGL, viewer CPU0)
- Cycle36 Instructor 기능 후보: `7f9a2d92d28a4cfd972355dbb76e07059d69c7c6`; 공개 Sidecar 기능 후보: `ccee3dd67981d9b6de18be25b5b8943d58aee8d6`
- Cycle36 latest actual L2 candidate workflow: `072bb4038025d9f6ff79e43494319e6ed2d2e676`; Run `43847651500` **실행 중/최종 판정 미기록**. 추후 실제 완료 판정으로 대체할 것.

## 2. 단계별 RED → GREEN 증거 원장

| 주기 | 최초 실패/문제 | 회귀 RED | 최소 GREEN 및 결과 | 검증 한계 |
|---|---|---|---|---|
| GUI 복구 | GUI 외부 분리+WSLg llvmpipe 충돌 후보, Empty `Entity 0` | public #43839017438 failure | public #43839666672 success, sealed private #43839805413 success | L0 `NO_ROS_NO_GOAL` |
| release preflight | 최신 Marker CPU selector `{2,3,4,5} → CPU5`인데 legacy test CPU4 기대 | real-L2 워크플로 #43840095807 failed *pre-Goal* | public `ccee3dd...`에서 테스트 expectation 수정 | Gazebo를 실행하기 이전 CI 계약 오류; 성공 주장 금지 |
| legacy missing file | 고정 공개 소스에 없는 `test_g07_cycle23_cm_marker_role_conflict.py` 호출 | #43840543618 failure pre-Goal | 실제 존재하는 `test_g07_unified_gui_sidecar_contract.py`로 교체 | 시연 Goal 미실행 |
| GUI 통합 후 종료 | 실제 #43840916334: CLEAR/SLOW/STOP, 7채널, Cancel/Nav2 shutdown ACK은 PASS; **26s 뒤 잔존 `ros2 launch`+ `gz sim -r -s`** | private sealed #43842468717 failure (후행 처분 분류기 미구현) | #43843080534 success: `tools/p4_g07_integrated_gui_shutdown_scope.py`, Goal cancel+양쪽 Nav2 ACK 후 정확히 2 프로세스만 남았을 때 SIGTERM, 다른 노드는 HOLD | L0 GREEN; 실제 새 SHA의 완전 종료까지 L2 미검증 |
| CLEAR 비결정성 | 실제 #43843169022: `CI_MOVING_GOAL_TIMEOUT_CLEAR`, CM/Command 0.30 slowdown, 전진 0.20m, CLEAR 조건 미충족 | #43845565141 failure, 원래 preload obstacle `(-1.81,.25)`가 경로에서 **0.002425m** | #43845741673 success, preload obstacle `(-2.12,.24)`로 경로와 **~0.296m** 이격, 기존 실제 LaserScan 측정 방향 자동 보정 | L0 GREEN; 추가 실제 L2 #43845879169에서 CLEAR/SLOW/STOP 통과 |
| G07 Observer 일괄 지연 | 실제 #43845879169에서 CLEAR/SLOW/STOP 통과, `clock 335ms, cm 369ms, guard 375ms, scan 381ms, source 378ms` 등 같은 Observer 다중 채널 동시 지연. CM RMW source max 128.706ms; 실제 Guard latch 증거 없음. **CI 안전 전달 Oracle은 fail-closed HOLD** | #43847104438 failure (integrated Gazebo GUI GUI-only schedule adapter 부재) | #43847550116 success: 정확히 소유된 `gz sim -g` GUI thread만 이전 단독 Viewer `nice19+lowest CPU` 복원, Safety/Nav2 CM/Guard 불변 | L0 GREEN; 실제 L2 `43847651500` 검증 대상 |

## 3. 원인 가설과 반증 조건을 분리

**GUI:** 구형 `owner-gui headless=False`와 분리 GUI를 섞지 않는다. 신규 `AXIA_G07_CYCLE36_INTEGRATED_GUI=1`에서 Gazebo 공식 통합 GUI를 띄우고 public Sidecar는 `gz sim -g` 중복 생성을 생략, 실제 `gz service -l`과 `gz model --list`로 World/Waffle를 확인한다. CI Xvfb는 실제 WSLg hardware EGL과 동일하지 않다. Window PID만으로 시연 PASS 선언 금지.

**CLEAR:** 시연용 preloaded 물리 원통이 원래 경로 중심에 있었던 것이 실제 0.30 slowdown의 유력 원인. 변경은 원통 초기 배치와 LaserScan probe bearing만이다. 임의 속도·안전 임계값 완화하지 않는다.

**첫 안전 지연:** #43845879169 같은 시점 모든 Observer callback 공백 약 0.34–0.38s와 CM source 0.1287s를 다르게 판단. CM publication 완전 중단 증명 아님. Source 120ms 릴리스 여유는 초과, 안전 Oracle FAIL. 이전 CI에서는 외부 GUI `taskset CPU0 nice19`; 통합 GUI는 기본 nice/CPU로 실행돼 Goal Observer와 경쟁한다는 가설. `p4_g07_integrated_gui_priority.py`는 Gazebo GUI **한 프로세스**만 제한, PID/PGID/UID/thread 및 설정 readback 후 Goal 허용; 없으면 fail-closed. 이 변경이 Observer gap을 없애는지는 실제 L2로만 판단.

**종료:** Nav2 lifecycle ACK 후 남은 `ros2 launch`와 Gazebo server 두 프로세스 종료를 기존 timeout 완화로 해결하지 않는다. 정확히 잔여 프로세스 두 개만 있다는 증거일 때만 bounded TERM. Guard, CM, Nav2, unknown PID 남아 있으면 FAIL·기존 원본 보존.

## 4. 현재 가드레일과 완결 정의

`AXIA_MVP_DEMO_ACCEPTED=HOLD`는 릴리스 전까지 유지한다. L0 PASS≠Gazebo 성공. 실제 Gazebo L2는 같은 private SHA/tree와 public GUI source를 사용해야 하며, 원본 14-topic bag, World/Waffle 실제 GUI, Goal EXECUTING, CLEAR→SLOW→STOP, 모든 안전층 7채널 주기와 native RMW source/receive, Odom 정지 ≥1s, 네이티브 Contact 0, 정확한 Goal Cancel ACK, Nav2 shutdown ACK, CM exit0, launch cleanup, CRC/SHA 보관이 모두 필요하다. Owner WSL2는 공개 CI GREEN 후 **최종 1회만** 수행하며 수동 TTY 승인만으로 실제 Goal 허가. 학생 정답/Private 원본 공개하지 않는다.

## 5. 재개해야 할 정확한 다음 동작

1. 공개 L2 #43847651500 상태·failed 최초 단계 조회.
2. CI PASS일 때만 해당 source+tree, 공용 GUI blob 및 원본 실측 데이터로 별도 Cycle36 Owner bootstrap/gate를 구성, 부트스트랩 고정 SHA 일치 테스트.
3. CI FAIL일 때는 마지막 문자열이 아니라 실제 최초 7채널/Guard/Nav2/Goal 타이밍 경계를 CI 재현 RED로 고정하고 최소 변경. 다른 계층 타이밍 통과를 모두 재확인.
4. 원본 실패, 승인 기록, Git 브랜치·커밋·테스트 출력·미검증 항목을 이 문서에 **순차 갱신**. main 병합 및 Owner 현장 재주행 금지.

*인수: 실제 Owner L3 `NOT_RUN`, 사용자 한 번 최종 검수 조건에 따라 모든 개발을 공개 CI 선행으로 진행.*
