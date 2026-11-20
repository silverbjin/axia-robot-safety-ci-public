# AXIA D08 Task00 — Baseline integration report (2026-11-18 KST)

## 작업 기준
- Public repo: silverbjin/axia-robot-safety-ci-public
- Branch: feat/d08-unified-sensor-cm-path-20261118; base main SHA: 62e366b51c64da25ad0216328fe1e019b78e0bef
- Related PR: https://github.com/silverbjin/axia-robot-safety-ci-public/pull/166
- Checked candidate source HEAD: 52b10486649b4e0070c67ca67b29be7cd82a3165; report commit creates new HEAD and requires exact SHA follow-up
- Reused prior D08 world/physical proxy/RGBD/scan; earlier D07-H01 L2 #44051183220 and D08 GUI L2 #44120800666 are different SHAs, not new D08 integrated proof
- Scope: NO_GOAL provenance. Excluded: current real Nav2/CM same-source data, D05 2 VALID, Owner WSLg pixels, Moving E2E.

## PLAN → RED → GREEN → REFACTOR → REVIEW → COMMIT
- First missing boundary: previous D08 L2 verdict had no exact SHA/world hash/domain/partition evidence to preclude joining unrelated runs.
- Hypothesis: fail closed on mixed worlds, nonphysical proxy, source SHA and runtime partition BEFORE actual Gazebo start.
- RED test committed: d08/tests/test_d08_unified_runtime_provenance.py (e80ff3cf30966aeb4321b46e357cd1c4e4e43155), workflow wired (79ac7b330ff7364135b9bba8adddd8cc962ea47a). RED **execution** not confirmed, only tests authored before implementation.
- GREEN helper: d08/harness/d08_runtime_provenance.py (de044e778cdefc5fbc7c1dfea8f593949354e061), attached to d08/scripts/d08_public_gazebo_l2.py (52b10486649b4e0070c67ca67b29be7cd82a3165).
- Actual CI: https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/44199555533; L0 job 134449804398.
- Actual CI command uses Python 3.12 and pytest 8.3.5:
  python -m pytest -q d08/tests/test_d08_unified_runtime_provenance.py d08/tests/test_d08_main_public_only_contract.py d08/tests/test_d08_collocated_human_proxy.py d08/tests/test_d08_g07_lidar_visible_proxy.py d08/tests/test_d08_rgbd_alignment_evidence.py d08/tests/test_d08_live_public_harness.py
- Actual L0 log: "22 passed in 0.12s", "D08_PUBLIC_MAIN_NO_GOAL_L0_PASS" (exit 0).
- REFACTOR/REVIEW: only a pure read-only provenance helper, no safety TTL or upstream Nav2/CM changes. Static no_moving_goal flag denotes code-path intent, not direct ROS graph audit. No private solution copied.
- Commit: report SHA to be referenced in PR comments after write.

## 증거 기반 판정
- L0: PASS (22 tests, candidate SHA above).
- L1: NOT_RUN for new integration; actual Gazebo L2: IN_PROGRESS / NOT_VERIFIED at time of report (same-run #44199555533); Owner WSL2 L3: NOT_RUN.
- Proposed runtime: Gazebo default, Waffle spawn axia_d08_ci_waffle, physical proxy axia_p2_g07_obstacle, ROS_DOMAIN_ID 69, generated GZ_PARTITION axia_d08_ci_<pid>. Actual artifacts must confirm these; no invented rates/times.
- ROS topic types/QoS, RGBD/person VALID/UNKNOWN, CM actual /scan input, costmaps and planner paths, Guard TTL, Contact/odom, 3D GUI pixels: not newly verified.
- G07 latest moving strict: HOLD; NO_GOAL path never authorizes Moving Goal.

## 다음 단계
- Review exact-HEAD real L2 output and first failure before declaring Task00 PASS.
- Task01 two real person VALID distances plus UNKNOWN; Task02 one-world actual CM+official Nav2 Path; Task04 classroom one-shot.
- No main merges. Owner single WSL2 run postponed until public exact-HEAD L2 proof.
