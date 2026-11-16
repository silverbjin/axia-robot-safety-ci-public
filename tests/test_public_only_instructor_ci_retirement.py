"""PUBLIC CI only: migration inventory for retired Instructor GitHub Actions.

No private checkout, no hidden tests, no approval inferred from public analogs.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "public_ci" / "instructor_workflow_migration_20261116.json"
WORKFLOWS = ROOT / ".github" / "workflows"
EXPECTED = {
    "block-c-release-branch-cleanup.yml",
    "p0-preflight.yml",
    "p0-staged-startup.yml",
    "p1-ci-runner-canary.yml",
    "p1-fix01-03-gates.yml",
    "p1-fix04-08-gazebo.yml",
    "p1-postp0-a-c.yml",
    "p1-preacceptance-s01-s05.yml",
    "p1-python-unit.yml",
    "p1-t04-ros-jazzy.yml",
    "p1-t05-ros-launch.yml",
    "p1-t06-ros-faults.yml",
    "p1-t07-evidence-runner.yml",
    "p1-t08-nav2-handoff.yml",
    "p1-t08-pre-goal-real-gazebo.yml",
    "p1-t08-ros-live.yml",
    "p1-t08-ros-shutdown.yml",
    "p1-t08-scan-arming-regression.yml",
}


def load_inventory():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_inventory_exists_and_exactly_covers_18_retired_instructor_workflows():
    inventory = load_inventory()
    assert inventory["policy"] == "PUBLIC_CI_ONLY"
    assert inventory["instructor_github_actions_allowed"] is False
    names = [item["instructor_workflow"] for item in inventory["mappings"]]
    assert len(names) == len(set(names)) == 18
    assert set(names) == EXPECTED


def test_each_public_reuse_target_is_existing_public_workflow():
    for item in load_inventory()["mappings"]:
        targets = item["public_workflows"]
        assert targets and all((WORKFLOWS / p).is_file() for p in targets)
        assert item["equivalence"] in ("partial", "canary", "not_equivalent")
        assert item["private_checks_executed"] is False


def test_release_and_private_gates_are_not_falsely_promoted():
    inventory = load_inventory()
    assert inventory["private_source_checkout_in_public_ci"] is False
    assert inventory["instructor_hidden_tests_in_public_ci"] is False
    assert inventory["gazebo_owner_acceptance_from_ci"] is False
    assert inventory["certified_estop_from_ci"] is False
    assert inventory["production_guard_ttl_from_ci"] is False
    assert inventory["legacy_instructor_workflows_reexecuted"] is False


def test_public_python_ros_and_readonly_gazebo_equivalents_are_scoped():
    inventory = load_inventory()
    workflows = {p for item in inventory["mappings"] for p in item["public_workflows"]}
    assert "public-contracts.yml" in workflows
    assert "public-jazzy-dds.yml" in workflows
    assert "public-gazebo-readonly.yml" in workflows
    assert "public-canary.yml" in workflows
    assert any(item["equivalence"] == "not_equivalent" for item in inventory["mappings"])
