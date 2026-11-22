# Velog Domain Labs — Public CI Contract (2026-11-23)

## Scope
- Instructor SHA: `d9cba3ee80066e067c6739503ab9eeec5f25ea68` (private, protected `axia-instructor-sealed`; no logs or answer export).
- Student SHA: `414518d407dfe10551dcbc73f856e0b944a43f9b` (independent student repository with deliberate TODO RED).
- Public branch: `feat/velog-domain-knowledge-labs-20261123` — not merged to main.
- Student: five ROS 2 Jazzy `ament_python` packages, diagram/README and 24 tests expected `NotImplementedError`.
- Instructor: 24 public cases and five additional **private** negative tests, total 29 tests GREEN.
- No new Nav2 Goal, no Gazebo launch, no WSL2 acceptance, no certified E-Stop claim.
- Only Public CI Actions permitted. Private CI checkout requires exact SHA and protected environment.

## Reproducing public contract locally
```bash
python3 velog_domain_labs_ci/check_student_contract.py ../axia-robot-safety-student/velog_domain_labs
```

## Release gate
Do not merge Instructor main until both actual GitHub Actions jobs are completed with conclusion=success. Skipped or pending private job is HOLD. Student and Public CI remain on their own feature branches; neither is merged into main by this task.

## Baseline protection
The existing G07 native Gazebo/Owner L3 source and its acceptance truth remain unchanged; an L0 educational test is not a G07/G00–G13 acceptance test.
