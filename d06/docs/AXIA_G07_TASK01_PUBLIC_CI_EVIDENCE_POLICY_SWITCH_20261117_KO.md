# AXIA G07 — Task01~04 공개 CI 증거보존 정책 전환 및 실행·검증 보고서

**기록일: 2026-11-17 KST | 정책 결정: PUBLIC CI ONLY FOR PRE-OWNER CI, NO PRIVATE WRITE SECRET | 최종 인수: HOLD**

## 0. 변경 목적과 오해 방지

과거 `AXIA_G07_EVIDENCE_WRITE_TOKEN`은 **private repo GitHub Actions를 호출하기 위한 토큰이 아니었다**. 공개 CI `silverbjin/axia-robot-safety-ci-public`에서 읽기 전용으로 checkout한 비공개 Instructor 증거 브랜치에 원시 파일을 **push**하기 위해 요청했던 별도 `Contents: Write` 권한이었다.

사용자 새 정책: **Task01~04의 최종 WSL2 Owner 인수 전 작업은 공개 CI에서 수행한다.** 그러므로 신규 private write credential 발급과 private evidence 브랜치에 push하는 동작을 현재 실행 흐름에서 제거한다. 기존 비공개 Instructor 정답 코드는 그대로 비공개이고, 공개 CI가 재사용할 때는 기존 sealed environment의 **읽기 전용 `AXIA_CLOUD_CI`**만 사용한다. 이 설정은 비공개 저장소의 GitHub Actions 실행이 아니다.

공개 증거 범위는 **비공개 원본이 아닌 allowlist 기반의 수치형 time-domain envelope + SHA256**로 제한한다. 공개 JSON을 열람할 수 있는 사람에게도 강사 소스/개인정보/기존 로봇 위치·라이다/카메라 데이터는 제공하지 않는다. LTTng trace·ROS bag·TF raw·메모리 주소는 업로드하지 않는다.

## 1. 기존 분리 원칙과 불변 안전 조건

- 원본 공식 Nav2/TB3 Waffle/Gazebo Harmonic·Jazzy 재사용. C34 종료 계약은 별도 source SHA 검증 후에만 통합.
- CM RMW source 간격 ≤120ms **AND** observer 간격 ≤120ms는 **최종 tracer-OFF 실제 Moving Goal에서** 각각 수치 검증.
- Guard hard TTL150ms/Scan·Odom·Clock300ms/정지0.40m·감속0.75m/실제 ZERO dwell≥1s/Native Contact0/Goal exact UUID terminal/Navigation+Localization native ACK/CM exit0/14-topic bag.
- TF 진단/LD_PRELOAD/LTTng ON 결과는 tracer-OFF 성능 수치가 아니다. 수집된 타이밍은 원인분석 전용이다.
- 시스템 클록: RMW publisher `source` **SYSTEM**, Observer callback/TF sleep **MONOTONIC**, 시간영역 동등성·sender host 확인 전 별도 offset만 보존. 두 숫자를 무작정 차감하거나 원인 증명으로 승격하지 않는다.
- `base_shift_correction=true`, `source_timeout=1.0s`, tolerance0.02s, 기존 정책/STOP geometry 변화 없음. 소프트웨어 STOP은 인증된 실제 E-Stop이 아니다.
- Owner WSL2 L3는 **사용자 최종 현장 검수**, 아직 실행하지 않음. `main` 병합은 별도 승인.

## 2. RED→GREEN 공개 CI — 재현·수정·실제 파일 업로드

