"""D04 branch ledger contract (public docs only; NO ROS/Goal/private Actions).

Deliberately tests *publication consistency* only. Runtime CI provenance is
recorded as existing URLs and not re-labeled as a new Gazebo test.
"""
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
LEDGER=ROOT/"docs/D04_MAIN_INTEGRATION_BRANCH_LEDGER_20261115_KO.md"


def test_d04_main_document_covers_all_eight_roles():
    doc=LEDGER.read_text(encoding="utf-8")
    for n in (7,8,9,11,14,59,61,62):
        assert f"pull/{n}" in doc
    assert "ahead_by=0" in doc
    assert "PRIVATE" not in doc.split("## D04 공개 CI 대표 근거")[0] or "비공개 Actions" in doc
    assert "d05-private-sealed-l0-l1.yml" in doc
    assert "의도적으로 main에 추가하지 않는다" in doc
    assert "비공개 Actions" in doc and "WSLg" in doc


def test_d04_main_keeps_existing_owner_runtime_entrypoints():
    for filename in (
        "scripts/axia_d04_classroom_wsl2_once.sh",
        "scripts/axia_d04_instructor_single_image_once.sh",
        "scripts/d04_owned_gui_shutdown.py",
        "scripts/d04_instructor_single_image_report.py",
    ):
        assert (ROOT/filename).is_file(), filename


def test_d04_ledger_no_main_merging_of_private_sealed_workflow():
    workflow=ROOT/".github/workflows/d04-main-merge-docs-ci.yml"
    src=workflow.read_text()
    assert "environment: axia-instructor-sealed" not in src
    assert "AXIA_CLOUD_CI" not in src
    assert "axia-robot-safety-instructor" not in src
    assert "pytest" in src
    assert "No private checkout" in src
