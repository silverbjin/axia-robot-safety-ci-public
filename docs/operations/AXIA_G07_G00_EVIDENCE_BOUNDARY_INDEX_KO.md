# AXIA G07 G00 — 최초 장애 경계 / SHA 동결 / 중복 구현 방지 인벤토리

- 날짜: 2026-11-21 KST.
- 범위: **기존 공개 CI artifact 원본을 읽은 G00 read-only 증거 동결**. 신규 Goal, Gazebo/WSL2 실행, runtime 수정 없음.
- 기준 문서: `AXIA_Robot_Safety_MVP_Baseline_Scenario_Acceptance_v1_KO.md`(기준값은 현행 CI 계약대로 유지).
- Public #215 `diag/g07-first-scan-rmw-exact-native-20261121` 기준 `344b06cb3e26d7e009bfe8f2cc4da90a1ad07376`; Student #89 `diag/g07-rmw-messageinfo-capability-20261121` `6895f90815fe62a4358abe6b306854af5b8cb6a5`.
- 공개 #211 S1 I/O, #212/#213 S3, #214 EventsExecutor 기각, #215 첫 Scan RMW/rosbag 동일 Header, D08 #206 same-world same/independent subscriber A/B를 재개발하지 않는다.

## 수집 증거 해시 (download ZIP 자체 SHA256, 원본 raw bag 파일 아님)

| Native Run / Cycle | Artifact ID | ZIP SHA256 | embedded SHA256 |
|---|---|---|---|
| 44870371777/1 | 14693367287 | `b3367f9b86ed57d1625283d4c08f2ae54a04f4847820df78cd147b9c1b34e0e5` | **6/6 PASS** |
| 44870371777/2 | 14694041862 | `f60aba405e64fcc260f161419ba5944fa901105172031cf9af436cf553bb3d0e` | **7/7 PASS** |
| 44870974857/1 | 14694147401 | `a21eadea8fe8f89864a9013902e277bbc69f1bce3116787ec362498475cd3f1f` | **6/6 PASS** |
| 44870974857/2 | 14694186347 | `f57bb87bda7e9a0bd3ba436285732c56db3b78ae4863fcb32ec7a95c3fcf8ed3` | **6/6 PASS** |
| 44871515361/1 | 14694540399 | `c765eaf3ffee4bf319788f4a9c56e521255a8febb05750b265d6f142615f7f51` | **7/7 PASS** |
| 44871515361/2 | 14694256885 | `270eb55f8fb07d47655a38a92c942b08ea43a8f1ad039e5f95ae544407f29751` | **6/6 PASS** |

확인 명령 (실제로 Python/zipfile로 실행한 동등 명령):
```bash
python3 - <<'PY'
import hashlib,zipfile,os
from pathlib import Path
for p in sorted(Path('/mnt/data').glob('axia_g07*cycle*.zip')):
    z=zipfile.ZipFile(p)
    ok=total=0
    for name in z.namelist():
        if not name.endswith('.sha256'):continue
        raw=z.read(name).decode().strip().split()
        candidate=os.path.dirname(name)+'/'+os.path.basename(raw[-1])
        total+=1
        ok+=int(candidate in z.namelist() and hashlib.sha256(z.read(candidate)).hexdigest()==raw[0])
    print(p.name,hashlib.sha256(p.read_bytes()).hexdigest(),ok,total)
PY
```

## 최초 장애 사건표: 실제 동일 clock-domain 간격만

### 44870371777 Cycle1 (original Multi2) — Goal 이후 최초 Odom delivery breach
- 최초 Observer Odom callback `180.661632101→181.026232955` monotonic, **364.600854ms >300ms**.
- 같은 first cluster의 Scan397.610405ms, Clock343.914547ms, CM pre-Guard388.878454ms >120, Guard350.320489ms >150, Supervisor390.286458ms >150.
- CM **같은 publisher seq+1** RMW Source **50.018636ms** vs original RMW Received **382.004174ms**; 독립 subscriber는 약 50ms 지속. `Source→Received` 직접 절대시간 차가 아닌 **각 쌍의 interarrival** 비교.
- Executor spin Python `_wait_for_ready_callbacks`; pool 두 worker `_worker` idle; heartbeat 계속 실행. Writer lock/write/flush 첫 gap을 설명할 300ms 정지 미측정.
- 관측 Supervisor 첫 전이 `BOOT_SAFE→NORMAL` monotonic 180.290259539 (**첫 gap 전에 발생**, 악화 아님). 실제 **최초 악화 FSM 전이는 관측되지 않았으므로 미입증**. Guard 최초 latch `null`. 다른 시각의 fault를 끌어오지 않는다.
- Run 결과 **Cycle1 FAIL / Cycle2 PASS = strict 2/2 FAIL**. Cycle2에서 첫 gap이 없다는 것이 Cycle1의 원인 수정 증거 아님.

