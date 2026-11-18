# AXIA G07 C29 — 실제 이동 Goal·Safety TTL 공개 CI / Owner 원샷 릴리스 REVIEW

**2026-11-17 KST · Jazzy / Gazebo Harmonic / 공식 Nav2·TB3 Waffle 시뮬레이션 1-Goal 범위.**
비공개 Instructor 솔루션/원본 bag는 이 공개 저장소에 포함하지 않는다.

## 출처·수준 동결

- 최신 D07 no-goal Owner JcX 성공: geometry·Costmap·Nav2 ordered shutdown은 검증됐지만 **`goal_sent=false`**, 이동/Guard TTL 증거가 아니다.
- 기존 G07 Owner one-Goal 성공 Source SHA `eb984b73138e592caa67426eed9c60dde2ca2ebd`: CLEAR→SLOW→STOP, odom0.209670m, CM Observer max140.852ms, 1.032s 정지.
- 기존 P4 Owner 첫 Guard CM stale failure: 내부 age **162.738ms** >150ms. 최초 Guard 안전 latch는 올바른 fail-close, 직접 원인(CM publish/DDS/Guard callback/host scheduler)은 미확정.
- 최신 비공개 Instructor 기능 pin `275d68012a6a1cdc5ce466f2581281b9614c4381`. 오류 후 CM internal TTL 및 RMW publish/receive/Observer 원인 분리 로그만 추가. Guard, Safety Supervisor 기본 정책, FaultInjector, CM zones, Nav2, 안전 TTL, ROS 정상경로 변경 없음.

## 실제 공개 CI 실행 증거: 같은 기능 범위지만 실행마다 결과가 다름

| 단계 | Actions | 실제 판정 |
|---|---|---|
| T01 최초 CM 내부 TTL 기록 RED→GREEN | [RED #44007440578](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44007440578) → [GREEN #44007586340](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44007586340) | 순수 진단 6+11 PASS |
| **실제 L2 1차** | [#44007778295](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44007778295) | **FAIL**. 공식 Goal/CLEAR/SLOW/STOP·odom STOP 1.010s 성공, 하지만 CM Observer 간격 **171.351249ms** >150ms (CROSSES_STOP); Guard latch 없음. CM publisher 원인 입증 불가 |
| T04 RMW 원인 분리 RED→GREEN | [RED #44008587413](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44008587413) → [GREEN #44008704363](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44008704363) | 신규5/5+기존11/11. 오류 경로에서 RMW src/receive/Observer 비교 기록, 안전 런타임 경로 무변경 |
| **실제 L2 2차** | [#44008818507](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44008818507) | **SUCCESS 한정**. 1 Goal CLEAR 2.053m / SLOW 0.749m / STOP 0.398m(최종0), odom STOP 1.006s. 최대: source57.798ms, CM129.400ms, Guard55.384ms, Supervisor57.591ms, Scan202.685ms, odom132.728ms, clock103.498ms. 실제 rosbag sqlite quick_check 및 Nav2 ACK/CM exit0 |
| Owner public-only L0 | [#44009636638](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44009636638) | **5/5 PASS + bash syntax + --self-check**. NO ROS/Goal/Owner L3 |

**가장 중요한 한계:** 성공한 L2 이전에 발생한 CM Observer 171.351ms 초과 원인은 해결된 것이 아니다. 이번 변경은 오류 진단만 추가했다. **두 번째 한정 L2 PASS를 전체 시연 안정성 PASS 또는 150ms 이슈 해결로 승격하지 않는다.** 실제 WSL2에는 Linux CI와 다른 WSLg GPU/DDS/CPU 스케줄러가 존재한다.

## Owner WSL2 한 번 인수 후보(안전 계약)

- Public 원샷: `scripts/axia_g07_c29_owner_one_goal_ttl_once.sh`, public branch `fix/g07-c29-owner-one-goal-ttl-20261117`.
- 인수 전 확인: immutable public CI workflow commit `70de0c1a52f11d194e1f2aa0f1b263db7f75912c`, real run `44008818507`가 정확히 `completed success`인지 GitHub API로 직접 검증. Private Instructor SHA `275d68012a6a1cdc5ce466f2581281b9614c4381`만 checkout.
- WSL2 Ubuntu24/ROS Jazzy/TTY/gh auth 필수. 원샷은 `--self-check`에서 어떠한 ROS/Goal도 실행하지 않는다.
- 실제 Goal은 비공개 기존 `scripts/p2_owner_l3_wsl2.sh --case G07 --mvp-relocated-obstacle`가 담당하며, 사용자 본인이 실제 제어 TTY에 `YES-P2-G07-GOAL` 입력해야 1회 승인된다. 스크립트가 승인 문자열을 자동 제공하지 않는다.
- 기존 private Owner는 rosbag14-topic, Goal UUID, Guard/CM/odom/Scan/clock, native obstacle pose ACK, ordered shutdown, 원본 SHA256/tar를 사용자 로컬에 보관. **Owner WSL2은 아직 실행하지 않았고, success 미표시**.
- 원본 WSLg GUI 실물과 Linux CI의 오프스크린 런타임이 다르다. D07에서 발생한 OGRE/Mesa SIGSEGV 가능성도 무시하지 않는다.
- 첫 안전 상태·첫 150/300ms timing 위반을 기준으로 분석. 새 현장 오류 발견 시 **같은 현장 재실행 반복 금지, 원본 수치 공개 CI 회귀 RED→GREEN 우선**.

## REVIEW 및 Git 상태

- Public 파일: 새 원샷 `scripts/axia_g07_c29_owner_one_goal_ttl_once.sh`, 테스트 `tests/test_axia_g07_c29_owner_candidate.py`, 워크플로 `.github/workflows/axia-g07-c29-owner-one-goal-ttl-public-l0.yml`, 이 보고서. Private 코드/강사용 정답·raw evidence 공개하지 않음.
- 테스트: `python3 -m unittest discover -s tests -p test_axia_g07_c29_owner_candidate.py -v`, `bash -n scripts/axia_g07_c29_owner_one_goal_ttl_once.sh`, `bash scripts/axia_g07_c29_owner_one_goal_ttl_once.sh --self-check`. 공개 GitHub Actions #44009636638 전부 성공.
- **전체 제품 `AXIA_MVP_DEMO_ACCEPTED=HOLD`**, 인증된 하드웨어 E-Stop 아님, G05/G06·다수 회귀 독립 인수 밖.
- Main에 병합하지 않고 Draft PR로만 보존하며 사용자 별도 승인 필요.