### RED: 비공개 원본을 안전하게 외부로 보낼 수 있는지 확인하는 최소 회귀
- 경로: `d06/tests/test_g07_task01_public_evidence_allowlist.py`, 신규 테스트 **5개**.
- 출력기 미구현 기준 [RED Run #44048040474](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44048040474): **failure** (해당 모듈을 import하지 못함). 이는 실제 ROS/Gazebo 실패가 아닌 의도된 테스트 RED.
- 반례: private `source_code`·`pose`·private raw file path·callback handle(pointer) 삽입; 공개 JSON에 이 문자열 및 `/cmd_vel_supervised`가 노출되면 FAIL; source SYSTEM vs observer MONOTONIC 섞기 금지; 최초 gap 없으면 `NOT_REPRODUCED`, `gate_c_authorized=false`; invalid SHA, unbounded raw input을 실패 차단.

### GREEN: 수치형 allowlist exporter
- 경로: `d06/diagnostic/export_public_cm120_first_gap.py`
- 공개 결과 스키마 `axia.g07.cm120.public_first_gap_v1`. 고정 필드/숫자만 재생성:
  - 정확히 첫 RMW source>120ms pair, seq-relative [0,1], source/received SYSTEM **wall anchor 상대 ns**, observer MONOTONIC **mono anchor 상대 ns** 및 간격
  - identity-filtered original CM TF 함수 개수·wall duration
  - 동일 CM PID/TID 및 Advanced TF call에 포함된 개별 `nanosleep` 시작·종료/요청 시간의 Observer 상대 offset(최대 64개)
  - clock anchor offset과 explicit `sender_clock_domain_proven=false`
  - `root_cause_proven=false`, `cm120_release_pass=false`, `owner_wsl2_accepted=false`, `certified_estop=false`
- **업로드 금지:** Instructor 코드, 비공개 Git SHA의 강제 공개, ROS 원시 메시지·Pose/TF transform/frames, LTTng CTF, raw TF lines, memory pointers, bag/카메라/라이다, 전체 소스 파일.
- 용량: 결과 JSON **32KiB 미만**, artifact는 **정확한 두 파일** `first_gap_sanitized.json`·`SHA256SUMS.txt`만 업로드한다.

### 추가 GREEN: 실제 private raw → 공개 JSON의 실패차단 adapter
- 경로: `d06/scripts/g07_task01_extract_public_gap.py`
- raw ROS event JSONL/TF log/LTTng trace/anchor를 **sealed runner 임시 작업공간에서만** 읽고 기존 `select_exact_cm_callbacks`으로 해당 official CM C++ callback만 추출한다. private origin 자체는 artifact에 저장하지 않는다.
- 원본 누락·형식 오류·TF 심볼 불일치·과도한 데이터·artifact 생성 실패 시 `HOLD` 상태의 작은 공개 JSON만 생성하거나 작업을 실패시킨다. 사용자 비밀값, exception payload, raw 경로는 로그에 출력하지 않는다.
- 신규 negative **3개** (`d06/tests/test_g07_task01_public_evidence_adapter.py`).
- [최종 순수 GREEN #44048860819](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44048860819), tested source `5e6db932728085398fd1b6d9441847286d70c2be`, `Ran 5 tests ... OK`, `Ran 3 tests ... OK`, Python compile PASS.
- 같은 실행에서 synthetic allowlisted evidence JSON + SHA256SUMS 생성, SHA256 검증, official GitHub `actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02` 업로드 PASS:
  - artifact `axia-g07-task01-public-timing-only-l0`, ID `14312528121`
  - GitHub 저장 ZIP SHA256 `0bfef7bacafd46722572ebcea1d2ad8483f915f8c8887f3c81e5be9e966b99d0` (**이 ZIP digest는 #44048351427 이전 run의 값**; #44048860819의 checksum/digest는 GitHub 아티팩트 API에서 다시 확인 후 별개 기록할 것)
  - 다운로드 URL: https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44048860819
  - **이는 synthetic NO_GOAL L0 파일 custody 검증이지 실제 Gazebo Moving artifact가 아니다.**

## 3. 현재 공개 실행기로의 실제 연결

- 공개 코드 브랜치: `fix/g07-cm120-task01-public-evidence-20261117` (prior PR #159 tip `432b99819b287368604e29f90d4826afbc3fee5d`에서 분기).
- 공개 CI 릴리스 경로에 새 단일 diagnostic Moving Goal workflow 추가:
  `.github/workflows/axia-g07-task01-public-evidence-one-goal-l2-20261117.yml`, 원본 S2 공식 Waffle/Nav2 single-run workflow 재사용, public branch의 exact allowlist SHA `5e6db932728085398fd1b6d9441847286d70c2be`를 pin.
- 실제 새 공개 Actions Run: [#44049067368](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44049067368), workflow commit `1b017541d5908f267711108f667bc248f4dfe939`. **본 보고서 최초 작성 시 실행 중; PASS/FAIL은 최종 run 결론을 다시 조회하여 정정한다.**
- 실제 원본 증거 읽기/업로드 순서: (1) 공식 Waffle/Nav2 원래 read-only ROS/TF 진단, (2) `if:always()`로 allowlist JSON·SHA256 생성, (3) `if:always()`로 정확한 2파일 artifact 업로드, (4) `if:always()`로 비공개 checkout, LTTng, raw TF/ROS, JSON을 실행기에서 삭제.
- 실제 script는 결과 JSON을 생성하더라도 `AXIA_G07_TASK01_PUBLIC_EVIDENCE_NOT_RELEASE_NOT_ESTOP`를 출력하며 CM120 release PASS는 주장하지 않음.
- 기존 공개 release branch의 비공개 `Contents:Write` Secret을 요구하던 preflight workflow `.github/workflows/axia-g07-task01-private-custody-release-preflight-20261117.yml` **삭제**, commit `2256e190f4a1c57ad3df15b29b68d16de6c24f1c`.
- 작업 feature branch에서 구 `d06/scripts/g07_task01_private_custody_canary.sh`, `d06/tests/test_g07_cm120_task01_private_custody_gate.py`, `.github/workflows/axia-g07-cm120-task01-private-custody-l0.yml` 제거. 이전 [PR #159](https://github.com/silverbjin/axia-robot-safety-ci-public/pull/159)와 CI 기록은 교육용 히스토리로 보존.
- 새로운 `AXIA_G07_EVIDENCE_WRITE_TOKEN` Secret **필요 없음**. 단, 비공개 instructor 소스를 공식 런타임에서 실행하기 위한 기존 read-only `AXIA_CLOUD_CI`는 현행 공개 CI sealed environment 안에서 계속 사용함. **비공개 GitHub Actions를 실행하는 것은 아니다.**

## 4. 이번 정책 변경으로도 남은 정확한 인수 조건

| 태스크 | 현재 판정 |
|---|---|
| Task01 산출물·증거보존 정책 | 공개 CI synthetic allowlist L0 GREEN8 + artifact upload 성공 |
| Task01 공식 실제 Moving Goal 최초 gap TF sleep vs Scheduler | 새 public diagnostic Run의 **실제 결과 검증 전**, 원인 미입증 |
| Task02 최소 성능 수정 | 원인 proven 전 **BLOCKED**, 파라미터/CPU affinity/안전 TTL 임의 변경 금지 |
| Task03 tracer-OFF 공개 실제 Gazebo L2 | **NOT_RUN**, original source/Observer ≤120ms 두 조건 동시 동일 run 미검증 |
| Task04 Owner WSL2 Gazebo/RViz L3 | **NOT_RUN**, 실제 수동 최종 인수 단계 |
| `main` 병합·학생 배포 | **NOT_DONE**, 사용자 승인 필요 |

원시 계측이 공개 allowlist artifact로 변환되더라도 현재 `sender_clock_domain_proven=false`; source SYSTEM과 observer MONOTONIC의 직접 인과는 **미증명**. Kernel `sched_schedstats=0`일 때 Scheduler runqueue 0으로 간주하지 않음. NO_FIRST_SOURCE_PAIR라면 동일 소스 재주행을 반복하지 않고 원인 미확정 HOLD.

## 5. 실행 명령·검증 수준·Git SHA

공개 CI L0 테스트:
```bash
python3 -m unittest discover -s d06/tests -p 'test_g07_task01_public_evidence_allowlist.py' -v
python3 -m unittest discover -s d06/tests -p 'test_g07_task01_public_evidence_adapter.py' -v
python3 -m py_compile d06/diagnostic/export_public_cm120_first_gap.py d06/scripts/g07_task01_extract_public_gap.py
# workflow는 공개 repo branch에서 push된 변경으로 이미 실행됨
```

실제 Gazebo/Owner 실행 여부는 각 위 원본 Run conclusion과 실측 값이 확인된 뒤에만 보고서·PR에 업데이트한다. 공개 Artifact 저장은 **민감정보를 제거한 시간 기록**을 남기는 행위이지, 완전한 원본 14-topic bag 보존과 동등하지 않다. 최종 L2에서는 기존 원본 bag custody를 **비공개 runner 내 검증**하고 공개 요약 수치만 남길 수 있으나 Owner 최종 인수 전까지 원본 매체의 보존 여부와 신뢰성을 별도 표시해야 한다.

```text
AXIA_G07_PUBLIC_CI_EVIDENCE_POLICY=ADOPTED_NO_PRIVATE_WRITE_TOKEN
AXIA_G07_PUBLIC_ALLOWLIST_L0=PASS_8
AXIA_G07_PUBLIC_ARTIFACT_SYNTHETIC_CANARY=PASS
AXIA_G07_PUBLIC_REAL_MOVING_DIAGNOSTIC=RUN_PENDING_AT_REPORT_CREATION
AXIA_G07_TASK01_SLEEP_VS_SCHEDULER_CAUSE=UNPROVEN
AXIA_G07_TASK02=NOT_STARTED
AXIA_G07_TASK03_TRACER_OFF_RELEASE=NOT_RUN
AXIA_G07_TASK04_OWNER_WSL2=NOT_RUN
CM120_TRACER_OFF_RELEASE=HOLD
AXIA_MVP_DEMO_ACCEPTED=HOLD
CERTIFIED_ESTOP=false
MAIN_MERGED=false
```
