# AXIA D08 Task02 — 실제 World의 3상 공식 Nav2 경로·Scan·Costmap 통합

## 작업 기준
- Public CI: `silverbjin/axia-robot-safety-ci-public`, branch `feat/d08-unified-sensor-cm-path-20261118`, base main 62e366b51c64da25ad0216328fe1e019b78e0bef, PR #166.
- 1차 성공 재사용: #44211587111 (HEAD 05503ecc434152ac497e3ae4b1535516a5410fc4) 공식 ONNX Runtime/YOLO ROS L1, 동일 World의 AMCL/TF/첫 official Nav2 Path L2. 각각 독립 job. 이번 E2E로 합치지 않음.
- D07 참조는 Student real L2 #44051183220: 물리 Proxy before world(-0.58,-0.5) → intrusion(-1.979118934,0.171291396) → restore(-0.58,-0.5) 및 official goal map(-1.7,0.7). **D08에서 값만 후보로 쓰고 검증을 새로 수행**.
- PLAN 고정 커밋 18c4eb448b503ba96f98d3851412ac9d29e1284e.

## PLAN → RED → GREEN → REFACTOR → REVIEW → COMMIT
- **실제 RED**: commit 1c3dc3e0ce90455effe1126b29084e96df538bcf, public Run #44226134951, L0 suite error `ModuleNotFoundError: No module named 'd08_same_world_replan'`; node/actual Gazebo L2 are SKIPPED. 기존 D08 official Nav2 first Path는 ONE phase만 보유한 결손과 테스트 우선 증거.
- GREEN candidate: `d08/harness/d08_same_world_replan.py` 단일 읽기전용 관측기. 같은 Gazebo 서버의 native /set_pose ACK 3회, 실제 /scan 및 official /global_costmap/costmap subscriber, 실제 /odom 정지, map→base_link TF, 공식 /compute_path_to_pose 3회 원본 Path를 JSONL에 기록. 다음 경로 사용: original Path와 물리 장애물 사이 최소 거리 비교; near-before >=0.15m / restored-before <=0.12m. Costmap 인체 lethal 마킹 3셀 이상 증가, 복귀 후 원래 수준 회복.
- 고정 실패 경계: 센서 header stamp/steady received gap 0.5s, 프레임·Costmap map 좌표·Action status, 원본 여명/restore native ACK, `Goal_SENT=False` 기록. CM 실제 /scan 구독자 그래프는 discovery로만 기록; actual CM receive interval/Guard age **미측정**.
- `d08/scripts/d08_public_gazebo_l2.py`에 `--official-path-phases` opt-in만 추가; 이전 `--official-nav2` first Path 및 독립 sensor/YOLO CI job 보존. `.github/workflows/d08-main-no-goal-real-gazebo-l2.yml`의 동일 official Nav2 job에만 옵션 부여.
- L0: `python3 -m pytest -q d08/tests/test_d08_same_world_replan.py`; actual L2 `python3 -u d08/scripts/d08_public_gazebo_l2.py --actor <pinned-walk.dae> --out results/d08-official-nav2-sameworld --official-nav2 --official-path-phases`.
- GREEN exact HEAD L0 및 실제 L2 출력: 신규 Run 이후 기록. 이미 통과한 테스트를 근거 없이 PASS 승격하지 않음.
- REVIEW: Nav2 Planner/Controller/CollisionMonitor 코드 불변, /cmd_vel publisher 추가 없음, 인증 E-Stop 주장 없음, D05/YOLO와 영상이 동시에 연결됐다는 주장 없음. 다중 World·서로 다른 SHA의 데이터 혼합 금지. G07 moving 별도 HOLD.

## 증거 판정
- Source, Domain/Partition, map/scan stamps, path polylines, original Gazebo native ACK, first scan receive gap -> `official_path_phases/{verdict.json,path_phases.jsonl,*_native_ack.txt}` 및 기존 `runtime_provenance.json`.
- 새 HEAD actual L2: **NOT_RUN** (커밋 직후 공개 CI에 의해 판정). Owner WSLg NOT_RUN.
- Task01 실제 2 VALID+UNKNOWN HOLD; Task02 전체 same-world YOLO+Depth·real CM→Guard 타이밍 HOLD; Task03 G07 moving strict HOLD. main 병합 NO.

## 다음
- 첫 실제 위반(Scan gap, Costmap mark, Path Δ, TF 등)을 원본 timestamp와 단계별 이벤트로 좁혀 CI 회귀를 먼저 수정. 한계를 우회하지 않음.
- 단계 성공 후 Task01 actual real-time YOLO/Depth 2 VALID+1 UNKNOWN 및 official CM source 주기 관측을 **같은 running world**에 통합.