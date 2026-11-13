#!/usr/bin/env python3
"""P4-00 metadata-only G11 source provenance fail-closed check.

This is NOT a ROS, Gazebo, safety, or release acceptance tool.
Reads a private metadata JSON in a sealed public-CI job; prints no source records.
The frozen v1 contract permits zero formally accepted scenario cold-runs.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
GOAL32 = re.compile(r"^[0-9a-f]{32}$")
IMAGE_DIGEST = re.compile(r"^[-.a-z0-9/]+@sha256:[0-9a-f]{64}$")
SCENARIOS = ("S01", "S02", "S03", "S04", "S05")


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError("P4_00_LEDGER_CONTRACT_BLOCKED:" + reason)


def check(data: dict) -> dict:
    """Check immutable *candidate index* v1, not whether a real run passed."""
    require(isinstance(data, dict), "ROOT")
    require(data.get("schema") == "axia_p4_g11_source_evidence_ledger_v1", "SCHEMA")
    require(data.get("scope") == "P4_00_METADATA_ONLY_NO_NEW_ROS_GAZEBO_OR_OWNER_RUN", "SCOPE")
    require(isinstance(data.get("origin_staging_sha"), str)
            and SHA40.fullmatch(data["origin_staging_sha"]) is not None, "STAGING_SHA")
    require(isinstance(data.get("runtime_reference_digest"), str)
            and IMAGE_DIGEST.fullmatch(data["runtime_reference_digest"]) is not None, "RUNTIME_DIGEST")
    require(data.get("runtime_digest_this_task_reverified") is False, "NO_RUNTIME_RECHECK")
    for key in ("formal_accepted", "main_merge_approved", "student_release_approved",
                "hardware_estop_certified"):
        require(data.get(key) is False, "FALSE_PROMOTION_" + key)

    sources = data.get("observed_sources")
    require(isinstance(sources, list) and len(sources) >= 5, "SOURCES_MISSING")
    by_id = {}
    for record in sources:
        require(isinstance(record, dict), "SOURCE_RECORD")
        rid = record.get("id")
        require(isinstance(rid, str) and rid and rid not in by_id, "DUPLICATE_OR_EMPTY_SOURCE_ID")
        require(record.get("scenario") in SCENARIOS, "SOURCE_SCENARIO")
        require(isinstance(record.get("gate"), str) and record["gate"].startswith("G"), "GATE")
        require(isinstance(record.get("capture_source_sha"), str)
                and SHA40.fullmatch(record["capture_source_sha"]) is not None, "SOURCE_SHA")
        require(isinstance(record.get("evidence_level"), str)
                and bool(record["evidence_level"]), "EVIDENCE_LEVEL")
        require(record.get("formal_eligible") is False, "UNSIGNED_SOURCE_PROMOTION")
        require(isinstance(record.get("reason"), str) and bool(record["reason"]), "MISSING_HOLD_REASON")
        for key, pattern in (("reported_goal_uuid", GOAL32), ("archive_sha256", SHA256)):
            if key in record and record[key] is not None:
                require(isinstance(record[key], str) and pattern.fullmatch(record[key]) is not None,
                        "INVALID_" + key.upper())
        by_id[rid] = record
    failed = by_id.get("p2_xjx_g06_failed")
    require(failed is not None and failed.get("gate") == "G06"
            and failed.get("scenario") == "S03"
            and failed.get("observed_result") == "FAIL"
            and "FAILED" in failed.get("evidence_level", ""), "HISTORIC_G06_FAILURE_PRESERVATION")

    g08 = data.get("g08")
    require(isinstance(g08, dict)
            and g08.get("status") == "G08_RAW_MISSING_IN_REVIEWED_INVENTORY_NOT_ACCEPTED"
            and g08.get("replayed_or_reran_goal") is False, "G08_RAW_NOT_ACCEPTED")
    origin = by_id.get(g08.get("reference_source_id"))
    require(origin is not None and origin["scenario"] == "S01" and origin["gate"] == "G08"
            and GOAL32.fullmatch(str(origin.get("reported_goal_uuid", ""))) is not None
            and SHA256.fullmatch(str(origin.get("archive_sha256", ""))) is not None
            and origin["evidence_level"] == "OWNER_REPORT_ONLY", "G08_REPORT_SOURCE_ONLY")

    g11 = data.get("g11")
    require(isinstance(g11, dict) and g11.get("required_scenarios") == 5
            and g11.get("required_formal_runs_each") == 3, "BASELINE_5X3")
    counts = g11.get("formal_acceptance_counts")
    require(isinstance(counts, dict) and set(counts) == set(SCENARIOS), "FORMAL_COUNTS_KEYS")
    require(all(type(counts[s]) is int and counts[s] == 0 for s in SCENARIOS),
            "NO_FORMAL_RUNS_JOINED")
    scenarios = g11.get("scenarios")
    require(isinstance(scenarios, list) and len(scenarios) == 5, "FIVE_SCENARIOS")
    seen = set()
    for entry in scenarios:
        require(isinstance(entry, dict) and entry.get("id") in SCENARIOS, "SCENARIO_ENTRY")
        sid = entry["id"]
        require(sid not in seen, "DUPLICATE_SCENARIO")
        seen.add(sid)
        require(entry.get("required") == 3 and type(entry.get("formal_verified")) is int
                and entry["formal_verified"] == counts[sid] == 0
                and type(entry.get("remaining_to_qualify")) is int
                and entry["remaining_to_qualify"] == 3, "NO_UNVERIFIED_NUMERATOR_PROMOTION")
        require(entry.get("new_runs_required_now") == "UNDETERMINED_REQUALIFY_EXISTING_RAW_FIRST",
                "DO_NOT_FORCE_NEW_OWNER_RUN")
        ids = entry.get("unverified_candidate_ids")
        require(isinstance(ids, list) and ids and len(ids) == len(set(ids)), "CANDIDATE_LIST")
        require(all(key in by_id and by_id[key]["scenario"] == sid for key in ids),
                "CANDIDATE_SCENARIO_JOIN")
        require(isinstance(entry.get("unresolved_join"), list)
                and len(entry["unresolved_join"]) > 0, "RAW_JOIN_GAP_RECORDED")
    require(seen == set(SCENARIOS), "MISSING_SCENARIO")

    g12 = data.get("g12")
    require(isinstance(g12, dict) and g12.get("status") == "D03_SCOPED_ONLY_FULL_RELEASE_HOLD"
            and g12.get("full_git_history_scan_done") is False
            and g12.get("full_p4_student_release_approved") is False, "G12_RELEASE_HOLD")
    g13 = data.get("g13")
    require(isinstance(g13, dict) and g13.get("status") == "NOT_RUN"
            and g13.get("required_distinct_external_pcs") == 2
            and type(g13.get("verified_distinct_external_pcs")) is int
            and g13["verified_distinct_external_pcs"] == 0, "G13_EXTERNAL_PC_NOT_RUN")
    return {
        "status": "P4_00_METADATA_SCOPE_PASS", "formal_accepted": False,
        "g11_formal_runs": 0, "observed_candidate_records": len(sources),
        "g08": "NOT_ACCEPTED", "g12": "D03_SCOPED_ONLY", "g13": "NOT_RUN",
        "ros_l1_run": False, "gazebo_l2_run": False, "owner_l3_run": False,
    }


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: p4_g11_source_ledger.py PRIVATE_LEDGER_JSON", file=sys.stderr)
        return 2
    try:
        result = check(json.loads(Path(argv[1]).read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        # Never echo sensitive path, raw fixture content, or private source lines.
        kind = str(exc) if isinstance(exc, ValueError) else "INVALID_OR_MISSING_LEDGER"
        print("AXIA_P4_00_LEDGER_L0_FAIL " + kind, file=sys.stderr)
        return 1
    print("AXIA_P4_00_LEDGER_L0_PASS candidates="
          + str(result["observed_candidate_records"]) + " G11_FORMAL_0_OF_15"
          + " G08_NOT_ACCEPTED G12_SCOPED_ONLY G13_NOT_RUN")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