### 44870974857 Cycle1 (20ms bounded wait CI-only, rejected) — Goal 이후 최초 Odom breach
- 최초 Observer Odom callback `237.997552200→238.361702817`, **364.150617ms >300**.
- CM seq+1 Source **50.456883ms** / independent RMW Received **50.411921ms** / original RMW Received **354.987322ms** / original callback **361.513010ms**.
- Executor `_wait_for_ready_callbacks→spin_once(.02)`의 **호출 중**에 첫 160ms 무콜백 스택 캡처; 20ms wait 수정을 해도 실패. Scheduler/RMW 원인은 아직 입증되지 않음.
- Supervisor 최초 `BOOT_SAFE→NORMAL` 237.799646538은 첫 경계 **이전**, 안전 악화 전이 아님. Guard latch null.

### 44870974857 Cycle2 (20ms bounded wait, rejected) — Goal **미발행** 첫 Scan breach
- original Observer Scan callback **600.502826ms >300**, 같은 LaserScan Header simulated interval **102.000ms**; 실제 original RMW Source **107.857389ms** / original RMW Received **599.696375ms**; 독립 rosbag **동일 Header pair** 수신 **107.737729ms**. 원본과 bag의 **DDS publication sequence 일치**를 자동으로 주장하지 않는다.
- PreGoal Scope `HOLD`; 기존 scan·clock·odom 모두 별도 검증. 7채널 postGoal 첫 cluster를 억지로 만들지 않는다. 첫 실제 Supervisor safety 전이 **미수집**(Goal 이전).
- 결론: **A/B 0/2 실패**, 기존 Multi2만 유지. **wait-set/take/원 Observer process의 DDS 수신 경계 후보**이며 실제 세부 root 미확정.

### 44871515361 Cycle2 — 실제 SLOW 실패 (TTL과 별개)
- 최초 실패 `CI_MOVING_GOAL_TIMEOUT_SLOW` (Goal 발행/EXECUTING, CLEAR 통과, native cylinder set-pose ACK 후).
- `slow_timeout_trace` 97 samples, 감속 거리 `0.4<front<0.75`에서 양의 Supervisor vx max **0.000120893411804m/s** (기존 SLOW 최소 >0.005m/s 미충족).
- 첫 표본 전방 **0.6776m**, Supervisor vx **-0.01668698m/s**, yaw 0.126rad; 마지막 odom yaw ~1.520rad, front >1.6m, 장애물이 전방 LiDAR에서 벗어난 현상.
- 보조 관측: 정상 `NORMAL / GOAL_AUTHORIZED`, Guard `FORWARDING_MONITORED_CM`, 최초 안전 악화 상태 미관측. **실제 SLOW/STOP 성공 아님**. 이 오류는 DDS 300ms 지연 해결과 독립적으로 처리해야 함.
- 44871515361 Cycle1 scoped PASS (Scan190.481ms/Clock103.173ms/CM78.349ms 등), 하지만 전체 **1/2 FAIL**. Callstack overrun 미포착, 해결 증거 아님.

## 분리된 다음 개발 질문(2개만)

1. **G10:** 원 Observer callback 빈 구간에서 독립 메시지가 RMW 버퍼까지 정상 도달했는데 *원 프로세스* `rcl_wait` ready→take 사이에서 지연된 것인지, 해당 Observer DDS transport/스케줄러에서 Received metadata 자체가 늦은 것인지, 정확한 same-session 첫 쌍으로 구별한다. 추가 데이터 확보 없이는 Fast DDS SHM 등의 원인이라고 단정하지 않는다.
2. **G20:** 기존 SLOW fixture와 Goal 진행 방향이 달라진 최초 시점을 실제 odom yaw/Scan/front 및 Goal 경로 데이터로 확인하고, **물리 장애물의 배치 시점/헤딩**만 최소 수정한다. 조건 완화나 속도 주입 금지.

## 진입/종료 게이트

G00=COMPLETE_EVIDENCE_ONLY; G10=HOLD; G20=HOLD; G30=strict native 2/2 NOT_PASS; G40 Owner script RELEASE_HOLD; G50 WSL2 NOT_RUN. Full CI가 PASS여도 실제 L2가 FAIL이면 인수준비 아님. 원본 교육 MVP baseline은 불변.
