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

## 3A. 추가 Cycle36 재개 진단 (2026-11-16, 원본 CI Run 대조)

- **실제 L2 #43847651500 — Goal 전 차단:** Gazebo World·Waffle·RViz 준비, NO_GOAL stage, `G07_GUI_READY_ATTESTED_PRE_GOAL`까지 실측. 그러나 `AXIA_G07_CYCLE36_OWNED_GAZEBO_GUI_NOT_UNIQUE_NO_GOAL`로 GUI PID 식별 실패; ROS Goal 전송 안 함. 이는 안전 계층의 실행 실패나 인증된 stop 증거가 아님.
- **원인 공식 소스 교차 확인:** Nav2 Jazzy `tb3_simulation_launch.py`는 `ros_gz_sim/gz_sim.launch.py`를 통해 GUI를 열고, Gazebo 공식 ROS 2 launch는 `ruby <gz 실행 경로> sim ... -g --force-version 8` 형태로 프로세스를 호출한다. 자체 GUI PID 검사기는 `gz sim -g`만 허용해 **정상 공식 Ruby 실행 형식**을 누락했다. (공식 공개 출처: https://api.nav2.org/nav2-jazzy/html/tb3__simulation__launch_8py_source.html ; https://github.com/gazebosim/ros_gz/blob/ros2/ros_gz_sim/launch/gz_sim.launch.py.in )
- **공개 CI TDD RED #43848704106**: private `tests/unit/test_g07_cycle36_gui_priority_isolation_20261116.py`에 공식 `ruby /opt/ros/jazzy/opt/gz_tools_vendor/bin/gz sim -v4 -g --force-version 8` fixture를 추가; `AssertionError: None != 2320`.
- **공개 CI GREEN #43848916833**: private `tools/p4_g07_integrated_gui_priority.py`가 UID/PGID 일치 및 지정된 ROS Jazzy gz 경로, `-g`·8버전을 갖춘 Ruby 실행 형식과 기존 직접 `gz sim -g`를 구분. 일반 Ruby `/tmp/gz` 및 `-s` 서버 거부. 소스 `ce9da373dd98269a38d77aade173425f0faf1a21`, unit/shell L0 PASS.
- **새 실제 Gazebo L2 #43849019677**: public workflow `c6ea0dc1970b06028c5c5dbd3f9ae382f8867914`에서 새 Instructor SHA를 사용한 실제 Gazebo Goal 후보를 검증 중. **이 문서 기록 시 결과 미판정**; 완료 여부를 Actions 원본에서 조회해 보완할 것.
- 변경 후 검증 미완료: 정확한 ROS GUI PID/threads runtime readback, 7채널 TTL, CM source/RMW, native Contact, original 14-topic bag, Cancel/Shutdown/Clean exit, WSLg renderer. 이 항목들은 **HOLD**.

## 3B. 실제 CI의 두 독립적인 후속 위반 (2026-11-16)

**실제 Gazebo L2 #43851121310**, Private `e94f84802d56080a5a11364ebad20fa25d785d2f`:
- `AXIA_G07_CYCLE36_OFFICIAL_GUI_LOW_PRIORITY_VERIFIED_NO_GOAL pid=2328 cpu=0 nice=19 threads=26` — 실제 GUI PID 검증 PASS. `CLEAR→SLOW→STOP` 실제 주행, `odom_dwell=1.029s`, Goal Cancel ACK, Nav2 shutdown ACK, `CM_CLEAN_EXIT`, bag, S02 native Contact 0/32899 iterations PASS.
- **릴리스 120ms 목표 FAIL**: CM Observer 최대 `0.135076s`, CM RMW Source 최대 `0.131583s`, Supervisor upstream publication 사이 최대 `0.0498s`; 150ms Guard 하드 TTL 미초과, Guard latch 관찰 없음. 시연 전체 승인 불가. 게시자 스케줄링 원인 입증 아직 안 됨.
- **읽기 전용 Marker 생존 실패 후보**: 실 World·RViz 창 확인, 그러나 Goal 구간의 `readonly_samples.jsonl`에서 실제 Scan 수신 증거 없음. World/GUI 프로세스 존재만으로 Marker 통과 아님.

**진단 추가 L2 #43852572728**, 동일 private source, 별도 공개 workflow `cd986f273bf0751f8942b4adae03b54f2cc4cc03`:
- Marker 샘플 3개만 `t_monotonic 356.033–358.035s`, 실제 Goal 시작 `382.631s`. **Goal 24초 전에 Sidecar가 종료**; `sidecar.log`에 `line 101: 1: command not found`, `line 171: 1: command not found`, `G07_UNIFIED_GUI_CHILD_EXITED_EARLY_UNVERIFIED`.
- 원인은 `d06/scripts/g07_shared_gui_clients.sh`에서 `( "$INTEGRATED_GUI" != 1 && ... )`와 `( "$INTEGRATED_GUI" == 1 || ... )`를 Bash **명령**으로 실행한 오류다. `1`이라는 실행파일을 찾다가 실패했음. Linux·GPU 또는 ROS2 Scan 장애로 오진 금지.
- **공개 L0 RED #43853421097 → GREEN #43853544471**: 두 조건식을 `{ [[ "$INTEGRATED_GUI" != 1 ]] && ...; }` / `{ [[ "$INTEGRATED_GUI" == 1 ]] || ...; }`로 교정. Public GUI source `132d8c64def534061d3467f3e1a339fbb44e3e68`, 오직 2줄 변경.
- 동일 실행에서 Nav2 Lifecycle navigation service `SERVICE_TIMEOUT` (40초)도 관찰; Goal 주행은 CLEAR/SLOW/STOP을 달성했으나 **종료 인수는 별개 FAIL**이다. Sidecar를 수정해도 Nav2 shutdown 재검증이 필요하다.
- 원본 Goal 중 7-channel Observer는 clock~0.10s / CM~0.135s / Scan~0.194s, RMW CM publication >120ms 재현. 기존 150ms TTL과 120ms 릴리스 목표 유지.
- 변경된 Public GUI 소스를 사용한 실제 Goal 후보 Run **#43853632352**는 이 문서 작성 당시 **진행 중**. L2 실제 종료 판정 전 `AXIA_MVP_DEMO_ACCEPTED=HOLD` 유지.

### 개발 원칙 재확인
- 확정된 Sidecar Bash 오류와 아직 원인 미증명 CM 발행 120ms 초과를 서로 섞지 않는다.
- `0.135s < 0.150s`는 120ms *릴리스 여유*를 PASS로 판정할 근거가 아니다.
- 비공개 Owner 원본을 공개 CI에 복제하지 않는다. 공개 CI에는 비식별 수치와 테스트만 포함한다.
- #43852572728 Nav2 shutdown service timeout은 후행 실패, CM source 전이와 독립적으로 조사한다. timeout 확대만으로 성공 처리 금지.

## 4. 현재 가드레일과 완결 정의

`AXIA_MVP_DEMO_ACCEPTED=HOLD`는 릴리스 전까지 유지한다. L0 PASS≠Gazebo 성공. 실제 Gazebo L2는 같은 private SHA/tree와 public GUI source를 사용해야 하며, 원본 14-topic bag, World/Waffle 실제 GUI, Goal EXECUTING, CLEAR→SLOW→STOP, 모든 안전층 7채널 주기와 native RMW source/receive, Odom 정지 ≥1s, 네이티브 Contact 0, 정확한 Goal Cancel ACK, Nav2 shutdown ACK, CM exit0, launch cleanup, CRC/SHA 보관이 모두 필요하다. Owner WSL2는 공개 CI GREEN 후 **최종 1회만** 수행하며 수동 TTY 승인만으로 실제 Goal 허가. 학생 정답/Private 원본 공개하지 않는다.

## 5. 재개해야 할 정확한 다음 동작

1. 공개 L2 #43847651500 상태·failed 최초 단계 조회.
2. CI PASS일 때만 해당 source+tree, 공용 GUI blob 및 원본 실측 데이터로 별도 Cycle36 Owner bootstrap/gate를 구성, 부트스트랩 고정 SHA 일치 테스트.
3. CI FAIL일 때는 마지막 문자열이 아니라 실제 최초 7채널/Guard/Nav2/Goal 타이밍 경계를 CI 재현 RED로 고정하고 최소 변경. 다른 계층 타이밍 통과를 모두 재확인.
4. 원본 실패, 승인 기록, Git 브랜치·커밋·테스트 출력·미검증 항목을 이 문서에 **순차 갱신**. main 병합 및 Owner 현장 재주행 금지.

*인수: 실제 Owner L3 `NOT_RUN`, 사용자 한 번 최종 검수 조건에 따라 모든 개발을 공개 CI 선행으로 진행.*
