# Velog Domain Labs — Public CI Contract (2026-11-23)

## Scope
- Instructor SHA: `e049cd85ea52ba4d55c0b79dbb96aa8476a6b10e` (private, protected `axia-instructor-sealed`; no logs or answer export).
- Student SHA: `89277c433a1b6485b8926712b54b6c0b133f11ec` (independent student repository with deliberate TODO RED).
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

### Protected branch restriction
신규 feature/release 브랜치의 sealed job이 runner allocation 이전에 실패하므로 기존 권한 승인된 `release/p2-g06-cm-ttl-20261110`에 **신규 이름의 독립 워크플로 파일만** 배치하여 private L0 검증. 이 검증은 G07/G06 시연 자체를 다시 인수하는 작업이 아님.
